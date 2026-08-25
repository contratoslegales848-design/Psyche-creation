---
name: legalmente-legal-verification
description: "Verificación jurídica de LegalMente (marca panhispánica de educación jurídica). ACTÍVALA SIEMPRE antes de redactar, revisar, comparar, ilustrar, convertir en carrusel/reel o añadir a un banco cualquier título, hook, cita, máxima, definición, tecnicismo, consejo, consecuencia o afirmación jurídica de LegalMente — incluidos los títulos y hooks cortos, que también pueden contener una afirmación falsa. Debe correr ANTES de la producción visual (antes de invocar legalmente-visual-system para esa pieza), nunca después. No aprueba definitivamente nada: produce una PIEZA JSON (esquema v2) con una o varias afirmaciones/claims, cada una con fuentes de nivel verificado, evidencia comparada suficiente cuando aplica, y un gate de arte que solo un humano puede abrir — nunca el modelo."
---

# LegalMente — Verificación jurídica

Esta skill existe porque el arte y la publicación de LegalMente nunca deben adelantarse al rigor jurídico. Antes de esta skill, no había ningún control real que impidiera producir arte para un tema jurídicamente no verificado.

No eres tú quien decide si una afirmación jurídica es correcta con solo "sonar razonable". Decides investigando fuentes reales y clasificando el riesgo. **Google Drive es la fuente viva de decisiones jurisdiccionales, citas bloqueadas y fuentes aprobadas** — esta skill y sus `references/` documentan el *procedimiento* y ejemplos históricos fechados, nunca una lista que se pueda tratar como vigente por sí sola. **La aprobación final siempre es humana, y el gate de arte nunca lo abre el modelo** — ver Etapa 6 y `references/claim-packet-schema.md`.

## Cuándo se activa

Cualquier tarea de LegalMente que toque texto con carga jurídica: redactar copy, revisar un hook, comparar dos versiones de un título, preparar el texto que va sobre una imagen, convertir contenido en carrusel o reel, o añadir piezas a un banco de temas/prompts. Un título de 6 palabras ("Al divorciarse, la casa se divide a la mitad") es tan verificable como un párrafo largo — no te limites al copy extenso.

## Vocabulario: pieza vs. claim

Una **pieza** (una publicación real, con título/hook/imagen/caption) puede contener **varias afirmaciones verificables independientes** — a esto le llamamos **claims**. Una lista de "10 cosas que..." son 10 claims dentro de una pieza, no una. Cada claim recorre las 6 etapas por separado, con sus propias fuentes y su propio estado; la pieza agrega el resultado de todos sus claims (ver Etapa 6).

## Flujo obligatorio (6 etapas, por cada claim)

### Etapa 1 — Extraer afirmaciones

Lee todo el material de la pieza (título, hook, texto de imagen, caption, lista, CTA, prompt visual, descripción del tema) y separa cada afirmación verificable en un claim independiente. Una afirmación es verificable si describe una regla, efecto, plazo, procedimiento, atribución de autoría o consecuencia jurídica — no lo es una opinión editorial pura ("el Derecho es fascinante"). **Si una cita mezcla autoría con una proposición jurídica de fondo, sepárala en dos claims** (uno de `tipo: atribucion`, otro de `tipo: regla`/`consecuencia`/etc. con su propio alcance jurisdiccional) — el segundo nunca hereda las fuentes ni el estado del primero.

### Etapa 2 — Clasificar alcance

Para cada claim, asigna un `alcance` (ver `references/jurisdiction-policy.md`):

