# LegalMente — Índice maestro del ecosistema

**Versión:** `ECOSYSTEM-INTEGRATION-V2` · **Fecha:** 2026-09-03
**Rama:** `claude/legalmente-integration-surgery-nap17t` · **Base:** `origin/main` en `ef7ffdd`
**Clasificación:** `AUXILIARY` — no modifica canon jurídico, RC0, claims, fuentes ni gates humanos.
**Estado:** `NOT_PUBLISHED` · `NO_PUSH` · `NO_MERGE` · `NO_DEPLOY`

La fuente de verdad es ejecutable y vive en `ecosystem/`. El registro comprueba el
sistema de archivos cada vez que se lee, así que no puede envejecer en silencio.

```bash
python3 -m ecosystem.validate                       # informe + hallazgos
python3 -m unittest ecosystem.test_ecosystem \
                    ecosystem.test_concept_claim_bridge   # 54 pruebas
```

---

## 1. Corrección de la versión anterior

La V1 de este índice concluyó que **seis paquetes auxiliares y el banco editorial de
LinkedIn no existían**, y lo presentó como el hallazgo central. Era falso. Esa
conclusión se apoyaba únicamente en búsquedas de texto sobre los dos repositorios;
nunca se buscó en Drive, que es donde esos objetos viven.

La búsqueda del 2026-09-03 los encontró **todos**, con ID, fecha y tamaño verificables.
El error no estuvo en el estado asignado sino en el método: **ausencia en un
repositorio no es evidencia de inexistencia**. Queda fijado por prueba
(`test_los_paquetes_auxiliares_si_existen_en_drive`) para que no se repita.

Segunda corrección, de la misma raíz: los cinco protocolos `HELP-001…005` que la V1
construyó **ya existían** en Drive (`02_five_help_protocols.md`), con los mismos cinco
protocolos en el mismo orden. `ecosystem/help_protocols.py` queda declarado
`DERIVED_FROM` ese original y no como segunda fuente.

## 2. `DRIVE_EVIDENCE` — qué se buscó y qué apareció

19 artefactos registrados en `ecosystem/drive_evidence.py`, cada uno con nombre, ID,
fecha, tipo, autoridad, clasificación y evidencia.

| Clasificación | N.º | Qué son |
|---|---:|---|
| `FOUND_CANONICAL` | 5 | Constitución, Bitácora, Neutralidad Jurisdiccional, `SOURCE_MX_LFT.pdf`, `SOURCE_ES_ET.pdf` |
| `FOUND_AUXILIARY` | 11 | Los 7 paquetes, LinkedIn Strategy, la aportación de Raymundo y sus dos documentos sueltos |
| `MISSING_ARTIFACT` | 3 | `AR_LCT`, `CO_CST`, `ES_STS_6207_2012` — buscados y no encontrados |

Distinción que este registro sostiene: un artefacto puede estar `FOUND_AUXILIARY`
y su contenido seguir en `ACCESS_GAP`. **Existencia verificada no es contenido
verificado**: las instrucciones prohíben descargar o ejecutar artefactos externos de
forma automática, así que los ZIP están localizados pero no leídos.

## 3. `OBJECT_REGISTRY` — 33 objetos, cero hallazgos

| Estado | N.º |
|---|---:|
| `CANONICAL` | 9 |
| `FOUND_AUXILIARY` | 8 |
| `MISSING_ARTIFACT` | 5 |
| `EXTERNAL_READ_ONLY` | 3 |
| `BLOCKED` | 2 |
| `ABSENT_ON_THIS_BRANCH` | 2 |
| `PROPOSED` | 2 |
| `FROZEN` | 1 |
| `READY_FOR_HUMAN_REVIEW` | 1 |

## 4. `CONCEPT_CLAIM_BRIDGE` — el hueco prioritario, parcialmente cerrado

`ecosystem/concept_claim_bridge.py` liga los conceptos de navegación de
`legalmente-web` con los claims de `psyche-creation`. No es un knowledge graph nuevo:
no redefine `content_id`, `claim_id`, la taxonomía ni el Canonical Envelope, y valida
cada relación contra los claim packets reales del disco.

| Vínculo | Pregunta humana | Estado | Por qué |
|---|---|---|---|
| `BND-002` | ¿Qué distingue propiedad, posesión y tenencia? | `VERIFIED_BINDING` | Claim apto, aprobado por una persona, con fuentes y límites |
| `BND-001` | ¿Cuándo existe relación de trabajo sin contrato escrito? | `PENDING_BINDING` | `pieza-04-claim-1` no está en el árbol de esta rama |
| `BND-003` | ¿Qué diferencia hay entre despido y renuncia? | `ACCESS_GAP` | El claim sigue en `REQUIERE_INVESTIGACION` |

**Una ruta queda recorrible de punta a punta** (`BND-002`), que es el criterio de
finalización: pregunta humana → concepto → claim → fuente → territorio → límite →
ayuda permitida → estado → owner → siguiente acción, todo en `NOT_PUBLISHED`.

