# Motor de generación visual — V1

**Estado: arquitectura construida y probada con proveedor falso. Ningún adapter real implementado.**

Esto es la capa que faltaba entre `ProductionHandoff` (fin de la cadena jurídica) y
el arte final. No sustituye a `legalmente-visual-system`: esa skill sigue teniendo
el criterio artístico (qué escuela toca, qué metáfora, qué rotación). Este módulo
ejecuta lo que un programa *puede* comprobar, y bloquea lo que no.

## Principio

LegalMente posee el contenido, las reglas, la intención visual, el prompt compilado,
el historial y la decisión humana. Los proveedores (OpenAI, Grok, Gemini, Higgsfield,
Flux, SD, Ideogram) son ejecutores reemplazables detrás de una interfaz. **El dominio
no menciona a ninguno.**

## Flujo

```
procedencia + ProductionHandoff
   → gate de entrada        gates.can_enter_visual_generation()
   → brief + política       brief.VisualBrief.validate()
   → prompt compilado       compiler.compile_prompt()
   → negociación            providers.base.negotiate()
   → adapter                providers.base.ImageProvider
   → QA estructural         qa.structural_qa()
   → [GATE HUMANO]          ← el código se detiene aquí, siempre
   → receipt                receipts.GenerationReceipt
```

## Lo que este módulo NO hace

- **No recalcula estado jurídico.** Lee `gate_arte` y el handoff que produjo la cadena
  canónica. Ante estado ilegible, cierra. Nunca escala autoridad.
- **No aprueba nada.** El mejor desenlace alcanzable es `PENDIENTE_REVISION_HUMANA`.
  No existe ningún status que signifique aprobado — verificado por prueba.
- **No llama a ningún proveedor real.** Sin credenciales, sin red, sin créditos.
- **No juzga estética ni identidad de marca.** El QA es estructural (formato,
  dimensiones, integridad, unicidad). Lo demás lo firma una persona.
- **No crea un `ContentUnit` paralelo.** `docs/contrato-motor-masivo.md` §1–§2 ya
  repartió esos campos entre el claim packet y `content/*.json`; duplicarlos habría
  cambiado el `contenido_hash_sha256` e invalidado aprobaciones firmadas.

## Conflicto abierto — requiere decisión del fundador

`policy/legalmente-visual-policy-v1.json` declara
`marca.texto_marca_lo_escribe_el_generador = "NO_RESUELTO"`.

| Fuente | Sostiene |
|---|---|
| Mandato de integración §20 | la palabra "LegalMente" se integra físicamente en la escena, generada dentro de la imagen |
| `docs/decision-visual-marca-sin-texto.md` (ADR **propuesto**, no aprobado) | el generador no escribe ninguna letra; la superficie de marca se reserva vacía y se monta después |
| Mandato §21 | para carga jurídica, preferir composición determinista posterior |

Mientras el valor sea `NO_RESUELTO`, cualquier brief que pida al generador escribir
la marca **se bloquea** con `BRIEF_INVALIDO`, y el prompt compilado describe una
superficie reservada vacía. Es una decisión de una línea (`SI` | `NO`), no un
refactor.

## Pruebas

```bash
cd visual && python3 -m unittest test_visual_pipeline -v
```

49 pruebas. Cubren: gate fail-closed (11), brief/política (8), compilador (7),
negociación (3), QA (5), pipeline (8), receipts (3), y los 7 modos de fallo del
proveedor falso.

## Añadir un proveedor real

1. Crear `providers/<nombre>.py` con una clase que implemente `ImageProvider`.
2. Declarar sus `ProviderCapabilities` con honestidad — `supports_reliable_text=True`
   solo con capacidad demostrada, no prometida.
3. Traducir `NormalizedImageRequest` al vocabulario del proveedor **dentro del
   adapter**. El dominio no cambia.
4. Las credenciales por variable de entorno. Nunca en el repositorio (es público).
