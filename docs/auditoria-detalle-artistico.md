# Auditoría de detalle artístico — pipeline visual

**Fecha**: 2026-09-13 · **Alcance**: `visual/` (política, familias, compilador, tipografía, compositor, inspección) y `src/` (render de video Remotion) · **Resultado**: 42 hallazgos; 33 corregidos en código, 9 abiertos. De los abiertos, dos dejaron de ser opiniones y pasaron a ser medidas: el contraste del video (§3.8) y el texto sobre zonas cargadas (T10).

No es una propuesta ni una asesoría: es el registro de lo que se auditó, lo que se
arregló y lo que quedó abierto. La regla que gobernó toda la auditoría:

> Ninguna regla artística nueva se inventó aquí. Todo lo que ahora comprueba el
> código estaba ya aprobado en la skill `legalmente-visual-system` (§3 núcleo de
> marca, §4 motor de rotación, §5 checklist de rotación, §6 tipografía) y en la
> política visual. Lo que faltaba era que fuera **comprobable**, no que existiera.

Versiones tras la auditoría: política visual **1.2**, registro de familias **1.1**,
compilador de prompt **2.1**, compositor **1.2**, esquema de memoria visual **1.1**.

---

## 1. El patrón del fallo

El pipeline sabía comprobar que una pieza estaba **autorizada** (gate jurídico,
procedencia, hashes, `exact_copy` inmutable, marca no degradada a watermark). No
sabía comprobar nada de lo que hace que una pieza **se vea bien**. Los defectos de
arte no rompían ninguna prueba: salían en la imagen.

Tres formas concretas de ese patrón, y las tres se repetían:

1. **Parámetros aprobados que vivían solo en prosa.** La zona segura real del feed,
   los escalones de cuerpo, el contraste mínimo y el máximo de líneas estaban
   escritos en la skill y no existían en el código; en su lugar había números
   redondos inventados (8 % de margen, 96/78/60/46 px, piso 34 px para todo).
2. **Prohibiciones declaradas en el prompt negativo mientras el positivo las
   pedía.** Un brief cuyo `subject` fuera "una balanza de bronce" compilaba sin
   problema: el negativo decía "balanza de la justicia" y el generador obedecía a
   la descripción positiva.
3. **Reglas centrales de la marca que el código no conocía.** "UNA sola escuela
   por pieza" es la corrección más importante de la skill §4 — el error que aplanó
   el feed — y no existía ni el campo donde declararla.

---

## 2. Hallazgos corregidos

### Tipografía (skill §6 → política `tipografia`)

