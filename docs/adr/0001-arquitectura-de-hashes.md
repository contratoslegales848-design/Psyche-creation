# ADR 0001 — Arquitectura de hashes: un solo hash, por ahora

- **Fecha:** 2026-08-27
- **Estado:** ACEPTADA (con revisión obligatoria antes de escalar a producción continua)
- **Ámbito:** `.claude/skills/legalmente-legal-verification/`

## Contexto

Hoy existe **un solo hash** en todo el sistema:

```python
HASH_EXCLUDED_FIELDS = {"revision_humana", "gate_arte"}

def compute_content_hash(claim):
    canonical = {k: v for k, v in claim.items() if k not in HASH_EXCLUDED_FIELDS}
    return sha256(json.dumps(canonical, sort_keys=True, ensure_ascii=True,
                             separators=(",", ":")).encode("utf-8")).hexdigest()
```

Se almacena en `revision_humana.contenido_hash_sha256` y responde exactamente a una
pregunta: **¿el contenido del claim es bit a bit el mismo que el humano firmó?**

Se evaluó si hacían falta tres hashes distintos:

| Hash propuesto | Pregunta que respondería |
|---|---|
| `semantic_claim_hash` | ¿la *proposición* sigue siendo la misma aunque cambie la redacción? |
| `evidence_snapshot_hash` | ¿la *fuente* sigue diciendo lo mismo que cuando se consultó? |
| `narrative_hash` | ¿la pieza publicada corresponde al claim aprobado? |

## Decisión

**No se añade ningún hash nuevo.** Se mantiene `compute_content_hash` como único
hash, y se cubre la tercera pregunta —la única con riesgo material hoy— sin
criptografía adicional, mediante la cadena post-aprobación
(`validate-publication-chain.py`): el `ProductionHandoff` transporta
`approved_claim_hash` y `approved_text`, y el validador comprueba que ambos sigan
coincidiendo con el claim aprobado. Si el texto cambia camino de arte, falla.

## Razones

**Contra `semantic_claim_hash`.** No existe una función determinista que decida si
dos redacciones expresan la misma proposición jurídica. Cualquier implementación
sería un modelo, y un modelo **no es fuente jurídica** (CLAUDE.md §4). Un hash
semántico daría una falsa sensación de continuidad: dos textos "equivalentes" según
el modelo pueden diferir en un matiz que cambie la regla. La equivalencia semántica
la decide un humano, y ya hay un mecanismo para eso: reaprobar. Un cambio de
redacción invalida el hash y **debe** volver a revisión. Eso es la propiedad
deseada, no un defecto a suavizar.

**Contra `evidence_snapshot_hash`.** Sería útil —las fuentes cambian— pero hoy no es
implementable con honestidad: el validador **no tiene red por diseño**, y no la va a
tener (una skill que descarga páginas durante la validación es una skill que se
puede envenenar desde fuera). Hashear un snapshot exige guardar el snapshot, y eso
plantea preguntas de peso jurídico (derechos sobre el texto oficial almacenado) y
operativas (¿quién lo captura, con qué autoridad, con qué periodicidad) que no
están resueltas. El sustituto actual es explícito y suficiente para el volumen
actual: `fecha_consulta`, `fecha_comprobacion`, `vigencia_comprobada`,
`texto_exacto_consultado` y `localizador`. Es un control humano fechado, no
criptográfico, y se declara como tal.

**Contra `narrative_hash`.** Lo que hacía falta no era otro hash, sino un eslabón:
alguien tenía que comprobar que lo que llega a arte es lo aprobado. Ese eslabón ya
existe (`ProductionHandoff`) y usa el hash que ya había. Un segundo hash sobre el
mismo contenido habría añadido una superficie de desincronización sin añadir una
sola garantía.

## Consecuencias

Aceptadas:
- Reformular un claim, aunque sea para mejorar su redacción, **invalida la
  aprobación**. Es fricción deliberada.
- El sistema **no detecta** que una fuente oficial haya cambiado después de la
  consulta. Riesgo real y declarado; se mitiga con la fecha de comprobación y con
  revisión humana, no con código.

Pendientes de revisar (disparadores para reabrir esta ADR):
1. Si se pasa de un piloto de 3 piezas a producción continua, la deriva de fuentes
   deja de ser un riesgo teórico → reconsiderar `evidence_snapshot_hash` **fuera**
   del validador (un proceso aparte, con red, que solo marque para re-revisión).
2. Si aparece una obligación de conservar prueba de lo publicado, `narrative_hash`
   sobre el asset final (no sobre el claim) pasa a tener sentido propio.

## Alternativa descartada explícitamente

Meter la decisión de publicación **dentro** del claim packet. Habría cambiado el
contenido del claim y, por tanto, su hash — invalidando aprobaciones jurídicas ya
firmadas cada vez que alguien decidiera publicar. Por eso la cadena post-aprobación
vive fuera del packet y solo lo referencia.
