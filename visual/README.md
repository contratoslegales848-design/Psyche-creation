# Motor de generación visual — V1

**Estado: arquitectura completa, probada con proveedor falso. Ningún adapter real implementado.**

La capa que faltaba entre `ProductionHandoff` (fin de la cadena jurídica) y el arte
final. No sustituye a `legalmente-visual-system`: esa skill conserva el criterio
artístico (qué escuela toca, qué metáfora). Aquí vive lo que un programa puede
comprobar y bloquear.

## Principio

LegalMente posee el contenido, las reglas, la intención visual, el prompt compilado,
la memoria, el QA y la decisión humana. Los proveedores (OpenAI, Grok, Gemini,
Higgsfield, Flux, SD, Ideogram) son ejecutores reemplazables detrás de una interfaz.
**El dominio no menciona a ninguno.**

## Flujo real

```
artefacto de content/ + ProductionHandoff
   → canonical.build_visual_input()      vista del canon, no segundo canon
   → gates.can_enter_visual_generation() fail-closed, lee gate_arte
   → brief + policy + family             VisualBrief / VisualPolicy / VisualFamily
   → memory.assess()                     riesgo de repetición determinista
   → compiler.compile_request()          CompiledVisualRequest + explicación
   → GenerationPlan                      serializable y hasheable
   → providers.selection.evaluate()      ACCEPT / ADAPT / REJECT
   → [DRY RUN corta aquí: 0 llamadas]
   → provider.generate()                 FakeImageProvider en CI
   → qa.structural_qa()                  MIME real, dimensiones, duplicados
   → inspection                          NOT_EVALUATED por defecto; nunca finge
   → composition                         TypographyPlan + BrandCompositionPlan
   → receipts.GenerationReceipt          en TODOS los desenlaces
   → registry.AssetRegistry              ficheros, sin base de datos
   → [GATE HUMANO]                       el código se detiene aquí, siempre
```

## Módulos

| Archivo | Responsabilidad |
|---|---|
| `canonical.py` | `VisualInput`: lee el canon, normaliza forma, preserva autoridad |
| `gates.py` | puertas fail-closed; nunca recalculan estado jurídico |
| `brief.py` | `VisualBrief` + `VisualPolicy` versionada |
| `families.py` | registro versionado de familias visuales |
| `memory.py` | memoria visual + `RepetitionAssessment` determinista |
| `compiler.py` | `CompiledVisualRequest` + explicabilidad |
| `plan.py` | `GenerationPlan` + hashes canónicos |
| `providers/` | interfaz, negociación, selección, `FakeImageProvider` |
| `qa.py` | QA estructural |
| `inspection.py` | contrato semántico + heurísticas de píxel honestas |
| `composition.py` | `TypographyPlan`, `BrandCompositionPlan` |
| `feedback.py` | códigos de feedback → cambios controlados de brief |
| `registry.py` | assets, receipts, decisiones humanas, seguridad de rutas |
| `receipts.py` | `GenerationReceipt` v2 + `HumanReviewPacket` |
| `pipeline.py` | orquestador, lotes, reintento selectivo, regeneración |
| `errors.py` / `observability.py` / `cli.py` | taxonomía, eventos, CLI |

## Lo que este módulo NO hace

- **No recalcula estado jurídico.** Lee `gate_arte` y el handoff. Estado ilegible → cierra.
- **No aprueba nada.** El mejor desenlace es `PENDIENTE_REVISION_HUMANA`. Ningún
  status significa aprobado — verificado por prueba y por guardia de CI.
- **No llama a proveedores reales.** Sin credenciales, sin red, sin créditos.
- **No entiende imágenes.** El inspector por defecto devuelve `NOT_EVALUATED`. Las
  heurísticas de píxel (luminancia, contraste, dominancia cálida) son medidas
  reales y escalan a revisión humana; nunca rechazan solas.
- **No rasteriza texto.** No hay Pillow en el repositorio. `TypographyPlan` y
  `BrandCompositionPlan` son contratos que un compositor externo ejecuta.
