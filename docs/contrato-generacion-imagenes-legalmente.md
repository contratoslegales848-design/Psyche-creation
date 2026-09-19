# Contrato de salida para generación text-to-image (Hotfix, 16-sep-2026)

Mandato del Founder: *"al intentar consumir el resultado para generar 10
imágenes nuevas de LegalMente General, el sistema de generación interpretó
la solicitud como EDIT/RESTORE de una imagen existente y exigió una imagen
de referencia."* Este documento define el contrato que cierra ese hueco.

## Causa raíz

`NormalizedImageRequest` (`visual/providers/base.py`) — el único lugar del
repositorio donde se construye la petición final hacia un proveedor de
imagen (`pipeline.py::generate_visual`, se construye una sola vez, línea
150) — no declaraba **ningún campo** que dijera si la petición era una
creación desde cero o una edición. El lenguaje creativo del prompt puede
sonar como "restaurar", "recrear" o "traer de vuelta" sin ser una
instrucción de edición real; un consumidor externo, sin un campo
estructural explícito, no tenía de dónde leer la intención real y
completó la ambigüedad asumiendo edición.

`CompiledVisualRequest` (`visual/compiler.py`) — el paquete/objeto final
que produce el compilador de prompts antes de llegar al proveedor —
tampoco lo declaraba.

## TEXT_TO_IMAGE

Creación de una pieza **nueva, desde cero**. Es el modo por defecto y, hoy,
el único que produce infraestructura real de este repositorio:
`compile_request()` no tiene ni tendrá una vía de edición — sólo compone
piezas nuevas.

```python
generation_mode = "TEXT_TO_IMAGE"
source_image = None
reference_images = ()
edit_instruction = None
```

## IMAGE_EDIT

Edición de una imagen **existente y declarada explícitamente**. No hay
ningún flujo de edición implementado en este repositorio hoy (no hay
proveedor real conectado, ver §"Capacidad real de imagen" más abajo) —
pero el contrato lo soporta estructuralmente para no bloquear un flujo
futuro.

```python
generation_mode = "IMAGE_EDIT"
source_image = <bytes>          # obligatorio — nunca se infiere
reference_images = (...)        # opcional
edit_instruction = "..."        # opcional, describe el cambio pedido
```

## Invariantes (fail-fast, `providers/base.py::validate_generation_contract`)

| Si `generation_mode` es... | entonces... | si no se cumple |
|---|---|---|
| `TEXT_TO_IMAGE` | `source_image` debe ser `None` | ERROR |
| `TEXT_TO_IMAGE` | `edit_instruction` debe ser `None` | ERROR |
| `IMAGE_EDIT` | `source_image` debe existir | ERROR |

Ninguna violación se "adivina" ni se corrige en silencio. `pipeline.py`
llama `validate_generation_contract()` inmediatamente después de construir
la petición normalizada; si hay problemas, el receipt queda en
`CONTRATO_GENERACION_INVALIDO` y **el proveedor nunca es contactado** — ni
siquiera en modo dry-run.

`source_image`/`reference_images` **nunca se heredan automáticamente** de
una generación anterior, de otra pieza del mismo lote, ni de un
`image_id`/asset/attachment previo — cada `generate_visual()` construye su
propia petición desde el `CompiledVisualRequest` de esa pieza únicamente.

## Batch de 10 piezas independientes

Un pedido de "genera 10 imágenes nuevas" se compila como 10 peticiones
`TEXT_TO_IMAGE` independientes, nunca como una cadena de variaciones. Cada
una conserva su propio `topic`, `legal_tension`, `metaphor`,
`primary_direction`, `secondary_direction`, `medium`, `lighting`,
`palette`, `composition`, `materiality`, `camera_optics`, `realism`,
`visual_mechanism` y `final_prompt` — el catálogo maestro (767 módulos,
`visual_fingerprint.py`) y su motor anti-repetición
(`visual_fingerprint_batch.py`) siguen siendo los responsables reales de
que las 10 no compartan una plantilla visual obligatoria; este contrato
sólo garantiza que las 10 lleguen al proveedor como 10 operaciones
`TEXT_TO_IMAGE` separadas, nunca como una cadena de ediciones.

Ejemplo real y verificado — ver
`docs/contrato-salida-10-temas-2026-09-16.md` (generado por
`demo_contrato_generacion_10_temas.py`, reutilizando el lote de
`docs/prueba-real-produccion-10-temas-2026-09-16.md`): 10/10
`TEXT_TO_IMAGE`, 10/10 `source_image` ausente, 10/10 `edit_instruction`
ausente, 10/10 `content_id` únicos.

## LegalMente General — invariantes de canal

```
channel: LegalMente General
format: vertical 9:16
single_scene: true
```

