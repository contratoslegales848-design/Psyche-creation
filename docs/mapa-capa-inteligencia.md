# Mapa de la capa de inteligencia de LegalMente

Documento-índice único. **Mapa, no contrato**: no define nada nuevo — enlaza cada
eslabón a su documento canónico y declara su estado real. No implementa código, no
abre gates, no toca producción, no crea métricas. Es el lente de *cadena*;
`docs/TECHNICAL_STATE.md` sigue siendo el lente de *subsistema* (estado técnico,
pruebas). Cuando ambos difieran, gana `TECHNICAL_STATE.md`.

La cadena que mapea:

```
Preocupación / señal → Necesidad → Clasificación jurídica → TopicCandidate
  → Verificación → Claim → Opción → Radar → Prioridad → Contenido / Herramienta
```

## Leyenda de estados

- **IMPLEMENTADO** — existe en código, con pruebas que pasan.
- **CONTRATO/POLÍTICA** — existe solo como documento normativo; sin código.
- **PILOTO** — existe como casos documentados de prueba, no como sistema.
- **PARCIAL** — parte implementada, parte no.
- **NO EXISTE** — ni documento ni código.
- **BLOQUEADO POR DATOS** — definido, pero inerte porque faltan datos reales.

## Tabla resumen

| # | Eslabón | Estado | Canónico | Lee/Escribe | ¿Abre gates? | Rev. humana |
|---|---|---|---|---|---|---|
| 1 | Preocupación / señal | CONTRATO/POLÍTICA (captura NO EXISTE) | `politica-capa-necesidad.md` | — | No | — |
| 2 | Necesidad | POLÍTICA + PILOTO | `politica-capa-necesidad.md` | Lee | No | Sí (frontera) |
| 3 | Clasificación jurídica | POLÍTICA + PILOTO | `politica-capa-necesidad.md` | Lee | No | Sí |
| 4 | TopicCandidate | CONTRATO (+4 ejemplos) | `contrato-topic-candidate.md` | Lee | No | Sí |
| 5 | Verificación | **IMPLEMENTADO** | skill `legalmente-legal-verification` | Escribe (claim) | No (los calcula) | Sí |
| 6 | Claim | **IMPLEMENTADO** | `references/claim-packet-schema.md` | Es el dato | Calcula gate | Sí (firma) |
| 7 | Opción | PILOTO / no implementado | `politica-capa-necesidad.md` | Lee | No | — |
| 8 | Radar | CONTRATO + BLOQUEADO POR DATOS | `contrato-legalmente-radar.md` | Lee | No | Sí |
| 9 | Prioridad | CONTRATO (parte de Radar) | `contrato-legalmente-radar.md` | Lee | No | Sí |
| 10 | Contenido / Herramienta | PARCIAL / NO EXISTE | `contrato-motor-masivo.md`, skill visual | Escribe (assets) | Lee gate, no lo abre | Sí |

## Detalle por eslabón

### 1. Preocupación / señal
- **Función**: puerta de entrada; una preocupación observable o una señal agregada.
- **Entrada**: lo que expresa una persona, o un agregado de Radar / cola de verificación.
- **Salida**: una preocupación observable + contexto funcional (sin PII).
- **Canónico**: `docs/politica-capa-necesidad.md`, `docs/direccion-trazabilidad-emocional.md`.
- **Estado real**: la *interpretación* está en política; la *captura automática* NO EXISTE — hoy la introduce un humano/agente a mano.
- **Dep. anterior**: ninguna (es el inicio). **Dep. siguiente**: Necesidad.
- **Lee/escribe**: —. **¿Gates?**: no. **Rev. humana**: —.
- **Riesgo**: leer la emoción como dato jurídico (Principio 1).
- **Hueco**: no hay mecanismo que capture ni persista señales.
- **Evidencia**: `politica-capa-necesidad.md` §principios.
- **Operativo si**: existiera un canal de captura que registrara señales anonimizadas.

### 2. Necesidad
- **Función**: traducir la preocupación en una necesidad concreta.
- **Entrada**: preocupación observable. **Salida**: necesidad concreta (educativa, general).
- **Canónico**: `docs/politica-capa-necesidad.md`.
- **Estado real**: POLÍTICA + PILOTO (6 casos base). Sin código.
- **Dep. anterior**: Preocupación. **Dep. siguiente**: Clasificación.
- **Lee/escribe**: lee. **¿Gates?**: no. **Rev. humana**: sí en frontera.
- **Riesgo**: forzar una necesidad jurídica donde no la hay.
- **Hueco**: no automatizada; sin persistencia.
- **Evidencia**: `piloto-capa-necesidad.json` (casos PC-01..PC-06).
- **Operativo si**: se implementara la capa y su almacén.

