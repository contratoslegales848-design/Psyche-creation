# Arquitectura real de LegalMente — auditoría y reconciliación 2026-09-13

**Base:** rama `claude/legalmente-architecture-reconciliation-xojn4i` sobre `main` en `ef7ffdd`.
**Fuente nueva obligatoria:** `LegalMente — Handoff Founder 2026-09-13`.
**Autoridades leídas:** `00 LEER PRIMERO` (7-sep), `Índice maestro v18`, `Capa canónica de
diversidad editorial y universo temático v1`, `Arquitectura del Corazón y Sistema Vivo V1`,
`Guía operativa del motor de dirección artística`, `Bitácora de cambios (ciclo 2026-09)`.

Regla de lectura (`CLAUDE.md §2`): **una mención en Drive no es una capacidad implementada.**
Todo lo marcado IMPLEMENTADO aquí tiene archivo real y prueba que pasa.

---

## 1. Clasificación de componentes

### CANÓNICO + IMPLEMENTADO (evidencia ejecutable)

| Componente | Archivo | Pruebas |
|---|---|---|
| Verificación jurídica (claim packets v4) | `.claude/skills/legalmente-legal-verification/` | 245 |
| Contrato canónico cross-repo | `contract/canonical_envelope.py` | 17 |
| Procedencia de contenido | `scripts/validate-content-provenance.py` | 34 |
| Pipeline visual (brief→plan→compilador→proveedor→QA→receipt) | `visual/{brief,plan,compiler,pipeline,qa,gates,receipts,registry}.py` | incluidas en las 521 |
| Composición tipográfica real | `visual/compositor.py` | " |
| Motor de rutas conceptuales | `visual/route_engine.py`, `route_sync.py` | " |
| Memoria **visual** anti-repetición | `visual/memory.py` | " |
| Rotación y diversidad visual de lote | `visual/rotation.py` | " |
| Inventario de estado y bandeja humana | `visual/inventory.py`, `command_center.py` | " |
| Feedback humano → mutación de brief | `visual/feedback.py` | " |

### IMPLEMENTADO EN ESTA SESIÓN (hueco P0/P1 cerrado)

| Componente | Archivo | Pruebas |
|---|---|---|
| Huella semántica de 22 campos | `visual/semantic_fingerprint.py` | 22 |
| Universo editorial abierto (58 familias) | `visual/editorial.py` + `policy/editorial-universe-v1.json` | 31 (con universo) |
| Reserva combinatoria y selección jerárquica | `visual/universe.py` + `policy/materias-seed-v1.json` | " |
| Motor emocional estructural | `visual/emotion.py` | 22 |
| Memoria semántica con estados y aprendizaje | `visual/semantic_memory.py` | 23 |
| QA de lote como sistema + telemetría | `visual/batch_qa.py` | 21 |
| Carriles LinkedIn | `visual/lanes.py` | 19 |
| Ciclo vertical del organismo | `visual/organism.py` | 28 |

### IMPLEMENTADO Y PROBADO — FASE 2 (memoria histórica)

| Componente | Archivo | Pruebas | Estado |
|---|---|---|---|
| Snapshot inmutable del corpus (174 piezas) | `corpus/` | — | IMPLEMENTADO |
| Importador idempotente + clasificación retroactiva | `visual/corpus_import.py` | 30 | IMPLEMENTADO Y PROBADO |
| Análisis: repetición, clusters, zonas sin explorar | `visual/corpus_analysis.py` | 18 | IMPLEMENTADO Y PROBADO |
| Calibración del umbral contra corpus real | `visual/calibration.py` | 16 | IMPLEMENTADO Y PROBADO |
| Las cinco distinciones de la memoria | `visual/test_distinciones_memoria.py` | 14 | PROBADO |
| Regresión contra las 174 históricas | `visual/test_regresion_historica.py` | 14 | PROBADO |
| Integridad del descubrimiento de CI | `visual/test_ci_discovery.py` | 6 | IMPLEMENTADO Y PROBADO |
| Estado `HISTORICA` en la memoria | `visual/semantic_memory.py` | incluidas | IMPLEMENTADO Y PROBADO |

