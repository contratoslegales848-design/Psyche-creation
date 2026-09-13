#!/usr/bin/env python3
"""Legibilidad real del render de video: contraste medido, no supuesto.

El compositor de imagen fija ya mide el contraste de cada bloque de texto contra
los píxeles que tiene debajo (`visual/compositor.py`). El render de video no medía
nada: resolvía la legibilidad con un degradado oscuro y una sombra de texto, que
es justo lo que la skill §6 desaconseja ("contraste mínimo 4,5:1, ideal 7:1,
resuelto con la luz de la propia escena, nunca con una caja opaca"). Sin medida,
nadie podía decir si el degradado bastaba o sobraba.

Cómo mide
---------
1. Renderiza el fotograma real de la composición.
2. Renderiza EL MISMO fotograma con el texto vacío (`--props`), que es el fondo
   exacto sobre el que cae el texto — degradado incluido.
3. Aísla los píxeles de glifo: los que en el fotograma con texto coinciden con un
   color declarado de la paleta y difieren del fondo. La sombra de texto y el
   antialias quedan fuera a propósito: no son el trazo, y promediarlos maquillaría
   el resultado.
4. Calcula la razón de contraste WCAG de cada uno de esos píxeles contra el fondo
   que tiene debajo, y reporta la distribución.

No aprueba nada: informa y, si el trazo cae por debajo del mínimo aprobado en más
píxeles que la tolerancia, sale con código 1 para que alguien lo mire.

    python3 scripts/audit-video-legibility.py
    python3 scripts/audit-video-legibility.py --composicion ejemplo --json
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "visual"))

from compositor import ratio_contraste  # noqa: E402
from brief import VisualPolicy  # noqa: E402
from composition import hex_a_rgb, safe_area_para, zona_visible_tras_recorte  # noqa: E402

# Campos de texto de una pieza. Vaciarlos da el fondo exacto sin tocar la escena.
CAMPOS_DE_TEXTO = ("titulo", "frase", "remate", "marca")

# Un píxel es trazo si está a esta distancia RGB de un color declarado...
TOLERANCIA_COLOR = 26
# ...y además difiere del fondo al menos esto. El umbral es deliberadamente
# bajo: los dos fotogramas son deterministas y solo se distinguen por el texto,
# así que cualquier diferencia real viene del trazo. Un umbral alto escondería
# justo el peor caso — texto del color del fondo, que no se ve y tampoco se
# "movería" lo suficiente para ser detectado.
DIFERENCIA_MINIMA = 4
# Fracción de trazo por debajo del mínimo que se tolera antes de fallar.
TOLERANCIA_BAJO_MINIMO = 0.02
# Holgura del borde, en px. Un glifo real sobresale ópticamente de su caja (la
# barra de una itálica, el descendente de una "p") y el antialias añade otro
# píxel. Exigir cero sería medir la rasterización, no el encuadre.
TOLERANCIA_BORDE_PX = 2


def _distancia(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def render_still(composicion, destino, frame, props=None):
    cmd = ["npx", "remotion", "still", "src/index.ts", composicion, str(destino),
           f"--frame={frame}",
           "--chromium-options=--no-sandbox --disable-setuid-sandbox"]
    if props is not None:
        cmd.append("--props=" + json.dumps(props, ensure_ascii=False))
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0 or not Path(destino).is_file():
        return (r.stderr or r.stdout or "").strip().splitlines()[-1:] or ["fallo desconocido"]
    return None


def medir(con_texto, sin_texto, colores, minimo, ideal):
    """Distribución de contraste del trazo contra su fondo real."""
    from PIL import Image

    a = Image.open(con_texto).convert("RGB")
    b = Image.open(sin_texto).convert("RGB")
    if a.size != b.size:
        raise SystemExit("los dos fotogramas no tienen el mismo tamaño; medida imposible.")

    pa, pb = a.load(), b.load()
    ratios, caja = [], None
    for y in range(a.height):
        for x in range(a.width):
            px_a, px_b = pa[x, y], pb[x, y]
            if _distancia(px_a, px_b) < DIFERENCIA_MINIMA:
                continue
            color = next((c for c in colores if _distancia(px_a, c) <= TOLERANCIA_COLOR), None)
            if color is None:
                continue    # sombra de texto o antialias: no es trazo
            ratios.append(ratio_contraste(color, px_b))
            caja = (min(caja[0], x), min(caja[1], y), max(caja[2], x), max(caja[3], y)) \
                if caja else (x, y, x, y)

    if not ratios:
        return None
    ratios.sort()
    n = len(ratios)
    bajo_minimo = sum(1 for r in ratios if r < minimo) / n
    bajo_ideal = sum(1 for r in ratios if r < ideal) / n
    return {
        "pixeles_de_trazo": n,
        "contraste_minimo": round(ratios[0], 2),
        "contraste_p05": round(ratios[int(0.05 * (n - 1))], 2),
        "contraste_mediano": round(ratios[n // 2], 2),
        "fraccion_bajo_minimo": round(bajo_minimo, 4),
        "fraccion_bajo_ideal": round(bajo_ideal, 4),
        "caja_del_texto": list(caja),
    }


def auditar(composicion, artefacto, policy, frame, tmp):
    colores = [hex_a_rgb(h)
               for clave in ("marfil_editorial", "laton_oro_viejo")
               for h in policy.data["paleta"]["requerida"][clave]]
    colores = [c for c in colores if c]
    tip = policy.data.get("tipografia", {})
    minimo = float(tip.get("contraste_minimo", 4.5))
    ideal = float(tip.get("contraste_ideal", 7.0))

    imagen = REPO / artefacto.get("imagen", "")
    if not imagen.is_file():
        return {"composicion": composicion, "estado": "SALTADA",
                "motivo": f"la pieza no tiene todavía su imagen: {artefacto.get('imagen')}"}

    con = tmp / f"{composicion}-con-texto.png"
    sin = tmp / f"{composicion}-sin-texto.png"
    for destino, props in ((con, None), (sin, {c: "" for c in CAMPOS_DE_TEXTO})):
        error = render_still(composicion, destino, frame, props)
        if error:
            return {"composicion": composicion, "estado": "ERROR", "motivo": " ".join(error)}

    medida = medir(con, sin, colores, minimo, ideal)
    if medida is None:
        # O la pieza no lleva texto, o el texto no está en un color de la paleta.
        # Las dos cosas piden que alguien mire: ninguna es un resultado neutro.
        return {"composicion": composicion, "estado": "REVISION_HUMANA", "medida": None,
                "problemas": ["no se encontró ningún píxel de texto en un color declarado de la "
                              "paleta: o la pieza no lleva texto, o el texto se pinta con un color "
                              "que la marca no ha aprobado."],
                "avisos": []}

    from PIL import Image
    with Image.open(con) as img:
        ancho, alto = img.size
    (sx, sy, sw, sh), origen = safe_area_para(ancho, alto, policy)
    visible = zona_visible_tras_recorte(ancho, alto, policy)
    x0, y0, x1, y1 = medida["caja_del_texto"]

    problemas = []
    if medida["fraccion_bajo_minimo"] > TOLERANCIA_BAJO_MINIMO:
        problemas.append(
            f"el {medida['fraccion_bajo_minimo'] * 100:.1f}% del trazo cae por debajo de "
            f"{minimo}:1 (mínimo aprobado). No se resuelve con una caja opaca: o cambia la luz de "
            "la escena, o cambia dónde va el texto.")
    h = TOLERANCIA_BORDE_PX
    if not (x0 >= sx - h and y0 >= sy - h and x1 <= sx + sw + h and y1 <= sy + sh + h):
        problemas.append(
            f"el texto ocupa {medida['caja_del_texto']} y la zona segura es "
            f"{[sx, sy, sx + sw, sy + sh]} (origen: {origen}).")
    if visible and not (x0 >= visible[0] - h and y0 >= visible[1] - h
                        and x1 <= visible[2] + h and y1 <= visible[3] + h):
        problemas.append("hay texto fuera de la banda que el feed deja ver: se publicaría recortado.")

    avisos = []
    if medida["fraccion_bajo_ideal"] > 0.5:
        avisos.append(
            f"más de la mitad del trazo ({medida['fraccion_bajo_ideal'] * 100:.1f}%) no llega al "
            f"contraste ideal de {ideal}:1.")

    return {"composicion": composicion, "estado": "MEDIDA" if not problemas else "REVISION_HUMANA",
            "medida": medida, "problemas": problemas, "avisos": avisos,
            "zona_segura": [sx, sy, sx + sw, sy + sh], "zona_segura_origen": origen,
            "nota": "medido sobre el fotograma real, degradado y sombra incluidos. "
                    "Una medida en verde no aprueba la pieza."}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--composicion", help="solo esta composición; por defecto, todas.")
    ap.add_argument("--frame", type=int, default=60,
                    help="fotograma a medir (por defecto 60: el texto ya entró del todo).")
    ap.add_argument("--out", default=None, help="dónde dejar los fotogramas medidos.")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    policy = VisualPolicy.load()
    tmp = Path(a.out) if a.out else REPO / ".runtime" / "video-legibility"
    tmp.mkdir(parents=True, exist_ok=True)

    resultados = []
    for ruta in sorted((REPO / "content").glob("*.json")):
        artefacto = json.loads(ruta.read_text(encoding="utf-8"))
        cid = artefacto.get("id")
        if not cid or (a.composicion and cid != a.composicion):
            continue
        resultados.append(auditar(cid, artefacto, policy, a.frame, tmp))

    if a.json:
        print(json.dumps(resultados, ensure_ascii=False, indent=2))
    else:
        for r in resultados:
            print(f"\n{r['composicion']}  [{r['estado']}]")
            if r.get("motivo"):
                print(f"  {r['motivo']}")
            m = r.get("medida")
            if m:
                print(f"  trazo medido      {m['pixeles_de_trazo']} px")
                print(f"  contraste mínimo  {m['contraste_minimo']}:1  "
                      f"(p05 {m['contraste_p05']}:1, mediano {m['contraste_mediano']}:1)")
                print(f"  bajo el mínimo    {m['fraccion_bajo_minimo'] * 100:.2f}%")
                print(f"  bajo el ideal     {m['fraccion_bajo_ideal'] * 100:.2f}%")
                print(f"  caja del texto    {m['caja_del_texto']} · zona segura {r['zona_segura']}")
            for p in r.get("problemas", []):
                print(f"  ! {p}")
            for w in r.get("avisos", []):
                print(f"  · {w}")
        print("\nMedir no es aprobar: la aprobación visual sigue siendo humana.")

    fallos = [r for r in resultados if r["estado"] in ("REVISION_HUMANA", "ERROR")]
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
