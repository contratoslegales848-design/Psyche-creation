# Esquema del paquete de verificación (claim packet)

**Formato del artefacto validado por máquina: JSON.** Un objeto JSON por afirmación, validado con `scripts/validate-claim-packet.py` (biblioteca estándar `json`, sin dependencias externas y sin parser YAML propio). El paquete puede *mostrarse* a un humano como texto en formato YAML o como tabla en cualquier otra parte del flujo editorial — pero lo único que este script valida, y lo único que debe tratarse como la fuente de verdad estructural, es el `.json`.

## Campos

| Campo | Obligatorio | Tipo | Notas |
|---|---|---|---|
| `claim_id` | sí | string | Identificador único dentro de la pieza (p. ej. `pieza-07-claim-1`). |
| `texto_exacto` | sí | string | La afirmación tal cual aparece en el material, sin parafrasear. Puede ser multilínea (usar `\n` dentro de la cadena JSON) y contener comillas, acentos y `ñ` sin ningún tratamiento especial — JSON los admite de forma nativa. |
| `ubicacion` | sí | enum | `titulo`, `hook`, `texto_imagen`, `caption`, `lista`, `cta`, `prompt_visual`, `descripcion_tema`. |
| `tipo` | sí | string | Naturaleza de la afirmación: `regla`, `definicion`, `cita`, `dato`, `procedimiento`, `consecuencia`, `consejo`. |
| `alcance` | sí | enum | `CAPA_A_TRANSVERSAL`, `CAPA_B_VARIABLE`, `CAPA_C_NACIONAL`, `NO_DETERMINADO`. |
| `jurisdiccion` | condicional | string o lista de strings | **Obligatorio si `alcance` es `CAPA_C_NACIONAL`.** Un país o una lista de países (para piezas explícitamente comparadas entre dos o más países concretos). |
| `nucleo_transversal` | no | string | Qué parte de la afirmación es común a toda la región, si aplica. |
| `variaciones_materiales` | condicional | string o lista | **Obligatorio si `alcance` es `CAPA_B_VARIABLE`.** Qué cambia entre países. |
| `jurisdicciones_revisadas` | condicional | lista de strings | **Obligatorio si `alcance` es `CAPA_A_TRANSVERSAL`.** Mínimo 3 países distintos — Capa A nunca se declara con evidencia de 1-2 jurisdicciones. |
| `diferencias_buscadas` | condicional | string | **Obligatorio si `alcance` es `CAPA_A_TRANSVERSAL`.** Qué diferencias concretas se buscaron entre las jurisdicciones revisadas (no basta con decir "se revisó"; hay que decir qué se comparó). |
| `contraejemplos_encontrados` | condicional | string | **Obligatorio si `alcance` es `CAPA_A_TRANSVERSAL`.** Qué contraejemplos o excepciones se encontraron (o "ninguno", explícitamente, si de verdad no se encontró ninguno). |
| `justificacion_suficiencia_comparada` | condicional | string | **Obligatorio si `alcance` es `CAPA_A_TRANSVERSAL`.** Por qué la evidencia reunida es suficiente para llamar a esto "núcleo transversal" y no simplemente "coincidencia entre los países que se revisaron". No hay un número mágico de países que la Decisión Constitucional establezca como umbral universal — la suficiencia se argumenta caso por caso, con un mínimo estructural de 3 jurisdicciones que el validador exige como piso, no como techo. |
| `fuentes` | condicional | lista de objetos | **Obligatorio (al menos 1) si `estado` es `APTO_PARA_NARRATIVA` o `APTO_CON_MATICES`.** Cada objeto necesita `titulo`, `organismo_autor`, `url`, `fecha_consulta`, `tipo_fuente`. |
| `confianza` | sí | enum | `alta`, `media`, `baja`. Un estado apto (`APTO_PARA_NARRATIVA` o `APTO_CON_MATICES`) nunca puede tener `confianza: baja` — es una combinación incoherente que el validador rechaza. |
| `riesgo_falsa_universalizacion` | sí | enum | `ninguno`, `bajo`, `medio`, `alto`. |
| `riesgo_asesoria` | sí | enum | `ninguno`, `bajo`, `medio`, `alto`. |
| `platform_review_required` | sí | boolean | Ver `blocked-content.md`. |
| `confidentiality_review_required` | sí | boolean | Ver CLAUDE.md sección de confidencialidad. |
| `apto_para_arte` | sí | boolean | Solo puede ser `true` cuando `estado = APTO_PARA_NARRATIVA`. Con cualquier otro estado (incluido `APTO_CON_MATICES`) debe ser `false` — el paso a producción visual exige el estado más alto, no un estado intermedio. |
| `redaccion_prohibida` | no | string | Ejemplo de formulación que no debe usarse (si aplica). |
| `redaccion_segura` | no | string | Alternativa propuesta que reduce el riesgo. |
| `estado` | sí | enum | `APTO_PARA_NARRATIVA`, `APTO_CON_MATICES`, `REQUIERE_INVESTIGACION`, `BLOQUEADO`, `PENDIENTE_APROBACION_HUMANA`. |
| `revisor_humano_requerido` | sí | boolean | **Siempre `true`.** El validador rechaza `false` sin excepción, en cualquier estado — esta skill nunca es la última palabra. |
| `notas` | no | string | Contexto adicional para quien revise. |

## Reglas de coherencia que el validador aplica

- Todo campo de `REQUIRED_FIELDS` presente y no vacío.
- `alcance`, `ubicacion`, `estado`, `confianza`, `riesgo_falsa_universalizacion`, `riesgo_asesoria` dentro de su enum.
- Si `alcance = CAPA_C_NACIONAL` → `jurisdiccion` no puede estar vacío.
- Si `alcance = CAPA_B_VARIABLE` → `variaciones_materiales` no puede estar vacío.
- Si `alcance = CAPA_A_TRANSVERSAL` → los 4 campos de justificación comparada no pueden estar vacíos, y `jurisdicciones_revisadas` necesita al menos 3 entradas.
- Si `estado` en (`APTO_PARA_NARRATIVA`, `APTO_CON_MATICES`) → `confianza` no puede ser `baja`, y `fuentes` necesita al menos un elemento con `url` o identificación suficiente.
- `apto_para_arte = true` solo es válido cuando `estado = APTO_PARA_NARRATIVA`.
- `revisor_humano_requerido` nunca puede ser `false`.

El script no evalúa si la clasificación jurídica en sí es correcta — eso es trabajo de las etapas 1-5 del flujo en `SKILL.md`, hecho por quien invoca la skill (con o sin ayuda de un modelo). El script solo bloquea paquetes incompletos, mal formados o internamente incoherentes.

## Por qué JSON y no un parser YAML propio

La primera versión de esta skill usaba un parser YAML manual, suficiente solo para el subconjunto de sintaxis usado en los primeros fixtures. Un parser manual es un riesgo: cualquier paquete real con dos puntos dentro de una URL, comillas dentro del texto citado, o una lista anidada de forma distinta a la anticipada, puede fallar en silencio o interpretarse mal sin que el error sea obvio. JSON con la biblioteca estándar `json` no tiene ese problema — es un formato completamente especificado, sin ambigüedad, y el parser de Python lo implementa de forma completa y probada. La salida legible para humanos (en un chat, en un documento) puede seguir presentándose como YAML o como texto — pero el artefacto que de verdad se valida es siempre el `.json`.
