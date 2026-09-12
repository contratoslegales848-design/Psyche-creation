# Contrato documental: LegalMente Radar

Estado: **contrato definido, Radar NO construido.** Documento de arquitectura, no
implementación (mismo patrón que `docs/contrato-motor-masivo.md`). Complementa la
arquitectura vigente; **no** reemplaza Constitución, gates jurídicos, fuentes
canónicas ni historial. No crea código, no abre gates, no toca producción.

Radar **no es** un predictor infalible ni un perfilador de personas. Es una capa
que convierte **señales observables agregadas** en **prioridades de trabajo**
(verificar, crear tema, detectar hueco), siempre con un humano en las decisiones que
llegan a una audiencia, y siempre trazable hasta una fuente cuando hace una
afirmación jurídica.

## 0. Estado de datos hoy (honesto, antes de definir nada)

Radar no tiene datos reales todavía. Las métricas de rendimiento no existen
(`TECHNICAL_STATE §1`: 0 de 52 entradas del historial con métricas; la ponderación
nunca corrió; ver también `docs/auditoria-automatizacion-segura.md §3.4` y
`docs/direccion-trazabilidad-emocional.md §6`). Por tanto, **hoy Radar produciría
cero tendencias y cero escenarios**: su fail-closed a nivel de datos (sección 16) es
la condición real actual, no un caso extremo. Lo único que Radar ya podría recibir
son dos flujos que sí existen conceptualmente: las clasificaciones de la capa de
necesidad (`docs/politica-capa-necesidad.md`) y la **cola de verificación** que el
propio piloto ya genera (los huecos temáticos de `docs/piloto-capa-necesidad.json`:
consumo, sucesiones, responsabilidad médica, arrendamiento).

## 1. Flujo conceptual

```
SEÑALES OBSERVABLES → PATRONES AGREGADOS → NECESIDADES EMERGENTES → PREGUNTAS JURÍDICAS
  → HUECOS DE VERIFICACIÓN → TENDENCIAS → ESCENARIOS → PRIORIZACIÓN
    → CONTENIDO / HERRAMIENTAS / VERIFICACIÓN
```

Cada flecha es un **hand-off propuesto**, no una tubería construida. Radar nunca
salta las puertas humanas ni la skill de verificación (secciones 12, 13, 15).

## 2. Las 18 definiciones mínimas del contrato

**(1) Qué señales puede recibir.** Solo señales ya anonimizadas y agregables:
(a) una clasificación de la capa de necesidad — `preocupacion_observable` +
`contexto_funcional` + `clasificacion_materia` + `ambito`; (b) una entrada de la
cola de verificación (una pregunta jurídica sin claim); (c) cuando existan, métricas
de publicación (`MeasurementRecord`). Nunca recibe el texto verbatim del usuario.

**(2) Qué campos puede almacenar/agregar.** Solo agregados sin persona: conteos por
`(ambito, contexto_funcional, clasificacion_materia, período)`; la pregunta jurídica
abstracta; el estado de verificación de esa pregunta; el identificador del hueco
temático. Todo contable y recomputable a mano.

**(3) Qué campos tiene prohibido almacenar.** El texto literal de la preocupación
(`preocupacion_como_se_expresa`), cualquier identificador de persona o sesión,
cualquier combinación que permita reconstruir a un individuo, y cualquier etiqueta
emocional atada a una persona. El `registro_comunicativo` es del *output*, no de la
persona, y no se almacena por individuo.

**(4) Prohibición expresa de PII y perfiles emocionales individuales.** Regla dura y
no negociable: Radar **no** guarda PII ni construye perfiles emocionales o de
comportamiento de personas. Solo existe el agregado. Si un dato no puede agregarse
sin identificar a alguien, **no entra**. Esto extiende la regla de confidencialidad
(`CLAUDE.md §5`) y el "cero PII" de la política de necesidad.

**(5) Separación señal / hecho / inferencia / tendencia / hipótesis / escenario.**
Seis niveles, nunca intercambiables, cada uno etiquetado como lo que es:
- **Señal**: un evento observado y anonimizado (una clasificación, una entrada de cola).
- **Hecho**: algo contado con evidencia (“en el período P hubo N señales de tipo X”) — un hecho sobre el agregado, no sobre el derecho.
- **Inferencia**: una lectura derivada de hechos (“el contexto X parece asociarse a la pregunta Q”) — marcada como inferencia.
- **Tendencia**: un cambio en el tiempo confirmado por encima del umbral de ruido (sección 8-9).
- **Hipótesis**: una explicación propuesta, aún no confirmada.
- **Escenario**: un futuro condicional (“si X continúa, podría ocurrir Y”) — jamás presentado como hecho (sección 3-horizontes).

