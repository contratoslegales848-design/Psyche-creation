# Estado técnico real de LegalMente

**Fecha:** 2026-08-27 (última verificación de suites y cruce con Drive: 2026-09-11) · **Base:** `origin/main` en `ef7ffdd` (incluye ya pieza-04-laboral-basico, PR #32)
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

**Pruebas: 651, todas en verde** (Psyche, reejecutadas el 2026-09-11 con `unittest discover`;
requiere `pip install Pillow` para `visual/`, tal como documenta `requirements.txt` — sin eso,
11 pruebas de `visual/` fallan por `ModuleNotFoundError`, no por regresión de código). Más 23
del consumidor de web, locales, no reejecutadas esta sesión.
| Suite | Pruebas |
|---|---|
| `test_validate_claim_packet` | 147 |
| `test_check_pilot_governance` | 37 |
| `test_validate_publication_chain` | 41 |
| `test_confidentiality_rules` | 20 |
| `test_validate_content_provenance` | 30 |
| `test_check_unittest_main_guard_position` | 4 |
| `visual/` (14 archivos `test_*.py`, `discover`) | 355 |
| `contract/test_canonical_envelope` | 17 |

El número de `visual/` y `contract/` creció frente a la última medición (207 y 12
respectivamente): son suites activas, no un error de conteo — verificado corriendo
`python3 -m unittest discover` sobre cada carpeta el 2026-09-11.

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
| `pieza-01-reales.json` | 3 (1, 2, 4) | APTO_PARA_NARRATIVA | CERRADO (gate global; el claim individual con aprobación humana está ABIERTO) |
| `pieza-02-laboral.json` | 7 | REQUIERE_INVESTIGACION | CERRADO |
| `pieza-03-honor.json` | 7 | REQUIERE_INVESTIGACION | CERRADO |
| `pieza-04-laboral-basico.json` | 1 (Capa A transversal) | APTO_CON_MATICES | CERRADO — pendiente `revision_humana` de `pieza-04-claim-1` |
| `linkedin-ray-01/04/05/12/13/14/17-*.json` (7 piezas) | 1 c/u | REQUIERE_INVESTIGACION | CERRADO — marcos de proceso sin fuente aplicable, `alcance: NO_DETERMINADO` |
| `linkedin-ray-16-poder-facultades-y-limites.json` | 3 | BLOQUEADO | CERRADO — claim 1 (mandato/poder) y claim 3 (reformulación corregida) en APTO_CON_MATICES, **con `revision_humana: APROBADO` desde 2026-09-12** (registrado en [Drive](https://docs.google.com/document/d/1YhXjLyJlHz5DmXq5r1W4aQuvTDjZDHga70jNkFH0u-o/edit); ver límite honesto del mecanismo ahí y en la skill). El gate sigue CERRADO porque `estado != APTO_PARA_NARRATIVA` — la aprobación humana no compensa el techo de Nivel 2. Claim 2 (formulación original, "el cargo no prueba representación") sigue BLOQUEADO tras investigación societaria real (LGSM/LSC/LGS/CCom): es falso para el cargo de administrador, que sí representa por ley. Un BLOQUEADO frena el agregado de toda la pieza — por diseño. |

Las 8 piezas `linkedin-ray-*` nacieron el 2026-09-12 por instrucción expresa
del fundador ("Empieza por los 8 SAFE_EDITORIAL_FRAME") sobre el banco de
`docs/linkedin-raymundo-inmobiliario.md §3.1` — detalle completo del resultado
ahí. `pilot/claim-packets/` tiene ahora **12** piezas reales (antes 4);
`test_las_piezas_reales_pasan_validacion_estructural`,
`visual/test_inventory.py` y `visual/test_resolver.py` se actualizaron para
reflejarlo (651 pruebas totales siguen en verde).

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
4. **El gateway de Drive ("00 LEER PRIMERO") y el Índice v18 citan
   `docs/auditoria-editorial.md` y `docs/auditoria-editorial-50-conceptos.md` como
   "en el repositorio".** Verificado el 2026-09-11 (`find` sobre el árbol completo
   de `Psyche-creation`, incluidas todas las ramas remotas relevantes): ninguno de
   los dos archivos existe. Es el mismo patrón que advierte `CLAUDE.md §2`, en la
   dirección inversa — una mención en Drive tampoco es, por sí sola, un archivo real
   en el repo. Requiere que el fundador o quien mantenga el Índice v18 corrija la
   referencia, o que alguien cargue esos documentos con su contenido real; ninguna
   sesión técnica debe inventar su contenido para "completar" la mención.
5. **Rama sin fusionar `claude/openhands-local-setup-ns163n`** (5 commits por
   delante de `main`, no en la lista de ramas activas conocidas): contiene los
   claim packets del Microlote 01 / Release 01 (`LM-R01-001`, `006`, `011`, `014`)
   que el handoff de Drive (`CLAUDE_DIRECT_HANDOFF_RELEASE01.md`,
   `RELEASE01_MICROLOT_STATUS.json`) pedía crear, y que **no existen todavía en
   `main` ni en esta rama** — el `canonical_validator_executed: false` que registra
   ese JSON de estado en Drive sigue siendo cierto para `main`. Esa rama también
   registra una `revision_humana.estado: "APROBADO"` para `LM-R01-006` con
   `revisor: "Raymundo"`, justificada en el commit como "confirmado vía chat de
   sesión de Claude Code" — exactamente el patrón que la propia skill señala como
   no verificable en su sección "Límite honesto sobre la aprobación humana" (un
   modelo puede escribir ese campo con la misma facilidad que un humano; el nombre
   no prueba autoría). No se fusionó ni se replicó ese patrón en esta sesión.
   **Pendiente de decisión del fundador**: (a) si esa aprobación es legítima y cómo
   autenticarla fuera de este mecanismo antes de confiar en ella, y (b) si/cómo
   fusionar esa rama — evaluando también que trae un commit de dirección artística
   adaptativa v1.2 que aún no pasó por este `main`. Hasta entonces, Release 01 sigue
   sin artefactos en `main`.
6. **Drive describe `LM-PC-013`, `LM-PC-031` y `LM-PC-065` como
   `CORE_LINKED_AND_READY_FOR_INTEGRATION`** (claims aprobados, fuentes
   mexicanas, copy, visuales 9:16/4:5, web brief y QA) en varios documentos de
   "agent contribution" no producidos por sesiones de este repositorio.
   Verificado el 2026-09-11 con `grep -r "LM-PC-01[35]\|LM-PC-065"` sobre todo
   el árbol de trabajo: **ninguno de esos tres IDs existe en `Psyche-creation`**
   — ni como claim packet, ni como contenido, ni en ninguna rama. Es el mismo
   patrón que el punto 4 de esta lista: una narrativa de "listo para integrar"
   en Drive, sin el archivo real detrás en el repositorio que sería su fuente
   de verdad técnica. No se puede confirmar ni negar el estado jurídico de esas
   tres piezas desde este repositorio — solo que no están aquí.
7. **`EGRESS_BLOCKED` reconfirmado el 2026-09-11** contra `www.diputados.gob.mx`
   (LFT) desde esta sesión, con `WebFetch` disponible como herramienta — no es que
   faltara intentarlo: el bloqueo de red persiste igual que documenta
   `docs/pieza-02-03-verificacion-pendiente.md`. La verificación de fuentes
   pendientes de PIEZA-02/03 y del Microlote 01 sigue requiriendo un humano o una
   sesión con salida de red distinta.

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
7. **Decisión del fundador sobre la rama `claude/openhands-local-setup-ns163n`**
   (Release 01 / Microlote 01): si la aprobación humana registrada para
   `LM-R01-006` es legítima y cómo autenticarla, y si/cómo fusionar los cuatro
   claim packets de esa rama a `main`. Ver §5.5 arriba. Sin esto, Release 01 no
   avanza en el repositorio canónico.
8. **Corregir en Drive** la referencia del Índice v18 a
   `docs/auditoria-editorial.md` / `docs/auditoria-editorial-50-conceptos.md`
   como "en el repositorio" — no existen ahí. Ver §5.4. Esto lo decide quien
   mantiene el Índice v18, no una sesión técnica; esta sesión no modificó Drive.
9. **Aclarar el estado real de `LM-PC-013`/`031`/`065`** — Drive los describe
   como listos para integrar a `legalmente-web`, pero no existen en ningún
   repositorio verificado desde aquí. Ver §5.6. Quien tenga acceso a
   `legalmente-web` y a los documentos originales de esas piezas debe
   confirmar si existen en otro lugar o si la narrativa de Drive está
   adelantada a la implementación real.
10. **Founder LinkedIn — 18 candidatos de experiencia real, sin verificar.**
    Ver `docs/linkedin-raymundo-inmobiliario.md` (nuevo, 2026-09-11). Ninguno
    tiene claim packet; el fundador debe elegir cuáles avanzan primero, y cada
    uno recorre `legalmente-legal-verification` antes de cualquier copy o arte.

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
- `docs/direccion-basico-antes-que-complejo.md` — prioridad de materias para
  contenido básico transversal.
- `docs/linkedin-raymundo-inmobiliario.md` — banco de 18 temas de experiencia
  profesional real del fundador para LinkedIn (Inmobiliario), sin verificar.
- `docs/auditoria-automatizacion-segura.md` — auditoría de todo el pipeline
  para automatización segura, priorizada en estandarización → automatización
  → ejecución continua con puertas de control (2026-09-12).
- `docs/direccion-trazabilidad-emocional.md` — dirección de producto: preocupación
  → necesidad → opciones con fuente, certidumbre y límite; estilo artístico acorde
  a la emoción (sin candado rígido), medible cuando existan métricas (2026-09-12).
- `docs/politica-capa-necesidad.md` + `docs/piloto-capa-necesidad.json` — política
  operativa corta de la capa de interpretación de necesidad (emoción como puerta de
  entrada, no salida) y piloto de 6 casos de extremo a extremo (v2, 2026-09-12):
  clasificación en tres estados con `FRONTERA_INDETERMINADO` (no se fuerza; hecho
  mínimo faltante) y registros como preocupación observable + contexto funcional
  (no taxonomía psicológica; agregan a la futura LegalMente Radar). No implementa nada.
