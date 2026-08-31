# Inventario materializado

Generador: `scripts/inventory.py` · Salida: `inventory/inventory.json`

## Qué es

Un **índice derivado y regenerable** de los artefactos que ya existen. Es lo que
faltaba para planificar producción a volumen: cada control mira hoy un archivo a la
vez, y a escala de cientos de piezas hace falta poder preguntar *¿qué está
publicado?*, *¿qué toca medir?*, *¿qué concepto ya está cubierto?*.

## Qué NO es

**No es una base de datos y no es autoridad sobre ningún dato.** Cada dato sigue
viviendo en su artefacto:

| Dato | Vive en |
|---|---|
| `content_id`, taxonomía, capa | `content/*.json` |
| `production_state` | `ProductionHandoff` |
| `publication_state`, `publication_url`, `measurement_due_at` | `PublicationDecision` / `PublicationRecord` |
| `metrics_state` | `MeasurementRecord` |
| `verification_state` | claim packet |
| `source_state` | libro mayor de vigencia |

Si el inventario y un artefacto discrepan, **el artefacto tiene razón**, y
`inventory.py check` falla para que se note.

## Determinismo

El índice almacenado **no depende del reloj**: mismos artefactos, mismo byte. Nada
que dependa de la fecha se congela dentro (ni el vencimiento de medición, ni el
plazo de revisión de fuentes); eso se calcula en `query`. Si el índice dependiera
del reloj, `check` empezaría a fallar solo por el paso del tiempo sin que ningún
artefacto hubiera cambiado — y un control que se rompe solo acaba desactivado.

## Comandos

```bash
python3 scripts/inventory.py build                       # regenera el índice
python3 scripts/inventory.py check                       # ¿está al día y sin duplicados?
python3 scripts/inventory.py query DUE_FOR_MEASUREMENT --today 2026-09-10
python3 scripts/inventory.py query DUPLICADOS
```

Consultas: `DUE_FOR_MEASUREMENT`, `DUPLICADOS`, `PUBLICADAS`, `SIN_PUBLICAR`,
`REQUIERE_REVISION_FUENTES`, `TODO`.

## Anti-duplicados

Cinco colisiones deterministas, ninguna semántica:

| Tipo | Detecta |
|---|---|
| `CONTENT_ID_REPETIDO` | la misma pieza registrada dos veces |
| `COMPOSICION_REPETIDA` | dos artefactos renderizarían la misma composición |
| `CONCEPTO_REPETIDO` | la casilla `materia/submateria/concepto` ocupada dos veces |
| `FINGERPRINT_IDENTICO` | la misma frase salvo mayúsculas, tildes y signos |
| `PUBLICACION_YA_REGISTRADA` | dos piezas apuntando a la misma publicación |

**No detecta paráfrasis.** Dos piezas que dicen lo mismo con otras palabras pasan
los cinco controles. Cerrarlo exigiría embeddings o un motor semántico, que hoy no
existe y que no se construye aquí. Hay una prueba que fija ese límite por escrito
(`test_la_parafrasis_NO_se_detecta_y_queda_declarado`) para que nadie suponga una
cobertura que no hay.

## Métricas

`DUE_FOR_MEASUREMENT` = publicada, sin `MeasurementRecord`, y con
`measurement_due_at` (= `published_at` + 7 días) ya cumplido. Es una consulta, no
una integración: **no hay conexión con ninguna plataforma y no hay scraping**.

## Fixtures

`inventory/fixtures/cadena-completa/` demuestra el recorrido entero — materia →
submateria → concepto → situación humana → contenido → producción → publicación →
métricas — con tres piezas: una medida, una vencida sin medir, y una `NO_APLICA`
legítima (cita histórica). `inventory/fixtures/duplicados/` provoca cuatro
colisiones a la vez. Ninguna es contenido real: todas usan revisor ficticio y
cifras de laboratorio.
