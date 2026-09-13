# Diseño editorial v1 — composición de la pieza

**Fecha**: 2026-09-13 · **Encargo**: «mejora LegalMente en todo lo que puedas, nos falta más diseño artístico» (fundador) · **Estado**: implementado y medido, **pendiente de confirmación del fundador**.

A diferencia de `docs/auditoria-detalle-artistico.md`, este documento **no** transcribe
reglas ya aprobadas: son decisiones de diseño nuevas. Por eso viven en un bloque
aparte de la política visual (`tipografia.ornamentos`, marcado como v1 a confirmar)
y no mezcladas con los parámetros que vienen de la skill.

---

## 1. La regla que gobernó todo

> **Un adorno que desplaza el texto no es un adorno: es un defecto.**

No es retórica. La primera versión de este sistema sangraba la columna de texto
para hacerle sitio a la comilla de apertura. Consecuencia medida sobre la escena
real: el texto ganaba una línea, el bloque de autor bajaba unos 50 px y aterrizaba
sobre el rostro de la escena. El contraste del autor pasó de **3,10:1 a 1,34:1** y
la carga de detalle bajo él, de **1,03× a 1,39×**. El adorno se veía bien y
arruinaba la pieza.

Se corrigió, y ahora está fijado por prueba: con y sin ornamentos, las cajas de
texto y sus medidas de contraste y carga son **idénticas**. Los adornos añaden
diseño y no mueven nada.

---

## 2. Qué se añadió

| Recurso | Qué hace | Cómo evita desplazar el texto |
|---|---|---|
| **Comilla colgante** («…») | La cita se lee como cita. Solo en layouts de cita: un concepto o un mito no se entrecomillan, no son cita de nadie. | La comilla cuelga en el **margen óptico**, fuera de la columna, nunca dentro. El texto conserva toda su medida. Si el margen no da, se apoya en el borde de la columna antes que salirse de la banda visible del feed. |
| **Filete de latón** | Separa la cita de su autor sin caja — la caja opaca está prohibida por la marca. | Se dibuja **centrado en el aire que ya existe** entre bloques. No reserva altura propia. |
| **Versalitas con tracking** en el autor | Un crédito editorial, no una línea suelta. Mayúsculas cerradas se leen como un bloque gris; el tracking las abre. | Las mayúsculas son **de dibujo**: el texto del bloque no se altera (`exact_copy` intacto, comprobado por prueba). |
| **Tracking de display** | El cuerpo grande se cierra levemente, como en cualquier titular compuesto. | Cambia el ancho, no la posición; el corte de línea se recalcula con la métrica real. |
| **Anclaje medido** | El bloque de texto ya no cae siempre arriba. | — |

---

## 3. El anclaje: la decisión que más cambia una pieza

Hasta ahora el texto caía arriba **por omisión, no por criterio**. Ahora se evalúan
las dos posiciones candidatas y gana la que deja el **peor bloque menos malo**:
primero que ninguno caiga sobre la zona cargada de la escena, luego el contraste.

Evaluar la banda entera en promedio no sirve: una banda puede medir bien de media
y aun así dejar el autor justo sobre un rostro. Por eso la evaluación es bloque a
bloque, con las mismas medidas que ya usa el compositor (energía de borde y
contraste WCAG), y viaja en el resultado (`anchor`, `anchor_metrics`).

Sobre la escena de ejemplo el sistema informa de algo útil y honesto: **ninguna de
las dos posiciones es buena** (arriba: peor detalle 1,39× y peor contraste 1,34:1;
abajo: 2,12× y 3,04:1). Esa imagen no tiene una banda limpia lo bastante alta para
cinco líneas más autor. La respuesta correcta no es un adorno: es otro encuadre o
menos copy, y eso lo decide una persona.

---

## 4. El video, igualado con la pieza fija

El render de Remotion usa ahora los mismos recursos, leídos de la misma política:
filete bajo el título, comilla colgante en la frase, versalitas del remate con el
tracking declarado.

Y se **quitó la sombra de texto**, que la medición anterior había demostrado que no
aportaba nada al contraste (variantes con y sin sombra idénticas hasta el tercer
decimal). Medido después del cambio: mediana **17,45:1** igual que antes, y la
fracción bajo el mínimo **mejora** de 0,23 % a 0,18 % — sin el halo, el borde del
glifo es más limpio. El degradado se mantiene: esa misma medición demostró que sí
hace un trabajo real, aunque no el que parecía (calma el fondo bajo el pie).

---

## 5. Qué necesita tu confirmación

1. **Los cinco recursos de arriba**, como sistema. Están en `tipografia.ornamentos`
   y se apagan poniendo ese bloque a `{}` — la pieza vuelve exactamente a como
   estaba, sin tocar código.
2. **Quitar la sombra del video** ya está hecho, respaldado por medida y es
   reversible en una línea.
3. Lo que **no** se tocó porque es decisión de marca: el wordmark de esquina del
   video frente al ADR 0002, y el degradado.

## 6. Cómo verlo

```bash
cd visual && python3 -m unittest test_art_direction -v    # 66 pruebas
python3 scripts/audit-video-legibility.py                 # contraste del video
```
