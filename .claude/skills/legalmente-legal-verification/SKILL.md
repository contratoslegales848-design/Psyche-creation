---
name: legalmente-legal-verification
description: Verificación jurídica de LegalMente (marca panhispánica de educación jurídica). ACTÍVALA SIEMPRE antes de redactar, revisar, comparar, ilustrar, convertir en carrusel/reel o añadir a un banco cualquier título, hook, cita, máxima, definición, tecnicismo, consejo, consecuencia o afirmación jurídica de LegalMente — incluidos los títulos y hooks cortos, que también pueden contener una afirmación falsa. Debe correr ANTES de la producción visual (antes de invocar legalmente-visual-system para esa pieza), nunca después. No aprueba definitivamente nada: produce un paquete de verificación que clasifica capa jurisdiccional, exige fuentes reales y deja la pieza en un estado (apta, con matices, bloqueada o pendiente de humano) para que un humano decida.
---

# LegalMente — Verificación jurídica

Esta skill existe porque el arte y la publicación de LegalMente nunca deben adelantarse al rigor jurídico. Antes de esta skill, no había ningún control real que impidiera producir arte para un tema jurídicamente no verificado — ver `references/blocked-content.md` para el historial de errores que motivan esto (boleto de compraventa argentino, art. 232 peruano, comisión mercantil, citas mal atribuidas).

No eres tú quien decide si una afirmación jurídica es correcta con solo "sonar razonable". Decides investigando fuentes reales y clasificando el riesgo. La aprobación final siempre es humana — ver `references/jurisdiction-policy.md` sección "Quién decide".

## Cuándo se activa

Cualquier tarea de LegalMente que toque texto con carga jurídica: redactar copy, revisar un hook, comparar dos versiones de un título, preparar el texto que va sobre una imagen, convertir contenido en carrusel o reel, o añadir piezas a un banco de temas/prompts. Un título de 6 palabras ("Al divorciarse, la casa se divide a la mitad") es tan verificable como un párrafo largo — no te limites al copy extenso.

## Flujo obligatorio (6 etapas)

### Etapa 1 — Extraer afirmaciones

Lee todo el material de la pieza (título, hook, texto de imagen, caption, lista, CTA, prompt visual, descripción del tema) y separa cada afirmación verificable en una unidad independiente. Una lista de "10 cosas que..." son hasta 10 afirmaciones distintas, no una. Una afirmación es verificable si describe una regla, efecto, plazo, procedimiento, atribución de autoría o consecuencia jurídica — no lo es una opinión editorial pura ("el Derecho es fascinante").

### Etapa 2 — Clasificar alcance

Para cada afirmación, asigna una capa (ver `references/jurisdiction-policy.md` para la definición completa y ejemplos):

- `CAPA_A_TRANSVERSAL` — misma lógica y mismo nombre en el derecho hispánico comparado.
- `CAPA_B_VARIABLE` — misma lógica de fondo, pero formalidades/plazos/requisitos/nombres cambian por país.
- `CAPA_C_NACIONAL` — no tiene sentido fingir universalidad (materia fiscal, procedimientos administrativos, artículos concretos, sentencias nacionales).
- `NO_DETERMINADO` — no se pudo clasificar con la investigación disponible; nunca fuerces una capa por defecto.

No asumas Capa A por comodidad. El historial real de este proyecto (`references/blocked-content.md`) incluye casos donde algo parecía transversal y no lo era.

### Etapa 3 — Investigar fuentes

Jerarquía de fuentes, de mayor a menor autoridad (detalle completo en `references/source-policy.md`):

1. Constitución, ley o reglamento oficial vigente.
2. Sentencia o fuente judicial oficial.
3. Autoridad pública o institución oficial.
4. Tratado, obra o publicación académica identificable.
5. Fuente secundaria especializada.
6. Material interno de Drive — únicamente como antecedente, nunca como fuente final.

Nunca aceptes como fuente: tu propia memoria como modelo, otro contenido generado por IA, publicaciones sin origen identificable, imágenes con texto sin fuente citable, o una cita viral sin obra identificable. Si no encuentras una fuente de nivel 1-5 real, el campo `fuentes` queda vacío y el estado no puede ser apto — pasa a `REQUIERE_INVESTIGACION`.

### Etapa 4 — Evaluar falsa universalización

Para cada afirmación Capa B o C (o dudosa), responde explícitamente:

