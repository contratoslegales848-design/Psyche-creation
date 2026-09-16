# Registro de fuente #5 (Memoria fuerte) — Contrato v4, 16-sep-2026

Fuente registrada: **"LegalMente — Memoria fuerte: piezas validadas por el
Founder y video real (fuente #5, Contrato v4)"**
<https://docs.google.com/document/d/1s4YUmSgBsEwYziXA5EaTG2qvo21qMuWTND-nlFAhhd8/edit>
(Drive, misma carpeta que el Índice maestro v18 y el Contrato v4).

Este documento cierra el hueco que el propio Contrato v4 (sección 2)
señalaba: la fuente de precedencia #5 ("Historial real de piezas aprobadas y
publicadas: memoria fuerte") no existía como documento independiente. El
contenido de la fuente #5 se cita aquí **verbatim** donde el registro lo
exige — no se reinterpreta, resume con pérdida ni generaliza: son hechos
verificados por el Founder, no hipótesis de estilo.

## PROBLEMA

El Contrato v4 (`LegalMente — 00 RUTA ACTIVA DE ARTE — Contrato de
generación visual v4`, sección 2, ítem 5) exige comparar cada pieza nueva
contra "Historial real de piezas aprobadas y publicadas: memoria fuerte"
como fuente #5 de precedencia — antes de este registro, esa fuente no tenía
documento propio, y el selector/compilador del motor visual no tenía ningún
dato real con el que ejecutar esa comparación.

## EVIDENCIA

1. El documento de fuente #5 ya existe en Drive (creado 16-sep-2026, ID
   `1s4YUmSgBsEwYziXA5EaTG2qvo21qMuWTND-nlFAhhd8`) y contiene: ranking real
   de Facebook (15-sep-2026, ~116 publicaciones), piezas históricas de mayor
   impacto con cifras (Carnelutti, Onassis, Calamandrei), layout/texto
   validados, 7 rechazos explícitos del Founder, 4 validaciones explícitas,
   y el estándar real de video (Grok, clips ~6s con audio, pipeline ffmpeg,
   y el fallo real de un Reel publicado sin sonido).
2. `visual/art_direction.py::draft_visual_brief()` — el selector/compilador
   real que traduce un `TopicCandidate` en dirección artística — recibe
   `catalogo_maestro` (`visual_fingerprint.MasterCatalog`), `memoria_huellas`
   (`visual_fingerprint.FingerprintMemory`, anti-repetición de huella
   reciente) y, opcionalmente, `memoria_visual`
   (`memory.VisualMemory`, sólo para elegir superficie de marca). Ninguno de
   los tres parámetros referencia `semantic_memory.SemanticMemory` ni ningún
   dato de la fuente #5 (líneas 227-276 de ese archivo).
3. `visual/semantic_memory.py` SÍ define un mecanismo estructural de
   "memoria fuerte" (`MEMORIA_FUERTE = (APROBADA, PUBLICADA,
   PRESELECCIONADA)`, con ventanas de cooldown más amplias que `GENERADA`) —
   pero es un mecanismo de estados y huellas semánticas, vacío por defecto:
   `production_run.py:267` y todos los demás llamadores instancian
   `SemanticMemory()` sin argumentos, sin cargar ningún registro persistido
   de las piezas reales que aprobó/publicó el Founder.
4. Búsqueda exhaustiva (`grep -r` sobre `visual/`) de `APROBADA|PUBLICADA|
   rendimiento_real|Facebook|founder_metrics|ajuste_afinidad_founder|
   memoria_fuerte` no devuelve ningún punto donde el código lea el ranking
   real de Facebook, los nombres de piezas (Carnelutti/Onassis/Calamandrei),
   ni las reglas cualitativas de rechazo/validación de las secciones 4 y 5
   de la fuente #5.
5. `founder_metrics.py` mide tasa de selección del Founder por eje sobre lo
   que el propio sistema generó y clasificó — no ingiere el ranking externo
   de Facebook ni las reglas cualitativas de la fuente #5.

## HIPÓTESIS

El selector/compilador no compara contra memoria fuerte real porque nunca
existió una fuente de datos real que ingerir: `SemanticMemory` es la
infraestructura correcta para la señal fuerte/corta, pero (a) no hay
pipeline que convierta la fuente #5 (ranking, rechazos, validaciones) en
`MemoryEntry`, y (b) `draft_visual_brief()` no acepta un parámetro de
`SemanticMemory` en absoluto — aunque existiera el pipeline de ingestión, el
selector no tiene el gancho para consultarlo antes de generar.

## CAMBIO

Ninguno en código. Por mandato explícito de esta tarea ("no la implementes
sin autorización de merge/deploy") y por CLAUDE.md §6 ("generar nunca
equivale a publicar"), esta brecha se documenta como **bloqueador abierto**,
no se implementa. Ver "Brecha detectada" más abajo para el diseño que
requeriría autorización antes de escribirse.

## PRUEBA

Lectura completa de `visual/art_direction.py`, `visual/semantic_memory.py`,
`visual/production_run.py` y `grep` exhaustivo sobre `visual/` confirmando
ausencia de cualquier referencia a los datos reales de la fuente #5 (ver
Evidencia, puntos 2-5). Sin ejecución de código: este registro es
documental, no altera comportamiento del motor.

