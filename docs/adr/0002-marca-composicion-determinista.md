# ADR 0002 — La marca se compone después; el generador no escribe ninguna letra

**Estado: APROBADO por el fundador (2026-08-31).** Sustituye a la propuesta de
`docs/decision-visual-marca-sin-texto.md`, que queda como antecedente histórico.

## Decisión

```
physical_brand_integration_required = SÍ
generator_writes_brand_text         = NO
post_composite_brand_text           = SÍ
```

El generador de imágenes **no escribe ninguna letra**: ni títulos, ni citas, ni
autores, ni numeración, **ni la palabra "LegalMente"**. No hay excepción de marca.

La integración física de marca **sigue siendo obligatoria**. Lo que cambia es
*cuándo* aparece la palabra, no *si* la marca está integrada en la escena:

```
ESCENA GENERADA EN BRUTO
        ↓
SUPERFICIE FÍSICA RESERVADA EN LA ESCENA   (placa, latón, bronce, lomo, sello,
        ↓                                   vidrio, piedra, madera, cuaderno…)
COMPOSICIÓN DETERMINISTA DE MARCA
        ↓
"LegalMente"
        ↓
COHERENCIA DE PERSPECTIVA / MATERIAL / LUZ
        ↓
QA
```

Sigue prohibido: watermark, logo flotante, branding de esquina ajeno a la escena,
overlay arbitrario, y texto de marca escrito por el generador.

## Por qué

Los generadores de imagen son inconsistentes al renderizar texto. Pedir a la vez
"ninguna letra" y "la palabra LegalMente legible" era una instrucción
contradictoria: el modelo podía ignorar cualquiera de las dos sin avisar, y la
marca salía deformada, ilegible o mal ubicada. Componer el texto después unifica
el tratamiento de *todo* el texto de una pieza en un solo paso controlado — el
mismo que ya monta título, autor y contexto.

## Cómo está ejecutado

No es una nota: es comportamiento, y falla cerrado.

| Dónde | Qué hace |
|---|---|
| `visual/policy/legalmente-visual-policy-v1.json` (v1.1) | `texto_marca_lo_escribe_el_generador: "NO"`, `post_composite_brand_text: true` |
| `visual/composition.py` → `build_brand_plan()` | emite `BrandCompositionPlan` con `generator_writes_text=False` |
| `visual/compiler.py` | el prompt pide una **superficie reservada vacía**; nunca pide escribir la marca |
| `visual/brief.py` | una política de marca ilegible bloquea (fail-closed) |
| `visual/feedback.py` | `BRAND_ERROR` / `BRAND_FLOATING` fuerzan composición determinista |
| `visual/test_visual_advanced.py::TestMarcaRedTeam` | 5 pruebas: la petición se convierte, nunca llega al proveedor |

Una petición de `marca_texto_en_imagen=True` **no se rechaza con un error seco**:
se **convierte** a composición posterior y la conversión queda anotada en el
`BrandCompositionPlan.coercion_note` y en la explicación del plan de generación.
Así el sistema es utilizable sin dejar de ser estricto.

## Qué falta (fuera del alcance de este repo)

1. `legalmente-visual-system` (skill global, sincronizada) sigue conteniendo la
   instrucción antigua. Editarla es una acción aparte, con autorización propia.
2. El rasterizado del texto **no** está implementado aquí: no hay Pillow ni
   ninguna dependencia de imagen en el repositorio. Lo que existe es el
   `TypographyPlan` + `BrandCompositionPlan` que un compositor debe ejecutar.
   Declarado como `CONTRACT_ONLY`, no como hecho.
