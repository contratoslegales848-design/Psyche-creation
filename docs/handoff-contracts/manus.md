# Contrato de traspaso — Manus — DRAFT / EXPERIMENTAL

> **DRAFT / EXPERIMENTAL.** No implementado, no probado, no autorizado.

## Papel propuesto

Ejecución de tareas operativas de larga duración que no tocan contenido jurídico:
recopilación de material público, organización de archivos, seguimiento de tareas.

## Entrada

```json
{
  "handoff_contract_version": "0.1-DRAFT",
  "sistema": "manus",
  "tarea": "RECOPILACION_OPERATIVA",
  "entrada": {
    "objetivo": "…",
    "fuentes_permitidas": ["dominios oficiales del registro"],
    "entregable": "listado con URL, título, organismo y fecha de consulta"
  },
  "salida_esperada": "RESUMEN"
}
```

## Prohibiciones específicas

- **No redacta contenido publicable.** Ni hooks, ni títulos, ni cuerpos.
- **No interpreta normas.** Puede localizar un texto; no puede decir qué significa.
- **No escribe en el repositorio ni en Drive.** Entrega, no ejecuta.
- **No accede a material confidencial.** Nada del Addendum ni de experiencia
  profesional privada sale de su ámbito local (`CLAUDE.md §5`).
- **No publica en ninguna plataforma.** Ninguna automatización publica
  (`CLAUDE.md §6`).

## Salida admisible

Material bruto con procedencia: URL, organismo, fecha de consulta, localizador.
Todo lo que devuelva entra como *candidato a fuente*, y debe pasar por el registro
oficial (`references/official-source-registry.json`) y por la verificación de
fuente del validador antes de sostener nada.

## Riesgo principal

Un agente de larga duración con permisos amplios es la superficie más peligrosa del
catálogo: puede escribir mucho, en muchos sitios, sin supervisión continua. Por eso
este contrato es deliberadamente el más estrecho de los tres: **solo lectura de
fuentes públicas y entrega de listados**. Cualquier ampliación exige decisión
expresa del fundador y su propio ejercicio de red team.
