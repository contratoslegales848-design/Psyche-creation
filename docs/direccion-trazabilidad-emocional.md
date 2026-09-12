# Dirección: trazabilidad emocional — de la preocupación a la opción con fuente, certidumbre y límite

Registra una decisión expresa del fundador (2026-09-12), transcrita y organizada
aquí con criterio, para que cualquier sesión de Claude Code y cualquier agente
futuro la lea antes de proponer tema, copy o estilo. No sustituye al Drive como
fuente de verdad de estrategia (`CLAUDE.md §2`); es la versión operativa registrada
como constancia (`docs/direccion-basico-antes-que-complejo.md §6`).

**Esto es dirección de producto, no implementación.** No modifica el esquema del
claim packet, ni la skill visual, ni el código. Igual que
`docs/contrato-motor-masivo.md`, señala **dónde viviría cada pieza** si se
construye — sin construir nada, sin abrir ningún gate.

## 1. El problema, en palabras del fundador

El problema principal ahora es el **diseño** de LegalMente. Si está bien
estructurado, el estilo artístico deja de ser decorativo: debe ser **acorde a la
emoción que transmite el tema**, y eso lo vuelve **medible** (una hipótesis que se
puede probar con estadísticas, no un gusto). LegalMente debe **consolar** a las
personas frente a problemas jurídicos, sencillos y complejos — de ahí los dos
canales (LegalMente general y LegalMente LinkedIn).

La regla que el fundador quiere fijar: **trazabilidad emocional.** Cuando se
detecta una preocupación (emoción + hechos + problema jurídico que van de la mano
con el estilo artístico), se **traduce esa preocupación en una necesidad concreta**
y se **ofrecen opciones**, cada una vinculada a una **fuente verificada**, con un
**margen de certidumbre** y un **límite** explícitos.

## 2. La idea en una frase

> Toda salida de LegalMente nace de una preocupación real, la traduce en una
> necesidad concreta, y responde con opciones — cada opción atada a una fuente
> verificada, a cuánta certeza hay, y a hasta dónde llega esa certeza.

```
PREOCUPACIÓN                 NECESIDAD CONCRETA          OPCIONES (1..n)
(emoción + hecho          →  (qué necesita entender   →  cada una:
 + problema jurídico)         o decidir la persona)       · texto
                                                          · FUENTE verificada
                                                          · CERTIDUMBRE (margen)
                                                          · LÍMITE (hasta dónde)
        └──────────────── ESTILO ARTÍSTICO acorde al registro emocional ───────┘
```

## 3. Por qué esto NO rompe la disciplina de verificación — la reusa

Lo más importante del diseño: **fuente, certidumbre y límite no son datos nuevos.**
Ya viven en el claim packet (esquema v4). La capa emocional es una **vista** sobre
un claim ya verificado — hereda su fail-closed, no lo debilita.

| Lo que el fundador pide | Dónde ya vive en el claim packet |
|---|---|
| **Fuente verificada** | `claims[].fuentes[]` con su `registro_oficial_id` y su nivel real (1-4) |
| **Margen de certidumbre** | `estado` (los cuatro estados) + `confianza` (alta/media/baja) + el nivel de la fuente |
| **Límite** | `alcance` (Capa A/B/C), `jurisdiccion`, `nucleo_transversal` vs. `variaciones_materiales`, y `redaccion_prohibida` (lo que NO se puede concluir) |
| **Riesgo de la simplificación** | `riesgo_falsa_universalizacion`, `riesgo_asesoria` |

