# Esquema v4 — pieza, claims, fuentes con verificación real y registro oficial único, gate ligado a hash

**Formato del artefacto validado por máquina: JSON.** Validado con `scripts/validate-claim-packet.py` (solo biblioteca estándar). Una **pieza** (`schema_version: "4.0"`) contiene una o varias **afirmaciones/claims**, cada una con sus propias fuentes, cada fuente con su propia jurisdicción cubierta y su propia verificación de origen/contenido/vigencia. El estado agregado de la pieza y el gate de arte **se calculan, nunca se escriben a mano**.

**Migración desde v3 (Fase 1D.1):** `"3.0"` ya no es una versión vigente — el validador la rechaza con un mensaje explícito de migración. La diferencia central es el campo `registro_oficial_id` en cada fuente (ver abajo): antes (Fase 1D) el validador cruzaba hostname↔jurisdicción con dos listas manuales paralelas (`OFFICIAL_HOSTNAMES`, `OFFICIAL_HOSTNAME_JURISDICTIONS`); ahora ambas se sustituyen por un **único** registro externo (`references/official-source-registry.json`) que además cruza organismo y tipo de fuente permitido — no solo jurisdicción.

## Límite honesto (léelo antes de usar `revision_humana`)

**Este validador solo lee JSON. No autentica personas.** Que el campo `revision_humana.revisor` contenga un nombre no prueba que esa persona escribió ese JSON — cualquier proceso, incluido un modelo, puede rellenarlo. Por eso:

- `APTO_PARA_NARRATIVA` significa **"listo para revisión humana"**, no "listo para arte".
- `gate_arte: "ABIERTO"` es una condición **necesaria pero no suficiente**: reduce el riesgo de que el propio modelo se autoapruebe sin dejar rastro verificable (liga la aprobación a un hash SHA-256 del contenido exacto del claim — ver más abajo), pero **no** demuestra que un humano real aprobó. La garantía real de autenticidad requiere un mecanismo externo (firma, sesión autenticada, flujo de aprobación fuera de este repositorio) que **esta skill no implementa**.
- **Ningún agente puede autoasignarse como revisor.** Que el validador o la gobernanza acepten una firma solo prueba que la firma existe, está bien formada y liga al contenido exacto — nunca quién la escribió.
- Nunca escribas un nombre real en un fixture de prueba. Usa `REVISOR_FICTICIO_SOLO_PRUEBA` o equivalente. El repositorio tiene pruebas de higiene (`test_no_nombres_reales_en_fixtures`, `test_no_nombres_reales_en_referencias_ni_skill` y `test_no_hay_nombres_reales_en_los_scripts`) que fallan si aparece el nombre real del fundador en cualquier fixture, referencia, `SKILL.md` o script.

## Los cuatro estados no son equivalentes (decisión del fundador, 2026-08-27)

Se confunden con facilidad y cada uno habilita algo distinto. En orden, y sin atajos entre ellos:

| Concepto | Qué significa exactamente | Qué habilita |
| --- | --- | --- |
| `estado = APTO_PARA_NARRATIVA` | La evidencia permite **someter el claim a aprobación humana**. Lo calcula el validador a partir de las fuentes. | Nada por sí solo. Solo autoriza pedir la revisión. |
| `revision_humana.estado = APROBADO` | Un humano aprobó **exactamente el contenido ligado al hash canónico**. | Nada por sí solo: si el estado no es `APTO_PARA_NARRATIVA`, o el hash no coincide, el gate sigue `CERRADO`. |
| `gate_arte = ABIERTO` | Se cumplen **todos** los requisitos a la vez (ver más abajo). Es un veredicto calculado, nunca escrito a mano. | **Exclusivamente**: puede comenzar la narrativa y la producción visual. |
| Autorización de publicación | Decisión humana **posterior, externa y separada**. | Publicar. |