**Hallazgos medidos sobre el corpus real (no estimados):**
- 174 metáforas distintas de 174 piezas: **la capa visual sí estaba diversificada.**
- 85 de 174 piezas (48%) comparten la misma función editorial inferida: **el
  problema estaba en la capa editorial**, como sostenía el fundador.
- Al umbral de bloqueo vigente (0.25) hay **0 clusters de duplicados**: el banco
  v3 cumplió lo que prometía, 174 temas realmente distintos. No existen "10 o 20
  piezas que sean la misma pregunta jurídica".
- 45 de 58 familias editoriales **nunca se han usado**; 6 materias no tienen una
  sola pieza; sólo 77 de 1.160 combinaciones materia × familia se han producido.

**Umbral calibrado:** 0.30 → **0.25**. En 0.30 aparecían 3 falsos positivos
(LM-151~152, LM-063~050, LM-077~079): misma materia, preguntas distintas —
justo lo que el canon prohíbe bloquear.

### IMPLEMENTADO Y PROBADO — FASE 3 (calibración Founder, saturación, territorio, generador)

| Componente | Archivo | Pruebas | Estado |
|---|---|---|---|
| Hoja de revisión Founder + incorporación trazable | `visual/founder_review.py` | 20 | IMPLEMENTADO Y PROBADO |
| Enriquecimiento de concepto_nucleo/pregunta_resuelta | `visual/corpus_enrichment.py` | 20 | IMPLEMENTADO Y PROBADO |
| Saturación editorial (distinta de repetición semántica) | `visual/editorial_saturation.py` | 9 | IMPLEMENTADO Y PROBADO |
| Territory Explorer (novelty/coverage/opportunity) | `visual/territory_explorer.py` | 18 | IMPLEMENTADO Y PROBADO |
| Subfunciones de `caso_cotidiano` | `corpus_analysis.analizar_caso_cotidiano` | 8 | IMPLEMENTADO Y PROBADO |
| Generador multi-factor con hard gates | `visual/generator.py` | 25 | IMPLEMENTADO Y PROBADO |
| Founder Selection Rate por eje | `visual/founder_metrics.py` | 12 | IMPLEMENTADO Y PROBADO |
| `corpus/eval-umbral-candidato.json` → revisión Founder | pendiente de respuesta | — | **ESPERANDO AL FOUNDER** |

**El umbral sigue calibrado sólo con etiquetas del agente.** `founder_review.py`
genera la hoja de revisión y la incorpora sin destruir el original
(`corpus/eval-umbral-founder.json`, ausente hasta que el Founder responda);
`calibration.py` ya prefiere ese fichero cuando exista, con fallback
transparente al del agente. Nadie ha respondido todavía — **acción pendiente
para el Founder**, no un hueco técnico.

**Dos controles separados, verificados como independientes** (`test_generator.
TestHardGates.test_saturacion_alta_bloquea_aunque_sea_semanticamente_nueva`):
repetición semántica (¿ya dijimos esto?, contra el corpus entero) y saturación
editorial (¿hemos usado demasiado esta función últimamente?, sólo contra
producción reciente — HISTORICA queda fuera para no prohibir `caso_cotidiano`
para siempre). Una pieza puede pasar la primera y ser rechazada por la
segunda.

**Territory Explorer, alcance declarado:** traza la malla MATERIA × FAMILIA
EDITORIAL en detalle (77/1.160 combinaciones sobre el seed original, **77/1.508**
tras incorporar `migracion` y `cultura_y_literatura_juridica` — coverage
global **5,11%**); los otros cinco ejes (necesidad, ángulo, rol, contexto,
profundidad) se informan como cobertura marginal, no como malla completa de 8
dimensiones — con los datos actuales esa malla sería casi toda vacía por
escasez, no por vacío editorial real.