| # | Hallazgo | Estado antes | Corrección |
|---|---|---|---|
| T1 | **Zona segura inventada.** Margen uniforme del 8 % (y 153–1766) frente a la zona medida del feed (y 290–1630 sobre 1080×1920, el feed recorta ~240 px arriba y abajo). El texto se colocaba dentro de la franja recortada. | `composition.SAFE_AREA_RATIO` | `composition.safe_area_para()` lee `tipografia.zona_segura_declarada` y escala a cualquier lienzo de la misma relación. El plan declara el origen (`politica` / `ratio_por_defecto`). |
| T2 | **Escalones de cuerpo no aplicados.** 96/78/60/46 px con piso 34 frente a la tabla aprobada (≤80 car. → 68–96; 81–140 → 60–82; secundario → 34–44). | números en `build_typography_plan` | `composition.escalon_para()` lee la tabla de la política. |
| T3 | **El cuerpo principal podía caer a tamaño de pie de foto.** El compositor reducía todos los bloques hasta un único piso de 34 px. | `plan.minimum_readable_size` único | Cada `TextBlock` lleva su `min_size_px`; el compositor respeta el piso de cada bloque. |
| T4 | **Máximo de 6 líneas: no existía.** | — | El plan reduce hasta el mínimo aprobado para cumplirlo y, si no lo consigue, lo señala (`EXCEDE_MAXIMO_DE_LINEAS`). Nunca acorta el texto. |
| T5 | **Contraste mínimo 4,5:1 nunca medido.** Se pintaba marfil sobre lo que hubiera debajo. | — | `compositor.contraste_sobre_region()`: WCAG 2.1 real, celda a celda (8×4), medido **antes** de dibujar. Por debajo del mínimo → `TEXT_CONTRAST_BELOW_MINIMUM` y revisión humana. **No se pinta caja opaca**: la skill exige resolverlo con la luz de la escena. |
| T6 | **Colores fuera de la paleta declarada.** `(252,250,242)` y `(197,160,89)` escritos a mano en el rasterizador. | literales | Derivados de `paleta.requerida` vía `tipografia.colores_por_rol`. Coinciden exactamente con los anteriores: el arreglo es que ahora *no pueden derivar*. |
| T7 | **Líneas huérfanas sin control.** Última línea de una sola palabra. | — | Reparto por caja más estrecha (hasta −30 %, una línea extra si cabe en el máximo). El texto no se toca; si no hay reparto, se señala. |
| T8 | **Texto sobre el objeto de marca.** Prohibido por la skill §6, no se comprobaba. | — | Colisión de rectángulos en el compositor → `TEXT_OVER_BRAND_SURFACE`, que la auditoría trata como bloqueo. |
| T9 | **Texto fuera de la banda visible del feed.** Sin comprobación. | — | `formatos.VERTICAL_9_16.zona_visible_tras_recorte` + `TEXTO_FUERA_DE_LA_ZONA_VISIBLE` (bloqueo). |
| T10 | **Texto sobre rostros, manos decisivas o el objeto de la revelación.** La skill lo prohíbe y reconocerlos exige visión, que no hay. | — | Se mide lo que sí se puede: la **energía de borde** bajo cada bloque comparada con la de la imagen entera. Un rostro, unas manos o el objeto de la revelación son casi siempre lo más cargado del encuadre. Por encima de 1,35× → `TEXT_OVER_BUSY_AREA` y revisión humana. Medido **antes** de dibujar (si no, el propio texto dispararía el aviso en toda pieza) y siempre relativo, nunca absoluto. Comprobado contra el fotograma real de la pieza de ejemplo: 0,31× donde hoy cae el texto, 1,68× en la franja del rostro donde caería un copy largo. |

### Dirección de arte (skill §3, §4, §5 → política `direccion_de_arte`, `escuelas`)

| # | Hallazgo | Corrección |
|---|---|---|
| D1 | **El prompt negativo no salva una escena que pide el recurso quemado.** | `art_direction` detecta los términos quemados en la descripción **positiva** del brief y **bloquea antes de llamar al proveedor** (`ARTE_BLOQUEADO`, 0 llamadas, 0 créditos). |
| D2 | **Los recursos quemados solo llegaban vía `forbidden_tropes` de algunas familias**: una familia que no listara "balanza" la dejaba pasar. | La lista de la política entra en los negativos de **todos** los prompts. |
| D3 | **"UNA sola escuela por pieza" no existía en el código.** | Campo `VisualBrief.escuela`, banco de 30 escuelas (carril A/B) en la política, validación de escuela única y perteneciente al banco, y rotación de 5 piezas (`rotation.verificar_rotacion_de_escuela`). |
| D4 | **Mezcla de carriles** (A pictórico / B fotográfico) sin control. | `CARRILES_MEZCLADOS` al cruzar el carril de la escuela con el de la familia. |
| D5 | **Mecanismo de revelación ausente.** El fenómeno físico que hace visible la idea es "el argumento visual" (§5.3) y no existía como dato. | Campo `mecanismo_revelacion`, insertado en el prompt antes de la cámara; ausencia → revisión humana. |
| D6 | **Presencia humana sin control.** "Nunca rostro completo ni cuerpo entero salvo excepción justificada". | Bloqueo si la escena los menciona sin `justificacion_presencia_humana`. |
| D7 | **Las familias solo proponían entornos jurídicos** (despacho, archivo, biblioteca), justo lo contrario de §5.2. | Cada familia declara `everyday_environments`; un entorno jurídico produce aviso con alternativas concretas. |
| D8 | **Superficie de marca repetida** ("no repetir siempre el sello de lacre"). | Aviso con ventana de 5 piezas. |
| D9 | **El prompt describía QUÉ hay en la escena, no CÓMO está hecha.** | Registro de familias 1.1: profundidad de campo, acabado de superficie, firma de imperfección, temperatura de color, curva de contraste, sesgo de composición y grano. El compilador 2.1 los inserta como bloque de "Detalle artístico". |
| D10 | **Superficies de marca de la skill que la política no admitía**: ex libris, filigrana al trasluz, marca de fuego, sello seco, monograma bordado, canto grabado de moneda. | Añadidas. |
| D11 | **Prohibiciones faltantes**: mosaico, iconos de call to action, texto ilegible, texto inventado. | Añadidas a `composicion.prohibido`. |
| D12 | **La clave de luz podía quedar sin declarar** pese al núcleo de marca ("una sola fuente dramática justificada en la escena"). | Revisión humana si no la declara ni el brief ni la familia; el prompt dice explícitamente "una sola fuente dramática justificada dentro de la escena". |