**`gate_arte: ABIERTO` NO constituye autorización de publicación.** Son dos controles distintos y no hay ninguna implicación del primero al segundo. Este repositorio todavía **no** implementa el control de autorización de publicación (no existe el campo, ni el proceso, ni el archivo). Mientras ese control no exista, **ninguna skill, workflow o agente tiene autorización para publicar** — la publicación la ejecuta un humano, fuera de este sistema.

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
| `url` / `identificador_bibliografico` | uno de los dos | string http/https o identificador bibliográfico | La URL se valida con una única función canónica (`parse_official_url`, Fase 1D.2) — ver "Validación canónica de URL" abajo. Una fuente oficial sin `url` (solo `identificador_bibliografico`) nunca alcanza Nivel 1, sin importar qué tan coherentes parezcan `registro_oficial_id`/`organismo_autor`/`verificacion_fuente` entre sí (Fase 1D.2, Paso 2) — no hay ningún hostname real que verificar. |
| `fecha_consulta` | sí | fecha ISO | |
| `localizador` | sí | string no vacío | Artículo, página, sentencia o sección concreta. |
| `jurisdicciones_cubiertas` | sí | lista no vacía de países | Qué países respalda de verdad esta fuente. Una norma nacional oficial normalmente cubre un solo país; una fuente académica/comparada puede cubrir varios **solo si lo declara explícitamente**. Una fuente española nunca cubre automáticamente a México. Para fuentes oficiales, debe ser subconjunto de lo autorizado por su entrada del registro (ver `registro_oficial_id`). |
| `registro_oficial_id` | sí (puede ser `null`) | string o `null` | **Nuevo en v4 (Fase 1D.1).** Para `NORMA_OFICIAL`/`JURISPRUDENCIA_OFICIAL`/`AUTORIDAD_PUBLICA_OFICIAL`: el `id` de la entrada correspondiente en `references/official-source-registry.json` — declararlo es obligatorio en cuanto el hostname de `url` resuelve a una entrada conocida; si el dominio es genuinamente desconocido puede quedar `null` (advertencia, nunca Nivel 1). Para `ACADEMICA_IDENTIFICABLE`/`SECUNDARIA_ESPECIALIZADA`/`DRIVE_INTERNO`: siempre `null` — solo las fuentes oficiales tienen registro. |
| `verificacion_fuente` | sí | objeto | Ver arriba. |

### Niveles de confianza de fuente — fail-closed, calculados, nunca autoafirmados

**Nivel 1 (puede sostener `APTO_PARA_NARRATIVA`) exige, a la vez:**

1. `tipo_fuente` es oficial (`NORMA_OFICIAL`, `JURISPRUDENCIA_OFICIAL`, `AUTORIDAD_PUBLICA_OFICIAL`).
2. `verificacion_fuente.origen_oficial_confirmado: true`.
3. `registro_oficial_id` referencia una entrada real del **registro oficial único** (`references/official-source-registry.json`, ver abajo) — cuyo hostname, organismo y tipo de fuente permitido son TODOS coherentes con la fuente declarada.
4. `verificacion_fuente.texto_exacto_consultado: true` **y** `vigencia_comprobada: true`.
5. La fuente tiene una **`url` real** que la función canónica `parse_official_url` acepta (ver abajo). Sin `url` (solo `identificador_bibliografico`), Nivel 1 es imposible aunque las condiciones 1-4 parezcan cumplirse — no hay ningún hostname que verificar (Fase 1D.2, Paso 2).

Si falta cualquiera de las 4 → la fuente cae a **Nivel 2**, techo `APTO_CON_MATICES`. El campo `origen_oficial_confirmado` autoafirmado, por sí solo, nunca es prueba suficiente — ese fue el bypass cerrado en la Fase 1C.

### Registro oficial único: hostname↔organismo↔tipo_fuente↔jurisdicción (Fase 1D.1)

Antes (Fase 1D) el validador mantenía DOS listas manuales paralelas en el propio script (`OFFICIAL_HOSTNAMES` para el hostname, `OFFICIAL_HOSTNAME_JURISDICTIONS` para la jurisdicción) — eso cerraba el Bypass E (una fuente española autoatribuyéndose cobertura de México) pero dejaba abierto un bypass distinto: nada impedía que esa misma fuente boe.es se declarara `tipo_fuente: "JURISPRUDENCIA_OFICIAL"` con `organismo_autor: "Suprema Corte de Justicia de México"`, porque el validador nunca comprobaba organismo ni tipo permitido, solo jurisdicción.

