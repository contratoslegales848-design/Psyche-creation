"""Ordena candidatos por rendimiento historico REAL, no inventado.

Fuente unica: `legalmente-visual-system` (skill sincronizada), seccion "La
formula de contenido — priorizar por lo que ya funciono". Esa seccion cita
su propia fuente: Drive, "Inventario de publicaciones — LegalMente
(Facebook)", 62 piezas con cifras. Este modulo transcribe ese orden, no lo
calcula ni lo actualiza — no hay conexion a ninguna API de metricas aqui.

Alcance deliberadamente estrecho: el dato es de la pagina de Facebook
historica de LegalMente. Extrapolarlo a LinkedIn, al sitio web o a
cualquier otra superficie sin datos propios seria la misma falsa
universalizacion que CLAUDE.md §4 prohibe para el contenido juridico,
aplicada esta vez al dato editorial — por eso `anotar()` deja el alcance
explicito en cada resultado en vez de dar a entender una garantia general.

No abre gates, no aprueba nada, no decide que se publica. Solo reordena
para que la revision humana empiece por lo que el patron historico
documentado favorece.
"""

METRICA = "compartidos por reaccion (interpretable solo con volumen: por debajo de ~60 reacciones el cociente es ruido)"

FUENTE = ("legalmente-visual-system SKILL.md, seccion 1 -- Drive: "
          "'Inventario de publicaciones - LegalMente (Facebook)', 62 piezas con cifras")

ALCANCE = ("Facebook historico de la pagina LegalMente. No se extrapola a otras "
           "superficies (LinkedIn, sitio web) sin datos propios de esa superficie.")

# Orden documentado, de mayor a menor rendimiento real. Solo entran aqui
# las formas editoriales con evidencia citada explicitamente en la skill —
# nunca se inventa una posicion para una forma sin cifra respaldandola.
RENDIMIENTO_DOCUMENTADO = (
    ("LISTADO", 1, "listado numerado de alto volumen -- p.ej. 2800/915, 760/309, 287/114"),
    ("MAXIMA", 2, "maxima latina con traduccion y aplicacion de hoy -- p.ej. 439/134, 394/102"),
    ("CONSECUENCIA", 3, "consecuencia concreta y personal -- p.ej. 526/200"),
    ("MITO", 4, "mito legal desmentido -- razon compartidos/reacciones mas alta de la pagina (0.87)"),
    ("DIFERENCIAS", 5, "diferencias entre figuras que la gente confunde"),
    ("CITA", 6, "cita de figura reconocible o frase que se atreve -- p.ej. 152/74, 89/48"),
    ("CONCEPTO", 7, "conceptos y tecnicismos -- sostienen autoridad, alcance moderado"),
)

# Formas que la skill documenta explicitamente como bajo rendimiento
# historico (no "evitar" en abstracto: son mas de la mitad del inventario
# historico y rinden 4-20 reacciones).
FORMAS_DE_BAJO_RENDIMIENTO_DOCUMENTADO = (
    "juristas tecnicos poco conocidos (Stammler, Raz, Hauriou)",
    "filosofos generales sin anclaje juridico",
)

SIN_DATO_HISTORICO = "SIN_DATO_HISTORICO"

_RANGO = {forma: rango for forma, rango, _ in RENDIMIENTO_DOCUMENTADO}
_DETALLE = {forma: detalle for forma, _, detalle in RENDIMIENTO_DOCUMENTADO}


def rango_de_forma(forma_editorial):
    """(rango, detalle) para una forma con evidencia citada, o
    (None, SIN_DATO_HISTORICO) si no hay cifra que respalde una posicion.

    No adivina: una forma editorial que el catalogo usa pero que la skill
    no cubrio con cifras (p.ej. GUIA_O_CHECKLIST, PREGUNTA_COMUN) se
    reporta honestamente sin dato, nunca con un rango estimado."""
    forma = str(forma_editorial or "").strip().upper()
    if forma in _RANGO:
        return _RANGO[forma], _DETALLE[forma]
    return None, SIN_DATO_HISTORICO


def ordenar_por_rendimiento(candidatos, forma_editorial_key="forma_editorial"):
    """Ordena `candidatos` (dicts) por rendimiento documentado, mejor
    primero. Los que no tienen dato historico quedan al final, en su orden
    relativo original (ordenamiento estable) -- nunca se les asigna un
    rango inventado para poder compararlos con los que si tienen cifra."""
    con_dato = []
    sin_dato = []
    for candidato in candidatos:
        rango, _ = rango_de_forma(candidato.get(forma_editorial_key))
        if rango is None:
            sin_dato.append(candidato)
        else:
            con_dato.append((rango, candidato))
    con_dato.sort(key=lambda par: par[0])
    return [c for _, c in con_dato] + sin_dato


def anotar(candidato, forma_editorial_key="forma_editorial"):
    """Copia de `candidato` con un campo `_rendimiento_documentado` anadido.
    No muta el original. El campo nunca certifica que la pieza vaya a
    viralizarse: documenta un patron historico de una pagina y un formato,
    no una prediccion sobre un candidato que todavia no existe como pieza."""
    forma = candidato.get(forma_editorial_key)
    rango, detalle = rango_de_forma(forma)
    anotado = dict(candidato)
    anotado["_rendimiento_documentado"] = {
        "forma_editorial": forma,
        "rango": rango,
        "detalle": detalle,
        "metrica": METRICA,
        "fuente": FUENTE,
        "alcance": ALCANCE,
    }
    return anotado


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import transversality as T

    catalogo = T.cargar_catalogo()
    ordenados = ordenar_por_rendimiento(catalogo["temas"])
    for t in ordenados:
        rango, detalle = rango_de_forma(t.get("forma_editorial"))
        etiqueta = f"#{rango}" if rango else SIN_DATO_HISTORICO
        print(f"{etiqueta:<20} {t['forma_editorial']:<18} {t['id']}  {t['titulo_de_trabajo']}")
    print(f"\nFuente: {FUENTE}")
    print(f"Alcance: {ALCANCE}")
