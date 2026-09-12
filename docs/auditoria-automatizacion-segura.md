# Auditoría de automatización segura — LegalMente

Pedido del fundador (2026-09-12): auditar todo el material de LegalMente,
identificar qué bloques se pueden automatizar de forma segura, y priorizar
en este orden: **estandarización → automatización → ejecución continua con
puertas de control**.

Regla de partida, la misma de siempre (`docs/contrato-motor-masivo.md`): no
se propone un sistema paralelo. Este documento audita lo que **ya existe y
se ejecuta** (verificado hoy, no supuesto) y organiza lo que falta sobre esa
base — nunca inventando una arquitectura nueva donde ya hay una madura.

**Lo que este documento NO hace**: no implementa nada. Es la auditoría que
el fundador pidió; las tres fases son la hoja de ruta, no un changelog. La
sección 5 marca qué es un cambio de bajo riesgo que se podría hacer ya
mismo si se autoriza, separado del resto.

---

## 1. Mapa real del pipeline (verificado en código, 2026-09-12)

```
BANCO DE TEMAS (Drive, sin schema propio)
   │
   ▼
CLAIM PACKET (esquema v4) ──► validate-claim-packet.py  [AUTOMATIZADO, determinista]
   │  Etapas 1-5: extraer, clasificar, investigar fuentes, falsa
   │  universalización, seguridad editorial — HOY las hace un agente a mano,
   │  claim por claim (WebSearch + criterio).
   ▼
REVISIÓN HUMANA (revision_humana.estado)  ──────────────── PUERTA — NUNCA AUTOMATIZAR
   │
   ▼
GATE DE ARTE (gate_arte)  ──► calculado por el validador  [AUTOMATIZADO]
   │
   ▼
visual/gates.py (lee el gate, nunca lo recalcula)  [AUTOMATIZADO]
   │
   ▼
compiler.py + plan.py + families.py + memory.py + rotation.py
   → CompiledVisualRequest determinista  [AUTOMATIZADO, sin red]
   │
   ▼
provider_preflight.py → HttpImageProvider  [ARMADO, no conectado — sin
   credenciales de proveedor en este entorno]
   │
   ▼
qa.py (estructural: tamaño, MIME, dimensiones, integridad)  [AUTOMATIZADO]
   │
   ▼
review_semantics.py (clasifica qué tipo de juicio falta)  ── PUERTA (humana)
   │
   ▼
registry.py + receipts.py (asset + HumanDecisionReceipt)  [AUTOMATIZADO,
   pero registry.py vive en directorio efímero — ver §4]
   │
   ▼
content/*.json (procedencia)  ──► validate-content-provenance.py  [AUTOMATIZADO]
   │
   ▼
ProductionHandoff → PublicationDecision  ──────────────────  PUERTA — NUNCA AUTOMATIZAR
   │
   ▼
PublicationRecord → MeasurementRecord → Learning
   ──► validate-publication-chain.py  [AUTOMATIZADO, valida la forma;
        la publicación real la ejecuta un humano fuera de este repo]
```

En paralelo, sin estar wireado al ciclo anterior:

- `route_engine.py` / `route_sync.py`: motor de navegación conceptual +
  export determinista de 14 columnas — **no escribe a Drive**, solo produce
  el payload (`build_drive_payload`) y sabe verificar una relectura
  (`verify_readback`). El paso de escritura real a la hoja es manual hoy.
- `inventory.py` / `resolver.py` / `command_center.py` /
  `source_verification.py`: read-models deterministas sobre el estado real
  (qué piezas existen, qué gate tienen, qué fuentes están verificadas). Se
  invocan a mano vía `visual/cli.py`; nada los dispara solo.
- `confidentiality_rules.py`: control determinista que decide cuándo
  `confidentiality_review` **no puede** declararse `NO_APLICA` — ya está
  automatizado y corre en CI.

---

## 2. Qué NO se automatiza nunca (constitucional — no es una limitación técnica)

Estos puntos no aparecen en las fases siguientes porque ninguna cantidad de
estandarización o infraestructura los vuelve automatizables: son la barrera
de diseño explícita del proyecto (`CLAUDE.md §3-4-6`, y reforzada dos veces
esta sesión con casos reales).

1. **`revision_humana.estado: APROBADO`.** Ningún proceso, hook o CI lo
   escribe. Solo un humano identificado, con un rastro fuera del repositorio
   (ver el registro de Drive del 2026-09-12 y su "límite honesto").
2. **`PublicationDecision: AUTORIZADA`.** No existe ni existirá un campo de
   autorización de publicación automática — es una decisión de diseño del
   fundador, no una función pendiente de escribir.
3. **Ampliar qué cuenta como "fuente oficial Nivel 1"**
   (`official-source-registry.json`). Técnicamente cualquier sesión puede
   editar este archivo hoy (yo mismo añadí 8 entradas de fuentes esta
   sesión) — recomiendo tratarlo como una puerta de control explícita
   (§3.3), no solo un archivo más.
