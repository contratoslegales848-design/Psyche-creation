# Auditoría de monotonía visual — 16-sep-2026 (Fase 1, mandato "Súper Prompt")

Origen: "LEGALMENTE — SÚPER PROMPT PARA CLAUDE CODE — CORRECCIÓN GLOBAL Y
DEFINITIVA DEL MOTOR DE DIRECCIÓN ARTÍSTICA" (Founder, 16-sep-2026), con
`LEGALMENTE_CATALOGO_MAESTRO_DIRECCION_ARTISTICA_CHATGPT.md` (767 módulos
visuales) como fuente canónica de vocabulario. Autorización expresa del
Founder para auditar y modificar; **sin autorización de merge ni deploy**.

Este documento es la Fase 1 (auditoría obligatoria) — causas concretas y
archivos, antes de implementar.

## Hallazgo 1 — el "azul petróleo" no es una tendencia, es una obligación de código

`visual/compiler.py::compile_request`, línea fija, **incondicional, para
toda pieza sin excepción**:

```python
partes.append(f"Paleta: {_paleta_texto(policy)}.")
partes.append(
    f"El acento azul petroleo debe proceder de un objeto fisico real de la escena: "
    f"{brief.acento_frio_objeto}."
)
```

No depende de la familia visual elegida, ni del tema, ni de la memoria —
se imprime siempre. Además, `visual/brief.py::VisualBrief.validate()` hace
que un brief **sin `acento_frio_objeto` sea inválido** cuando
`policy.paleta.acento_frio_debe_ser_objeto_fisico` es verdadero (y lo es,
ver Hallazgo 2) — el nombre mismo del campo (`acento_frio_objeto`, con el
comentario "el azul petroleo") codifica el azul como la única opción
aceptable, no como una entre varias.

## Hallazgo 2 — la paleta "requerida" de la política es un catálogo de 4 colores, para siempre

`visual/policy/legalmente-visual-policy-v1.json`:

```json
"paleta": {
  "requerida": {
    "nogal_profundo": ["#2B1B17", "#1E1412"],
    "marfil_editorial": ["#FCFAF2", "#F4EFE1"],
    "azul_petroleo": ["#0F2537", "#16324F"],
    "laton_oro_viejo": ["#C5A059", "#B38F4D"]
  }
}
```

`requerida` (required), no `sugerida` (suggested) ni `disponible`
(available). Cuatro tokens, para las 174+ piezas que pasen por este motor,
sin condición ni rotación.

## Hallazgo 3 — el catálogo de 8 "familias" es el `catalogo-estilos.json` reducido que el mandato pide buscar

`visual/policy/visual-families-v1.json` declara 8 familias
(`hiperrealismo_editorial_cinematografico`, `oleo_cinematografico`,
`oleo_clasico_institucional`, `claroscuro_de_museo`, `foto_impasto`,
`neo_editorial_dark_luxury`, `basalt_and_gold_leaf`, `oleo_narrativo`).
Verificado programáticamente: **`nogal_profundo` aparece en 7/8 familias,
`azul_petroleo` en 5/8, `laton_oro_viejo` en 4/8** — la variedad de
NOMBRE de familia no se traduce en variedad de PALETA real, porque las 8
heredan del mismo pool de 4 tokens del Hallazgo 2. Dos de los ocho nombres
(`claroscuro_de_museo`, `neo_editorial_dark_luxury`) son literalmente los
términos que el mandato nombra como síntoma ("claroscuro", "dark luxury").
6/8 son variantes de óleo/museo/dark-luxury.

`elegir_familia_visual()` (`art_direction.py`) sin memoria elige
determinísticamente la primera familia por orden alfabético — con historial
real escaso (como es el caso hoy), la selección es efectivamente fija salvo
que exista memoria visual persistida entre ejecuciones.

## Hallazgo 4 — `legalmente-remotion`: un solo "look" declarado como obligatorio, para el 100% de las piezas

`legalmente-marca-y-estilo.md` §3.1 (arquitectura del prompt, aplicada a
TODAS las piezas del catálogo, incluidas las máximas latinas de §3.3) y
§3.5 (tabla de parámetros):

