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

## Añadir un proveedor real

1. `providers/<nombre>.py` con una clase que implemente `ImageProvider`.
2. Declarar `ProviderCapabilities` **con honestidad** — `supports_reliable_text=True`
   solo con capacidad demostrada.
3. Traducir `NormalizedImageRequest` al vocabulario del proveedor **dentro del
   adapter**. El dominio no cambia.
4. Pasar `TestProviderContract` (en `test_visual_advanced.py`).
5. Credenciales por variable de entorno. Nunca en el repositorio (es público).