El enlace pasa de `DISCONNECTED` a `READY_TO_CONNECT`, no a `CONNECTED`: los
`concept_id` todavía se declaran a mano en vez de leerse del grafo de web, que este
repositorio no puede importar.

Durante la construcción el contrato **rechazó un error propio**: se declaró
`CAPA_A_TRANSVERSAL` para un claim que realmente es `CAPA_B_VARIABLE`. Es exactamente
la falsa universalización que debía impedir, detectada antes de que llegara a nada.

## 5. `PUBLICATION_GATE_MATRIX` — 10 gates, 8 implementados

Invariante probada: ningún gate automático autoriza publicar, y el único que lo hace
(`GATE-PUBLICATION-HUMAN`) no está implementado en código a propósito. Los dos gates
humanos —jurídico y visual— siguen deliberadamente desconectados entre sí.

## 6. `PROVENANCE_MANIFEST`

| Fuente | Estado | Evidencia |
|---|---|---|
| `MX_LFT` | `VERIFIED` | `SOURCE_MX_LFT.pdf` en Drive, 4.225.835 B. Receipt humano 2026-09-02 |
| `ES_ET` | `VERIFIED` | `SOURCE_ES_ET.pdf` en Drive, 695.761 B. Receipt humano 2026-09-02 |
| `AR_LCT` | `HOLD` | Buscado en Drive 2026-09-03: sin resultado. Carpeta AR vacía |
| `CO_CST` | `HOLD` | Buscado en Drive 2026-09-03: sin resultado. Carpeta CO vacía |
| `ES_STS_6207_2012` | `HOLD` | Buscado 2026-09-03: sin resultado. CAPTCHA no se resuelve ni se elude |

Ninguna fuente fue verificada por este trabajo: los estados se transcriben del receipt
humano. Ninguna se promovió por aparecer en Drive.

## 7. `HELP_PROTOCOL_REGISTRY` — `DERIVED_FROM`, no original

Cinco protocolos, todos `PROPOSED`, ninguno con `EXACT_COPY` ni `CLAIM_ID` —hay prueba
que lo impide— y todos con condiciones de parada. Autoridad del original de Drive
(`17HeKx9FqZrvqwMDTOarjUtuzqvtYeOUf`); si divergen, gana Drive. La versión en código
se conserva sólo porque aporta validación determinista que el documento no tiene.

## 8. `TEST_REPORT` — conteo real de esta ejecución

| Suite | Pruebas | Resultado |
|---|---:|---|
| `visual/` | 294 | `PASS` |
| Skill de verificación jurídica | 245 | `PASS` |
| `scripts/` | 30 | `PASS` |
| `contract/` | 17 | `PASS` |
| `ecosystem/` | 54 | `PASS` |
| **Total** | **640** | `PASS` |

El informe anterior decía 587: omitía `scripts/`. Este conteo es de una ejecución
nueva, no una cifra histórica reutilizada.

## 9. `FAILURE_INJECTION_REPORT`

Del registro (13 escenarios) y del puente (14 más). Ninguno termina en aprobación
silenciosa:

| Fallo inyectado | Resultado |
|---|---|
| `CONCEPT_ID` ausente | `REJECTED` |
| `CLAIM_ID` ausente | `REJECTED` |
| Claim no encontrado en el canon local | `PENDING_BINDING` |
| Fuente ausente del claim real | `REJECTED` |
| Sin ninguna fuente declarada | `REVIEW_REQUIRED` |
| Territorio ausente en claim nacional | `REJECTED` |
| **Falsa universalización** | `REJECTED` |
| Estado de verificación incompatible | `ACCESS_GAP` |
| Duplicación sin `ALIAS_OF`/`DERIVED_FROM` | `REJECTED` |
| Relación de identidad inventada | `REJECTED` |
| **Publicación activada por error** | `REJECTED` |
| Owner o siguiente acción ausentes | `REJECTED` |
| Packet equivocado | `REVIEW_REQUIRED` |
| Sin acceso al canon | `PENDING_BINDING` |
| Objeto declarado presente y ausente | `HOLD` |
| `object_id` duplicado | `REJECT` |
| Estado o capa inventados | `REJECT` |
| `CANONICAL` con bloqueos | `REVIEW_REQUIRED` |
| Protocolo sin condición de parada | `REJECT` |
| Protocolo con claim | `HOLD` |
| Gate automático que declara publicar | `REJECT` |
| Relación colgante | `FIX_REQUIRED` |

El validador se probó además contra el repositorio real y encontró deriva verdadera
en dos ocasiones: objetos declarados y ausentes en esta rama, y una relación colgante
tras la corrección de Drive. No son pruebas de laboratorio.

## 10. `DECISION_LOG`

