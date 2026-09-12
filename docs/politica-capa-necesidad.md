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
                              (si detrás no hay pregunta jurídica → se dice; no se fabrica una)
```

## Principios obligatorios

1. **La emoción no es dato jurídico.** No se diagnostica, no se infieren
   intenciones ni estado psicológico. El registro emocional se clasifica por la
   **superficie de lo expresado** (una etiqueta de una lista cerrada), solo para
   elegir tono y estilo visual — nunca entra como insumo del análisis jurídico ni
   se guarda como una afirmación sobre la persona.
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

## Regla fail-closed (idéntica a la del resto del sistema)

- **Hay pregunta jurídica + claim verificado** (`APTO_PARA_NARRATIVA` /
  `APTO_CON_MATICES`) → se emite opción, con su certidumbre y límite reales.
- **Hay pregunta jurídica pero sin claim verificado** (`REQUIERE_INVESTIGACION`,
  `BLOQUEADO`, o inexistente) → **no hay opción.** Va a cola de verificación. No se
  consuela afirmando algo no verificado.
- **No hay pregunta jurídica** → se declara "no es materia jurídica", se separa la
  emoción del derecho, y se ofrece un puente general (no un dead-end), **sin PII y
  sin intake de caso** — nunca "cuéntame tu caso".
- **Ante la duda de si es materia jurídica**, se trata como que **sí** lo es y se
  enruta a verificación (se falla hacia el derecho, no en su contra).

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

5 casos reales documentados de extremo a extremo en
`docs/piloto-capa-necesidad.json`, anclados solo en claims ya verificados. Cubre
las tres ramas del fail-closed, incluidos un caso que **no es materia jurídica** y
uno que **sí lo es pero aún no está verificado**.