```
Style: cinematic legal realism with restrained symbolic surrealism,
premium editorial art direction, photorealistic detail, museum-quality
composition.
```

| Estilo declarado | cinematic realism · premium editorial art direction · museum-quality composition | **Siempre presente** |

Es más extremo que el Hallazgo 3: aquí no hay ni 8 familias — hay UNA sola
técnica/medio (fotorrealismo editorial cinematográfico) para el 100% del
catálogo (5 pilares de contenido, máximas incluidas). La paleta de acento
(§2.2, 8 combinaciones: Oxblood, Esmeralda, Índigo, Cobre, Terracota,
Acero, Miel, Ciruela) sí varía más que en Psyche-creation, pero el MEDIO
visual (fotografía cinematográfica) nunca cambia.

## Hallazgo 5 — `legalmente-web`: `visualGrammars` por canal es un catálogo de 5 tokens repartidos en 4 canales

`src/lib/editorial-engine/channel-strategy.ts`
(rama `chatgpt/image-generator-reconciliation-v2-2026-09-13`, repositorio
**solo lectura** para esta cuenta — CLAUDE.md §8): cada canal declara
`visualGrammars: readonly string[]` con 3 entradas, tomadas de un universo
de solo 5 tokens en total (`CINEMATIC_PHOTOGRAPHY`, `EDITORIAL_STILL_LIFE`,
`CONCEPTUAL_SYMBOLISM`, `ARCHITECTURAL_MINIMALISM`,
`HISTORICAL_DOCUMENTARY`). `scoreChannelFit()` puntúa por coincidencia con
esa lista fija — un catálogo reducido por diseño, sin conexión a ningún
catálogo maestro.

## Qué NO se encontró (para no sobre-reportar)

- No hay confusión entre `composición central` como default forzado en
  código — `composition_intent` en `compiler.py` viene de
  `brief.focal_point`, no de un valor fijo. El problema de composición es
  indirecto: como la familia casi nunca cambia (Hallazgo 3), la
  composición tampoco.
- `families.py`/`VisualFamilyRegistry.load()` es una arquitectura correcta
  y ya abierta por diseño (lee de un JSON versionado, sin lógica que limite
  el número de entradas) — el problema es enteramente de **datos**
  (8 entradas anémicas), no de mecanismo. Esto simplifica la corrección:
  no hace falta reescribir el cargador, hace falta un catálogo real.
- `visual_distance.py` (distancia visual estricta, 8 dimensiones) y
  `batch_qa.py` ya existen y están probados — se extienden, no se
  duplican, para las fases 6-7 y 12.

## Plan de corrección (Fases 2 en adelante)

1. Traer `LEGALMENTE_CATALOGO_MAESTRO_DIRECCION_ARTISTICA_CHATGPT.md`
   como fuente canónica humana (`visual/policy/catalogo-maestro-v1.md`).
2. Generar `visual/policy/catalogo-maestro-v1.json` **derivado
   automáticamente** por un parser (`visual/catalog_parser.py`), nunca
   una lista manual — declarado como derivado, no canónico.
3. `visual_fingerprint.py` (nuevo): las 10 dimensiones del mandato,
   selección semántica + anti-repetición sobre el catálogo real.
4. `visual/policy/legalmente-visual-policy-v1.json`: `paleta.requerida`
   deja de ser una obligación de 4 colores — pasa a `paleta.prohibida`
   (negativos reales, se conservan) + el nuevo catálogo como espacio de
   selección.
5. `compiler.py`: retirar la línea incondicional de azul petróleo;
   `acento_frio_objeto` se generaliza a `acento_objeto` (objeto físico
   real, color derivado de la huella, no fijo).
6. `legalmente-remotion/legalmente-marca-y-estilo.md`: el "Estilo
   declarado... Siempre presente" pasa a ser una entre varias direcciones
   posibles del catálogo maestro (rama nueva, PR, sin merge).
7. `legalmente-web`: solo lectura — se documenta el hallazgo y se
   entrega como propuesta (parche/patch-series), no se aplica en el
   repositorio ajeno (CLAUDE.md §8).