## RESULTADO

Fuente #5 registrada como vigente (este documento + adenda de Bitácora en
Drive, ver más abajo). Brecha del selector documentada con precisión de
archivo/línea. Checklist QA obligatorio (secciones 4 y 5 de la fuente,
verbatim) queda disponible para el QA visual de cualquier lote nuevo desde
hoy, como verificación **humana** — no automatizada — hasta que la brecha se
cierre con autorización expresa.

## DECISIÓN

Registrar, documentar la brecha, no implementar sin autorización. Bloqueado
para automatización; no bloquea el uso humano del checklist en el QA de
cada lote.

---

## Registro en "00 LEER PRIMERO" y en el Contrato v4 §2 — limitación de herramienta

Se leyó el contenido completo de ambos documentos de Drive antes de proponer
cualquier cambio:

- `LegalMente — 00 LEER PRIMERO — Motor único para agentes, contenido e
  imágenes` (ID `1Aby_uhs_cuHJCsszKbyveN13qFzbG9gMSLzEoELRabA`).
- `LegalMente — 00 RUTA ACTIVA DE ARTE — Contrato de generación visual v4`
  (ID `1lRWHheyLHuTbPC6oTi3QESHquc45vWQ4v4qgyBsGEYE`), sección 2, ítem 5.

Las herramientas de Google Drive disponibles en esta sesión (`search_files`,
`read_file_content`, `download_file_content`, `create_file`, `copy_file`,
`update_file` — sólo título/carpeta —, `share_file`, `trash_file`) no
incluyen edición del **cuerpo** de un Google Doc existente: no hay
operación de inserción/reemplazo de texto sobre un documento ya creado. Por
eso el enlace no pudo escribirse directamente dentro de "00 LEER PRIMERO" ni
del Contrato v4 §2 en esta sesión — no es una decisión de alcance, es un
límite real de herramienta, y se reporta así en vez de simular la edición.

En su lugar se creó, como adenda (aditivo, no sustituye ni borra nada):

**`LegalMente — Bitácora — Adenda 16-sep-2026: registro de fuente #5
(Memoria fuerte, Contrato v4)`** — Drive, misma carpeta que el Contrato v4 y
el Índice maestro v18. Esa adenda:

1. Registra la fuente #5 como vigente y enlaza el documento de memoria
   fuerte.
2. Transcribe el texto exacto propuesto para insertarse en cada documento,
   listo para pegar por el Founder o por una sesión con capacidad de editar
   el cuerpo de Google Docs:

   - **Para "00 LEER PRIMERO"**, como nuevo bloque fechado al final del
     documento (seguir el mismo patrón de "ACTUALIZACIÓN 8 SEP 2026 —
     CALIDAD VISUAL"):

     > ACTUALIZACIÓN 16 SEP 2026 — FUENTE #5 (MEMORIA FUERTE) REGISTRADA
     >
     > La fuente #5 de precedencia del Contrato v4 ("Historial real de
     > piezas aprobadas y publicadas: memoria fuerte") ya tiene documento
     > propio: `LegalMente — Memoria fuerte: piezas validadas por el
     > Founder y video real (fuente #5, Contrato v4)`. Antes de aprobar
     > cualquier lote nuevo, comparar contra su sección 1 (qué rindió mejor
     > de verdad) y su sección 4 (qué ya fue rechazado). El selector real
     > del motor de código (`visual/art_direction.py`) todavía NO consulta
     > esta fuente de forma automática — brecha registrada como
     > bloqueador abierto en `docs/memoria-fuerte-fuente-5-registro-2026-09-16.md`
     > del repositorio Psyche-creation; la verificación contra esta fuente
     > es, por ahora, responsabilidad humana en el QA visual.

   - **Para el Contrato v4, sección 2, ítem 5** (reemplazar únicamente esa
     línea, conservando la numeración):

     > 5\) Historial real de piezas aprobadas y publicadas: memoria fuerte
     > — ver `LegalMente — Memoria fuerte: piezas validadas por el Founder
     > y video real (fuente #5, Contrato v4)`:
     > <https://docs.google.com/document/d/1s4YUmSgBsEwYziXA5EaTG2qvo21qMuWTND-nlFAhhd8/edit>.

3. Sigue el formato PROBLEMA → EVIDENCIA → HIPÓTESIS → CAMBIO → PRUEBA →
   RESULTADO → DECISIÓN, igual que los demás registros de Bitácora del
   proyecto.

## Brecha detectada — bloqueador abierto (no implementado)

**No implementar sin autorización expresa de merge/deploy.** Diseño
propuesto únicamente para que quede documentado qué haría falta, no como
instrucción de ejecución:

