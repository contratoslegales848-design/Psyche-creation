# Política de capas jurisdiccionales

**Fuente viva de esta política**: "LegalMente — Decisión Constitucional: Neutralidad Jurisdiccional" (Google Drive, carpeta del proyecto). Este archivo es una guía de método para aplicar esa decisión desde Claude Code — no la sustituye ni la reemplaza. Si hay una diferencia entre lo que dice aquí y lo que dice el documento vigente de Drive, gana Drive (ver jerarquía de autoridad en `CLAUDE.md`), y este archivo debe corregirse para reflejarlo.

## Regla en una frase

Primero lo transversal, después lo jurisdiccional — nunca al revés, y nunca como disclaimer añadido a una base nacional al final.

Jurisdicción por defecto de LegalMente: panhispánica / conceptual / comparada. Jurisdicción nacional: excepción explícita, nunca supuesto implícito. La pregunta de investigación no es "¿qué dice el código de tal país sobre esto?" sino "¿cuál es el núcleo jurídico de esta institución que puede explicarse válidamente a una audiencia panhispánica, y qué cambia materialmente entre países?".

## Las tres capas

**Capa A — Núcleo transversal.** Conceptos suficientemente comunes entre sistemas jurídicos hispánicos como para explicarse sin anclarlos a un país. La explicación se centra en función, lógica, diferencia, problema y consecuencia — no en números de artículo de un país concreto.

No basta con revisar 1-2 jurisdicciones para declarar Capa A (ver `claim-packet-schema.md`: el validador exige un mínimo estructural de 3 jurisdicciones revisadas, más una justificación explícita de por qué esa evidencia es suficiente). El mínimo de 3 es un piso técnico del validador, no una regla constitucional — la suficiencia real de la evidencia comparada se argumenta caso por caso, y el documento de Drive es quien tiene la última palabra sobre qué cuenta como "suficiente" para una pieza concreta.

**Capa B — Variación jurisdiccional relevante.** Comparten lógica general, pero la regulación concreta cambia por país: formalidades, plazos, requisitos notariales, registro, acciones disponibles, denominaciones, competencias judiciales, efectos frente a terceros. Se explica primero el núcleo común, se identifica que existe variación, no se presenta una regla nacional como universal, y se usa una fórmula breve tipo "las formalidades y efectos concretos pueden variar según la legislación de cada país". Solo se añaden ejemplos nacionales cuando aportan valor real.

**Capa C — Contenido necesariamente nacional.** No tiene sentido fingir universalidad: materialidad fiscal de un país concreto, procedimientos administrativos nacionales, artículos concretos de códigos, reformas legislativas, sentencias nacionales. Debe quedar visible desde el inicio a qué país pertenece y presentarse como vertical nacional o comparada — nunca como Derecho universal. Requiere país visible, autoridad nacional citada, fuente oficial vigente, fecha de consulta y revisor humano.

**NO_DETERMINADO** — usar cuando la investigación disponible no permite clasificar con confianza. No es una capa cómoda de "salida rápida": si algo queda en `NO_DETERMINADO`, el estado del paquete debe ser `REQUIERE_INVESTIGACION`, no un estado apto.

## Ejemplos históricos de metodología (fechados — no son la lista vigente)

Estos ejemplos ilustran *cómo* se aplicó el método en el pasado, para que quien use esta skill entienda el nivel de rigor esperado. **No son una fuente de verdad viva.** El estado actual de qué figuras están confirmadas en qué capa vive en la Matriz de contenido y en los documentos de decisión de Drive — antes de publicar, cruzar contra esos documentos, no contra esta lista.

- *(Registrado antes de 2026-08-21)* Se investigó si "promesa de compraventa" era Capa A universal. No lo era: en Argentina la figura equivalente ("boleto de compraventa") tiene un régimen legal distinto (Código Civil y Comercial de 2015, con efectos parcialmente traslativos bajo ciertas condiciones). Se reclasificó como Capa B/C.
- *(Registrado antes de 2026-08-21)* Se investigó la comisión mercantil en México, Colombia y Perú y se encontró la misma lógica de fondo con una excepción terminológica en Argentina — evidencia comparada suficiente para tratarla como Capa A en esos términos específicos.

Ver el documento canónico "LegalMente — Matriz de contenido (Addendum procesado + capas jurisdiccionales + Angle Engine)" en Drive para el estado vigente de estos y otros casos.

## Quién decide

El Jurisdiction Check de esta skill (etapas 2 y 4 del flujo en `SKILL.md`) es una herramienta de investigación y clasificación, no una autoridad jurídica ni la fuente de verdad del proyecto. La clasificación de capa y el estado del paquete son un insumo para que un humano (el fundador o quien él delegue) tome la decisión final de publicar, cotejando siempre contra los documentos vigentes de Drive. Ninguna IA — este modelo incluido — es fuente jurídica ni sustituye la revisión de un abogado humano sobre el fondo.
