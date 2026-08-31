# Prompt de arranque — sesión con `legallmente-alt/legalmente-web` como source inicial

Copia esto como instrucción inicial de la nueva sesión. No hace falta
redescubrir nada: todo lo de abajo está verificado.

---

Este workspace tiene `legallmente-alt/legalmente-web` como fuente. Otra sesión
(sin permiso de escritura sobre ese repo) preparó una serie de 3 patches ya
verificados con `git am` en un clon limpio. Tu trabajo es aplicarlos y abrir un
PR **draft**, nada más.

## Datos exactos

| Campo | Valor |
|---|---|
| Base | `23a9ce0209579a9b85c049b628e2a2c86fb0c5d7` (`main`, reverificado sin cambios el 2026-08-31, dos veces) |
| Patches | 3, en este mismo directorio |
| sha256 `0001` | `3cc324f4e60fc0a2b939df7f304592b42304d9854c255a42dcb1ed82f3aa7020` |
| sha256 `0002` | `26d54fdff4ac25f2167efcc04bced69044fd0fd9947f2ae5bfa448ce7d0ae15c` |
| sha256 `0003` | `21785ad5f6f92ee723e7b12922a75ea3fb665de69fc16b027d91dc197db5c702` |

## Pasos exactos

```bash
git fetch origin main
git checkout -b feat/psyche-contract-consumer-v1 origin/main
git am 0001-*.patch 0002-*.patch 0003-*.patch
npm ci
```

## Pruebas esperadas (todas deben pasar; ninguna es nueva por ti)

```bash
npm run typecheck && npm run lint
npm run test:legal-core && npm run test:knowledge-safety
npm run test:knowledge-integrity && npm run test:ecosystem-kernel
npm run test:agent-contribution && npm run test:psyche-contract   # 23 tests
npm run build:public && npm run test:public-routes
```

`test:public-routes` **exige haber corrido `build:public` antes** — no es un
fallo si falla sin eso, es la precondición del script.

## Qué traen los 3 patches (no lo reinvestigues)

1. **`src/lib/psyche-contract/`** — consumidor estricto del Canonical Envelope
   de Psyche. `deriveVisualOutputState()` deriva SOLO desde el canon: la web no
   puede declarar `READY_FOR_VISUAL` ni pasando un `outputState` falso. Incluye
   `source_system`/`source_revision`/`provenance_digest` para trazabilidad
   cross-repo (con dos diferencias deliberadas y probadas frente al análogo en
   PR #27: el estado canónico no es opaco, y la tolerancia a campos v1 futuros
   es una política declarada).
2. **`scripts/public-route-proof.mjs`** — dos guardas nuevas: fuga por
   **contenido serializado** (no solo nombre de archivo) y **enlaces** públicos
   a `/internal` (el recorrido anterior los saltaba). Ambas verificadas
   plantando la fuga: deben seguir fallando si alguien las rompe.

## Fronteras que no se tocan

```
WEB PUEDE:      display · adapt_presentation · filter_safely · prepare_ux
WEB NO PUEDE:   approve_claim · recompute_sources · upgrade_jurisdiction
                open_legal_gate · change_canonical_hash
                infer_missing_provenance_as_valid
```

## Al terminar

1. `git push -u origin feat/psyche-contract-consumer-v1`
2. Abrir PR **draft** contra `main`, título:
   `feat(contract): consumidor estricto del Canonical Envelope de Psyche`
3. **NO merge.**
4. Reportar: HEAD, número de PR, resultado exacto de cada comando de arriba.

## Contexto sobre PR #25 / #26 / #27 / #28 (no rehacer el análisis)

`#25` es el sucesor activo (contiene el fold de `#28`). `#26` y `#28` son
`SUPERSEDED` — técnicamente listos para cerrarse, requiere permiso que esa
sesión tampoco tenía. `#27` diverge de `main` en 114 archivos y su única
capacidad única y útil (metadatos de transporte) ya está portada en estos
patches. No reabras ese análisis.


## Nota — PIEZA-01 ya tiene ProductionHandoff real (no cambia este contrato)

Del lado de Psyche: `PIEZA-01-REALES` ya tiene un `ProductionHandoff` real emitido y un `CONTENT_ID` real (`LM-PIEZA-01-REALES`), con un `GenerationReceipt` de prueba producido por el pipeline formal. **El esquema del Canonical Envelope no cambió** — `contract/canonical_envelope.py` y las 8 fixtures siguen siendo las mismas que consumen estos 3 patches. No hace falta regenerar nada por este motivo.