Consecuencia directa y no negociable: **una opción no puede mostrar más certeza de
la que su claim permite.** Si el claim es `APTO_CON_MATICES`, la opción debe decir
la matización en voz alta ("esto varía por país", "no pudimos confirmar el texto
íntegro"). Si es `REQUIERE_INVESTIGACION` o `BLOQUEADO`, **no hay opción** — no se
consuela con una afirmación que no resiste verificación. Consolar nunca es afirmar
de más.

## 4. La cadena en detalle

### 4.1 Preocupación
Una preocupación es `emoción + hecho + problema jurídico`, no una de las tres
suelta. "Miedo" no es una preocupación; "miedo a haber trabajado un año sin
contrato firmado y quedarme sin nada" sí lo es. La emoción da el registro visual;
el hecho + problema jurídico dan el claim que hay que verificar.

### 4.2 Necesidad concreta
Traducir la preocupación en lo que la persona necesita **entender o decidir** —
en general, nunca en su caso individual. "¿Tengo derechos sin contrato firmado?"
→ necesidad: *entender si la relación laboral existe por los hechos o por el
papel.* Esto es educativo y transversal; no es "cuéntame tu caso".

### 4.3 Opciones
Cada opción es una respuesta educativa respaldada por uno o más claims **ya
verificados**. Formato obligatorio de cada opción:

- **Qué dice** (el texto, dentro de lo que el claim sostiene).
- **Fuente**: el/los `fuente` del claim, con organismo y localizador reales.
- **Certidumbre**: el `estado` del claim traducido a lenguaje humano ("confirmado
  en las fuentes revisadas" / "con matices: varía por país" / "sin confirmar").
- **Límite**: hasta dónde llega — jurisdicciones cubiertas, qué NO afirma
  (`redaccion_prohibida`), y el recordatorio de que un caso concreto necesita
  análisis individual.

### 4.4 Dos ejemplos reales (anclados en claims que YA existen y están verificados)

**LegalMente general — consuelo, tema sencillo**
- Preocupación: "trabajé casi un año pero nunca firmé un contrato; siento que no
  tengo cómo defenderme." (inseguridad / desamparo)
- Necesidad concreta: entender si existe relación laboral sin papel firmado.
- Opción (anclada en `pieza-04-claim-1`, `APTO_CON_MATICES`):
  - Qué dice: en los países revisados la relación laboral existe por los hechos
    —servicio personal + subordinación + salario—, no por la firma.
  - Fuente: LFT (México), LCT (Argentina), CST (Colombia), ET (España).
  - Certidumbre: **con matices** — confirmado por búsqueda convergente, falta
    lectura directa del texto íntegro (Nivel 2).
  - Límite: los tres elementos son transversales (Capa A); plazos, montos y
    procedimientos cambian por país y **no** están en esta opción.
- Registro emocional → estilo: **alivio / calidez.** Sesga hacia familias de luz
  cálida y entrante (`oleo_cinematografico`, `hiperrealismo_editorial_cinematografico`),
  nunca tribunal amenazante.

**LegalMente LinkedIn — certeza antes de decidir, tema más complejo**
- Preocupación: "alguien va a firmar por la empresa / voy a firmar yo; ¿el cargo
  basta para obligarla?" (ansiedad de decisión, no desamparo)
- Necesidad concreta: entender si un cargo, por sí solo, acredita representación.
- Opción (anclada en `linkedin-ray-16-claim-1` y `claim-3`, `APTO_CON_MATICES`,
  con aprobación humana registrada 2026-09-12):
  - Qué dice: la representación nace de un poder con alcance propio; el cargo
    formalmente designado de administrador sí representa por ley, cualquier otro
    cargo necesita poder expreso.
  - Fuente: Códigos Civiles + leyes societarias de los 4 países.
  - Certidumbre: **con matices**, con aprobación humana registrada.
  - Límite: no dice qué facultades concretas tiene un poder específico — eso es
    caso individual (`riesgo_asesoria`, `redaccion_prohibida`).
- Registro emocional → estilo: **sobriedad, autoridad serena** (`oleo_clasico_institucional`,
  `basalt_and_gold_leaf`), no consuelo cálido. El registro de LinkedIn es "certeza
  antes de decidir", no "alivio".

## 5. Emoción ↔ estilo artístico: cómo, sin recrear el "materia = estilo" rígido

Tensión real que hay que respetar: la **Dirección Artística Adaptativa v1.2**
(Drive, `LM-ART-ADAPTIVE-1.2`) rechaza de forma explícita cualquier unión rígida
"materia = estilo". Fijar ahora "una emoción = un estilo" recrearía el mismo error,
solo que con otra llave.

**Diseño correcto: la emoción *sesga la paleta elegible*, la rotación elige dentro.**
Las familias visuales (`visual/policy/visual-families-v1.json`) ya traen
`lighting_intent`, `palette_tendency`, `human_presence` y `forbidden_tropes` — que
es exactamente el vocabulario de un registro emocional. Entonces:

1. La preocupación declara un **registro emocional** (de una lista cerrada — §7).
2. Ese registro define un **subconjunto de familias elegibles** (las de luz/paleta
   coherentes: p. ej. "alivio" → cálidas; "gravedad" → `claroscuro_de_museo`,
   `neo_editorial_dark_luxury`).
3. El motor de **rotación** (`visual/rotation.py`) elige *dentro* de ese
   subconjunto, preservando la variedad que v1.2 exige (≥3 de 5 variables cambian
   entre piezas consecutivas).

Así el estilo es acorde a la emoción **y** medible **y** variado. Nunca un candado
1:1.

## 6. Medición: el hueco real, dicho en voz alta

El fundador dice "existen estadísticas". El repositorio dice lo contrario, y no lo
tapo: `TECHNICAL_STATE §1` y la auditoría del Índice v18 registran **0 de 52
entradas del historial con métricas**; la ponderación por rendimiento **nunca
corrió**. La propia Dirección Artística Adaptativa v1.2 marca sus resultados como
"PENDIENTE DE PRUEBA VISUAL Y DATOS REALES" y advierte "datos ausentes no equivalen
a cero".

Lo bueno: la trazabilidad emocional da por fin una **hipótesis concreta que probar**
—¿un estilo acorde a la emoción consuela/engancha más que uno arbitrario?— y ya
existe el esqueleto para medirlo: la cadena post-aprobación
(`PublicationRecord → MeasurementRecord → Learning`, en
`.claude/skills/legalmente-legal-verification/publication/`) tiene el *schema* de
métricas, aunque nunca ha cargado datos reales. Cerrar ese hueco (empezar a
capturar engagement por pieza, etiquetado con su registro emocional y su familia)
es el requisito para que "medible" deje de ser una aspiración. Es el mismo hueco
que la auditoría de automatización (`docs/auditoria-automatizacion-segura.md §3.4`,
`§4`) ya señala como pendiente.

## 7. Taxonomía de emociones: vocabulario cerrado, no texto libre

Para que el registro emocional sea auditable y medible, no puede ser una cadena
libre. Debe ser un **enum cerrado**, igual que el repo ya hace con
`command_center.FRESHNESS_*` y `feedback.FEEDBACK_CODES`. Propuesta inicial (a
refinar con el fundador, no cerrada aquí):

| Registro emocional | Preocupación típica | Sesgo de familia visual |
|---|---|---|
| `ALIVIO` | "creo que perdí un derecho y no es así" | luz cálida, entrante |
| `DESAMPARO` | "no sé por dónde empezar / a quién acudir" | cálida pero contenida |
| `GRAVEDAD` | "esto es serio y quiero entender el peso" | claroscuro, clave baja |
| `CERTEZA_ANTES_DE_DECIDIR` | "voy a firmar / decidir y quiero estar seguro" (LinkedIn) | sobriedad institucional |
| `CURIOSIDAD` | "no me afecta hoy pero quiero entenderlo" | editorial neutro |

Regla dura: **el registro emocional elige el estilo; nunca elige, suaviza ni
inventa el contenido jurídico.** Una emoción no baja el umbral de verificación de
un claim.

## 8. Los dos canales

- **LegalMente general**: público amplio, registros de `ALIVIO`/`DESAMPARO`/
  `GRAVEDAD`/`CURIOSIDAD`. Consuela traduciendo lo básico transversal (Capa A) a
  lenguaje humano. 9:16.
- **LegalMente LinkedIn**: decisor profesional, registro dominante
  `CERTEZA_ANTES_DE_DECIDIR`. No consuela: reduce la ansiedad de decidir con
  criterio y fuente. 4:5. (Se conecta con el banco de experiencia del fundador,
  `docs/linkedin-raymundo-inmobiliario.md`.)

Ambos comparten la **misma regla de trazabilidad emocional** y la **misma
disciplina de verificación**. Cambia el registro emocional y el formato, nunca la
exigencia de fuente/certidumbre/límite.

## 9. Límite de seguridad: consolar sin volverse asesoría individual

Riesgo que hay que vigilar desde el diseño: "consolar frente a un problema
jurídico" está a un paso de "cuéntame tu caso". No se cruza ese paso.

- La preocupación se detecta como **patrón general**, nunca como intake de un caso
  concreto. Cero PII (regla ya registrada en la directiva de onboarding del
  fundador, Drive).
- La necesidad se traduce a algo **educativo y transversal**, no a un dictamen.
- Cada opción termina recordando su límite y que un caso concreto necesita análisis
  individual — la regla "cero dead-ends" del fundador se cumple apuntando a *tres
  preguntas para el abogado* o a una herramienta, no a un DM ni a un servicio.
- Nada de esto autoriza publicación ni asesoría (`CLAUDE.md §4-5-6`).

## 10. Dónde viviría cada pieza si se implementa (no ahora)

| Pieza nueva | Dónde vive | Reusa |
|---|---|---|
| Enum de registro emocional | archivo de política nuevo (patrón de `visual/policy/`) | vocabulario cerrado como `command_center` |
| Mapa registro → subconjunto de familias | política, no código de decisión | `visual/policy/visual-families-v1.json` + `rotation.py` |
| `TopicCandidate` con preocupación/necesidad | schema del "banco de temas" (hoy inexistente, ver `auditoria-automatizacion-segura.md §3.2`) | previo al claim packet |
| Vista "opción" (texto+fuente+certidumbre+límite) | read-model, como `source_verification.py`/`inventory.py` | **lee** el claim packet, nunca lo escribe |
| Etiqueta emocional en la medición | `MeasurementRecord` de la cadena post-aprobación | schema ya existente |

## 11. Qué NO cambia ni autoriza este documento

- No modifica el esquema del claim packet, la skill jurídica ni la visual.
- No baja el umbral de verificación de ningún claim: la emoción elige estilo, no
  contenido.
- No abre ningún gate de arte ni de publicación.
- No declara que la medición exista: la marca como el requisito pendiente que es.
- No crea contenido jurídico nuevo — es dirección, no producción.

## 12. Siguiente paso ejecutable

Cuando el fundador lo confirme, el primer paso barato y reversible es **Fase 1
(estandarización)**: cerrar el enum de registros emocionales y el mapa
registro→familias como archivos de política (sin tocar decisión de código), y
etiquetar los claims ya verificados (`pieza-04`, `linkedin-ray-16`) con su
preocupación y su registro emocional, como prueba de concepto sobre contenido que
ya pasó verificación. Recién después tiene sentido medir — y para medir, primero
hay que cerrar el hueco de métricas de §6.
