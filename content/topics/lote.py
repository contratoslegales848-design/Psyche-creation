"""Diversidad editorial de un lote, y memoria contra lo ya producido.

Dos controles que se necesitan mutuamente y que este modulo mantiene juntos
porque separados se enganan solos:

  DIVERSIDAD  Un lote de diez piezas no puede ser diez veces la misma forma.
              Variar el diseno no convierte contenido repetido en contenido
              nuevo, y variar la forma tampoco: por eso la comprobacion mira
              tambien concepto, angulo, situacion humana y utilidad.

  MEMORIA     Comprobar que los identificadores del lote nuevo son distintos
              ENTRE SI no demuestra nada. Lo que hay que comprobar es que no
              repiten lo que ya existe. Y cuando el inventario no puede
              consultarse, la respuesta honesta no es "es nuevo": es
              INVENTORY_NOT_CHECKED.

Ninguno de los dos aprueba nada. Organizan un lote; no acreditan derecho, no
abren gates y no autorizan arte ni publicacion.

Sin red. Determinista.
"""

import json
import sys
from collections import Counter
from pathlib import Path

import transversality as T

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parent.parent

# Formas editoriales admitidas. La version anterior de este motor solo conocia
# cuatro arquetipos cerrados, y eso empujaba a forzar cualquier idea dentro de
# ellos — o a descartarla. Una marca de educacion juridica necesita mas registros
# que "diferencias, mito, consecuencia, listado".
FORMAS_EDITORIALES = (
    "FRASE_O_MAXIMA",
    "REFLEXION",
    "PREGUNTA_COMUN",
    "APRENDIZAJE",
    "ERROR_FRECUENTE",
    "CONCEPTO",
    "DIFERENCIAS",
    "MITO",
    "CONSECUENCIA",
    "PASOS",
    "GUIA_O_CHECKLIST",
    "SITUACION_HUMANA",
    "PRESENTACION_INSTITUCIONAL",
)

# Soportes. Se separan de la forma editorial a proposito: el mismo contenido en
# carrusel y en short NO es contenido nuevo, y mezclarlos en un solo eje habria
# permitido justificar repeticion cambiando de soporte.
SOPORTES = ("PIEZA_ESTATICA", "CARRUSEL", "SHORT", "COPY")

# Reglas por defecto para un lote de diez.
LOTE_ESTANDAR = 10
MINIMO_FORMAS_DISTINTAS = 5
MAXIMO_POR_FORMA = 2


def _dim(item):
    """Las cuatro dimensiones cuya coincidencia simultanea es repeticion.

    Coincidir en una o dos es normal y hasta deseable: una materia se construye
    volviendo sobre el mismo concepto. Coincidir en las cuatro significa que la
    pieza nueva no anade nada que la anterior no dijera ya.
    """
    return (
        str(item.get("concepto", "")).strip().casefold(),
        str(item.get("angulo", "")).strip().casefold(),
        str(item.get("situacion_humana", "")).strip().casefold(),
        str(item.get("utilidad", "")).strip().casefold(),
    )


def evaluar_diversidad(lote):
    """Dictamen de diversidad editorial de un lote. Nunca lanza: informa."""
    problemas = []
    formas = [i.get("forma_editorial") for i in lote]

    desconocidas = sorted({f for f in formas if f not in FORMAS_EDITORIALES})
    if desconocidas:
        problemas.append(f"formas editoriales fuera del vocabulario: {desconocidas}")

    distintas = len(set(formas))
    if len(lote) >= LOTE_ESTANDAR and distintas < MINIMO_FORMAS_DISTINTAS:
        problemas.append(
            f"solo {distintas} formas editoriales distintas; el minimo para un "
            f"lote de {LOTE_ESTANDAR} es {MINIMO_FORMAS_DISTINTAS}")

    for forma, n in Counter(formas).items():
        if n > MAXIMO_POR_FORMA:
            problemas.append(
                f"la forma {forma!r} aparece {n} veces; el maximo es "
                f"{MAXIMO_POR_FORMA} salvo serie expresamente solicitada")

    vistos = {}
    for i, item in enumerate(lote):
        clave = _dim(item)
        if clave in vistos:
            problemas.append(
                f"posiciones {vistos[clave]} y {i} coinciden en concepto, angulo, "
                "situacion humana y utilidad: es la misma pieza con otra ropa")
        else:
            vistos[clave] = i

    return {
        "tamano": len(lote),
        "formas_distintas": distintas,
        "reparto": dict(Counter(formas)),
        "diverso": not problemas,
        "problemas": problemas,
        # Invariante: organizar un lote no acredita nada de lo que contiene.
        "aprueba_claims": False,
        "abre_gate": False,
        "autoriza_publicacion": False,
    }