- **No crea un `ContentUnit` paralelo.** `docs/contrato-motor-masivo.md` §1–§2 ya
  repartió esos campos; duplicarlos habría cambiado el `contenido_hash_sha256`.

## Decisión de marca (ADR 0002, aprobada 2026-08-31)

```
integración física de marca = OBLIGATORIA
el generador escribe "LegalMente" = NO
composición determinista posterior = SÍ
```

Una petición de texto de marca **se convierte** a composición posterior y queda
anotada; nunca llega al proveedor. Ver `docs/adr/0002-marca-composicion-determinista.md`.

## Pruebas

```bash
cd visual && python3 -m unittest test_visual_pipeline test_visual_advanced -v
```

121 pruebas. Gate fail-closed, adapter canónico, familias, memoria/repetición,
compilador, marca (red-team), composición, inspección, negociación, contrato de
proveedor, dry-run, lotes, reintento selectivo, regeneración, idempotencia,
registro, seguridad de rutas, integridad de receipts, escalamiento de autoridad y
observabilidad.

## CLI

```bash
python3 cli.py policy
python3 cli.py families
python3 cli.py validate      content/ejemplo.json
python3 cli.py dry-run       content/ejemplo.json --handoff h.json
python3 cli.py simulate      content/ejemplo.json --handoff h.json --out artifacts/visual
python3 cli.py show-history  artifacts/visual LM-TEST-001
```

## Motor de dirección artística (catálogo maestro, 16-sep-2026)

Mandato "Súper Prompt" (Founder, 16-sep-2026):
`docs/auditoria-monotonia-visual-2026-09-16.md` encontró que la variedad
visual real de este motor estaba forzada a un puñado de valores fijos —
una paleta de 4 colores obligatoria en cada prompt, 8 "familias" visuales
que heredaban todas del mismo pool de color, y una línea de código que
imprimía "azul petróleo" en el 100% de las piezas sin excepción. Esta
sección documenta el sistema que lo reemplaza como fuente REAL de
variedad (no elimina `families.py`/`visual-families-v1.json`: siguen
siendo un campo estructural del brief, pero la dirección artística ya no
depende de ellos).

**Fuente canónica humana** (nunca se edita a mano el derivado):

```
policy/catalogo-maestro-v1.md      767 módulos: 504 direcciones (10 categorías,
                                    sección 3) + 263 auxiliares (7 dimensiones,
                                    sección 4). Documento del Founder, copia
                                    literal.
        ↓  catalog_parser.parse_catalogo() / generar_json()
policy/catalogo-maestro-v1.json    DERIVADO. Se regenera, nunca se edita
                                    directamente. Fail-closed si el parseo da
                                    menos de 100 entradas o alguna sección
                                    queda vacía.
```

**Pipeline de selección** (`visual_fingerprint.py`):

```
seleccionar_huella(content_id, catalogo, memoria, canal)
   → VisualFingerprint: primary_direction, secondary_direction?, medium
     (= la categoría real de la que salió primary_direction — nunca se
     elige aparte), lighting, composition, camera_optics, palette,
     materiality, realism, visual_mechanism
   → selección por frecuencia de uso reciente (no random puro, sin
     afinidad tema→categoría inventada — todas las categorías arrancan
     elegibles por igual, mismo criterio fail-closed que
     territory_explorer.coherencia())
   → si la huella coincide en demasiadas dimensiones con la pieza
     anterior o el historial reciente, se muta y reselecciona (hasta
     MAX_INTENTOS_MUTACION) antes de entregarse
```

**QA de lote** (`visual_fingerprint_batch.py`): `evaluar_lote_visual()`
exige, escalado al tamaño real del lote (base: lote de 10) — mínimo 7
huellas realmente distintas, mínimo 5 medios/familias distintos, tope 2
piezas por medio, cero repeticiones consecutivas en
primary_direction/composition/lighting/palette. `generar_lote_visual()`
regenera el lote completo hasta que pasa el QA — nunca lo rellena con
candidatos débiles.

