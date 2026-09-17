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
| Orden CONCEPTO→TENSIÓN→METÁFORA→DIRECCIÓN ARTÍSTICA (Contrato v4 §4) | 🟢 RESUELTO (continuación, ver §16) | `visual/direccion_causal.py`, wireado en `art_direction.py` — ver §13 tabla, fila 1 (actualizada) |
| `legalmente-web` (visibilidad, `CLAUDE.md §8`) | 🟢 RESUELTO — sin cambio necesario | `CLAUDE.md` ya decía "público" (commit `9e4bded`, 31-ago-2026); la contradicción era de `TECHNICAL_STATE.md`, no de `CLAUDE.md`. Ver §16. |
| `legalmente-story-engine`, 6 agentes, 4 hooks | ⚫ NO IMPLEMENTADO (confirmado, sin cambio) | `docs/TECHNICAL_STATE.md` §3 |
| Proveedor de imagen real | ⚫ BLOQUEADO EXTERNAMENTE | Sin credenciales en el workspace; Higgsfield prohibido por CLAUDE.md |
| `visual/README.md` (punto de entrada) | 🟢 CORREGIDO | Desactualizado desde 16-sep-2026 respecto a memoria fuerte/pedagogía/contrato — actualizado esta ejecución |
| `docs/TECHNICAL_STATE.md` | 🟢 RECONCILIADO (continuación, ver §16) | Reconciliado línea por línea el 17-sep-2026 — ver §16 |
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
| 1 | Contrato v4 §4-5: "El concepto jurídico debe gobernar la propuesta visual. CONCEPTO → TENSIÓN → IDEA → METÁFORA → ESCENA → DIRECCIÓN ARTÍSTICA. Y después selección de recursos." | **RESUELTO en la continuación (17-sep-2026, mismo día):** `visual/direccion_causal.py` deriva SIGNIFICADO (concepto/tensión ya reales; movimiento_juridico de `necesidad`; grado_abstraccion de `profundidad`) y restringe `realism`/`visual_mechanism` del catálogo (2 de 10 dimensiones) por coincidencia textual auditable ANTES de seleccionar — wireado en `art_direction.draft_visual_brief()`, reemplazando la llamada ciega a `vf.seleccionar_huella()`. | RESUELTO (parcial, honesto: 2/10 dimensiones causadas; las otras 8, incluida la biblioteca de 504 direcciones, siguen rotando por anti-repetición — filtrarlas exigiría la misma afinidad fabricada que se evitó a propósito) | El orden algorítmico ahora SÍ es SIGNIFICADO → restricción del catálogo → selección — ya no invertido. `objeto_protagonista`/metáfora/escena siguen `PENDIENTE_CONTENIDO` (autoría humana, sin cambio). | 24 tests nuevos (`test_direccion_causal.py`): materia no determina estilo, cambiar tensión cambia el pool con la misma materia, ninguna dirección domina un lote de 10, memoria evita repetición, determinismo bajo semilla, diversidad real entre 3 tandas. | 1115 tests, OK (suite completa). Ver `visual/direccion_causal.py` para el detalle causal completo y §16 de este documento. |
| 2 | Mandato Maestro §1-3 (17-sep-2026, este mismo mandato): balance ~70/30 conocimiento/narrativa, configurable, no cuota. | Antes de esta ejecución: no existía ningún mecanismo — medido que el selector converge a 90-100% conocimiento sin intervención (narrativa, 5/58 familias, no favorecida por ningún otro factor). | RESUELTO esta ejecución | — | `visual/pedagogia.py` (nuevo) + `generator.ajuste_balance_pedagogico` wireado en `puntuar_candidato()`/`seleccionar_lote()`. | 18 tests nuevos (`test_pedagogia.py`) + verificación empírica (8 tandas reales, seeds 501-505/601-604) | 70-80% conocimiento sostenido con el mecanismo activo (antes: 90-100%); narrativa presente en todas las tandas. |
| 3 | Mandato Maestro §6 (17-sep-2026): memoria fuerte debe influir en "selección temática; novedad; anti-repetición; dirección visual...", no sólo en un documento pasivo. | Antes de esta ejecución (sesión previa, 16-sep): memoria fuerte conectada SÓLO a dirección visual (`draft_visual_brief`), no a selección temática. | RESUELTO esta ejecución (extensión) | — | `generator.ajuste_afinidad_founder(candidato, memoria, memoria_fuerte=None)` — suma preferencias reales de fuente #5 a la selección temática, mismo techo acotado. `production_run.py` la propaga también a `generator.seleccionar_lote()`. | 2 tests nuevos en `test_generator.py` + verificación empírica confirmando que el balance pedagógico se sostiene incluso con esta señal narrativa-heavy activa. | Selección temática ahora aprende de curaduría Founder real, con el mismo tope de siempre — verificado que no desplaza el balance 70/30 del punto 2. |
| 4 | `CLAUDE.md §8`: (según se citó erróneamente en el reporte ejecutivo anterior de esta sesión) "legalmente-web es privado". | **CORRECCIÓN (17-sep-2026): `CLAUDE.md §8` YA dice "público"**, correctamente, desde el commit `9e4bded` (31-ago-2026) — leído y confirmado línea por línea en esta sesión. La contradicción real estaba en `docs/TECHNICAL_STATE.md` (§1 y §7 P1.4), que nunca se actualizó tras esa corrección, y el reporte ejecutivo anterior de esta misma sesión la repitió citando ese documento sin releer `CLAUDE.md`. | RESUELTO — no era una divergencia Drive↔código real, era un documento secundario desactualizado citado sin verificar la fuente primaria. | Ninguno en `CLAUDE.md` (no lo necesitaba). El gap real era `TECHNICAL_STATE.md` desactualizado. | Ninguno — reverificación directa: lectura de `CLAUDE.md` + `git ls-remote` anónimo real (HEAD `3d9d298`, hoy). | `docs/TECHNICAL_STATE.md` §5.1 y §7 P1.4 corregidos en el mismo ciclo. Lección operativa reforzada: releer la fuente primaria, no el documento que la cita. |
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
  ejecución). **Actualización (continuación, §16): 1115 tests, OK** tras
  añadir el compilador causal.
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

