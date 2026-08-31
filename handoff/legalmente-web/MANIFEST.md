# Patch manifest — legalmente-web

Trabajo implementado y probado localmente en esta sesión. No se pudo empujar:
la escritura remota sobre `legallmente-alt/legalmente-web` está bloqueada
(`BLOCKED_BY_REMOTE_WRITE`). Todo lo demás está hecho.

## Datos del paquete

| Campo | Valor |
|---|---|
| Repositorio destino | `legallmente-alt/legalmente-web` |
| Commit base | `23a9ce0209579a9b85c049b628e2a2c86fb0c5d7` (`main`) |
| Rama local | `local/psyche-contract-consumer-v1` |
| Commits | 2 |
| Patches | `0001-feat-contract-*.patch`, `0002-test-public-*.patch` |
| Bundle | `legalmente-web-integration.bundle` |
| Conflictos conocidos | ninguno contra `23a9ce0` |

## Commits

1. **`feat(contract)`** — `src/lib/psyche-contract/` (adapter estricto + mapeo con
   procedencia + snapshot de 8 fixtures + 18 contract tests) y el script
   `test:psyche-contract` en `package.json`.
2. **`test(public)`** — endurece `scripts/public-route-proof.mjs` con dos guardas
   nuevas: fuga por serialización (contenido, no solo nombre de archivo) y
   enlaces públicos a rutas `/internal`.

## Cómo aplicarlo

```bash
git clone https://github.com/legallmente-alt/legalmente-web.git
cd legalmente-web
git checkout -b feat/psyche-contract-consumer-v1
git am /ruta/a/handoff/legalmente-web/*.patch
```

o con el bundle:

```bash
git fetch /ruta/a/legalmente-web-integration.bundle
```

## Cómo verificarlo

```bash
npm ci
npm run typecheck && npm run lint
npm run test:legal-core && npm run test:knowledge-safety
npm run test:knowledge-integrity && npm run test:ecosystem-kernel
npm run test:agent-contribution && npm run test:psyche-contract
npm run build:public && npm run test:public-routes
```

## Resultado observado

Verificado **en un clon limpio distinto del directorio de trabajo**
(`/tmp/verify`), tras aplicar los patches con `git am`:

| Comprobación | Baseline (23a9ce0) | Tras los patches |
|---|---|---|
| `typecheck` | OK | OK |
| `lint` | OK | OK |
| `test:legal-core` | OK | OK |
| `test:knowledge-safety` | OK | OK |
| `test:knowledge-integrity` | OK | OK |
| `test:ecosystem-kernel` | OK | OK |
| `test:agent-contribution` | OK | OK |
| `test:psyche-contract` | no existía | OK (18) |
| `build` / `build:public` | OK | OK |
| `test:public-routes` | OK | OK (con 2 guardas nuevas) |

Ningún fallo preexistente y ningún fallo introducido.

**Nota sobre el baseline:** `npm run test:public-routes` falla en un árbol recién
clonado con *"Public artifact missing: run build:public first."*. No es un fallo
del repositorio: es una precondición del script. Hay que ejecutar `build:public`
antes.

## Lo que este paquete NO hace

- No abre PR, no fusiona, no despliega.
- No toca el Operations Engine de PR #27: esa rama diverge de `main` en 114
  archivos y es experimental. El adapter se construyó sobre `main`, que es donde
  todo acaba integrándose, para que el patch aplique donde importa.
- No añade UI. El adapter es una biblioteca; conectarlo a pantallas es otra
  unidad de trabajo.
