# Contrato de traspaso — Gemini — DRAFT / EXPERIMENTAL

> **DRAFT / EXPERIMENTAL.** No implementado, no probado, no autorizado.

## Papel propuesto

Apoyo multimodal en la fase **visual**, después de que el contenido jurídico esté
aprobado: revisión de legibilidad, contraste, jerarquía tipográfica y encaje del
texto aprobado en el formato.

## Momento exacto en la cadena

Solo **después** de un `ProductionHandoff` válido. Nunca antes: el arte no valida el
contenido jurídico, y las verificaciones van en ese orden (`CLAUDE.md §6`).

## Entrada

```json
{
  "handoff_contract_version": "0.1-DRAFT",
  "sistema": "gemini",
  "tarea": "REVISION_LEGIBILIDAD",
  "entrada": {
    "content_id": "…",
    "texto_aprobado": "literal, no reformulable",
    "advertencia_editorial": "…",
    "jurisdiccion_visible": "…",
    "asset": "referencia local a la imagen o video"
  },
  "salida_esperada": "RESUMEN"
}
```

## Salida admisible

Observaciones sobre la **forma**, con esta estructura:

```json
{
  "legibilidad_movil": "OK | PROBLEMA",
  "jurisdiccion_localizada_en_la_pieza": true,
  "advertencia_localizada_en_la_pieza": true,
  "texto_coincide_literalmente": true,
  "observaciones_visuales": ["…"],
  "procedencia": { "sistema": "gemini", "modelo": "…", "fecha": "AAAA-MM-DD" }
}
```

Estas salidas son **insumo** para que un humano marque las comprobaciones de
`PublicationDecision.qa`. No las marcan ellas.

## Prohibiciones específicas

- **No reformula el texto aprobado**, ni para que quepa mejor. Si no cabe, se
  cambia el diseño o se vuelve a revisión jurídica — nunca se recorta la
  proposición.
- **No genera arte**: Canva se usa para texto y montaje controlados, no para
  generar arte con IA (`CLAUDE.md §6`).
- **No opina sobre corrección jurídica.** Si detecta algo que le parece un error de
  fondo, lo devuelve como observación para revisión humana, y esa observación
  **bloquea** hasta que un humano decida; no lo corrige.
- **No rellena el QA automáticamente.**

## Riesgo principal

Que una revisión de forma se lea como validación de fondo. El diseño de la salida lo
previene: no hay ningún campo en el que Gemini pueda afirmar que el contenido
jurídico es correcto.