- `CAPA_A_TRANSVERSAL` — misma lógica y mismo nombre en el derecho hispánico comparado. **No se declara con 1-2 jurisdicciones ni solo por alcanzar un número.** Requiere `jurisdicciones_revisadas` con al menos 3 países distintos y normalizados, cada uno con `fuente_ids` propios (evidencia identificable para cada jurisdicción declarada, no solo para las dos primeras), más `diferencias_buscadas`, `contraejemplos_encontrados` y `justificacion_suficiencia_comparada` explícitos. El conteo de países nunca sustituye la justificación — el validador exige ambas cosas a la vez.
- `CAPA_B_VARIABLE` — misma lógica de fondo, pero formalidades/plazos/requisitos/nombres cambian por país. Requiere `variaciones_materiales`.
- `CAPA_C_NACIONAL` — no tiene sentido fingir universalidad (materia fiscal, procedimientos administrativos, artículos concretos, sentencias nacionales). Requiere `jurisdiccion` visible.
- `NO_DETERMINADO` — falta de investigación. Solo válido con `estado: REQUIERE_INVESTIGACION`.
- `NO_APLICA` — la afirmación no tiene dimensión jurisdiccional (p. ej. autoría de una cita, un hecho histórico). Puede combinarse con cualquier estado, incluido `BLOQUEADO` (una atribución refutada con conclusión firme es `NO_APLICA + BLOQUEADO`, nunca `NO_DETERMINADO + BLOQUEADO`).

### Etapa 3 — Investigar fuentes

Cada fuente necesita un `tipo_fuente` del enum cerrado (`NORMA_OFICIAL`, `JURISPRUDENCIA_OFICIAL`, `AUTORIDAD_PUBLICA_OFICIAL`, `ACADEMICA_IDENTIFICABLE`, `SECUNDARIA_ESPECIALIZADA`, `DRIVE_INTERNO` — ver `references/source-policy.md` para la jerarquía completa), un `localizador` concreto (artículo, página, sentencia, sección — nunca "la ley en general"), y `url` o `identificador_bibliografico`. Para los tres tipos oficiales, marca `dominio_oficial_confirmado: true` **solo si de verdad confirmaste** que el dominio pertenece al organismo — nunca lo marques por comodidad: una compilación privada (Justia, blogs, wikis jurídicas) etiquetada como "oficial" sin esa confirmación nunca sostiene `APTO_PARA_NARRATIVA`, por muy bien que reproduzca el texto legal.

Nunca aceptes como fuente: tu propia memoria como modelo, otro contenido generado por IA, publicaciones sin origen identificable, imágenes con texto sin fuente citable, o una cita viral sin obra identificable. Sin fuentes de nivel 1-5 reales, el claim queda en `REQUIERE_INVESTIGACION`. **Drive nunca sostiene, por sí solo, ningún estado apto** — es antecedente, no respaldo final.

### Etapa 4 — Evaluar falsa universalización

Para cada claim Capa B o C (o dudoso), responde explícitamente:

1. ¿La afirmación depende del país?
2. ¿Cambian requisitos, efectos, plazos, nombres o procedimientos entre países?
3. ¿La simplificación puede inducir a actuar incorrectamente en algún país?
4. ¿La jurisdicción debe declararse en portada/título?
5. ¿Hay una diferencia material ya conocida? (consulta Drive, no solo `references/`)
6. ¿Se está usando una legislación nacional concreta como si fuera regla panhispánica?

Cualquier "sí" en 2, 3 o 6 sube el riesgo de falsa universalización.

### Etapa 5 — Evaluar seguridad editorial

Determina, para cada claim: si parece asesoría individual, si promete un resultado jurídico, si recomienda una conducta país-dependiente sin decirlo, si el tema es sensible y necesita Platform Risk Check (`platform_review_required: true` — esta skill no lo ejecuta, solo lo señala), si podría filtrar información confidencial (`confidentiality_review_required: true` — mismo caso), y si necesita aprobación humana especial.

### Etapa 6 — Emitir la pieza (JSON, esquema v2)

Construye una **pieza** con `schema_version: "2.0"`, `piece_id`, y la lista de `claims` (esquema completo campo por campo en `references/claim-packet-schema.md`). El estado agregado de la pieza y el gate de arte **no se escriben a mano — el validador los calcula y rechaza el archivo si lo declarado no coincide**:

