# Política de fuentes

## Jerarquía, de mayor a menor autoridad

1. Constitución, ley o reglamento oficial vigente.
2. Sentencia o fuente judicial oficial.
3. Autoridad pública o institución oficial (SAT, registros públicos, ministerios, etc.).
4. Tratado, obra o publicación académica identificable (autor, título, editorial/año).
5. Fuente secundaria especializada (medio jurídico reconocido, colegio de abogados, etc.).
6. Material interno de Drive de LegalMente — únicamente como antecedente de investigación previa, nunca como fuente final de una afirmación jurídica nueva.

Una afirmación con fuente de nivel 1-3 puede llegar a `APTO_PARA_NARRATIVA` o `APTO_CON_MATICES`. Una afirmación que solo alcanza nivel 4-5 normalmente queda en `APTO_CON_MATICES` como máximo, con nota explícita del nivel de fuente. Una afirmación que solo tiene nivel 6 (Drive) como respaldo no está verificada — trátala como `REQUIERE_INVESTIGACION`.

## Nunca aceptar como fuente

- La memoria del propio modelo ("sé que en la mayoría de países...").
- Otro contenido generado por IA (otro chat, otro documento producido por un modelo sin cita primaria).
- Publicaciones sin origen identificable (memes legales, capturas de pantalla sin fuente).
- Imágenes con texto sin una fuente citable detrás.
- Una cita viral atribuida a alguien sin obra o discurso identificable — ver `blocked-content.md` para el listado de citas ya detectadas como mal atribuidas en este proyecto.

## Qué necesita cada fuente en el paquete

Cada entrada de `fuentes` en el paquete de verificación necesita, como mínimo:

- `titulo`: nombre exacto del instrumento, sentencia, obra o publicación.
- `organismo_autor`: quién lo emitió o escribió.
- `url`: enlace verificable. Si la fuente no tiene URL pública (p. ej. un libro físico), usar una identificación suficiente (ISBN, editorial + año + página) en su lugar — pero el campo no puede quedar vacío ni decir solo "internet" o "búsqueda general".
- `fecha_consulta`: cuándo se verificó, no cuándo se publicó el instrumento.
- `tipo_fuente`: uno de los 6 niveles de la jerarquía de arriba.

Una fuente sin URL ni identificación suficiente se trata como fuente inválida — el script de validación estructural la rechaza (ver `scripts/validate-claim-packet.py`), y el paquete no puede alcanzar un estado apto con esa fuente como único respaldo.

## Citas de autor/figura reconocible

Una cita atribuida a una persona necesita obra, discurso o entrevista identificable donde se pronunció — no basta con que "circule" atribuida a esa persona en redes o compilaciones. Antes de dar una cita por buena, cruzarla contra `blocked-content.md`: varias citas que parecían obviamente atribuibles a figuras reconocibles ya se investigaron en este proyecto y resultaron mal atribuidas.