**Hallazgo de la Fase 6:** de las 85 piezas `caso_cotidiano`, **42 (49%)**
tienen subestructura léxica detectable (omisión no actuada, alcance
extendido, apariencia engañosa, relato explícito…) que mapea a
advertencia/consecuencia/riesgo/error/explicación. Las otras 43 quedan
honestamente sin marcador — no se fuerza una subfunción donde no hay
evidencia. Confirma parcialmente la hipótesis del Founder: una parte real del
48% sí era un problema de clasificación, no sólo de producción.

**El generador (Fase 7) tiene tres hard gates**, no penalización blanda:
repetición semántica, saturación editorial ALTA, y cuota de materia agotada
(`00 LEER PRIMERO` §3.A). Seis factores con evidencia real entran en el score
compuesto (semantic_novelty, editorial_diversity, territory_coverage,
utility, emotional_fit, recent_cooldown); tres se declaran **PENDIENTE** en
vez de fabricarse: `legal_support` (no hay verificación jurídica sobre un
candidato combinatorio todavía), `human_interest` (0 métricas reales, y el
texto de `pregunta_resuelta` es plantilla fija — un proxy léxico sería ruido
constante, no señal) y `visual_distance` (sin plan visual en esta etapa).

**Defecto real encontrado y corregido durante esta fase:** el ajuste de
afinidad del Founder (`ajuste_afinidad_founder`) se sumaba al score y se
recortaba a `[0,1]` — pero con territorio muy virgen (el caso normal: 5,11%
de cobertura) casi todos los candidatos ya tocan el techo de 1.0 por pura
novedad, así que el recorte volvía el ajuste invisible justo cuando más
importa. El desempate en `generator.seleccionar_lote` ahora usa el valor SIN
recortar como criterio secundario — verificado con
`test_lote_posterior_a_una_curaduria_refleja_la_preferencia`: sin el fix, el
lote posterior a una curaduría no heredaba ninguna preferencia (0/10); con
el fix, todas las piezas heredan afinidad de los ejes coincidentes cuando el
material está disponible.

### PENDIENTE / NO CONECTADO — declarado, no implementado
- Métricas de rendimiento: **0 entradas**. `selection_rate` sigue siendo la única
  señal real de aprendizaje.
- Repositorio histórico de Remotion (guiones completos): **inaccesible**.
- El conjunto de calibración está **etiquetado por el agente**, no por el Founder
  — hoja de revisión lista en `founder_review.generar_hoja_revision()`.
- `direccion_artistica` y `hook` por candidato: no existen en la etapa
  combinatoria (`universe.TopicCandidate`); nacen en `brief.py`/`pipeline.py`,
  después de la verificación jurídica. `founder_metrics.py` ya declara estos
  ejes como `EJES_PENDIENTES` en vez de fabricar una tasa sobre datos
  inexistentes.

### PILOTO / PROPUESTA
- Piezas 01–03 del piloto: `pieza-01-reales` en `APTO_PARA_NARRATIVA` con gate CERRADO;
  02 y 03 en `REQUIERE_INVESTIGACION`. La aprobación humana de la pieza 01 vive en una rama
  **sin fusionar** — decisión humana pendiente, no paso técnico.
- `docs/contrato-motor-masivo.md`: contrato definido, motor deliberadamente no construido.

### AUXILIAR
- `scripts/check-unittest-main-guard-position.py` (higiene), `visual/observability.py`,
  `visual/runtime_config.py`, `visual/inspection.py`.

### LEGACY / SUPERADO
- Índices maestros v8–v17 en Drive (`00 — Archivo`, marcados SUPERADO). No borrados.
- Bancos finitos de prompts (300→174): **semilla**, nunca universo temático.

### HUÉRFANO (existe, no está conectado)
- `visual/registry.py` (AssetRegistry) vive en directorios efímeros y no sobrevive entre
  sesiones; `inventory.py` deliberadamente **no** lo lee para no mentir.
- `handoff/legalmente-web/`: serie de patches verificada localmente, **sin empujar**
  (cuentas distintas, `CLAUDE.md §8`).
