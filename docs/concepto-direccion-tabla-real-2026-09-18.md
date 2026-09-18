# Tabla real CONCEPTO → DIRECCIÓN ARTÍSTICA con evidencia empírica — 18-sep-2026

Autorización del Founder (18-sep-2026): construir la tabla real
CONCEPTO→TENSIÓN→METÁFORA→DIRECCIÓN ARTÍSTICA que el Contrato v4 §4 exige y
que `docs/mandato-maestro-cierre-2026-09-17.md` (fila 1, 17-sep-2026) dejó
documentada como gap real — "hoy se resuelve en autoría humana, no en
selección automática". Construcción y prueba en la rama actual — sin
autorización de merge, deploy ni publicación.

## PROBLEMA

`direccion_causal.py` (17-sep-2026) ya derivaba SIGNIFICADO (concepto/
tensión reales; movimiento_juridico de `necesidad`; grado_abstraccion de
`profundidad`) y restringía `realism`/`visual_mechanism` del catálogo antes
de seleccionar — pero **2 de las 10 dimensiones de la huella** (2/10, no
2/504: `primary_direction`/`secondary_direction` son 2 de las 10 dimensiones
que componen una huella; la biblioteca de la que salen tiene 504 entradas
reales). Esas 2 dimensiones seguían rotando por anti-repetición pura, sin
ningún componente causal informado por evidencia real de qué dirección
artística funcionó para qué concepto — documentado explícitamente en
`docs/mandato-maestro-cierre-2026-09-17.md` fila 1: "filtrarlas exigiría la
misma afinidad fabricada que se evitó a propósito".

## EVIDENCIA

