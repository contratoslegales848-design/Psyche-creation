# Convergencia del registro oficial — `MERGE_CANDIDATE`

**Fecha:** 2026-09-03 · **Base:** `origin/main` en `ef7ffdd` · **Rama:** `claude/registro-oficial-convergencia`
**Estado:** `MERGE_CANDIDATE` — **no aprobado**, no publicado, sin merge. 4 archivos.

## Por qué existe este PR

La rama de trabajo `claude/legalmente-integration-surgery-nap17t` partió de un registro de **22
entradas** y le añadió 4. `origin/main`, entretanto, llegó a **26** por un camino distinto. Los
conjuntos no se solapan:

| | Entradas |
|---|---|
| Solo en `main` | `secretariasenado-gov-co`, `tribunalconstitucional-es`, `oas-org`, `corteidh-or-cr` |
| Solo en la rama de trabajo | `aepd-es`, `inai-org-mx`, `sic-gov-co`, `ilo-org` |

Ambos registros declaran «26 entradas» y ambos son correctos por separado. Fusionar la rama de
trabajo tal cual **habría borrado cuatro entradas de `main`** sin que ningún error lo señalara: el
validador falla cerrado ante un hostname ausente, así que la pérdida se habría manifestado como
fuentes de la OEA, la Corte IDH, el Tribunal Constitucional español y el Senado colombiano cayendo
silenciosamente por debajo de Nivel 1.

Este PR converge el registro por **adición pura sobre `main`** y añade la prueba que impide que
vuelva a ocurrir. No porta claim packets, copy, salidas ni componentes: solo el registro.

## Qué cambia

**31 entradas** (26 de `main` + 5). El validador no se modifica: lee el registro de forma genérica,
así que añadir entradas no toca una línea de `validate-claim-packet.py`.

| `id` | Organismo | Ámbito | Vigencia |
|---|---|---|---|
| `aepd-es` | Agencia Española de Protección de Datos | España | `VIGENTE` |
| `sic-gov-co` | Superintendencia de Industria y Comercio (Colombia) | Colombia | `VIGENTE` |
| `ilo-org` | Organización Internacional del Trabajo | Internacional | `VIGENTE` |
| `inai-org-mx` | INAI | México | **`HISTORICO`** |
| `sabg-buengobierno-mx` | Secretaría Anticorrupción y Buen Gobierno (México) | México | `VIGENTE` |

### El INAI ya no es autoridad vigente

La entrada del INAI no se registra como una autoridad más. La reforma constitucional de
simplificación orgánica (publicada en diciembre de 2024) extinguió el organismo autónomo; la
disolución efectiva se sitúa en marzo de 2025 y sus funciones se repartieron: **protección de datos
personales a la Secretaría Anticorrupción y Buen Gobierno**, acceso a la información a
«Transparencia para el Pueblo».

Registrarlo como si siguiera vigente habría permitido escribir «la autoridad mexicana de datos
personales exige…» citando a un organismo que ya no existe. Por eso el registro incorpora un tercer
eje, `vigencia_institucional`, y la sucesión explícita en `sucedido_por` / `sucede_a`. Una entrada
`HISTORICO` sigue siendo fuente válida **para el periodo en que fue competente, con la fecha
visible**; nunca para una afirmación en presente.

**Límite declarado:** las fechas exactas de extinción y de traspaso de competencias **no** están
verificadas contra el DOF por este agente. Requieren comprobación humana antes de que ningún claim
que dependa de ellas alcance Nivel 1.

### Identidad verificada ≠ contenido verificado

`WebFetch` sigue `EGRESS_BLOCKED`; `WebSearch` no. Con esa asimetría se puede acreditar **a quién
pertenece un dominio**, y no se puede acreditar **qué dice un texto**. El registro separa ahora las
dos cosas, y ninguna prueba las colapsa:

| Eje | Campo | Estado hoy |
|---|---|---|
| Identidad del dominio | `verificacion_identidad` | `SOURCE_IDENTITY_VERIFIED` en las 5 nuevas (WebSearch, 2026-09-03) |
| Contenido jurídico leído | `verificacion_contenido` | `SOURCE_CONTENT_NOT_VERIFIED` en **todas**, sin excepción |
| Vigencia del organismo | `vigencia_institucional` | 4 `VIGENTE`, 1 `HISTORICO` |