### 3. Clasificación jurídica
- **Función**: decidir si hay materia jurídica: `ES_` / `NO_` / `FRONTERA_INDETERMINADO`.
- **Entrada**: necesidad. **Salida**: clasificación + (si frontera) hecho mínimo faltante.
- **Canónico**: `docs/politica-capa-necesidad.md` (tres estados).
- **Estado real**: POLÍTICA + PILOTO (9 casos con calibración de frontera).
- **Dep. anterior**: Necesidad. **Dep. siguiente**: TopicCandidate / Verificación.
- **Lee/escribe**: lee. **¿Gates?**: no. **Rev. humana**: sí.
- **Riesgo**: forzar la clasificación en vez de reconocer frontera.
- **Hueco**: la frontera es criterio humano; sin código.
- **Evidencia**: `piloto-capa-necesidad.json` → `calibracion_frontera_v1`.
- **Operativo si**: se implementara con revisión humana de la frontera.

### 4. TopicCandidate
- **Función**: capturar una oportunidad temática sin volverla afirmación jurídica.
- **Entrada**: señal/necesidad/hueco. **Salida**: candidato con su pregunta jurídica candidata.
- **Canónico**: `docs/contrato-topic-candidate.md` (+ `topic-candidates-calibracion.json`).
- **Estado real**: CONTRATO + 4 ejemplos. Objeto NO implementado.
- **Dep. anterior**: Clasificación / Radar. **Dep. siguiente**: Verificación.
- **Lee/escribe**: lee (estado del claim, si existe). **¿Gates?**: no. **Rev. humana**: sí (promover/descartar).
- **Riesgo**: inflar recurrencia sin datos; falso anti-duplicado (semántico no existe).
- **Hueco**: sin almacén consultable ni control semántico/ángulo/narrativa.
- **Evidencia**: `contrato-topic-candidate.md`, 4 candidatos de calibración.
- **Operativo si**: existiera el almacén (`contrato-motor-masivo.md §4.1`) y el control de repetición.

### 5. Verificación — **el único eslabón robusto de punta a punta**
- **Función**: verificar fuentes y calcular estado jurídico y gate (fail-closed).
- **Entrada**: una pregunta jurídica. **Salida**: un claim packet con estado y gate calculados.
- **Canónico**: skill `legalmente-legal-verification`; `references/claim-packet-schema.md`; `scripts/validate-claim-packet.py`.
- **Estado real**: **IMPLEMENTADO**. Determinista, con CI.
- **Dep. anterior**: TopicCandidate / Clasificación. **Dep. siguiente**: Claim.
- **Lee/escribe**: escribe el claim (nunca inventa aprobación). **¿Gates?**: los **calcula**, no los fuerza. **Rev. humana**: sí (la aprobación es humana, externa).
- **Riesgo**: `EGRESS_BLOCKED` topa el estado a `APTO_CON_MATICES` cuando no se lee el texto íntegro.
- **Hueco**: red bloqueada para lectura directa de fuentes.
- **Evidencia**: 245 pruebas en verde; validador de 1.217 líneas; registro oficial único.
- **Operativo si**: ya lo es. Mejora pendiente: acceso de red a fuentes oficiales.

### 6. Claim
- **Función**: el dato jurídico verificado, ligado por hash a la aprobación humana.
- **Entrada**: verificación. **Salida**: el propio claim (estado, fuentes, gate, límites).
- **Canónico**: `references/claim-packet-schema.md` (esquema v4).
- **Estado real**: **IMPLEMENTADO**. Existen claims reales: pieza-01 (gate ABIERTO, aprobado), pieza-04 y linkedin-ray-16 (APTO_CON_MATICES, este con aprobación humana), pieza-02/03 (REQUIERE_INVESTIGACION).
- **Dep. anterior**: Verificación. **Dep. siguiente**: Opción / Contenido.
- **Lee/escribe**: es el dato. **¿Gates?**: `gate_arte` se calcula sobre él. **Rev. humana**: sí (firma por hash).
- **Riesgo**: confundir `gate_arte: ABIERTO` con autorización de publicación (no lo es).
- **Hueco**: la mayoría de materias no tiene claim (consumo, sucesiones, médica, arrendamiento, familia, etc.).
- **Evidencia**: `pilot/claim-packets/*.json` (12 piezas reales).
- **Operativo si**: ya lo es; falta cobertura de materias.