### Marca compuesta

| # | Hallazgo | Corrección |
|---|---|---|
| M1 | **La marca se pegaba como texto plano.** Una palabra plana sobre una placa delata el montaje; lo que hace creíble la integración física es el canto. | Grabado determinista: sombra del corte arriba-izquierda, luz del bisel abajo-derecha, ambas derivadas del mismo latón de la paleta. Desplazamiento en función del cuerpo, reproducible. |
| M2 | **La marca podía quedar ilegible sobre su superficie** (latón sobre latón). | Contraste WCAG medido sobre la superficie reservada → `BRAND_CONTRAST_BELOW_MINIMUM` + revisión humana. No se recolorea la marca ni se añade caja. |
| M3 | **La marca podía caer en la franja que el feed recorta.** | `BRAND_SURFACE_OUTSIDE_VISIBLE_AREA`. |
| M4 | **La marca solo se componía de frente.** Cualquier placa girada más de 3° o vista en ángulo se rechazaba: la integración física quedaba limitada a superficies que miran a cámara, que es justo lo que hace que una marca parezca pegada. | La superficie se declara como rectángulo, como rectángulo con ángulo o como sus **cuatro esquinas reales**; la marca se graba en una capa plana y se lleva a ese plano con una transformación en perspectiva (solucionador de 8 coeficientes en Python puro, sin añadir dependencias). Un quad mal formado, contradictorio (`flat=False`) o sin área **no degrada al rectángulo**: se rechaza. Sigue sin haber visión: las esquinas las declara una persona. |

### Render de video (`src/`, skill §3 y §6)

El render de Remotion llevaba su propia tipografía y su propia paleta, sin
relación con la política visual. Se verificó renderizando fotogramas reales
antes y después (`npx remotion still`), no solo leyendo el código.

| # | Hallazgo | Corrección |
|---|---|---|
| V1 | **El título y el remate se publicaban recortados.** Padding de 130 px arriba y 90 abajo, dentro de la franja de ~240 px que el feed corta. Comprobado en el fotograma: el título arrancaba en y≈130. | `src/brandTypography.ts` deriva la zona segura de la política (80 / 290 / 1000 / 1630) y el render la usa como padding. |
| V2 | **Paleta propia del video**: `#F4EBD8`, `#E6C879`, `#100d0b`, ninguno de la paleta institucional. El video y la imagen fija de la misma marca no se parecían. | Colores leídos de `paleta.requerida` (marfil editorial, latón viejo, nogal profundo). |
| V3 | **Cuerpos por debajo del mínimo declarado**: remate a 25 px (mínimo 34 para autor/fuente) y frase a 44 px. | Cuerpos derivados de `tipografia.escalones_principal` y `tipografia.secundario`. El hook conserva la proporción del diseño ya en uso; el segundo nivel nunca baja del máximo secundario. |

