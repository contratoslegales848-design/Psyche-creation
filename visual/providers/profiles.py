"""Perfiles de proveedor de imagen. Un perfil es CONFIGURACION, no un vendor.

Por que existe este archivo: `HttpImageProvider` sabe hablar HTTP, pero cada
API tiene su propia autenticacion, su propio cuerpo y su propia ruta hacia los
bytes de la imagen. Antes eso estaba hardcodeado a la forma "compatible con
OpenAI" (cabecera `Authorization: Bearer`, cuerpo plano, imagen en
`data[0].b64_json`), asi que cualquier API con otra forma quedaba fuera sin
tocar codigo. Aqui se declara la forma; el adapter la ejecuta.

ESTADO DE VERIFICACION DE CADA PERFIL — leelo antes de usar uno:

  - `generic-http-image-v1`: forma generica compatible con OpenAI. VERIFICADA
    de extremo a extremo contra un servidor HTTP local en las pruebas de este
    repositorio (`test_cli_live_gate.py`). No garantiza que un vendor concreto
    la respete; garantiza que el adapter la ejecuta bien.

  - `gemini-3-pro-image`: PROPUESTO, **NO VERIFICADO CONTRA LA DOCUMENTACION
    OFICIAL**. El proxy de egress de este entorno bloquea `ai.google.dev` y
    `docs.cloud.google.com` (comprobado: EGRESS_BLOCKED en ambos), asi que la
    forma exacta de la peticion y de la respuesta NO se pudo leer de la fuente
    oficial. Lo que hay aqui es la forma que este repositorio ESPERA; puede
    estar desfasada o ser incorrecta.

    Que hacer antes de gastar creditos con el: correr `simulate --live` UNA vez
    con un prompt barato y mirar el error. Si el adapter responde
    "ninguna de las rutas declaradas por el perfil contiene imagen" te dira las
    claves de primer nivel que SI llegaron — con eso se corrige `response_paths`
    aqui, sin tocar codigo. Ese mensaje existe precisamente para este caso.

Ninguna credencial vive en este archivo: solo el NOMBRE de la variable de
entorno de la que se lee.
"""

import os

from .http_provider import HttpProviderConfig

VERIFICADO = "VERIFICADO_CONTRA_SERVIDOR_LOCAL"
NO_VERIFICADO = "PROPUESTO_NO_VERIFICADO_CONTRA_DOC_OFICIAL"


def _generico():
    return HttpProviderConfig(
        provider_id="generic-http-image-v1",
        endpoint=os.environ.get("LEGALMENTE_IMAGE_PROVIDER_ENDPOINT", ""),
        api_key_env="LEGALMENTE_IMAGE_PROVIDER_API_KEY",
        aspect_ratios=("9:16", "4:5"),
    )


def _gemini():
    """Perfil propuesto para la familia `generateContent` de Gemini.

    El endpoint por defecto se puede sobreescribir con
    LEGALMENTE_IMAGE_PROVIDER_ENDPOINT: si la ruta o el nombre del modelo
    cambian, se ajusta por entorno sin tocar este archivo.
    """
    modelo = os.environ.get("LEGALMENTE_GEMINI_MODEL", "gemini-3-pro-image")
    por_defecto = (f"https://generativelanguage.googleapis.com/v1beta/models/"
                   f"{modelo}:generateContent")
    return HttpProviderConfig(
        provider_id="gemini-3-pro-image",
        endpoint=os.environ.get("LEGALMENTE_IMAGE_PROVIDER_ENDPOINT") or por_defecto,
        model=modelo,
        api_key_env="LEGALMENTE_GEMINI_API_KEY",
        # Gemini autentica por cabecera propia, no con Bearer.
        auth_header="x-goog-api-key",
        auth_prefix="",
        payload_style="gemini",
        # La imagen viaja como parte inline dentro del primer candidato. Se
        # declaran variantes en camelCase y snake_case porque distintas
        # versiones de la API han usado ambas.
        response_paths=(
            "candidates.0.content.parts.*.inlineData.data",
            "candidates.0.content.parts.*.inline_data.data",
            "candidates.*.content.parts.*.inlineData.data",
        ),
        # No expone prompt negativo propio: el adapter lo concatena al texto.
        supports_negative_prompt=True,
        supports_seed=False,
        aspect_ratios=("9:16", "4:5"),
    )


# id -> (constructor, estado de verificacion, nota corta)
PERFILES = {
    "generic-http-image-v1": (
        _generico, VERIFICADO,
        "Forma compatible con OpenAI: Bearer + cuerpo plano + data[0].b64_json."),
    "gemini-3-pro-image": (
        _gemini, NO_VERIFICADO,
        "Gemini generateContent. Forma NO confirmada contra la doc oficial "
        "(ai.google.dev bloqueado por el proxy de egress de este entorno)."),
}

POR_DEFECTO = "generic-http-image-v1"


def cargar(provider_id=None):
    """Construye el config del perfil pedido. Lanza ValueError si no existe.

    Se construye en cada llamada, no en import: el endpoint y el modelo salen
    de variables de entorno, y un perfil congelado en import ignoraria una
    credencial exportada despues.
    """
    pid = provider_id or POR_DEFECTO
    if pid not in PERFILES:
        raise ValueError(
            f"perfil de proveedor desconocido: {pid!r}. Disponibles: {sorted(PERFILES)}")
    constructor, _estado, _nota = PERFILES[pid]
    return constructor()


def estado_de_verificacion(provider_id):
    if provider_id not in PERFILES:
        raise ValueError(f"perfil de proveedor desconocido: {provider_id!r}")
    _c, estado, nota = PERFILES[provider_id]
    return estado, nota


def listar():
    """[(id, estado, nota)] para que el CLI lo imprima sin conocer el detalle."""
    return [(pid, estado, nota) for pid, (_c, estado, nota) in sorted(PERFILES.items())]
