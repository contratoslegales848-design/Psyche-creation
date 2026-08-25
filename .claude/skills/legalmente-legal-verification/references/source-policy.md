# Política de fuentes

## Jerarquía y su equivalencia con el enum `tipo_fuente` (esquema v4)

| Jerarquía (orden de autoridad) | `tipo_fuente` correspondiente |
|---|---|
| 1. Constitución, ley o reglamento oficial vigente | `NORMA_OFICIAL` |
| 2. Sentencia o fuente judicial oficial | `JURISPRUDENCIA_OFICIAL` |
| 3. Autoridad pública o institución oficial (SAT, registros públicos, ministerios, etc.) | `AUTORIDAD_PUBLICA_OFICIAL` |
| 4. Tratado, obra o publicación académica identificable (autor, título, editorial/año) | `ACADEMICA_IDENTIFICABLE` |
| 5. Fuente secundaria especializada (medio jurídico reconocido, colegio de abogados, blog de despacho, etc.) | `SECUNDARIA_ESPECIALIZADA` |
| 6. Material interno de Drive de LegalMente | `DRIVE_INTERNO` |

`tipo_fuente` es un **enum cerrado** — cualquier otro valor es rechazado por el validador. No se puede inventar un séptimo nivel ni reetiquetar una fuente de nivel 4-5 como si fuera de nivel 1-3 para que "se vea mejor": el validador calcula el techo real de `estado` que esa fuente puede sostener a partir de `tipo_fuente` **y** de una verificación de cuatro condiciones a la vez (ver `claim-packet-schema.md`, sección "Niveles de confianza de fuente" — fail-closed).

**Importante (cerrado en la Fase 1C tras una revisión externa que reprodujo el bypass):** el booleano `verificacion_fuente.origen_oficial_confirmado` **nunca basta por sí solo** para que una fuente alcance Nivel 1. Una compilación privada (Justia, blogs, wikis jurídicas) puede etiquetarse `NORMA_OFICIAL` y marcar `origen_oficial_confirmado: true` — eso no la convierte en oficial. Lo que de verdad decide es que el **hostname real** de la URL coincida, por límite de dominio exacto (no por subcadena), con una lista cerrada de dominios oficiales conocidos, **y** que `texto_exacto_consultado`/`vigencia_comprobada` también sean `true`. Etiquetar mal una fuente, o autoafirmar su verificación sin base real, no cambia ese techo — solo hace que el paquete se rechace por incoherencia si el `estado` declarado lo supera.

**Importante (cerrado en la Fase 1D, ampliado en la Fase 1D.1):** que el hostname sea oficial tampoco basta para que esa fuente respalde **cualquier** país, se presente como **cualquier** organismo, ni emita **cualquier** tipo de fuente. Un único registro cerrado, `references/official-source-registry.json`, fija para cada organismo real: sus hostnames, su nombre canónico y alias, su(s) jurisdicción(es)/ámbito, y los `tipo_fuente` que puede emitir (p. ej. `boe.es` solo `NORMA_OFICIAL` — publica normas, no dicta sentencias). Cada fuente oficial declara `registro_oficial_id` apuntando a esa entrada, y el validador cruza los cuatro (hostname, organismo, tipo, jurisdicción) — una fuente oficial nacional que declare en `jurisdicciones_cubiertas` un país ajeno a su propio organismo, o que se presente como un organismo o tipo de fuente que su hostname real no puede sostener, es rechazada con un error específico, sin importar qué tan convincente parezca el resto del JSON. Las fuentes supranacionales (`eur-lex.europa.eu`) tienen un ámbito explícito propio ("Unión Europea"), nunca un país concreto asumido. Solo las fuentes académicas/secundarias (Nivel 3, techo `APTO_CON_MATICES`, `registro_oficial_id: null` siempre) pueden declarar cobertura de varios países sin esta restricción — precisamente porque nunca pueden sostener por sí solas `APTO_PARA_NARRATIVA`. Ya no hay dos listas manuales paralelas dentro del script: toda esta validación se deriva de un único archivo, para no repetir el error de mantener el mismo control en dos sitios que puedan desincronizarse.

