"""Cola de aprobacion: que la decision humana sea barata, no que desaparezca.

(El archivo se llama cola.py y no queue.py a proposito: queue.py habria
sombreado el modulo estandar de Python para todo lo que se importe desde aqui.)

El problema real. Hoy cada pieza espera su propia aprobacion, y mientras espera
no avanza nada: ni el arte, ni el copy, ni la siguiente pieza. El fundador es un
cuello de botella de una sola persona y el flujo se para entero en el.

La solucion NO es quitar la aprobacion. Es separar dos cosas que estaban pegadas:

    PREPARAR   todo lo que no requiere juicio humano. Lo hace el agente, hasta
               el ultimo milimetro antes de la decision. Puede llevar un lote
               del 0 % al 99 % sin preguntar nada.

    DECIDIR    el juicio humano. Sigue siendo indispensable, pero deja de ser
               veinte decisiones dispersas para ser UNA sobre un lote revisable.

Lo que este modulo NO hace, y no puede hacer aunque se le pida:

  - No aprueba. No hay ninguna funcion que ponga APROBADO.
  - No abre gates. El gate lo abre la cadena de publicacion existente, ligada
    por hash, y solo despues de una decision humana registrada.
  - No infiere consentimiento del silencio. Una solicitud sin responder caduca;
    no se convierte en un si.

La aprobacion en lote es una decision informada sobre varias piezas a la vez,
no una aprobacion generica ni un cheque en blanco: cada solicitud lleva el hash
del contenido exacto, y si el contenido cambia despues, la decision deja de
valer para el.

Sin red. Determinista.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parent
SOLICITUDES_DIR = AQUI / "solicitudes"
DECISIONES_DIR = AQUI / "decisiones"

# Estados de una solicitud. Solo los dos primeros los produce el agente.
PREPARADA = "PREPARADA"                # lista para que un humano decida
INCOMPLETA = "INCOMPLETA"              # falta trabajo del agente; no molestar todavia
DECIDIDA = "DECIDIDA"                  # existe decision humana registrada
CADUCADA = "CADUCADA"                  # el contenido cambio tras preparar la solicitud

# Tipos de decision que un humano puede tomar. No hay ninguno mas, y ninguno
# significa "aprobado por omision".
DECISIONES_VALIDAS = ("APROBADA", "RECHAZADA", "APROBADA_CON_CAMBIOS")

# Dias tras los cuales una solicitud sin responder se considera caducada. El
# silencio nunca es un si: caducar es lo contrario de auto-aprobar.
CADUCIDAD_DIAS = 30


def _ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def hash_de_contenido(payload):
    """Hash canonico del contenido exacto sobre el que se pide decision.

    Es lo que impide que una aprobacion viaje a un contenido distinto del que se
    reviso: si el texto cambia una coma, el hash cambia y la decision deja de
    aplicar.
    """
    canon = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def _falta_para_decidir(item):
    """Que le falta a un item para que preguntar tenga sentido.

    Preguntar antes de tiempo es peor que no preguntar: gasta la atencion del
    fundador en algo que el agente todavia podia resolver solo.
    """
    faltan = []
    if not item.get("contenido_exacto"):
        faltan.append("el contenido exacto todavia no esta redactado")
    if not item.get("fuentes"):
        faltan.append("no hay ninguna fuente declarada")
    else:
        sin_verificar = [f.get("id", "?") for f in item["fuentes"]
                         if not (f.get("verificacion_fuente") or {}).get("texto_exacto_consultado")]
        if sin_verificar:
            faltan.append(f"fuentes sin texto leido: {sin_verificar}")
    if item.get("alcance") in (None, "", "NO_DETERMINADO"):
        faltan.append("el alcance jurisdiccional sigue sin determinar")
    return faltan


def preparar_solicitud(lote_id, items, preparado_por="agente"):
    """Construye UNA solicitud de decision sobre un lote entero.

    Devuelve la solicitud. No la guarda y no decide nada: solo deja el trabajo
    hecho hasta donde el agente puede llegar.
    """
    preparados, incompletos = [], []
    for item in items:
        faltan = _falta_para_decidir(item)
        registro = {
            "id": item.get("id"),
            "titulo": item.get("titulo", ""),
            "contenido_hash": hash_de_contenido(item),
            "falta_para_decidir": faltan,
        }
        (incompletos if faltan else preparados).append(registro)

    estado = PREPARADA if preparados and not incompletos else INCOMPLETA
    return {
        "lote_id": lote_id,
        "creada": _ahora(),
        "preparada_por": preparado_por,
        "estado": estado,
        "items_listos": preparados,
        "items_incompletos": incompletos,
        "decision_requerida": bool(preparados),
        "caducidad_dias": CADUCIDAD_DIAS,
        # Invariantes. Ninguna funcion de este modulo los puede cambiar.
        "aprobada": False,
        "gate_arte": "CERRADO",
        "publicacion": "NOT_PUBLISHED",
        "_nota": ("Preparar no es aprobar. Esta solicitud describe trabajo "
                  "terminado por el agente y pendiente de juicio humano. "
                  "El silencio no la aprueba: la caduca."),
    }


def cargar_decision(lote_id, decisiones_dir=None):
    """Lee la decision humana de un lote, si existe. Nunca la fabrica."""
    d = Path(decisiones_dir) if decisiones_dir else DECISIONES_DIR
    ruta = d / f"{lote_id}.json"
    if not ruta.is_file():
        return None
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def evaluar_decision(solicitud, decision):
    """Comprueba que una decision humana es aplicable a esta solicitud.

    Fail-closed en todos los sentidos: sin decision no hay aprobacion; con
    decision mal formada tampoco; y con el contenido cambiado desde que se
    reviso, la decision caduca en vez de arrastrarse.
    """
    problemas = []
    if decision is None:
        return {"aplicable": False, "estado": solicitud["estado"],
                "problemas": ["no existe decision humana registrada para este lote"],
                "items_aprobados": []}

    if decision.get("decision") not in DECISIONES_VALIDAS:
        problemas.append(
            f"decision invalida: {decision.get('decision')!r} "
            f"(una de {list(DECISIONES_VALIDAS)})")
    if not str(decision.get("decidida_por", "")).strip():
        problemas.append("la decision no declara quien la tomo")
    if not str(decision.get("fecha", "")).strip():
        problemas.append("la decision no declara fecha")

    # El control central: la decision solo vale para el contenido que se reviso.
    hashes_solicitud = {i["contenido_hash"] for i in solicitud["items_listos"]}
    hashes_decision = set(decision.get("contenido_hashes") or [])
    if not hashes_decision:
        problemas.append("la decision no declara sobre que hashes de contenido recae")
    huerfanos = hashes_decision - hashes_solicitud
    if huerfanos:
        problemas.append(
            f"la decision recae sobre contenido que no esta en esta solicitud: "
            f"{sorted(huerfanos)}")
    cambiados = hashes_solicitud - hashes_decision
    if cambiados:
        problemas.append(
            f"estos items cambiaron desde que se reviso el lote y quedan fuera "
            f"de la decision: {sorted(cambiados)}")

    aprobados = []
    if not problemas and decision["decision"] in ("APROBADA", "APROBADA_CON_CAMBIOS"):
        aprobados = [i["id"] for i in solicitud["items_listos"]
                     if i["contenido_hash"] in hashes_decision]

    return {
        "aplicable": not problemas,
        "estado": DECIDIDA if not problemas else CADUCADA,
        "decision": decision.get("decision"),
        "decidida_por": decision.get("decidida_por"),
        "problemas": problemas,
        "items_aprobados": aprobados,
        # Aun aprobada, esto NO publica. Abrir el gate y publicar siguen siendo
        # pasos posteriores de la cadena de publicacion, con sus propias reglas.
        "gate_arte": "CERRADO",
        "publicacion": "NOT_PUBLISHED",
        "_nota": ("Una decision aprobatoria habilita PRODUCIR el arte del lote. "
                  "No abre el gate por si sola ni autoriza publicar."),
    }


def resumen(solicitudes):
    """Cuanto trabajo esta esperando a una persona, y cuanto no."""
    listos = sum(len(s["items_listos"]) for s in solicitudes)
    incompletos = sum(len(s["items_incompletos"]) for s in solicitudes)
    return {
        "solicitudes": len(solicitudes),
        "items_esperando_decision_humana": listos,
        "items_que_todavia_puede_avanzar_el_agente": incompletos,
        "decisiones_humanas_necesarias": sum(
            1 for s in solicitudes if s["estado"] == PREPARADA),
        "_lectura": ("Cada 'decision humana necesaria' cubre un lote entero. "
                     "Los items incompletos NO deben llevarse a una persona: "
                     "todavia hay trabajo de agente por hacer."),
    }
