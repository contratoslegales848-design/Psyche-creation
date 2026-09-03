# LegalMente — Índice maestro del ecosistema

**Versión:** `ECOSYSTEM-INTEGRATION-V1` · **Fecha:** 2026-09-03
**Rama:** `claude/legalmente-integration-surgery-nap17t`
**Clasificación:** `AUXILIARY` — no modifica el canon jurídico, ni RC0, ni los gates humanos.
**Estado de publicación:** `NOT_PUBLISHED` · `NO_AUTO_SEND` · `NO_PII`

Este documento es la vista humana. La **fuente de verdad es ejecutable** y vive en
`ecosystem/`: el registro comprueba el sistema de archivos real cada vez que se lee,
así que no puede quedar obsoleto en silencio como un inventario escrito a mano.

```bash
python3 -m ecosystem.validate          # informe + hallazgos
python3 -m unittest ecosystem.test_ecosystem   # 31 pruebas
```

---

## 1. `MASTER_ECOSYSTEM_INDEX` — qué es el ecosistema hoy

| Módulo | Responsabilidad | Estado |
|---|---|---|
| `ecosystem/registry.py` | 30 objetos con estado verificado en ejecución | `AUXILIARY` |
| `ecosystem/relations.py` | Grafo de relaciones; consume `visual/topology.py` | `AUXILIARY` |
| `ecosystem/gate_matrix.py` | Matriz única de los 10 gates | `AUXILIARY` |
| `ecosystem/help_protocols.py` | HELP-001 a HELP-005 | `PROPOSED` |
| `ecosystem/validate.py` | Validación determinista + severidades | `AUXILIARY` |
| `ecosystem/test_ecosystem.py` | 31 pruebas, mitad inyección de fallos | `AUXILIARY` |

## 2. `OBJECT_REGISTRY` — 30 objetos, cero hallazgos

| Estado | N.º | Lectura |
|---|---:|---|
| `CANONICAL` | 9 | Existen, se ejecutan y tienen prueba |
| `MISSING_ARTIFACT` | 10 | **Nombrados por el prompt; sin artefacto en ningún repositorio** |
| `EXTERNAL_READ_ONLY` | 3 | Viven en `legalmente-web`; legibles, no escribibles desde aquí |
| `BLOCKED` | 2 | PIEZA-02 y PIEZA-03, por fuentes en HOLD |
| `PROPOSED` | 2 | Construidos y probados, sin fusionar |
| `ABSENT_ON_THIS_BRANCH` | 2 | Existen en `main`; esta rama va 27 commits detrás |
| `FROZEN` | 1 | PIEZA-01, aprobada con handoff emitido |

`ABSENT_ON_THIS_BRANCH` se separó de `MISSING_ARTIFACT` a propósito: confundir
«nunca se construyó» con «esta rama está atrasada» haría creer que el proyecto no
tiene PIEZA-04 ni la dirección de contenido, cuando ambas están fusionadas en `main`.

## 3. `RELATIONSHIP_MAP` — los cinco huecos de integración

El grafo hereda en vivo `visual/topology.py` (enlaces del organismo, etapas del
content factory, cadena publicación/medición/aprendizaje) y añade la capa de
ecosistema. **No se construyó un grafo paralelo.** 19 huecos declarados; los cinco
que deciden si LegalMente se lee como un solo sistema:

| # | Hueco | Evidencia verificada |
|---|---|---|
| 1 | **Seis de siete paquetes del §1 no existen** | `Visual Factory`, `Expansion Lab`, `Commercial Ops`, `LC1`, `Public Closure`, `Demand Intelligence`: cero coincidencias en ambos repositorios |
| 2 | **La entrada humana no conoce la evidencia** | El grafo de mundos y conceptos vive en `legalmente-web`; los claim packets en Psyche. Ningún objeto liga un `CONCEPT` con un `CLAIM_ID` |
| 3 | **HELP-001…005 no existían** | Cero coincidencias. Creados aquí como `PROPOSED`, sin copy normativo |
| 4 | **No había matriz de gates única** | Gates reales dispersos entre `visual/gates.py` y el contrato de web |
| 5 | **El puente Raymundo/LinkedIn no existe** | `Raymundo` aparece sólo como aprobador humano; `LinkedIn` una vez, de paso |

El hueco 2 es el más importante: es el que impide recorrer *pregunta humana →
fuente → límite* sin cambiar de repositorio a mano.