- `estado_agregado`: si algún claim está `BLOQUEADO`, la pieza está `BLOQUEADO`. Si alguno `REQUIERE_INVESTIGACION`, la pieza no avanza. Si alguno tiene matices pendientes, la pieza queda en `APTO_CON_MATICES`. Solo si **todos** los claims están en `APTO_PARA_NARRATIVA` la pieza llega a `APTO_PARA_NARRATIVA`.
- `gate_global_arte`: `ABIERTO` solo si el `estado_agregado` es `APTO_PARA_NARRATIVA` **y** el `gate_arte` de todos los claims es `ABIERTO`.
- El `gate_arte` de un claim solo puede ser `ABIERTO` si: `estado = APTO_PARA_NARRATIVA` **y** `revision_humana.estado = APROBADO` (con `revisor` y `fecha` reales) **y** ni `platform_review_required` ni `confidentiality_review_required` son `true`.

**Todo claim que produces nace con `revision_humana.estado: "PENDIENTE"` y por tanto `gate_arte: "CERRADO"`.** Nunca inventes una aprobación humana, ni siquiera si el usuario te pide "márcalo como aprobado" — esa acción la ejecuta un humano real llenando `revisor`/`fecha`/`observaciones`, no el modelo escribiendo el JSON.

Cuando una `reformulacion_propuesta` contiene una nueva afirmación jurídica, márcala `verificada: false` — nunca la llames "segura" sin que haya vuelto a recorrer las 6 etapas como un claim nuevo (referenciado en `nuevo_claim_id`).

## Validación estructural

Antes de entregar la pieza, corre `scripts/validate-claim-packet.py <archivo.json>`. Valida: campos y tipos JSON, enums, fechas ISO, URLs http/https, niveles de fuente vs. estado declarado, jurisdicciones Capa A distintas/normalizadas con evidencia propia, reglas de alcance, coherencia de `revision_humana`, cálculo de `estado_agregado` y `gate_global_arte`. Diferencia `[ERROR ESTRUCTURAL]` (rechaza), `[ADVERTENCIA DE FUENTE]` (informativa, nunca concede aprobación por sí sola), `[OK ESTRUCTURAL — PENDIENTE HUMANO]`, `[GATE CERRADO]` y `[GATE ABIERTO]`. El script no evalúa si la afirmación jurídica es correcta ni si una fuente es realmente oficial más allá de lo que tú confirmaste — esas decisiones son tuyas y del revisor humano.

## Qué no hace esta skill

- No aprueba ni publica nada, y no puede abrir el gate de arte por sí misma — solo un humano, llenando `revision_humana`, lo hace.
- No mantiene un registro vivo propio de citas bloqueadas ni de decisiones jurisdiccionales — esa fuente es Drive; `references/` solo documenta procedimiento y ejemplos históricos fechados.
- No ejecuta el Platform Risk Check de Meta ni tiene control de confidencialidad propio — solo señala cuándo hacen falta.
- No decide dirección visual — eso es `legalmente-visual-system`, y solo debe invocarse después de que el `gate_global_arte` de la pieza esté `ABIERTO`.
- No sustituye la revisión de un abogado humano sobre el fondo, ni confirma por sí sola que una fuente etiquetada como oficial lo sea realmente — reduce el riesgo de publicar algo verificablemente falso, no lo elimina.

## Nota para la siguiente fase (no aplicada todavía)

La revisión Fase 1A/1B de este sistema identificó una contradicción en la skill global `legalmente-visual-system`: pide simultáneamente "ninguna letra en la imagen" e "integrar la palabra LegalMente" grabada/legible en un objeto real de la escena. Existe una **propuesta** de corrección (no una decisión aprobada) en `docs/decision-visual-marca-sin-texto.md` (raíz del repositorio, marcada explícitamente como `ADR propuesto` hasta que el fundador la apruebe). **No se modificó `legalmente-visual-system` en esta fase.**