- Métricas de rendimiento: 0 entradas del historial tienen métricas reales. Toda ponderación
  por rendimiento sigue siendo decorativa. **Es el cuello de botella del aprendizaje.**

---

## 2. Contradicciones encontradas

1. **`familias` significaba dos cosas.** `visual/families.py` registra familias VISUALES
   (óleo, claroscuro); la `Capa canónica de diversidad` exige familias EDITORIALES (mito,
   checklist, etimología). Eran ejes ortogonales con el mismo nombre. **Ésta es la raíz
   del defecto que reporta el fundador**: diez estilos distintos sobre diez definiciones
   siguen siendo diez definiciones. Resuelto separando `editorial.py` de `families.py`.

2. **La memoria no podía detectar repetición semántica.** `memory.py` puntúa escena,
   sujeto, cámara, metáfora y objeto. Cambiar el estilo artístico bastaba para pasar su
   control con el mismo contenido. Resuelto en `semantic_fingerprint.py`, donde hook,
   formato y emoción **no participan** en la distancia semántica.

3. **CI nombraba 5 de 17 suites visuales.** Memoria, rotación, motor de rutas e inventario
   nunca se ejecutaban en CI. Resuelto con `unittest discover`.

4. **Pillow no estaba instalado en el entorno**, lo que hacía fallar 11 pruebas del
   compositor. No era un fallo de código: `pip install -r requirements.txt` lo resuelve.

5. **`CLAUDE.md §8` declaraba `legalmente-web` privado**; el propio archivo ya registra la
   corrección (verificado público el 2026-08-31). Sin acción pendiente.

---

## 3. El ciclo, ejecutable

```
NECESIDAD → CANDIDATO → HUELLA SEMÁNTICA → RESERVA AMPLIA → DIVERSIDAD
→ PERFIL EMOCIONAL → QA DE LOTE → CURATION_READY
→ CURADURÍA DEL FOUNDER → MEMORIA → APRENDIZAJE → NUEVA GENERACIÓN
```

Demostración: `cd visual && python3 demo_ciclo.py`.

**Producción continua (Handoff §5):** `organism.producir_lote()` no recibe ni consulta
ninguna aprobación previa. Su estado terminal es `CURATION_READY` y el ciclo completo no
puede dejar ninguna huella en `APROBADA` ni `PUBLICADA` — probado en
`test_organism_cycle.py`. Publicación, merge y deploy siguen siendo gates separados.

---

## 4. Lo que sigue SIN estar conectado (no declarar integrado)

| Subsistema | Estado real |
|---|---|
| Proveedor de imagen real | Adapter HTTP probado con transporte inyectable; **cero llamadas externas ejecutadas**. Sin créditos. |
| Video (Remotion) | Renderiza y exige procedencia, pero **no consume** `TopicCandidate` ni el perfil emocional. |
| Web (`legalmente-web`) | Consumidor del Canonical Envelope probado localmente; **no se puede empujar** desde este repo. |
| Aplicación | No existe. |
| Señales/dudas externas | No existe captura. El motor genera candidatos combinatorios, no escucha al público todavía. |
| Reacciones / analytics | No existe ingesta. `selection_rate` es hoy la única señal real disponible. |
| Instagram | Bloqueado por autorización pendiente. |

---

## 5. Riesgos

1. **`selection_rate` es la única señal de aprendizaje real.** Sin métricas de rendimiento,
   el sistema aprende sólo del gusto declarado del fundador. Es mejor que nada y es
   exactamente lo que pidió el Handoff, pero no sustituye a datos de audiencia.
2. **Los umbrales están calibrados contra pares sintéticos**, no contra el corpus histórico
   de 174 guiones. Conviene recalibrar `UMBRAL_EQUIVALENCIA` cuando ese corpus esté
   disponible como huellas.
3. **`register_familia` no detecta duplicidad semántica.** El canon exige que una familia
   nueva no duplique otra; esa valoración se deja explícitamente a un humano en vez de
   fingir un juicio automático.
