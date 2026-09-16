# Cierre — "Súper Prompt" motor de dirección artística (16-sep-2026)

Mandato: "LEGALMENTE — SÚPER PROMPT PARA CLAUDE CODE — CORRECCIÓN GLOBAL Y
DEFINITIVA DEL MOTOR DE DIRECCIÓN ARTÍSTICA" (Founder), con
`LEGALMENTE_CATALOGO_MAESTRO_DIRECCION_ARTISTICA_CHATGPT.md` (767 módulos
visuales) como vocabulario canónico. Autorización expresa citada
textualmente: *"Tienes autorización para auditar y modificar el sistema
existente de LegalMente con este objetivo. No hagas merge ni deploy a
producción sin autorización final del founder."*

15 fases pedidas. Las 14 primeras están implementadas, probadas y
documentadas; la 15 es este documento. Ninguna fase produjo un merge ni un
deploy — eso sigue pendiente del Founder, como el mandato exige.

## 1. Qué se hizo

**Fase 1 — auditoría** (`docs/auditoria-monotonia-visual-2026-09-16.md`):
5 hallazgos concretos y verificados con evidencia de código/datos, no
impresión: una línea incondicional de "azul petróleo" en `compiler.py`
para el 100% de las piezas; una paleta "requerida" de 4 colores fija en la
política; 8 "familias" visuales que en la práctica heredan todas del mismo
pool de 4 colores; `legalmente-remotion` con un solo "look"
("cinematic legal realism... museum-quality composition") declarado
"Siempre presente" para el 100% del catálogo, máximas latinas incluidas;
`legalmente-web` con un universo de 6 `visualGrammar` (no 5, corregido al
verificar) repartido en 4 canales, uno de ellos código muerto.

**Fases 2-3 — catálogo maestro real:** el documento del Founder se trajo
como fuente canónica humana (`visual/policy/catalogo-maestro-v1.md`) y se
parseó automáticamente (`visual/catalog_parser.py`, nunca a mano) a un
JSON derivado — 504 direcciones (10 categorías) + 263 auxiliares
(7 dimensiones) = 767, coincidencia exacta con lo que el documento declara.

**Fases 4-5 — huella visual + selección semántica:** `visual/visual_fingerprint.py`.
`VisualFingerprint` con las 10 dimensiones del mandato; `medium` se deriva
de la categoría real de `primary_direction` (nunca se elige aparte);
selección por frecuencia de uso reciente (no random puro, sin afinidad
tema→categoría inventada) con mutación cuando la huella coincide en
demasiadas dimensiones con la pieza anterior o el historial.

**Fases 6-7 — memoria y lote de 10:** `visual/visual_fingerprint_batch.py`.
`evaluar_lote_visual()` (mínimo 7 huellas distintas, mínimo 5 medios, tope
2 por medio, cero repetición consecutiva en dimensiones dominantes) y
`generar_lote_visual()` (regenera el lote completo hasta que pasa el QA —
nunca lo rellena). Detectó y corrigió sobre datos reales: un lote generado
solo con anti-repetición por pieza sobreexplotaba un medio 3 veces —
evidencia de que la regla de lote no era redundante.

**Fases 8-9 — eliminar los defaults dominantes, en los 3 repos:**

- *Psyche-creation*: `compiler.py` deja de imprimir la línea incondicional
  de azul petróleo; `brief.py` generaliza `acento_frio_objeto` →
  `acento_objeto`; `policy/legalmente-visual-policy-v1.json` cambia
  `paleta.requerida` (obligación de 4 colores) por `paleta.marca_de_referencia`
  (referencia de marca, ya no obligación de escena) — `paleta.prohibida`
  se conserva intacta, son restricciones reales, no parte del hallazgo.
