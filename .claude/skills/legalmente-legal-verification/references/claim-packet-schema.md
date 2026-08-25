# Esquema v3 — pieza, claims, fuentes con verificación real, gate ligado a hash

**Formato del artefacto validado por máquina: JSON.** Validado con `scripts/validate-claim-packet.py` (solo biblioteca estándar). Una **pieza** (`schema_version: "3.0"`) contiene una o varias **afirmaciones/claims**, cada una con sus propias fuentes, cada fuente con su propia jurisdicción cubierta y su propia verificación de origen/contenido/vigencia. El estado agregado de la pieza y el gate de arte **se calculan, nunca se escriben a mano**.

## Límite honesto (léelo antes de usar `revision_humana`)

**Este validador solo lee JSON. No autentica personas.** Que el campo `revision_humana.revisor` contenga un nombre no prueba que esa persona escribió ese JSON — cualquier proceso, incluido un modelo, puede rellenarlo. Por eso:

- `APTO_PARA_NARRATIVA` significa **"listo para revisión humana"**, no "listo para arte".
- `gate_arte: "ABIERTO"` es una condición **necesaria pero no suficiente**: reduce el riesgo de que el propio modelo se autoapruebe sin dejar rastro verificable (liga la aprobación a un hash SHA-256 del contenido exacto del claim — ver más abajo), pero **no** demuestra que un humano real aprobó. La garantía real de autenticidad requiere un mecanismo externo (firma, sesión autenticada, flujo de aprobación fuera de este repositorio) que **esta skill no implementa**.
- Nunca escribas un nombre real en un fixture de prueba. Usa `REVISOR_FICTICIO_SOLO_PRUEBA` o equivalente. El repositorio tiene una prueba de higiene (`test_no_nombres_reales_en_fixtures`) que falla si aparece el nombre real del fundador en cualquier fixture, referencia o `SKILL.md`.

## Objeto VERIFICACION_FUENTE (nuevo en v3 — dentro de cada fuente)

| Campo | Tipo | Notas |
|---|---|---|
| `origen_oficial_confirmado` | boolean | Que el organismo/autor es quien dice ser. Por sí solo **no basta** para Nivel 1 — ver más abajo. |
| `texto_exacto_consultado` | boolean | Si `true`, exige `metodo_o_evidencia` no vacío (cómo se consultó: lectura directa, snippet de búsqueda, etc. — decirlo explícitamente). |
| `vigencia_comprobada` | boolean | Que la norma/criterio sigue vigente. Si `true`, exige `fecha_comprobacion` real — una fecha de consulta NO equivale a vigencia comprobada. |
| `fecha_comprobacion` | fecha ISO o null | |
| `metodo_o_evidencia` | string o null | |
| `observaciones` | string o null | Aquí se declara honestamente una limitación, p. ej. "WebFetch bloqueado por el proxy; no se pudo confirmar el texto". |

## Objeto FUENTE

| Campo | Obligatorio | Tipo | Notas |
|---|---|---|---|
| `id` | sí | string único en el claim | |
| `tipo_fuente` | sí | enum cerrado | `NORMA_OFICIAL`, `JURISPRUDENCIA_OFICIAL`, `AUTORIDAD_PUBLICA_OFICIAL`, `ACADEMICA_IDENTIFICABLE`, `SECUNDARIA_ESPECIALIZADA`, `DRIVE_INTERNO`. |
| `titulo`, `organismo_autor` | sí | string no vacío | |
| `url` / `identificador_bibliografico` | uno de los dos | string http/https o identificador bibliográfico | |
| `fecha_consulta` | sí | fecha ISO | |
| `localizador` | sí | string no vacío | Artículo, página, sentencia o sección concreta. |
| `jurisdicciones_cubiertas` | sí | lista no vacía de países | **Nuevo en v3.** Qué países respalda de verdad esta fuente. Una norma nacional oficial normalmente cubre un solo país; una fuente académica/comparada puede cubrir varios **solo si lo declara explícitamente**. Una fuente española nunca cubre automáticamente a México. |
| `verificacion_fuente` | sí | objeto | Ver arriba. |

### Niveles de confianza de fuente — fail-closed, calculados, nunca autoafirmados

**Nivel 1 (puede sostener `APTO_PARA_NARRATIVA`) exige las CUATRO condiciones a la vez:**

1. `tipo_fuente` es oficial (`NORMA_OFICIAL`, `JURISPRUDENCIA_OFICIAL`, `AUTORIDAD_PUBLICA_OFICIAL`).
2. `verificacion_fuente.origen_oficial_confirmado: true`.
3. El **hostname real** de `url` coincide, por igualdad exacta o por límite real de subdominio, con una **lista cerrada** de dominios oficiales conocidos (`OFFICIAL_HOSTNAMES` en el script) — **nunca por subcadena**. `boe.es` y `www.boe.es` coinciden; `boe.es.evil.com` y `notboe.es` NO coinciden aunque contengan la subcadena "boe.es". Un dominio oficial legítimo que falte en la lista falla cerrado — un humano debe añadirlo explícitamente al script, no forzarlo con el booleano.
4. `verificacion_fuente.texto_exacto_consultado: true` **y** `vigencia_comprobada: true`.

Si falta cualquiera de las 4 → la fuente cae a **Nivel 2**, techo `APTO_CON_MATICES`. El campo `origen_oficial_confirmado` autoafirmado, por sí solo, nunca es prueba suficiente — es exactamente el bypass que esta versión cierra (ver `docs/` o el informe de la Fase 1C).

