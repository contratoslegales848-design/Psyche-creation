# Partes XIV-XVI del mandato "Fase post-implementación" (16-sep-2026)

## Parte XIV — QA visual del lote

Reglas ya implementadas (`visual_fingerprint_batch.evaluar_lote_visual`),
aplicadas al lote real de
`docs/prueba-real-produccion-10-temas-2026-09-16.md`: **ACEPTADO en 1
intento** — 10/10 huellas perceptiblemente diferentes, 8 medios/familias
distintos (mínimo real 5), ningún medio por encima del tope de 2, cero
repetición consecutiva de primary_direction/composition/lighting/palette,
distancia mínima de 4 dimensiones sustantivas cumplida entre todas las
piezas consecutivas.

**Revisión perceptual, no solo el JSON** (la pregunta explícita del
mandato: "¿Las 10 parecen realmente distintas?"): leídas las 10
combinaciones de `primary_direction`/`medium`/`palette`/`materiality` una
por una —

1. tapiz (escultura/objeto) — ciruela y gris humo, arena
2. dibujo de ingeniería (grabado/estampa) — marfil y grafito, mármol
3. pintura de borde duro (pintura) — verde salvia y grafito, acero pulido
4. cámara de documentos (arquitectura/escenografía) — grises cálidos, polvo mineral
5. objeto encontrado refinado (escultura/objeto) — aluminio y negro, yeso
6. diagrama jurídico visual (editorial/gráfico) — high-key casi blanca, vidrio
7. cartografía topográfica (editorial/gráfico) — pasteles arquitectónicos, porcelana
8. firma manuscrita abstracta (archivo/manuscrito) — rojo carmín y negro, madera quemada
9. render arquitectónico fotorrealista (CGI) — vidrio transparente y blanco, fieltro
10. fotografía naturalista sobria (fotografía) — tritono editorial, papel reciclado

Son diez imágenes mentales genuinamente distintas al leerlas — un tapiz no
se confunde con un render arquitectónico, ni un diagrama jurídico con una
fotografía documental. Las dos que comparten medio (6 y 7, ambas
`editorial_diseno_grafico_y_sistemas_impresos`) son perceptualmente
distintas entre sí (diagrama jurídico vs. mapa topográfico, paletas y
materialidad opuestas) — el medio compartido no las vuelve intercambiables.

## Parte XV — capacidad real de generación de imagen

Ya determinado en la Fase 1 de este mandato
(`docs/auditoria-inteligencia-tematica-2026-09-16.md` §3), confirmado de
nuevo aquí sin cambios: `visual/providers/` sólo tiene `FakeImageProvider`
(pruebas) y un perfil de ejemplo de proveedor HTTP genérico sin
credenciales. **No existe ningún generador de imagen real y autorizado
conectado a este repositorio.** Higgsfield es técnicamente alcanzable
desde esta sesión vía MCP, pero está **prohibido de forma permanente**
para LegalMente por CLAUDE.md — no se usa, con independencia de la
disponibilidad técnica.

**Consecuencia directa, tal como exige la Parte XV**: la prueba de
producción real (Parte XIII) entrega los 10 paquetes completos — huella
visual + prompt compilado — y se detiene ahí. Ninguna imagen fue generada,
ninguna se simuló, ninguna se marcó como aprobada. El componente que debe
consumir estos paquetes cuando exista un proveedor real y autorizado es
`providers.selection.evaluate()` + `provider.generate()`
(`pipeline.generate_visual()`, ya implementado y probado con
`FakeImageProvider` desde el mandato original de `visual/`) — no hace
falta construir nada nuevo para ese paso, sólo un adapter real cuando el
Founder autorice un proveedor.

## Parte XVI — criterios de rechazo de imagen

Mapeo contra lo que ya existe. Ninguno de estos criterios se verificó
sobre una imagen real (no hay imagen) — se documenta qué mecanismo YA lo
cubriría en cuanto exista una, y cuáles sólo pueden verificarse con una
imagen real en mano.

| Criterio del mandato | Mecanismo existente | Estado hoy |
|---|---|---|
| Parece plantilla / repite fórmula visual | `visual_fingerprint_batch.evaluar_lote_visual` (huellas distintas, tope por medio, sin repetición consecutiva) | Verificado a nivel de PLAN (Parte XIV) — falta la imagen real para confirmarlo a nivel de píxel |
| Parece otra pieza reciente | `visual_fingerprint.FingerprintMemory` + `semantic_memory` (repetición temática) | Verificado a nivel de PLAN — ambos motores corrieron sobre el lote real |
| Usa clichés automáticos | `families.py::forbidden_tropes` (compilador ya los añade como negativos) + `policy.composicion.prohibido` | Verificado en el prompt compilado (negativos incluidos) |
| Marca incorrecta / "LegalMente" flota como watermark | `compiler.py` (marca siempre `POST_COMPOSITE`, nunca la escribe el generador) + `composition.py::build_brand_plan` | Cubierto por diseño — ADR 0002, ya probado |
| Collage/grid/storyboard | `policy.composicion.prohibido` (negativo fijo en cada prompt) | Cubierto en el prompt compilado |
| Formato incorrecto | `qa.structural_qa` (dimensiones reales del PNG) | Requiere imagen real — no verificable sobre un plan |
| Texto ilegible | `compositor.py::composition_qa` (texto se compone determinísticamente, nunca lo escribe el generador) | Cubierto por diseño para el texto compuesto; el generador nunca escribe texto legal |
| Metáfora no corresponde al tema | Sin mecanismo automatizado — es juicio editorial humano | **Hueco real, declarado**: ningún módulo verifica correspondencia semántica metáfora↔tema hoy |
| Dirección artística declarada no es perceptible | Revisión perceptual manual (ver Parte XIV arriba) | Parcialmente cubierto — funciona sobre la DESCRIPCIÓN, no sobre el píxel final |
| Iluminación/paleta/default anterior reaparece sistemáticamente | `visual_fingerprint_batch` (tope por medio) + Fase 8-9 del mandato anterior (retiró el default de azul petróleo) | Cubierto por diseño y por corrección ya aplicada |
| Composición no coincide con fingerprint | `compiler.py` imprime `composition_intent` desde la huella; sin imagen real no hay forma de comparar contra el píxel | Requiere imagen real |
| Técnicamente correcta pero conceptualmente genérica | Sin mecanismo automatizado — es juicio editorial humano, como "metáfora no corresponde al tema" | **Hueco real, declarado** |

**Conclusión honesta**: 9 de 12 criterios ya tienen un mecanismo real que
los cubre en la etapa de PLAN (antes de imagen); 2 (metáfora↔tema,
genérico-pero-correcto) son juicio humano y no tienen ni deberían tener
automatización que reemplace esa revisión; el resto requiere una imagen
real en mano, que no existe en este repositorio hoy.