- *legalmente-remotion*: rama nueva `claude/direccion-artistica-catalogo-maestro-sep2026`,
  [PR #5](https://github.com/contratoslegales848-design/legalmente-remotion/pull/5)
  (draft, sin merge) — §3.1/§3.3/§3.4 cambian el "Style" fijo por
  `[DIRECCIÓN ARTÍSTICA]`, §3.5 actualiza la fila de parámetros. No se
  apiló sobre los PR #3/#4 ya abiertos (mismo archivo, otras secciones) —
  rama nueva desde `main` para evitar conflicto innecesario.
- *legalmente-web* (solo lectura, CLAUDE.md §8): propuesta no aplicada —
  `docs/propuesta-legalmente-web-diversidad-canal-2026-09-16.md` +
  `.patch`, verificados con `git apply --check` contra el clon real
  (SHA `27df096e54e9ca4c5552eb26bbe60319d4ef70d5`) y probados
  temporalmente (el test nuevo falla sin el fix, pasa con él; el clon se
  restauró sin dejar cambios).

**Fase 10 — la huella llega al prompt, no solo al metadata:**
`compile_request(..., fingerprint=huella)` construye la sección de
dirección artística y la paleta del prompt desde las 10 dimensiones de la
huella. `visual/test_compiler.py` (11 tests): `primary_direction`,
`medium`, `lighting`, `composition`, `palette` aparecen literalmente en el
texto; dos huellas distintas producen prompts y `sha256` distintos; la
misma huella es determinista; sin huella el comportamiento anterior se
mantiene.

**Fases 12-13 — QA automatizada + prueba de aceptación:**
`visual/test_prueba_aceptacion_10_temas.py` atrapa, cada una con un caso
real que la dispara: monopolio de estilo, catálogo reducido por
accidente, repetición por dimensión en lote, metadata que no llega al
prompt, fallback dominante, catálogo derivado desconectado de su fuente
`.md`, distancia visual insuficiente. `visual/demo_prueba_aceptacion_10_temas.py`
genera 10 temas jurídicos reales panhispánicos (Capa A transversal, orden
de `docs/direccion-basico-antes-que-complejo.md` §3) → 10 huellas + 10
prompts compilados, **nunca imágenes** — resultado real:
`docs/prueba-aceptacion-10-temas-2026-09-16.md`, lote `ACEPTADO` en 3
intentos, 10/10 huellas distintas, 7 medios distintos, distancia pareja
predominantemente 9-10/10 entre las 45 combinaciones de las 10 piezas.

**Fase 14 — no romper lo existente:** verificado en cada commit, no solo
al final — la suite completa de `visual/` corrió en verde después de cada
fase (909 → 918 → 929 → 941 tests), nunca se avanzó sobre una suite roja.

## 2. Qué se verificó (con evidencia, no solo afirmación)

- Conteo exacto del catálogo parseado contra lo que el documento fuente
  declara (504 + 263 = 767) — `visual/test_catalog_parser.py`.
- Ejecución real (no solo lectura de código) de `visual_fingerprint.py`
  sobre 30-60 piezas antes de escribir los tests formales: determinismo,
  `medium` siempre igual a la categoría real, distancia mínima
  consecutiva cumplida sin necesitar el bucle de mutación.
- El lote generado con solo anti-repetición por pieza (sin regla de lote)
  sobreexplotaba un medio 3 veces — la regla de lote captura un caso
  real, no uno fabricado para que el test pase.
- El patch de `legalmente-web` se aplicó de verdad sobre el clon local
  (SHA verificado), el test nuevo se corrió con `npx tsx --test` (falla
  sin el fix, pasa con él), y el clon se devolvió a su estado original.
- La prueba de aceptación de 10 temas se corrió y su salida real (matriz
  de distancia, veredicto de lote) quedó guardada en
  `docs/prueba-aceptacion-10-temas-2026-09-16.md`, generada por el script,
  no escrita a mano.
- Suite completa de `visual/`: **941 tests, 0 fallos**, corrida después
  de cada fase, no solo al cierre.

## 3. Qué se bloqueó y por qué

- **Merge y deploy**: bloqueados en los 3 repos, por instrucción expresa
  del Founder en el propio mandato. Las 3 ramas (`claude/legalmente-architecture-reconciliation-xojn4i`
  en Psyche-creation; `claude/direccion-artistica-catalogo-maestro-sep2026`,
  PR #5, en legalmente-remotion; la propuesta de legalmente-web sin
  aplicar) quedan como entregas pendientes de revisión.
- **legalmente-web**: bloqueado por permisos, no por decisión — cuenta
  distinta (`legallmente-alt`), solo lectura (CLAUDE.md §8). Se entregó
  como patch-series verificado, nunca se intentó push.
- **Google Drive**: no se tocó. La "Bitácora de cambios (ciclo 2026-09)"
  de Drive (mencionada en `docs/arquitectura-real-2026-09-13.md`) no
  recibió esta entrada — CLAUDE.md §6 exige autorización explícita para
  esa sesión, y esta no la tuvo. El registro local (este documento +ver
  los `docs/*-2026-09-16.md` de cada fase) es el registro real.
- **`legalmente-web`, integración real con el catálogo maestro**: se
  propuso el fix puntual (Hallazgo 5), no una migración completa de su
  enum de 6 `visualGrammar` al catálogo de 767 — eso es una decisión de
  arquitectura cross-repo, no un fix de hallazgo, y el propio documento de
  propuesta lo deja explícito como pendiente de decisión del Founder.

## 4. Qué requiere aprobación humana

1. Aprobar o rechazar el PR en Psyche-creation
   (`claude/legalmente-architecture-reconciliation-xojn4i`).
2. Aprobar, pedir cambios, o rechazar el
   [PR #5 de legalmente-remotion](https://github.com/contratoslegales848-design/legalmente-remotion/pull/5)
   — y decidir el orden de fusión frente a los PR #3/#4 ya abiertos
   (todos tocan `legalmente-marca-y-estilo.md`, en secciones distintas;
   alguno requerirá reconciliar `BITACORA.md` al fusionarse después del
   primero).
3. Decidir si se aplica la propuesta de `legalmente-web` (requiere una
   sesión con permisos de push a `legallmente-alt/legalmente-web`) y
   resolver las dos preguntas abiertas del documento de propuesta
   (integración con el catálogo maestro sí/no; destino de
   `CLASSICAL_REINTERPRETATION`).
4. Registrar (o autorizar que se registre) esta entrada en la Bitácora de
   Drive, ya que esta sesión no tenía autorización para escribir ahí.

## 5. Siguiente paso ejecutable

Con aprobación del Founder: fusionar el PR de Psyche-creation primero (no
depende de los otros dos), luego decidir el orden entre los PR #3/#4/#5 de
legalmente-remotion (los tres tocan el mismo archivo en secciones
distintas — ninguno depende técnicamente de otro, pero fusionarlos en
serie evita reconciliar `BITACORA.md` tres veces en paralelo). La
propuesta de `legalmente-web` queda para una sesión aparte con permisos de
push a esa cuenta, tal como exige CLAUDE.md §8.

## 6. Archivos tocados (por commit, todos en la rama de esta sesión)

- `73e0c17` — Fase 1-5: `docs/auditoria-monotonia-visual-2026-09-16.md`,
  `visual/policy/catalogo-maestro-v1.{md,json}`, `visual/catalog_parser.py`,
  `visual/test_catalog_parser.py`, `visual/visual_fingerprint.py`,
  `visual/test_visual_fingerprint.py`.
- `f1045e9` — Fase 6-7: `visual/visual_fingerprint_batch.py`,
  `visual/test_visual_fingerprint_batch.py`.
- `bc1df15` — Fase 8-9-10: `visual/brief.py`, `visual/cli.py`,
  `visual/compiler.py`, `visual/pipeline.py`,
  `visual/policy/legalmente-visual-policy-v1.json`,
  `visual/test_compiler.py`, y los 3 tests actualizados al campo renombrado
  (`test_emotion.py`, `test_visual_advanced.py`, `test_visual_pipeline.py`).
- `62b56ab` — Fase 8-9 (legalmente-web): `docs/propuesta-legalmente-web-diversidad-canal-2026-09-16.{md,patch}`.
- `af84f72` — Fase 12-13: `visual/demo_prueba_aceptacion_10_temas.py`,
  `visual/test_prueba_aceptacion_10_temas.py`,
  `docs/prueba-aceptacion-10-temas-2026-09-16.md`.
- Este commit (Fase 15): este documento + sección nueva en `visual/README.md`.

En `legalmente-remotion` (rama `claude/direccion-artistica-catalogo-maestro-sep2026`):
`legalmente-marca-y-estilo.md`, `BITACORA.md`.

## 7. Conflicto conocido pendiente de reconciliar

`legalmente-remotion` tiene 3 ramas abiertas sobre el mismo archivo
(`legalmente-marca-y-estilo.md`), cada una en secciones distintas:
PR #3 (texto/formato, §2), PR #4 (banco de escenarios, §3.2), PR #5
(dirección artística, §3.1/§3.3/§3.4/§3.5). Las tres crean o tocan
`BITACORA.md` de forma independiente porque `main` no lo tenía cuando se
abrió la primera. Ninguna se fusionó en esta sesión — la reconciliación
(orden de merge + resolución de `BITACORA.md`) es una decisión humana, no
técnica: las tres correcciones son reales y no se pisan en contenido, solo
coinciden en tocar el mismo archivo.