| Decisión | Razón |
|---|---|
| Buscar en Drive antes de concluir inexistencia | La V1 falló por no hacerlo; §3.6 lo exige explícitamente |
| No abrir los ZIP | Las instrucciones prohíben descargar o ejecutar artefactos externos automáticamente |
| Separar existencia de contenido (`FOUND_AUXILIARY` + `ACCESS_GAP`) | Localizar un paquete no es haberlo leído |
| Declarar `help_protocols.py` como `DERIVED_FROM` | Dos objetos que representan lo mismo no pueden ser canónicos independientes |
| No resolver los conflictos rama/`main` | Siete conflictos, incluidos claim packets: adjudicar canon es decisión del fundador |
| Corregir el vínculo `BND-002` a `CAPA_B_VARIABLE` | El contrato detectó la falsa universalización; se corrigió el dato, no la regla |
| `NO_PUSH` | El §2 de las instrucciones exige autorización específica para esa operación |

**Conflictos rama ↔ `main`** (comprobados, no resueltos): `pieza-03-honor.json`,
`contract/test_canonical_envelope.py`, `visual/pipeline.py`, `visual/test_composition.py`,
`visual/test_inventory.py`, `visual/test_resolver.py`, `visual/test_visual_advanced.py`.
La rama va 37 adelante y 33 atrás; su PR #17 está **cerrado sin fusionar**. El commit
de esta sesión es portable: se verificó con el diff real que `90f0063` no modificó
ningún archivo existente (0 archivos `M`, sólo altas).

## 11. `BLOCKER_BURN_DOWN` — los diez objetos, con clasificación exacta

| Objeto | Clasificación | Evidencia |
|---|---|---|
| Content Factory V1 | `FOUND_AUXILIARY` | Drive `1uNgeBTXxDxy9pPRQxs75d9YAMYRDo1Kf`, 142.868 B |
| Visual Factory V1 | `FOUND_AUXILIARY` | Drive `12q4732yQ1HDvw4r1lEVabGrG2O9BKnc-`, 124.547.274 B |
| Expansion Business Launch Lab V1 | `FOUND_AUXILIARY` | Drive `1b-AwtjFLi4u1xD4Tj_l6iGuy80cUeRH3`, 110.266 B |
| Commercial & Launch Operations V1 | `FOUND_AUXILIARY` | Drive `1Nl35JS4UAZpaCIac7rP2tOAbZDX_nRTX`, 35.622 B |
| LC1 Release Assembly Dry Run V1 | `FOUND_AUXILIARY` | Drive `13lt8LdL6PyEp0lIaUXlpkGuUF5VfBuAY`, 34.036 B |
| Public Launch Closure Factory V1 | `FOUND_AUXILIARY` | Drive `1r_55-ApsfRO8I2dzcqurBZUmA-NyMf9Q`, 41.285 B |
| Demand / Growth Intelligence V1 | `FOUND_AUXILIARY` | Drive `1VY9AcbVa-KZk3xA4yKtGCzo71EXwd5Or`, 136.573 B |
| LinkedIn Strategy (Artefacto 05) | `FOUND_AUXILIARY` | Drive `1GWyYAZ2T7x__I-FqmRsDrbaEC7IXloo2Ycq3tcWc_I0` |
| RC0 | `MISSING_ARTIFACT` | Sin artefacto en repos ni en la búsqueda de Drive |
| Gold Standard visual | `MISSING_ARTIFACT` | Sin artefacto; la condición para generar arte no puede darse por cumplida |

Bloqueos activos:

| ID | Bloqueo | Dueño |
|---|---|---|
| `ECO-BLK-SOURCES-HOLD` | 3 PDFs oficiales sin obtener | fundador |
| `ECO-BLK-DRIVE-CONTENT-UNREAD` | 8 paquetes localizados, contenido no leído | fundador |
| `ECO-BLK-NO-WRITE-WEB` | Sin permisos sobre `legallmente-alt` | fundador |
| `ECO-BLK-STALE-BRANCH` | Rama 33 detrás, PR #17 cerrado sin fusionar | fundador |
| `ECO-BLK-NAMED-NOT-BUILT` | RC0 y Gold Standard sin artefacto | fundador |
| `ECO-BLK-NO-REAL-PROVIDER` | Sin credenciales de proveedor de imagen | fundador |

## 12. `HANDOFF_README`

Leer en este orden: `CLAUDE.md`, `docs/TECHNICAL_STATE.md`, este índice; después
ejecutar `python3 -m ecosystem.validate`. Si devuelve hallazgos, empezar por ahí:
significa que el repositorio y el registro divergieron.

Nada de esta sesión requiere reversión: todo es adición en `ecosystem/` y
`docs/ecosystem/`. Reversible borrando los archivos o revirtiendo el commit.

## 13. `CHECKSUMS`

`docs/ecosystem/CHECKSUMS.txt`, `sha256sum` sobre los módulos de `ecosystem/`.

---

## Siguiente acción única

**Autorizar la lectura del contenido de los paquetes de Drive**, empezando por
`LEGALMENTE_CONTENT_FACTORY_V1.zip`. Es lo que desbloquea más: ocho objetos están hoy
localizados pero no integrados, y sin leerlos no se puede saber qué parte del
ecosistema ya está resuelta ahí y qué se estaría reconstruyendo por segunda vez —que
es precisamente el error que esta sesión tuvo que corregir dos veces.

Las tres fuentes en `HOLD` siguen siendo el bloqueo jurídico, pero ya no es la única
acción disponible.