**(6) Nivel de confianza y evidencia exigible por categoría.** Escalonado: un hecho
agregado exige el conteo real y su período; una inferencia exige ≥ el umbral de
patrón (sección 8) y se declara como inferencia; una tendencia exige varias ventanas
temporales comparables; una hipótesis se admite sin confirmar pero etiquetada; un
escenario exige evidencia suficiente para construir sus ramas (sección 3-horizontes)
— sin ella, no se construye. Ningún nivel hereda la confianza del anterior.

**(7) Vigencia temporal de una señal.** Cada señal caduca: pasado su período de
vigencia deja de contar para “presente” y solo cuenta para series históricas. La
vigencia concreta se **calibra sobre datos reales que aún no existen** — el contrato
fija que la vigencia existe y es finita, no un número inventado.

**(8) Señales repetidas sin contar ruido como tendencia.** Un patrón exige, a la vez:
un mínimo de ocurrencias, en un mínimo de ventanas temporales distintas, desde un
mínimo de orígenes independientes. Por debajo del umbral = **ruido**, se retiene como
“no concluyente”, nunca como tendencia. Los tres mínimos son **placeholders a
calibrar con datos reales**; el contrato define su forma, no su valor.

**(9) Cambios de tendencia.** Se comparan tasas entre ventanas; se marca un cambio
(aumento / disminución / desplazamiento) solo cuando excede la banda de ruido de la
sección 8. Un cambio se registra en ambas direcciones y con su ventana.

**(10) Registrar predicciones/escenarios para comprobar después.** Todo escenario o
predicción se escribe con: (a) la condición, (b) el horizonte temporal, (c) qué lo
confirmaría o refutaría, (d) una fecha de revisión. Así es verificable a posteriori.
Un escenario sin fecha de comprobación no es válido.

**(11) Aprender de falsos positivos, falsos negativos y pronósticos fallidos.** Al
llegar la fecha de revisión, cada predicción se marca confirmada/refutada en un
libro de resultados. Los umbrales (secciones 7-8) solo se ajustan **con revisión
humana** (sección 15), nunca en silencio. Un FP/FN nunca se borra: se conserva como
aprendizaje.

**(12) Proponer un tema sin convertirlo en contenido.** Radar emite un registro
“propuesta de tema” (candidato con su evidencia). Ese candidato entra al **mismo
filtro humano + verificación** que cualquier tema (`docs/direccion-basico-antes-que-complejo.md §6`,
y el `TopicCandidate` pendiente de `docs/auditoria-automatizacion-segura.md §3.2`).
**Proponer ≠ producir.** Radar no crea copy, prompt ni arte.

**(13) Proponer verificación sin abrir gate.** Radar puede encolar una “solicitud de
verificación” (enrutar una pregunta jurídica a `legalmente-legal-verification`) —
exactamente lo que el piloto ya hace a mano en PC-05, PC-06 y los tres casos de
calibración. Radar **no** escribe `revision_humana`, **no** calcula ni fuerza
`gate_arte`, **no** toca el claim packet. Solo pone la pregunta en la cola.

**(14) Detectar que LegalMente tiene un hueco temático.** Cuando la cola de
verificación acumula preguntas repetidas en un `ambito` **sin** claim verificado,
Radar marca un “hueco temático”. El piloto ya produce los primeros huecos reales:
consumo, sucesiones, responsabilidad médica, arrendamiento. Un hueco es una señal de
prioridad, no una conclusión jurídica.

**(15) Qué decisiones requieren revisión humana.** Promover una hipótesis a
tendencia declarada; publicar cualquier escenario; convertir una propuesta de tema
en contenido real; ajustar umbrales; y **cualquier salida que llegue a una
audiencia**. Radar prepara; el humano decide.

**(16) Fail-closed.** Sin datos → sin tendencia, sin escenario, sin prioridad. Por
debajo del umbral → “no concluyente”, nunca hecho. Señal ambigua → no se cuenta. Un
almacén de señales vacío o corrupto produce “nada que reportar”, jamás una tendencia
fabricada. (Hoy, sección 0: Radar está en este estado.)

