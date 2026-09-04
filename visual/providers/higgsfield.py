"""Proveedor Higgsfield: el motor de imagen real, cableado y con freno de mano.

Estado comprobado hoy, no supuesto. Consultado el 2026-09-03 contra el conector
en vivo:

    balance          -> {"credits": 0, "subscription_plan_type": "free"}
    models_explore   -> unlim.available = false

Es decir: HOY NO SE PUEDE GENERAR NINGUNA IMAGEN. Ni de pago (cero creditos) ni
por la via gratuita (sin asignacion). Este modulo existe para que el dia que haya
creditos no haya que escribir nada: la peticion ya sale formada y validada.

Por que no es un HttpImageProvider. Higgsfield se alcanza por un conector MCP,
no por un endpoint HTTP con clave: Python no puede llamarlo en tiempo de
ejecucion. Lo honesto es no fingir que si. Este proveedor NORMALIZA la peticion
y emite un despacho pendiente; quien lo ejecuta es un agente con el conector, y
devuelve la URL de la imagen al pipeline. El dominio no se entera de la
diferencia porque la frontera es la misma: entra NormalizedImageRequest, sale
GenerationResult.

Y un freno que no depende de los creditos: este proveedor se niega a preparar
nada cuyo gate de arte no este ABIERTO. Que exista presupuesto no es una razon
para generar arte de un claim sin verificar.
"""

from dataclasses import dataclass

from .base import GenerationResult, ImageProvider, ProviderCapabilities, ProviderError

# Catalogo verificado contra models_explore el 2026-09-03. No se inventa ni se
# amplia de memoria: un modelo que no este aqui no se usa.
MODELOS = {
    "nano_banana_pro": {
        "nombre": "Nano Banana Pro",
        "proveedor_origen": "Google",
        "aspect_ratios": ("1:1", "3:2", "2:3", "4:3", "3:4", "4:5", "5:4", "9:16", "16:9", "21:9"),
        "resoluciones": ("1k", "2k", "4k"),
        "texto_fiable": True,
        "_por_que": ("Es el unico del catalogo verificado que declara a la vez "
                     "'text-rendering' y 9:16. LegalMente monta texto juridico "
                     "exacto sobre la imagen: un modelo que deforma letras no "
                     "sirve, por bonito que sea el fondo."),
    },
    "gpt_image_2": {
        "nombre": "GPT Image 2",
        "proveedor_origen": "OpenAI",
        "aspect_ratios": ("1:1", "4:3", "3:4", "16:9", "21:9", "9:16", "3:2", "2:3"),
        "resoluciones": ("1k", "2k", "4k"),
        "texto_fiable": True,
        "_por_que": "Alternativa con tipografia fiable y edicion.",
    },
    "nano_banana": {
        "nombre": "Nano Banana",
        "proveedor_origen": "Google",
        "aspect_ratios": ("1:1", "3:2", "2:3", "4:3", "3:4", "4:5", "5:4", "9:16", "16:9", "21:9"),
        "resoluciones": (),
        "texto_fiable": False,
        "_por_que": "Economico, para exploracion de escena. NO para texto montado.",
    },
    "soul_2": {
        "nombre": "Higgsfield Soul 2.0",
        "proveedor_origen": "Higgsfield",
        "aspect_ratios": ("1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"),
        "resoluciones": ("1.5k", "2k"),
        "texto_fiable": False,
        "_por_que": "Editorial realista. Buen fondo, tipografia no fiable.",
    },
}

MODELO_POR_DEFECTO = "nano_banana_pro"

# Estados del despacho. Ninguno significa "imagen aprobada".
PENDIENTE_DE_DESPACHO = "PENDING_MCP_DISPATCH"
SIN_CREDITOS = "PROVIDER_NO_CREDITS"
GATE_CERRADO = "GATE_CERRADO"


@dataclass(frozen=True)
class EstadoDeCuenta:
    """Lo que se sabe de la cuenta. Se pasa desde fuera, nunca se adivina."""
    creditos: int = 0
    plan: str = "free"
    unlim_disponible: bool = False

    def puede_generar(self):
        return self.creditos > 0 or self.unlim_disponible


