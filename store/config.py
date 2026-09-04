"""Configuracion del almacen canonico. Nunca simula una conexion.

Decision del fundador (2026-09-04): el almacen vive en un proyecto Supabase
PROPIO Y DEDICADO de LegalMente. El proyecto existente de la cuenta
`legallmente-alt` NO se reutiliza: pertenece a otra cuenta/contexto, esta
hibernado y no cuenta con decision expresa de reutilizacion.

Este modulo hace una sola cosa: decir si hay configuracion suficiente para
hablar con ese proyecto. Si no la hay, devuelve CONFIGURATION_REQUIRED y se
detiene. No abre conexiones, no reintenta contra un proyecto por defecto y no
inventa una URL: un almacen "que parece conectado" es peor que uno apagado,
porque invita a creer que lo que se leyo es real.

Ninguna credencial se escribe aqui ni se registra en ningun sitio: solo el
NOMBRE de la variable de entorno y, como mucho, si esta presente (booleano).
"""

import os
import re

CONFIGURACION_COMPLETA = "CONFIGURED"
CONFIGURACION_REQUERIDA = "CONFIGURATION_REQUIRED"

# Variables acordadas en la decision de arquitectura. Los nombres son los que
# el fundador fijo; no se renombran ni se aceptan alias silenciosos.
VAR_URL = "NEXT_PUBLIC_SUPABASE_URL"
VAR_ANON = "NEXT_PUBLIC_SUPABASE_ANON_KEY"
VAR_SERVICE_ROLE = "SUPABASE_SERVICE_ROLE_KEY"

# Para leer la vista publica basta la clave anonima. La clave de servicio SOLO
# la necesita el pipeline que escribe, y nunca debe llegar al navegador.
VARIABLES_DE_LECTURA = (VAR_URL, VAR_ANON)
VARIABLES_DE_ESCRITURA = (VAR_URL, VAR_SERVICE_ROLE)

# El proyecto de otra cuenta que la decision excluye expresamente. Se comprueba
# para que una variable copiada por inercia no convierta a LegalMente en
# dependiente de un proyecto ajeno sin que nadie lo note.
PROYECTO_EXCLUIDO = "mvyuimzcmgciwqfcsnwp"

_URL_VALIDA = re.compile(r"^https://[a-z0-9-]+\.supabase\.(co|in)/?$", re.IGNORECASE)


class ConfiguracionInvalida(Exception):
    """La configuracion existe pero no sirve. Nunca se degrada a 'sin configurar'."""


def _presente(nombre):
    return bool(str(os.environ.get(nombre) or "").strip())


def estado(modo="lectura", entorno=None):
    """Estado de configuracion para `modo` ('lectura' o 'escritura').

    Devuelve un dict con `estado`, `faltan` (nombres de variables ausentes) y
    `motivo`. Nunca devuelve la URL ni ninguna clave.
    """
    env = entorno if entorno is not None else os.environ
    requeridas = VARIABLES_DE_ESCRITURA if modo == "escritura" else VARIABLES_DE_LECTURA

    faltan = [v for v in requeridas if not str(env.get(v) or "").strip()]
    if faltan:
        return {
            "estado": CONFIGURACION_REQUERIDA,
            "modo": modo,
            "faltan": faltan,
            "motivo": (
                "faltan variables de entorno del proyecto Supabase dedicado de "
                f"LegalMente: {', '.join(faltan)}. Ver store/README.md, seccion "
                "'Procedimiento de configuracion'. No se intenta ninguna conexion."),
        }

    url = str(env.get(VAR_URL) or "").strip()
    if not _URL_VALIDA.match(url):
        raise ConfiguracionInvalida(
            f"{VAR_URL} no parece la URL de un proyecto Supabase "
            "(se esperaba https://<ref>.supabase.co). No se intenta ninguna conexion.")

    if PROYECTO_EXCLUIDO in url:
        raise ConfiguracionInvalida(
            "la URL apunta al proyecto Supabase de la cuenta legallmente-alt, que la "
            "decision de arquitectura del 2026-09-04 excluye expresamente. LegalMente "
            "necesita un proyecto propio y dedicado. No se intenta ninguna conexion.")

    return {"estado": CONFIGURACION_COMPLETA, "modo": modo, "faltan": [], "motivo": ""}


def listo(modo="lectura", entorno=None):
    """True solo si hay configuracion completa. Cualquier duda es False."""
    try:
        return estado(modo, entorno)["estado"] == CONFIGURACION_COMPLETA
    except ConfiguracionInvalida:
        return False


def cliente(modo="lectura", entorno=None):
    """Deliberadamente NO devuelve un cliente todavia.

    La decision del fundador autoriza disenar y preparar el cimiento, no
    conectar la base de datos. Devolver aqui un cliente a medias, o un doble
    que finge responder, es exactamente lo que el requisito 4 prohibe: no
    simular una conexion exitosa.

    Cuando se autorice conectar, este es el unico punto que cambia, y lo hara
    exigiendo `listo(modo)` antes de construir nada.
    """
    info = estado(modo, entorno)
    raise NotImplementedError(
        "La conexion al almacen no esta autorizada todavia (decision 2026-09-04: "
        "solo disenar y preparar). Estado de configuracion: "
        f"{info['estado']}. " + (info["motivo"] or ""))


def informe():
    """Texto legible para el CLI. Nunca imprime una credencial, solo si esta."""
    lineas = ["Almacen canonico — proyecto Supabase DEDICADO de LegalMente", ""]
    for var in (VAR_URL, VAR_ANON, VAR_SERVICE_ROLE):
        lineas.append(f"  {var:32} {'presente' if _presente(var) else 'AUSENTE'}")
    lineas.append("")
    for modo in ("lectura", "escritura"):
        try:
            info = estado(modo)
            detalle = info["estado"]
            if info["faltan"]:
                detalle += f" (faltan: {', '.join(info['faltan'])})"
        except ConfiguracionInvalida as exc:
            detalle = f"INVALIDA — {exc}"
        lineas.append(f"  {modo:10} {detalle}")
    lineas.append("")
    lineas.append("  La conexion no esta autorizada todavia: solo diseno y preparacion.")
    return "\n".join(lineas)


if __name__ == "__main__":
    print(informe())