4. **Confidencialidad**: sigue sin control automatizado de contenido identificable sin
   marcadores léxicos (hueco conocido, red team B5). Este trabajo no lo toca.
5. El motor combinatorio puede producir combinaciones jurídicamente vacías; por eso todo
   candidato nace `NO_VERIFICADO` y la verificación jurídica sigue siendo obligatoria.

---

## 6. Reconciliación con la línea ChatGPT (2026-09-14)

**Aclaración estructural primero, porque cambia la forma de "reconciliar":**
las dos líneas viven en **repositorios distintos, cuentas distintas**:

| | Repositorio | Cuenta | Rama | SHA |
|---|---|---|---|---|
| Esta línea | `Psyche-creation` | `contratoslegales848-design` | `claude/legalmente-architecture-reconciliation-xojn4i` | `57baf5b0c21f2bcbeec7ba250d0bc363a46299ce` (antes de esta sesión) |
| Línea ChatGPT | `legalmente-web` | `legallmente-alt` | `chatgpt/image-generator-reconciliation-v2-2026-09-13` | `27df096e54e9ca4c5552eb26bbe60319d4ef70d5` (confirmado) |

`CLAUDE.md §8` ya lo declara: sesiones de este repo pueden **leer y trabajar
`legalmente-web` en local**, pero no hacer push ni operar sus PRs. Por tanto
esta reconciliación es de **ontología y contrato**, no de historial git: no
se copia código TypeScript a este repo ni se toca `legalmente-web`. Se leyó
el diff real (58 archivos, +4896/-204 líneas contra `merge-base
46948a0`), se instalaron sus dependencias y se **ejecutó de verdad** su
suite — `npm run test:convergence`: **62/62 tests reales, 0 fallos**
(19 production-policy + 9 visual-argument + 8 visual-factory + 6
image-generator + 6 production-learning + 7 production-runtime + 7
release-readiness); `npx tsc --noEmit` limpio. No se asumió el reporte de
la otra línea: se verificó.

### Matriz de reconciliación