class HiggsfieldProvider(ImageProvider):
    """Prepara peticiones para el conector. No genera por si mismo.

    `despachador` es la funcion que un agente con el conector inyecta para
    ejecutar de verdad. Sin ella, el proveedor devuelve el despacho pendiente y
    lo dice: no simula un resultado.
    """

    id = "higgsfield"

    def __init__(self, modelo=MODELO_POR_DEFECTO, cuenta=None, despachador=None):
        if modelo not in MODELOS:
            raise ProviderError(
                f"modelo desconocido: {modelo!r}. El catalogo esta verificado "
                f"contra la API y no se amplia de memoria: {sorted(MODELOS)}")
        self.modelo = modelo
        self.cuenta = cuenta or EstadoDeCuenta()
        self._despachador = despachador

    def capabilities(self):
        m = MODELOS[self.modelo]
        return ProviderCapabilities(
            provider_id=self.id,
            aspect_ratios=m["aspect_ratios"],
            supports_negative_prompt=True,
            supports_reference_image=True,
            supports_editing=self.modelo in ("gpt_image_2", "nano_banana", "nano_banana_pro"),
            supports_reliable_text=m["texto_fiable"],
            supports_seed=False,
            supports_transparency=False,
            max_width=4096,
            max_height=4096,
        )

    def construir_peticion(self, request):
        """Traduce la peticion normalizada al vocabulario del conector.

        Toda la traduccion vive aqui. El dominio no sabe que existe Higgsfield.
        """
        payload = {
            "model": self.modelo,
            "prompt": request.prompt,
            "aspect_ratio": request.aspect_ratio,
        }
        if getattr(request, "negative_prompt", ""):
            payload["negative_prompt"] = request.negative_prompt
        if MODELOS[self.modelo]["resoluciones"]:
            payload["resolution"] = "2k"
        return payload

    def generate(self, request, gate_arte="CERRADO"):
        """Prepara o ejecuta. Nunca inventa una imagen que no existe.

        `gate_arte` es obligatorio y por defecto CERRADO: un proveedor al que se
        le olvide preguntarlo no genera nada.
        """
        def _fallo(error, notas, payload=None):
            return GenerationResult(
                provider_id=self.id, model=self.modelo, ok=False,
                image_bytes=b"", width=0, height=0, mime_type="",
                seed=None, error=error,
                raw_meta={"notas": notas, "payload": payload or {}})

        if gate_arte != "ABIERTO":
            return _fallo(GATE_CERRADO,
                          ["el gate de arte esta CERRADO: no se prepara ni se genera "
                           "arte de un claim sin verificar, haya creditos o no"])

        payload = self.construir_peticion(request)

        if not self.cuenta.puede_generar():
            return _fallo(SIN_CREDITOS,
                          [f"cuenta sin capacidad de generacion: creditos="
                           f"{self.cuenta.creditos}, plan={self.cuenta.plan!r}, "
                           f"unlim={self.cuenta.unlim_disponible}",
                           "peticion preparada y valida; falta presupuesto, no codigo"],
                          payload)

        if self._despachador is None:
            return _fallo(PENDIENTE_DE_DESPACHO,
                          ["peticion lista para el conector MCP; ningun agente la ha "
                           "despachado todavia"],
                          payload)

        datos = self._despachador(payload)
        if not datos:
            return _fallo("PROVIDER_EMPTY_RESULT",
                          ["el despachador no devolvio ninguna imagen"], payload)
        return GenerationResult(
            provider_id=self.id, model=self.modelo, ok=True,
            image_bytes=datos.get("image_bytes", b""),
            width=datos.get("width", 0), height=datos.get("height", 0),
            mime_type=datos.get("mime_type", "image/png"),
            seed=None, error="",
            raw_meta={"notas": [f"generada con {MODELOS[self.modelo]['nombre']}"],
                      "payload": payload, "url": datos.get("url", "")})


def modelo_recomendado_para(lleva_texto_montado):
    """Que modelo toca segun lo que la pieza necesita de verdad.

    LegalMente monta texto juridico exacto sobre la imagen. Cuando ese texto va
    dentro del render, el modelo tiene que renderizar letras fiables; si el texto
    se compone despues, el modelo solo tiene que dar buena escena.
    """
    return MODELO_POR_DEFECTO if lleva_texto_montado else "soul_2"
