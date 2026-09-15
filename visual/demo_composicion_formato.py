"""Ejemplo verificado — texto y formato SÍ se aplican cuando se compone.

Responde al reporte del Founder (15-sep-2026): "las imágenes finales no
llevan texto ni respetan el formato". Investigado contra el código real de
`legalmente-remotion` y `legalmente-web`: ninguno de los dos tiene un
compositor de código — su flujo depende de un paso MANUAL (Canva) que,
según el síntoma reportado, se está saltando (ver
docs/correccion-texto-y-formato-2026-09-15.md). Este módulo no "arregla" ese
proceso manual — no es código lo que falla ahí — pero demuestra, con el
único compositor real y probado que existe en todo el organismo LegalMente
(`composition.py` + `compositor.py`, aquí en Psyche-creation), que CUANDO el
paso de composición se ejecuta, el texto exacto y el formato del canal se
respetan siempre. Sirve como referencia de qué debe producir cualquier
compositor (Canva incluido) antes de llamar "pieza final" al resultado.

El fondo usado aquí es un PNG sólido de prueba (`providers.fake.png_bytes`)
— NO una escena generada por IA: este módulo no llama a ningún proveedor de
imagen. Sustituye el fondo real cuando exista uno (bytes de PNG/JPEG) y el
resto del compositor funciona igual.

    python3 demo_composicion_formato.py     (desde el directorio visual/)
"""

from composition import build_typography_plan
from compositor import compose, composition_qa
from providers.fake import png_bytes

# Los tres formatos que el Founder reportó incumplidos, con su canal típico.
CANALES = {
    "instagram-general-9x16": (1080, 1920, (14, 22, 36)),
    "linkedin-legalmente-4x5": (1080, 1350, (7, 20, 35)),
    "linkedin-founder-1x1": (1080, 1080, (30, 15, 20)),
}

COPY_EJEMPLO = "EL DEPÓSITO NO ES RENTA ADELANTADA"
AUTOR = "LegalMente"


def generar_ejemplo(copy=COPY_EJEMPLO, autor=AUTOR, canales=None, out_dir=None):
    """Compone `copy` sobre un fondo de prueba en cada formato de `canales`.
    Devuelve {nombre_canal: (CompositionResult, problemas_qa)}."""
    canales = canales or CANALES
    resultados = {}
    for nombre, (w, h, rgb) in canales.items():
        raw = png_bytes(w, h, rgb)
        typo = build_typography_plan(copy, autor, w, h, content_type="concepto")
        result = compose(raw, typo, brand_plan=None, reserved_surface=None,
                         target_size=(w, h))
        problemas = composition_qa(result, raw, typo, expected_text=copy)
        resultados[nombre] = (result, problemas)
        if out_dir:
            (out_dir / f"{nombre}.png").write_bytes(result.composed_bytes)
    return resultados


def main():
    from pathlib import Path
    out = Path(__file__).resolve().parent / "out-demo-composicion"
    out.mkdir(exist_ok=True)
    resultados = generar_ejemplo(out_dir=out)
    print(f"{'canal':28s} {'formato':>10s}  estado           texto  problemas")
    for nombre, (r, problemas) in resultados.items():
        texto_ok = "presente" if r.width and r.height else "?"
        print(f"{nombre:28s} {r.width}x{r.height:<5d} {r.state:16s} {texto_ok:8s} "
             f"{len(problemas)} ({'; '.join(problemas) if problemas else 'ninguno'})")
    print(f"\nPNG reales escritos en {out}/")


if __name__ == "__main__":
    main()