`src/brandTypography.ts` **importa el JSON de la política**: no puede desviarse
de ella sin que el typecheck lo vea.

### Píxeles (política `paleta`)

| # | Hallazgo | Corrección |
|---|---|---|
| P1 | **"Negros sin detalle" y "pieza excesivamente oscura" están prohibidos en la política y nadie los medía** sobre la imagen: solo había luminancia media y near-black. | `inspection.ArtDetailInspector`: ratio de negro empastado y de altas luces quemadas, rango tonal (p95−p05). |
| P2 | **El acento frío obligatorio se exigía declarar en el brief y no se comprobaba en la imagen.** | `cold_accent_ratio` contra los anclajes de azul petróleo → `COLD_ACCENT_ABSENT`. |
| P3 | **Adherencia a la paleta institucional sin medir.** | `palette_adherence` por distancia a los 8 anclajes. |
| P4 | **El decodificador PNG propio no leía JPEG ni otros modos de color**, pese a que Pillow ya es dependencia (ADR 0003). | El inspector nuevo usa Pillow; el antiguo se conserva para entornos sin dependencias. |

Ninguna medida de píxeles rechaza por sí sola: todas escalan a revisión humana.

---

## 3. Lo que la auditoría dejó abierto (decisión humana)

1. **`LM-PIEZA-01-REALES` no es componible con la tipografía aprobada.** Su
   `exact_copy` tiene 262 caracteres: fuera de la tabla (máximo declarado 140) y
   10 líneas frente a un máximo de 6. Las salidas posibles son carrusel,
   reencuadre u **acortar el texto en la fuente** — y esto último exige volver a
   pasar verificación jurídica, porque cambia una afirmación aprobada. El código
   no elige ninguna: lo señala y se detiene.
   Reproducible con `cd visual && python3 cli.py audit-art`.
2. **Ninguna pieza declara todavía escuela ni mecanismo de revelación.** Los
   campos son nuevos; hasta que se rellenen, la auditoría dice "no se puede
   comprobar", que no es lo mismo que "cumple".
3. **Los umbrales de paleta son provisionales.** No existe arte real generado por
   un proveedor real contra el que calibrarlos. Se fijaron conservadores y
   quedan anotados como tales en la política.
4. **`SOCIAL_4_5` no tiene zona segura medida en el feed.** Se usa el margen
   proporcional por defecto y el plan lo declara. No se inventó una medida.
5. **Perspectiva de marca**: resuelto para superficies planas declaradas (ver
   M4) — recta, girada o en perspectiva por sus cuatro esquinas. Lo que sigue
   abierto es lo que no es un plano: un lacre con relieve, una botella, una
   tela. Ahí no hay transformación honesta y la pieza va a revisión humana.
   Tampoco hay visión que deduzca la geometría mirando la imagen.
6. **No hay comprensión visual.** Manos con seis dedos, collages, si la marca
   está *bien* integrada: nada de eso lo ve este código, y no se finge que sí.
7. **La marca en el video es un wordmark de esquina.** `LegalMenteQuote` dibuja
   "LegalMente" en gótico abajo a la derecha. Eso es exactamente el
   "branding de esquina ajeno a la escena" que la política prohíbe y que el ADR
   0002 resolvió para la imagen fija (superficie física reservada + composición
   determinista). El video no declara superficie reservada. **No se tocó**: o se
   declara una excepción expresa para video, o el video adopta el mismo esquema.
   Es decisión del fundador, no del código.
