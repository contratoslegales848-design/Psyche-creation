# Motor de candidatos temáticos

Produce **candidatos**, no claims. Un candidato es una pregunta o una distinción que merece
investigarse — pero **no es terreno neutral**: un título o una justificación pueden contener
una proposición jurídica, y por eso las justificaciones se guardan como hipótesis, no como
hechos.

Documentación: [`docs/motor-de-temas-transversales.md`](../../docs/motor-de-temas-transversales.md).
Canon de dirección: [`docs/direccion-basico-antes-que-complejo.md`](../../docs/direccion-basico-antes-que-complejo.md).

## Qué hay aquí

| Archivo | Qué es |
|---|---|
| `catalogo-transversal-v1.json` | 24 candidatos en `LEGAL_HYPOTHESIS`, sin evidencia en ninguna jurisdicción |
| `transversality.py` | Barrera de anclaje nacional + cobertura real por fuentes |
| `lote.py` | Diversidad editorial de un lote y memoria contra el inventario |
| `brief.py` | Candidato → **ficha de investigación** (no ejecutable) |
| `rendimiento.py` | Reordena candidatos por rendimiento histórico real documentado (no lo calcula) |
| `test_topics.py` | 73 pruebas |
| `test_rendimiento.py` | 17 pruebas |

```bash
python3 content/topics/transversality.py     # qué pasa el filtro y qué no
python3 content/topics/lote.py               # inventario y novedad
python3 content/topics/brief.py --tema LM-T-001 --json
python3 content/topics/rendimiento.py        # orden por rendimiento documentado
cd content/topics && python3 -m unittest test_topics test_rendimiento
```

## Priorizar por lo que ya funcionó, sin inventar una cifra

`rendimiento.py` transcribe el orden de formatos por rendimiento real que ya
documenta la skill `legalmente-visual-system` (fuente: Drive, "Inventario de
publicaciones — LegalMente (Facebook)", 62 piezas con cifras). No calcula nada
por sí solo, no se conecta a ninguna API de métricas, y no le asigna un rango
inventado a una forma editorial que la skill no cubrió con cifras — esas
quedan marcadas `SIN_DATO_HISTORICO`, nunca estimadas.

**El dato es de Facebook.** Extrapolarlo a LinkedIn o al sitio web sin datos
propios de esa superficie sería la misma falsa universalización que
`CLAUDE.md` §4 prohíbe para el contenido jurídico, aplicada esta vez al dato
editorial — por eso cada resultado de `anotar()` declara su alcance
explícitamente en vez de darlo por sentado.

Reordena para que la revisión humana empiece por lo que el patrón histórico
favorece. No abre ningún gate, no aprueba nada, no decide qué se publica.

## Lo que el filtro demuestra, y lo que no

Demuestra `NO_EXPLICIT_NATIONAL_ANCHOR`: el texto no nombra país, ley, moneda ni plazo.

**No demuestra `CAPA_A_TRANSVERSAL`.** Cuatro de las diez piezas del último lote estaban
escritas sin un solo topónimo y describían el derecho de un único país. La capa sale como
`NO_DETERMINADO` para los 24.

Tres jurisdicciones con evidencia propia demuestran **cobertura comparada de esas tres**, no
universalidad panhispánica.

## El inventario del repositorio no es el inventario de publicaciones

`CLAUDE.md` §2 sitúa el inventario de publicaciones y la matriz de contenido en **Google Drive**.
Este módulo solo lee el repositorio, así que lo más alto que alcanza es
`INVENTORY_REPO_COMPLETE` — nunca `INVENTORY_CANONICAL`.

Consecuencia: hoy **0 de 24** candidatos pueden declararse novedad global.
`NO_ENCONTRADO_EN_EL_REPOSITORIO` **no significa «no publicado»**. Lo local sigue sirviendo: las
repeticiones y ramificaciones dentro del repo se detectan igual.

Solo un inventario inyectado con procedencia acreditada (`drive_file_id`, `exportado_en`,
`exportado_por`) habilita la afirmación global. Etiquetarlo canónico sin esa procedencia lo
degrada.

## Lo que una ficha no es

Sale con `ejecutable: false`, `gate_arte: CERRADO`, `estado_epistemico: TOPIC_CANDIDATE`,
`revision_humana: PENDIENTE`, `publicacion: NOT_PUBLISHED`, y hay pruebas que lo impiden
cambiar. El copy se entrega vacío y el prompt de animación se guarda como
`propuesta_de_prompt_NO_EJECUTABLE`.
