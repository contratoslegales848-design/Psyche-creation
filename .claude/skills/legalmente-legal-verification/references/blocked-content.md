# Procedimiento de contenido bloqueado

**Este archivo NO es el registro vivo de citas bloqueadas, decisiones jurisdiccionales ni fuentes aprobadas de LegalMente.** Esa fuente de verdad vive en Google Drive y puede cambiar entre sesiones. Este archivo describe el *procedimiento* para consultarla y las *categorías* de bloqueo — no sustituye consultar el documento vigente antes de publicar.

## Dónde vive la lista vigente

Antes de dar una cita, atribución o afirmación por verificada, cruzarla contra los documentos canónicos de Drive del proyecto (nombres exactos, a buscar por título en el conector de Drive):

- **"LegalMente — Matriz de contenido (Addendum procesado + capas jurisdiccionales + Angle Engine)"** — estado de capa jurisdiccional por tema, incluida la columna de riesgo de falsa universalización.
- **"Inventario de publicaciones — LegalMente (Facebook)"** — qué ya se publicó, para no repetir ni contradecir.
- **"LegalMente — Estado del proyecto y continuación (leer primero)"** — decisiones y bloqueos más recientes del fundador.
- Cualquier documento de Drive con "citas" o "bloqueadas" en el título (p. ej. reacciones críticas a bancos de citas de terceros) — buscar por título exacto en el momento de verificar, no asumir que la lista de abajo sigue vigente.

Si esta skill y Drive no coinciden, Drive gana siempre (jerarquía de autoridad, `CLAUDE.md`).

## Categorías de bloqueo (procedimiento, estable)

1. **Atribución no confirmada.** Una cita atribuida a una persona sin obra, discurso o entrevista identificable donde se pronunció. No basta con que "circule" atribuida a esa persona.
2. **Falsa universalización conocida.** Una figura o regla que parece transversal pero tiene una diferencia material ya documentada en algún país (ver `jurisdiction-policy.md` para el procedimiento de investigación).
3. **Contenido sensible sin Platform Risk Check.** Violencia, muerte, amenazas, suicidio/autolesión, sexualidad, drogas, delitos, salud mental — necesita `platform_review_required: true` en el paquete (ver "ACTUALIZACIÓN OPERATIVA — Platform Risk Check para Meta y contenido sensible" en Drive; esa skill/hook no existe todavía en el repositorio, ver `CLAUDE.md`).
4. **Posible información confidencial.** Cualquier detalle que pueda reconstruir un caso real de experiencia profesional privada — necesita `confidentiality_review_required: true` (control formal todavía no implementado, ver `CLAUDE.md`).

## Ejemplos históricos de metodología (fechados — no son la lista vigente)

Estos son ejemplos de *cómo se investigó* un bloqueo en el pasado, para calibrar el nivel de rigor esperado. **No los trates como la lista actual de citas bloqueadas** — confirma siempre contra Drive antes de publicar.

- *(Registrado antes de 2026-08-20, según el documento de Drive "LegalMente — Reacción crítica al banco de citas @perillo_ius")*: varias citas circulando con atribución a figuras reconocibles (entre ellas una atribuida a Erin Brockovich, dos frases distintas atribuidas a Ihering — una de las cuales apunta en realidad a Séneca —, una atribuida a Agatha Christie, una atribuida a Emma Goldman que en realidad es de Lacassagne, y una atribuida a Édouard Laboulaye) se investigaron y no tenían fuente primaria confirmada en ese momento.
- *(Registrado antes de 2026-08-20)*: el hook "Le dijo a su psicólogo: 'Voy a matarlo'. ¿Sigue siendo un secreto?" se identificó como innecesariamente agresivo para distribución en Meta y se reformuló a una versión que conserva la tensión jurídica con menor riesgo — ejemplo de metodología para el punto 3 de arriba.

## Qué NO pertenece a esta skill

Los recursos visuales sobreexplotados (balanza de la justicia, mazo de juez, columnas judiciales, libros/pergaminos apilados, escritorios oscuros, objeto forense sobre pergamino) son un asunto de dirección de arte, no de verificación jurídica. Esta skill puede señalar en `notas` que una afirmación parece diseñada para encajar con uno de esos recursos, pero la lista y su cumplimiento son responsabilidad de `legalmente-visual-system` — consultar esa skill directamente, no este archivo.