1. Un módulo de ingestión (`visual/memoria_fuerte.py`, no creado) que lea la
   fuente #5 (manual o vía un export estructurado que el Founder autorice) y
   produzca `MemoryEntry` con `estado=APROBADA`/`PUBLICADA` para las piezas
   nombradas en su sección 1 y 2 (con las cifras de Facebook como
   metadato, no como override de gates jurídicos).
2. Un segundo módulo o extensión de `art_direction.py::draft_visual_brief()`
   que acepte un parámetro `memoria_fuerte` (`SemanticMemory` poblada) y
   compare el candidato contra sus entradas antes de fijar la dirección
   artística — hoy `draft_visual_brief()` no tiene ese parámetro.
3. Una verificación cualitativa (no sólo de huella) contra las reglas
   textuales de las secciones 4 y 5 de la fuente #5 (paletas, técnicas y
   composiciones nombradas explícitamente) — esto no es un chequeo de
   `visual_fingerprint` por dimensión, porque los rechazos del Founder son
   afirmaciones en lenguaje natural, no coordenadas del catálogo maestro.
   Requiere diseño propio, distinto de la anti-repetición existente.

Hasta que el Founder autorice este trabajo, la verificación contra la
fuente #5 se hace **humanamente**, con el checklist de la siguiente sección.

## QA visual obligatorio — secciones 4 y 5 de la fuente #5 (verbatim)

Fuente: `LegalMente — Memoria fuerte: piezas validadas por el Founder y
video real (fuente #5, Contrato v4)`,
<https://docs.google.com/document/d/1s4YUmSgBsEwYziXA5EaTG2qvo21qMuWTND-nlFAhhd8/edit>.
Este checklist se suma al QA visual ya vigente (Contrato v4 §7, 10 motivos
de rechazo) — no lo sustituye. Es de aplicación humana obligatoria en cada
lote nuevo hasta que exista automatización autorizada (ver brecha arriba).

### RECHAZAR si la pieza coincide con cualquiera de estos rechazos ya confirmados por el Founder (Contrato v4 fuente #5, sección 4)

1. Paleta "limpia" inventada (azul tinta #0d1826 + teal + ámbar + oro) —
   rechazada, "fea"/"asquerosa".
2. Fotografía hiperrealista con 4 capas de texto (máximas, hitos
   históricos, ciencia, naturaleza, símbolos, literatura) — rechazada: "no
   me gustaron, no me gustan para mi página".
3. Escenas de objeto/metáfora fría sin figura humana con emoción real
   (manos, puertas, cadenas) — rechazadas: "horribles"/"basura", indignas
   de la página.
4. Flat illustration en colores bold — rechazada: "feo y simple sin llamar
   a la interacción".
5. Sepia monocromo plano y negrura murky ilegible — rechazados de forma
   permanente.
6. Prompts con "negative space upper/lower band" — rechazados porque
   generan bandas/recuadros separados; reemplazados por la regla full-bleed.
7. Formato collage/grid multipanel como sustituto de piezas individuales —
   rechazado.

### VERIFICAR que la pieza sea compatible con lo ya validado positivamente (Contrato v4 fuente #5, sección 5) — confirmación explícita, no sólo ausencia de rechazo

1. Formato surrealista estructurado (fusión de partes del cuerpo humano con
   objetos jurídicos, estructura Título/Frase/Remate) — el Founder confirmó
   "me gustaron" y pidió una segunda tanda en el mismo estilo.
2. Citas reales incorporadas de @perillo_ius: Luigi Lucchini ("La culpa y
   no la inocencia debe ser demostrada") y José Cafferata Nores ("Son las
   pruebas, no los jueces, los que condenan") — usadas y formalizadas en el
   lote surrealista final.
3. Pieza del Poder Notarial ("Un poder mal dado abre todas tus puertas") —
   producida con éxito como imagen; el Founder decidió animarla en video.
4. Reel "El primer mandamiento del abogado: estudiar" (cita de Eduardo
   Couture) — elegido por el Founder como primer Reel para impulsar con
   pauta paga real.

### Referencia de layout/texto validados (sección 3, contexto para el revisor humano)

Full-bleed sin marco; texto CONTENIDO (nunca "HUGE capitals"): título
mediano en serif (dos líneas cortas), subtítulo en cursiva fina, autor en
letras pequeñas espaciadas, wordmark mediano abajo. Regla explícita del
Founder citada en la fuente: "el texto ocupa solo una porción modesta del
marco; la pintura sigue siendo la protagonista".

### Estándar de video (sección 6, cuando el lote incluya video)

Herramienta vigente: Grok (no Veo/Gemini). Clips ~6s con audio,
consolidados por pipeline ffmpeg (concat hard-cut + crossfade de audio +
normalización de volumen), vertical 9:16. Regla derivada del fallo real
confirmado por el Founder (Reel sin sonido publicado vía Manus en
Instagram): **ningún video se publica sin verificar que el audio esté
presente.**
