# Cadena post-aprobación

Este directorio cubre el tramo que **empieza donde termina** `validate-claim-packet.py`:
desde que una pieza tiene aprobación jurídica humana hasta que se mide lo publicado.

Validador: `scripts/validate-publication-chain.py`
Pruebas: `scripts/test_validate_publication_chain.py`

## 1. El problema que resuelve

Antes de esto, el repositorio representaba un solo permiso —el gate de arte— y
no distinguía entre **producir** y **publicar**. Eso deja abierta la posibilidad
de que abrir un gate se lea, en la práctica, como autorización para publicar.

Cuatro estados **no equivalentes**, en orden:

| Estado | Qué significa | Quién lo otorga |
|---|---|---|
| `estado: APTO_PARA_NARRATIVA` | la afirmación resiste verificación de fuentes | el validador (determinista) |
| `revision_humana.estado: APROBADO` | un humano firmó la afirmación | persona identificada |
| `gate_arte: ABIERTO` | se puede producir arte y narrativa | consecuencia de lo anterior |
| `PublicationDecision: AUTORIZADA` | **se puede publicar** | persona identificada, decisión posterior y separada |

El último eslabón vive en este directorio, **fuera del claim packet**. Es
deliberado: si viviera dentro, cada decisión de publicación cambiaría el
contenido del claim y por tanto su `contenido_hash_sha256`, invalidando la
aprobación jurídica ya firmada. La cadena de publicación referencia el claim
packet; nunca lo modifica.

## 2. Los cinco registros

Cada registro es un objeto JSON con `record_type` y `schema_version: "1.0"`.
Un archivo puede contener un registro o una lista de registros.

```
ProductionHandoff  →  PublicationDecision  →  PublicationRecord  →  MeasurementRecord  →  Learning
   (¿qué produzco?)      (¿puedo publicar?)      (¿qué se publicó?)     (¿qué pasó?)      (¿qué aprendo?)
```

### `ProductionHandoff`
Traslada a producción **exactamente** lo aprobado. Exige:
- `claim_packet` resuelto dentro de la skill, estructuralmente válido, con `gate_global_arte: "ABIERTO"`.
- Por cada claim: `approved_claim_hash` idéntico a `compute_content_hash(claim)` y `approved_text` idéntico a `texto_exacto`.
- `advertencia_editorial` no vacía y `redacciones_prohibidas` que incluya cada `redaccion_prohibida` declarada por los claims.

Si el texto o el contenido del claim cambian después de la aprobación, el hash
deja de coincidir y el handoff falla. Ese es el mecanismo antimutación.

Los handoffs reales viven en `publication/records/`. Desde ahí los lee también
`scripts/validate-content-provenance.py` (en la raíz del repositorio), que exige que
todo artefacto de `content/` en modo `GOBERNADO` apunte a un handoff válido. Un
handoff que no valida no se indexa: el artefacto que lo invoque quedará sin
procedencia.

### `PublicationDecision`
La autorización humana de publicación. `decision` ∈ `AUTORIZADA | RECHAZADA | PENDIENTE`.
Solo `AUTORIZADA` habilita publicar, y exige firma completa (`decisor`, `fecha` ISO,
`observaciones`), `advertencia_editorial_verificada: true`, al menos una plataforma
en `plataformas_autorizadas`, y **todas** las comprobaciones de `qa` en `true`:

`provenance_claim_packet`, `hash_coincide`, `jurisdiccion_visible`,
`advertencia_editorial_presente`, `texto_coincide_con_aprobado`, `legibilidad_movil`.

Son comprobaciones deterministas y verificables. Deliberadamente **no** incluyen
calidad estética ni juicio profesional: eso no se automatiza y sigue siendo humano.

Rechazar no exige requisitos; lo que exige requisitos es autorizar.

### `PublicationRecord`
Lo que efectivamente se publicó: `content_id`, `platform`, `format`,
`publication_url` (http/https obligatoria si `status: PUBLICADA`), `asset_version`,
`published_at`, y `publication_decision_id` — **no existe publicación sin decisión**.
`measurement_due_at` debe ser `published_at` + 7 días exactos.

### `MeasurementRecord`
Métricas a la ventana declarada. `available_metrics` y `metrics` deben coincidir
clave por clave: ni una métrica declarada disponible que falte, ni una métrica
presente que no se haya declarado disponible. No se inventan cifras.

### `Learning`
`observation`, `hypothesis`, `decision`, `reuse`, `next_action`. Exige que exista
una medición previa del mismo `content_id`: no se extraen aprendizajes de métricas
inexistentes.

## 3. Content ID

`^[A-Z0-9][A-Z0-9\-]{2,63}$`. Es la clave que une handoff → decisión → publicación
→ medición → aprendizaje, y la que permite detectar duplicados. Una misma pieza no
puede registrarse dos veces en la misma plataforma.

## 4. Uso

```bash
cd .claude/skills/legalmente-legal-verification
python3 scripts/validate-publication-chain.py publication/fixtures/validos/cadena-completa.json
python3 scripts/validate-publication-chain.py --dir publication/records
```

Salida `0` = cadena coherente. `1` = registro inválido, eslabón roto o duplicado.
Los registros pasados en una misma invocación se validan **como una sola cadena**.

## 5. Fixtures

- `publication/fixtures/claim-packet-aprobado.json` — claim packet sintético con
  gate ABIERTO y revisor ficticio. Es la única base aprobada que usan las fixtures;
  ningún paquete real del piloto se toca.
- `publication/fixtures/validos/` — cadenas que deben pasar (exit 0).
- `publication/fixtures/invalidos/` — una fixture por modo de fallo (exit 1).

## 6. Lo que este validador NO hace

- No publica, no llama a ninguna plataforma, no tiene red.
- No decide por un humano: solo comprueba que la decisión humana **conste, esté
  completa y sea coherente** con lo aprobado.
- No juzga calidad editorial ni visual.
- No sustituye a `validate-claim-packet.py`: lo invoca y se apoya en él.
