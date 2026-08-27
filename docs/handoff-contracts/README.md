# Contratos de traspaso a sistemas externos — DRAFT / EXPERIMENTAL

> **DRAFT / EXPERIMENTAL.** Nada de este directorio está implementado, probado ni
> autorizado. Son borradores de interfaz para discutir, no capacidades. Ninguna
> sesión debe asumir que existe integración con estos sistemas. Regla vigente de
> `CLAUDE.md §2`: una mención en un documento no es una capacidad implementada.

## Regla común a todos los contratos

Ningún sistema externo —sea Grok, Manus, Gemini o cualquier otro— puede:

1. **Aprobar un claim.** La aprobación jurídica es humana y nominal (`CLAUDE.md §4`).
2. **Abrir un gate.** El gate lo calcula el validador canónico, nunca un tercero.
3. **Autorizar publicación.** Exige una `PublicationDecision` humana.
4. **Ser citado como fuente.** Ninguna IA es fuente jurídica.
5. **Escribir en el repositorio.** El traspaso es de datos, no de permisos.

Todo sistema externo opera **antes** de la verificación o **al margen** de ella, y
su salida entra al sistema como *material en bruto sin verificar*, con el mismo
estatuto que un borrador humano: tiene que pasar el validador completo.

## Formato del traspaso

Entrada al sistema externo: un objeto explícito de tarea.
Salida del sistema externo: **texto sin estatuto**, más metadatos de procedencia.

```json
{
  "handoff_contract_version": "0.1-DRAFT",
  "sistema": "grok | manus | gemini",
  "tarea": "…",
  "entrada": { "…": "…" },
  "salida_esperada": "TEXTO_SIN_VERIFICAR | LISTA_DE_CANDIDATOS | RESUMEN",
  "prohibiciones": [
    "no afirmar contenido jurídico como verificado",
    "no inventar citas, artículos ni sentencias",
    "no atribuir frases sin autor y obra identificables",
    "no usar datos identificables de experiencia profesional privada"
  ],
  "procedencia": {
    "sistema": "…",
    "modelo": "…",
    "fecha": "AAAA-MM-DD",
    "prompt_hash_sha256": "…"
  }
}
```

`procedencia` es obligatorio en el borrador: si algún día entra material generado
por un tercero, debe poder rastrearse de dónde salió.

## Contratos

- [`grok.md`](grok.md) — radar editorial / señal de actualidad.
- [`manus.md`](manus.md) — ejecución de tareas operativas de larga duración.
- [`gemini.md`](gemini.md) — apoyo multimodal y revisión de legibilidad.

## Estado

| Sistema | Contrato | Implementado | Probado | Autorizado |
|---|---|---|---|---|
| Grok | borrador | no | no | no |
| Manus | borrador | no | no | no |
| Gemini | borrador | no | no | no |