La Fase 1D.1 sustituye ambas listas por un **único archivo externo cerrado**: `references/official-source-registry.json`. Cada entrada fija, para un organismo real: sus hostnames, su nombre canónico y alias aceptados, la(s) jurisdicción(es) o ámbito que puede respaldar, y el conjunto (deliberadamente conservador) de `tipo_fuente` que puede emitir — p. ej. el BOE publica normas pero no dicta sentencias, así que `boe-es` solo permite `NORMA_OFICIAL`; la SCJN mexicana solo `JURISPRUDENCIA_OFICIAL`. Para toda fuente con `tipo_fuente` oficial, el validador cruza:

- **Hostname → entrada**: coincidencia exacta o de subdominio real (nunca por subcadena), y cuando varios hostnames del registro coinciden por subdominio, gana el **más específico** — `dof.gob.mx` resuelve antes que la entrada genérica `gob.mx` (que existe solo como respaldo conservador para subdominios `*.gob.mx` sin entrada propia, y por eso solo permite `AUTORIDAD_PUBLICA_OFICIAL`, nunca `NORMA_OFICIAL` ni `JURISPRUDENCIA_OFICIAL`).
- **`registro_oficial_id` declarado == entrada que resuelve el hostname real de `url`**: declarar un id de un organismo distinto al que realmente aloja la URL es un error explícito, aunque el id declarado exista de verdad en el registro.
- **`organismo_autor`**: comparación exacta tras normalizar (minúsculas, espacios colapsados) contra el nombre canónico o alguno de los alias registrados — **nunca por subcadena** (`"Suprema Corte de Justicia de la Nación (México) — Sala Segunda"` no coincide con el nombre canónico exacto).
- **`tipo_fuente` ∈ `tipos_fuente_permitidos`** de esa entrada.
- **`jurisdicciones_cubiertas` ⊆ jurisdicciones/ámbito** autorizados de esa entrada (esto reemplaza, con la misma severidad, el cierre del Bypass E de la Fase 1D: el BOE sigue sin poder autoatribuirse México, Argentina o Perú).

Cualquier incoherencia en los cinco puntos anteriores es `[ERROR ESTRUCTURAL]`. Un hostname/organismo que el registro no conoce en absoluto no produce un error duro — genera advertencia y cae a Nivel 2 (fail-closed, igual que en la Fase 1D) hasta que un humano añada la entrada real. Las fuentes `ACADEMICA_IDENTIFICABLE`/`SECUNDARIA_ESPECIALIZADA` no tienen ninguna de estas restricciones (`registro_oficial_id` siempre `null` para ellas) y pueden declarar cobertura de varios países libremente, pero nunca pasan de Nivel 3 (techo `APTO_CON_MATICES`).

Un registro corrupto (archivo ausente/ilegible, o con `id`s duplicados) **falla cerrado**: el validador no lanza una excepción, simplemente trata esas entradas como inexistentes — ninguna fuente puede alcanzar Nivel 1 a través de un registro roto.

### Validación canónica de URL (Fase 1D.2)

Toda comprobación de URL/hostname del validador pasa por una única función: `parse_official_url`. Antes de esta fase, `extract_hostname` calculaba el host dividiendo `netloc` a mano (`rsplit("@", 1)`), lo que dejaba una ambigüedad real de parseo: la URL `https://evil.example\@boe.es/falso` contiene una barra invertida antes del `@`, y `urllib.parse` de Python la deja tal cual dentro de `netloc`, así que el `rsplit("@")` calculaba el host como `boe.es` — mientras que un navegador conforme a WHATWG normaliza la barra invertida como `/` en esquemas especiales (http/https) *antes* de parsear, así que la misma cadena se convierte en `https://evil.example/@boe.es/falso` y el host real es `evil.example`. Dos parsers, dos hosts distintos para la misma cadena — exactamente el tipo de ambigüedad que un validador fail-closed no puede tolerar.

`parse_official_url` cierra esto **rechazando la ambigüedad en sí misma**, en vez de intentar reimplementar la normalización WHATWG (con el riesgo de introducir un tercer desacuerdo):

- Rechaza cualquier URL con **barra invertida**, en cualquier posición.
- Rechaza **userinfo** (`usuario:contraseña@host`) — una fuente oficial nunca lo necesita, y es el vector colateral del bypass de arriba.
- Rechaza **espacios y caracteres de control**.
- Acepta únicamente esquema **http/https**.
- Rechaza **puertos inválidos** (fuera de 0-65535, o no numéricos).
- El hostname resultante se compara por **igualdad exacta o límite real de subdominio** (nunca por subcadena) contra el registro — sin cambios respecto a la Fase 1D/1D.1.