1. ¿La afirmación depende del país?
2. ¿Cambian requisitos, efectos, plazos, nombres o procedimientos entre países?
3. ¿La simplificación puede inducir a actuar incorrectamente en algún país?
4. ¿La jurisdicción debe declararse en portada/título?
5. ¿Hay una diferencia material ya conocida (ver `references/blocked-content.md`)?
6. ¿Se está usando una legislación nacional concreta como si fuera regla panhispánica?

Cualquier "sí" en 2, 3 o 6 sube el riesgo de falsa universalización y normalmente exige declarar el país desde el título (Capa C) o una fórmula explícita de variación (Capa B) — nunca un disclaimer añadido al final como ocurrencia tardía.

### Etapa 5 — Evaluar seguridad editorial

Determina, para la pieza completa:

- ¿Parece asesoría individual dirigida a "tú, en tu caso concreto"?
- ¿Promete un resultado jurídico específico?
- ¿Recomienda una conducta que depende del país sin decirlo (p. ej. "firma bajo protesta")?
- ¿Contiene datos, artículos, cifras o procedimientos no verificados en la Etapa 3?
- ¿El tema es sensible (violencia, muerte, autolesión, amenazas, delitos, salud mental) y por tanto necesita Platform Risk Check antes de publicar? Márcalo como pendiente — esta skill no ejecuta ese check, solo lo señala (`platform_review_required: true`).
- ¿Podría filtrar información confidencial o un caso identificable de experiencia profesional privada? Márcalo (`confidentiality_review_required: true`) — esta skill no tiene control de confidencialidad propio todavía (gap conocido, ver CLAUDE.md).
- ¿Necesita aprobación humana especial más allá de la revisión estándar?

### Etapa 6 — Emitir el paquete de verificación

Emite un paquete YAML por afirmación (esquema completo en `references/claim-packet-schema.md`), con esta forma:

```yaml
claim_id:
texto_exacto:
ubicacion:
tipo:
alcance:
jurisdiccion:
nucleo_transversal:
variaciones_materiales:
fuentes:
  - titulo:
    organismo_autor:
    url:
    fecha_consulta:
    tipo_fuente:
confianza:
riesgo_falsa_universalizacion:
riesgo_asesoria:
platform_review_required:
confidentiality_review_required:
redaccion_prohibida:
redaccion_segura:
estado:
revisor_humano_requerido:
notas:
```

Estados permitidos — usa exactamente estos literales:

- `APTO_PARA_NARRATIVA` — verificado, fuentes suficientes, sin riesgo relevante.
- `APTO_CON_MATICES` — verificado, pero necesita la fórmula de variación jurisdiccional o una nota visible.
- `REQUIERE_INVESTIGACION` — no hay fuentes suficientes todavía; no se bloquea para siempre, se bloquea hasta investigar.
- `BLOQUEADO` — falsa universalización real, cita no verificable, o contradice un hallazgo ya documentado.
- `PENDIENTE_APROBACION_HUMANA` — verificado técnicamente pero toca un criterio que solo el fundador puede cerrar (p. ej. tono, riesgo editorial límite).

Esta skill **nunca** cambia un estado a "publicado" ni "aprobado definitivamente" — el estado más alto que puede emitir es `APTO_PARA_NARRATIVA`, que sigue requiriendo revisión humana antes de producción visual y antes de publicar.

## Validación estructural

Antes de entregar el paquete, corre `scripts/validate-claim-packet.py <archivo.yaml>` — valida que el paquete esté completo y bien formado (campos obligatorios, estado válido, jurisdicción cuando es Capa C, variaciones cuando es Capa B, al menos una fuente para estados aptos, fuentes con URL/identificación). El script no evalúa si la afirmación jurídica es correcta — eso lo decides tú en las etapas 1-5; el script solo bloquea paquetes incompletos o mal formados. Ver `references/claim-packet-schema.md` para el detalle campo por campo.

## Qué no hace esta skill

- No aprueba ni publica nada — el estado más alto que emite deja la decisión final a un humano.
- No ejecuta el Platform Risk Check de Meta — solo señala cuándo hace falta (`platform_review_required`).
- No tiene control de confidencialidad propio — solo señala cuándo hace falta revisión (`confidentiality_review_required`).
- No decide dirección visual — eso es `legalmente-visual-system`, y solo debe invocarse después de que esta skill deje la pieza en un estado apto o con matices.
- No sustituye la revisión de un abogado humano sobre el fondo — reduce el riesgo de publicar algo verificablemente falso, no lo elimina.