| Capacidad | Esta línea (Python) | Línea ChatGPT (TS) | Solapamiento | Conflicto | Decisión | Implementación final |
|---|---|---|---|---|---|---|
| Repetición semántica | `semantic_memory.py`, corpus histórico incluido | `production-policy`: `productionContentFingerprint`, memoria fuerte/corta | Alto — mismo principio, mismos 3 estados fuerte/2 cortos | No | **KEEP_CLAUDE** | Sin cambios; ya cubre HISTORICA, ausente en TS |
| Saturación editorial | `editorial_saturation.py` (Fase 3, esta sesión) | No existe como control separado — TS mezcla familia dentro de `batch.ts` (sólo diversidad de lote) | Parcial | No | **KEEP_CLAUDE** | Sin cambios; es una distinción que la línea TS no hace |
| Territory Explorer | `territory_explorer.py` novelty/coverage/opportunity | No existe | Ninguno | No | **KEEP_CLAUDE** | Sin cambios |
| Enriquecimiento histórico | `corpus_enrichment.py`, 5 niveles de confianza | No existe (no hay corpus histórico cargado en TS) | Ninguno | No | **KEEP_CLAUDE** | Sin cambios |
| Calibración Founder (umbral) | `founder_review.py`, hoja de 18 pares, pendiente de respuesta | No existe | Ninguno | No | **KEEP_CLAUDE** | Sin cambios |
| Founder learning / explotación | `generator.ajuste_afinidad_founder`, acotado, 0 sin curaduría | `learning.ts`: `founderSelectionMetrics` por eje, sin sesgo de selección hacia el generador | Parcial — TS mide, no realimenta la selección | No | **MERGE_CONCEPTS** | Se conserva el sesgo acotado de Python; `founder_metrics.py` ya iguala el desglose por eje de `learning.ts` |
| Emoción → tratamiento visual | `emotion.py` causal (composición/cámara/luz nacen del perfil) | `IMAGE_GENERATOR_INVARIANTS.emotionChangesVisualTreatment: true` **declarado, no aplicado** — `emotion` es un string libre sin derivación | Nominal únicamente | **Sí — hallazgo real** | **KEEP_CLAUDE** | Sin cambios en emotion.py; se añadió `art_direction.py` con prueba causal explícita (`test_la_imagen_nunca_se_genera_exactamente_igual_bajo_otra_emocion`) |
| Argumento visual (qué hace la imagen) | No existía | `visual-argument/index.ts`: 11 `VISUAL_FUNCTIONS`, `SceneStrategy`, validación de lote | Ninguno antes de esta sesión | No | **REIMPLEMENT_CLEANLY** | `art_direction.py` (nuevo): mismo vocabulario de 11 funciones, implementación propia en Python, mapeo por familia editorial/necesidad con procedencia declarada |
| Brief de generación de imagen | `brief.py` (`VisualBrief`, preexistente, canónico) | `image-generator/types.ts` (`ImageGenerationBrief`) | Conceptual — campos equivalentes, nombres distintos | No (son contratos de capas distintas: Python aún no verifica; TS asume verificación previa) | **DEFER** | `art_direction.draft_visual_brief` produce un BORRADOR pre-verificación, explícitamente no autorizado; conectar con `brief.py` real exige que exista primero un `ProductionHandoff` — fuera de alcance de esta sesión |
| Dirección artística / familia visual | `families.py` (8 familias, catálogo **cerrado**) | `artStyleRegistryIsOpen: true`, string libre | Bajo | **Sí — techo real** | **CONFLICT_REQUIRES_FOUNDER** | `art_direction.verificar_diversidad_de_estilos` usa `min(8, n)` como techo honesto, documentado; ampliar el catálogo a 10+ familias es decisión de contenido/arte, no técnica |
| Memoria visual / distancia visual | `memory.py` (score ponderado 0-100) | `production-policy`: distancia estricta 8 dimensiones, mínimo 5 cambiadas, 3 vecinos por ámbito (lote/historia) | Ejes parcialmente distintos | No | **MERGE_CONCEPTS** | `visual_distance.py` (nuevo): la regla estricta de TS, implementación propia en Python sobre los mismos campos de `VisualMemoryEntry` — no sustituye a `memory.py`, lo complementa |
| Lote QA — diversidad | `batch_qa.py`, `rotation.py` | `batch.ts`: máx. 2/materia, máx.1 digital, `imageVisualFingerprint` único por lote | Alto | No | **KEEP_CLAUDE** | Cuotas ya vivían en `universe.py`/`generator.py` con la misma proporción |
| Marca física, nunca overlay | `policy/legalmente-visual-policy-v1.json` (`integracion_fisica_requerida: true`) | `production-policy`: `brandIntegration !== "PHYSICAL_SCENE"` es error | Idéntico | No | **KEEP_CLAUDE** | Ya implementado, ambas líneas coinciden sin ajuste |
| Copy exacto no confiado al generador | `policy`: `texto_marca_lo_escribe_el_generador: "NO"`, composición posterior determinista | `validation.ts`: prohíbe que `artDirection` sustituya al argumento de imagen; `baseArtContainsNoFinalCopy: true` | Idéntico en espíritu | No | **KEEP_CLAUDE** | Ya implementado |
| Neutralidad panhispánica | Jurisdicción por defecto conceptual/comparada (CLAUDE.md §4) | `territoryMode: "PANHISPANIC_NEUTRAL" \| "VERIFIED_LOCAL"`, explícito en el prompt | Alto | No | **DEFER** | El principio ya rige; una bandera explícita por pieza (`territoryMode`) sólo tiene sentido cuando exista generación real — se deja para esa fase |
| Gate de proveedor prohibido | No existía | `runtime.ts`: bloquea "higgs"+"field" antes de generar, fail-closed | Ninguno antes de esta sesión | **Sí — hallazgo real** | **REIMPLEMENT_CLEANLY** | `provider_gate.py` (nuevo): mismo principio, denylist propia en Python |
| Carriles LinkedIn | `lanes.py` (3 carriles, memorias separadas) | `channel-strategy.ts` (4 canales, perfiles de estilo, regla de 75% escenas operativas) | Parcial | No | **MERGE_CONCEPTS** | `lanes.verificar_ratio_operativo` (nuevo): la regla del 75% portada a Python |
| CI | `unittest discover` sobre `visual/` | `production-policy-ci.yml`, scoped por paths, incluye build+typecheck+lint | Ninguno (repos distintos) | No | **DEFER** | Cada repo mantiene su propio CI; no hay CI cruzado posible sin permisos de push a `legalmente-web` |
| Telemetría / Founder Selection Rate | `founder_metrics.py`: por materia/familia/necesidad/emoción, muestra visible | `learning.ts`: por matter/editorialFamily/emotion/artDirection/need, `lowSample` | Alto | No | **KEEP_CLAUDE** | Ya cubre los mismos ejes; se añadió aviso textual donde TS sólo marca un booleano |