`is_valid_http_url` y `extract_hostname` ahora son envoltorios delgados sobre esta única función — ya no hay una segunda lógica de parseo por separado.

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

## Cobertura completa exigida por país, en cualquier alcance con `jurisdiccion` declarada — no "alguna fuente cubre algún país" (Fase 1D, extendida a Capa B en la Fase 1E)

Cuando `jurisdiccion` es una **lista** de países (comparación explícita entre varios países concretos, no un solo país) — sea `CAPA_C_NACIONAL`, `CAPA_B_VARIABLE` o cualquier otro alcance que la declare — el validador ya no acepta que "alguna fuente cubre algún país declarado". Usa la misma lógica de techo-por-país-y-mínimo que Capa A (función compartida `compute_ceiling_by_countries`, reutilizada por `compute_capa_a_ceiling` y por `compute_declared_countries_ceiling` — a su vez usada tanto para Capa C como, desde la Fase 1E, para cualquier claim con `jurisdiccion` declarada, sin duplicar la lógica de verificación de fuentes): para cada país declarado calcula el mejor nivel entre las fuentes cuya `jurisdicciones_cubiertas` realmente lo incluye, y el techo final es el **mínimo** entre todos los países declarados. Un país declarado sin ninguna fuente propia da techo `REQUIERE_INVESTIGACION` para ese país — y por tanto para toda la comparación, salvo que el `estado` declarado ya sea honestamente `REQUIERE_INVESTIGACION` (eso sigue siendo válido: declarar la verdad nunca es un error). Duplicar el mismo país en la lista, o declarar la lista vacía, es rechazado directamente como error estructural.

**En todo claim multijurisdiccional, incluido `CAPA_B_VARIABLE`, el techo jurídico se calcula como el mínimo de cobertura entre todas las jurisdicciones declaradas** (Fase 1E — Bypass E). Antes de esta fase, `CAPA_B_VARIABLE` caía en la rama genérica `compute_max_estado_por_fuentes` (un máximo plano sobre todas las fuentes del claim, sin partir por país): una sola fuente Nivel 1 de un país bastaba para declarar `APTO_PARA_NARRATIVA` un claim que también declaraba otros países sin cobertura equivalente. Esa rama genérica sigue existiendo únicamente para claims **sin** `jurisdiccion` declarada (p. ej. `NO_APLICA` o `NO_DETERMINADO` sin país visible) — cualquier claim con `jurisdiccion` no vacía, sea cual sea su `alcance`, pasa por el techo por país.

## Objeto REVISION_HUMANA (reemplaza el `apto_para_arte` booleano de v2)

| Campo | Notas |
|---|---|
| `estado` | `PENDIENTE` / `APROBADO` / `RECHAZADO`. Todo claim producido por el modelo nace `PENDIENTE`. |
| `revisor`, `fecha` | Obligatorios (no vacíos) si `estado = APROBADO`. **Nunca un nombre real en fixtures.** |
| `observaciones` | string o null. |
| `contenido_hash_sha256` | **Obligatorio si `estado = APROBADO`.** 64 caracteres hexadecimales — SHA-256 de un JSON canónico determinista. |

**Cobertura del hash (Fase 1D — cierra el Bypass F):** el hash ya no cubre solo un subconjunto de campos. Cubre **todo el claim excepto `revision_humana` y `gate_arte`** (`HASH_EXCLUDED_FIELDS` en el script) — se excluyen justo esos dos porque son el objeto que registra la aprobación misma y el resultado calculado, no contenido aprobado; todo lo demás, incluidos `titulo`, `organismo_autor` y `fecha_consulta` de **cada** fuente, la `confianza`, los riesgos, el `estado` declarado, `platform_review`/`confidentiality_review`, `reformulacion_propuesta` y `redaccion_prohibida`, entra en el hash. Antes de la Fase 1D el hash omitía `titulo`/`organismo_autor`/`fecha_consulta` de las fuentes — eso permitía cambiar la fuente citada (p. ej. de una norma vigente a una derogada, o de un organismo a otro) sin invalidar una aprobación ya dada; ese hueco quedó cerrado. Si cualquier campo cubierto cambia después de aprobar, el hash recalculado ya no coincide y **la aprobación queda invalidada automáticamente** — el gate vuelve a `CERRADO` y el validador lo marca como error.

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

