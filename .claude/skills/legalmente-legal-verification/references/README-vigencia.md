# Vigencia de fuentes (source freshness)

Validador: `scripts/check-source-freshness.py` · Libro mayor: `source-freshness.json`

## El riesgo

Una fuente oficial puede derogarse, sustituirse o cambiar de URL y **seguir
sosteniendo un claim ya aprobado**. El validador jurídico no lo detecta y no debe
detectarlo: no tiene red por diseño, porque una skill que descarga páginas durante
la validación se puede envenenar desde fuera.

## La separación

| Operación | Quién | Con red | Cuándo |
|---|---|---|---|
| **Investigar** la vigencia y actualizar el libro mayor | humano | sí, fuera del repositorio | cuando toca revisar |
| **Comprobar** la coherencia y derivar el veredicto | este script | **no** | en cada CI |

Este script es determinista y offline. Nunca sale a la red y **nunca modifica un
claim packet**.

## Dos registros distintos, y por qué

| Archivo | Registra |
|---|---|
| `official-source-registry.json` | **organismos** (BOE, Diputados MX, InfoLEG…) |
| `source-freshness.json` | **documentos concretos** y su estado de vigencia |

El libro mayor reutiliza el registro como autoridad única: el hostname debe
pertenecer al organismo declarado, y la jurisdicción y el tipo deben estar entre
los que ese organismo admite.

## Estados

| `verification_status` | Significa |
|---|---|
| `CURRENT` | un humano comprobó su vigencia y no consta sustituida |
| `NEEDS_REVIEW` | vencido el plazo de revisión, o marcado para revisar |
| `SUPERSEDED` | sustituida por otra fuente registrada (`superseded_by`) |
| `REPEALED` | derogada |
| `UNKNOWN` | registrada, pero sin comprobación de vigencia |

## Veredicto de un claim — derivado, nunca almacenado

| Veredicto | Cuándo |
|---|---|
| `CURRENT` | todas sus fuentes registradas y vigentes |
| `REQUIERE_REVISION` | alguna NEEDS_REVIEW, sin registrar, o UNKNOWN donde hace falta vigencia |
| `BLOQUEADO` | alguna SUPERSEDED o REPEALED |

**Por qué derivado y no almacenado:** escribir el veredicto dentro del claim
cambiaría su contenido y, con él, su `contenido_hash_sha256`, invalidando en
silencio una aprobación humana ya firmada. El contenido aprobado no se toca. Lo
que ocurre es que el sistema deja de dejarlo avanzar:

```
FUENTE DESACTUALIZADA  →  CLAIM REQUIERE REVISIÓN
```

Fail-closed donde hay algo en riesgo: un claim con `gate_arte: ABIERTO` cuyo
veredicto no sea `CURRENT` es un **error**. Con el gate cerrado es una
**advertencia** — todavía no hay nada en producción.

## Identificadores

`source_id` = `SRC-` + los 12 primeros hex del SHA-256 de la URL canonicalizada.
Derivarlo del contenido significa que regenerar o reordenar el libro mayor nunca
renumera nada, y que **cambiar la URL crea otra fuente** — que es lo correcto: una
URL nueva no hereda la vigencia comprobada de la vieja. Para enlazarlas están
`supersedes` / `superseded_by`, que el validador exige simétricos y sin ciclos.

La canonicalización conserva query y fragmento: en SPIJ (Perú) la norma concreta
vive en el fragmento, y descartarlo fundiría fuentes distintas en una sola.

## Plazos de revisión

`review_due_at` = `last_verified_at` + la ventana del tipo (180 días para
`NORMA_OFICIAL`, 365 para jurisprudencia y autoridad, 730 para doctrina). No es una
verdad jurídica: es la frecuencia con la que la casa se obliga a volver a mirar.
Un `CURRENT` con el plazo vencido se degrada a `NEEDS_REVIEW` en el cálculo.

## Sobre la siembra inicial

Los `CURRENT` de la primera versión son **transcripción** de lo que los propios
claim packets ya declaraban (`vigencia_comprobada` + `fecha_comprobacion`), no una
comprobación nueva — de ahí `verified_by: "TRANSCRITO_DEL_CLAIM_PACKET"`.
`published_at`, `effective_from` y `effective_to` quedan en `null` porque nadie los
ha verificado: declararlos sin fuente sería inventar un hecho jurídico.

## Uso

```bash
cd .claude/skills/legalmente-legal-verification
python3 scripts/check-source-freshness.py --solo-libro-mayor
python3 scripts/check-source-freshness.py pilot/claim-packets/*.json
python3 scripts/check-source-freshness.py --today 2026-08-27 <paquete.json>
```