**Llega al prompt final, no solo al metadata** (`compiler.py`):
`compile_request(..., fingerprint=huella)` usa las 10 dimensiones de la
huella para construir la sección de dirección artística y la paleta del
prompt, reemplazando la paleta de marca fija y la línea incondicional de
acento azul. Sin `fingerprint` (parámetro opcional), el comportamiento es
compatible hacia atrás. Verificado en `test_compiler.py`.

**Cómo extender el catálogo sin tocar lógica:** editar
`policy/catalogo-maestro-v1.md` (añadir líneas `- entrada` bajo la
sección `### N.M Nombre` correspondiente) y correr
`python3 catalog_parser.py` para regenerar el JSON derivado. Ningún
módulo de selección necesita cambiar: `MasterCatalog.load()` lee
cualquier tamaño de catálogo sin límite hardcodeado.

**Demostraciones y prueba de aceptación:**

```bash
cd visual && python3 demo_prueba_aceptacion_10_temas.py   # 10 temas reales -> 10 prompts, sin imágenes
```

Ver `docs/prueba-aceptacion-10-temas-2026-09-16.md` (generado por el
comando de arriba, no escrito a mano) para un ejemplo completo con matriz
de distancia entre las 10 huellas.

## ACTUALIZACIÓN 17-sep-2026 — Mandato Maestro: motor de conocimiento real, memoria fuerte, contrato de generación

Todo lo de abajo se construyó DESPUÉS de la sección "Motor de dirección
artística" de arriba, sobre el mismo catálogo maestro (nunca un motor
paralelo). Este bloque es el punto de entrada real para cualquier sesión
que retome el trabajo — evita reconstruir la historia leyendo `docs/`
entero.

**El candidato temático real** (`universe.TopicCandidate`, no una lista
escrita a mano) nace de `universe.build_reserve()` sobre
`editorial.py`/`policy/editorial-universe-v1.json` (58 familias
editoriales reales, semilla abierta — `register_familia()` la amplía sin
tocar lógica) y pasa por `generator.seleccionar_lote()`: selección
GREEDY iterativa, multi-factor, con 3 hard gates (repetición semántica,
saturación editorial, cuota de materia) y factores blandos acotados que
nunca rescatan un hard gate:

```
seleccionar_lote(reserva, memoria, mapa_territorio, universo, n=10, ...)
   por cada candidato restante:
      hard gates (semantic_memory.evaluar / editorial_saturation / cuota) -> RECHAZO si falla
      score_base = Σ PESOS[factor] · factor   (novedad, diversidad de lote,
                    territorio -- territory_explorer.py --, utilidad,
                    ajuste emocional, cooldown)
      + ajuste_afinidad_founder()      acotado, de memoria de esta corrida
                                        Y de memoria_fuerte real (ver abajo)
      + ajuste_senal_mercado()         acotado, de vacantes reales (market_signal.py)
      + ajuste_balance_pedagogico()    acotado, ver "Motor pedagógico" abajo
   toma el mejor superviviente, repite
```

Todos los ajustes usan el mismo patrón: pequeños, acotados a un máximo
fijo, exactamente 0.0 sin evidencia, nunca excluyen — sólo el score. Ver
`generator.py` (docstring completo de cada uno).

### Motor pedagógico — balance conocimiento/narrativa (`pedagogia.py`)

Mandato Maestro §1-3 (17-sep-2026): el Founder detectó riesgo de sesgo
hacia situaciones humanas/narrativas. Medido primero, no asumido: la
reserva real de candidatos ya es casi uniforme sobre las 58 familias — sin
sesgo narrativo medible — pero SIN intervención el selector greedy converge
a 90-100% conocimiento (narrativa es sólo 5/58 familias:
`caso_cotidiano`, `caso_historico`, `jurista`, `historia_del_derecho`,
`cultura_juridica` — clasificación auditable contra su propia
`funcion_editorial`, ver `pedagogia.FAMILIAS_NARRATIVA`). El riesgo medido
es que narrativa case desaparezca, no que domine.
`pedagogia.ajuste_balance_pedagogico()` empuja el score (acotado, nunca
cuota) hacia un objetivo configurable — 70% conocimiento por defecto,
`objetivo_conocimiento=None` lo desactiva — medido contra el LOTE EN
PROGRESO. Verificado con 5 tandas reales consecutivas: 70-80% conocimiento
sostenido, familias narrativas presentes en las 5, nunca eliminadas.

