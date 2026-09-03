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

def cargar_inventario():
    """Lo ya producido o pendiente, leido de las fuentes reales del repositorio.

    Devuelve (entradas, estado). El estado es INVENTORY_NOT_CHECKED cuando no se
    pudo consultar, y en ese caso NINGUN candidato puede declararse nuevo.
    """
    entradas = []
    consultado = False

    # 1. Piezas de contenido con taxonomia declarada.
    dir_contenido = REPO / "content"
    if dir_contenido.is_dir():
        consultado = True
        for ruta in sorted(dir_contenido.glob("*.json")):
            try:
                datos = json.loads(ruta.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            tax = datos.get("taxonomia") or {}
            if tax:
                entradas.append({
                    "origen": f"content/{ruta.name}",
                    "concepto": tax.get("concepto", ""),
                    "materia": tax.get("materia", ""),
                    "situacion_humana": tax.get("situacion_humana", ""),
                    "forma_editorial": tax.get("content_type", ""),
                })

    # 2. Claim packets: pendientes, pero ocupan concepto.
    dir_packets = REPO / "content" / "claim-packets"
    if dir_packets.is_dir():
        consultado = True
        for ruta in sorted(dir_packets.glob("*.json")):
            try:
                datos = json.loads(ruta.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for claim in datos.get("claims", []):
                entradas.append({
                    "origen": f"claim-packets/{ruta.name}",
                    "concepto": str(claim.get("concepto", "") or datos.get("tema", "")),
                    "materia": str(datos.get("materia", "")),
                    "situacion_humana": "",
                    "forma_editorial": "",
                })

    # 3. Inventario de produccion visual, si es consultable.
    try:
        sys.path.insert(0, str(REPO / "visual"))
        import inventory as _inv  # noqa: PLC0415
        for reg in _inv.build_readiness():
            entradas.append({
                "origen": f"inventario/{reg.piece_id}",
                "concepto": "",
                "materia": "",
                "situacion_humana": "",
                "forma_editorial": "",
                "piece_id": reg.piece_id,
                "content_ids": list(reg.content_ids),
            })
        consultado = True
    except Exception as exc:  # noqa: BLE001 - cualquier fallo es "no consultado"
        entradas.append({"origen": "inventario", "error": str(exc)})

    estado = "INVENTORY_CHECKED" if consultado else T.INVENTORY_NOT_CHECKED
    return entradas, estado


def evaluar_novedad(candidato, inventario=None, estado_inventario=None):
    """?Este candidato aporta algo que el inventario no tenga ya?

    La respuesta nunca es un simple si/no: cuando el inventario no se pudo
    consultar, decir "es nuevo" seria inventar una comprobacion que no ocurrio.
    """
    if inventario is None or estado_inventario is None:
        inventario, estado_inventario = cargar_inventario()

    if estado_inventario == T.INVENTORY_NOT_CHECKED:
        return {
            "candidato": candidato.get("id"),
            "estado_inventario": T.INVENTORY_NOT_CHECKED,
            "puede_declararse_nuevo": False,
            "coincidencias": [],
            "motivo": ("no se pudo consultar el inventario vigente; sin esa "
                       "comprobacion no se declara novedad"),
        }

    concepto = str(candidato.get("concepto", "")).strip().casefold()
    situacion = str(candidato.get("situacion_humana", "")).strip().casefold()
    coincidencias = []
    for e in inventario:
        if not concepto:
            break
        if str(e.get("concepto", "")).strip().casefold() == concepto:
            coincidencias.append({"origen": e["origen"], "dimension": "concepto"})
        elif situacion and str(e.get("situacion_humana", "")).strip().casefold() == situacion:
            coincidencias.append({"origen": e["origen"], "dimension": "situacion_humana"})

    return {
        "candidato": candidato.get("id"),
        "estado_inventario": estado_inventario,
        "puede_declararse_nuevo": not coincidencias,
        "coincidencias": coincidencias,
        "motivo": ("sin coincidencias en el inventario consultado" if not coincidencias
                   else "el concepto o la situacion humana ya estan ocupados"),
    }


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    inventario, estado = cargar_inventario()
    novedades = [evaluar_novedad(t, inventario, estado)
                 for t in T.cargar_catalogo().get("temas", [])]
    if args.json:
        print(json.dumps({"estado_inventario": estado, "novedad": novedades},
                         ensure_ascii=False, indent=2))
        return 0

    print(f"inventario            : {estado} ({len(inventario)} entradas)")
    nuevos = [n for n in novedades if n["puede_declararse_nuevo"]]
    print(f"candidatos            : {len(novedades)}")
    print(f"declarables como nuevos: {len(nuevos)}")
    for n in novedades:
        if n["coincidencias"]:
            print(f"\n  {n['candidato']} — ya ocupado")
            for c in n["coincidencias"][:3]:
                print(f"    - {c['origen']} ({c['dimension']})")
    print("\nOrganizar un lote no acredita derecho, no abre gates y no autoriza nada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
