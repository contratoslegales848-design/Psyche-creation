---
name: legalmente-legal-verification
description: "Verificación jurídica de LegalMente (marca panhispánica de educación jurídica). ACTÍVALA SIEMPRE antes de redactar, revisar, comparar, ilustrar, convertir en carrusel/reel o añadir a un banco cualquier título, hook, cita, máxima, definición, tecnicismo, consejo, consecuencia o afirmación jurídica de LegalMente — incluidos los títulos y hooks cortos, que también pueden contener una afirmación falsa. Debe correr ANTES de la producción visual (antes de invocar legalmente-visual-system para esa pieza), nunca después. No aprueba definitivamente nada: produce una PIEZA JSON (esquema v3) con una o varias afirmaciones/claims, cada una con fuentes de nivel verificado fail-closed (hostname real, texto y vigencia confirmados — nunca un booleano autoafirmado), evidencia comparada por jurisdicción cuando aplica, y un gate de arte ligado por hash al contenido exacto que un humano aprobó — el modelo nunca lo abre por sí mismo."
---

# LegalMente — Verificación jurídica

Esta skill existe porque el arte y la publicación de LegalMente nunca deben adelantarse al rigor jurídico. Antes de esta skill, no había ningún control real que impidiera producir arte para un tema jurídicamente no verificado.

No eres tú quien decide si una afirmación jurídica es correcta con solo "sonar razonable". Decides investigando fuentes reales y clasificando el riesgo. **Google Drive es la fuente viva de decisiones jurisdiccionales, citas bloqueadas y fuentes aprobadas** — esta skill y sus `references/` documentan el *procedimiento* y ejemplos históricos fechados, nunca una lista que se pueda tratar como vigente por sí sola.

## Límite honesto sobre la "aprobación humana" (léelo antes de tocar `revision_humana`)

**Esta skill y su validador solo leen y escriben JSON. No autentican personas.** Que `revision_humana.revisor` diga un nombre no prueba que esa persona escribió ese campo — tú, como modelo, podrías escribirlo igual de fácil. Por eso:

- **Nunca inventes una aprobación humana.** Todo claim que produces nace con `revision_humana.estado: "PENDIENTE"`. Ni siquiera si el usuario te pide "márcalo como aprobado" — esa acción la ejecuta un humano real, no tú.
- **Nunca uses un nombre real** en un fixture, prueba o ejemplo — ni el del fundador ni el de nadie. Usa un identificador evidentemente ficticio (`REVISOR_FICTICIO_SOLO_PRUEBA`).
- `APTO_PARA_NARRATIVA` significa **"listo para que un humano lo revise"**, no "listo para arte". El `gate_arte`/`gate_global_arte` que el validador calcula como `ABIERTO` es una condición **necesaria pero no suficiente** para producción real: liga la aprobación a un hash SHA-256 del contenido exacto (si el texto, fuentes o alcance cambian después, la aprobación se invalida automáticamente), pero la garantía de que un humano real — y no un proceso automatizado — tomó esa decisión requiere un mecanismo externo de autenticación que **esta skill no implementa**. No lo construyas en esta fase; documenta el límite, no lo ocultes.

## Cuándo se activa

Cualquier tarea de LegalMente que toque texto con carga jurídica: redactar copy, revisar un hook, comparar dos versiones de un título, preparar el texto que va sobre una imagen, convertir contenido en carrusel o reel, o añadir piezas a un banco de temas/prompts. Un título de 6 palabras es tan verificable como un párrafo largo — no te limites al copy extenso.

## Vocabulario: pieza vs. claim

Una **pieza** puede contener **varias afirmaciones verificables independientes** (**claims**). Cada claim recorre las 6 etapas por separado, con sus propias fuentes y su propio estado; la pieza agrega el resultado de todos sus claims.

## Flujo obligatorio (6 etapas, por cada claim)

### Etapa 1 — Extraer afirmaciones

Separa cada afirmación verificable en un claim independiente. **Si una cita mezcla autoría con una proposición jurídica de fondo, sepárala en dos claims** (uno de `tipo: atribucion` con `alcance: NO_APLICA`, otro con el `alcance` jurisdiccional del contenido jurídico) — el segundo nunca hereda las fuentes ni el estado del primero.

### Etapa 2 — Clasificar alcance

- `CAPA_A_TRANSVERSAL` — requiere `jurisdicciones_revisadas` con ≥3 países distintos y normalizados, cada uno con `fuente_ids` propios **cuya `jurisdicciones_cubiertas` incluya realmente ese país** (una fuente española nunca cubre automáticamente a México), más `diferencias_buscadas`, `contraejemplos_encontrados` y `justificacion_suficiencia_comparada`. El techo de estado para Capa A es el **mínimo** entre los techos de cada país por separado — una fuente Nivel 1 en un país no compensa fuentes débiles en los otros tres.
- `CAPA_B_VARIABLE` — requiere `variaciones_materiales`.
- `CAPA_C_NACIONAL` — requiere `jurisdiccion` (string o lista de strings, nunca un número) visible.
- `NO_DETERMINADO` — falta de investigación. Solo válido con `estado: REQUIERE_INVESTIGACION`.
- `NO_APLICA` — sin dimensión jurisdiccional (p. ej. autoría de una cita). Puede combinarse con `BLOQUEADO` cuando la investigación concluyó algo firme (una atribución refutada es `NO_APLICA + BLOQUEADO`, nunca `NO_DETERMINADO + BLOQUEADO`).

