# Contenido ya bloqueado o de riesgo conocido

Este archivo registra hallazgos reales de investigación ya hecha en el proyecto LegalMente, para no repetir el mismo error dos veces. No es exhaustivo — es lo que ya se investigó. La ausencia de una cita o tema aquí no significa que esté verificada; significa que todavía no se ha investigado en este proyecto.

## Citas bloqueadas por atribución no confirmada

No publicar ninguna de estas sin fuente primaria nueva que resuelva la atribución:

- **Erin Brockovich** — cita sin fuente primaria identificada.
- **"La pena como secuestro"**, atribuida a Ihering — atribución no confirmada.
- **"La lentitud de la justicia..."**, atribuida a Ihering — la investigación apunta a que en realidad es de Séneca, no de Ihering.
- **Agatha Christie** — cita sin fuente primaria identificada.
- **Emma Goldman** — la cita que circula atribuida a ella es en realidad de Lacassagne.
- **Édouard Laboulaye** — cita sin fuente primaria identificada.

Cualquier variante, traducción o paráfrasis de estas cinco entradas hereda el mismo bloqueo hasta que exista fuente primaria verificable.

## Casos donde una figura "obviamente Capa A" resultó ser Capa B/C

Ver `jurisdiction-policy.md` para el detalle completo. Resumen:

- "Promesa de compraventa" ≠ figura panhispánica universal (Argentina: "boleto de compraventa", régimen distinto).
- Comisión mercantil sí es Capa A confirmada en México/Colombia/Perú, pero se llegó a esa conclusión por verificación explícita país por país, no por asunción.

## Recursos visuales saturados (referencia cruzada con legalmente-visual-system)

Esta skill no decide dirección visual, pero si una afirmación jurídica se está redactando específicamente para encajar con uno de estos recursos ya sobreexplotados, señálalo en `notas` del paquete para que quien monte el arte lo sepa: balanza de la justicia, mazo de juez, persona sola frente a un edificio de columnas, libros o pergaminos apilados sobre escritorio oscuro, objeto forense sobre pergamino.

## Temas que requieren Platform Risk Check antes de arte/publicación

Cualquier pieza que toque violencia, muerte, amenazas, suicidio/autolesión, sexualidad, drogas, delitos o salud mental necesita `platform_review_required: true` en el paquete. Ejemplo ya resuelto en el proyecto: el hook "Le dijo a su psicólogo: 'Voy a matarlo'. ¿Sigue siendo un secreto?" se reformuló a "Le dijo a su psicólogo que podía poner una vida en riesgo. ¿Hasta dónde llega el secreto profesional?" — misma tensión jurídica, menor riesgo de distribución. Esta skill no ejecuta el Platform Risk Check (vive fuera de su alcance), solo lo señala.
