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

## READY_FOR_WEB_SESSION — contrato nuevo del Command Center (v1.0, no integrado todavía)

**Estado explícito: no está integrado.** Es una especificación de consumer delta lista para aplicarse — no un cuarto patch generado contra el repo real de `legalmente-web` (esta sesión no tiene ese repo clonado ni permiso de escritura sobre él).

Productor: `visual/command_center.py` (Psyche). Contrato:

- `command_center_contract_version: "1.0"` (`command_center.CONTRACT_VERSION`).
- Envelope con: `content` (una fila por `content_id` real), `human_decision_inbox`, `automatic_executable_now`, `data_freshness` a nivel de payload y por fila.
- Vocabulario cerrado de `data_freshness`: `LIVE / DERIVED / SNAPSHOT / SIMULATED / UNKNOWN`. Ningún consumidor debe tratar `SIMULATED` ni `SNAPSHOT` como `LIVE`.
- Vocabulario cerrado de `human_art_review`: `PENDIENTE / SIN_GENERACION / APPROVE_VISUAL / REJECT_VISUAL / NOT_ACTIONABLE_UNTIL_REAL_PROVIDER / NOT_AVAILABLE / DESCONOCIDO`. `NOT_ACTIONABLE_UNTIL_REAL_PROVIDER` significa exactamente eso: el proveedor es `FakeImageProvider` (simulado) y no hay arte real que un humano pueda juzgar todavía. Un consumidor NUNCA debe presentar esto como "listo para revisar".
- Separación explícita e irrenunciable en cada fila: `art_gate` (juicio jurídico) ≠ `human_art_review` (juicio visual) ≠ `publication_decision`/`publication_state` (autorización de publicar). `publicable: true` en el canon de Psyche es una etiqueta de categoría, nunca autorización de publicar.
- Ausencia de dato se representa como `UNKNOWN` / `NOT_AVAILABLE` / `NO_MEDIDO` — nunca como `0`, `false` ni una aprobación implícita.
- **Fail-closed obligatorio**: un consumidor que reciba una `contract_version` que no reconoce debe **rechazar el payload entero**, no leerlo parcialmente. `command_center.validate_envelope()` es la referencia de esa validación del lado productor; portar la misma lógica (o equivalente) al lado consumidor.
- Fixtures de referencia (8, todas verificadas contra `validate_envelope()`): `visual/fixtures/command_center/{valid,unknown_version,unknown_state,simulated_provider,blocked_content,no_metrics,publication_absent,authority_escalation_attempt}.json`.

**Integración requerida cuando exista una sesión con permiso de escritura sobre `legalmente-web`:**
1. Añadir un reader estricto análogo a `src/lib/psyche-contract/index.ts` (mismo patrón fail-closed que ya usa el Canonical Envelope) para el envelope del Command Center.
2. Rechazar cualquier `contract_version` fuera de `{"1.0"}`.
3. Nunca derivar `publication_state` ni `human_art_review` — son campos transportados, no recalculados (mismo principio que `deriveVisualOutputState()` ya aplica al Canonical Envelope).
4. Renderizar `NOT_ACTIONABLE_UNTIL_REAL_PROVIDER` de forma visualmente distinta a `PENDIENTE`: la UI no debe invitar a "aprobar" un placeholder de `FakeImageProvider`.
5. Portar las 8 fixtures como casos de prueba del lado consumidor antes de confiar en datos reales de Psyche.

No se regeneró ningún patch de los 3 existentes: el Canonical Envelope no cambió. Esta sección es aditiva.
