# LegalMente-web — Integration Pack

Para el siguiente agente o sesión que trabaje en `legallmente-alt/legalmente-web`.
No hace falta redescubrir nada de lo que hay aquí.

## 1. Acceso — hecho verificado esta sesión (2026-08-31)

`legallmente-alt/legalmente-web` **es público y clonable de forma anónima**.

```bash
git ls-remote https://github.com/legallmente-alt/legalmente-web.git HEAD
# 23a9ce0209579a9b85c049b628e2a2c86fb0c5d7   HEAD
git clone https://github.com/legallmente-alt/legalmente-web.git
```

- **Lectura: DISPONIBLE.** Se clonó y analizó en esta sesión.
- **Escritura: `BLOCKED_BY_WORKSPACE_ACCESS`.** No hay `gh` CLI, y el servidor MCP
  de GitHub está limitado a `contratoslegales848-design/psyche-creation`. No se
  puede hacer push, abrir PR ni cerrar PR en ese repositorio desde aquí.

Esto **corrige** el diagnóstico de la sesión anterior ("inaccesible") y **confirma**
la deriva de `CLAUDE.md §8`, que declara ese repositorio privado.

## 2. Estado real de los PRs (no los hashes del mandato — GitHub gobierna)

| PR | HEAD observado | ¿en `main`? | Lectura |
|---|---|---|---|
| `main` | `23a9ce0` | — | Muy por delante del `47ea0a2` del mandato |
| #25 | `48d846f` | NO | **Ya contiene el hardening de #28** |
| #26 | `5b80963` | NO | Superseded, como se sabía |
| #27 | `ae2cd8f` | NO | Movido desde `52a47d9` |
| #28 | `99d728e` | NO | **Redundante: contenido íntegro en #25** |
| #29, #30, #31 | — | SÍ | Fusionados (ecosystem kernel, agent contribution contract) |

### El hallazgo que decide la Fase A

El commit más reciente de #25 es literalmente:

```
48d846f  merge: fold PR #28 no-leak hardening into PR #25
```

Verificado con `git merge-base --is-ancestor`: **#28 no contiene ningún commit
que #25 no tenga**, y `git rev-list --count pr28..pr25` = 1 (justo ese merge).

Es decir: **la OPCIÓN B (fold) del mandato anterior ya fue ejecutada** por otra
sesión. La estrategia de integración no está pendiente de decidirse — está
pendiente de *reconocerse*:

- **#28 → cerrar como SUPERSEDED BY #25.** No fusionar: sería un no-op ruidoso.
- **#26 → cerrar como SUPERSEDED.** Ya estaba claro.
- **#25 → sigue siendo el PR grande.** La cirugía de descomposición (§8 del
  mandato anterior) sigue pendiente y ahora es la única pieza real de Fase A/B.

Cerrar PRs requiere permisos de escritura que esta sesión no tiene.

## 3. Contrato cross-repo — lado Psyche, LISTO

Está implementado y probado en este repositorio:

```
contract/canonical_envelope.py        Canonical Envelope v1 (productor + validador)
contract/fixtures/*.json              8 fixtures versionadas
contract/test_canonical_envelope.py   12 contract tests
```

```bash
cd contract && python3 -m unittest test_canonical_envelope -v
```

### Fixtures que el consumidor debe pasar

| Fixture | El consumidor debe |
|---|---|
| `valid_ready` | aceptar y mostrar |
| `blocked_claim` | mostrar bloqueado; jamás elegible para arte |
| `source_pending` | no habilitar arte |
| `unsupported_territory` | mantener el territorio como no cubierto |
| `missing_provenance` | **rechazar** (no inferir procedencia válida) |
| `unknown_version` | **rechazar** (fail-closed) |
| `unknown_state` | **rechazar** |
| `authority_escalation_attempt` | **rechazar** (claim bloqueado + gate abierto) |

Además: un campo opcional nuevo **no** debe romper al consumidor
(compatibilidad hacia adelante, probada).

### Fronteras de autoridad

```
WEB PUEDE:      display · adapt_presentation · filter_safely · prepare_ux
WEB NO PUEDE:   approve_claim · recompute_sources · upgrade_jurisdiction
                open_legal_gate · change_canonical_hash
                infer_missing_provenance_as_valid
```

Estas dos listas están en el código (`WEB_MAY`, `WEB_MUST_NOT`), no solo en prosa.

## 4. Lo que web debe implementar

1. Un **adapter estricto** que consuma el envelope y falle cerrado ante versión o
   estado desconocidos. `validate_envelope()` es la referencia portable: cada
   regla que contiene es un test que el consumidor debe pasar.
2. **Copiar `contract/fixtures/` a web** y ejecutar los mismos casos desde el lado
   consumidor. Sin acoplamiento en tiempo de ejecución: se copian ficheros, los
   repos no se clonan mutuamente.
3. **PR #27 (Operations Engine) como consumidor, no como canon**: debe leer el
   envelope en vez de recalcular estado jurídico. Clasificar cada dato mostrado
   como `CANONICAL | DERIVED | SNAPSHOT | EXPERIMENTAL | UNKNOWN | NO_MEDIDO`, y
   nunca presentar un snapshot como dato en vivo.

## 5. Comandos exactos de validación

```bash
# Lado Psyche (este repo)
cd contract && python3 -m unittest test_canonical_envelope -v
cd visual   && python3 -m unittest test_visual_pipeline test_visual_advanced -v

# Recuperar el estado real de web
git clone https://github.com/legallmente-alt/legalmente-web.git
cd legalmente-web
git ls-remote origin 'refs/pull/*/head'
git fetch origin refs/pull/25/head:pr25 refs/pull/28/head:pr28
git rev-list --count pr28..pr25     # 1 = #28 está contenido en #25
```
