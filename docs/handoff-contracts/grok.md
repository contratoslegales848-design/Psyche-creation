# Contrato de traspaso — Grok — DRAFT / EXPERIMENTAL

> **DRAFT / EXPERIMENTAL.** No implementado, no probado, no autorizado.

## Papel propuesto

Radar editorial: detectar **de qué se está hablando** en materia jurídica en el
espacio hispanohablante, para alimentar la selección de temas. Nada más.

## Entrada

```json
{
  "handoff_contract_version": "0.1-DRAFT",
  "sistema": "grok",
  "tarea": "RADAR_EDITORIAL",
  "entrada": {
    "ventana_dias": 7,
    "ambito": "panhispánico",
    "materias": ["civil", "laboral", "penal", "digital"],
    "excluir": ["casos individuales identificables", "polémica política partidista"]
  },
  "salida_esperada": "LISTA_DE_CANDIDATOS"
}
```

## Salida admisible

Una lista de **temas**, no de afirmaciones:

```json
{
  "candidatos": [
    {
      "tema": "…",
      "por_que_ahora": "…",
      "senal_observada": "…",
      "jurisdicciones_implicadas": ["…"],
      "estatuto": "SIN_VERIFICAR"
    }
  ],
  "procedencia": { "sistema": "grok", "modelo": "…", "fecha": "AAAA-MM-DD" }
}
```

`estatuto: "SIN_VERIFICAR"` es obligatorio y no admite otro valor.

## Prohibiciones específicas

- No devuelve afirmaciones jurídicas, solo temas. Si devuelve una regla, esa regla
  **no entra**: se descarta y se investiga desde fuente oficial.
- No devuelve citas. Ninguna frase atribuida a un autor procedente de este canal
  puede publicarse sin fuente identificable independiente (`CLAUDE.md §4`).
- No devuelve casos individuales, nombres de personas ni de empresas.
- Su señal de actualidad **no** es evidencia de vigencia normativa.

## Qué pasa después

El tema entra en la matriz de contenido. La afirmación jurídica se construye desde
cero contra fuente oficial, se registra en un claim packet y pasa el validador. El
origen del tema no otorga ningún privilegio en la verificación.

## Riesgo principal

Sesgo de actualidad: lo que más se comenta no es lo más relevante ni lo más
riguroso, y suele ser lo más nacional. Contrapeso: la regla de neutralidad
jurisdiccional se aplica igual, y un tema viral de un solo país entra como Capa C
con el país visible desde el título.