### 7. Opción
- **Función**: presentar a la persona una opción = vista derivada de un claim (texto + fuente + certidumbre + límite).
- **Entrada**: un claim verificado. **Salida**: una opción trazable, o "no hay opción".
- **Canónico**: `docs/politica-capa-necesidad.md` (cómo se monta); patrón `visual/source_verification.py`.
- **Estado real**: SOLO DOCUMENTADO / PILOTO. **No implementada** como vista viva (el patrón read-model existe, la "Opción" no).
- **Dep. anterior**: Claim. **Dep. siguiente**: Radar (consume el resultado anonimizado).
- **Lee/escribe**: lee. **¿Gates?**: no. **Rev. humana**: —.
- **Riesgo**: mostrar más certeza que la del claim.
- **Hueco**: no existe el componente que renderiza la opción en vivo.
- **Evidencia**: opciones descritas en `piloto-capa-necesidad.json` (PC-01..03).
- **Operativo si**: se construyera el read-model de opción sobre el claim packet.

### 8. Radar
- **Función**: convertir señales agregadas en prioridades (verificar, tema, hueco).
- **Entrada**: señales anonimizadas + cola de verificación. **Salida**: propuestas (tema, verificación, hueco, tendencia).
- **Canónico**: `docs/contrato-legalmente-radar.md`.
- **Estado real**: CONTRATO + **BLOQUEADO POR DATOS** (hoy produciría cero: no hay señales ni métricas reales).
- **Dep. anterior**: Opción / capa de necesidad (señales). **Dep. siguiente**: Prioridad.
- **Lee/escribe**: lee agregados. **¿Gates?**: no (propone verificación sin abrir gate). **Rev. humana**: sí (toda salida a audiencia).
- **Riesgo**: presentar prospectiva como hecho; PII por agregados finos.
- **Hueco**: **no hay señales reales** — el hueco raíz de todo el back de la cadena.
- **Evidencia**: `contrato-legalmente-radar.md` §0 (estado de datos hoy).
- **Operativo si**: existieran señales acumuladas (requiere eslabones 1-4 persistidos).

### 9. Prioridad
- **Función**: ordenar qué merece recursos (verificación, contenido, herramienta).
- **Entrada**: candidatos + señales de Radar. **Salida**: un orden propuesto (nunca ejecutado solo).
- **Canónico**: `docs/contrato-legalmente-radar.md` §2.12-14; `docs/direccion-basico-antes-que-complejo.md §6` (filtro humano).
- **Estado real**: CONTRATO. El filtro humano existe como regla; la priorización automática no.
- **Dep. anterior**: Radar / TopicCandidate. **Dep. siguiente**: Contenido / Verificación.
- **Lee/escribe**: lee. **¿Gates?**: no. **Rev. humana**: sí (la decisión de gastar recursos).
- **Riesgo**: priorizar por entusiasmo en vez de por evidencia/dependencia.
- **Hueco**: sin datos, la priorización es cualitativa y manual.
- **Evidencia**: principio de valor en `contrato-topic-candidate.md §6`.
- **Operativo si**: hubiera señales + criterio de valor con respaldo.

### 10. Contenido / Herramienta
- **Función**: producir la pieza visual (contenido) o una herramienta interactiva.
- **Entrada**: un claim con `gate_arte: ABIERTO`. **Salida**: asset + receipt (contenido); herramienta (no existe).
- **Canónico**: skill `legalmente-visual-system`; `visual/*`; `docs/contrato-motor-masivo.md`; `docs/real-generation-readiness.md`.
- **Estado real**: **PARCIAL** (contenido) / **NO EXISTE** (herramienta). El pipeline visual está implementado (compilador, familias, memoria, QA, gates, receipts) pero: solo pieza-01 tiene el gate abierto, no hay proveedor de imagen real conectado, y el almacén de assets no es persistente.
- **Dep. anterior**: Claim (gate abierto). **Dep. siguiente**: publicación (humana, separada, fuera de este repo).
- **Lee/escribe**: lee el gate (no lo abre); escribe assets/receipts. **¿Gates?**: lee, nunca abre. **Rev. humana**: sí (arte y publicación).
- **Riesgo**: que el arte se lea como validación jurídica (no lo es).
- **Hueco**: proveedor real ausente; raíz de assets efímera; herramientas inexistentes.
- **Evidencia**: 355 pruebas de `visual/`; `provider_preflight.py` armado sin credenciales; `docs/real-generation-readiness.md`.
- **Operativo si**: raíz persistente + proveedor real + más claims con gate abierto.

## FLUJO REAL HOY

Lo que LegalMente puede hacer de punta a punta **hoy**, sin adornos: **solo el tramo
central**, y a mano.

Un humano/agente toma un tema, **crea un claim packet a mano** → la **verificación
funciona de verdad** (real, probada) → un humano **firma la aprobación** → el
validador **calcula `gate_arte`** → si abre (hoy solo pieza-01), el **pipeline visual
produce** un asset con un **proveedor falso** y emite un receipt. Ahí termina: la
publicación no existe por diseño.

