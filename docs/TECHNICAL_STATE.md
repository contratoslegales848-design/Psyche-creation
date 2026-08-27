# Estado técnico real de LegalMente

**Fecha:** 2026-08-27 · **Base:** `origin/main` en `82f226e` + rama `chore/phase1-technical-readiness`
**Semáforo global: AMARILLO.**

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
| Enlace verificación → renderizado | 🔴 ROJO | `content/*.json` no tiene ningún campo que lo ligue a un claim packet aprobado. |
| Confidencialidad | 🔴 ROJO | Campo declarativo sin ningún control ejecutable sobre el contenido publicable. |
| Pipeline de video (Remotion) | 🟡 AMARILLO | Funciona y renderiza, pero renderiza contenido sin respaldo jurídico. |
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
- `scripts/validate-publication-chain.py` — **nuevo**: la cadena post-aprobación.
- `references/official-source-registry.json` — 22 organismos oficiales.
- `fixtures/` — 10 positivas, 46 negativas.
- `publication/fixtures/` — 2 cadenas válidas, 14 inválidas, 1 claim packet sintético.

**Pruebas: 225, todas en verde.**
| Suite | Pruebas |
|---|---|
| `test_validate_claim_packet` | 147 |
| `test_check_pilot_governance` | 37 |
| `test_validate_publication_chain` | 41 |

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
Remotion 4 + React/TypeScript. `content/*.json` → `src/content.ts` (validación de
forma) → `src/compositions/LegalMenteQuote.tsx`. CI renderiza en `push` a `main`
que toque `content/**`, y sube los MP4 como artefactos. Funciona.

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
- `legalmente-confidentiality` — no implementada. **Es el hueco más serio.**
- Los 6 agentes (`legal-researcher`, `legal-auditor`, `narrative-editor`,
  `visual-director`, `privacy-reviewer`, `growth-analyst`) — ninguno existe.
- Los 4 hooks (PRE-NARRATIVA, PRE-ARTE, PRE-PUBLICACIÓN, POST-PUBLICACIÓN) — ninguno existe.
- Integración con Grok, Manus o Gemini — solo contratos en borrador
  (`docs/handoff-contracts/`, marcados DRAFT / EXPERIMENTAL).
- Lectura automatizada de métricas de plataforma.
- Cualquier forma de publicación automática. **Por diseño, y así debe seguir.**

---

## 4. El corte real de la cadena

```
[verificación jurídica]                              [producción de video]
claim packet  →  aprobación humana  →  gate arte      content/*.json  →  Remotion  →  MP4
      │                                     │               ▲
      └──────────── ProductionHandoff ──────┘               │
                     (nuevo, existe)                        │
                                                            │
                            ┌───────── AÚN NO CONECTADO ────┘
```

`content/ejemplo.json` se renderiza en CI y **no tiene detrás ningún claim packet**.
`src/content.ts` valida forma (id, título, frase, remate, marca, imagen, duración);
no valida procedencia. El `ProductionHandoff` es el puente diseñado para cerrar ese
hueco, pero el renderizador todavía no lo exige.

**Siguiente paso técnico natural:** añadir a `content/*.json` un campo obligatorio
`content_id` + `handoff_id`, y un paso de CI que rechace renderizar contenido cuya
cadena no valide. No se ha hecho en esta fase porque toca `content/` y `src/`, fuera
del alcance autorizado de este trabajo.

---

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

**P0 — antes de publicar nada**
1. Control de confidencialidad sobre contenido publicable (`CLAUDE.md §5` no tiene
   hoy ningún mecanismo ejecutable).
2. Ligar `content/*.json` a un `ProductionHandoff` válido y hacer que la CI lo exija.

**P1 — antes de escalar el volumen**
3. Decidir sobre la Pieza 1: fusionar o no la aprobación registrada.
4. Corregir la deriva de `legalmente-web` en `CLAUDE.md §8`.

**P2 — cuando el piloto esté medido**
5. Detección de deriva de fuentes oficiales, fuera del validador (ver ADR 0001).
6. Control de duplicados por contenido, no solo por identificador.

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
