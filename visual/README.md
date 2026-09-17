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

**CONTINUACIÓN EJECUTIVA — prioridad pedagógica (17-sep-2026, misma fecha,
segunda pasada; "conocimiento primero, formato después"):** el registro
editorial creció de 58 a **65 familias** — 7 altas reales, mismo mecanismo
(`register_familia()`/`editorial-universe-v1.json`), cubriendo ítems del
mandato §3 sin familia previa: `clasificacion`, `elementos`,
`mapa_de_materia`, `institucion_juridica`, `para_recordar`,
`quiz_juridico`, `relacion_figuras`. Ninguna de las 7 es narrativa
(`FAMILIAS_NARRATIVA` sigue siendo exactamente 5/65). `pedagogia.py` ganó:

- `DIMENSIONES_CONOCIMIENTO` / `DIMENSION_POR_FAMILIA` — las 20 dimensiones
  de conocimiento del mandato §1/§8 (qué es, elementos, requisitos,
  clasificación... siguiente pregunta), leídas de forma auditable de la
  `funcion_editorial` real de cada una de las 65 familias — nunca un
  catálogo paralelo. `dimension_de_familia()` la consulta;
  `cubre_dimensiones_distintas(candidatos)` mide si un conjunto de piezas
  que comparten `concepto_nucleo` (una "ruta de aprendizaje", mandato §4)
  enseña ángulos distintos o repite el mismo ángulo.
