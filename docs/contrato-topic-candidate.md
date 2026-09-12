# Contrato documental: TopicCandidate

Estado: **contrato definido, objeto NO implementado.** Documento de arquitectura, no
código (mismo patrón que `docs/contrato-motor-masivo.md` y
`docs/contrato-legalmente-radar.md`). No abre gates, no toca producción, no crea
métricas, no convierte candidatos en contenido.

**No es arquitectura nueva ni paralela.** `docs/contrato-motor-masivo.md §4.1` ya
anticipó "un inventario consultable" y `docs/auditoria-automatizacion-segura.md §3.2`
nombró exactamente este hueco: no existe un schema para "candidato de tema" antes del
claim packet. Este contrato define ese front-end que faltaba. Revisado antes de
escribir: no existe hoy ningún `TopicCandidate`, `ContentUnit` ni `InventoryItem` en
el repositorio (`contrato-motor-masivo.md §1`).

## 0. Qué es y qué NO es (separaciones obligatorias)

`TopicCandidate` es la **unidad intermedia** que captura una oportunidad temática sin
convertirla todavía en afirmación jurídica, claim ni pieza:

```
señal / necesidad / hueco detectado → TopicCandidate → evaluación → verificación → eventual contenido o herramienta
```

Diez separaciones, no negociables:

1. **NO es un Claim.** No contiene afirmación jurídica verificada. Vive **antes** del
   claim packet.
2. **NO es contenido.** No es copy, prompt, pieza ni herramienta.
3. **NO es tendencia solo por repetirse.** La repetición es señal, no tendencia
   (umbral y ventanas los define Radar, `contrato-legalmente-radar.md §2.8`).
4. **NO es recomendación jurídica.** Nombra una pregunta, no una respuesta.
5. **NO abre gates.** Ni de arte ni de publicación.
6. **Puede morir sin generar nada** (`DESCARTADO`/`ARCHIVADO`). Es un resultado
   válido, no un fallo.
7. **Un candidato sin fuente suficiente conserva el hueco visible** — el hueco es
   parte del registro, no se oculta ni se rellena inventando.
8. **Una preocupación humana puede originarlo, pero nunca determina la conclusión
   jurídica** (extiende `politica-capa-necesidad.md`, Principio 1).
9. **Radar puede proponer candidatos, pero no aprobarlos**
   (`contrato-legalmente-radar.md §2.12`).
10. **La revisión humana decide** (sección 10): promover, mantener en espera, devolver
    a investigación, fusionar, archivar o descartar.

## 1. Posición en el ciclo de vida

```
[Radar / capa de necesidad / detección manual]
        │  (señal, necesidad, hueco)
        ▼
   TopicCandidate  ── evaluación + revisión humana ──►  (promovido)
        │                                                   │
        │ (descartado / archivado)                          ▼
        ▼                                        legalmente-legal-verification
     fin                                          (claim packet, gates, fuentes)
                                                             │
                                                             ▼
                                          content/*.json (taxonomía) → producción → publicación
```

El `TopicCandidate` se sitúa **aguas arriba del claim packet**. Cuando un candidato se
`PROMOVIDO`, se entrega a la skill de verificación — **no** produce el claim por sí
mismo, y "promovido" no implica ninguna suficiencia jurídica.

## 2. Campos

| Campo | Tipo | Nota |
|---|---|---|
| `topic_candidate_id` | string único | Identificador estable (p. ej. `TC-consumo-cobro-tras-cancelar`). |
| `origen` | string/enum | De dónde salió: `capa_de_necesidad`, `radar`, `deteccion_manual`, `piloto`, etc. Trazable. |
| `fecha_deteccion` | fecha ISO | |
| `horizonte` | enum | `PRESENTE` / `TENDENCIA` / `PROSPECTIVA`. Sin datos de serie temporal, solo `PRESENTE` es honesto (ver `contrato-legalmente-radar.md §3`). |
| `materia_juridica_probable` | string | Materia probable, **marcada como probable**, no confirmada. |
| `problema_o_necesidad` | string | El problema/necesidad en lenguaje humano. |
| `preocupacion_observable_agregada` | string | Preocupación observable agregada (nunca texto verbatim ni PII — `contrato-legalmente-radar.md §2.3-4`). |
| `pregunta_juridica_candidata` | string | La pregunta jurídica candidata — **candidata**, no verificada, sin responder. |
| `razon_de_interes` | string | Por qué podría importar (cualitativo, sin sobreafirmar recurrencia sin datos). |
| `tipo_de_oportunidad` | enum | Ver §3. |
| `evidencia_disponible` | lista | Qué evidencia real respalda que esto es una oportunidad (p. ej. un caso del piloto). |
| `fuentes_disponibles` | lista | Fuentes verificadas ya en el repo, si existen. |
| `fuentes_faltantes` | lista | Categorías de fuente que harían falta — **sin inventar su contenido**, solo el tipo/gap. |
| `estado_verificacion` | enum | `SIN_CLAIM_VERIFICADO` / `CLAIM_PARCIAL` / `CLAIM_VERIFICADO` (lee el estado del claim si existe; no lo calcula). |
| `nivel_de_incertidumbre` | string | Cualitativo: de clasificación, de fuente, o ambos. |
| `limite` | string | Hasta dónde llega el candidato; qué no abarca. |
| `riesgo_de_sobreinterpretacion` | string | Riesgo de leer más de lo que la evidencia permite. |
| `necesidad_de_revision_humana` | bool | Casi siempre `true`; toda promoción/descarte con impacto la requiere. |
| `posible_destino` | enum | Ver §3. |
| `razones_para_descartar` | lista | Motivos por los que podría descartarse (siempre se documentan, aunque no se descarte). |
| `duplicados_o_similares` | lista | Candidatos/claims/piezas semejantes (por materia, ángulo y estructura, no solo título — §9). |
| `antecedente_en_historial` | string/lista | Qué hay ya en el historial sobre esto. |
| `vigencia` | string/fecha | Hasta cuándo la señal sigue vigente (finita; el valor concreto se calibra con datos que aún no existen). |
| `estado_del_candidato` | enum | Ver §4. |
| `trazabilidad` | objeto/lista | Cadena desde la señal de origen hasta cualquier fuente que respalde una conclusión (§7-8). |

