# Partes IX-XI del mandato "Fase post-implementación" (16-sep-2026)

## Parte IX — mezcla editorial

`universe.select_batch()` ya impone cuotas DURAS reales por lote de 10:
mínimo 8-10 materias/familias distintas, máximo 2 piezas por emoción
(`MAX_POR_EMOCION_POR_10`), cuota de materia escalable
(`cuota_max_por_lote_10` en `materias-seed-v1.json`). Esas cuotas no se
tocan — son las que garantizan que el lote no colapse a una sola materia o
familia.

Lo que faltaba era el reporte específico por PROFUNDIDAD (accesible/
intermedio/especializado) que pide el mandato. Se añadió
`topic_classification.reportar_mezcla_editorial()` — deliberadamente
**informativo, nunca una cuota dura ni un hard gate**: el mandato es
explícito ("NO conviertas esos números en una cárcel matemática"). Cuenta
la proporción real por `profundidad` (base/media/alta) contra el rango
sugerido (3-4/3-4/2-3 sobre 10, escalado a `n`) y sólo produce avisos
textuales — nunca rechaza ni fuerza el lote a esa proporción.

## Parte X — citas y máximas

Ya existe una vía específica en el universo editorial real
(`policy/editorial-universe-v1.json`), no un sistema aparte:

```json
"maxima_aforismo": {
  "funcion_editorial": "transmitir una máxima verificable",
  "tension_tipica": "frase viral sin origen",
  "necesidades_afines": ["recordar"],
  "roles_lector_afines": ["persona", "estudiante"]
}
```

El propio campo `tension_tipica` ("frase viral sin origen") codifica
exactamente el riesgo que la Parte X pide vigilar — una cita sin fuente
verificable es la tensión típica que esta familia declara, no una regla
añadida aparte. `corpus_import.py` reconoce el mismo patrón en el corpus
histórico (`PREFIJO_FAMILIA["cita"] = "maxima_aforismo"`). La verificación
de la fuente real de cada cita antes de publicar sigue siendo, sin
excepción, responsabilidad de `legalmente-legal-verification`
(CLAUDE.md §4: "una cita necesita autor/obra identificable, no solo
atribución viral") — no se duplica ese control aquí.

## Parte XI — jurisdicción

Ningún `TopicCandidate` ni ninguna estructura de `visual/` lleva hoy un
campo `jurisdiccion` explícito. Se evaluó añadirlo y se decidió NO
hacerlo, por una razón de arquitectura, no de omisión:

La clasificación panhispánica/Capa A/B/C (CLAUDE.md §4: "Toda afirmación
se clasifica en Capa A (núcleo transversal), Capa B (misma lógica, varía
por país) o Capa C (necesariamente nacional)") es una propiedad de una
**afirmación jurídica concreta ya verificada**, no de un candidato
temático combinatorio que todavía no tiene contenido. `TopicCandidate`
nace `NO_VERIFICADO` deliberadamente (`universe.py`) — nace ANTES de que
exista ninguna afirmación que clasificar por jurisdicción. Forzar un campo
`jurisdiccion` en esta etapa obligaría a inventar un valor sin evidencia
(el mismo error, por analogía exacta, que `generator.py` ya evita al
declarar `legal_support`/`human_interest` como `PENDIENTE_VERIFICACION` en
vez de fabricarlos).

La jurisdicción se determina correctamente en `legalmente-legal-
verification`, sobre la pieza concreta y su claim verificado — ese es el
punto del pipeline donde existe evidencia real para decidirla, y es donde
ya vive según CLAUDE.md §4. Añadir un campo aquí no cerraría un hueco real:
crearía un lugar más donde ese dato podría quedar sin poblar o, peor,
poblado con una suposición. No se toca `TopicCandidate` por esta razón.