**Importante (cerrado en la Fase 1D.2):** todo lo anterior depende de que el hostname de la URL se calcule sin ambigüedad. Antes, dividir `netloc` a mano dejaba pasar `https://evil.example\@boe.es/falso` como si fuera `boe.es` — un navegador conforme a WHATWG la interpreta como `evil.example` (la barra invertida es separador de host en esquemas especiales). Ahora una única función canónica (`parse_official_url`) rechaza directamente cualquier URL con barra invertida, con userinfo, con espacios o caracteres de control, o con puerto inválido — la ambigüedad entre parsers es en sí misma la señal de fallo, no algo que el validador intente adivinar. Y una fuente oficial **sin URL** (solo `identificador_bibliografico`) nunca alcanza Nivel 1, sin importar qué tan coherentes parezcan `registro_oficial_id`/`organismo_autor`/`verificacion_fuente` entre sí — no hay ningún hostname real que verificar. Sigue siendo estructuralmente válida, capada en Nivel 2/`APTO_CON_MATICES`, con advertencia explícita; las fuentes académicas físicas sin URL no se ven afectadas por esta regla (nunca pasan por el registro oficial).

**Una afirmación con solo fuentes de nivel 4-5 (`ACADEMICA_IDENTIFICABLE`, `SECUNDARIA_ESPECIALIZADA`) nunca puede llegar a `APTO_PARA_NARRATIVA` — como máximo, `APTO_CON_MATICES`.** Una afirmación cuya única fuente sea `DRIVE_INTERNO` no puede llegar a ningún estado apto — Drive es antecedente de investigación, nunca el respaldo final de una pieza publicable.

## Nunca aceptar como fuente

- La memoria del propio modelo ("sé que en la mayoría de países...").
- Otro contenido generado por IA (otro chat, otro documento producido por un modelo sin cita primaria).
- Publicaciones sin origen identificable (memes legales, capturas de pantalla sin fuente).
- Imágenes con texto sin una fuente citable detrás.
- Una cita viral atribuida a alguien sin obra o discurso identificable — ver `blocked-content.md` para el procedimiento sobre citas ya investigadas en el proyecto.

## Qué necesita cada fuente en el paquete

Ver el esquema completo del objeto FUENTE en `claim-packet-schema.md`. En resumen: `id`, `tipo_fuente` (del enum cerrado), `titulo`, `organismo_autor`, `fecha_consulta` (ISO), `localizador` (artículo/página/sentencia/sección concreta — nunca "la ley en general"), `jurisdicciones_cubiertas` (qué países respalda de verdad — una fuente española nunca cubre automáticamente a México), `registro_oficial_id` (para fuentes oficiales, el id de su entrada en `references/official-source-registry.json`; `null` para académicas/secundarias/Drive), `verificacion_fuente` (origen/texto/vigencia, ver abajo), y **o bien** `url` (http/https) **o bien** `identificador_bibliografico` (ISBN, editorial, edición, año — para fuentes físicas sin URL, perfectamente válido).

Que el dominio sea oficial no demuestra que el artículo citado diga lo afirmado ni que siga vigente — por eso `verificacion_fuente` separa explícitamente **identidad del organismo**, **acceso al texto exacto**, y **vigencia verificada**, cada una con su propia fecha y evidencia. Si el acceso al texto oficial estuvo bloqueado (p. ej. `WebFetch` no disponible en el entorno), la fuente **no puede sostener `APTO_PARA_NARRATIVA`** — debe quedar como pendiente de investigación/verificación, y esa limitación se declara en `observaciones`, nunca se omite.

## Citas de autor/figura reconocible

Una cita atribuida a una persona necesita obra, discurso o entrevista identificable donde se pronunció — no basta con que "circule" atribuida a esa persona en redes o compilaciones. Un claim de `tipo: atribucion` con `alcance: NO_APLICA` es la forma correcta de modelar esta verificación (ver `claim-packet-schema.md`). Antes de dar una cita por buena, cruzarla contra `blocked-content.md` y contra los documentos vigentes de Drive.
