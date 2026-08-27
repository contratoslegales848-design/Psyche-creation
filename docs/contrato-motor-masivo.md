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
| `SOURCE_STATE` | `claim.fuentes[].verificacion_fuente` + `registro_oficial_id` | ya existía |
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

## 4. Lo que el motor necesitará y todavía no existe

1. **Un inventario consultable.** Hoy la unicidad se comprueba archivo a archivo en
   `validate-content-provenance.py`. A escala de cientos de piezas hará falta un
   índice materializado (un JSON generado, no una base de datos nueva) con
   `content_id`, taxonomía, huella y estados.
2. **Planificación de cobertura.** Qué casillas de `materia/submateria/concepto`
   están cubiertas y cuáles no. Es un informe sobre el inventario, no un sistema.
3. **Detección de paráfrasis.** El control actual es literal (ver §5). Solo merece
   la pena cuando el volumen lo justifique, y probablemente fuera del validador.
4. **Ingesta de métricas.** Hoy las cifras se teclean. Sin lectura automatizada, el
   bucle de aprendizaje no escala.

## 5. Anti-duplicados: qué se detecta y qué no

Implementado, determinista y barato:

| Control | Detecta |
|---|---|
| `content_id` único | la misma pieza registrada dos veces |
| `id` de composición único | colisión en el renderizador |
| huella normalizada de la frase | la misma pieza con otro ID, salvo mayúsculas, tildes y signos |
| casilla `materia/submateria/concepto` | el mismo concepto producido dos veces |

**No** detecta paráfrasis ni reformulación semántica: eso exigiría un motor
semántico, y hoy no lo hay. Se declara como límite, no se disimula.

## 6. Lo que el contrato NO autoriza

- No autoriza construir la fábrica de contenido. `CLAUDE.md §6` sigue vigente: no se
  producen bancos grandes de temas mientras el piloto no se haya publicado y medido.
- No autoriza publicar. Un artefacto de producción válido habilita **producir**.
- No sustituye la aprobación humana en ninguno de sus dos puntos: la jurídica
  (claim) y la de publicación (`PublicationDecision`).
