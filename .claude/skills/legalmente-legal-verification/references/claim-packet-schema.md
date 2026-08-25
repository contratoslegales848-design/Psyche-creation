# Esquema v2 — pieza, claims, fuentes, gate

**Formato del artefacto validado por máquina: JSON.** Validado con `scripts/validate-claim-packet.py` (solo biblioteca estándar). Este documento describe el esquema v2 — una **pieza** (`schema_version: "2.0"`) que contiene una o varias **afirmaciones/claims**, cada una con sus propias fuentes, su propio estado y su propia revisión humana. El estado agregado de la pieza y el gate de arte **se calculan, nunca se escriben a mano** — el validador los recalcula y rechaza el paquete si no coinciden con lo declarado.

## Por qué v2 y qué cambió respecto a v1

La v1 tenía tres fallas de fondo, encontradas en la revisión Fase 1B:

1. `tipo_fuente` era texto libre — una compilación privada podía etiquetarse "ley oficial" sin que nada lo impidiera.
2. Un booleano aislado `apto_para_arte` podía ponerse en `true` sin que existiera ninguna aprobación humana real detrás.
3. No existía el concepto de "pieza" — cada afirmación era un paquete suelto, así que una pieza con 10 afirmaciones podía tratarse como si una sola verificación bastara para las 10.

v2 corrige las tres: `tipo_fuente` es un enum cerrado con niveles de confianza calculados, `apto_para_arte` se sustituye por una estructura de revisión humana explícita más un `gate_arte` que el validador calcula, y toda afirmación vive dentro de una pieza con agregación calculada.

## Objeto FUENTE

| Campo | Obligatorio | Tipo | Notas |
|---|---|---|---|
| `id` | sí | string | Único dentro del claim; referenciado desde `jurisdicciones_revisadas[].fuente_ids`. |
| `tipo_fuente` | sí | enum cerrado | `NORMA_OFICIAL`, `JURISPRUDENCIA_OFICIAL`, `AUTORIDAD_PUBLICA_OFICIAL`, `ACADEMICA_IDENTIFICABLE`, `SECUNDARIA_ESPECIALIZADA`, `DRIVE_INTERNO`. Cualquier otro valor es rechazado. |
| `titulo` | sí | string no vacío | |
| `organismo_autor` | sí | string no vacío | |
| `url` | condicional | string http/https | Requerido si no hay `identificador_bibliografico`. |
| `identificador_bibliografico` | condicional | string no vacío | Alternativa válida a `url` para fuentes físicas (ISBN, editorial, edición, año). Requerido si no hay `url`. |
| `fecha_consulta` | sí | fecha ISO (`YYYY-MM-DD`) | |
| `localizador` | sí | string no vacío | Artículo, página, sentencia o sección concreta — nunca "la ley en general". |
| `dominio_oficial_confirmado` | sí | boolean | Ver "Niveles de confianza de fuente" abajo. |

### Niveles de confianza de fuente (calculados por el validador, no declarados)

| Nivel | Condición | Techo de `estado` que puede sostener |
|---|---|---|
| 1 — Confirmado | `tipo_fuente` oficial (los 3 primeros del enum) **y** `dominio_oficial_confirmado: true` | `APTO_PARA_NARRATIVA` |
| 2 — Declarado, no verificado | `tipo_fuente` oficial pero `dominio_oficial_confirmado: false` | `APTO_CON_MATICES` |
| 3 — Académica/secundaria | `ACADEMICA_IDENTIFICABLE` o `SECUNDARIA_ESPECIALIZADA` | `APTO_CON_MATICES` |
| 4 — Drive interno | `DRIVE_INTERNO` | Ninguno — Drive nunca sostiene, por sí solo, un estado apto |

Si **todas** las fuentes de un claim son de Nivel 4, el techo es `REQUIERE_INVESTIGACION` aunque haya varias. El validador compara el `estado` declarado contra el techo real y rechaza el paquete si lo excede.

