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

## Contenido real — matriz de gates (2026-08-31, tras ProductionHandoff real)

| CONTENT_ID | Canon | Territory | Art Gate | Handoff | Visual |
|---|---|---|---|---|---|
| `LM-PIEZA-01-REALES` | APTO_PARA_NARRATIVA | CAPA_B_VARIABLE (MX·ES·AR) | **ABIERTO** | **VALID** | **READY_FOR_VISUAL** |
| *(sin minar)* `PIEZA-02-LABORAL` | REQUIERE_INVESTIGACION | — | CERRADO | NONE | BLOCKED |
| *(sin minar)* `PIEZA-03-HONOR` | REQUIERE_INVESTIGACION | — | CERRADO | NONE | BLOCKED |
| `LM-EJEMPLO-TECNICO-001` | — | NO_APLICA | — | — | material de prueba, no publicable |

**PIEZA-01-REALES tiene ahora `ProductionHandoff` real** (`HO-PIEZA-01-REALES-001`,
en `publication/records/handoff-pieza-01-reales.json`) y un `CONTENT_ID` real
minado (`LM-PIEZA-01-REALES`, en `content/pieza-01-reales.json`, modo `GOBERNADO`).
Verificado con `python3 cli.py gates` y `python3 cli.py resolve LM-PIEZA-01-REALES`
→ `produccion: AUTORIZADA`.

## Prueba de producción real ejecutada — pipeline formal, sin bypass

Con el gate abierto y el handoff emitido, se ejecutó el **orquestador oficial**
(`pipeline.generate_visual`, sin llamadas directas al compositor) sobre el
contenido real de PIEZA-01:

1. `visual resolve LM-PIEZA-01-REALES` → `produccion: AUTORIZADA`.
2. `visual dry-run` → `DRY_RUN` (READY), **0 llamadas al proveedor**.
3. `visual simulate` → `PENDIENTE_REVISION_HUMANA`, `GenerationReceipt` real,
   `AssetRegistry` real (raw + composed en disco). Marca "LegalMente" compuesta
   en superficie reservada real. Copy exacto verbatim, autor correcto, sin
   watermark, sin recorte. Verificado visualmente.
4. **Regenerado una vez** (`TOO_DARK`): GEN2 con `parent_generation_id` = GEN1,
   GEN1 preservado sin cambios, mismo `ProductionHandoff` reutilizado (no se
   emite uno nuevo por reintento).
5. **Identidad consistente** entre `ProductionHandoff.content_id`,
   `content/*.json.procedencia.content_id` y `GenerationReceipt.content_id`:
   los tres coinciden. El hash aprobado coincide en los tres lugares.
6. **Canon inmutable**: el claim packet y el handoff no cambiaron (`git status`
   limpio) durante toda la generación.
7. **Bloqueo de control reconfirmado**: `PIEZA-02-LABORAL` (real, sin handoff)
   sigue en `GATE_CERRADO`, 0 llamadas, 0 bytes.

### Segundo hallazgo de red-team real, corregido

Una aprobación humana **congelada** (`revision_humana.contenido_hash_sha256`)
no protegía por sí sola contra un claim **mutado después de aprobado**: el gate
solo comparaba dos snapshots estáticos entre sí, nunca contra el contenido
actual. Corregido: `gates.py` recalcula ahora el hash real y vigente del claim
con la misma función canónica que usa el validador
(`compute_content_hash`), cerrando exactamente el hueco que
`scripts/validate-content-provenance.py` ya cerraba a nivel de artefacto, pero
que faltaba a nivel de gate para llamadores que no pasan por ese script. 1
prueba de regresión adicional.

## Qué significa `publicable: true` en `content/pieza-01-reales.json`

El validador exige ese valor para todo artefacto en modo `GOBERNADO` — es una
etiqueta de categoría ("esto es contenido de producción real", no material de
prueba), **no una autorización de publicar**. Publicar exige una
`PublicationDecision` humana separada, con decisor identificado, que **no
existe**. `content/pieza-01-reales.json` lo declara explícitamente en
`procedencia.nota`.

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
