# Estado técnico real de LegalMente

**Fecha original:** 2026-08-27 · **Base original:** `origin/main` en `82f226e` + ramas `chore/phase1-technical-readiness` y `chore/phase1-p0-confidencialidad-procedencia`
**Reconciliado:** 17-sep-2026, rama `claude/legalmente-architecture-reconciliation-xojn4i` (Mandato Maestro). Cifras marcadas **RE-VERIFICADO 17-sep** se corrieron de verdad hoy; el resto conserva su fecha y alcance originales — no se re-auditó línea por línea el subsistema jurídico completo en esta pasada, sólo se corrigió lo que el Mandato Maestro pidió explícitamente cerrar.
**Integrado 18-sep-2026:** el PR #16 (`feat/source-freshness-e-inventario`, construido 31-ago-2026, nunca fusionado) traía vigencia de fuentes offline (`check-source-freshness.py`) e inventario materializado (`inventory.py`), 337 pruebas propias — exactamente lo que §7 P2.5/P2.6 y el red-team B1 pedían como prioridad de cierre. Se auditó, se confirmó que sigue vigente y compatible con todo lo construido después, y se fusionó a esta rama (ver "seguimiento del proyecto — 18-sep-2026" al final de este documento para el detalle completo).
**Semáforo global: AMARILLO** (los dos P0 originales quedaron cerrados; el amarillo lo sostienen ahora riesgos declarados, no huecos sin control; ver también §7 para los pendientes que siguen abiertos hoy).