4. **Confirmar que un `localizador` realmente dice lo que un claim afirma.**
   `confidentiality_rules.py` y el validador detectan patrones e imponen
   requisitos, pero no leen jurisprudencia — cuando `EGRESS_BLOCKED` impide
   `WebFetch`, la lectura real la hace un humano o una sesión con otra red,
   nunca se sustituye por convergencia de `WebSearch` declarada como
   suficiente (esa convergencia solo alcanza `APTO_CON_MATICES`, nunca
   `APTO_PARA_NARRATIVA` — el propio validador lo fuerza).
5. **Publicación en cualquier plataforma.** Ningún workflow de este
   repositorio tiene ni tendrá credenciales de publicación.

---

## 3. Fase 1 — Estandarización (antes de automatizar nada)

Automatizar sobre una base no estandarizada solo escala el desorden más
rápido. Estos son los huecos concretos encontrados hoy:

### 3.1 CI valida una lista de piezas hardcodeada, no el estado real
`.github/workflows/legalmente-legal-verification.yml` (paso "Paquetes
reales del piloto...") tiene `REQUIRED=(pieza-01... pieza-02... pieza-03...)`
escrito a mano. Ya se desincronizó una vez (no incluía `pieza-04`, mergeada
hace días) y ahora tampoco cubre las 8 piezas `linkedin-ray-*` — aunque el
test unitario `test_las_piezas_reales_pasan_validacion_estructural` sí las
descubre por glob, el paso de CI en YAML es una segunda fuente de verdad
separada que puede volver a desincronizarse. **Arreglo de bajo riesgo**:
reemplazar la lista fija por un glob real de `pilot/claim-packets/*.json`,
igual que ya hace el test de Python.

### 3.2 No existe un schema para "candidato de tema" antes del claim packet
El claim packet (esquema v4) está muy bien estandarizado. Lo que **no**
tiene forma fija es el paso anterior: de dónde sale un tema candidato. Hoy
vive repartido en ~10 documentos de Drive con estados inconsistentes
(`SAFE_EDITORIAL_FRAME`, `REVIEW_REQUIRED`, `AUXILIARY_CONTRIBUTION_READY`,
`CORE_LINKED_AND_READY_FOR_INTEGRATION`...) escritos por agentes distintos
(Manus, Grok, Claude) sin un vocabulario cerrado compartido — el mismo
problema de fondo que ya resolvió `command_center.py` para el estado
visual (vocabulario cerrado, `FRESHNESS_LIVE/DERIVED/SNAPSHOT/SIMULATED`).
Antes de automatizar la selección de temas, hace falta un
`TopicCandidate` con estados cerrados y un solo lugar canónico — no volver
a escribir, cada vez que hace falta, un documento ad hoc como
`docs/linkedin-raymundo-inmobiliario.md` (que es exactamente ese problema,
resuelto a mano una vez más).

### 3.3 El registro oficial de fuentes crece sin puerta propia
`references/official-source-registry.json` decide qué hostname puede
alcanzar Nivel 1. Cualquier sesión puede añadir una entrada directamente
(lo hice yo mismo el 2026-09-12, 8 entradas para 2 claims). Es razonable
que una sesión *proponga* una entrada nueva tras encontrar evidencia real
— no lo es que quede incorporada sin que nadie la revise como lo que es:
una ampliación de autoridad. Estandarizar: el mismo patrón de
`revision_humana` (propuesta con evidencia → aprobación humana explícita
→ solo entonces cuenta para Nivel 1), no un archivo de edición libre.

### 3.4 El `AssetRegistry` no tiene raíz persistente real
`visual/registry.py` + `runtime_config.py` ya resolvieron el mecanismo
(`LEGALMENTE_RUNTIME_ROOT`), pero nunca se fijó a un valor real en
producción — sigue viviendo en directorios efímeros de sesión
(`docs/real-generation-readiness.md`, hueco ya documentado).
`inventory.py` deliberadamente no lo lee por esto mismo. Cualquier
automatización de producción visual real necesita esto resuelto primero,
o el inventario seguirá sin poder confiar en qué assets existen.

### 3.5 El vocabulario por materia se llena ad hoc
`VOCABULARIO_POR_MATERIA` (penal/civil/laboral/inmobiliario, esta última
añadida hoy) sigue un patrón implícito y consistente, pero nunca escrito
como checklist. Documentarlo como plantilla explícita (qué campos, qué
tipo de término, cómo decidir si hace falta `VOCABULARIO_POR_SUBMATERIA`)
antes de que la próxima materia (familia, digital y datos) se añada con
otro criterio.

---

## 4. Fase 2 — Automatización (una vez resuelto lo anterior)

Ordenado por relación beneficio/riesgo, de más a menos seguro:

1. **Sincronización Drive real** (`route_sync.build_drive_payload` +
   `verify_readback` → escritura real vía el conector de Drive). Es el
   candidato más seguro de toda la lista: no decide nada jurídico ni de
   contenido, solo serializa estado ya calculado y verifica que la
   relectura coincide. Hoy ese último tramo (escribir/leer la hoja real)
   se hace a mano.
2. **Cobertura completa de CI sobre `pilot/claim-packets/`** — aplicar el
   arreglo de bajo riesgo de §3.1. Automatiza que ninguna pieza real vuelva
   a quedar fuera del chequeo por simple olvido humano.
3. **Reporte automático de "qué requiere tu firma"** — `visual/cli.py
   inventory` / `system-queue` / `command-center` ya calculan esto de forma
   determinista; falta que algo los invoque y publique el resultado (a un
   Drive doc o similar) en vez de que un agente tenga que ejecutarlos a
   mano cada vez que el fundador pregunta "qué me falta aprobar" (como en
   esta misma conversación).
4. **Andamiaje de investigación de fuentes** — el patrón que usé para
   `pieza-04` y `linkedin-ray-16` (WebSearch → objeto `fuente` con
   `verificacion_fuente` pre-rellenado, `texto_exacto_consultado: false`
   hasta lectura directa) es repetible y mecánico en su forma, aunque el
   *criterio* de qué buscar y cómo interpretarlo siga siendo de un agente.
   Automatizar el armado del JSON reduce el trabajo repetitivo sin tocar
   la parte que sí requiere criterio.
5. **Conexión de un proveedor de imagen real** — `provider_preflight.py`
   ya arma la petición completa; falta credencial real y el paso de
   envío. Solo tiene sentido después de resolver §3.4 (raíz persistente),
   o los assets generados no sobrevivirán a la sesión.

---

## 5. Fase 3 — Ejecución continua con puertas de control

Hoy **no existe ningún workflow con `schedule:`** — todo corre por `push`,
`pull_request` o `workflow_dispatch` manual. No hay ejecución continua de
ningún tipo todavía; esto es la fase que la crea, deliberadamente acotada.

**Job propuesto — "estado diario" (solo lectura y reporte, nunca decide):**
- corre la suite completa + `check_pilot_governance.py` sobre **todo**
  `pilot/claim-packets/*.json` (glob real, no lista fija);
- corre `visual/cli.py inventory` / `system-queue` y publica el resultado
  (Drive, o un issue/PR comment) — la misma bandeja que hoy un agente arma
  a mano cuando el fundador pregunta;
- corre `route_sync` hacia Drive (una vez la Fase 2.1 esté lista), para que
  la hoja nunca quede desincronizada del repo.

**Puerta de control de este job, explícita y no negociable**: solo lee,
calcula y reporta. No escribe `revision_humana`, no calcula ni fuerza
ningún `gate_arte`, no crea ni modifica ningún registro de la cadena de
publicación. Si algún cambio futuro a este job alguna vez necesitara tocar
esos tres campos, eso ya no es este job — es una propuesta de cambio a la
constitución del sistema (`CLAUDE.md §3-4`), no una mejora incremental de
automatización.

**Job futuro — "producción visual" (cuando la Fase 2.5 esté resuelta):**
para piezas con `gate_arte: ABIERTO` ya calculado (nunca lo calcula este
job), dispara generación real → `qa.py` estructural → dejar el resultado
en `HUMAN_ART_REVIEW` (nunca autoaprobado — `review_semantics.py` ya
distingue "hay algo que juzgar" de "juzgado"). Puerta de control: el
resultado de este job nunca es "listo", siempre es "pendiente de que
alguien lo mire".

**Lo que ninguna fase futura debe intentar automatizar**: la Sección 2
completa. Ninguna puerta de control sustituye esas tres barreras — las
vuelve visibles y a tiempo, nunca las elimina.

---

## 6. Resumen ejecutable

| Fase | Qué | Riesgo si se salta |
|---|---|---|
| 1. Estandarización | §3.1-3.5: glob real en CI, schema de banco de temas, puerta para el registro de fuentes, raíz persistente de assets, checklist de vocabulario | Automatizar sobre esto construye automatización que se desincroniza sola, como ya pasó con el CI hardcodeado |
| 2. Automatización | §4: Drive real, CI completo, reporte de bandeja, andamiaje de fuentes, proveedor real | Sin la Fase 1, cada pieza de automatización hereda el mismo hueco de origen |
| 3. Ejecución continua | §5: job diario de solo-lectura, luego job de producción con QA estructural | Sin puertas de control explícitas, "ejecución continua" y "publicación automática" se vuelven indistinguibles — exactamente lo que `CLAUDE.md §6` prohíbe |

Ningún punto de este documento abre un gate, aprueba un claim, ni modifica
CI, Drive o el registro de fuentes. Es la auditoría pedida; ejecutar
cualquier fase es una decisión aparte del fundador.