- `aprendizaje_concreto(candidato)` — QA del mandato §7 ("¿la persona
  aprendió algo jurídico concreto? Si NO: REWORK"), proxy estructural sobre
  `concepto_nucleo` + `pregunta_resuelta`/`consecuencia`/`relacion`. Cablea
  a `production_run.qa_dos_ejes()` como el quinto eje del QA,
  `sustancia_pedagogica_ok`, mismo patrón no-exclusión-silenciosa que
  `memoria_fuerte_ok`.
- `formato_sugerido(profundidad, n_dimensiones_disponibles)` — sugerencia
  (mandato §6, nunca obligación) de formato editorial cuando una pieza
  compleja no cabe en una sola pieza simple: "nunca elimines relaciones
  importantes, selecciona otro formato o divide la enseñanza".

**Investigación cerrada, sin gate nuevo (mandato §4):** ¿hace falta un
mecanismo separado para evitar que una ruta de aprendizaje salga entera en
un solo lote? No — el hard gate `_cuota_materia` ya existente (una ruta
real comparte materia) ya limita a ~2/10 cuántas piezas de una misma ruta
salen juntas, y las que sí salen juntas cubren dimensiones distintas
(verificado con `cubre_dimensiones_distintas`, ver
`test_generator.py::TestRutaDeAprendizajeNoSeAmontonaEnUnLote`). Construir
un segundo gate habría sido el "segundo motor" que el mandato prohíbe
explícitamente.

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

### Orden causal Contrato v4 §4/§5 — RESUELTO (`direccion_causal.py`, continuación Mandato Maestro, 17-sep-2026)

**Corrección de esta misma sección** (quedó desactualizada tras resolverse
el gap, sin corregirse en su momento — lección operativa registrada en
`docs/TECHNICAL_STATE.md`): el orden CONCEPTO → TENSIÓN → IDEA → METÁFORA →
ESCENA → DIRECCIÓN ARTÍSTICA que pedía el Contrato v4 YA está implementado
algorítmicamente, sin fabricar una tabla "concepto=estilo" (explícitamente
prohibida por el mandato que cerró este gap). `direccion_causal.
seleccionar_direccion_causal()` deriva un `Significado` determinista y
auditable de cada `TopicCandidate` (concepto, tensión, movimiento jurídico,
grado de abstracción, contraste — cada uno citando qué campo real lo causó),
restringe SÓLO 2 de las 10 dimensiones del catálogo maestro (`realism`,
`visual_mechanism`) al subconjunto causalmente compatible con ese
significado, y reutiliza sin cambios el motor de anti-repetición de
`visual_fingerprint.seleccionar_huella()` sobre esa vista filtrada. Las
otras 8 dimensiones (incluida la biblioteca de 504 `primary_direction`)
siguen rotando por anti-repetición pura — límite honesto documentado en el
propio módulo, no un oversight. `art_direction.draft_visual_brief()` llama
a este compilador en vez de la selección ciega anterior. Demostración:
`python3 demo_reconciliation.py` y `test_direccion_causal.py` (24 tests,
incluida la prueba de que la materia NO determina el estilo y de que
cambiar la tensión sí puede cambiar la dirección visual con la materia
constante).

### Safe zone multiformato 9:16 → 4:5 (`safe_zone.py`, tarea 78, 17-sep-2026)

**Regla canónica: "9:16 visualmente amplio; 4:5 semánticamente completo".**
Toda pieza maestra `VERTICAL_9_16` (1080×1920) debe seguir siendo semántica
y visualmente completa si se le aplica un recorte CENTRAL `SOCIAL_4_5`
(1080×1350) — Facebook u otra superficie puede hacerlo sin avisar. **Esto
NO es "generar dos versiones"**: el asset maestro sigue siendo 9:16; lo que
cambia es que el contenido indispensable vive dentro de una safe zone
interior al área que sobrevive al recorte, y la extensión superior/inferior
se usa activamente como expansión artística (atmósfera, profundidad),
nunca como excusa para centrar todo y vaciar el fondo. **Una pieza 9:16 no
pasa producción si al recortarse centralmente a 4:5 pierde información
jurídica esencial.**

- **Geometría** (`legalmente-visual-policy-v1.json`, sección `formatos` +
  `safe_zone` nuevas): `VERTICAL_9_16` declara `crop_safe_for:
  "SOCIAL_4_5"`; el recorte central elimina 285px arriba y 285px abajo
  (mismo ancho, alto reducido simétricamente), y la safe zone real añade un
  padding interno del 6% (`safe_zone.padding_interno_ratio`, también en la
  política) porque distintas superficies no garantizan recortar
  exactamente igual — el margen es deliberadamente conservador, nunca el
  borde exacto del crop. `safe_zone.calcular_geometria(policy)` deriva
  todo esto de los formatos YA declarados; ningún número de canvas/crop se
  repite aparte.
- **Clasificación esencial/decorativo**: reutiliza los campos YA
  declarados de `brief.VisualBrief` — `subject`/`focal_point`/`metaphor`/
  `acento_objeto` (y `marca_superficie` cuando la integración física de
  marca es obligatoria) son esenciales por su propio significado; `
  environment`/`camera`/`negative_space`/`key_light`/`brightness_intent`
  son atmósfera/puesta en escena y pueden vivir en la extensión que el
  recorte elimina.
- **Compilación** (`compiler.compile_request()`): cuando el formato pedido
  declara `crop_safe_for`, el prompt compilado incluye una instrucción
  determinista (derivada de la geometría real, nunca texto libre inventado
  cada vez) — "componer nativamente para 9:16 completo... pero mantener
  todo el contenido esencial dentro del área central segura... usar las
  extensiones sólo para atmósfera". `CompiledVisualRequest` gana
  `crop_safe_4_5_ok`/`crop_safe_4_5_detalle` — informativo, mismo patrón
  que `memoria_fuerte_ok`: nunca bloquea la compilación por sí solo, quien
  orquesta decide.
- **QA** (`safe_zone.crop_safe_4_5()`): sin visión por computadora — no hay
  bounding boxes reales para la escena que genera el proveedor de imagen
  (mismo límite honesto que `compositor.py` declara para la superficie de
  marca). El QA opera sobre la representación semántica REAL que el sistema
  sí controla: el texto declarado de cada campo del brief, con patrones de
  riesgo de zona (mismo patrón de coincidencia que
  `memoria_fuerte.REGLAS_RECHAZO_FOUNDER`, vía la normalización compartida
  `memory.normaliza_texto_libre()`). Un campo ESENCIAL que declara una
  ubicación de riesgo (extremo superior, extremo inferior, fuera del
  recorte) falla; el mismo texto en un campo decorativo nunca falla — ahí
  es exactamente donde debe vivir.
- **Evidencia real**: `demo_produccion_real_10_temas_nuevos.py` documenta,
  sobre 3 piezas reales del mismo lote (una figura jurídica, una pieza
  probatoria/procesal, una pieza conceptual), qué permanece dentro del
  crop, qué puede perderse arriba/abajo y por qué el mensaje sigue íntegro
  — ver `docs/prueba-real-produccion-10-temas-2026-09-16.md`, sección
  "Safe zone multiformato 9:16 → 4:5".
- **Tests**: `test_safe_zone.py` (26) — geometría, contenido crítico
  (PASS/FAIL adversarial), formatos (9:16 declara compatibilidad sin
  forzar un segundo asset; `SOCIAL_4_5` nativo no aplica la regla),
  regresión (compila igual, nunca bloquea, diversidad artística intacta) y
  determinismo (misma entrada → misma geometría/instrucción/veredicto).

### Disciplina visual recuperada del motor anterior (Drive, 3ª pasada, 17-sep-2026)

Mandato del Founder: "recuperar la disciplina visual del motor antiguo
dentro del motor actual" — auditado contra Drive (`Guía operativa del
motor de dirección artística`, `Bancos del motor artístico`, `Dirección
Artística Adaptativa v1.2/v1.3`, `legalmente-generador-aleatorio.xlsx`,
`Protocolo maestro visual v3`), todos ellos marcados **LEGACY/histórico**
en Drive — no se restauran como motor activo (el Excel está
explícitamente etiquetado `[USO LIMITADO — temas; no dirección
artística]`, y `catalogo-maestro-v1.md` es copia literal del Founder que
nunca se edita a mano, así que ninguna de sus escuelas/escenarios propios
se mezcla con ese archivo).

**Causa raíz real, no hipotética**: el HOTFIX del banco anterior
("DISTANCIA VISUAL Y ANTI-MONOTONÍA", 8-sep-2026 — 8 dimensiones, mínimo 5
cambiadas, comparado contra los 3 vecinos más cercanos) YA estaba portado
en este repositorio (`visual_distance.py`, reconciliación con
`legalmente-web`) — pero NUNCA se ejercitaba con datos reales. El flujo
automatizado (`production_run.py`) tiene `metaphor`/`scene_type`
deliberadamente `PENDIENTE_CONTENIDO` (correcto: son contenido creativo
que requiere verificación jurídica y autoría humana, no infraestructura),
así que sus 8 dimensiones nunca están completas y el mecanismo siempre
reporta `EVIDENCIA_INCOMPLETA` — nunca llega a validar nada. Y
`demo_produccion_real_10_temas_nuevos.py`, que SÍ tiene autoría real
completa (`DIRECCION_VISUAL`), nunca llamaba a `visual_distance.py` en
absoluto. El mecanismo que habría detectado "esto parece una plantilla
repetida" existía, era correcto, y estaba desconectado del único lugar con
datos reales para probarlo.

**KEEP** (verificado, sin tocar): una escuela por pieza, integración física
de marca, no-collage/grid, `visual_distance.py` en sí (sólo se cablea, no
se reescribe), causal pipeline (`direccion_causal.py`), 65 familias,
pedagogía §12, memoria fuerte, `_cuota_materia`, safe zone.
**REJECT**: el Excel como motor activo, cualquier unión rígida
materia→escuela (ambos bancos, el anterior y el actual, la prohíben
explícitamente), y "3 de 5 dimensiones cambiaron" como prueba suficiente
de variedad — el banco anterior corrigió esa misma regla en su propio
HOTFIX por insuficiente.

**ADAPT** (cableado nuevo, cero motor nuevo):
- `demo_produccion_real_10_temas_nuevos.py::_entry_real()` construye un
  `VisualMemoryEntry` real por pieza reutilizando datos YA calculados
  (`huella.primary_direction/camera_optics/lighting/materiality/palette` +
  `direccion_causal.derivar_significado()` para `scene_type`/
  `human_presence`, ambos reutilizados, no fabricados) y
  `_distancia_estricta_del_lote()` corre `visual_distance.
  verificar_lote_contra_historia(entries, historia=())` sobre el lote
  real — la primera vez que el HOTFIX de 8 dimensiones se valida con
  datos genuinamente completos en este repositorio (30/30 comparaciones,
  8/8 dimensiones conocidas en las 45 parejas, mínimo real 6/8 distintas
  — nunca menos de las 5 exigidas).
- `arquetipo_compositivo.py` (nuevo, pequeño, mismo patrón de coincidencia
  léxica que `memoria_fuerte.py`/`safe_zone.py`): Regla 3 del banco
  anterior ("no más de 3 piezas del mismo arquetipo compositivo — objeto
  sobre superficie, retrato/persona frontal, documento en close-up,
  pasillo/arquitectura central, bodegón, escena de escritorio"). Este
  chequeo SÍ encontró algo real que `visual_distance.py` no detecta por
  diseño (dos piezas pueden diferir en escuela/luz/material y aun así
  compartir el mismo patrón compositivo de fondo): el lote real original
  tenía 6/10 piezas clasificadas `ESCENA_ESCRITORIO` (dos sillas/mesa de
  reunión). Se re-autoraron 3 (`CAND-0034`, `CAND-0076`, `CAND-0041`) con
  composiciones genuinamente distintas — mismo concepto jurídico, otra
  puesta en escena — hasta quedar en `{DOCUMENTO_CLOSEUP: 3,
  ESCENA_ESCRITORIO: 3, OBJETO_SOBRE_SUPERFICIE: 2,
  PASILLO_ARQUITECTURA_CENTRAL: 1, SIN_CLASIFICAR: 1}`, dentro del tope.
- `arquetipo_compositivo.py` reutiliza `memory.normaliza_texto_libre()`
  (promovida en la tarea 78, safe zone) en vez de duplicar la
  normalización una tercera vez.

**Tests**: `test_arquetipo_compositivo.py` (13, nuevo) + 2 nuevos en
`test_produccion_real_10_temas_nuevos.py` (distancia estricta y arquetipo
compositivo sobre el lote real, no simulado).

### 4ª pasada (17-sep-2026): afinidad entre arquetipos cercanos

El Founder observó, correctamente, que "3 escritorios + 3 documentos"
puede seguir siendo un lote perceptualmente monótono aunque cada
arquetipo individual respete su propio tope de 3. El banco anterior ya lo
advertía en su Regla 9 ("Revisión del lote como portafolio", HOTFIX
8-sep-2026): "Si 4 o más se sienten de la misma sesión... sustituir las
más débiles." `arquetipo_compositivo.py` gana dos verificaciones nuevas
(no sustituyen la Regla 3, se suman):

- `verificar_afinidad_familias()` — agrupa arquetipos perceptualmente
  cercanos (`FAMILIAS_PERCEPTUALES`: `DOCUMENTO_CLOSEUP` +
  `ESCENA_ESCRITORIO` + `PASILLO_ARQUITECTURA_CENTRAL` = "interior
  institucional"; `OBJETO_SOBRE_SUPERFICIE` + `BODEGON` = "objeto
  aislado") y aplica un tope combinado (4/10, literal de la Regla 9) más
  estricto que la suma de topes individuales.
- `verificar_redundancia_ambientacion()` — eje DISTINTO: vocabulario
  compartido en `environment`, no en el arquetipo. Encontró un problema
  real que ninguno de los chequeos anteriores detectaba: 4/10 piezas
  mencionaban "archivo"/"archivador" en su entorno pese a tener
  arquetipos compositivos distintos entre sí.

**Hallazgo real con estos dos chequeos nuevos**: el lote (ya corregido en
la 3ª pasada para la Regla 3) tenía 7/10 piezas en la familia perceptual
"interior institucional" — pasaba el tope individual de cada arquetipo
pero no el combinado. Re-autoradas 3 piezas más (`CAND-0041`, `CAND-0053`,
`CAND-0013`), cada una con una escena en un registro genuinamente distinto
(planta industrial, orilla de un río, jardín) — dos de ellas incluso
ligadas más de cerca a su propia metáfora ya declarada (`CAND-0053`: "un
río que cambia de cauce" ahora tiene un río real en escena, no un
despacho). Distribución final: arquetipo `{DOCUMENTO_CLOSEUP: 2,
OBJETO_SOBRE_SUPERFICIE: 2, ESCENA_ESCRITORIO: 1,
PASILLO_ARQUITECTURA_CENTRAL: 1, SIN_CLASIFICAR: 4}`; familias
`{INTERIOR_INSTITUCIONAL: 4, OBJETO_AISLADO: 2}` (dentro del tope de 4);
ambientación `{ARCHIVO: 2, DESPACHO_OFICINA: 1, SALA_DE_REUNION: 1,
LABORATORIO: 1, TERRENO_EXTERIOR: 2, MUSEO_VITRINA: 1}` (ninguna por
encima de 3). La distancia estricta de 8 dimensiones (`visual_distance.py`)
se re-verificó sin cambios: sigue en 30/30, mínimo real 6/8.

**Auditoría de los 6 mecanismos del mandato** (KEEP/ADAPT/REJECT):

| Mecanismo | Estado | Evidencia |
|---|---|---|
| Dirección artística dominante | **KEEP** — activo | `visual_fingerprint._construir_huella()`: un solo `primary_direction` por pieza, `secondary_direction` opcional (50%), nunca se mezclan referentes en el mismo prompt. |
| Mecanismo visual/revelación | **KEEP** — activo y causal | `visual_mechanism` restringido por `direccion_causal.py` según `necesidad` (mejor que el banco anterior: causal, no sólo anti-repetición). |
| Composición cerrada | **KEEP** — activo estructuralmente | `policy.composicion.scene_count=1` + lista `prohibido` (collage/grid/split screen/díptico/tríptico) + un solo campo `metaphor`/`acento_objeto` en el schema (no listas) — el "no acumular símbolos" lo impone la forma del dato, no sólo una regla de texto. |
| Combinaciones curadas | **ADAPT parcial, límite honesto** | Las 7 dimensiones auxiliares del catálogo maestro rotan independientemente por anti-repetición, sin verificar coherencia entre sí ni con la escena autorada — limitación YA documentada en `direccion_causal.py` (sólo 2/10 dimensiones son causales). Ejemplo real encontrado: `materiality="hielo"` para una escena de "placa de bronce en archivo corporativo" — incoherente, pero corregirlo de verdad exigiría fabricar afinidad material→escena que este repositorio no tiene evidencia para sostener (mismo criterio fail-closed de todo el módulo). No se fuerza. |
| Rotación de escenario/material/medio | **ADAPT** (escenario) / **KEEP** (material, medio) | `medium`/`materiality` SÍ rotan (parte del catálogo maestro real). `escenario` (el lugar físico) NO tiene banco propio — es texto libre autorado por humano, sin anti-repetición mecanizada (no se puede inyectar un banco propio en `catalogo-maestro-v1.md`: es copia literal del Founder). Se cubre con `verificar_redundancia_ambientacion()` sobre el texto YA autorado, no con un banco nuevo. |
| Prompt final compacto | **ADAPT** — redundancia real eliminada | `compiler.py` repetía el nombre completo de la paleta dos veces seguidas ("Paleta: X." + "el acento de color (X) debe proceder..."); ahora refiere "esa misma paleta". Confirmado que `explanation`/`metadata` (razonamiento editorial) nunca se mezclan con `positive_prompt` — están en campos separados de `CompiledVisualRequest` desde su diseño original. |

**REJECT reafirmado**: el Excel (`legalmente-generador-aleatorio.xlsx`)
sigue sin restaurarse como motor activo; ninguna unión rígida
materia→escuela; "cambiaron 3 de 5 dimensiones" nunca es prueba suficiente
de variedad por sí sola (por eso existen los 4 chequeos independientes:
`visual_distance` + arquetipo + familias + ambientación).

**Validación estructural vs. raster** — explícitamente separadas: (A)
**completada**: reserva/selección/dirección de arte/prompt compilado/QA de
9 ejes (intelectual, visual, títulos ocultos, memoria fuerte, sustancia
pedagógica, safe zone, distancia estricta, arquetipo, afinidad de
familias, ambientación — son 10 en realidad, contados aquí) sobre un lote
real de 10, con datos reales de principio a fin. (B) **pendiente,
exclusivamente por falta de proveedor de imagen**: ningún píxel real se
generó ni se verá — no hay proveedor de imagen conectado en este entorno
(Higgsfield permanece prohibido; ver `providers/`). La afirmación de que
"las 10 piezas se ven distintas" se sostiene sobre el plan/prompt/escena
declarados, nunca sobre una imagen renderizada.

## Añadir un proveedor real

1. `providers/<nombre>.py` con una clase que implemente `ImageProvider`.
2. Declarar `ProviderCapabilities` **con honestidad** — `supports_reliable_text=True`
   solo con capacidad demostrada.
3. Traducir `NormalizedImageRequest` al vocabulario del proveedor **dentro del
   adapter**. El dominio no cambia.
4. Pasar `TestProviderContract` (en `test_visual_advanced.py`).
5. Credenciales por variable de entorno. Nunca en el repositorio (es público).