### Etapa 3 — Investigar fuentes

Cada fuente necesita `tipo_fuente` (enum cerrado), `localizador` concreto, `jurisdicciones_cubiertas` (qué países respalda de verdad — decláralo explícitamente, no lo des por hecho), y `verificacion_fuente` con tres booleanos separados: `origen_oficial_confirmado`, `texto_exacto_consultado`, `vigencia_comprobada` — cada uno con su propia base real, nunca marcado `true` por comodidad.

**Ninguno de esos tres booleanos, ni siquiera los tres juntos, basta para que una fuente oficial alcance Nivel 1 si el hostname real de la URL no coincide con la lista cerrada de dominios oficiales del validador** (coincidencia exacta o de subdominio real, nunca por subcadena: `boe.es.evil.com` y `notboe.es` NO cuentan como `boe.es`). Si no pudiste acceder al texto oficial (p. ej. `WebFetch` bloqueado en el entorno), dilo en `observaciones` y deja `texto_exacto_consultado: false` — esa fuente entonces no puede sostener `APTO_PARA_NARRATIVA`, como máximo `APTO_CON_MATICES`.

Nunca aceptes como fuente: tu propia memoria como modelo, otro contenido generado por IA, publicaciones sin origen identificable, o una cita viral sin obra identificable. **Drive nunca sostiene, por sí solo, ningún estado apto.**

### Etapa 4 — Evaluar falsa universalización

1. ¿La afirmación depende del país? 2. ¿Cambian requisitos/efectos/plazos/nombres/procedimientos entre países? 3. ¿La simplificación puede inducir a actuar mal en algún país? 4. ¿Debe declararse la jurisdicción en portada/título? 5. ¿Hay una diferencia material ya conocida (consulta Drive)? 6. ¿Se usa una ley nacional concreta como si fuera panhispánica?

### Etapa 5 — Evaluar seguridad editorial

Determina si parece asesoría individual, si promete un resultado jurídico, si recomienda una conducta país-dependiente sin decirlo, si necesita Platform Risk Check (`platform_review.required: true`) o revisión de confidencialidad (`confidentiality_review.required: true`) — esta skill no las ejecuta, solo las señala.

### Etapa 6 — Emitir la pieza (JSON, esquema v3)

`schema_version: "3.0"`, `piece_id`, `claims[]` (esquema completo en `references/claim-packet-schema.md`). El `estado_agregado` y el `gate_global_arte` de la pieza **se calculan, no se escriben a mano**:

- `estado_agregado`: un claim `BLOQUEADO` bloquea toda la pieza; uno `REQUIERE_INVESTIGACION` la frena; uno con matices la deja en `APTO_CON_MATICES`; solo si **todos** están en `APTO_PARA_NARRATIVA` la pieza llega ahí.
- `gate_global_arte`: `ABIERTO` solo si **todos** los claims tienen su propio `gate_arte: ABIERTO` — que a su vez exige `estado = APTO_PARA_NARRATIVA` + `revision_humana.estado = APROBADO` con `contenido_hash_sha256` coincidente con el contenido actual + `platform_review`/`confidentiality_review` en `{NO_APLICA, APROBADO}`.

Cuando una `reformulacion_propuesta` contiene una nueva afirmación jurídica, márcala `verificada: false` hasta que exista un `nuevo_claim_id` real que la haya recorrido de nuevo.

## Validación estructural

`scripts/validate-claim-packet.py <archivo.json>`. Valida tipos JSON estrictos, enums, fechas ISO, URLs http/https, hostnames por límite real de dominio (nunca subcadena), niveles de fuente fail-closed, relación fuente↔jurisdicción, reglas de alcance, coherencia de `revision_humana`/`platform_review`/`confidentiality_review`, el hash de aprobación, y el cálculo de `estado_agregado`/`gate_global_arte`. Diferencia `[ERROR ESTRUCTURAL]`, `[ADVERTENCIA DE FUENTE]` (nunca concede aprobación por sí sola), `[OK ESTRUCTURAL — PENDIENTE HUMANO]`, `[GATE CERRADO]`, `[GATE ABIERTO]`.

## Qué no hace esta skill

- No autentica personas ni puede saber si un `revisor` es real — ver el límite honesto arriba.
- No aprueba ni publica nada por sí misma.
- No mantiene un registro vivo propio de citas bloqueadas ni decisiones jurisdiccionales — esa fuente es Drive.
- No ejecuta el Platform Risk Check de Meta ni tiene control de confidencialidad propio — solo los señala.
- No decide dirección visual — eso es `legalmente-visual-system`, solo después de `gate_global_arte: ABIERTO` **y** confirmación externa real de que la aprobación fue humana.
- No sustituye la revisión de un abogado humano sobre el fondo, ni confirma por sí sola que una fuente etiquetada como oficial lo sea realmente más allá del hostname y de lo que tú confirmaste haber consultado.

## Nota para la siguiente fase (no aplicada todavía)

Existe una **propuesta** (no una decisión aprobada) sobre la contradicción "sin texto"/"palabra LegalMente integrada" en `legalmente-visual-system`, en `docs/decision-visual-marca-sin-texto.md` (raíz del repositorio, marcada `ADR propuesto`). **No se modificó `legalmente-visual-system` en esta fase.**