### Hallazgos reales (no reportados por ninguna de las dos líneas hasta ahora)

1. **`emotionChangesVisualTreatment: true` está declarado y no aplicado** en
   la línea ChatGPT — es exactamente el patrón que `CLAUDE.md §2` advierte
   ("una mención no es una capacidad implementada"), esta vez encontrado en
   el otro repositorio. La línea Python sí lo cumple y ahora lo prueba
   causalmente (`test_art_direction.TestPruebaCausal`).
2. **El catálogo de familias visuales de este repo es cerrado (8), el de la
   línea ChatGPT se declara abierto.** Ningún lado lo había señalado como
   conflicto. Documentado como `CONFLICT_REQUIRES_FOUNDER`: ampliar el
   catálogo es una decisión de dirección artística, no un fix de código.
3. **No existía gate de proveedor prohibido en Python** pese a que "No usar
   Higgsfield" es regla escrita en el Índice maestro v18 desde antes de esta
   sesión. Cerrado con `provider_gate.py`.
4. **La distancia visual estricta (8 dimensiones, ≥5 cambiadas, 3 vecinos
   por ámbito) de la línea ChatGPT es más rigurosa que el score ponderado de
   `memory.py`.** Portada a `visual_distance.py`. Aplicada al lote de
   reconciliación, es **honesta sobre su propio límite**: con escena y
   metáfora todavía `PENDIENTE_CONTENIDO`, las 30 comparaciones del lote de
   prueba dan `EVIDENCIA_INCOMPLETA` — nunca un PASS fabricado.

### Módulos nuevos de esta fase

| Componente | Archivo | Pruebas | Estado |
|---|---|---|---|
| Argumento visual + borrador de brief | `visual/art_direction.py` | 17 | IMPLEMENTADO, PROBADO, CONECTADO |
| Distancia visual estricta (8 dim.) | `visual/visual_distance.py` | 13 | IMPLEMENTADO, PROBADO — no conectado a producción real (falta escena/metáfora) |
| Gate de proveedor prohibido | `visual/provider_gate.py` | 8 | IMPLEMENTADO, PROBADO — no conectado a ningún proveedor real todavía |
| Ratio operativo LinkedIn | `visual/lanes.py` (extensión) | 7 | IMPLEMENTADO, PROBADO, CONECTADO |
| Cadena end-to-end reconciliada | `visual/demo_reconciliation.py` | 8 | PROBADO |

**Issue #57** (`legallmente-alt/legalmente-web`, "implementar especificación
operativa del sistema vivo") queda como **punto de seguimiento** de esta
reconciliación — no como canon nuevo ni como autorización de merge.

### Lo que esta reconciliación NO hace

- No toca `legalmente-web`: cero commits, cero push, cero PR en ese repositorio.
- No genera imágenes reales ni llama a ningún proveedor.
- No amplía el catálogo de familias visuales (decisión pendiente del Founder).
- No conecta `visual_distance.py` a un flujo de producción real: falta que
  exista escena/metáfora concretas, que siguen siendo contenido, no infraestructura.
