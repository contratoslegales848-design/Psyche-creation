# Auditoría — Inteligencia temática + prueba real de producción (16-sep-2026, Parte I)

Mandato: "LEGALMENTE — SÚPER PROMPT — FASE POST-IMPLEMENTACIÓN: PRUEBA REAL
DE PRODUCCIÓN + INTELIGENCIA TEMÁTICA" (Founder). Parte I exige auditar
antes de implementar, no duplicar lo que ya existe. Este documento es esa
auditoría — con evidencia de código, no impresión.

## Resumen del hallazgo central

El sistema editorial de este repositorio es **mucho más sofisticado de lo
que el mandato parece asumir**: ya existe un motor de candidatos temáticos
combinatorio, una huella semántica de 22 campos calibrada contra el corpus
real, memoria con estados y aprendizaje, saturación editorial separada de
repetición semántica, un explorador de territorio (novedad/cobertura/
oportunidad), un generador multi-factor con hard gates, y un radar de
señales externas (vacantes) — todo construido, probado y documentado en
sesiones anteriores. **El hallazgo crítico no es que falte inteligencia
temática: es que esa inteligencia temática está desconectada del motor de
dirección artística que se corrigió en el mandato inmediatamente
anterior.**

## 1. Qué ya existe (no se duplica)

### 1.1 Motor de candidatos combinatorio (`universe.py`)

`TopicCandidate` ya es, casi campo por campo, lo que la Parte IV del nuevo
mandato pide como "modelo de señal" — pero a nivel EDITORIAL, no de señal
externa:

```
candidate_id, materia, submateria, familia_editorial, necesidad,
rol_lector, angulo, contexto_funcional, profundidad, formato,
concepto_nucleo, relacion, pregunta_resuelta, consecuencia, hook,
perfil_emocional, estado_verificacion, proxima_accion
```

`build_reserve()` genera una reserva amplia (mínimo 4x el lote) con
`random.Random(seed)` — reproducible, no random puro sin control.
`select_batch()` selecciona con cuotas duras (materia, familia editorial,
emoción) y distancia semántica mínima contra lo ya elegido — nunca rellena
con candidatos débiles.

### 1.2 Huella semántica de 22 campos (`semantic_fingerprint.py`)

Esto ES el motor de comparación semántica que la Parte VII del mandato
pide explícitamente ("¿Puede valer un WhatsApp como prueba?" ==
"Valor probatorio de conversaciones de mensajería"). `SemanticFingerprint`
separa NÚCLEO (11 ejes semánticos, pesos declarados), EXPRESIVOS (hook,
formato, emoción — no compran novedad) y VISUALES (8 ejes, distancia
propia). Comparación por solapamiento de tokens en vocabulario abierto
(`concepto_nucleo`, `pregunta_resuelta`, etc.) — exactamente el caso del
ejemplo del mandato. **`UMBRAL_EQUIVALENCIA = 0.25` está calibrado contra
el corpus histórico real (174 piezas)**, con precisión/recall
documentados, no elegido a ojo.

### 1.3 Memoria con estados y clasificación (`semantic_memory.py`)

`SemanticMemory.evaluar()` ya devuelve un `Veredicto` con
`bloquea`/`motivo`/`distancia`/`contra`/`estado_contra`, comparando contra
HISTORICA (corpus completo, ventana de 100000 — nunca se "redescubre" lo
ya contado), GENERADA, PRESELECCIONADA, APROBADA, PUBLICADA y DESCARTADA
(cada una con su propia ventana de cooldown). Esto es prácticamente la
clasificación NUEVO/VARIANTE/REPETIDO/SATURADO que pide la Parte VII —
falta solo la etiqueta explícita, no el motor.

### 1.4 Saturación editorial, separada de repetición semántica (`editorial_saturation.py`)

Ya distingue exactamente lo que la Parte VI del mandato pide separar: "¿ya
dijimos esto?" (repetición semántica, `semantic_memory`) vs. "¿estamos
contando todo con la misma función editorial?" (saturación, este módulo —
familia_editorial + necesidad, ventana de 30 piezas recientes, nunca el
corpus histórico completo). Nivel ALTO bloquea como hard gate.

### 1.5 Territory Explorer (`territory_explorer.py`)

`novelty` (qué tan vacía está la celda materia×familia), `coverage`
(fracción del mapa completo ya tocada) y `opportunity` (novelty ponderada
por coherencia declarada — un hueco sin afinidad no es oportunidad). Cubre
gran parte de la Parte VI ("territorio", "utilidad").