**(17) Trazabilidad completa desde una señal agregada hasta la fuente.** Toda
conclusión enlaza hacia atrás: agregado → señales contribuyentes (anonimizadas) →
pregunta jurídica → claim (si existe) → fuente verificada. Una conclusión que hace
una afirmación jurídica **no existe sin esa cadena** hasta una fuente real; un
agregado meramente descriptivo (“N preocupaciones sobre X”) traza al conteo y se
etiqueta como descriptivo, no jurídico.

**(18) Métricas futuras posibles — sin inventar métricas inexistentes.** Posibles el
día que haya datos: volumen por contexto; latencia cola→verificación; persistencia
de un hueco; tasa de acierto de predicciones. **Ninguna existe hoy** y ninguna se
reporta como medida hasta que se capture de verdad (misma honestidad que
`auditoria-automatizacion-segura.md §6`). El contrato las nombra como posibilidad, no
como dato.

## 3. Tres horizontes — nunca prospectiva como hecho

| Horizonte | Pregunta | Exigencia |
|---|---|---|
| **PRESENTE** | ¿Qué preocupa o pregunta la gente ahora? | Descriptivo, desde señales vigentes. Es un hecho agregado, no una predicción. |
| **TENDENCIA** | ¿Qué aumenta, disminuye o cambia de forma verificable? | Varias ventanas temporales comparables por encima del ruido (secciones 8-9). |
| **PROSPECTIVA** | ¿Qué podría ocurrir si ciertas variables continúan? | Condicional y etiquetada. **Nunca se presenta como hecho.** |

**Escenarios** (conservador / central-probable / acelerado-disruptivo) solo se
construyen **cuando existe evidencia suficiente** para sostener sus ramas. Hoy no
existe (sección 0), así que **hoy Radar no construye ningún escenario**. Cada
escenario, cuando proceda, se registra con su condición y su fecha de comprobación
(sección 10).

## 4. OBJETIVO C — Cómo se conectaría con el sistema existente (sin implementar)

```
Preocupación → Necesidad → Clasificación jurídica → Pregunta → Claim → Verificación → Opción → Radar → Prioridad → Contenido/Herramienta
```

| Eslabón | Dónde vive hoy | Estado |
|---|---|---|
| Preocupación → Necesidad → Clasificación → Pregunta | `docs/politica-capa-necesidad.md` + piloto | documentado (política + piloto) |
| Pregunta → Claim → Verificación | skill `legalmente-legal-verification` (esquema v4, gates) | **vigente y sin cambios** |
| Verificación → Opción | read-model (patrón `visual/source_verification.py`) | documentado, no implementado |
| Opción → Radar → Prioridad | este contrato | contrato, no construido |
| Prioridad → Contenido/Herramienta | filtro humano + producción visual | vigente; Radar solo propone |

Puntos no negociables de la conexión:
- Radar se sitúa **después** de la Opción y consume **resultados anonimizados**, no
  el flujo individual.
- Radar **realimenta** hacia Prioridad / Verificación / Contenido, pero **nunca**
  ejecuta esas etapas: encola y propone (secciones 12-13).
- La conexión **no está implementada** y este documento no la implementa.

## 5. Riesgos y ambigüedades detectados

- **Anonimato del agregado**: en un `ambito` con muy pocas señales, un agregado
  podría, en teoría, señalar a una persona. Mitigación de diseño: umbral mínimo de
  señales antes de reportar cualquier agregado (extiende la sección 8); por debajo,
  no se reporta.
- **Sesgo del hueco por sesgo de entrada**: si las señales vienen de un canal
  sesgado, los “huecos” reflejan ese canal, no la necesidad real. Debe declararse el
  origen de las señales en cada conclusión (trazabilidad, sección 17).
- **Tentación de prospectiva sin datos**: el mayor riesgo. Hoy no hay datos y la
  presión por “predecir” puede empujar a inventar tendencias. La sección 0 + 16 lo
  bloquean explícitamente.
- **Frontera pericial (hallazgo del caso F-03)**: algunos huecos no son solo de
  verificación jurídica sino que exigen pericia externa (médica). Radar puede marcar
  el hueco, pero no debe sugerir que LegalMente puede cerrarlo solo.

## 6. Lo que este contrato NO autoriza

No construye Radar, no captura señales, no crea métricas, no abre gates, no publica
escenarios, no toca el claim packet ni la producción, y no modifica lógica jurídica
vigente. Es contrato documental; construir Radar es una decisión posterior del
fundador.
