# Auditoría de evidencia externa — piloto jurídico (v1.2 + ZIP)

Registro de trazabilidad exigido por el encargo "AUDITAR E INTEGRAR PRUDENTEMENTE EL EXPEDIENTE EXTERNO EN LOS 3 CLAIM PACKETS". El PDF y el ZIP en sí **no se copian a este repositorio** — se usaron como insumos externos de auditoría, fuera del control de versiones.

## Entregables auditados

| Entregable | SHA-256 |
|---|---|
| `legalmente-piloto-evidencia-primaria-v1.2.md` (PDF, 18 páginas) | `65b8ae1913b751bbf4dd804bd84c53ab24787fc9d08ff0adc29449c34988c462` |
| `legalmente-piloto-fuentes-primarias-v1.zip` | `39fd2436476d427fc4c8a93432ab9efff5c7a940b2f504b7cded4383b21a4d40` |

- **Fecha recibida (esta sesión):** 2026-08-26.
- **Fecha real de investigación/consulta que declara el expediente:** 2026-08-25.
- **Número de entradas:** 45 fichas en `manifest.json`, referenciando 30 rutas de archivo distintas (29 archivos `.txt` reales en disco + 1 marcada `NO_DESCARGABLE` sin archivo).

## Resultado de la auditoría del ZIP (recalculado de forma independiente)

- 0 `source_id` duplicados.
- 0 rutas faltantes salvo la marcada `NO_DESCARGABLE` (`SRC-P03-MX-SCJN-01`), que el propio manifest documenta como tal y para la que **no se fabricó ningún extracto**.
- **Los 44 SHA-256 de archivos con contenido coinciden exactamente** con lo declarado en `manifest.json` (recalculados de forma independiente en esta sesión, no solo leídos del manifest).
- Distribución de `resultado`: 40 `SUFICIENTE`, 4 `PARCIAL`, 1 `NO_DESCARGABLE`.
- Tamaño real de los 44 archivos con contenido: 687–6215 bytes.

## Hallazgo central: los extractos no son documentos completos

44 de 45 entradas declaran `documento_completo: true`, pero los archivos referenciados son de 687–6215 bytes — fragmentos de artículos concretos, nunca el código, ley, constitución o sentencia completos (que en la realidad ocupan cientos de KB o más). Esto es una inconsistencia interna del propio expediente, **no aceptada** en la integración: los 3 claim packets del piloto tratan estos archivos como extractos de artículos concretos, nunca como el documento íntegro.

## Regla de gobernanza aplicada (no automatismo)

Ninguna fuente de los 3 claim packets se marcó `origen_oficial_confirmado`, `texto_exacto_consultado` o `vigencia_comprobada` en `true` solo porque el manifest o el informe v1.2 lo autoafirmen. Motivo: el expediente es contenido producido por otro modelo de IA, y tanto `references/source-policy.md` ("nunca aceptar como fuente otro contenido generado por IA") como `CLAUDE.md` ("ninguna IA es fuente jurídica") lo prohíben expresamente. Se intentó verificación de red independiente y real contra 7 dominios oficiales representativos citados en el expediente (`boe.es`, `diputados.gob.mx`, `infoleg.gob.ar`, `sjf2.scjn.gob.mx`, `corteidh.or.cr`, `funcionpublica.gov.co`, `ordenjuridico.gob.mx`) en la integración anterior de esta misma sesión: **los 7 devolvieron `EGRESS_BLOCKED`**. Ninguna fuente pudo verificarse de forma independiente.

## Hallazgos adicionales de auditoría (fuentes reclasificadas o dejadas sin registrar)

- **`SRC-P02-AR-JUR-01`** (CNAT, "Torres c/ Securitas"): el expediente la presenta como jurisprudencia oficial (`PARCIAL`), pero su único `url_oficial_directa` es `aldiaargentina.microjuris.com` — un agregador **privado** de jurisprudencia, no un portal judicial oficial. Reclasificada de `JURISPRUDENCIA_OFICIAL` a `SECUNDARIA_ESPECIALIZADA` (techo Nivel 3, nunca Nivel 1).
- **`SRC-P01-MX-QROO-02`** (Tesis 2014491): el hostname `sjf2.scjn.gob.mx` resuelve al registro oficial como `scjn-gob-mx`, pero el organismo real que emitió la tesis es un Tribunal Colegiado de Circuito, no la SCJN. En vez de declarar un `organismo_autor` falso para que coincida, se dejó la URL fuera del campo `url` del esquema (solo como referencia en `identificador_bibliografico`) — la fuente no puede alcanzar Nivel 1 así, que es el techo honesto que le corresponde.
- **`SRC-P01-MX-QROO-01`** y **`SRC-P03-MX-QROO-PEN-01`**: los hostnames `congresoqroo.gob.mx` y `satq.qroo.gob.mx` no tienen entrada propia en el registro oficial — resuelven solo a la entrada genérica `gob-mx-generico` (`AUTORIDAD_PUBLICA_OFICIAL`, nunca `NORMA_OFICIAL`), aunque el organismo real sea legislativo. `tipo_fuente` se ajustó en consecuencia.
- **`SRC-P02-CO-JUR-01`**, **`SRC-P03-ES-TC-01/02`**, **`SRC-P03-CIDH-*`**: hostnames oficiales legítimos (`cortesuprema.gov.co`, `hj.tribunalconstitucional.es`, `oas.org`, `corteidh.or.cr`) que no están en el registro cerrado — se dejaron con `registro_oficial_id: null` en vez de forzar una entrada nueva sin decisión humana explícita; el validador los marca `[ADVERTENCIA DE FUENTE]`, nunca error duro.
- **`SRC-P03-MX-SCJN-01`** (expediente íntegro del Amparo Directo 3/2011, `NO_DESCARGABLE`): no se creó ninguna fuente estructurada propia ni se fabricó extracto. Se cita solo en notas del claim correspondiente, que se apoya en `SRC-P03-MX-SCJN-02` (la Tesis, que sí tiene extracto real en el ZIP).

## Qué se incorporó

Los `source_id`, localizadores de artículo/sentencia y organismos del expediente auditado, en la medida en que fueron internamente consistentes entre el informe v1.2, `manifest.json` y el archivo `.txt` correspondiente — como candidatos más precisos para investigación humana futura, nunca como verificación ya alcanzada. Los 3 claim packets pasaron de 2-3 claims genéricos por pieza a 5-7 claims atómicos por pieza (uno por afirmación jurídica concreta), cada fuente limitada a una sola norma o sentencia (nunca varias agrupadas).

## Qué permanece sin verificar

Absolutamente todo: los 3 claim packets permanecen en `estado: REQUIERE_INVESTIGACION` y `gate_arte`/`gate_global_arte: CERRADO` en la totalidad de sus claims. `revision_humana.estado` permanece `PENDIENTE` en todos. Ningún gate de arte, narrativa o publicación fue abierto.