### 1.6 Generador multi-factor con hard gates (`generator.py`)

Ya calcula **seis factores con evidencia real** (semantic_novelty,
editorial_diversity, territory_coverage, utility, emotional_fit,
recent_cooldown) y declara **tres como PENDIENTE sin fabricarlos**
(legal_support, human_interest, visual_distance) — la misma honestidad que
el nuevo mandato exige en la Parte XI ("una señal no es autoridad
jurídica"). Tres hard gates reales: cuota de materia del lote, repetición
semántica, saturación editorial ALTA. Incluye ya un ajuste PEQUEÑO Y
ACOTADO por afinidad del Founder (`ajuste_afinidad_founder`,
`AJUSTE_AFINIDAD_MAX = 0.12`) — el patrón exacto que la Parte VI pide para
cualquier ponderación nueva.

### 1.7 Radar de señales externas (`vacancy_radar.py`, sesión del 15-sep)

Ya existe una primera versión real de "señal de vida jurídica" — vacantes
de Indeed clasificadas contra vocabulario controlado
(`PALABRAS_CLAVE_POR_MATERIA`), cruzadas contra cobertura real del corpus,
con propuesta de temas nuevos y candidatos a depurar (nunca a borrar), y
un log append-only para que la depuración se decida sobre evidencia
acumulada. **Limitación real, confirmada por diseño explícito del propio
módulo**: clasifica a nivel de MATERIA (26 posibles), no de concepto
jurídico específico — el propio mandato lo señala: "una vacante de
corporativo" no debe producir "hablemos de derecho corporativo", debe
producir "reducción de capital y protección de acreedores". Esa
granularidad NO existe todavía. Es el hueco real de la Parte V.

### 1.8 Ciclo completo ya diagramado (`organism.py`)

El propio código ya declara el ciclo que el mandato pide en la Parte II:

```
SEÑAL/NECESIDAD → CANDIDATO → HUELLA SEMÁNTICA → RESERVA/DIVERSIDAD
→ PERFIL EMOCIONAL → QA DE LOTE → CURATION_READY
→ SELECCIÓN/DESCARTE DEL FOUNDER → MEMORIA → APRENDIZAJE → NUEVA GENERACIÓN
```

Pero "SEÑAL" aquí es un concepto abstracto (necesidad editorial), NUNCA
poblado por una señal EXTERNA real (vacante, publicación institucional,
criterio judicial) — `universe.build_reserve()` genera candidatos
combinatoriamente, con semilla, no desde el radar de vacantes. Ese cable
no existe todavía.

### 1.9 Taxonomía y mezcla editorial

`editorial-universe-v1.json`: 58 familias editoriales, 15 necesidades, 3
niveles de profundidad (`base`/`media`/`alta`), 4 roles de lector. No es
la lista de 20+ categorías que enumera la Parte VIII del mandato, pero
cubre el mismo propósito — y el propio mandato autoriza explícitamente no
limitarse a su lista si ya existe una taxonomía más completa que sirva.
`universe.select_batch()` ya impone cuotas duras de materia y familia por
lote (8-10 materias/familias distintas por lote de 10, máx. 2 por
emoción) — cubre gran parte de la Parte IX (mezcla editorial), aunque no
en los términos exactos de "3-4 accesibles / 3-4 intermedios / 2-3
especializados" (se verifica en la Parte IX de este mandato, sección
correspondiente del trabajo).

### 1.10 Citas y máximas

`editorial.py`/`corpus_import.py` ya declaran una familia editorial
`maxima_aforismo` (prefijo de slug `cita`, necesidad `recordar`) — la vía
específica que la Parte X pide ya existe como una familia más del universo
editorial, no como un sistema aparte. La verificación de la cita antes de
publicar sigue siendo responsabilidad de `legalmente-legal-verification`
(CLAUDE.md §4) — no se duplica aquí.

## 2. Qué falta realmente (esto sí es trabajo nuevo)

1. **Modelo de señal externa reusable** (Parte IV): `vacancy_radar.py`
   tiene `VacancyPosting`/`ClasificacionVacante`, pero no un modelo de
   Señal genérico que otras fuentes (publicaciones institucionales,
   criterios judiciales, reformas...) puedan compartir sin reinventar
   campos. Los campos concretos que pide el mandato
   (`source_type`, `date_detected`, `frequency`, `recency`,
   `risk_dimension`, `professional_demand`, `public_relevance`,
   `editorial_potential`, `verification_status`...) no existen hoy en
   ninguna estructura.
