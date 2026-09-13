# Arquitectura real de LegalMente — auditoría y reconciliación 2026-09-13

**Base:** rama `claude/legalmente-architecture-reconciliation-xojn4i` sobre `main` en `ef7ffdd`.
**Fuente nueva obligatoria:** `LegalMente — Handoff Founder 2026-09-13`.
**Autoridades leídas:** `00 LEER PRIMERO` (7-sep), `Índice maestro v18`, `Capa canónica de
diversidad editorial y universo temático v1`, `Arquitectura del Corazón y Sistema Vivo V1`,
`Guía operativa del motor de dirección artística`, `Bitácora de cambios (ciclo 2026-09)`.

Regla de lectura (`CLAUDE.md §2`): **una mención en Drive no es una capacidad implementada.**
Todo lo marcado IMPLEMENTADO aquí tiene archivo real y prueba que pasa.

---

## 1. Clasificación de componentes

### CANÓNICO + IMPLEMENTADO (evidencia ejecutable)

| Componente | Archivo | Pruebas |
|---|---|---|
| Verificación jurídica (claim packets v4) | `.claude/skills/legalmente-legal-verification/` | 245 |
| Contrato canónico cross-repo | `contract/canonical_envelope.py` | 17 |
| Procedencia de contenido | `scripts/validate-content-provenance.py` | 34 |
| Pipeline visual (brief→plan→compilador→proveedor→QA→receipt) | `visual/{brief,plan,compiler,pipeline,qa,gates,receipts,registry}.py` | incluidas en las 521 |
| Composición tipográfica real | `visual/compositor.py` | " |
| Motor de rutas conceptuales | `visual/route_engine.py`, `route_sync.py` | " |
| Memoria **visual** anti-repetición | `visual/memory.py` | " |
| Rotación y diversidad visual de lote | `visual/rotation.py` | " |
| Inventario de estado y bandeja humana | `visual/inventory.py`, `command_center.py` | " |
| Feedback humano → mutación de brief | `visual/feedback.py` | " |

### IMPLEMENTADO EN ESTA SESIÓN (hueco P0/P1 cerrado)

| Componente | Archivo | Pruebas |
|---|---|---|
| Huella semántica de 22 campos | `visual/semantic_fingerprint.py` | 22 |
| Universo editorial abierto (58 familias) | `visual/editorial.py` + `policy/editorial-universe-v1.json` | 31 (con universo) |
| Reserva combinatoria y selección jerárquica | `visual/universe.py` + `policy/materias-seed-v1.json` | " |
| Motor emocional estructural | `visual/emotion.py` | 22 |
| Memoria semántica con estados y aprendizaje | `visual/semantic_memory.py` | 23 |
| QA de lote como sistema + telemetría | `visual/batch_qa.py` | 21 |
| Carriles LinkedIn | `visual/lanes.py` | 19 |
| Ciclo vertical del organismo | `visual/organism.py` | 28 |

### PILOTO / PROPUESTA
- Piezas 01–03 del piloto: `pieza-01-reales` en `APTO_PARA_NARRATIVA` con gate CERRADO;
  02 y 03 en `REQUIERE_INVESTIGACION`. La aprobación humana de la pieza 01 vive en una rama
  **sin fusionar** — decisión humana pendiente, no paso técnico.
- `docs/contrato-motor-masivo.md`: contrato definido, motor deliberadamente no construido.

### AUXILIAR
- `scripts/check-unittest-main-guard-position.py` (higiene), `visual/observability.py`,
  `visual/runtime_config.py`, `visual/inspection.py`.

### LEGACY / SUPERADO
- Índices maestros v8–v17 en Drive (`00 — Archivo`, marcados SUPERADO). No borrados.
- Bancos finitos de prompts (300→174): **semilla**, nunca universo temático.

### HUÉRFANO (existe, no está conectado)
- `visual/registry.py` (AssetRegistry) vive en directorios efímeros y no sobrevive entre
  sesiones; `inventory.py` deliberadamente **no** lo lee para no mentir.
- `handoff/legalmente-web/`: serie de patches verificada localmente, **sin empujar**
  (cuentas distintas, `CLAUDE.md §8`).