**Dónde se rompe el flujo, en orden:**
- **Antes del claim** (eslabones 1-4): la preocupación, la necesidad, la
  clasificación y el TopicCandidate son política/piloto/contrato. **No fluyen solos**;
  no hay captura ni almacén. El único "flujo" es que un humano los ejecuta mentalmente
  antes de escribir un claim.
- **Opción** (7): descrita, no construida — no hay componente que la renderice.
- **Radar / Prioridad** (8-9): **inertes por falta de señales reales**.
- **Contenido** (10): el motor existe pero corre con proveedor falso y solo para una
  pieza; **Herramienta** no existe.

En una frase: **hoy la cadena solo respira del Claim al asset gated, y respira a
mano.** Todo lo anterior y casi todo lo posterior es documentación.

## FLUJO OBJETIVO

La arquitectura deseada completa, cada componente etiquetado con su estado actual:

```
Preocupación/señal   [CAPTURA: NO EXISTE]
   → Necesidad        [POLÍTICA+PILOTO]
   → Clasificación    [POLÍTICA+PILOTO]
   → TopicCandidate   [CONTRATO]
   → Verificación     [IMPLEMENTADO] ─────────────┐  el corazón sano
   → Claim            [IMPLEMENTADO] ─────────────┘
   → Opción           [PILOTO / no implementado]
   → Radar            [CONTRATO + BLOQUEADO POR DATOS]
   → Prioridad        [CONTRATO]
   → Contenido        [PARCIAL]   /   Herramienta  [NO EXISTE]
        └─ (publicación: INEXISTENTE por diseño; decisión humana externa)
```

El objetivo NO es construir todo: es que cada eslabón alcance su estado siguiente sin
saltarse las puertas humanas ni la verificación.

## CUELLOS DE BOTELLA (ordenados por dependencia lógica, no por entusiasmo)

1. **No hay captura ni almacén persistente de los objetos del frente de cadena**
   (señales, clasificaciones, TopicCandidates). Es el cuello **más temprano**: sin él,
   nada se acumula → Radar no tiene señales, no hay inventario consultable, no hay
   índice anti-repetición. Bloquea 1, 4, 8 y 9 a la vez. El `contrato-motor-masivo.md
   §4.1` ya lo nombró ("inventario consultable") pero nunca se especificó su forma.
2. **No hay control de repetición semántico/ángulo/narrativo** (solo literal). Bloquea
   aceptar TopicCandidates con confianza a volumen. Depende de (1) para tener qué comparar.
3. **No hay ingesta de métricas** (0/52 en el historial). Bloquea tendencias de Radar,
   respaldo cuantitativo del valor y la medición emoción↔estilo. **Depende de (1)**:
   sin señales acumuladas ni publicación medida, no hay nada que medir. Por eso va
   *después* del almacén, no antes — discutir métricas de Radar antes de tener señales
   sería invertir el orden.
4. **Producción real incompleta**: proveedor de imagen ausente + raíz de assets
   efímera + solo pieza-01 con gate abierto. Bloquea contenido a volumen. Downstream.
5. **Herramientas inexistentes**. El destino "herramienta" del TopicCandidate no tiene
   ningún componente. Downstream/opcional.

El patrón es claro: **casi todos los cuellos aguas abajo cuelgan del cuello (1)**. La
verificación (5-6) es el único tramo sano y no es el cuello.

## PRÓXIMO PASO DE MAYOR VALOR (uno solo — NO ejecutado)

**Especificar, en un documento, el vocabulario de campos común y el contrato del
almacén de frente de cadena** — la forma del "inventario consultable" que
`contrato-motor-masivo.md §4.1` nombró pero nunca definió, y el esquema único que
comparten la capa de necesidad, el TopicCandidate y las señales de Radar.

Por qué este y no otro:
- **Cierra el cuello más temprano (1)**: sin una forma acordada de almacenar
  señales/candidatos, cualquier implementación futura forkaría tres esquemas.
- **Reversible y barato**: es un documento, se borra sin consecuencia.
- **No productivo**: no captura datos, no publica, no abre gates, no crea métricas.
- **Desbloquea en cascada**: una vez definido el almacén, TopicCandidate, Radar y el
  índice anti-repetición tienen dónde apoyarse.

**Hueco real detectado que habría que reportar antes de crearlo**: hoy los tres
objetos del frente (clasificación de necesidad, TopicCandidate, señal de Radar)
definen campos solapados (`preocupacion_observable`, `contexto_funcional`, `ambito`,
`materia`) **sin un vocabulario único**. Antes de escribir ese contrato del almacén,
convendría una **reconciliación de campos** de una sola página que evite que el
almacén nazca con tres dialectos. Ese sería, en rigor, el paso mínimo previo — y NO lo
ejecuto sin tu autorización, conforme pediste.