`gate_arte` (`CERRADO`/`ABIERTO`, **calculado, nunca escrito a mano**): `ABIERTO` solo si se cumplen **todas** estas condiciones a la vez:

1. `estado = APTO_PARA_NARRATIVA`;
2. `revision_humana.estado = APROBADO`;
3. `revision_humana.revisor` no vacío;
4. `revision_humana.fecha` ISO válida;
5. `revision_humana.contenido_hash_sha256` de 64 hexadecimales **que coincide con el hash canónico recalculado del contenido actual del claim**;
6. `platform_review` y `confidentiality_review` con `status` en `{NO_APLICA, APROBADO}`;
7. el claim no tiene ningún otro error estructural.

Si falta cualquiera de las siete, el gate es `CERRADO` (fail-closed). Declarar `ABIERTO` sin cumplirlas es `[ERROR ESTRUCTURAL]` — y declarar `CERRADO` cuando se cumplen todas **también** lo es: el gate declarado debe reflejar el cálculo, en las dos direcciones.

Recordatorio: un `gate_arte: ABIERTO` habilita narrativa y producción visual. **No autoriza publicación** (ver la tabla de los cuatro estados, arriba).

## Objeto PIEZA

`schema_version` (`"4.0"` exacto), `piece_id`, `claims[]` (≥1, `claim_id` únicos), `estado_agregado` (calculado: `BLOQUEADO` > `REQUIERE_INVESTIGACION` > `PENDIENTE_APROBACION_HUMANA` > `APTO_CON_MATICES` > `APTO_PARA_NARRATIVA` solo si todos los claims lo están), `revisiones_pendientes` (calculado), `gate_global_arte` (calculado: `ABIERTO` solo si todos los claims tienen su propio `gate_arte: ABIERTO`).

## Verdicto del validador

`[ERROR ESTRUCTURAL]` (rechaza) · `[ADVERTENCIA DE FUENTE]` (informativa — p. ej. hostname fuera de la lista cerrada; nunca concede aprobación por sí sola) · `[OK ESTRUCTURAL — PENDIENTE HUMANO]` · `[GATE CERRADO]` · `[GATE ABIERTO]`.

## Control de gobernanza del piloto (`scripts/check_pilot_governance.py`)

Salvaguarda adicional de CI sobre los paquetes **reales** del piloto (`pilot/claim-packets/`), no sobre los fixtures. **Verifica coherencia; no congela artificialmente los gates.**

Comprueba, para cada paquete: `schema_version` exactamente `"4.0"`; que `revision_humana.estado` sea `PENDIENTE` o `APROBADO`; que toda aprobación esté firmada de forma verificable (`revisor`, `fecha` ISO, hash de 64 hexadecimales); que el `gate_arte` declarado en cada claim **coincida exactamente** con el gate canónico que calcula el validador; y que `gate_global_arte` coincida con el agregado canónico de esos gates.

No reimplementa ninguna regla jurídica: importa `validate-claim-packet.py` con `importlib` (el nombre del archivo lleva guiones y no admite un `import` normal) y delega la decisión del gate en `validate_claim()`, además de reutilizar `compute_content_hash`, `compute_estado_agregado` y `review_allows_gate`. No existe una segunda implementación de esas reglas.

**Historia — el deadlock corregido (2026-08-27):** la versión anterior exigía `gate_arte = CERRADO` de forma **incondicional** en todo el piloto. En cuanto un claim alcanzó `APTO_PARA_NARRATIVA` (Pieza 1, claims 1/2/4, tras la migración de fuentes argentinas), registrar la aprobación humana pasó a ser imposible sin dejar CI en rojo: el validador obligaba a declarar `ABIERTO` y la gobernanza obligaba a `CERRADO`, y ambos corren en el mismo job. La causa de fondo era conceptual — se usaba el gate de **arte** como si fuera un permiso de **publicación**. Al separarlos, la gobernanza pasa a comprobar coherencia con las reglas fail-closed en lugar de congelar el gate, y la garantía de "el piloto no se publica" descansa donde corresponde: en que **no existe** control de autorización de publicación y, por tanto, ningún agente puede publicar.
