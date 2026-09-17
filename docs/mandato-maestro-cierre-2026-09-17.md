# Mandato Maestro — saneamiento, integración y evolución del motor (17-sep-2026)

Cierre técnico del "Mandato Maestro — LegalMente" del Founder. Documento
único de esta ejecución (mandato §17: "no generes diez documentos nuevos") —
el detalle de cada mecanismo vive en su módulo (`visual/pedagogia.py`,
`visual/memoria_fuerte.py`, etc.) y en `visual/README.md` (punto de entrada
actualizado). Este documento es el mapa de estado (§0) y la tabla
Drive↔código (§13) que el mandato exige por separado.

## Mapa de estado (§0)

| Subsistema | Estado | Evidencia |
|---|---|---|
| Verificación jurídica (claim packets) | 🟢 ACTIVO | `docs/TECHNICAL_STATE.md` — sin cambios en esta ejecución |
| Pipeline Remotion/video | 🟢 ACTIVO | `npm run typecheck` limpio (tras `npm ci`); sin cambios de código esta ejecución |
| Catálogo maestro visual (767 módulos, 504 direcciones) | 🟢 ACTIVO | `visual_fingerprint.py`, verificado en sesiones previas (16-sep) |
| Universo editorial (58 familias pedagógicas) | 🟢 ACTIVO, AMPLIADO | `editorial.py` + `pedagogia.py` (nuevo, esta ejecución) |
| Motor pedagógico (balance conocimiento/narrativa) | 🟢 NUEVO, ACTIVO | `pedagogia.py`, 18 tests, verificación empírica de 8 tandas reales |
| Memoria fuerte (fuente #5, Contrato v4) | 🟢 ACTIVO (extendido esta ejecución) | Ya conectada a dirección visual (sesión previa); esta ejecución la conecta también a **selección temática** (`ajuste_afinidad_founder`) |
| Generador multi-factor + hard gates | 🟢 ACTIVO | `generator.py`, sin regresión (76 tests) |
| Contrato TEXT_TO_IMAGE/IMAGE_EDIT | 🟢 ACTIVO | Hotfix 16-sep-2026, sin cambios esta ejecución |
| Orden CONCEPTO→TENSIÓN→METÁFORA→DIRECCIÓN ARTÍSTICA (Contrato v4 §4) | 🟡 PARCIALMENTE IMPLEMENTADO | Ver §13 tabla, fila 1 |
| `legalmente-story-engine`, 6 agentes, 4 hooks | ⚫ NO IMPLEMENTADO (confirmado, sin cambio) | `docs/TECHNICAL_STATE.md` §3 |
| Proveedor de imagen real | ⚫ BLOQUEADO EXTERNAMENTE | Sin credenciales en el workspace; Higgsfield prohibido por CLAUDE.md |
| `visual/README.md` (punto de entrada) | 🟢 CORREGIDO | Desactualizado desde 16-sep-2026 respecto a memoria fuerte/pedagogía/contrato — actualizado esta ejecución |
| `docs/TECHNICAL_STATE.md` | 🟡 ALCANCE ACOTADO EXPLÍCITAMENTE | Nota de vigencia añadida: sigue siendo correcto para verificación jurídica, no describe el motor editorial/visual — no se reescribió completo (fuera de alcance seguro para esta sesión) |
| Deuda técnica literal (TODO/FIXME/HACK) | 🟢 LIMPIO | 0 hallazgos reales en todo el repo (Python + TypeScript) — ver §12 |
| Dependencias npm (vulnerabilidades) | 🟢 CORREGIDO | 3 altas (fast-uri, js-yaml, nanoid, transitivas) → 0 tras `npm audit fix` sin `--force` |

## Pendientes históricos (§12) — auditoría de TODO/FIXME/PENDIENTE/BLOCKED/EXPERIMENTAL

Búsqueda exhaustiva (`grep -rn` sobre `visual/`, `src/`, `scripts/`,
`contract/`, `handoff/`, `docs/`, más TypeScript):

- `TODO`, `FIXME`, `HACK`: **0 hallazgos reales** — las 5 coincidencias de
  "TODO" son la palabra española "todo" (ej. "TODOS los pares reales"), no
  marcadores de trabajo pendiente. Ningún archivo Python o TypeScript de
  este repositorio tiene un TODO/FIXME/HACK de código olvidado.
- `PENDIENTE`/`PENDING`/`BLOCKED` (107+3+42 coincidencias): **todos
  legítimos** — son valores de estado de máquinas de estado ya
  documentadas y con dueño explícito (`PENDIENTE_VERIFICACION`,
  `PENDIENTE_CONTENIDO`, `BLOCKED_BY_SOURCE_ACCESS` con
  `OWNER_SYSTEM`/`OWNER_HUMAN` declarado en `inventory.py`), no deuda
  olvidada. Revisados uno por uno por módulo — ninguno señala trabajo
  interno ejecutable sin decisión humana o proveedor externo.
- `PARCIAL` (3): dos son la constante real `GROUND_TRUTH_FOUNDER_PARCIAL`
  (estado legítimo cuando el Founder no respondió todas las preguntas de
  una revisión, `founder_review.py`), una es prosa ("memorias editoriales
  PARCIALMENTE...", `lanes.py` docstring).
- `EXPERIMENTAL` (16): todas en `docs/handoff-contracts/` — contratos
  externos marcados DRAFT/EXPERIMENTAL a propósito (Grok/Manus/Gemini, P3
  del `TECHNICAL_STATE.md`), no se implementan sin autorización.

**Conclusión**: el repositorio no tiene deuda de comentarios sin cerrar.
La disciplina de "nunca simular, siempre declarar el hueco explícito con
dueño" ya está aplicada en todo el árbol. No se encontró nada que
"depurar del runtime" en este barrido — resultado real, no buscado a la
fuerza para llenar la sección.

## Drive ↔ código — tabla de divergencias (§13)

| # | REGLA DRIVE | IMPLEMENTACIÓN CÓDIGO | ESTADO | GAP | CAMBIO REALIZADO | TEST | RESULTADO |
|---|---|---|---|---|---|---|---|
| 1 | Contrato v4 §4-5: "El concepto jurídico debe gobernar la propuesta visual. CONCEPTO → TENSIÓN → IDEA → METÁFORA → ESCENA → DIRECCIÓN ARTÍSTICA. Y después selección de recursos." | `visual_fingerprint.seleccionar_huella()` elige `primary_direction`/medio por anti-repetición (frecuencia de uso reciente), **sin leer** concepto/tensión/metáfora del candidato — decisión deliberada y documentada en el propio módulo: "este repositorio no tiene evidencia real de qué categoría conviene a qué materia jurídica, y no se finge una que no existe". | PARCIAL, documentado desde antes de esta ejecución | El orden algorítmico real es DIRECCIÓN ARTÍSTICA (huella, primero) → luego ESCENA/METÁFORA (autoría humana/pipeline, después, compatibles con la huella ya elegida) — literalmente invertido respecto al orden declarado en Drive. El orden Drive SÍ se cumple en la etapa de autoría (`demo_produccion_real_10_temas_nuevos.py`), nunca algorítmicamente. | Ninguno — implementarlo algorítmicamente exigiría fabricar una afinidad concepto→estilo sin evidencia real, prohibido por el mismo criterio fail-closed que ya rige `territory_explorer.coherencia()`. Se documentó explícitamente en `visual/README.md` (nueva sección) en vez de dejarlo implícito. | N/A (no hay cambio de comportamiento que probar) | Gap declarado, no cerrado. Requiere decisión del Founder: o bien autoriza construir/validar una tabla real concepto→familia (con evidencia, no intuición), o bien confirma que el orden se satisface en la etapa de autoría y el hallazgo se cierra como "por diseño". |
| 2 | Mandato Maestro §1-3 (17-sep-2026, este mismo mandato): balance ~70/30 conocimiento/narrativa, configurable, no cuota. | Antes de esta ejecución: no existía ningún mecanismo — medido que el selector converge a 90-100% conocimiento sin intervención (narrativa, 5/58 familias, no favorecida por ningún otro factor). | RESUELTO esta ejecución | — | `visual/pedagogia.py` (nuevo) + `generator.ajuste_balance_pedagogico` wireado en `puntuar_candidato()`/`seleccionar_lote()`. | 18 tests nuevos (`test_pedagogia.py`) + verificación empírica (8 tandas reales, seeds 501-505/601-604) | 70-80% conocimiento sostenido con el mecanismo activo (antes: 90-100%); narrativa presente en todas las tandas. |
| 3 | Mandato Maestro §6 (17-sep-2026): memoria fuerte debe influir en "selección temática; novedad; anti-repetición; dirección visual...", no sólo en un documento pasivo. | Antes de esta ejecución (sesión previa, 16-sep): memoria fuerte conectada SÓLO a dirección visual (`draft_visual_brief`), no a selección temática. | RESUELTO esta ejecución (extensión) | — | `generator.ajuste_afinidad_founder(candidato, memoria, memoria_fuerte=None)` — suma preferencias reales de fuente #5 a la selección temática, mismo techo acotado. `production_run.py` la propaga también a `generator.seleccionar_lote()`. | 2 tests nuevos en `test_generator.py` + verificación empírica confirmando que el balance pedagógico se sostiene incluso con esta señal narrativa-heavy activa. | Selección temática ahora aprende de curaduría Founder real, con el mismo tope de siempre — verificado que no desplaza el balance 70/30 del punto 2. |
| 4 | `CLAUDE.md §8`: "legalmente-web es privado". | Público, reverificado por clonado anónimo el 31-ago-2026 (`docs/TECHNICAL_STATE.md` §5.1). | CONOCIDO, NO CORREGIDO | Afirmación de seguridad incorrecta en documento operativo. | Ninguno esta ejecución — decisión de visibilidad no la toma una sesión técnica (ya señalado en `TECHNICAL_STATE.md`, P1 punto 4, sin resolver desde 27-ago). | N/A | Sigue pendiente de decisión del Founder (cambiar CLAUDE.md o cambiar visibilidad del repo). |
| 5 | `00 LEER PRIMERO` §11 (Drive): "Cuando el Founder dice 'dame 10 imágenes'... 2) Consultar memoria real." | Ahora cumplido en el código real (ver fila 3) — antes de la sesión del 16/17-sep no existía memoria real que consultar en absoluto. | RESUELTO (acumulado entre dos sesiones) | — | Ver filas 3 y la incorporación de fuente #5 (sesión del 16-sep). | Ver fila 3. | Consistente. |
| 6 | `visual/README.md` como punto de entrada del módulo. | Desactualizado: no mencionaba `memoria_fuerte.py`, `pedagogia.py`, `market_signal.py`, `topic_classification.py`, el contrato TEXT_TO_IMAGE/IMAGE_EDIT, ni el generador multi-factor real. | CORREGIDO esta ejecución | Divergencia doc↔código: un agente nuevo habría reconstruido desde `docs/` (25+ archivos) en vez de leer un punto de entrada. | Sección "ACTUALIZACIÓN 17-sep-2026" añadida (aditiva, no se borró nada existente). | N/A (documentación) | Punto de entrada ahora reflect el estado real completo. |

## Prueba de lotes a escala (§15)

Reserva real de 250 candidatos (`universe.build_reserve(seed=42, factor=25)`)
medida por `familia_editorial`: distribución prácticamente uniforme, sin
familia dominante (máximo observado 5.2%, mínimo 0.4% — 58 familias sobre
250 candidatos). Sin sesgo narrativo ni digital medible en el generador
combinatorio.

8 tandas de selección real de 10 (`generator.seleccionar_lote()`, seeds
501-505 y 601-604) con el motor pedagógico activo: 70-80% conocimiento
jurídico en las 8, familias narrativas presentes en todas — nunca 0,
nunca dominante. Sin el mecanismo, las mismas semillas producen 90-100%
conocimiento (medido, no estimado) — confirma que el mecanismo corrige un
riesgo real de infrarrepresentación de narrativa, no uno de sobre-
representación (el sesgo que el Founder reporta percibir probablemente no
viene del motor combinatorio automático, sino de lotes curados a mano en
sesiones anteriores o de la influencia de memoria fuerte real, cuyo
contenido de mejor rendimiento histórico SÍ es mayormente narrativo —
exactamente la señal que el balance pedagógico ahora contrapesa).

## Pruebas (§14)

- `cd visual && python3 -m unittest discover -p "test_*.py"` → **1091
  tests, OK** (suite completa fresca, tras todos los cambios de esta
  ejecución).
- `npm ci && npm run typecheck` → limpio, sin errores (dependencias no
  estaban instaladas en este contenedor; instaladas para poder ejecutar
  el check real, no asumirlo).
- `npm audit` → 3 vulnerabilidades altas (fast-uri, js-yaml, nanoid,
  transitivas) → `npm audit fix` (sin `--force`) → 0 vulnerabilidades,
  typecheck sigue limpio.
- Regresión real detectada y corregida durante esta misma ejecución:
  `demo_produccion_real_10_temas_nuevos.py` (referencia congelada del
  16-sep-2026) dejó de reproducir su lote exacto porque el nuevo balance
  pedagógico desplazó la selección greedy — 7 suites afectadas en
  cascada. Corregido desactivando explícitamente el ajuste sólo en esa
  llamada (`objetivo_conocimiento=None`, documentado en el código),
  preservando la reproducibilidad de ese artefacto histórico sin apagar
  el mecanismo en el motor real.

## No implementado — deliberadamente fuera de esta ejecución

- Reescribir `docs/TECHNICAL_STATE.md` completo: su alcance (verificación
  jurídica/publicación) sigue vigente y no cambió esta ejecución; se le
  añadió una nota de vigencia en vez de reescribirlo entero, para no
  introducir errores en una sección que no se auditó línea por línea.
- Motor de producción masiva (`docs/contrato-motor-masivo.md`): sigue
  deliberadamente NO CONSTRUIDO, sin cambios — es una decisión de alcance
  del Founder, no un pendiente técnico de esta sesión.
- Integración con Grok/Manus/Gemini, agentes y hooks descritos en Drive:
  siguen sin implementarse — P3, explícitamente "no ahora".
- Proveedor de imagen real: sigue bloqueado por falta de credenciales; no
  se simuló ni se declaró resuelto.