## 3. Enums de clasificación

**`tipo_de_oportunidad`**: `duda_recurrente`, `hueco_verificacion`, `cambio_normativo`,
`cambio_social`, `senal_profesional`, `senal_sectorial`, `confusion_recurrente`,
`oportunidad_herramienta`, `otro`.

**`posible_destino`**: `verificacion`, `contenido_general`, `linkedin`, `herramienta`,
`radar`, `archivo`, `descartar`.

**`horizonte`**: `PRESENTE`, `TENDENCIA`, `PROSPECTIVA` — nunca presentar `PROSPECTIVA`
como hecho.

Vocabulario cerrado, en mayúsculas/minúsculas consistentes, siguiendo el patrón del
repo (`command_center.FRESHNESS_*`, `feedback.FEEDBACK_CODES`).

## 4. Estados del candidato

Se adopta el enum propuesto por el fundador:
`DETECTADO`, `EN_ANALISIS`, `REQUIERE_FUENTES`, `LISTO_PARA_VERIFICACION`,
`EN_VERIFICACION`, `DESCARTADO`, `ARCHIVADO`, `PROMOVIDO`.

**Decisión documentada (no choca con el canon):** este enum describe el ciclo de vida
del *candidato*, un objeto distinto del claim. NO se confunde con los estados del claim
(`APTO_PARA_NARRATIVA` / `APTO_CON_MATICES` / `REQUIERE_INVESTIGACION` / `BLOQUEADO`) ni
con la clasificación de la capa de necesidad (`ES_/NO_/FRONTERA_MATERIA`). Frontera dura:
`PROMOVIDO` significa **entregado a verificación**, nunca "jurídicamente suficiente". El
estado jurídico solo lo produce la skill de verificación, después.

## 5. Control de repetición (antes de aceptar un candidato)

Un candidato debe poder consultar, **antes** de aceptarse, los ocho frentes que pidió el
fundador: temas publicados, temas generados, candidatos existentes, claims existentes,
historial reciente, similitud semántica, similitud de ángulo, similitud de estructura
narrativa. **La duplicidad no se evalúa solo por título.**

Honestidad sobre qué existe hoy (`contrato-motor-masivo.md §5`):

| Frente de repetición | Estado real en el repo |
|---|---|
| `content_id` / pieza duplicada | **existe** (determinista) |
| huella normalizada de la frase | **existe** (literal: mayúsculas/tildes/signos) |
| casilla `materia/submateria/concepto` | **existe** |
| similitud **semántica** (paráfrasis) | **NO existe** — declarado como límite, no disimulado |
| similitud de **ángulo** | **NO existe** como control automático |
| similitud de **estructura narrativa** | **NO existe** como control automático |

El contrato define qué **debería** consultarse; marca lo que aún no existe. Mientras la
similitud semántica/ángulo/narrativa no esté implementada, esa parte del control la hace
un humano, y el candidato debe registrarlo (no fingir un control que no corre).

## 6. Principio de valor (por qué merece recursos)

Un candidato **no basta con que sea jurídicamente válido**: debe justificar por qué
merece recursos. El valor potencial se expresa **cualitativamente** en estas dimensiones
—utilidad, recurrencia, urgencia, impacto, confusión pública, novedad, capacidad de
convertirse en herramienta, relevancia profesional, potencial educativo— con una
**justificación escrita por dimensión relevante**.

