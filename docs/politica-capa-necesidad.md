# Política operativa: capa de interpretación de necesidad humana

Instrucción expresa del fundador (2026-09-12). **Complementa** la arquitectura
vigente; no reemplaza Constitución, fuentes canónicas, gates jurídicos ni
historial. Es política, no implementación: no toca esquema, skill, código ni CI.
El desarrollo conceptual largo vive en `docs/direccion-trazabilidad-emocional.md`;
esto es la regla corta que un agente sigue.

## Qué es esta capa

Una interpretación de necesidad que usa la **preocupación emocional como puerta
de entrada, nunca como salida**. La salida siempre es una o más **opciones
jurídicas trazables** — o la declaración honesta de que no hay materia jurídica.

```
[emoción = ENTRADA]  →  necesidad concreta  →  pregunta jurídica  →  [OPCIÓN(es) = SALIDA]
                                                                       cada una: fuente + límite + incertidumbre
   · si detrás no hay pregunta jurídica → se dice; no se fabrica una
   · si no se puede decidir → FRONTERA/INDETERMINADO: se nombra el hecho mínimo faltante, no se fuerza
```

## Principios obligatorios

1. **La emoción no es dato jurídico, y no se construye una taxonomía psicológica.**
   No se diagnostica a nadie, no se infieren intenciones ni estado mental. Lo que
   se registra es la **preocupación observable** que el usuario expresa y su
   **contexto funcional** (la situación, no la persona). Ese registro elige el tono
   y el estilo del *output* y —en agregado— alimenta la detección de patrones de
   necesidad (finalidad futura declarada por el fundador, aún **no** implementada,
   `CLAUDE.md §2`: **LegalMente Radar** — priorizar verificación, descubrir temas y
   herramientas útiles). Nunca entra como insumo del análisis jurídico ni se guarda
   como un perfil de la persona.
2. **Toda salida incluye fuente, límite y margen de incertidumbre.** Sin las tres,
   no hay salida. Una opción nunca muestra más certeza que su claim.
3. **La preocupación se traduce en necesidad concreta y en pregunta jurídica.** Si
   no se puede formular una pregunta jurídica real, la preocupación **no es materia
   jurídica** y así se declara.

## Cómo se monta sobre el claim packet (sin duplicar ni crear sistema paralelo)

La capa **no posee verdad jurídica**. Es entrada (interpreta) + salida (vista).
Fuente, certidumbre y límite **ya existen** en el claim packet; la opción los
**lee**, no los reescribe.

| Elemento de la opción | De dónde sale (claim packet v4) |
|---|---|
| Fuente verificada | `claims[].fuentes[]` + `registro_oficial_id` + nivel real (1-4) |
| Margen de incertidumbre | `estado` (los 4 estados) + `confianza` |
| Límite | `alcance`, `jurisdiccion`, `variaciones_materiales`, `redaccion_prohibida` |

Posición en el flujo actual: la capa se sitúa **antes** del claim packet (entrada:
preocupación → pregunta jurídica) y **después** de la verificación (salida: opción
= read-model, como `visual/source_verification.py` lee sin escribir). No inventa un
segundo canon (`docs/contrato-motor-masivo.md`).

## Clasificación de la preocupación — tres estados, sin forzar

Toda preocupación cae en uno de tres estados. **La ambigüedad no se resuelve
forzando la clasificación** (modificación del fundador, 2026-09-12 — sustituye la
regla anterior de "fallar hacia el derecho"):

1. **`ES_MATERIA_JURIDICA`** — hay una pregunta jurídica formulable.
2. **`NO_ES_MATERIA_JURIDICA`** — no hay pregunta jurídica; se declara, no se fabrica
   una.
3. **`FRONTERA_INDETERMINADO`** — no se puede decidir todavía. **No se fuerza a SÍ ni
   a NO.** Se identifica el **hecho mínimo faltante** que permitiría decidir, se
   nombra de forma general (sin intake ni PII), y se enruta a verificación **cuando
   corresponda** (solo si al aparecer ese hecho la preocupación resulta jurídica). La
   emoción nunca decide la clasificación.

## Regla fail-closed sobre la opción (idéntica a la del resto del sistema)

- **`ES_MATERIA_JURIDICA` + claim verificado** (`APTO_PARA_NARRATIVA` /
  `APTO_CON_MATICES`) → se emite opción, con su certidumbre y límite reales.
- **`ES_MATERIA_JURIDICA` sin claim verificado** (`REQUIERE_INVESTIGACION`,
  `BLOQUEADO`, o inexistente) → **no hay opción.** Va a cola de verificación. No se
  consuela afirmando algo no verificado.
- **`NO_ES_MATERIA_JURIDICA`** → se separa la emoción del derecho y se ofrece un
  puente general (no un dead-end), **sin PII y sin intake de caso** — nunca "cuéntame
  tu caso".
- **`FRONTERA_INDETERMINADO`** → **no hay opción** mientras siga indeterminado; la
  salida es el hecho mínimo faltante, no una respuesta jurídica.

## Qué NO hace esta capa (fuera de alcance, explícito)

- No abre gates de arte ni de publicación.
- No baja el umbral de verificación de ningún claim: la emoción elige tono, no
  contenido.
- No diagnostica emociones, relaciones ni personas.
- No recolecta datos personales ni recibe casos individuales.
- No sustituye la revisión de un abogado humano.
- No implementa nada en producción: hoy solo existe esta política y el piloto
  documentado en `docs/piloto-capa-necesidad.json`.

## Piloto

6 casos reales documentados de extremo a extremo en
`docs/piloto-capa-necesidad.json`, anclados solo en claims ya verificados. Cubre
los tres estados de clasificación y las ramas del fail-closed: opción emitida (con
matices / con aprobación / gate abierto), **no es materia jurídica** (PC-04), materia
jurídica **sin claim verificado** (PC-05, cola de verificación) y
**`FRONTERA_INDETERMINADO`** (PC-06, cambio de puesto — se nombra el hecho mínimo
faltante en vez de forzar la clasificación).