## 4. `PUBLICATION_GATE_MATRIX` — 10 gates, 8 implementados

Invariante probada: **ningún gate automático autoriza publicar**, y el único que lo
hace (`GATE-PUBLICATION-HUMAN`) no está implementado en código a propósito. Los dos
gates humanos —revisión jurídica y revisión visual— están deliberadamente
desconectados entre sí: aprobar uno nunca implica el otro.

Detalle completo en `ecosystem/gate_matrix.py`, con la columna que más importa:
qué **no** autoriza cada gate.

## 5. `PROVENANCE_MANIFEST`

| Fuente | Estado | Verificado por |
|---|---|---|
| `MX_LFT` | `VERIFIED` | Receipt humano 2026-09-02: PDF directo, 457 págs, SHA-256 fijado |
| `ES_ET` | `VERIFIED` | Receipt humano 2026-09-02: PDF consolidado, 97 págs, SHA-256 fijado |
| `AR_LCT` | `HOLD` | Infoleg entrega HTML; sin PDF oficial directo |
| `CO_CST` | `HOLD` | SUIN-Juriscol sin PDF verificable |
| `ES_STS_6207_2012` | `HOLD` | Enlace del CGPJ redirige a CAPTCHA — no se resuelve ni se elude |

Ninguna fuente fue verificada por este trabajo: los estados se **transcriben** del
receipt humano. Una fuente en `HOLD` no autoriza claims, `EXACT_COPY` ni arte.

## 6. `RAYMUNDO_LINKEDIN_BRIDGE` — vacío a propósito

`MIS-LINKEDIN-BANK` = `MISSING_ARTIFACT`. El prompt describe un banco de experiencia
profesional y siete pilares editoriales, pero **no existe ningún artefacto** en los
repositorios. Registrar temas inferidos de esa descripción sería inventar contenido
editorial y, peor, arriesgaría convertir experiencia profesional privada en material
publicable —lo que `CLAUDE.md §5` prohíbe.

El puente se construirá cuando el banco exista como documento real y anonimizado.
Hasta entonces: cero `PROPOSED_TOPIC`, y ninguna publicación autorizada.

## 7. `HELP_PROTOCOL_REGISTRY` — 5 protocolos, todos `PROPOSED`

`HELP-001` antes de comprar tierra · `HELP-002` de predio matriz a lote ·
`HELP-003` quién debe intervenir · `HELP-004` marketing, autorización y contrato ·
`HELP-005` cuándo detenerse.

Ninguno lleva `EXACT_COPY` ni `CLAIM_ID`, y hay una prueba que lo impide: en cuanto
un protocolo afirmara una regla concreta dejaría de orientar y pasaría a exigir
fuente, territorio y vigencia. Cada uno declara sus condiciones de parada —la parte
importante, porque marcan dónde el sistema deja de ayudar y empieza a hacer daño.

## 8. `CONTENT_GENERATION_FLOW_MATRIX`

El pipeline del §8 del prompt existe **parcialmente y repartido**: la verificación de
fuentes y el gate de arte en Psyche; la rotación visual y la composición editorial en
web; la autorización de publicación en ninguna parte, por diseño. `content_factory_topology()`
ya clasifica cada etapa por lo que existe hoy, y esa lectura se hereda aquí sin duplicarse.

## 9. `BUILD_BACKLOG_P0_P3`

**P0 — completado en esta sesión:** índice maestro, registro de objetos, grafo de
relaciones, matriz de gates, manifiesto de procedencia, suite determinista.

**P1 — parcial:** `Before Signing` existe en web; HELP-001…005 quedan `PROPOSED` a la
espera de revisión humana. La navegación por pregunta humana depende del hueco 2.

**P2 y P3 — bloqueados.** El §9 prohíbe avanzar con blockers críticos en P0/P1, y hay
dos: fuentes en HOLD y sin escritura sobre `legalmente-web`.

## 10. `TEST_REPORT`

| Suite | Pruebas | Resultado |
|---|---:|---|
| `visual/` | 294 | `PASS` |
| Skill de verificación jurídica | 245 | `PASS` |
| `contract/` | 17 | `PASS` |
| `ecosystem/` (nueva) | 31 | `PASS` |
| **Total** | **587** | `PASS` |

## 11. `FAILURE_INJECTION_REPORT`

Trece escenarios del §11 inyectados; los trece terminan en una severidad explícita,
ninguno en aprobación silenciosa:

| Fallo inyectado | Resultado |
|---|---|
| Objeto declarado presente y ausente | `HOLD` |
| `object_id` duplicado | `REJECT` |
| Owner ausente | `FIX_REQUIRED` |
| Siguiente acción ausente | `FIX_REQUIRED` |
| Estado inventado fuera del vocabulario | `REJECT` |
| Capa inventada | `REJECT` |
| **Flag de publicación activado por error** | `REJECT` |
| `CANONICAL` con bloqueos activos | `REVIEW_REQUIRED` |
| Protocolo de ayuda sin condición de parada | `REJECT` |
| Protocolo de ayuda con claim | `HOLD` |
| Gate automático que declara autorizar publicación | `REJECT` |
| Relación colgante | `FIX_REQUIRED` |
| Severidad inventada | imposible por construcción |

El validador se probó además **contra el repositorio real y encontró deriva
verdadera** (dos objetos declarados y ausentes en esta rama), que es lo que motivó
el estado `ABSENT_ON_THIS_BRANCH`. No es una prueba de laboratorio.

## 12. `DECISION_LOG`

| Decisión | Razón |
|---|---|
| Consumir `visual/topology.py` en vez de escribir un grafo nuevo | §2 prohíbe arquitecturas paralelas; el grafo ya existía y funciona |
| Registrar los 6 paquetes ausentes en lugar de construirlos | §2 prohíbe inventar; su ausencia **es** el hallazgo |
| Verificar el estado en ejecución, no declararlo estático | `CLAUDE.md §2`: una mención no es una capacidad |
| Separar `ABSENT_ON_THIS_BRANCH` de `MISSING_ARTIFACT` | Confundirlos borraría la diferencia entre «no existe» y «rama atrasada» |
| Dejar vacío el puente de LinkedIn | Inferir temas sería inventar contenido y rozar `CLAUDE.md §5` |
| Abortar el merge de `main` | Siete conflictos, incluidos claim packets: adjudicar canon es decisión del fundador |
| Un índice con 15 secciones, no 15 archivos | §13: más archivos no es más integración |

## 13. `BLOCKER_BURN_DOWN`

| ID | Bloqueo | Desbloquea | Dueño |
|---|---|---|---|
| `ECO-BLK-SOURCES-HOLD` | 3 PDFs oficiales sin obtener | PIEZA-02, PIEZA-03, cualquier `D4` comparativo | fundador |
| `ECO-BLK-NO-WRITE-WEB` | Sin permisos sobre `legallmente-alt` | Canonical Envelope y contrato de composición | fundador |
| `ECO-BLK-NAMED-NOT-BUILT` | 10 objetos nombrados sin artefacto | La jerarquía de autoridad §1 completa | fundador |
| `ECO-BLK-ENTRY-EVIDENCE-GAP` | `CONCEPT` no liga con `CLAIM_ID` | Recorrido completo del ecosistema | pendiente de decisión |
| `ECO-BLK-STALE-BRANCH` | Rama 27 commits detrás, PR #17 cerrado sin fusionar | Registro completo en esta rama | fundador |
| `ECO-BLK-NO-REAL-PROVIDER` | Sin credenciales de proveedor de imagen | Generación visual real | fundador |

## 14. `HANDOFF_README`

Quien continúe debe leer, en este orden: `CLAUDE.md`, `docs/TECHNICAL_STATE.md`, este
índice, y después ejecutar `python3 -m ecosystem.validate`. Si el informe devuelve
hallazgos, **empezar por ahí**: significa que el repositorio y el registro divergieron.

Ninguna acción de esta sesión requiere reversión: todo lo construido son archivos
nuevos en `ecosystem/` y `docs/ecosystem/`, sin tocar canon, claims, gates ni fuentes.

## 15. `CHECKSUMS`

Ver `docs/ecosystem/CHECKSUMS.txt`, generado con `sha256sum` sobre los seis módulos
de `ecosystem/`.

---

## Siguiente acción única

**Obtener los tres PDFs oficiales en `HOLD` (`AR_LCT`, `CO_CST`, `ES_STS_6207_2012`)
o autorizar una entrega manual.** Es el bloqueo con más dependencias aguas abajo: sin
él no avanzan PIEZA-02, PIEZA-03, ninguna pieza comparativa ni el cierre del hueco 2.

No generar más contenido para llenar el vacío.