2. **Extracción granular** (Parte V): el radar clasifica a nivel de
   materia (26 valores), no a nivel de concepto jurídico específico. No
   existe ningún mapeo vacante→concepto fino.
3. **Señal de mercado en el scoring** (Parte VI): `generator.py` no
   conoce el radar de vacantes en absoluto. `professional_demand`
   (demanda profesional real) no es uno de los seis factores con
   evidencia — sería un séptimo factor genuinamente nuevo, con datos
   reales disponibles (frecuencia/recencia de vacantes), no fabricado.
4. **Etiqueta explícita de clasificación anti-repetición** (Parte VII):
   el motor existe (`semantic_memory.evaluar`); la etiqueta
   NUEVO/VARIANTE/REPETIDO/SATURADO que el mandato pide como vocabulario
   de reporte no está expuesta como tal.
5. **LA DESCONEXIÓN CRÍTICA con el motor visual** (Parte XII):
   `art_direction.py::elegir_familia_visual()` sigue leyendo
   `families.py` (el registro de 8 familias reducidas, el mismo que el
   mandato anterior diagnosticó como Hallazgo 3 de monotonía visual).
   `demo_founder_loop.py` lo confirma en su propia salida: *"DIRECCIÓN
   ARTÍSTICA: PENDIENTE — biblioteca abierta (families.py); se asigna en
   brief.py."* — ni un solo módulo del motor editorial importa
   `visual_fingerprint.py`. El catálogo maestro de 767 módulos que se
   integró Fase 2-5 del mandato anterior nunca se conectó al lado
   editorial/temático. Es el hallazgo más importante de esta auditoría:
   la Parte XII del nuevo mandato no es una mejora incremental, es cerrar
   una desconexión real entre dos mandatos.
6. **Prueba real de producción con candidatos reales** (Parte XIII): la
   prueba de aceptación de la sesión anterior (10 temas) usó temas
   redactados a mano, no candidatos del motor editorial. Esta vez el
   mandato pide que salgan del motor real (señales + banco), no de una
   lista escrita para la ocasión.

## 3. Generación de imagen — determinación de capacidad real (Parte XV, adelantada)

`visual/providers/` contiene únicamente:

- `fake.py` — `FakeImageProvider`, para tests, nunca produce una imagen real.
- `http_provider.py` — perfil de ejemplo de un proveedor HTTP genérico
  (`generic-http-image-v1`), sin credenciales ni endpoint real configurado.

**No hay ningún adapter para OpenAI, Grok, Gemini, Flux, Stable Diffusion,
Ideogram ni ningún otro proveedor real.** CLAUDE.md §7 confirma el mismo
estado: Higgsfield "presente pero sin validar en producción" — y, más
importante, **este mismo documento (CLAUDE.md, checked into el repo)
prohíbe a Higgsfield como proveedor de imagen para LegalMente de forma
permanente**, con independencia de que esta sesión tenga herramientas MCP
de Higgsfield técnicamente accesibles. No se usan.

**Conclusión, sin ambigüedad**: no existe en este momento ningún camino
autorizado y funcional para generar una imagen real de LegalMente desde
este repositorio. La prueba de producción de la Parte XIII entregará
paquetes completos (huella + prompt compilado), nunca imágenes — tal como
exige la propia Parte XV del mandato ("NO simules imágenes").

## 4. Plan de trabajo (Partes II en adelante)

1. Modelo de `Signal` genérico en `vacancy_radar.py` (adapta, no duplica).
2. Extracción granular vacante→concepto jurídico específico.
3. Séptimo factor de scoring (señal de mercado), acotado, en `generator.py`.
4. Wrapper de clasificación NUEVO/VARIANTE/REPETIDO/SATURADO sobre
   `semantic_memory`.
5. Taxonomía derivada (Parte VIII) desde materia+profundidad+familia.
6. Verificar mezcla editorial (Parte IX), citas (Parte X), jurisdicción
   (Parte XI) — documentar cobertura existente.
7. **Cerrar la desconexión de la Parte XII**: conectar
   `art_direction.py` (o un módulo nuevo equivalente) a
   `visual_fingerprint.seleccionar_huella()`.
8. Prueba real de producción de 10 temas nuevos (Parte XIII), con QA de
   lote (Parte XIV) y reporte honesto de capacidad de imagen (Parte XV,
   ya determinado arriba) y criterios de rechazo (Parte XVI).
9. Tests + suite completa en verde antes de cada commit.
10. Reporte final de 23 puntos (Parte XVIII).

Ningún merge, ningún deploy — consistente con la Parte XVII del mandato y
con CLAUDE.md.
