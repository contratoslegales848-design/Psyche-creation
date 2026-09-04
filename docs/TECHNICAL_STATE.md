# Estado técnico real de LegalMente

**Fecha:** 2026-08-27 · **Base:** `origin/main` en `3dd358b` (PR #14 y #15 fusionados) + rama `feat/source-freshness-e-inventario`
**Semáforo global: AMARILLO** (los dos P0 quedaron cerrados; el amarillo lo sostienen ahora riesgos declarados, no huecos sin control).

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
| Anti-duplicados | 🟡 AMARILLO (nuevo) | Controles literales implementados; la paráfrasis sigue sin detectarse. |
| Motor de generación visual | 🟢 VERDE (para su alcance) | `visual/`, 124 pruebas. Gate fail-closed, adapter canónico, familias, memoria anti-repetición, compilador explicable, dry-run, lotes, reintento selectivo, regeneración, registro. Decisión de marca aplicada (ADR 0002). |
| Composición tipográfica / marca | 🟢 VERDE (nuevo) | `visual/compositor.py`: rasterizado real con Pillow. Métrica tipográfica real, área segura, `exact_copy` inmutable (desborda antes que mutar), marca solo sobre superficie reservada declarada y plana. 33 pruebas. |
| Adapter de proveedor real | 🟡 AMARILLO (nuevo) | `providers/http_provider.py`: adapter HTTP real con transporte inyectable, 23 pruebas, cero llamadas externas. Sin credenciales configuradas en el workspace: no se ha ejecutado contra ningún proveedor. |
| Contrato cross-repo | 🟢 VERDE (ambos lados) | Psyche: `contract/`, Canonical Envelope v1, 8 fixtures, 12 tests. Web: consumidor estricto implementado y probado **localmente** (18 tests), entregado como serie de patches verificada en `handoff/legalmente-web/`. Falta empujarlo: escritura remota bloqueada. |
| Vigencia de fuentes | 🟡 AMARILLO (nuevo, era rojo implícito) | Libro mayor + control offline fail-closed (PR #16, rescatado). Abierto: nadie avisa desde fuera de que una norma cambió, y 25 de 39 fuentes siguen `UNKNOWN`. |
| Inventario materializado | 🟢 VERDE (nuevo) | Índice determinista y regenerable; `check` detecta que está obsoleto (PR #16, rescatado). |
| Métricas | 🟡 AMARILLO | `DUE_FOR_MEASUREMENT` consultable; las cifras siguen tecleándose a mano. |
| Perfiles de proveedor de imagen | 🟡 AMARILLO (nuevo) | Catálogo declarativo (`visual/providers/profiles.py`) + `simulate --live`. El perfil de Gemini está `PROPUESTO_NO_VERIFICADO`: la doc oficial está bloqueada por el proxy de egress. |
| Motor de producción masiva | ⚫ NO CONSTRUIDO | Contrato e infraestructura mínima listos (`docs/contrato-motor-masivo.md`, inventario); el motor, deliberadamente, no. |
| Documentación vs. realidad | 🟡 AMARILLO | Dos derivas detectadas (ver §5). |
| `legalmente-web` | 🟡 AMARILLO | Prototipo honesto, pero el repositorio es **público** y `CLAUDE.md §8` lo declara privado. |
| Publicación automatizada | ⚫ INEXISTENTE (por diseño) | Ninguna automatización publica. Es una regla, no una carencia. |

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

**Pruebas: 1001, todas en verde** (Psyche, contadas por `unittest discover` sobre las 8 suites del repositorio: `visual/` 394, `.claude/skills/legalmente-legal-verification/scripts` 301, `content/topics` 93, `scripts/` 86, `ecosystem/` 57, `content/linkedin` 33, `contract/` 27, `content/claim-packets` 10). Más 23 del consumidor de web, locales.
| Suite | Pruebas |
|---|---|
| `test_validate_claim_packet` | 147 |
| `test_check_pilot_governance` | 37 |
| `test_validate_publication_chain` | 41 |
| `test_confidentiality_rules` | 20 |
| `test_validate_content_provenance` | 30 |
| `visual/` (5 suites) | 207 |
| `contract/test_canonical_envelope` | 12 |
| `test_check_source_freshness` | 31 |
| `test_inventory` | 31 |

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

1. **`CLAUDE.md §8` dice que `legalmente-web` es privado. Es público.** Reverificado
   el 2026-08-31 por clonado anónimo (`git ls-remote` y `git clone` sin credenciales
   funcionan; HEAD `23a9ce0`). Sigue sin corregirse. Es una afirmación de seguridad incorrecta en
   el documento operativo, y conviene corregirla o cambiar la visibilidad — pero
   ninguna de las dos cosas la decide una sesión técnica.
2. **Nombre de paso de CI obsoleto** — decía "mantener el gate cerrado" cuando el
   control ya comprueba coherencia. Corregido en esta rama.
3. **Pruebas congeladas obsoletas** — dos pruebas afirmaban que los paquetes del
   piloto siguen PENDIENTE con gates CERRADO. Hacían fallar la suite ante cualquier
   aprobación humana legítima. Sustituidas por pruebas de coherencia en esta rama.

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
4. Corregir la deriva de `legalmente-web` en `CLAUDE.md §8`.
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
- `.claude/skills/legalmente-legal-verification/references/README-vigencia.md` — el
  libro mayor de vigencia y por qué el veredicto se deriva en vez de almacenarse.
- `inventory/README.md` — el índice derivado, sus consultas y sus límites.
