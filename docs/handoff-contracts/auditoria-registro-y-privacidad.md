# Auditoría — registro de fuentes, privacidad histórica y limpieza

**Fecha:** 2026-09-03 · **Rama:** `claude/legalmente-integration-surgery-nap17t`
**Estado:** `NOT_PUBLISHED` · 10/10 gates `CERRADO` · sin force-push, sin reescritura de historia

## 1. Referencias verificadas

| Commit | Estado | Contenido |
|---|---|---|
| `1e6ddb7` | **existe** | Primeros 3 claim packets v4 |
| `ee20c22` | **existe** | Lote completo de 10 + registro v1.0→v1.1 |
| `2f57dd8` | **existe** | Retirada del correo del árbol |
| `aeb7596` | **NO EXISTE** | Referencia fantasma |

`aeb7596` no está en este repositorio. El cambio que se le atribuía —aceptar AEPD, INAI, SIC y OIT—
está en `ee20c22`. No se buscó reproducirlo ni se revirtió nada.

## 2. Registro oficial único

Un solo registro, canónico:
`.claude/skills/legalmente-legal-verification/references/official-source-registry.json`, v1.1, 26
entradas. No existe ningún registro paralelo (comprobado por búsqueda de nombre en todo el árbol).

### Estado de verificación de las cuatro entradas nuevas

| `id` | Hostname declarado | Verificación de dominio | Estado |
|---|---|---|---|
| `aepd-es` | `aepd.es` | **PENDIENTE** | `EGRESS_BLOCKED` |
| `inai-org-mx` | `inai.org.mx`, `home.inai.org.mx` | **PENDIENTE** | `EGRESS_BLOCKED` |
| `sic-gov-co` | `sic.gov.co` | **PENDIENTE** | `EGRESS_BLOCKED` |
| `ilo-org` | `ilo.org`, `normlex.ilo.org` | **PENDIENTE** | `EGRESS_BLOCKED` |

Las cuatro descansan en la orden expresa del fundador, **no** en una comprobación de dominio hecha
por el modelo. Cada entrada lo declara en su propio `_nota`. Ninguna fuente que las use alcanza hoy
Nivel 1, porque además falta la lectura del texto.

Distinciones que el registro mantiene separadas, y que no deben colapsarse: nombre declarado ≠
dominio verificado; URL oficial ≠ texto jurídico exacto; fuente internacional ≠ fuente nacional;
fuente institucional ≠ artículo aplicable.

### Pruebas nuevas: `scripts/test_official_source_registry.py`

23 pruebas deterministas, en dos planos.

**El registro en sí** — identificadores únicos, toda entrada con autoridad, toda entrada con
jurisdicción, tipos del enum cerrado, hostnames parseables, ningún hostname en dos entradas, ningún
organismo canónico repetido, ningún alias que colisione con el canónico de otra entrada, las cuatro
autoridades nuevas presentes, y la OIT sin respaldar ninguna jurisdicción nacional.

**El uso del registro** — resolución de `registro_oficial_id` a entrada real, **prohibición de usar
una fuente fuera del territorio autorizado**, fechas ISO válidas, URLs parseables, ninguna fuente
sin verificar alcanzando Nivel 1, y ninguna fuente duplicada dentro de un claim.

## 3. Barrera anti-falsa-universalización

Cuatro pruebas nuevas convierten el hallazgo del lote en una barrera automática:

- Capa A exige ≥3 jurisdicciones revisadas, cada una con `fuente_ids` propios.
- Ningún claim transversal puede sostenerse en países **realmente cubiertos por sus fuentes** < 3
  —se cuentan las fuentes, no los países nombrados en la prosa.
- `NO_DETERMINADO` nunca supera `REQUIERE_INVESTIGACION` ni abre gate.
- Las cuatro piezas monopaís (`LM-EVG-002`, `LM-EVG-003`, `LM-CORP-002`, `LM-CORP-004`) no pueden
  promoverse a transversales sin ampliar jurisdicciones.