**No se inventan puntuaciones numéricas mientras no existan datos reales**
(`TECHNICAL_STATE §1`: 0 métricas; `auditoria §6`). Cuando existan métricas, estas
dimensiones podrán ganar un respaldo cuantitativo; hoy son juicio cualitativo,
declarado como tal.

## 7. Relación exacta con Radar

- Radar **propone** `TopicCandidate`s (`contrato-legalmente-radar.md §2.12`) a partir de
  señales agregadas y huecos de verificación (§2.14); **no los aprueba**.
- Un `TopicCandidate` con `origen: radar` lleva en `trazabilidad` la señal agregada
  anonimizada que lo originó — nunca PII.
- Radar puede **priorizar** candidatos existentes, pero la priorización es propuesta;
  la decisión de gastar recursos es humana (§10).

## 8. Relación exacta con Claim Packet

- El `TopicCandidate` es **anterior** al claim packet y no contiene afirmación jurídica.
- Al `PROMOVIDO`, se entrega la `pregunta_juridica_candidata` a
  `legalmente-legal-verification`, que crea el claim packet y corre sus 6 etapas.
- El candidato **lee** el estado del claim resultante (`estado_verificacion`); **no** lo
  escribe, no toca `revision_humana`, no calcula `gate_arte`.
- La taxonomía editorial (materia/submateria/concepto/situación/tipo) NO vive en el
  candidato: vive en `content/*.json` cuando ya hay pieza (`contrato-motor-masivo.md §2`).
  El candidato solo lleva `materia_juridica_probable`, marcada como probable.

## 9. Relación con historial y anti-repetición

- El candidato consulta el inventario consultable anticipado en
  `contrato-motor-masivo.md §4.1` (índice materializado, aún no construido) y los
  controles de duplicados existentes (§5).
- `duplicados_o_similares` y `antecedente_en_historial` se llenan comparando por
  **materia + ángulo + estructura**, no por título. Ejemplo real en la calibración: el
  candidato de arrendamiento es adyacente a `PC-03`/`pieza-01` (inquilino y propiedad)
  pero con un **ángulo distinto** (inviolabilidad del inmueble vs. usucapión) → no es
  duplicado. Eso muestra el control de ángulo funcionando a nivel de juicio, aunque el
  control automático semántico no exista todavía.

## 10. Revisión humana — acciones permitidas

La revisión humana sobre un candidato puede: **promover**, **mantener en espera**,
**devolver a investigación**, **fusionar** (con otro candidato/claim), **archivar** o
**descartar**. Toda acción con impacto queda registrada en `trazabilidad`. Ninguna de
estas acciones abre un gate ni produce contenido por sí sola.

## 11. Fail-closed y hueco visible

- Sin evidencia suficiente → el candidato no se promueve; queda `REQUIERE_FUENTES` o
  `EN_ANALISIS`, con el hueco visible.
- Sin fuente verificada → `estado_verificacion: SIN_CLAIM_VERIFICADO`; el candidato puede
  existir y esperar, pero **no** genera opción ni contenido.
- Ambigüedad de si es materia jurídica → hereda `FRONTERA_INDETERMINADO` de la capa de
  necesidad; no se fuerza.

## 12. Riesgos detectados

- **Inflar recurrencia sin datos**: llamar "duda_recurrente" a algo visto una vez. El
  principio de valor exige evidencia; sin ella, `tipo_de_oportunidad: hueco_verificacion`
  u `otro`, no "recurrente".
- **Falso anti-duplicado**: creer que el control automático detecta paráfrasis. No lo
  hace (§5); confiar en él dejaría pasar duplicados semánticos.
- **Deriva a contenido**: la tentación de que un candidato "interesante" salte a
  producción. La separación 2 y 5 lo bloquean; solo un humano promueve, y promover es a
  verificación, no a contenido.
- **PII por la puerta de atrás**: un `preocupacion_observable_agregada` demasiado
  específico podría identificar a alguien. Debe mantenerse agregado y general
  (`contrato-legalmente-radar.md §2.3-4`).

## 13. Lo que este contrato NO autoriza

No construye el objeto, no crea un almacén de candidatos, no implementa el control
semántico, no abre gates, no produce contenido, no crea métricas ni puntuaciones, y no
convierte los cuatro huecos de calibración en prioridades definitivas — son solo casos de
prueba. Construir `TopicCandidate` es una decisión posterior del fundador.

## Calibración

Cuatro ejemplos en `docs/topic-candidates-calibracion.json`, uno por hueco detectado
(consumo, sucesiones, responsabilidad médica, arrendamiento), construidos **solo** con lo
ya documentado en el piloto de la capa de necesidad. No se inventa derecho ni fuentes:
cada uno conserva su hueco visible.