| Nivel | Condición | Techo |
|---|---|---|
| 1 — Confirmado (las 4 condiciones) | | `APTO_PARA_NARRATIVA` |
| 2 — Oficial declarado, no verificado del todo | Falta hostname real, o texto/vigencia no confirmados | `APTO_CON_MATICES` |
| 3 — Académica/secundaria | `ACADEMICA_IDENTIFICABLE`, `SECUNDARIA_ESPECIALIZADA` | `APTO_CON_MATICES` |
| 4 — Drive interno | `DRIVE_INTERNO` | Ninguno — nunca sostiene un estado apto |

## Capa A: el techo es por jurisdicción, no "existe alguna fuente Nivel 1 en cualquier parte"

Para `alcance: CAPA_A_TRANSVERSAL`, `jurisdicciones_revisadas` es una lista de `{pais, fuente_ids}`. El validador:

1. Exige al menos 3 países distintos y normalizados (sin duplicados por mayúsculas/espacios).
2. Para cada país, cada `fuente_id` referenciado debe existir **y** su `jurisdicciones_cubiertas` debe incluir ese país — si no, error explícito ("la fuente X no cubre esta jurisdicción").
3. Calcula el **techo de cada país por separado** (el mejor nivel entre sus propias fuentes) y el techo final de la Capa A es el **mínimo** entre todos los países — no el máximo de cualquier fuente suelta. Una fuente Nivel 1 en España más tres fuentes sin verificar en México/Argentina/Perú da como techo `APTO_CON_MATICES`, el de los países más débiles, nunca `APTO_PARA_NARRATIVA`.

## Objeto REVISION_HUMANA (reemplaza el `apto_para_arte` booleano de v2)

| Campo | Notas |
|---|---|
| `estado` | `PENDIENTE` / `APROBADO` / `RECHAZADO`. Todo claim producido por el modelo nace `PENDIENTE`. |
| `revisor`, `fecha` | Obligatorios (no vacíos) si `estado = APROBADO`. **Nunca un nombre real en fixtures.** |
| `observaciones` | string o null. |
| `contenido_hash_sha256` | **Obligatorio si `estado = APROBADO`.** 64 caracteres hexadecimales — SHA-256 de un JSON canónico determinista de `{claim_id, texto_exacto, alcance, jurisdiccion, variaciones_materiales, jurisdicciones_revisadas, fuentes[id/tipo_fuente/url/identificador_bibliografico/localizador/jurisdicciones_cubiertas/verificacion_fuente]}` (ver `compute_content_hash` en el script). Si el texto, alcance, jurisdicción, fuentes o localizadores cambian después de aprobar, el hash recalculado ya no coincide y **la aprobación queda invalidada automáticamente** — el gate vuelve a `CERRADO` y el validador lo marca como error. |

## Objetos PLATFORM_REVIEW / CONFIDENTIALITY_REVIEW (reemplazan los booleanos de v2)

| Campo | Notas |
|---|---|
| `required` | boolean — se conserva como historial aunque el estado cambie; no se puede "borrar" que hizo falta revisión. |
| `status` | `NO_APLICA` (solo si `required: false`) / `PENDIENTE` / `APROBADO` / `RECHAZADO`. |
| `revisor`, `fecha` | Obligatorios si `status = APROBADO`. |
| `observaciones` | string o null. |

El gate de un claim solo puede abrirse si ambos objetos tienen `status` en `{NO_APLICA, APROBADO}` — `PENDIENTE` o `RECHAZADO` lo cierran, y no se puede "olvidar" que la revisión era necesaria porque `required` persiste.

## Objeto CLAIM — resto de campos sin cambios de fondo respecto a v2

`claim_id`, `texto_exacto`, `ubicacion` (enum), `tipo` (enum, incluye `atribucion`), `alcance` (`CAPA_A_TRANSVERSAL`, `CAPA_B_VARIABLE`, `CAPA_C_NACIONAL`, `NO_DETERMINADO`, `NO_APLICA`), `jurisdiccion` (string no vacío o lista no vacía de strings — nunca un entero), `variaciones_materiales` (mismo tipo), `confianza`, `riesgo_falsa_universalizacion`, `riesgo_asesoria`, `estado`, `reformulacion_propuesta` (`{texto, verificada, nuevo_claim_id}` — `verificada: true` exige `nuevo_claim_id` real dentro de la misma pieza), `redaccion_prohibida`, `notas` (string o null).

`gate_arte` (`CERRADO`/`ABIERTO`, calculado): `ABIERTO` solo si `estado = APTO_PARA_NARRATIVA` **y** `revision_humana.estado = APROBADO` con hash coincidente **y** `platform_review`/`confidentiality_review` en `{NO_APLICA, APROBADO}`.

## Objeto PIEZA

`schema_version` (`"3.0"` exacto), `piece_id`, `claims[]` (≥1, `claim_id` únicos), `estado_agregado` (calculado: `BLOQUEADO` > `REQUIERE_INVESTIGACION` > `PENDIENTE_APROBACION_HUMANA` > `APTO_CON_MATICES` > `APTO_PARA_NARRATIVA` solo si todos los claims lo están), `revisiones_pendientes` (calculado), `gate_global_arte` (calculado: `ABIERTO` solo si todos los claims tienen su propio `gate_arte: ABIERTO`).

## Verdicto del validador

`[ERROR ESTRUCTURAL]` (rechaza) · `[ADVERTENCIA DE FUENTE]` (informativa — p. ej. hostname fuera de la lista cerrada; nunca concede aprobación por sí sola) · `[OK ESTRUCTURAL — PENDIENTE HUMANO]` · `[GATE CERRADO]` · `[GATE ABIERTO]`.