# ---------------------------------------------------------------------------
# Memoria: contra lo que ya existe, no contra el propio lote.
# ---------------------------------------------------------------------------

# Estados del inventario.
#
# CORRECCION 2026-09-04. La version anterior devolvia INVENTORY_CANONICAL cuando
# lograba importar visual/inventory.py. Era falso por dos motivos, y el error era
# grave porque producia justo la afirmacion que el fundador teme:
#
#   1. CLAUDE.md §2 situa el inventario de publicaciones y la matriz de contenido
#      en Google Drive. Ninguna de las tres fuentes que se leian —content/,
#      claim-packets/ y visual/inventory.py— esta en Drive: las tres son locales
#      al repositorio. Llamar canonico a eso es apropiarse de una autoridad que
#      vive en otro sitio.
#   2. visual/inventory.py ni siquiera aporta identidad tematica: sus entradas
#      llegaban con concepto, angulo, utilidad y conexion juridica vacios, asi que
#      no podian coincidir con ningun candidato ni aunque el tema fuera el mismo.
#
# El resultado era que los 24 candidatos salian con
# puede_declararse_nuevo_globalmente=true sin haber mirado nunca lo publicado.
INVENTARIO_LOCAL = "INVENTORY_LOCAL"
# El arbol del repositorio leido por completo. Es mas que LOCAL parcial y MENOS
# que canonico: demuestra que no hay choque AQUI, y nada sobre lo publicado.
INVENTARIO_REPO_COMPLETO = "INVENTORY_REPO_COMPLETE"
# Reservado. Solo lo alcanza un inventario que incorpore explicitamente la fuente
# canonica de publicaciones de Drive, o una exportacion identificada y
# verificable de ella. Este modulo NO la consulta ni la copia: la recibe.
INVENTARIO_CANONICO = "INVENTORY_CANONICAL"
INVENTARIO_INCOMPLETO = "INVENTORY_INCOMPLETE"

# Solo este estado permite afirmar novedad frente a TODO lo publicado. Ninguna
# lectura del repositorio lo alcanza, por completa que sea.
ESTADOS_QUE_PERMITEN_NOVEDAD_GLOBAL = (INVENTARIO_CANONICO,)

# Frontera de entrada, no infraestructura. Un inventario solo puede declararse
# canonico si viene acompanado de la identificacion de su origen en Drive: id del
# archivo, fecha de exportacion y quien la hizo. Sin eso, se degrada.
CAMPOS_DE_AUTORIDAD_CANONICA = ("drive_file_id", "exportado_en", "exportado_por")


def evaluar_autoridad_canonica(procedencia):
    """Decide si una procedencia declarada basta para el estado canonico.

    Es deliberadamente estricta y no consulta nada: comprueba que quien inyecta
    el inventario haya dicho de donde sale. Un inventario sin origen declarado no
    es canonico aunque lo diga su etiqueta.
    """
    if not isinstance(procedencia, dict):
        return False, ["no se declaro procedencia del inventario"]
    faltan = [c for c in CAMPOS_DE_AUTORIDAD_CANONICA
              if not str(procedencia.get(c, "")).strip()]
    if faltan:
        return False, [f"la procedencia no declara: {faltan}"]
    return True, []


