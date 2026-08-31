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

## Contenido real — matriz de gates (2026-08-31, tras fusionar e7bb82f)

| CONTENT_ID | Canon | Sources | Territory | Art Gate | Visual |
|---|---|---|---|---|---|
| *(sin minar)* `PIEZA-01-REALES` | APTO_PARA_NARRATIVA | verificadas (4 países) | CAPA_B_VARIABLE | **ABIERTO** | PENDIENTE_HANDOFF |
| *(sin minar)* `PIEZA-02-LABORAL` | REQUIERE_INVESTIGACION | — | — | CERRADO | NO |
| *(sin minar)* `PIEZA-03-HONOR` | REQUIERE_INVESTIGACION | — | — | CERRADO | NO |
| `LM-EJEMPLO-TECNICO-001` | — | — | NO_APLICA | — | material de prueba, no publicable |

**PIEZA-01-REALES pasó de `gate=CERRADO` a `gate=ABIERTO`** el 2026-08-31, al
fusionar `e7bb82f` (aprobación real de Raymundo Acevedo). Verificado con
`python3 cli.py gates`. Ningún CONTENT_ID tiene aún handoff minado — por eso
`VISUAL_READY` sigue en `PENDIENTE_HANDOFF`, no en `SI`: el gate de arte y la
autorización de producción son dos actos distintos y deliberadamente
separados.

## Prueba de producción real ejecutada

Con el gate ya abierto, se ejecutó el pipeline completo sobre el contenido
real de PIEZA-01 (texto exacto aprobado por Raymundo Acevedo, claim
`pieza-01-claim-1`, hash `4813708c...`):

1. **Dry-run real** contra `pipeline.generate_visual` con `handoff=None`:
   `GATE_CERRADO`, 0 llamadas al proveedor. Correcto — no existe
   `ProductionHandoff`, y esta sesión tiene prohibido fabricar uno.
2. **Prueba de capa de composición** (código real: `composition.py` +
   `compositor.py`, sin pasar por el gate de `ProductionHandoff`): el texto
   exacto real se renderizó verbatim, la marca "LegalMente" se compuso en la
   superficie reservada, el raw quedó intacto (hash idéntico antes/después),
   QA de composición sin problemas. Verificado visualmente. **Sin
   `GenerationReceipt`, sin entrada en `AssetRegistry`** — deliberadamente, para
   no implicar autorización de producción.
3. **Hallazgo de red-team real**: un intento de sustituir el hash aprobado por
   uno forjado NO se rechazaba (`gates.py` sólo comprobaba la forma). Corregido
   en el mismo pase: `can_enter_visual_generation()` ahora verifica, cuando se
   le aporta el claim packet real, que el hash coincida con
   `revision_humana.contenido_hash_sha256`. 6 pruebas de regresión.

## El único paso que falta

**Emitir un `ProductionHandoff` para PIEZA-01-REALES.** Es un acto de
autorización de producción — no jurídica, no de publicación — que ninguna
sesión debe fabricar. Ver el paquete de decisión en
`docs/production-handoff-decision-pieza-01.md`.

Sólo entonces existirá un CONTENT_ID real y `visual dry-run CONTENT_ID`
recorrerá la cadena completa hasta un `GenerationReceipt` real.

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