Esto **cierra** la decisión pendiente «verificar los cuatro hostnames»: las entradas ya no descansan
en una orden, descansan en evidencia de identidad. Y **no abre** nada más: identidad verificada no
abre gate, no acredita vigencia normativa y no sustituye la lectura del texto. Una fuente sigue
necesitando `texto_exacto_consultado` y `vigencia_comprobada` en su propio claim para llegar a
Nivel 1. Los 13 claims de la rama de trabajo siguen en `REQUIERE_INVESTIGACION` con gate `CERRADO`;
este PR no mueve ni uno.

## La prueba nueva

`.claude/skills/legalmente-legal-verification/scripts/test_official_source_registry.py` — 25 pruebas
deterministas, sin red, que no comprueban que el registro «esté bien escrito» sino que **no se pueda
usar para colar autoridad**. Se ejecuta en CI.

**Preservación:** los 26 identificadores de `main` están escritos literalmente en el archivo de
prueba, no derivados del propio registro. Una lista derivada no puede detectar que el registro perdió
una entrada — que es exactamente el fallo que este PR corrige.

**Verificado por mutación, no por afirmación.** Ocho mutaciones adversariales, aplicadas una a una;
las ocho fueron detectadas:

| Mutación | Detectada |
|---|---|
| Borrar `oas-org` (el fallo original de la rama de trabajo) | sí |
| Declarar el INAI `VIGENTE` | sí |
| Añadir «España» a las jurisdicciones de la OIT | sí |
| Declarar `SOURCE_CONTENT_VERIFIED` en la AEPD | sí |
| Dar `aepd.es` a la entrada de la SIC (secuestro de dominio) | sí |
| Declarar «AEPD» como alias de la SIC (suplantación por alias) | sí |
| Romper la simetría de la sucesión INAI → SABG | sí |
| Meter una URL completa en `hostnames` | sí |

La sexta encontró un hueco real: la primera versión de la prueba comparaba los alias solo contra los
nombres canónicos, y «AEPD» no es el canónico de nadie. Se corrigió a comparación alias↔alias en
ambas direcciones.

Además: `boe.es.ejemplo.com`, `aepd.es.phishing.net` y `noaepd.es` **no resuelven a ninguna entrada**
—el emparejamiento es por límite real de subdominio, nunca por subcadena— y el subdominio propio de
la SABG resuelve a su entrada y no a `gob-mx-generico`, porque gana el hostname más específico.

## Verificación ejecutada

| Comprobación | Resultado |
|---|---|
| `origin/main` = `ef7ffdd…` (base esperada) | coincide — sin `STOP_BASE_DRIFT` |
| Suite de la skill (`unittest`, 5 módulos) | **270 OK** (245 previas + 25 nuevas) |
| Fixtures positivos + 3 paquetes del piloto | validan, exit 0 |
| Fixtures negativos | rechazados, exit ≠ 0 |
| Mutaciones adversariales | 8/8 detectadas; registro restaurado, árbol limpio |
| Entradas | 26 → 31, ninguna eliminada, ninguna modificada |
| `validate-claim-packet.py` | **sin cambios** |

## Qué NO hace este PR

No porta claim packets, copy, `visual_prompt.json`, `handshake_web.json`, receipts ni componentes.
No abre ningún gate. No registra ninguna aprobación humana. No modifica el canon del piloto. No
reescribe historia ni hace force-push. No toca Drive.

## Decisiones que siguen requiriendo al fundador

1. **Registrar `curia.europa.eu`** (TJUE). Sin él, ninguna afirmación apoyada en jurisprudencia del
   Tribunal alcanza Nivel 1 aunque se lea el texto. No se añade aquí: excede el alcance declarado de
   esta convergencia.
2. **Fechas exactas del INAI** contra el DOF: extinción y traspaso de competencias.
3. **Alcance real de las competencias heredadas** por la Secretaría Anticorrupción y Buen Gobierno.
4. **Aprobar o rechazar este PR.** Se entrega como `MERGE_CANDIDATE`.

## Siguiente acción única

Aprobar la convergencia y fusionarla **antes** de cualquier otro PR que toque el registro. Mientras
`main` y la rama de trabajo declaren dos registros de 26 entradas distintas, cualquier fusión en el
orden equivocado borra evidencia sin producir un solo error.
