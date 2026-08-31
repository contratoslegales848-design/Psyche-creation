"""HttpImageProvider — adapter REAL contra una API de imagen por HTTP.

Por que este y no un SDK concreto: en este workspace no hay ningun SDK de
proveedor de imagen instalado ni ninguna credencial configurada (verificado).
Escribir `OpenAIImageProvider` sin su SDK seria inventar un proveedor, que el
mandato prohibe. Este adapter, en cambio, es codigo real: habla HTTP de verdad,
traduce la peticion normalizada, normaliza la respuesta y normaliza los errores
al vocabulario del dominio. Sirve para cualquier endpoint que acepte JSON y
devuelva imagen en base64 o por URL — incluidos los compatibles con OpenAI.

NO se ejecuta ninguna llamada externa en las pruebas: el transporte es
inyectable y se prueba con un doble.

La credencial se lee del entorno y NUNCA se registra, ni en receipts, ni en
eventos, ni en mensajes de error.
"""

import base64
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from .base import ImageProvider, ProviderCapabilities, GenerationResult

DEFAULT_TIMEOUT = 60


class HttpTransportError(Exception):
    """Fallo de transporte con un codigo ya clasificado."""

    def __init__(self, kind, message, status=None):
        super().__init__(message)
        self.kind = kind          # AUTH | RATE_LIMIT | TIMEOUT | INVALID_REQUEST |
        self.status = status      # UNAVAILABLE | CONTENT_REJECTED | TRANSPORT


@dataclass
class HttpProviderConfig:
    """Todo lo especifico del proveedor vive aqui, no en el dominio."""

    provider_id: str
    endpoint: str
    model: str = ""
    api_key_env: str = ""
    aspect_ratios: tuple = ("9:16", "4:5")
    supports_negative_prompt: bool = True
    supports_reference_image: bool = False
    supports_editing: bool = False
    supports_reliable_text: bool = False
    supports_seed: bool = True
    supports_transparency: bool = False
    max_width: int = 4096
    max_height: int = 4096
    timeout: int = DEFAULT_TIMEOUT
    # Nombres de campo del proveedor. Traducir aqui, nunca en el dominio.
    field_map: dict = field(default_factory=lambda: {
        "prompt": "prompt", "negative_prompt": "negative_prompt",
        "width": "width", "height": "height", "seed": "seed", "model": "model",
    })


def urllib_transport(url, payload, headers, timeout):
    """Transporte por defecto. Clasifica el fallo; no lo interpreta."""
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        cuerpo = ""
        try:
            cuerpo = exc.read().decode("utf-8", "replace")[:500]
        except Exception:
            pass
        kind = {401: "AUTH", 403: "AUTH", 429: "RATE_LIMIT",
                400: "INVALID_REQUEST", 422: "INVALID_REQUEST"}.get(
                    exc.code, "UNAVAILABLE" if exc.code >= 500 else "TRANSPORT")
        raise HttpTransportError(kind, f"HTTP {exc.code}: {cuerpo}", status=exc.code)
    except TimeoutError as exc:
        raise HttpTransportError("TIMEOUT", f"timeout tras {timeout}s: {exc}")
    except urllib.error.URLError as exc:
        motivo = getattr(exc, "reason", exc)
        if isinstance(motivo, TimeoutError) or "timed out" in str(motivo).lower():
            raise HttpTransportError("TIMEOUT", f"timeout tras {timeout}s")
        raise HttpTransportError("UNAVAILABLE", f"proveedor inalcanzable: {motivo}")
    except json.JSONDecodeError as exc:
        raise HttpTransportError("TRANSPORT", f"respuesta no es JSON: {exc}")


class HttpImageProvider(ImageProvider):
    def __init__(self, config, transport=None, image_fetcher=None):
        self.config = config
        self.id = config.provider_id
        self._transport = transport or urllib_transport
        self._fetch = image_fetcher
        self.llamadas = 0

    # --- capacidades ---
    def capabilities(self):
        c = self.config
        return ProviderCapabilities(
            provider_id=c.provider_id,
            aspect_ratios=tuple(c.aspect_ratios),
            supports_negative_prompt=c.supports_negative_prompt,
            supports_reference_image=c.supports_reference_image,
            supports_editing=c.supports_editing,
            supports_reliable_text=c.supports_reliable_text,
            supports_seed=c.supports_seed,
            supports_transparency=c.supports_transparency,
            max_width=c.max_width, max_height=c.max_height,
        )

    # --- credencial ---
    def _auth_headers(self):
        if not self.config.api_key_env:
            return {}
        key = os.environ.get(self.config.api_key_env)
        if not key:
            raise HttpTransportError(
                "AUTH", f"falta la credencial: variable de entorno "
                        f"{self.config.api_key_env} no definida.")
        return {"Authorization": f"Bearer {key}"}

    # --- traduccion ---
    def _payload(self, request):
        f = self.config.field_map
        p = {f["prompt"]: request.prompt,
             f["width"]: request.width,
             f["height"]: request.height}
        if self.config.model:
            p[f["model"]] = self.config.model
        if request.negative_prompt and self.config.supports_negative_prompt:
            p[f["negative_prompt"]] = request.negative_prompt
        if request.seed is not None and self.config.supports_seed:
            p[f["seed"]] = request.seed
        return p

    def _extraer_imagen(self, data):
        """Acepta las dos formas habituales: base64 embebido o URL."""
        if not isinstance(data, dict):
            raise HttpTransportError("TRANSPORT", "respuesta con forma inesperada.")

        if data.get("error"):
            err = data["error"]
            msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
            kind = "CONTENT_REJECTED" if "safety" in msg.lower() or "policy" in msg.lower() \
                else "INVALID_REQUEST"
            raise HttpTransportError(kind, msg)

        items = data.get("data") or data.get("images") or []
        if not items:
            raise HttpTransportError("TRANSPORT", "el proveedor no devolvio ninguna imagen.")
        item = items[0]
        if isinstance(item, str):
            item = {"b64_json": item}

        b64 = item.get("b64_json") or item.get("base64") or item.get("image")
        if b64:
            try:
                return base64.b64decode(b64, validate=True)
            except Exception as exc:
                raise HttpTransportError("TRANSPORT", f"base64 invalido: {exc}")

        url = item.get("url")
        if url:
            if self._fetch is None:
                raise HttpTransportError(
                    "TRANSPORT", "el proveedor devolvio una URL y no hay descargador configurado.")
            return self._fetch(url)
        raise HttpTransportError("TRANSPORT", "la respuesta no contiene imagen reconocible.")

    # --- ejecucion ---
    def generate(self, request):
        self.llamadas += 1
        base = dict(provider_id=self.id, model=self.config.model, seed=request.seed)
        try:
            data = self._transport(self.config.endpoint, self._payload(request),
                                   self._auth_headers(), self.config.timeout)
            img = self._extraer_imagen(data)
        except HttpTransportError as exc:
            # Error normalizado al vocabulario del dominio. Sin credenciales dentro.
            return GenerationResult(ok=False, error=f"{exc.kind}: {exc}", **base)
        except Exception as exc:                      # noqa: BLE001
            return GenerationResult(ok=False, error=f"TRANSPORT: {type(exc).__name__}", **base)

        if not img:
            return GenerationResult(ok=False, error="TRANSPORT: asset vacio", **base)

        mime = "image/png" if img.startswith(b"\x89PNG") else \
               "image/jpeg" if img.startswith(b"\xff\xd8") else ""
        # El adapter NO decide autoridad: solo reporta lo que recibio.
        return GenerationResult(ok=True, image_bytes=img, width=request.width,
                                height=request.height, mime_type=mime, **base)