- Métricas de rendimiento: 0 entradas del historial tienen métricas reales. Toda ponderación
  por rendimiento sigue siendo decorativa. **Es el cuello de botella del aprendizaje.**

---

## 2. Contradicciones encontradas

1. **`familias` significaba dos cosas.** `visual/families.py` registra familias VISUALES
   (óleo, claroscuro); la `Capa canónica de diversidad` exige familias EDITORIALES (mito,
   checklist, etimología). Eran ejes ortogonales con el mismo nombre. **Ésta es la raíz
   del defecto que reporta el fundador**: diez estilos distintos sobre diez definiciones
   siguen siendo diez definiciones. Resuelto separando `editorial.py` de `families.py`.

2. **La memoria no podía detectar repetición semántica.** `memory.py` puntúa escena,
   sujeto, cámara, metáfora y objeto. Cambiar el estilo artístico bastaba para pasar su
   control con el mismo contenido. Resuelto en `semantic_fingerprint.py`, donde hook,
   formato y emoción **no participan** en la distancia semántica.

3. **CI nombraba 5 de 17 suites visuales.** Memoria, rotación, motor de rutas e inventario
   nunca se ejecutaban en CI. Resuelto con `unittest discover`.

4. **Pillow no estaba instalado en el entorno**, lo que hacía fallar 11 pruebas del
   compositor. No era un fallo de código: `pip install -r requirements.txt` lo resuelve.

5. **`CLAUDE.md §8` declaraba `legalmente-web` privado**; el propio archivo ya registra la
   corrección (verificado público el 2026-08-31). Sin acción pendiente.

---

## 3. El ciclo, ejecutable

```
NECESIDAD → CANDIDATO → HUELLA SEMÁNTICA → RESERVA AMPLIA → DIVERSIDAD
→ PERFIL EMOCIONAL → QA DE LOTE → CURATION_READY
→ CURADURÍA DEL FOUNDER → MEMORIA → APRENDIZAJE → NUEVA GENERACIÓN
```

Demostración: `cd visual && python3 demo_ciclo.py`.

**Producción continua (Handoff §5):** `organism.producir_lote()` no recibe ni consulta
ninguna aprobación previa. Su estado terminal es `CURATION_READY` y el ciclo completo no
puede dejar ninguna huella en `APROBADA` ni `PUBLICADA` — probado en
`test_organism_cycle.py`. Publicación, merge y deploy siguen siendo gates separados.

---

## 4. Lo que sigue SIN estar conectado (no declarar integrado)

| Subsistema | Estado real |
|---|---|
| Proveedor de imagen real | Adapter HTTP probado con transporte inyectable; **cero llamadas externas ejecutadas**. Sin créditos. |
| Video (Remotion) | Renderiza y exige procedencia, pero **no consume** `TopicCandidate` ni el perfil emocional. |
| Web (`legalmente-web`) | Consumidor del Canonical Envelope probado localmente; **no se puede empujar** desde este repo. |
| Aplicación | No existe. |
| Señales/dudas externas | No existe captura. El motor genera candidatos combinatorios, no escucha al público todavía. |
| Reacciones / analytics | No existe ingesta. `selection_rate` es hoy la única señal real disponible. |
| Instagram | Bloqueado por autorización pendiente. |

---

## 5. Riesgos

1. **`selection_rate` es la única señal de aprendizaje real.** Sin métricas de rendimiento,
   el sistema aprende sólo del gusto declarado del fundador. Es mejor que nada y es
   exactamente lo que pidió el Handoff, pero no sustituye a datos de audiencia.
2. **Los umbrales están calibrados contra pares sintéticos**, no contra el corpus histórico
   de 174 guiones. Conviene recalibrar `UMBRAL_EQUIVALENCIA` cuando ese corpus esté
   disponible como huellas.
3. **`register_familia` no detecta duplicidad semántica.** El canon exige que una familia
   nueva no duplique otra; esa valoración se deja explícitamente a un humano en vez de
   fingir un juicio automático.
4. **Confidencialidad**: sigue sin control automatizado de contenido identificable sin
   marcadores léxicos (hueco conocido, red team B5). Este trabajo no lo toca.
5. El motor combinatorio puede producir combinaciones jurídicamente vacías; por eso todo
   candidato nace `NO_VERIFICADO` y la verificación jurídica sigue siendo obligatoria.