Marca ("LegalMente") integrada físicamente en la escena (metal, vidrio,
piedra, papel, libro, placa, sello, madera, arquitectura u otro objeto
físicamente coherente) — **nunca** como watermark flotante. Este
comportamiento ya existía (`compiler.py`, ADR 0002,
`composition.py::build_brand_plan`) y el hotfix no lo toca: la superficie
de marca varía pieza por pieza (`policy/legalmente-visual-policy-v1.json`,
`marca.superficies_permitidas`), nunca se fuerza el mismo objeto en las
10 piezas de un lote.

## No reintroduce defaults (mandato §9)

Este hotfix es puramente de CONTRATO DE SALIDA — no toca ni reintroduce
ninguno de los defaults ya retirados en mandatos anteriores del mismo día
(óleo/hiperrealismo/claroscuro obligatorio, azul petróleo, nogal, oro
viejo, composición central obligatoria). La dirección artística sigue
viniendo del catálogo maestro (`visual_fingerprint.py`), no de este
módulo.

## Errores

| Error | Cuándo | Qué NO hace el sistema |
|---|---|---|
| `CONTRATO_GENERACION_INVALIDO` (receipt) | `validate_generation_contract()` devuelve problemas | No adivina cuál campo "tiene razón"; no contacta al proveedor |
| `INVALID_REQUEST` (`HttpTransportError`) | `IMAGE_EDIT` sin `edit_endpoint` configurado en el adapter | No reutiliza el endpoint de creación |
| incompatibilidad de `negotiate()` | proveedor sin `supports_editing` y la petición es `IMAGE_EDIT` | No degrada a `TEXT_TO_IMAGE` en silencio ni fuerza la edición |

## Manifiesto machine-readable

`demo_contrato_generacion_10_temas.py` produce
`corpus/manifiesto-generacion-legalmente-general-2026-09-16.json`:

```json
{
  "brand": "LegalMente",
  "channel": "general",
  "operation": "batch_generation",
  "format": "vertical_9_16",
  "count": 10,
  "delivery_status": "COMPILED",
  "provider_connected": false,
  "items": [
    {
      "content_id": "...",
      "topic": {"materia": "...", "concepto_nucleo": "...", "legal_tension": "...", "metaphor": "..."},
      "generation_mode": "TEXT_TO_IMAGE",
      "source_image": null,
      "reference_images": [],
      "edit_instruction": null,
      "format": {"aspect_ratio": "9:16", "width": 1080, "height": 1920, "single_scene": true},
      "fingerprint": {"primary_direction": "...", "...": "..."},
      "final_prompt": "...",
      "negative_prompt": "...",
      "delivery_status": "COMPILED"
    }
  ]
}
```

Sin bytes de imagen, sin referencias ficticias — cualquier agente o
generador externo puede leer `generation_mode` de cada item sin tener que
adivinar intención.

## Estados de entrega (mandato §15)

```
COMPILED          -- el prompt/paquete existe, nada se envió todavía.
SENT_TO_PROVIDER  -- la petición se envió a un proveedor real.
GENERATED         -- el proveedor devolvió una imagen.
QA_ACCEPTED       -- la imagen pasó QA estructural/semántico.
REJECTED          -- la generación o el QA fallaron.
```

Constantes en `providers/base.py` (`DELIVERY_COMPILED`,
`DELIVERY_SENT_TO_PROVIDER`, `DELIVERY_GENERATED`, `DELIVERY_QA_ACCEPTED`,
`DELIVERY_REJECTED`). **Claude Code nunca afirma "las imágenes fueron
generadas" cuando sólo compiló prompts** — el estado máximo alcanzado hoy,
en todo este repositorio, es `COMPILED`: no existe ningún proveedor de
imagen real y autorizado conectado (`docs/auditoria-inteligencia-tematica-2026-09-16.md`
§3). Higgsfield es técnicamente alcanzable vía MCP en algunas sesiones
pero está **prohibido de forma permanente** para LegalMente por CLAUDE.md
— nunca cuenta como "proveedor conectado" a efectos de este contrato.

## Integración futura con proveedores

`providers/http_provider.py::HttpProviderConfig` ya distingue
`endpoint` (creación) de `edit_endpoint` (edición, opcional) — nunca se
mezclan payloads ni se infiere un endpoint de edición a partir del de
creación. Cuando el Founder autorice un proveedor real:

1. Configurar `HttpProviderConfig` con credenciales reales (variable de
   entorno, nunca en código) y, si el proveedor soporta edición,
   `edit_endpoint` + `supports_editing=True`.
2. `pipeline.generate_visual()` ya construye y valida el contrato
   correctamente — no requiere cambios.
3. Los manifiestos ya compilados (`demo_contrato_generacion_10_temas.py`)
   pueden alimentar directamente `NormalizedImageRequest` sin rediseño.

## No inventar un proveedor

Ningún adapter de un proveedor específico (OpenAI, Grok, Gemini, Flux,
Stable Diffusion, Ideogram) se escribió en este hotfix ni se escribirá sin
su SDK/credenciales reales — sería inventar un proveedor, prohibido por
mandato. El contrato queda listo, agnóstico de proveedor, para que
cualquier adapter real futuro lo consuma sin ambigüedad.