**Verificado por mutación, no por afirmación:** al promover artificialmente `LM-EVG-002` a
`CAPA_A_TRANSVERSAL`, **tres pruebas independientes fallaron** con el detalle exacto
(«sus fuentes solo cubren ['méxico']»). Restaurado después; árbol limpio.

## 4. Correcciones jurídico-editoriales aplicadas

Dos piezas mezclaban afirmaciones que deben viajar separadas. Ninguna corrección inventó evidencia:
sólo se separó lo que ya estaba declarado.

**`LM-HIS-005` — 1 claim → 2.** El copy afirmaba restitución «desde el origen» citando la STS de
9-5-2013, que precisamente **limitó** la retroactividad. Ahora:

- `claim-1` (STS 2013): la nulidad por falta de transparencia material — lo que esa sentencia sí sostiene.
- `claim-2` (TJUE): la restitución íntegra, con `redaccion_prohibida` explícita contra atribuirla a la STS.

Se corrigió el copy, no sólo la tabla de fuentes.

**`LM-ACT-001` — 1 claim → 2.** El Convenio 158 de la OIT viajaba junto a la jurisprudencia
española. Un convenio internacional no es fuente de derecho interno por sí solo: sólo obliga en el
país que lo ratificó y su efecto depende de ese derecho. El `claim-2` queda en `NO_APLICA` —describe
un instrumento internacional, no una regla nacional.

Los 10 packets suman ahora **13 claims**, todos en `REQUIERE_INVESTIGACION` con gate `CERRADO`.

## 5. Privacidad histórica — informe, sin remediación

| Dato | Valor |
|---|---|
| Dato afectado | Una dirección de correo electrónico |
| Archivos | `ecosystem/drive_evidence.py`, `docs/handoff-contracts/lote-10-claim-packets.md` |
| Commits | `70995d5` (introducción), `ee20c22` (segunda introducción), `2f57dd8` (retirada) |
| Rama afectada | `claude/legalmente-integration-surgery-nap17t`, **únicamente** |
| ¿En el árbol actual? | **No** — 0 archivos |
| ¿En el historial? | **Sí** — en los tres commits citados |
| ¿En `origin/main`? | **No** — 0 archivos |
| ¿En artefactos generados? | No — ningún artefacto versionado lo contiene |
| ¿En PRs, comentarios o releases? | No se abrió PR desde esta rama |
| Alcance de exposición | Repositorio **público**; rama remota publicada. Exposición real aunque limitada a una rama de trabajo |

### Opciones de remediación y sus riesgos

| Opción | Efecto | Riesgo |
|---|---|---|
| **No hacer nada** | El dato permanece en 3 commits de una rama pública | Exposición continuada; bajo impacto (dirección del propio titular) |
| **Reescribir los 3 commits** (`filter-repo` o rebase interactivo) + force-push | Elimina el dato del historial de la rama | Reescribe historia y exige force-push; invalida clones existentes; **prohibido por las reglas vigentes sin autorización explícita** |
| **Descartar la rama y rehacer sobre `main` limpio** | Historial nuevo sin el dato | Pierde 41 commits de trabajo; desproporcionado |
| **Fusionar a `main` sólo el árbol final** (squash) | `main` nunca recibe el dato | La rama de trabajo lo conserva; requiere decisión de merge |

**Ninguna se ejecutó.** La reescritura queda pendiente de autorización explícita posterior, como
indica el mandato. Recomendación técnica: la cuarta opción es la de mejor relación coste/beneficio si
el objetivo es que `main` quede limpio.

## 6. Limpieza — nada se eliminó