**Sobre la heurística de dominios**: el validador conoce una lista corta de dominios oficiales conocidos (BOE, DOF, InfoLEG, SPIJ, etc.) y emite una `[ADVERTENCIA DE FUENTE]` si una URL declarada como oficial no coincide con ninguno — pero esa lista es **orientativa, nunca prueba jurídica definitiva por sí sola**. Lo que de verdad decide si una fuente es Nivel 1 o Nivel 2 es el campo explícito `dominio_oficial_confirmado`, no la coincidencia de dominio. Esto es deliberadamente **fail-closed**: si `dominio_oficial_confirmado` es `false` (o falta), la fuente nunca sostiene `APTO_PARA_NARRATIVA`, sin importar cuán oficial parezca la URL.

## Objeto CLAIM (afirmación)

| Campo | Obligatorio | Tipo | Notas |
|---|---|---|---|
| `claim_id` | sí | string único en la pieza | |
| `texto_exacto` | sí | string | Puede ser multilínea (`\n`) y contener comillas/Unicode sin tratamiento especial. |
| `ubicacion` | sí | enum | `titulo, hook, texto_imagen, caption, lista, cta, prompt_visual, descripcion_tema`. |
| `tipo` | sí | enum | `regla, definicion, cita, atribucion, dato, procedimiento, consecuencia, consejo`. |
| `alcance` | sí | enum | `CAPA_A_TRANSVERSAL, CAPA_B_VARIABLE, CAPA_C_NACIONAL, NO_DETERMINADO, NO_APLICA`. |
| `jurisdiccion` | condicional | string o lista | Obligatorio si `alcance = CAPA_C_NACIONAL`. |
| `variaciones_materiales` | condicional | string/lista | Obligatorio si `alcance = CAPA_B_VARIABLE`. |
| `jurisdicciones_revisadas` | condicional | lista de `{pais, fuente_ids}` | Obligatorio si `alcance = CAPA_A_TRANSVERSAL`. Mínimo 3 países **distintos y normalizados** (mayúsculas/espacios no cuentan como distintos); cada país necesita `fuente_ids` no vacío referenciando fuentes reales del mismo claim. El conteo de países nunca sustituye la justificación — ambos se exigen. |
| `diferencias_buscadas`, `contraejemplos_encontrados`, `justificacion_suficiencia_comparada` | condicional | string | Obligatorios (no vacíos) si `alcance = CAPA_A_TRANSVERSAL`. |
| `fuentes` | sí | lista de objetos FUENTE | Puede estar vacía (fuerza `REQUIERE_INVESTIGACION`). |
| `confianza` | sí | enum | `alta, media, baja`. Un estado apto nunca puede tener `baja`. |
| `riesgo_falsa_universalizacion`, `riesgo_asesoria` | sí | enum | `ninguno, bajo, medio, alto`. |
| `platform_review_required`, `confidentiality_review_required` | sí | boolean | Si cualquiera es `true`, el gate de ese claim queda cerrado sin importar lo demás. |
| `estado` | sí | enum | `APTO_PARA_NARRATIVA, APTO_CON_MATICES, REQUIERE_INVESTIGACION, BLOQUEADO, PENDIENTE_APROBACION_HUMANA`. |
| `revision_humana` | sí | objeto | `{estado: PENDIENTE\|APROBADO\|RECHAZADO, revisor, fecha, observaciones}`. **Todo claim producido por el modelo nace con `estado: PENDIENTE`.** `APROBADO` exige `revisor` y `fecha` no vacíos. |
| `gate_arte` | sí | enum calculado | `CERRADO` o `ABIERTO`. Solo puede ser `ABIERTO` si: `estado = APTO_PARA_NARRATIVA` **y** `revision_humana.estado = APROBADO` **y** ni `platform_review_required` ni `confidentiality_review_required` son `true`. El validador recalcula y rechaza si no coincide. |
| `reformulacion_propuesta` | sí | objeto | `{texto, verificada, nuevo_claim_id}`. Sustituye a `redaccion_segura` de v1 — nunca llames "segura" a algo no verificado. Si `texto` contiene una afirmación jurídica nueva, `verificada` debe ser `false` salvo que `nuevo_claim_id` apunte a un claim real de la misma pieza que la haya vuelto a recorrer las 6 etapas. |
| `redaccion_prohibida`, `notas` | no | string | |

