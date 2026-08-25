# Esquema del paquete de verificación (claim packet)

Un archivo YAML por afirmación. Campos y significado:

| Campo | Obligatorio | Tipo | Notas |
|---|---|---|---|
| `claim_id` | sí | string | Identificador único dentro de la pieza (p. ej. `pieza-07-claim-1`). |
| `texto_exacto` | sí | string | La afirmación tal cual aparece en el material, sin parafrasear. |
| `ubicacion` | sí | string | Dónde vive dentro de la pieza: `titulo`, `hook`, `texto_imagen`, `caption`, `lista`, `cta`, `prompt_visual`, `descripcion_tema`. |
| `tipo` | sí | string | Naturaleza de la afirmación: `regla`, `definicion`, `cita`, `dato`, `procedimiento`, `consecuencia`, `consejo`. |
| `alcance` | sí | enum | `CAPA_A_TRANSVERSAL`, `CAPA_B_VARIABLE`, `CAPA_C_NACIONAL`, `NO_DETERMINADO`. |
| `jurisdiccion` | condicional | string o lista | **Obligatorio si `alcance` es `CAPA_C_NACIONAL`.** Nombre del país o países. |
| `nucleo_transversal` | no | string | Qué parte de la afirmación es común a toda la región, si aplica. |
| `variaciones_materiales` | condicional | string o lista | **Obligatorio si `alcance` es `CAPA_B_VARIABLE`.** Qué cambia entre países. |
| `fuentes` | condicional | lista de objetos | **Obligatorio (al menos 1) si `estado` es `APTO_PARA_NARRATIVA` o `APTO_CON_MATICES`.** Cada objeto necesita `titulo`, `organismo_autor`, `url`, `fecha_consulta`, `tipo_fuente`. |
| `confianza` | sí | enum | `alta`, `media`, `baja`. |
| `riesgo_falsa_universalizacion` | sí | enum | `ninguno`, `bajo`, `medio`, `alto`. |
| `riesgo_asesoria` | sí | enum | `ninguno`, `bajo`, `medio`, `alto`. |
| `platform_review_required` | sí | boolean | Ver `blocked-content.md`. |
| `confidentiality_review_required` | sí | boolean | Ver `references/jurisdiction-policy.md` y CLAUDE.md sección de confidencialidad. |
| `redaccion_prohibida` | no | string | Ejemplo de formulación que no debe usarse (si aplica). |
| `redaccion_segura` | no | string | Alternativa propuesta que reduce el riesgo. |
| `estado` | sí | enum | `APTO_PARA_NARRATIVA`, `APTO_CON_MATICES`, `REQUIERE_INVESTIGACION`, `BLOQUEADO`, `PENDIENTE_APROBACION_HUMANA`. |
| `revisor_humano_requerido` | sí | boolean | En la práctica, casi siempre `true` — esta skill nunca es la última palabra. |
| `notas` | no | string | Contexto adicional para quien revise. |

## Reglas de coherencia entre campos

- Si `alcance = CAPA_C_NACIONAL` → `jurisdiccion` no puede estar vacío.
- Si `alcance = CAPA_B_VARIABLE` → `variaciones_materiales` no puede estar vacío.
- Si `estado` en (`APTO_PARA_NARRATIVA`, `APTO_CON_MATICES`) → `fuentes` necesita al menos un elemento, y cada fuente necesita `url` o una identificación suficiente en su lugar.
- Si `estado = BLOQUEADO` o `REQUIERE_INVESTIGACION` → `fuentes` puede estar vacío (es justamente lo que falta), pero `notas` debería explicar qué falta.
- `revisor_humano_requerido` no puede ser `false` cuando `estado = PENDIENTE_APROBACION_HUMANA` (sería contradictorio).

El script `scripts/validate-claim-packet.py` valida estas reglas de forma puramente estructural — no evalúa si la clasificación jurídica en sí es correcta.