def cargar_inventario():
    """Lo ya producido o pendiente, leido de las fuentes reales del repositorio.

    Devuelve (entradas, estado, fuentes). El estado distingue tres situaciones
    que no son equivalentes:

      LOCAL       se leyo el arbol de este repositorio y nada mas. Sirve para
                  detectar choques dentro del repo; NO para afirmar que un
                  concepto no existe en el canon de produccion.
      CANONICO    se leyo ademas el inventario de produccion (visual/inventory).
      INCOMPLETO  alguna fuente fallo. La respuesta honesta no es "es nuevo".
    """
    entradas = []
    fuentes = {"contenido": False, "packets": False, "inventario_produccion": False}
    fallos = []

    dir_contenido = REPO / "content"
    if dir_contenido.is_dir():
        for ruta in sorted(dir_contenido.glob("*.json")):
            try:
                datos = json.loads(ruta.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                fallos.append(f"content/{ruta.name}: {exc}")
                continue
            tax = datos.get("taxonomia") or {}
            if tax:
                entradas.append({
                    "origen": f"content/{ruta.name}",
                    "ambito": INVENTARIO_LOCAL,
                    "concepto": tax.get("concepto", ""),
                    "materia": tax.get("materia", ""),
                    "situacion_humana": tax.get("situacion_humana", ""),
                    "angulo": tax.get("angulo", ""),
                    "utilidad": tax.get("utilidad", ""),
                    "forma_editorial": tax.get("content_type", ""),
                })
        fuentes["contenido"] = True

    dir_packets = REPO / "content" / "claim-packets"
    if dir_packets.is_dir():
        for ruta in sorted(dir_packets.glob("*.json")):
            try:
                datos = json.loads(ruta.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                fallos.append(f"claim-packets/{ruta.name}: {exc}")
                continue
            for claim in datos.get("claims", []):
                entradas.append({
                    "origen": f"claim-packets/{ruta.name}",
                    "ambito": INVENTARIO_LOCAL,
                    "concepto": str(claim.get("concepto", "") or datos.get("tema", "")),
                    "materia": str(datos.get("materia", "")),
                    "situacion_humana": "", "angulo": "", "utilidad": "",
                    "forma_editorial": "",
                })
        fuentes["packets"] = True

    try:
        sys.path.insert(0, str(REPO / "visual"))
        import inventory as _inv  # noqa: PLC0415
        for reg in _inv.build_readiness():
            entradas.append({
                "origen": f"inventario/{reg.piece_id}",
                "ambito": INVENTARIO_CANONICO,
                "concepto": "", "materia": "", "situacion_humana": "",
                "angulo": "", "utilidad": "", "forma_editorial": "",
                "piece_id": reg.piece_id,
                "content_ids": list(reg.content_ids),
            })
        fuentes["inventario_produccion"] = True
    except Exception as exc:  # noqa: BLE001
        fallos.append(f"inventario de produccion: {exc}")

    # Este loader NUNCA devuelve INVENTARIO_CANONICO, y no es una omision: no
    # lee Drive. Importar visual/inventory.py con exito solo demuestra que el
    # repositorio esta completo, no que se haya mirado lo publicado.
    if fallos or not (fuentes["contenido"] and fuentes["packets"]):
        estado = INVENTARIO_INCOMPLETO
    elif fuentes["inventario_produccion"]:
        estado = INVENTARIO_REPO_COMPLETO
    else:
        estado = INVENTARIO_LOCAL

    return entradas, estado, {
        "fuentes": fuentes,
        "fallos": fallos,
        "alcance": "solo este repositorio",
        "no_consultado": ("inventario de publicaciones y matriz de contenido de "
                          "Google Drive (CLAUDE.md §2)"),
    }


# Dimensiones sustantivas. Coincidir en TODAS es repeticion; diferir en una sola
# de forma demostrable es ramificacion legitima. La forma editorial y el soporte
# NO estan aqui a proposito: cambiar de formato o de envase no aporta
# conocimiento nuevo, y meterlos habria dado una coartada para repetir.
DIMENSIONES_SUSTANTIVAS = ("angulo", "situacion_humana", "utilidad", "conexion_juridica")


def _sustantivo(item):
    return tuple(str(item.get(d, "")).strip().casefold() for d in DIMENSIONES_SUSTANTIVAS)


def aportacion_nueva(candidato, existente):
    """En que dimensiones sustantivas difiere el candidato de lo ya producido.

    Devuelve la lista de dimensiones con aportacion DEMOSTRABLE: no basta con que
    el campo sea distinto, tiene que estar relleno en el candidato. Un campo
    vacio frente a uno lleno no es una aportacion, es una omision.
    """
    nuevas = []
    for d in DIMENSIONES_SUSTANTIVAS:
        valor = str(candidato.get(d, "")).strip().casefold()
        previo = str(existente.get(d, "")).strip().casefold()
        if valor and valor != previo:
            nuevas.append(d)
    return nuevas


def evaluar_novedad(candidato, inventario=None, estado_inventario=None,
                    procedencia_canonica=None):
    """Que aporta este candidato frente al inventario, y con que alcance se sabe.

    El resultado NO es un si/no. Son tres cosas distintas que antes estaban
    mezcladas:

      - si el CONCEPTO ya esta ocupado (dato, no veredicto);
      - si aun asi hay APORTACION NUEVA demostrable, que legitima ramificar;
      - hasta donde llega la comprobacion, segun el estado del inventario.

    Reutilizar un concepto es normal y deseable: una materia se construye
    volviendo sobre el mismo concepto desde otro angulo, otra situacion humana,
    otra utilidad u otra conexion juridica. Lo que no vale es volver sobre el
    mismo concepto sin cambiar ninguna de esas cuatro cosas.
    """
    if inventario is None or estado_inventario is None:
        inventario, estado_inventario, _ = cargar_inventario()

    # Unica via hacia el estado canonico: que quien inyecta el inventario
    # acredite su origen en Drive. Etiquetarlo canonico sin procedencia no basta,
    # y degradarlo aqui es lo que impide que una etiqueta se convierta en
    # autoridad.
    degradacion = []
    if estado_inventario == INVENTARIO_CANONICO:
        acreditado, problemas = evaluar_autoridad_canonica(procedencia_canonica)
        if not acreditado:
            estado_inventario = INVENTARIO_REPO_COMPLETO
            degradacion = problemas

    concepto = str(candidato.get("concepto", "")).strip().casefold()
    clave = _sustantivo(candidato)

    ocupaciones, repeticiones, ramificaciones = [], [], []
    for e in inventario:
        if not concepto or str(e.get("concepto", "")).strip().casefold() != concepto:
            continue
        ocupaciones.append(e["origen"])
        if _sustantivo(e) == clave:
            repeticiones.append(e["origen"])
        else:
            nuevas = aportacion_nueva(candidato, e)
            if nuevas:
                ramificaciones.append({"origen": e["origen"], "aporta_en": nuevas})

    alcance_ok = estado_inventario in ESTADOS_QUE_PERMITEN_NOVEDAD_GLOBAL

    if repeticiones:
        veredicto, motivo = "REPETICION", (
            "coincide en todas las dimensiones sustantivas con contenido ya "
            "existente: es la misma pieza con otra ropa")
    elif ocupaciones and ramificaciones:
        veredicto, motivo = "RAMIFICACION", (
            "el concepto ya existe, pero hay aportacion nueva demostrable en "
            + ", ".join(sorted({d for r in ramificaciones for d in r["aporta_en"]})))
    elif ocupaciones:
        veredicto, motivo = "SIN_APORTACION_DEMOSTRABLE", (
            "el concepto ya existe y el candidato no rellena ninguna dimension "
            "sustantiva que lo diferencie")
    else:
        veredicto, motivo = "NO_ENCONTRADO_EN_EL_REPOSITORIO", (
            "el concepto no aparece en el inventario consultado; eso NO significa "
            "que no se haya publicado ya fuera del repositorio")

    return {
        "candidato": candidato.get("id"),
        "estado_inventario": estado_inventario,
        "veredicto": veredicto,
        "motivo": motivo,
        "concepto_ocupado_en": ocupaciones,
        "repite_a": repeticiones,
        "ramifica_sobre": ramificaciones,
        # El alcance de lo que se acaba de comprobar. Con inventario LOCAL o
        # INCOMPLETO, "no aparece" significa "no aparece AQUI", nunca "no existe".
        "puede_declararse_nuevo_globalmente": (
            alcance_ok and veredicto in ("NO_ENCONTRADO_EN_EL_REPOSITORIO", "RAMIFICACION")),
        "alcance_de_la_comprobacion": (
            "inventario canonico de publicaciones, con procedencia acreditada"
            if alcance_ok else
            f"solo el repositorio ({estado_inventario}); el inventario de "
            "publicaciones de Drive NO se ha consultado"),
        "degradacion_de_autoridad": degradacion,
    }


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    inventario, estado, detalle = cargar_inventario()
    novedades = [evaluar_novedad(t, inventario, estado)
                 for t in T.cargar_catalogo().get("temas", [])]
    if args.json:
        print(json.dumps({"estado_inventario": estado, "detalle": detalle,
                          "novedad": novedades}, ensure_ascii=False, indent=2))
        return 0

    from collections import Counter as _C
    print(f"inventario : {estado} ({len(inventario)} entradas)")
    if detalle["fallos"]:
        print(f"  fallos   : {detalle['fallos']}")
    print(f"candidatos : {len(novedades)}")
    for veredicto, n in sorted(_C(x["veredicto"] for x in novedades).items()):
        print(f"  {veredicto:<28} {n}")
    for n in novedades:
        if n["veredicto"] in ("REPETICION", "SIN_APORTACION_DEMOSTRABLE"):
            print(f"\n  {n['candidato']} — {n['veredicto']}: {n['motivo']}")
    globales = sum(1 for n in novedades if n["puede_declararse_nuevo_globalmente"])
    print(f"\ndeclarables como novedad GLOBAL: {globales} de {len(novedades)}")
    print("El inventario de publicaciones y la matriz de contenido viven en Google")
    print("Drive (CLAUDE.md §2) y NO se han consultado. 'No encontrado en el")
    print("repositorio' no significa 'no publicado'.")
    print("\nOrganizar un lote no acredita derecho, no abre gates y no autoriza nada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