| Elemento | Clasificación | Prueba |
|---|---|---|
| `artifacts/human-review/LM-PIEZA-01-REALES/review-packet.json` | **Canónico · NO SEGURO DE ELIMINAR** | Idéntico a `review-packet-gen-2f2dfb9c6f2f.json` pero es el **puntero** que lee el inventario. Referenciado en `visual/review_semantics.py` y en dos pruebas de `visual/test_inventory.py` |
| `docs/handoff-contracts/*.md` (5) | **Handoff · necesarios para auditoría** | Contenidos distintos: `README`, `gemini`, `grok`, `manus`, `lote-10` |
| `__pycache__/` (5 directorios) | **Artefacto de compilación** | Correctamente ignorados por `.gitignore`; ninguno versionado |
| Registro de fuentes | **Canónico · único** | Una sola copia en todo el árbol |

**Resultado: cero archivos eliminados, cero marcados `CANDIDATO_A_LIMPIEZA`.** No se hallaron
duplicados exactos no justificados, artefactos de compilación versionados, registros paralelos ni
PII en fixtures, logs o snapshots. El único par idéntico es un puntero deliberado con su snapshot.

## 7. Pruebas — §10 frente a la realidad de este repositorio

Siete de los ocho comandos del mandato son de `legalmente-web`, no de `psyche-creation`.

| Comando | Resultado |
|---|---|
| `npm run typecheck` | **FALLO PREEXISTENTE** — `TS2688: Cannot find type definition file for 'webpack-env'`. Falla idéntico en `origin/main` puro; causa: `node_modules` ausente. Ningún `.ts` fue modificado en los 41 commits de la rama. Se corrige con `npm ci` |
| `npm run lint` | `MISSING_SCRIPT` |
| `npm run test:legal-core` | `MISSING_SCRIPT` |
| `npm run test:knowledge-safety` | `MISSING_SCRIPT` |
| `npm run test:knowledge-integrity` | `MISSING_SCRIPT` |
| `npm run test:ecosystem-kernel` | `MISSING_SCRIPT` |
| `npm run test:agent-contribution` | `MISSING_SCRIPT` |
| `npm run build:public` | `MISSING_SCRIPT` |
| `src/schemas/content-factory.test.ts` | `MISSING_FILE` — `src/` contiene `Root.tsx`, `compositions/`, `content.ts`, `index.ts`, `types.ts` |

Scripts reales de este `package.json`: `typecheck`, `studio`, `render:example`, `render:all`.

### Suite real ejecutada

| Suite | Antes | Ahora | Resultado |
|---|---:|---:|---|
| `visual/` | 294 | 294 | `OK` |
| Skill de verificación jurídica | 245 | **268** | `OK` (+23 nuevas) |
| `scripts/` | 30 | 30 | `OK` |
| `contract/` | 17 | 17 | `OK` |
| `ecosystem/` | 54 | 54 | `OK` |
| **Total** | **640** | **663** | `OK` |

`git diff --check`: limpio. Canon del piloto intacto. Resolver sin cambios.

## 8. Decisiones que siguen requiriendo al fundador

1. **Verificar los cuatro hostnames** del registro — hoy descansan en una orden, no en comprobación.
2. **Registrar `curia.europa.eu`** — sin él, `LM-HIS-005` no puede alcanzar Nivel 1 aunque se lea el texto.
3. **Las cuatro piezas monopaís** — ¿ampliar a tres jurisdicciones o reclasificar a Capa C con México en el título?
4. **Privacidad histórica** — elegir opción de remediación; la reescritura exige autorización explícita.
5. **`LM-ACT-004`** — `platform_review.required: true` sin ejecutar.
6. **`npm ci`** — para que `typecheck` deje de fallar por dependencias ausentes.

## 9. Siguiente acción única

**Conseguir lectura de las fuentes oficiales** —levantar `EGRESS_BLOCKED` o depositar los textos en
Drive— empezando por los tres artículos de `LM-EVG-001` (CCF 791, CC 432, CCyCN 1910): es la única
pieza del lote con tres países, tres fuentes registradas y cobertura estructural completa, y por
tanto la primera capaz de subir de estado.

Sin ella, los 13 claims siguen en `REQUIERE_INVESTIGACION` y los 10 gates cerrados.
