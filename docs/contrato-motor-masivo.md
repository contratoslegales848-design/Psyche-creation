# Contrato técnico del motor de producción masiva

Estado: **contrato definido, motor NO construido.** Este documento fija dónde vive
cada dato del futuro motor para que, cuando se construya, no invente estructuras
paralelas a las que ya existen.

Regla de partida: **no se crea un sistema paralelo.** Antes de proponer un modelo
nuevo se revisó qué había. No existe hoy ningún `ContentUnit` ni `InventoryItem` en
el repositorio — lo que existe son dos estructuras ya probadas (el claim packet y la
cadena post-aprobación) más el artefacto de contenido. Los campos del motor se
reparten entre ellas.

---

## 1. Dónde vive cada campo

| Campo del motor | Dónde vive hoy | Estado |
|---|---|---|
| `MATERIA` | `content/*.json` → `taxonomia.materia` | **añadido** |
| `SUBMATERIA` | `content/*.json` → `taxonomia.submateria` | **añadido** |
| `CONCEPTO` | `content/*.json` → `taxonomia.concepto` | **añadido** |
| `SITUACION_HUMANA` | `content/*.json` → `taxonomia.situacion_humana` | **añadido** |
| `CONTENT_TYPE` | `content/*.json` → `taxonomia.content_type` | **añadido** |
| `JURISDICTION_LAYER` | `claim.alcance`, replicado y **verificado** en `procedencia.jurisdiction_layer` | ya existía |
| `SOURCE_STATE` | libro mayor `source-freshness.json`, derivado por claim | **añadido** |
| `TERRITORY` | `claim.jurisdiccion` + `jurisdicciones_revisadas[].pais` | ya existía |
| `EDITORIAL_STATUS` | `claim.estado` + `claim.revision_humana.estado` | ya existía |
| `VISUAL_STATUS` | `claim.gate_arte` + `ProductionHandoff.status` | ya existía |
| `PUBLICATION_STATUS` | `PublicationDecision.decision` + `PublicationRecord.status` | ya existía |
| `MEASUREMENT_DUE_AT` | `PublicationRecord.measurement_due_at` | ya existía |

Solo los cinco campos de taxonomía editorial eran nuevos. El resto ya estaba, y
duplicarlo en un modelo aparte habría creado exactamente el problema que este
documento evita: dos verdades sobre el mismo hecho.

## 2. Por qué la taxonomía vive en el artefacto de contenido

Porque es una propiedad de **la pieza**, no de la afirmación jurídica. Un mismo
claim (por ejemplo, la distinción comodato/mutuo) puede sostener piezas de tipos
distintos y dirigidas a situaciones humanas distintas. Meter la taxonomía en el
claim packet habría acoplado la clasificación editorial a la verificación jurídica
y —peor— habría cambiado el `contenido_hash_sha256` de cada claim al reclasificar,
invalidando aprobaciones humanas ya firmadas.

## 3. Ciclo de vida de una unidad de contenido

```
taxonomía (materia/submateria/concepto/situación/tipo)
        │
        ▼
claim packet ── verificación de fuentes ──► APTO_PARA_NARRATIVA
        │
        ▼
aprobación humana firmada (hash) ──► gate_arte ABIERTO
        │
        ▼
ProductionHandoff (APROBADO_QA)
        │
        ▼
content/*.json  procedencia.modo = GOBERNADO   ──► renderizador
        │
        ▼
PublicationDecision AUTORIZADA (humana, separada)
        │
        ▼
PublicationRecord ──► MeasurementRecord (+7 días) ──► Learning
```

Cada flecha ya está verificada por código. Lo que el motor masivo añadirá es
**volumen y planificación**, no eslabones nuevos.

## 4. Estado de la infraestructura del motor

1. **Inventario consultable** — ✅ **implementado** el 2026-08-27
   (`scripts/inventory.py`, `inventory/README.md`). JSON generado determinísticamente
   desde los artefactos, sin base de datos nueva y sin autoridad propia.
2. **Vigencia de fuentes** — ✅ **implementada** (`scripts/check-source-freshness.py`).
   No estaba en la lista original y resultó ser prioritaria: sin ella, una norma
   derogada seguiría sosteniendo un claim aprobado.
3. **Planificación de cobertura** — pendiente. Es un informe sobre el inventario
   (qué casillas de `materia/submateria/concepto` faltan), no un sistema nuevo.
4. **Detección de paráfrasis** — pendiente. El control actual es literal (§5). Solo
   merece la pena cuando el volumen lo justifique, y probablemente fuera del validador.
5. **Ingesta de métricas** — pendiente. Hoy las cifras se teclean. Sin lectura
   automatizada, el bucle de aprendizaje no escala.
6. **Vigilancia activa de cambios normativos** — pendiente y **no es código de
   validación**: exige red, y el validador no la tendrá. Sería un proceso de research
   separado que marque fuentes para revisión en el libro mayor.

## 5. Anti-duplicados: qué se detecta y qué no

Implementado, determinista y barato. En `validate-content-provenance.py` (por
artefacto) y en `inventory.py` (sobre el índice completo):

| Control | Detecta |
|---|---|
| `content_id` único | la misma pieza registrada dos veces |
| `id` de composición único | colisión en el renderizador |
| huella normalizada de la frase | la misma pieza con otro ID, salvo mayúsculas, tildes y signos |
| casilla `materia/submateria/concepto` | el mismo concepto producido dos veces |
| `publication_url` única | dos piezas apuntando a la misma publicación |

**No** detecta paráfrasis ni reformulación semántica: eso exigiría embeddings o un
motor semántico, y hoy no lo hay. Se declara como límite, no se disimula — y hay una
prueba que lo fija por escrito para que nadie suponga lo contrario.

## 6. Lo que el contrato NO autoriza

- No autoriza construir la fábrica de contenido. `CLAUDE.md §6` sigue vigente: no se
  producen bancos grandes de temas mientras el piloto no se haya publicado y medido.
- No autoriza publicar. Un artefacto de producción válido habilita **producir**.
- No sustituye la aprobación humana en ninguno de sus dos puntos: la jurídica
  (claim) y la de publicación (`PublicationDecision`).