## Reglas especiales de `alcance`

- `NO_DETERMINADO` = falta de investigación. Solo puede combinarse con `estado = REQUIERE_INVESTIGACION`. Nunca con `BLOQUEADO`, `APTO_*`, etc.
- `NO_APLICA` = la afirmación no tiene dimensión jurisdiccional (p. ej. autoría/atribución de una cita). Puede combinarse con cualquier estado, incluido `BLOQUEADO` (una atribución refutada con conclusión firme usa `NO_APLICA + BLOQUEADO`, no `NO_DETERMINADO`).
- Si una cita contiene además una proposición jurídica de fondo, se separan en dos claims: uno de `tipo: atribucion` con `alcance: NO_APLICA` (o `NO_DETERMINADO` si aún no se sabe), y otro de `tipo: regla` con el `alcance` jurisdiccional que corresponda al contenido jurídico. El segundo claim nunca hereda las fuentes ni el estado del primero.

## Objeto PIEZA (nivel superior del archivo)

| Campo | Obligatorio | Tipo | Notas |
|---|---|---|---|
| `schema_version` | sí | string | Debe ser exactamente `"2.0"`. |
| `piece_id` | sí | string no vacío | |
| `claims` | sí | lista de objetos CLAIM | Al menos 1. Una pieza de "diez afirmaciones" debe tener 10 claims, no un resumen genérico. `claim_id` únicos dentro de la pieza. |
| `estado_agregado` | sí | enum calculado | Prioridad: `BLOQUEADO` > `REQUIERE_INVESTIGACION` > `PENDIENTE_APROBACION_HUMANA` > `APTO_CON_MATICES` > `APTO_PARA_NARRATIVA` (solo si **todos** los claims están en `APTO_PARA_NARRATIVA`). Un solo claim bloqueado bloquea toda la pieza; un solo claim pendiente de investigación frena toda la pieza, aunque los otros nueve estén perfectos. |
| `revisiones_pendientes` | sí | lista de `claim_id` calculada | Todo claim que no esté simultáneamente en `APTO_PARA_NARRATIVA`, con `revision_humana.estado = APROBADO`, y sin revisión de plataforma/confidencialidad pendiente. |
| `gate_global_arte` | sí | enum calculado | `ABIERTO` solo si `estado_agregado = APTO_PARA_NARRATIVA` **y** el `gate_arte` de **todos** los claims es `ABIERTO`. Cualquier claim pendiente cierra el gate global. |

## Verdicto del validador (líneas de salida)

- `[ERROR ESTRUCTURAL]` — el paquete es rechazado (JSON mal formado, campo faltante, enum inválido, estado que excede lo que las fuentes permiten, gate declarado que no corresponde, etc.).
- `[ADVERTENCIA DE FUENTE]` — informativa, no rechaza por sí sola (p. ej. dominio que no coincide con la heurística de dominios oficiales conocidos, aunque `dominio_oficial_confirmado` sea `true`). Una advertencia nunca concede aprobación — solo informa.
- `[OK ESTRUCTURAL — PENDIENTE HUMANO]` — el paquete es válido, pero el gate está cerrado a la espera de revisión humana (o de investigación adicional).
- `[GATE CERRADO]` — se imprime junto con el anterior, o solo, cuando el estado agregado es `BLOQUEADO`/`REQUIERE_INVESTIGACION`.
- `[GATE ABIERTO]` — el paquete es válido y todas las condiciones para producción visual están cumplidas.

El script no evalúa si la clasificación jurídica en sí es correcta, ni si una fuente etiquetada como oficial lo es de verdad más allá de la heurística de dominio — eso es trabajo humano (etapas 1-5 de `SKILL.md`, más la revisión humana real que llena `revision_humana`).
