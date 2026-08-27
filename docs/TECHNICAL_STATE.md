# Estado técnico real de LegalMente

**Fecha:** 2026-08-27 · **Base:** `origin/main` en `82f226e` + ramas `chore/phase1-technical-readiness` y `chore/phase1-p0-confidencialidad-procedencia`
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
| Motor de producción masiva | ⚫ NO CONSTRUIDO | Contrato técnico definido (`docs/contrato-motor-masivo.md`); el motor, deliberadamente, no. |
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
- `scripts/validate-content-provenance.py` (en la raíz) — **nuevo**: procedencia de
  los artefactos de `content/` y controles anti-duplicados.
- `references/official-source-registry.json` — 22 organismos oficiales.
- `fixtures/` — 10 positivas, 46 negativas.
- `publication/fixtures/` — 2 cadenas válidas, 14 inválidas, 1 claim packet sintético.

**Pruebas: 275, todas en verde.**
| Suite | Pruebas |
|---|---|
| `test_validate_claim_packet` | 147 |
| `test_check_pilot_governance` | 37 |
| `test_validate_publication_chain` | 41 |
| `test_confidentiality_rules` | 20 |
| `test_validate_content_provenance` | 30 |

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

1. **`CLAUDE.md §8` dice que `legalmente-web` es privado. Es público.** Verificado
   directamente contra el repositorio. Es una afirmación de seguridad incorrecta en
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
3. Decidir sobre la Pieza 1: fusionar o no la aprobación registrada.
4. Corregir la deriva de `legalmente-web` en `CLAUDE.md §8`.

**P2 — cuando el piloto esté medido**
5. Detección de deriva de fuentes oficiales, fuera del validador (ver ADR 0001).
   Es ahora el riesgo abierto de mayor consecuencia.
6. Inventario materializado y planificación de cobertura para el motor masivo
   (ver `docs/contrato-motor-masivo.md` §4).
7. Detección de duplicados por paráfrasis, cuando el volumen lo justifique.

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
