"""Gate fail-closed de proveedores prohibidos.

Hueco real encontrado al reconciliar contra `legallmente-alt/legalmente-web`
rama `chatgpt/image-generator-reconciliation-v2-2026-09-13`
(`src/lib/image-generator/runtime.ts`): esa rama bloquea Higgsfield ANTES de
cualquier llamada de generación, sin fallback silencioso —

    const blockedProviderKey = ["higgs", "field"].join("");
    ...
    if (provider.includes(blockedProviderKey)) errors.push(...)

El lado Python (`provider_preflight.py`) sólo comprueba credenciales y
capacidades — nunca comprueba si el proveedor está PROHIBIDO. "No usar
Higgsfield" vive como texto en el Índice maestro v18 y en CLAUDE.md §6/§7,
nunca como control ejecutable. Este módulo lo cierra: mismo principio,
implementación propia en Python, no un port literal del TypeScript.

Fail-closed: la comprobación se hace ANTES de construir cualquier solicitud
al proveedor, y un proveedor prohibido nunca cae a otro en silencio — el
llamador decide qué hacer con el error, este módulo sólo se niega a decir
que está permitido.
"""

import re

# Coincide por subcadena normalizada, no por igualdad exacta: "Higgsfield API
# v3", "higgsfield.ai" y "HIGGS_FIELD" deben bloquearse igual. Los proveedores
# no incluidos aquí no están "aprobados" por omisión — sólo no están
# prohibidos; la aprobación real la da la configuración del provider
# (`provider_preflight.py`), este módulo únicamente veta.
PROVEEDORES_PROHIBIDOS = frozenset({
    "higgsfield",
})


class ProviderGateError(ValueError):
    """Un proveedor prohibido intentó usarse. Nunca se atrapa para reintentar
    con otro proveedor en silencio — eso sería el fallback que el mandato
    prohíbe explícitamente."""


def _colapsa(texto):
    """Minúsculas y sólo caracteres alfanuméricos, nada más. 'Higgs Field',
    'higgs-field', 'higgsfield.ai' y 'HIGGS_FIELD' deben comparar igual.

    Deliberadamente NO usa `memory.normaliza()`: esa función está pensada
    para valores de taxonomía y descarta el token entero si no es alfanumérico
    puro (así "higgs-field.ai" perdía la palabra "field" completa, porque
    "field.ai" no es alnum) — correcto para nombres de familia/materia,
    equivocado para cadenas libres de proveedor/modelo con puntos o
    versiones. Aquí sólo se despoja de separadores, nunca se pierde una
    palabra entera."""
    return re.sub(r"[^a-z0-9]", "", texto.lower())


def proveedor_prohibido(nombre_proveedor, modelo=""):
    """Devuelve el nombre prohibido que coincide, o cadena vacía si no hay
    coincidencia. Nunca lanza — quien necesita fail-closed llama a
    `verificar_proveedor_permitido`."""
    combinado = _colapsa(f"{nombre_proveedor} {modelo}")
    if not combinado:
        return ""
    for prohibido in PROVEEDORES_PROHIBIDOS:
        if _colapsa(prohibido) in combinado:
            return prohibido
    return ""


def verificar_proveedor_permitido(nombre_proveedor, modelo=""):
    """Fail-closed: lanza ProviderGateError si el proveedor está prohibido.
    Devuelve True en cualquier otro caso — este gate nunca aprueba
    credenciales ni capacidades, sólo veta lo explícitamente prohibido."""
    coincidencia = proveedor_prohibido(nombre_proveedor, modelo)
    if coincidencia:
        raise ProviderGateError(
            f"proveedor prohibido para LegalMente: {nombre_proveedor!r} "
            f"(modelo {modelo!r}) coincide con {coincidencia!r}. "
            "Ver Índice maestro v18: 'No usar Higgsfield'. Sin fallback silencioso: "
            "corrige la configuración del proveedor, no reintentes con otro sin decirlo.")
    return True