8. **El degradado y la sombra del video: medidos, y hacen otra cosa de la que
   parecía.** La pregunta era si el margen de contraste lo daba la luz de la
   escena o las dos muletas. Se midió la misma escena y el mismo fotograma en
   tres variantes:

   | Variante | mediana | p05 | bajo 4,5:1 | detalle bajo el bloque inferior |
   |---|---|---|---|---|
   | A · como está (degradado + sombra) | 17,45:1 | 8,05:1 | 0,23 % | 1,20× |
   | B · sin degradado | 16,93:1 | 7,96:1 | 0,40 % | **1,42×** |
   | C · sin degradado ni sombra | 16,93:1 | 7,96:1 | 0,36 % | 1,42× |

   Tres lecturas:
   - **Para el contraste, el degradado aporta medio punto de mediana**: el
     margen lo da la luz de la propia escena, que es exactamente lo que §6 pide.
   - **La sombra de texto no aporta nada medible** (B y C son idénticas hasta el
     tercer decimal). Es la muleta que podría irse sin perder legibilidad.
   - **El degradado sí hace un trabajo real, pero otro**: calma el fondo bajo el
     remate y la marca. Sin él, esa banda pasa de 1,20× a 1,42× el detalle medio
     de la imagen y cruzaría el umbral de "texto sobre la zona más cargada"
     (T10). No sostiene el contraste: sostiene el silencio visual del pie.

   Reproducible: quitar el `AbsoluteFill` del degradado y/o el `textShadow` en
   `src/compositions/LegalMenteQuote.tsx` y volver a correr
   `python3 scripts/audit-video-legibility.py`.

   **Límite de esta medida**: una sola escena, porque `assets/images/` solo tiene
   la imagen de ejemplo. Sobre una imagen clara el degradado podría ser
   estructural. Por eso la medida corre por pieza y no una vez para siempre.
   Qué hacer con las dos muletas sigue siendo decisión del fundador: cambia el
   aspecto de todas las piezas.
9. **El texto del video se ancla arriba sin saber qué hay debajo.** Con copy
   largo cae sobre el rostro de la escena, y §6 prohíbe poner texto sobre
   rostros o manos decisivas. Comprobado en el fotograma de prueba con 262
   caracteres. La imagen fija ya lo detecta por densidad de detalle (T10); el
   render de video **no**, porque no compone por bloques medibles sino por
   layout de CSS. Trasladar esa medida al video es trabajo pendiente; hoy lo
   evita el copy corto. Reconocer el rostro en sí sigue exigiendo visión.
10. **El asset de ejemplo acumula cuatro recursos quemados.**
    `assets/images/ejemplo.jpg` tiene balanza, mazo, columnas y un hombre solo
    ante un escritorio. Es `EJEMPLO_TECNICO` y no publicable, pero es el modelo
    que cualquiera copia al crear su primera pieza.

---

## 4. Cómo se ejercita

```bash
cd visual
python3 -m unittest test_art_direction -v     # 49 pruebas del detalle artístico
python3 -m unittest discover -p "test_*.py"   # 405 pruebas
python3 cli.py audit-art                      # auditoría sobre todo content/
python3 cli.py audit-art --asset ../artifacts/human-review/LM-PIEZA-01-REALES/gen-2f2dfb9c6f2f.png
```

Y para el video:

```bash
npm run typecheck
python3 scripts/audit-video-legibility.py            # contraste real, medido
python3 -m unittest -v scripts.test_audit_video_legibility  # desde scripts/
```

`audit-video-legibility.py` renderiza dos veces cada composición —con texto y
con el texto vacío— y compara: los píxeles que cambian y coinciden con un color
de la paleta son el trazo, y el segundo fotograma es el fondo exacto que tienen
debajo. La sombra de texto y el antialias quedan fuera a propósito: contarlos
maquillaría la medida. Corre en el workflow de render, donde ya hay Chromium.

`audit-art` sale con código 1 si hay algún BLOQUEA, y corre en CI. Una auditoría
sin bloqueos **no** es una aprobación: la aprobación visual sigue siendo humana,
como el resto del pipeline.