> **ALCANCE:** este documento describe el subsistema de verificación
> jurídica/publicación (fila "Verificación jurídica", "Gobernanza del gate de
> arte", "Confidencialidad", "Anti-duplicados", "Separación producción/
> publicación") — sigue siendo la fuente correcta para ESE alcance.
> **NO describe** el motor editorial/visual construido desde el 16-sep-2026
> (catálogo maestro de 767 módulos, motor de conocimiento con 58 familias
> pedagógicas + capa pedagógica de balance, memoria fuerte real conectada a
> selección temática Y dirección visual, señal de mercado, contrato
> TEXT_TO_IMAGE/IMAGE_EDIT, compilador causal de dirección artística) — para
> eso, el punto de entrada real y vigente es `visual/README.md` (sección
> "ACTUALIZACIÓN 17-sep-2026") y `docs/mandato-maestro-cierre-2026-09-17.md`.
> La fila "Motor de generación visual" de la tabla de abajo quedó superada
> por esas dos fuentes; no la actualices aquí.

Este documento describe lo que **existe y se ejecuta**, no lo que está planeado.
Regla de lectura (`CLAUDE.md §2`): una mención en un documento no es una capacidad
implementada. Todo lo que aparece aquí como verde está respaldado por un archivo
real y una prueba que pasa.

---

## 1. Semáforo por subsistema

| Subsistema | Estado | Por qué |
|---|---|---|
| Verificación jurídica (claim packets) | 🟢 VERDE | Validador de 1.217 líneas, 147 pruebas, 10 fixtures positivas y 46 negativas, CI que las ejecuta. |
| Gobernanza del gate de arte | 🟢 VERDE | Deadlock resuelto (PR #12); la gobernanza comprueba coherencia contra el validador canónico, no congela gates. |
| Registro de fuentes oficiales | 🟢 VERDE | 22 entradas, coincidencia por frontera real de subdominio, cobertura probada. |
| Separación producción / publicación | 🟢 VERDE (nuevo) | `validate-publication-chain.py` + 41 pruebas + 16 fixtures. Antes no existía. |
| Enlace verificación → renderizado | 🟢 VERDE (nuevo) | Cada artefacto declara procedencia; sin ella el bundle de Remotion falla. Verificado de punta a punta. |
| Confidencialidad | 🟡 AMARILLO (era rojo) | Control determinista fail-closed implementado; queda el contenido identificable sin marcadores léxicos (red team B5). |
| Pipeline de video (Remotion) | 🟢 VERDE (nuevo) | Renderiza, y ya no puede renderizar contenido publicable sin origen verificable. |
| Anti-duplicados | 🟡 AMARILLO (v2, integrado 18-sep) | Cinco colisiones deterministas (`content_id`, id de composición, huella normalizada de frase, casilla materia/submateria/concepto, `FINGERPRINT_IDENTICO`); la paráfrasis sigue sin detectarse. |
| Vigencia de fuentes | 🟡 AMARILLO (nuevo, integrado 18-sep — era B1, máxima prioridad del red-team) | `check-source-freshness.py`: libro mayor + control offline fail-closed, deriva el veredicto sin tocar el claim packet. Abierto: nadie avisa desde fuera de que una norma cambió (riesgo residual C6, ver `docs/red-team-cadena-editorial.md`). |
| Inventario materializado | 🟢 VERDE (nuevo, integrado 18-sep) | `scripts/inventory.py`: índice determinista y regenerable desde artefactos reales (nunca autoridad); `check` detecta que está obsoleto y falla. |
| Motor de generación visual | 🟢 VERDE (SUPERADO por `visual/README.md`, RE-VERIFICADO 17-sep) | Cifra de 124 pruebas está muy desactualizada: `visual/` tiene hoy **1234 tests** (suite completa fresca, `python3 -m unittest discover`, corrida real 18-sep), no 124 — el subsistema creció enormemente desde el 27-ago (catálogo maestro 767 módulos, motor pedagógico, memoria fuerte, compilador causal de dirección artística, tabla concepto→dirección con evidencia real). Detalle real y vigente: `visual/README.md` + `docs/mandato-maestro-cierre-2026-09-17.md`, no esta fila. |
| Composición tipográfica / marca | 🟢 VERDE (nuevo) | `visual/compositor.py`: rasterizado real con Pillow. Métrica tipográfica real, área segura, `exact_copy` inmutable (desborda antes que mutar), marca solo sobre superficie reservada declarada y plana, alineación de texto real (centro/izquierda/derecha, corregido 18-sep). |
| Adapter de proveedor real | 🟡 AMARILLO (nuevo) | `providers/http_provider.py`: adapter HTTP real con transporte inyectable, 23 pruebas, cero llamadas externas. Sin credenciales configuradas en el workspace: no se ha ejecutado contra ningún proveedor. |
| Métricas | 🟡 AMARILLO (nuevo, integrado 18-sep) | `DUE_FOR_MEASUREMENT` consultable vía inventario (publicada + sin medir + 7 días cumplidos); las cifras siguen tecleándose a mano, sin lectura automatizada de ninguna plataforma. |
| Contrato cross-repo | 🟢 VERDE (Psyche, RE-VERIFICADO 17-sep) | `contract/`, Canonical Envelope v1, 8 fixtures, **17 tests** (creció de 12 — no re-medido cuándo; confirmado hoy con ejecución real: `python3 -m unittest discover` en `contract/`, 17/17 OK). Lado web (18 tests, `handoff/legalmente-web/`, escritura remota bloqueada): NO re-verificado esta sesión, se conserva la cifra original del 27-ago sin reconfirmar. |
| Motor de producción masiva | ⚫ NO CONSTRUIDO | Contrato técnico definido (`docs/contrato-motor-masivo.md`) más la infraestructura mínima (vigencia + inventario, integrada 18-sep); el motor en sí, deliberadamente, no. |
| Documentación vs. realidad | 🟢 VERDE (RESUELTO 17-sep, era 🟡) | Las dos derivas de §5 quedaron cerradas — ver §5 actualizado. |
| `legalmente-web` (visibilidad) | 🟢 VERDE (RESUELTO, ya estaba resuelto desde 31-ago) | El repositorio es público; `CLAUDE.md §8` YA lo declara público (commit `9e4bded`, 31-ago-2026) — la fila anterior de esta misma tabla describía una contradicción que ya no existe. Re-verificado hoy con `git ls-remote` anónimo real (sin credenciales), HEAD actual `3d9d298`. Ver §5. |
| Publicación automatizada | ⚫ INEXISTENTE (por diseño) | Ninguna automatización publica. Es una regla, no una carencia. Sin cambios. |

---

## 2. Lo que existe y se ejecuta

### 2.1 Skill de verificación jurídica
`.claude/skills/legalmente-legal-verification/`

- `scripts/validate-claim-packet.py` — validador canónico, esquema v4.0. Calcula el
  estado de cada claim, el gate de arte y el agregado de la pieza. **Fail-closed**:
  ante duda, cierra. Sin red.
- `scripts/check_pilot_governance.py` — control de CI: verifica que cada gate
  declarado coincida exactamente con el que calcula el validador.
- `scripts/validate-publication-chain.py` — la cadena post-aprobación.
- `scripts/confidentiality_rules.py` — **nuevo**: control determinista de
  confidencialidad. Doce indicadores sobre los campos publicables del claim; si
  alguno dispara, la revisión humana deja de ser opcional.
- `scripts/validate-content-provenance.py` (en la raíz) — procedencia de los
  artefactos de `content/` y controles anti-duplicados.
- `scripts/check-source-freshness.py` — **nuevo**: vigencia de fuentes. Offline y
  sin reloj de red; deriva el veredicto sin tocar el claim packet.
- `scripts/inventory.py` (en la raíz) — **nuevo**: inventario materializado,
  determinista y regenerable, con consultas y anti-duplicados v2.
- `references/official-source-registry.json` — 22 organismos oficiales.
- `fixtures/` — 10 positivas, 46 negativas.
- `publication/fixtures/` — 2 cadenas válidas, 14 inválidas, 1 claim packet sintético.

**Pruebas: 358, todas en verde** (Psyche — skill jurídica + scripts de raíz + contrato cross-repo; corrida real, no estimada, 18-sep-2026 tras integrar vigencia de fuentes + inventario). Más 23 del consumidor de web, locales.
| Suite | Pruebas |
|---|---|
| `test_validate_claim_packet` | 147 |
| `test_check_pilot_governance` | 37 |
| `test_validate_publication_chain` | 41 |
| `test_confidentiality_rules` | 20 |
| `test_check_source_freshness` | 31 (nuevo, integrado 18-sep) |
| `test_validate_content_provenance` | 30 |
| `test_inventory` | 31 (nuevo, integrado 18-sep) |
| `test_check_unittest_main_guard_position` | 4 |
| `contract/test_canonical_envelope` | 17 |
| **Total de esta tabla** | **358** |
| `visual/` (suite completa) | 1234 (RE-VERIFICADO 18-sep; contado aparte, ver `visual/README.md` — no se suma al 358 de arriba, que es sólo el alcance jurídico/publicación de esta sección) |

### 2.2 Los cuatro estados no equivalentes

Esta es la distinción central del sistema y está ahora ejecutada de punta a punta:

```
estado: APTO_PARA_NARRATIVA   → la afirmación resiste verificación   (validador)
revision_humana: APROBADO     → un humano la firmó                   (persona identificada)
gate_arte: ABIERTO            → se puede PRODUCIR                    (consecuencia)
PublicationDecision AUTORIZADA→ se puede PUBLICAR                    (decisión humana separada)
```

Hasta hoy solo existían los tres primeros. El cuarto vive en
`.claude/skills/legalmente-legal-verification/publication/` y, por diseño, **fuera
del claim packet**: si viviera dentro, cada decisión de publicación cambiaría el
hash del claim e invalidaría la aprobación jurídica ya firmada.

### 2.3 Pipeline de video
Remotion 4 + React/TypeScript. `content/*.json` → `src/content.ts` →
`src/compositions/LegalMenteQuote.tsx`. CI renderiza en `push` a `main` que toque
`content/**`, y sube los MP4 como artefactos.

`src/content.ts` ya no valida solo la forma de la pieza: exige `procedencia`, sin
modo por defecto. Los tres modos son `GOBERNADO` (hay un `ProductionHandoff`
detrás), `NO_APLICA` (por decisión de gobernanza no hay afirmación jurídica que
verificar — cita histórica, formato de marca) y `EJEMPLO_TECNICO` (material de
prueba, `publicable: false` obligatorio). La forma se comprueba en tiempo de bundle
y el fondo en CI, donde sí se pueden leer los claim packets.

### 2.4 CI
| Workflow | Dispara en | Qué hace |
|---|---|---|
| `legalmente-legal-verification.yml` | PR y push a `main` que toquen la skill | compileall, higiene de bytecode, 3 suites unitarias, fixtures positivas/negativas, fixtures de la cadena, paquetes reales del piloto |
| `render-video.yml` | push a `main` que toque `content/**`, o manual | typecheck y render Remotion |

**Deriva conocida:** ningún workflow se dispara al empujar a una rama de trabajo.
La CI solo corre en el PR. No es un fallo, pero conviene saberlo: una rama puede
acumular commits sin que nada la valide hasta que se abre el PR.

### 2.5 Piloto
| Pieza | Claims | Estado agregado | Gate |
|---|---|---|---|
| `pieza-01-reales.json` | 3 (1, 2, 4) | APTO_PARA_NARRATIVA | CERRADO |
| `pieza-02-laboral.json` | 7 | REQUIERE_INVESTIGACION | CERRADO |
| `pieza-03-honor.json` | 7 | REQUIERE_INVESTIGACION | CERRADO |

La Pieza 1 tiene aprobación humana expresa registrada en la rama
`claude/legalmente-pieza-01-aprobacion-humana-final-v1` (commit `e7bb82f`), **sin
fusionar**. Esa fusión es una decisión humana pendiente, no un paso técnico.

---

## 3. Lo que NO existe (contra lo que pueda decir cualquier documento)

- `legalmente-story-engine` — no implementada.
- `legalmente-confidentiality` — la **skill** no existe. Lo que sí existe desde el
  2026-08-27 es el control ejecutable (`scripts/confidentiality_rules.py`), que era
  lo que faltaba de verdad. Una skill aportaría guía de redacción, no bloqueo.
- Los 6 agentes (`legal-researcher`, `legal-auditor`, `narrative-editor`,
  `visual-director`, `privacy-reviewer`, `growth-analyst`) — ninguno existe.
- Los 4 hooks (PRE-NARRATIVA, PRE-ARTE, PRE-PUBLICACIÓN, POST-PUBLICACIÓN) — ninguno existe.
- Integración con Grok, Manus o Gemini — solo contratos en borrador
  (`docs/handoff-contracts/`, marcados DRAFT / EXPERIMENTAL).
- Lectura automatizada de métricas de plataforma.
- Cualquier forma de publicación automática. **Por diseño, y así debe seguir.**

---

## 4. La cadena, ya completa

```
[verificación jurídica]                                    [producción]
claim packet → aprobación humana → gate arte → ProductionHandoff
                                                      │
                                                      ▼
                                        content/*.json (procedencia) → Remotion → MP4
                                                      │
                                                      ▼
                                        PublicationDecision AUTORIZADA (humana)
                                                      │
                                                      ▼
                                     PublicationRecord → Measurement → Learning
```

El corte que existía entre la mitad jurídica y la de producción está cerrado. Queda
verificado, no solo afirmado: quitando `procedencia` de `content/ejemplo.json`, el
bundle de Remotion falla con exit 1.

`content/ejemplo.json` es hoy el único artefacto, en modo `EJEMPLO_TECNICO` y
`publicable: false`: es material de prueba del pipeline, no una pieza publicable.

## 5. Derivas entre documentación y realidad

1. **`CLAUDE.md §8` — RESUELTO, no es una deriva vigente.** Este punto describía,
   el 27-ago-2026, que `CLAUDE.md §8` declaraba `legalmente-web` privado
   siendo público. Esa corrección **ya se aplicó** el 2026-08-31, commit
   `9e4bded` ("docs: corregir el hecho de visibilidad de legalmente-web en
   CLAUDE.md §8") — el mismo día de la reverificación por clonado anónimo
   (HEAD `23a9ce0` entonces). **Esta sección de este mismo documento quedó
   desactualizada** después de esa corrección (no se actualizó cuando el
   fix se aplicó) y por eso siguió listando el punto como pendiente en la
   tabla de §1 y en §7 P1.4 — error de mantenimiento documental, corregido
   ahora (17-sep-2026). Re-verificado hoy de forma independiente:
   `git ls-remote https://github.com/legallmente-alt/legalmente-web.git`
   (sin credenciales) responde con éxito, HEAD actual `3d9d298`. `CLAUDE.md`
   §8 dice correctamente "**público**" — leído y confirmado en esta misma
   sesión. **Ningún cambio a `CLAUDE.md` fue necesario**: ya estaba
   correcto, sólo este documento (`TECHNICAL_STATE.md`) llevaba 17 días
   diciendo lo contrario de sí mismo.
2. **Nombre de paso de CI obsoleto** — decía "mantener el gate cerrado" cuando el
   control ya comprueba coherencia. Corregido el 27-ago (histórico, no re-verificado hoy).
3. **Pruebas congeladas obsoletas** — dos pruebas afirmaban que los paquetes del
   piloto siguen PENDIENTE con gates CERRADO. Hacían fallar la suite ante cualquier
   aprobación humana legítima. Sustituidas por pruebas de coherencia el 27-ago
   (histórico, no re-verificado hoy).
4. **(nuevo, encontrado 17-sep-2026) Este mismo documento repitió el error
   del punto 1** en un reporte ejecutivo de esta sesión, antes de esta
   reconciliación: se afirmó "CLAUDE.md §8 dice que legalmente-web es
   privado" citando este documento sin re-leer `CLAUDE.md` directamente.
   Corregido en el mismo ciclo que produjo este punto — ver
   `docs/mandato-maestro-cierre-2026-09-17.md` para la nota de corrección
   completa. Lección operativa (ya era la regla de `CLAUDE.md §2`, reforzada
   aquí con un ejemplo real): un documento secundario desactualizado puede
   propagar un error aunque la fuente primaria (`CLAUDE.md`) ya esté
   correcta — re-verificar la fuente primaria, no el documento que la cita.

---

## 6. Seguridad (repositorio público)

`contratoslegales848-design/Psyche-creation` es **público**. Consecuencias asumidas:

- Todo el contenido del repositorio es visible: skills, validador, fixtures,
  documentos operativos y `CLAUDE.md`.
- No se detectó ningún secreto, credencial ni token en el árbol de trabajo ni en
  los archivos revisados.
- `.gitignore` no cubría bytecode de Python ni archivos `.env`. Corregido en esta
  rama (`__pycache__/`, `*.py[cod]`, `.env`, `.env.*`, `*.log`).
- Los nombres reales están prohibidos en fixtures, pruebas y ejemplos, y hay una
  comprobación ejecutable que lo verifica en dos ámbitos (fixtures y scripts).

Riesgo residual declarado: `CLAUDE.md` describe públicamente la arquitectura de
control y sus huecos conocidos. Es información útil para quien quisiera explotarlos.
La alternativa —ocultar los huecos— sería peor para el rigor operativo. Es una
decisión del fundador, no técnica.

---

## 7. Prioridades

**P0 — cerrados el 2026-08-27**
1. ~~Control de confidencialidad sobre contenido publicable.~~ Implementado.
2. ~~Ligar `content/*.json` a un `ProductionHandoff` válido.~~ Implementado.

**P1 — antes de escalar el volumen**
3. ~~Decidir sobre la Pieza 1: fusionar o no `e7bb82f`.~~ **FUSIONADA** el
   2026-08-31 (commit `0f8c697`), autorizada expresamente por el fundador.
   ~~Emitir `ProductionHandoff` para PIEZA-01.~~ **EMITIDO** el mismo día
   (`HO-PIEZA-01-REALES-001`), autorizado expresamente. `LM-PIEZA-01-REALES`
   ahora resuelve `AUTORIZADA` y el pipeline formal produjo un
   `GenerationReceipt` real (incluida una regeneración con lineage). **Ningún
   `PublicationDecision` existe**: la publicación sigue sin autorizarse. Ver
   `docs/production-handoff-decision-pieza-01.md` y
   `docs/real-generation-readiness.md`.
4. ~~Corregir la deriva de `legalmente-web` en `CLAUDE.md §8`.~~ **YA ESTABA
   RESUELTO** desde el 2026-08-31 (commit `9e4bded`) — este propio documento
   no reflejaba esa corrección hasta la reconciliación del 17-sep-2026. Ver §5.1.
5. ~~Resolver el conflicto de marca.~~ **RESUELTO** el 2026-08-31: `NO`. Ver
   `docs/adr/0002-marca-composicion-determinista.md`. Aplicado en política 1.1.
6. **Cerrar los PR #26 y #28 de `legalmente-web` como SUPERSEDED.** Verificado que
   el HEAD de #25 (`48d846f`) ya contiene íntegramente el hardening de #28.
   Requiere permisos de escritura que las sesiones de este repo no tienen.

**P2 — cuando el piloto esté medido**
5. ~~Inventario materializado.~~ Implementado.
6. Vigilancia activa de cambios normativos: un proceso de research **con red y
   fuera del validador** que marque fuentes para revisión. Es ahora el riesgo
   abierto de mayor consecuencia (red team C6): el libro mayor solo sabe lo que un
   humano escribió en él.
7. Planificación de cobertura sobre el inventario (qué casillas de
   `materia/submateria/concepto` faltan).
8. Ingesta automatizada de métricas: hoy las cifras se teclean.
9. Detección de duplicados por paráfrasis, cuando el volumen lo justifique.

**P3 — no ahora**
7. Integraciones externas (Grok/Manus/Gemini): los contratos están en borrador
   precisamente para no implementarlos todavía.
8. Agentes y hooks descritos en Drive.

---

## 8. Documentos relacionados

- `.claude/skills/legalmente-legal-verification/publication/README.md` — la cadena post-aprobación.
- `docs/adr/0001-arquitectura-de-hashes.md` — por qué hay un solo hash.
- `docs/red-team-cadena-editorial.md` — vectores de ataque y qué los bloquea.
- `docs/handoff-contracts/` — contratos externos en borrador.
- `docs/contrato-motor-masivo.md` — dónde vive cada campo del futuro motor y por qué
  no se creó ningún modelo paralelo.
- `visual/README.md` — punto de entrada real y vigente del motor editorial/visual
  (catálogo maestro, motor pedagógico, memoria fuerte, compilador causal de
  dirección artística, contrato TEXT_TO_IMAGE/IMAGE_EDIT). Este documento
  (`TECHNICAL_STATE.md`) no cubre ese alcance.
- `docs/mandato-maestro-cierre-2026-09-17.md` — mapa de estado y tabla
  Drive↔código de la sesión "Mandato Maestro" (17-sep-2026): motor
  pedagógico, memoria fuerte en selección temática, compilador causal de
  dirección artística, auditoría de deuda técnica (resultado: limpia),
  reconciliación de este mismo documento.
- `.claude/skills/legalmente-legal-verification/references/README-vigencia.md` — el
  libro mayor de vigencia y por qué el veredicto se deriva en vez de almacenarse
  (integrado 18-sep-2026, ver §9).
- `inventory/README.md` — el índice derivado, sus consultas y sus límites
  (integrado 18-sep-2026, ver §9).

## 9. Pendientes P1-P3 genuinamente abiertos hoy

- **PR #26/#28 de `legalmente-web`** (P1.6): cerrarlos como SUPERSEDED
  requiere permisos de escritura que las sesiones de este repo no tienen
  (cuenta distinta, `CLAUDE.md §8`). Estado sin re-verificar hoy.
- **Detección de deriva de fuentes oficiales** (P2.5): **parcialmente
  cerrada 18-sep-2026** — el PR #16 (`feat/source-freshness-e-inventario`,
  construido 31-ago-2026, nunca fusionado hasta hoy) traía
  `check-source-freshness.py` (libro mayor offline, fail-closed, 31 tests)
  y se integró a esta rama tras confirmar que sigue vigente. Sigue abierto
  lo que el propio PR ya declaraba como límite estructural: nadie avisa
  desde fuera de que una fuente cambió — el libro mayor sólo sabe lo que
  un humano investigó y escribió en él (riesgo C6 de
  `docs/red-team-cadena-editorial.md`).
- **Inventario materializado** (`docs/contrato-motor-masivo.md` §4.1):
  **cerrado 18-sep-2026** por la misma integración — `scripts/inventory.py`,
  31 tests, determinista y regenerable desde artefactos reales.
- **Detección de duplicados por paráfrasis** (P2.7): sin cambios, sigue
  fuera de alcance sin motor semántico — declarado explícitamente, no
  disimulado (ver `test_la_parafrasis_NO_se_detecta_y_queda_declarado`).
- **Integraciones externas (Grok/Manus/Gemini) y agentes/hooks de Drive**
  (P3): deliberadamente no implementados, sin cambios.
- **Proveedor de imagen real conectado**: sigue bloqueado por falta de
  credenciales en el workspace (motor visual, no el subsistema jurídico de
  este documento) — ver `docs/mandato-maestro-cierre-2026-09-17.md`.

## 10. Seguimiento del proyecto — 18-sep-2026

Auditoría integral pedida por el Founder ("da seguimiento al estado actual
del proyecto"): repo, Drive, PRs abiertos, bitácoras, `TECHNICAL_STATE.md`,
documentación, TODOs, demos, módulos y tests. Objetivo: cerrar pendientes
reales con lo ya construido, sin reinventar arquitectura.

**Hallazgo principal: dos PRs abiertos desde antes de esta sesión, nunca
reconciliados con el trabajo posterior.**

1. **PR #16 — `feat/source-freshness-e-inventario`** (construido
   31-ago-2026, 337 tests propios, declarado "NO MERGE" en su momento
   porque era una entrega de validación pendiente de reconciliar, nunca
   fusionado desde entonces). Contenido: exactamente lo que el red-team
   (B1, "mayor consecuencia de lo que queda") y
   `docs/contrato-motor-masivo.md` §4 pedían como prioridad — vigencia de
   fuentes offline/fail-closed y un inventario materializado y
   regenerable. **Integrado hoy** a esta rama (commit `30a9ae5`): cero
   conflictos de código (el PR nunca tocó `visual/` ni la skill jurídica
   existente), sólo conflictos de documentación, resueltos a mano.
   Inventario regenerado tras 18 días de deriva real
   (`python3 scripts/inventory.py build`). 358 tests, todos en verde.
2. **PR #34 — `claude/convergencia-superset`** (`MERGE_CANDIDATE`
   deliberado, 837 tests, `mergeable_state: clean` contra `main`,
   90 archivos, +15.637/-86 líneas, 3-4-sep-2026). Repara bugs
   semánticos reales del motor de candidatos (una capa jurisdiccional que
   el código emitía como `CAPA_A_TRANSVERSAL` contradiciendo su propia
   documentación; `INVENTORY_CANONICAL` declarado falsamente sin haber
   leído nunca Drive — 24/24 candidatos salían "novedad global" sin
   comprobarlo; el registro de fuentes oficiales de 26 a 31 entradas) y
   converge 44 commits divergidos de `main` con 33 commits propios de
   `main`, sin perder trabajo de ningún lado. **NO se integra hoy**: el
   propio PR declara explícitamente "Requiere al fundador" — fusionarlo,
   fechas del INAI contra el DOF, registrar `curia.europa.eu`, decidir
   sobre 4 piezas mono-país, depositar PDFs oficiales en Drive. Absorber
   90 archivos de contenido jurídico y registro de fuentes sin esas
   decisiones del fundador excedería la autorización de esta sesión
   ("puedes... sin volver al Founder por decisiones intermedias" no cubre
   decisiones que el propio autor del PR marcó como del fundador). Queda
   documentado aquí para que el fundador lo revise como su propia
   decisión — ver el PR para el detalle completo.
3. **Paquete Drive "01 — Implementación técnica pendiente (no activa)"**
   (`delivery-art-direction-2026-09-16.zip` + 4 documentos, cuenta
   `legallmente-alt`, bloqueado de publicarse en este repo por permisos
   cruzados de cuenta). Describe una huella visual de 10 dimensiones
   (`primary_direction`, `secondary_direction`, `medium`, `lighting`,
   `palette`, `composition`, `materiality`, `camera_optics`, `realism`,
   `visual_mechanism`) y un catálogo de 780 direcciones — **ya construido
   de forma independiente y más avanzada** en este repo
   (`visual_fingerprint.VisualFingerprint`, exactamente esas 10
   dimensiones; catálogo maestro real de 504 direcciones vía
   `catalog_parser.py`/`policy/catalogo-maestro-v1.md`; más
   `direccion_causal.py`, `concepto_direccion.py`,
   `arquetipo_compositivo.py`, `safe_zone.py`, ninguno presente en el
   paquete de Drive de 16-sep). El propio Drive ya etiqueta el plan
   asociado como "[REFERENCIA TÉCNICA — no ejecutar como canon]" — la
   etiqueta "pendiente" de los otros archivos de esa carpeta está
   desactualizada: la capacidad que describen ya existe, por una vía
   distinta y más completa. No se modifica Drive (fuera de autorización).

**Clasificación de todo lo demás revisado** (ver también §9 arriba y
`docs/mandato-maestro-cierre-2026-09-17.md`): B5 (contenido identificable
sin marcadores léxicos) y C4/P2.7 (paráfrasis) siguen correctamente
diferidos — el propio red-team dice que B5 no se cierra con más regex, y
P2.7 está gated explícitamente a cuando el volumen lo justifique, que hoy
no se cumple (4 piezas piloto). El inventario "a escala de cientos de
piezas" de `contrato-motor-masivo.md` §4.1 tampoco corresponde todavía por
la misma razón — la infraestructura para construirlo ya existe (PR #16,
integrado hoy), falta el volumen que lo justifique, no el mecanismo.
