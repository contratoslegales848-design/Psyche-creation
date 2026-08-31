# Real Generation Readiness

Estado verificado el 2026-08-31. Ejecutado, no estimado.

## Scorecard

| Capacidad | Estado |
|---|---|
| Resolución canónica (`CONTENT_ID` → input) | READY |
| Gate de arte fail-closed | READY |
| VisualBrief / VisualPolicy / VisualFamily | READY |
| VisualMemory + anti-repetición | READY |
| Prompt Compiler V2 + explicabilidad | READY |
| GenerationPlan + dry-run | READY |
| Adapter de proveedor (`HttpImageProvider`) | READY (código); **BLOCKED_BY_CREDENTIALS** para ejecución |
| Credenciales de proveedor en vivo | BLOCKED_BY_CREDENTIALS |
| Arte en bruto | SIMULATED (`FakeImageProvider`) |
| Tipografía determinista | READY |
| Marca determinista | READY (superficie plana declarada); revisión humana en superficie compleja |
| QA estructural | READY |
| QA semántica | CONTRACT_ONLY + heurísticas de píxel |
| GenerationReceipt / AssetRegistry | READY |
| Lotes / reintento selectivo / regeneración | READY |
| Human review packet | READY |
| `visual explain GENERATION_ID` | READY |
| Consumidor de `legalmente-web` | PATCH_READY (**BLOCKED_BY_REMOTE_WRITE**) |
| Publicación | OUT_OF_SCOPE (prohibida por diseño) |

## Contenido real: ninguna pieza es elegible hoy

Esto es un hallazgo de producto, no un fallo técnico. El pipeline **bloquea
correctamente** y lo demuestra.

| PIECE_ID | Canon | Gate de arte | Visual |
|---|---|---|---|
| `PIEZA-01-REALES` | APTO_PARA_NARRATIVA | **CERRADO** | NO |
| `PIEZA-02-LABORAL` | REQUIERE_INVESTIGACION | CERRADO | NO |
| `PIEZA-03-HONOR` | REQUIERE_INVESTIGACION | CERRADO | NO |

Artefactos en `content/`: **uno**, `LM-EJEMPLO-TECNICO-001`, en modo
`EJEMPLO_TECNICO` y `publicable: false`. `ProductionHandoff` reales: **ninguno**.

## El candidato más cercano y qué lo bloquea exactamente

`PIEZA-01-REALES` **ya tiene aprobación humana real**, firmada por Raymundo
Acevedo, con `gate_arte: ABIERTO` en los tres claims. Vive en la rama
**`claude/legalmente-pieza-01-aprobacion-humana-final-v1` (`e7bb82f`), sin fusionar.**

El mensaje de ese commit dice que quedó *"BLOQUEADO por tests stale"*. **Esos
tests ya se corrigieron** y están en `main` (ver `TECHNICAL_STATE.md` §5.3).

Verificado ahora contra el validador canónico de `main`:

```
$ python3 scripts/validate-claim-packet.py pieza-01-aprobada.json
[GATE ABIERTO] estado_agregado=APTO_PARA_NARRATIVA
exit 0
```

**El validador vigente acepta el paquete aprobado y abre el gate.** El bloqueo
original ya no existe.

### Los tres pasos que faltan, en orden

1. **Fusionar `e7bb82f`.** Decisión humana. Sin ella, en `main` el gate sigue
   cerrado y toda la cadena posterior está correctamente bloqueada.
2. **Emitir un `ProductionHandoff`** para `PIEZA-01-REALES`. No existe ninguno.
   Es un acto de autorización de producción; ninguna sesión debe fabricarlo.
3. **Crear el artefacto `content/*.json`** con `procedencia.modo = GOBERNADO`,
   `piece_id`, `handoff_id` y los `approved_claim_hash` de los claims aprobados.

Sólo entonces `visual dry-run LM-PIEZA-01-...` recorrerá la cadena completa.

## Comandos

```bash
cd visual
python3 cli.py content                  # CONTENT_ID reales declarados
python3 cli.py gates                    # estado canónico por pieza
python3 cli.py resolve  CONTENT_ID      # resuelve y dice qué bloquea
python3 cli.py dry-run  artefacto.json  # plan sin llamar al proveedor
python3 cli.py simulate artefacto.json  # genera y compone con FakeProvider
python3 cli.py explain  DIR CONTENT_ID GENERATION_ID
python3 cli.py show-history DIR CONTENT_ID
```

Modo seguro por defecto: el único proveedor registrado es el falso. Ejecutar
contra un proveedor de pago exigirá intención explícita (`--live`), que **no
está implementada** a propósito.