1. `memoria_fuerte.py` (fuente #5 del Contrato v4) contiene 16 piezas reales
   (`PIEZAS_PUBLICADAS` + `PIEZAS_PRESELECCIONADAS`), cada una con
   `concepto_nucleo` real. De esas 16, **exactamente 4** documentan también
   `direccion_artistica` verbatim: MF-10 (Carnelutti, likes/compartidos
   reales), MF-11 (Onassis, likes/compartidos reales), MF-12 (Calamandrei,
   likes/compartidos reales), MF-13 (Surrealista estructurado, confirmación
   explícita del Founder: "me gustaron") — verificado por
   `grep -n "direccion_artistica=" memoria_fuerte.py`, no una cifra elegida
   a mano.
2. Ninguna de las 16 piezas documenta `relacion` (tensión) ni `metafora` —
   verificado con `grep -n "relacion=\|metafora=" memoria_fuerte.py`, cero
   resultados. La forma de 4 eslabones (CONCEPTO→TENSIÓN→METÁFORA→
   DIRECCIÓN) que describe el mandato no tiene evidencia real para 2 de sus
   4 eslabones.
3. Las 4 direcciones artísticas reales son texto libre, anteriores al
   catálogo maestro estructurado de 504 direcciones (son descripciones de
   piezas de Facebook, no entradas del catálogo). Verificado por coincidencia
   textual literal contra las 504 direcciones reales: 3/4 comparten al menos
   una palabra real con el catálogo (Carnelutti → "pergamino"; Calamandrei →
   "papel"; Surrealista → "surrealismo"); Onassis ("retrato con frase en
   mayúsculas bold superpuesta") no comparte ninguna palabra real con el
   vocabulario del catálogo maestro.

## HIPÓTESIS

Se puede construir una tabla real de 2 eslabones — CONCEPTO → DIRECCIÓN
ARTÍSTICA (nunca los 4 que describe el mandato, por falta de evidencia en
2 de ellos) — que, cuando el concepto de un candidato nuevo se parece
realmente a uno de esos 4 conceptos documentados, informe (nunca fuerce) la
selección de `primary_direction`/`secondary_direction` hacia el vocabulario
real del catálogo que comparte palabras con la dirección artística
histórica. Sin ese parecido real, o sin vocabulario compartido, el
comportamiento debe ser idéntico al de antes de este cambio.

## CAMBIO

- `visual/concepto_direccion.py` (nuevo): `TABLA_CONCEPTO_DIRECCION` (4
  filas reales, construida desde `memoria_fuerte.py`, nunca inventada);
  `buscar_evidencia_concepto()` (solapamiento de tokens sobre
  `concepto_nucleo`, reutilizando `semantic_fingerprint._similitud`/
  `_tokens` — no reimplementado); `direcciones_informadas_por_evidencia()`
  (coincidencia textual literal contra el catálogo real, mismo mecanismo
  que `direccion_causal._valores_permitidos_mecanismo`); `cobertura()`
  (reporta con precisión qué tan completa está la tabla, nunca "cobertura
  del catálogo").
- `visual/direccion_causal.py`: `Significado` gana 3 campos auditable
  (`evidencia_concepto_id`, `evidencia_concepto_similitud`,
  `evidencia_concepto_direccion_artistica`); `_catalogo_causal()` acepta
  `evidencia_concepto` opcional y restringe `direcciones` (no sólo
  `auxiliares`) cuando hay evidencia real con vocabulario compartido;
  `seleccionar_direccion_causal()` gana el parámetro opcional
  `tabla_concepto_direccion` (`None` por defecto — mismo patrón que
  `memoria_fuerte`, cero cambio de comportamiento sin él).
- `visual/art_direction.py`: `draft_visual_brief()` reenvía
  `tabla_concepto_direccion` a `seleccionar_direccion_causal()`, opcional,
  `None` por defecto.
- `visual/production_run.py`: `producir_y_dirigir()` reenvía el parámetro;
  `cargar_contexto()` carga la tabla real por defecto
  (`concepto_direccion.TABLA_CONCEPTO_DIRECCION`) para producción real,
  mismo patrón que `memoria_fuerte`.

## PRUEBA

`visual/test_concepto_direccion.py` (23 tests nuevos):

- **Normal**: un candidato cuyo `concepto_nucleo` coincide (idéntico o
  parafraseado) con el de MF-10 (Carnelutti) encuentra la evidencia, y la
  huella elegida respeta el pool de direcciones informado por esa
  evidencia (`TestBuscarEvidenciaConceptoCasoNormal`,
  `TestSeleccionCausalCasoNormalConEvidencia`).
- **Límite**: sin `tabla_concepto_direccion`, comportamiento idéntico al de
  antes de este cambio; con la tabla pero sin concepto relacionado, cero
  restricción; con concepto relacionado (Onassis) pero sin vocabulario real
  compartido con el catálogo, tampoco se restringe nada — sólo se deja
  constancia (`TestSeleccionCausalCasoLimiteSinEvidencia`).
- **Adversarial**: (1) pedir exactamente el concepto de MF-10 con la tabla
  activa — la tabla informa/guía la dirección hacia el vocabulario
  histórico de Carnelutti, pero `memoria_fuerte.evaluar()` bloquea la
  repetición igual que sin la tabla (`bloqueado_memoria_fuerte=True` en
  ambos casos). (2) un catálogo minúsculo cuya única dirección disponible
  dispara `RECHAZO-4-FLAT-ILLUSTRATION-BOLD` — aun con el pool
  completamente restringido a esa dirección por la evidencia (no hay otra
  opción posible), `verificar_rechazos_founder()` sigue bloqueándola
  (`TestAdversarial`).

Regresión: `test_direccion_causal.py` (24 tests), `test_art_direction.py`
(26 tests), `test_production_run.py`, `test_memoria_fuerte.py` — 100 tests
en total sobre los módulos directamente tocados, sin cambios de
comportamiento fuera de lo descrito arriba.

## RESULTADO

Tabla construida y wireada, **sólo hasta donde la evidencia real alcanza**:
4 de 16 piezas de memoria fuerte documentan dirección artística (25%); de
esas 4, 3 comparten vocabulario real con el catálogo maestro de 504
direcciones (75% de las 4, no del catálogo). Para cualquier concepto nuevo
sin parecido real a esos 4 — la inmensa mayoría de los candidatos que
produce el motor combinatorio — el catálogo sigue tan abierto como antes de
este cambio: esta tabla no resuelve la causalidad completa de
`primary_direction`/`secondary_direction`, la extiende sólo donde hay
evidencia real, sin fabricar el resto.

**Honestidad declarada explícitamente**: la tabla NO tiene los 4 eslabones
que describe el mandato (CONCEPTO→TENSIÓN→METÁFORA→DIRECCIÓN); tiene 2
(CONCEPTO→DIRECCIÓN), porque la fuente real no documenta tensión ni
metáfora para ninguna de las 16 piezas. Completar esos 2 eslabones habría
exigido fabricar datos que no existen — exactamente lo que este repositorio
evita en todos sus demás módulos.

## DECISIÓN

Se cierra la parte del gap de `docs/mandato-maestro-cierre-2026-09-17.md`
fila 1 que era alcanzable con evidencia real ("las otras 8 [dimensiones],
incluida la biblioteca de 504 direcciones, siguen rotando por
anti-repetición pura"): ahora 2 de esas 8 (`primary_direction`/
`secondary_direction`) SÍ tienen un componente causal informado por
evidencia real, cuando esa evidencia existe. Las 6 dimensiones restantes
(`medium`, `lighting`, `composition`, `camera_optics`, `palette`,
`materiality`) siguen sin evidencia real que las module — no se tocan, para
no fabricar la misma afinidad que este módulo evita.

Commit en `claude/legalmente-architecture-reconciliation-xojn4i` (PR #35).
NO MERGE. NO DEPLOY. NO PUBLICAR.
