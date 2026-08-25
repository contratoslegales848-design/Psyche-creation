# ADR propuesto — arte base sin texto, marca y tipografía se montan después

**Estado: PROPUESTA, no decisión aprobada.** Registrada por el modelo en la revisión Fase 1A (2026-08-25) y renombrada explícitamente como "ADR propuesto" en la revisión Fase 1B (corrección de que no se presente como si ya estuviera aprobada por el fundador). Ningún cambio a `legalmente-visual-system` se ha aplicado ni se aplicará a partir de este documento hasta que Raymundo la apruebe expresamente. Este documento no modifica esa skill global — solo deja la propuesta por escrito para que una fase futura, ya autorizada, la implemente si se aprueba.

## El hallazgo que motiva esto

La auditoría de `legalmente-visual-system` (Fase 1) encontró una contradicción entre dos instrucciones que la skill da al mismo tiempo:

1. "TEXTO EN LA IMAGEN: ninguno. Ni una letra, ni firma, ni numeración."
2. La marca debe integrarse "físicamente en un objeto real de la escena" mediante **la palabra "LegalMente"** grabada, sellada o legible en ese objeto (sello de lacre, placa de latón, matasellos, etc.).

Pedirle a un generador de imágenes "ninguna letra" y "la palabra LegalMente legible" en el mismo prompt es una instrucción ambigua: los generadores de imagen son notoriamente inconsistentes al renderizar texto, y esta contradicción aumenta el riesgo de que la marca salga ilegible, deformada o mal ubicada — o que el generador ignore una de las dos instrucciones sin avisar.

## La propuesta

**El generador de imágenes no escribe ninguna letra — ni "LegalMente", ni títulos, ni citas, ni firmas, ni artículos, ni numeración.** El arte base se genera completamente limpio, siempre.

Para integrar la marca físicamente en un objeto de la escena (siguiendo el mismo núcleo de marca ya validado: sello de lacre, placa de latón, matasellos, chapa numerada, etc.):

- El arte reserva una **placa, sello, etiqueta o superficie vacía** en el objeto — con la forma, el relieve, la luz y la perspectiva correctos para que algo se lea ahí, pero sin ningún carácter dentro.
- La palabra "LegalMente" (o el logotipo real de la marca) se añade **después**, en Canva o mediante composición controlada, con perspectiva y tipografía controladas manualmente — igual que ya se hace con el título, el autor y el contexto de cada pieza.
- No se acepta como válido ningún texto generado por el modelo de imagen, tampoco el de la propia marca. La excepción "LegalMente sí cuenta" queda eliminada — no hay excepción.

## Por qué esto no cambia el resultado visual buscado

El objetivo original (la marca integrada físicamente en un objeto real, nunca como logo flotante ni marca de agua) se mantiene intacto. Lo único que cambia es *cuándo* se añade la palabra: no dentro del prompt de imagen, sino en el montaje posterior — que es exactamente el mismo paso que ya existe para el título, el autor/fuente y el contexto de cada pieza (ver la sección de tipografía de `legalmente-visual-system` y el documento de Drive "Flujo persistido de carruseles"). Esto unifica el tratamiento de todo el texto de una pieza en un solo lugar del proceso, en vez de dividirlo entre "texto que el generador debe escribir bien" (la marca) y "texto que se monta después" (todo lo demás).

## Qué falta para aplicar esto

1. Editar `legalmente-visual-system` (skill global sincronizada, fuera del alcance de esta fase) para:
   - Eliminar la instrucción de que la palabra "LegalMente" se genere dentro de la imagen.
   - Cambiar la descripción del "objeto de integración de marca" para que describa una superficie reservada vacía, no un texto legible.
   - Actualizar los prompts de ejemplo (incluidos los ya generados en `docs/prompts-48-temas.md`, si se reutilizan) para quitar cualquier instrucción de escribir "LegalMente" dentro de la escena.
2. Confirmar con el fundador si esto requiere ajustar también el flujo de montaje en Canva (probablemente no — ya monta título/autor/contexto de la misma forma).
3. Validar con una pieza de prueba real antes de aplicarlo al lote completo.