## §16 — Continuación (17-sep-2026, mismo día): cierre de los 3 pendientes que el reporte anterior había dejado abiertos

El Founder pidió explícitamente no dar el mandato por cerrado mientras
quedaran pendientes internos ejecutables. Se cerraron los tres señalados:

1. **Gap causal del motor visual (Contrato v4 §4)** — RESUELTO. Ver fila 1
   de la tabla de arriba (actualizada) y `visual/direccion_causal.py`. No
   se construyó una tabla "concepto = estilo" (prohibida explícitamente
   por la instrucción de continuación): se separó SIGNIFICADO (derivado de
   `necesidad`/`profundidad`/`relacion`, campos ya reales) de la
   restricción del catálogo (por coincidencia textual auditable contra el
   vocabulario real de `realism`/`visual_mechanism`, nunca una afirmación
   "el concepto X pertenece al estilo Y"). Bug real encontrado y corregido
   durante la construcción: `memory.normaliza()` colapsa frases con "/" a
   cadena vacía, que como substring "coincide" con cualquier texto — un
   filtro que dejaba de filtrar en silencio hasta que se detectó
   (`test_direccion_causal.py::TestTextoLibre`).
2. **`CLAUDE.md §8` — verificado de nuevo, NO tenía la contradicción
   reportada.** El reporte ejecutivo anterior de esta sesión afirmó,
   citando `docs/TECHNICAL_STATE.md` sin releer `CLAUDE.md` directamente,
   que `CLAUDE.md §8` decía "privado". Falso: `CLAUDE.md` ya decía
   "público" desde el commit `9e4bded` (31-ago-2026) — confirmado leyendo
   el archivo real y con `git ls-remote` anónimo hoy (HEAD `3d9d298`). El
   documento desactualizado era `TECHNICAL_STATE.md`, no `CLAUDE.md` — ver
   punto 3. Ningún cambio a `CLAUDE.md` fue necesario ni se hizo.
3. **`docs/TECHNICAL_STATE.md` reconciliado línea por línea**, no
   pospuesto. Cambios reales: fila `legalmente-web` corregida (ver punto
   2), `contract/` actualizado de 12 a 17 tests (re-verificado con
   ejecución real), fila "Motor de generación visual" corregida de "124
   pruebas" a la cifra real (1115, remitiendo a `visual/README.md` en vez
   de duplicar una cifra que volverá a desactualizarse), §5 con la
   corrección completa (ANTES/EVIDENCIA/CAMBIO/DESPUÉS), §7 P1.4 marcado
   resuelto, y una sección §9 nueva que lista explícitamente qué P1-P3 NO
   se tocaron esta sesión (para no dar una falsa sensación de que "todo"
   quedó reconciliado).

**Re-auditoría de pendientes (repetida, mandato de continuación):** el
mismo barrido de 15 palabras clave (`TODO`...`EXPERIMENTAL`) sobre el
repositorio completo (incluidos los archivos nuevos de esta sesión) sigue
sin encontrar ningún pendiente interno ejecutable nuevo — todos los
"nuevos" hallazgos frente al barrido anterior son: (a) el propio texto de
este documento citándose a sí mismo, (b) constantes reales
(`NEXT_EXECUTABLE_ACTION`, `NEXT_SESSION_PROMPT.md`), (c) falsos positivos
de substring (`TEMPORAL`/`ATEMPERADO` conteniendo "TEMP"). Cero deuda
nueva.

**Verificación end-to-end real:** `production_run.ejecutar()` con dos
semillas reales corrió el compilador causal a través del driver de
producción completo — `qa_dos_ejes().aceptado == True`,
`memoria_fuerte_ok == True`, sin ninguna excepción.

## No implementado — deliberadamente fuera de esta ejecución

- Motor de producción masiva (`docs/contrato-motor-masivo.md`): sigue
  deliberadamente NO CONSTRUIDO, sin cambios — es una decisión de alcance
  del Founder, no un pendiente técnico de esta sesión.
- Integración con Grok/Manus/Gemini, agentes y hooks descritos en Drive:
  siguen sin implementarse — P3, explícitamente "no ahora".
- Proveedor de imagen real: sigue bloqueado por falta de credenciales; no
  se simuló ni se declaró resuelto.
- Restringir las 8 dimensiones restantes de la huella (más allá de
  `realism`/`visual_mechanism`) por significado: exigiría el mismo tipo de
  afinidad fabricada que el mandato de continuación prohibió
  explícitamente construir sin evidencia real — no se hizo.
- `objeto_protagonista`, metáfora y escena concretos por candidato: siguen
  `PENDIENTE_CONTENIDO` — contenido creativo/editorial, no infraestructura;
  no se fabrican.
- Cierre de PR #26/#28 de `legalmente-web`, detección de deriva de fuentes
  oficiales, detección de duplicados por paráfrasis: sin cambios, fuera del
  alcance de esta sesión (ver `docs/TECHNICAL_STATE.md` §9, nuevo).