### Memoria fuerte real — fuente #5 del Contrato v4 (`memoria_fuerte.py`)

Puebla `semantic_memory.SemanticMemory` con datos REALES (no sintéticos)
de "LegalMente — Memoria fuerte: piezas validadas por el Founder y video
real" (Drive): 12 piezas `PUBLICADA` (ranking real de Facebook +
histórico de mayor impacto, métricas verbatim) y 4 `PRESELECCIONADA`
(validaciones explícitas). Define también `REGLAS_RECHAZO_FOUNDER` (7
reglas, sección 4 de esa fuente) — mecanismo SEPARADO de `SemanticMemory`
(los rechazos son reglas negativas de texto, no huellas de piezas; ver el
docstring del módulo para la incompatibilidad detectada y por qué no se
forzó el dato). `memoria_fuerte.cargar_memoria_fuerte()` se carga por
defecto en `production_run.cargar_contexto()` y alimenta:

- **Selección temática** — vía `ajuste_afinidad_founder(..., memoria_fuerte=...)`.
- **Dirección visual** — vía `art_direction.draft_visual_brief(..., memoria_fuerte=...)`,
  que también consulta `SemanticMemory.evaluar_visual_fuerte()` (distancia
  VISUAL contra memoria fuerte, método nuevo y additivo — `evaluar()`
  original mide sólo tema) y los 7 rechazos, ANTES de compilar el prompt
  final (`VisualBriefDraft.bloqueado_memoria_fuerte`/
  `motivos_bloqueo_memoria_fuerte` — el llamador decide, nunca excepción).

### Contrato TEXT_TO_IMAGE vs IMAGE_EDIT (`providers/base.py`, Hotfix 16-sep-2026)

Causa raíz cerrada: `NormalizedImageRequest`/`CompiledVisualRequest` ahora
declaran `generation_mode` (`TEXT_TO_IMAGE`/`IMAGE_EDIT`) explícito, nunca
inferido del lenguaje del prompt. `validate_generation_contract()` bloquea
fail-closed antes de contactar al proveedor si el contrato es
inconsistente. Ver `docs/contrato-generacion-imagenes-legalmente.md`.

### Límite honesto que sigue abierto — orden Contrato v4 §4/§5

El Contrato v4 exige el orden CONCEPTO → TENSIÓN → METÁFORA → FAMILIA
VISUAL → técnicas. `visual_fingerprint.seleccionar_huella()` (arriba) NO
implementa ese orden algorítmicamente: elige `primary_direction` por
anti-repetición, sin leer concepto/tensión/metáfora, porque este
repositorio no tiene evidencia real de qué categoría "conviene" a qué
concepto jurídico y no finge una afinidad inventada (mismo criterio
fail-closed que `territory_explorer.coherencia()`). El orden real del
Contrato v4 se satisface hoy en la ETAPA DE AUTORÍA humana/pipeline
(`demo_produccion_real_10_temas_nuevos.py` autora escena/metáfora
COMPATIBLES con la huella ya seleccionada, no al revés) — no hay ningún
algoritmo que derive dirección artística desde el concepto jurídico
automáticamente, y construir uno fabricaría un juicio editorial que nadie
ha verificado. No se implementa sin autorización expresa del Founder
(sería inventar afinidad tema→estilo, prohibido explícitamente en este
mismo módulo).

## Añadir un proveedor real

1. `providers/<nombre>.py` con una clase que implemente `ImageProvider`.
2. Declarar `ProviderCapabilities` **con honestidad** — `supports_reliable_text=True`
   solo con capacidad demostrada.
3. Traducir `NormalizedImageRequest` al vocabulario del proveedor **dentro del
   adapter**. El dominio no cambia.
4. Pasar `TestProviderContract` (en `test_visual_advanced.py`).
5. Credenciales por variable de entorno. Nunca en el repositorio (es público).
