# Cierre — "Fase post-implementación: prueba real de producción + inteligencia temática" (16-sep-2026)

Mandato del Founder, continuación directa del "Súper Prompt" de dirección
artística (mismo día). Reporte de cierre en los 23 puntos exactos que pide
la Parte XVIII.

## 1. Estado encontrado

El mandato asumía que faltaba construir inteligencia temática desde cero.
La auditoría obligatoria (Parte I) encontró lo contrario: ya existía un
motor editorial combinatorio real y sofisticado —`TopicCandidate`
(`universe.py`), huella semántica de 22 campos calibrada contra 174 piezas
históricas reales (`semantic_fingerprint.py`, precisión/recall
documentados), memoria con estados y aprendizaje (`semantic_memory.py`),
saturación editorial separada de repetición semántica
(`editorial_saturation.py`), Territory Explorer
(`territory_explorer.py`), generador multi-factor con 3 hard gates
(`generator.py`), y un radar de señales de vacantes reales
(`vacancy_radar.py`, 15-sep-2026). El hallazgo crítico real: ese motor
editorial nunca se conectó al catálogo maestro de 767 módulos que el
mandato ANTERIOR (mismo día) había construido — `art_direction.py` seguía
leyendo `families.py` (8 familias reducidas).

## 2. Qué ya existía

Detalle completo en `docs/auditoria-inteligencia-tematica-2026-09-16.md`
§1. Resumen: motor combinatorio, huella semántica, memoria con
aprendizaje, saturación, territorio, scoring multi-factor con hard gates,
radar de vacantes a nivel de materia, taxonomía editorial de 58 familias +
26 materias + 3 niveles de profundidad, familia editorial dedicada a
citas/máximas (`maxima_aforismo`) con el riesgo de atribución codificado
en su propia definición.

## 3. Qué faltaba realmente

1. Modelo de señal externa reusable con los campos que pide el mandato.
2. Extracción granular vacante→concepto jurídico específico (el radar
   existente sólo llegaba a nivel de materia).
3. Señal de mercado real dentro del scoring del generador.
4. Etiqueta explícita NUEVO/VARIANTE/REPETIDO/SATURADO sobre el motor de
   repetición ya calibrado.
5. **La desconexión crítica**: `art_direction.py` sin conectar al
   catálogo maestro de 767 módulos.
6. Una prueba de producción con candidatos REALES del motor, no una lista
   redactada para la ocasión.

## 4. Qué se implementó

- `visual/market_signal.py` (Partes III-VI): modelo `Signal` genérico,
  extracción granular con vocabulario controlado (5 conceptos literales
  del mandato ya cubiertos: reducción de capital, formalización de
  asambleas, límites de poder, libros corporativos, beneficiario
  controlador), `professional_demand` real sobre conteo observado.
- `visual/generator.py`: `ajuste_senal_mercado()`, mismo patrón acotado
  que `ajuste_afinidad_founder` (máx. 0.08, cero sin evidencia).
- `visual/topic_classification.py` (Partes VII-IX): `clasificar_repeticion()`
  (NUEVO/VARIANTE JUSTIFICADA/REPETIDO/SATURADO), `clasificar_taxonomia()`
  (23 etiquetas del mandato derivadas de materia+profundidad+familia),
  `reportar_mezcla_editorial()` (informativo, nunca cuota dura).
- `visual/art_direction.py` (**Parte XII, crítico**): `draft_visual_brief()`
  ahora usa `visual_fingerprint.seleccionar_huella()` sobre el catálogo
  maestro real; `verificar_diversidad_de_estilos()` acepta el catálogo
  maestro como techo real (antes 8, ahora 504). `production_run.py` y
  `demo_reconciliation.py` actualizados y **verificados corriendo de
  verdad**: "10/10 estilos distintos (catálogo maestro: 504 direcciones)",
  antes "8/8 (8 familias)".
- `visual/demo_produccion_real_10_temas_nuevos.py` (Parte XIII): 10 temas
  reales del motor combinatorio + señal de mercado, con dirección visual
  autorada sobre cada uno, compilados a prompt final con el catálogo
  maestro.
- Documentación: `docs/verificacion-mezcla-citas-jurisdiccion-2026-09-16.md`
  (Partes IX-XI), `docs/qa-lote-capacidad-imagen-criterios-2026-09-16.md`
  (Partes XIV-XVI).

## 5. Fuentes de señales soportadas

Implementada y probada con datos reales: **vacantes de empleo** (Indeed,
vía `vacancy_radar.py` + `market_signal.py`). El modelo `Signal` es
fuente-agnóstico por diseño (`source_type` como campo, no como código
duro) — las demás fuentes que enumera la Parte III (publicaciones
institucionales, criterios judiciales, reformas, consultas recurrentes...)
no tienen conector implementado todavía; el modelo está preparado para
recibirlas sin rediseño, pero construir cada conector real es trabajo
futuro explícitamente fuera de esta fase.

## 6. Modelo de clasificación

`Signal` (fuente→concepto, `market_signal.py`) y `TopicCandidate`
(concepto→pieza editorial, `universe.py`, ya existente) — dos modelos
distintos y conectados, no uno inventado desde cero. Extracción granular
por vocabulario controlado (`CONCEPTOS_GRANULARES_POR_MATERIA`),
fail-closed: sin coincidencia literal, no hay concepto, nunca se inventa.

## 7. Anti-repetición temática

`topic_classification.clasificar_repeticion()` sobre `semantic_memory.py`
(ya calibrado, UMBRAL_EQUIVALENCIA=0.25, precisión/recall documentados
contra el corpus real) + `editorial_saturation.py`. Probado con el
ejemplo literal del mandato: "¿Puede valer un WhatsApp como prueba?" ==
"Valor probatorio de conversaciones de mensajería" → **REPETIDO**.

## 8. Scoring / priorización

`generator.py` ya calculaba 6 factores reales con hard gates; se añadió
un séptimo — señal de mercado real, acotado a ±0.08, patrón idéntico al
ya existente `ajuste_afinidad_founder`. Nunca se fabricó una fórmula
nueva ni se afirmó "viral"/"tendencia" (prohibido explícitamente por la
Parte VI) — `professional_demand` es un bucket determinista sobre conteo
observado.

## 9. Integración con motor visual

Cerrada la desconexión: `art_direction.py` → `visual_fingerprint.py` →
`compiler.py`, con las 10 dimensiones del catálogo maestro llegando al
prompt final. Verificado end-to-end en `production_run.py` y
`demo_reconciliation.py` (corridas reales, no solo unitarios) y en la
prueba de producción de la Parte XIII.

## 10. Tests ejecutados

`visual/test_market_signal.py` (18), `visual/test_generator.py`
(+8 nuevos), `visual/test_topic_classification.py` (17),
`visual/test_art_direction.py` (actualizado + 5 nuevos),
`visual/test_produccion_real_10_temas_nuevos.py` (9). Suite completa
corrida en verde después de cada commit — nunca se avanzó sobre una suite
roja.

## 11. Resultados

**983 → 996 tests, 0 fallos**, en verde de principio a fin. Evidencia real
no simulada: 4/10 candidatos de la prueba de producción con señal de
mercado real activa; QA de huella ACEPTADO en 1 intento; las 10 piezas
clasificadas NUEVO contra 174 piezas históricas reales; "10/10 estilos
distintos" verificado por ejecución real, no sólo por test unitario.

## 12. 10 temas de aceptación (de esta fase)

Ver tabla completa en `docs/prueba-real-produccion-10-temas-2026-09-16.md`.
Resumen: CAND-0008 (mercantil/representación orgánica), CAND-0034
(mercantil/sociedades), CAND-0107 (civil/donación), CAND-0044
(historia_del_derecho/juristas), CAND-0087 (seguridad_social/pensión),
CAND-0127 (transito/atestado), CAND-0128 (ambiental/daño ambiental),
CAND-0025 (salud_medico_legal/responsabilidad sanitaria), CAND-0076
(ambiental/licencia ambiental), CAND-0003 (civil/obligaciones).

## 13. 10 huellas visuales

Ver §10 de cada pieza en el documento de la Parte XIII. Resumen de medios:
escultura/objeto (x2), grabado/estampa, pintura, arquitectura/escenografía,
editorial/gráfico (x2), archivo/manuscrito, CGI, fotografía — 8 medios
distintos sobre 10 piezas.

## 14. 10 prompts

Los 10 prompts compilados completos están en
`docs/prueba-real-produccion-10-temas-2026-09-16.md` §11 de cada pieza.

## 15. Imágenes reales generadas

**Ninguna.** No existe proveedor de imagen real y autorizado conectado a
este repositorio (`docs/auditoria-inteligencia-tematica-2026-09-16.md` §3,
confirmado sin cambios en
`docs/qa-lote-capacidad-imagen-criterios-2026-09-16.md` Parte XV).
Higgsfield, técnicamente accesible vía MCP en esta sesión, está prohibido
permanentemente para LegalMente por CLAUDE.md — no se usó bajo ninguna
circunstancia.

## 16. Fallos visuales encontrados

Ninguno a nivel de imagen (no hay imagen). A nivel de PLAN: la primera
corrida naïve del lote de la Parte XIII (sin `generar_lote_visual`)
habría sobreexplotado un medio — evitado usando el generador de lote con
regeneración (mismo mecanismo de la Fase 6-7 del mandato anterior).

## 17. Regeneraciones

1 — `generar_lote_visual` convergió en el primer intento sobre este lote
específico (a diferencia de la prueba de aceptación anterior, que necesitó
3 intentos); el mecanismo de regeneración se ejercitó y probó en la Fase
6-7 del mandato anterior con casos que sí requirieron reintentos.

## 18. Archivos modificados

**Nuevos:** `docs/auditoria-inteligencia-tematica-2026-09-16.md`,
`corpus/vacantes-16-sep-2026.json`, `visual/market_signal.py` +
`test_market_signal.py`, `visual/topic_classification.py` +
`test_topic_classification.py`,
`docs/verificacion-mezcla-citas-jurisdiccion-2026-09-16.md`,
`visual/demo_produccion_real_10_temas_nuevos.py` +
`test_produccion_real_10_temas_nuevos.py`,
`docs/prueba-real-produccion-10-temas-2026-09-16.md`,
`docs/qa-lote-capacidad-imagen-criterios-2026-09-16.md`, este documento.

**Modificados:** `visual/generator.py` + `test_generator.py`,
`visual/art_direction.py` + `test_art_direction.py`,
`visual/production_run.py`, `visual/demo_reconciliation.py`.

## 19. Commits

`a54bc01` (Parte I, auditoría), `ffc1ef7` (Partes III-IX-XI, señal +
clasificación), `baf0731` (Parte XII, conexión crítica), `790e415`
(Partes XIII-XVI, producción real + QA), y este cierre — todos en
`claude/legalmente-architecture-reconciliation-xojn4i` (Psyche-creation).

## 20. PRs

Ninguno nuevo — esta fase continúa el PR ya abierto
[#35](https://github.com/contratoslegales848-design/Psyche-creation/pull/35)
sobre la misma rama, consistente con ser la continuación directa del
mismo mandato el mismo día.

## 21. Bloqueos

- Generación de imagen real: sin proveedor autorizado conectado (Parte
  15). No es un bloqueo de esta fase — es el estado real del repositorio,
  documentado, no trabajado alrededor.
- Fuentes de señales más allá de vacantes (publicaciones institucionales,
  criterios judiciales, reformas): el modelo las soporta, los conectores
  reales no están construidos — fuera de alcance de esta fase.
- Metáfora↔tema y "técnicamente correcto pero genérico": declarados como
  juicio humano sin automatización posible razonable (Parte XVI).

## 22. Qué requiere aprobación del Founder

1. Revisión del PR #35 (ahora con esta fase incluida).
2. Autorizar (o no) que una sesión futura construya conectores reales
   para otras fuentes de señal (publicaciones institucionales, criterios
   judiciales...).
3. Autorizar (o no) un proveedor de imagen real, cuando exista uno
   aprobado — sin eso, esta fase no puede avanzar más allá de PLANES.
4. Decidir si la clasificación de taxonomía (`topic_classification.py`)
   se usa como criterio editorial vigente o queda como herramienta de
   apoyo.

## 23. Siguiente paso ejecutable

Con aprobación del Founder: (a) fusionar el PR #35 de Psyche-creation
(incluye ahora ambos mandatos del 16-sep); (b) si se autoriza, construir
un segundo conector de señal real (el más cercano a listo: publicaciones
institucionales, mismo patrón que `market_signal.py`); (c) cuando exista
un proveedor de imagen real y autorizado, conectar
`pipeline.generate_visual()` (ya implementado) sobre los paquetes que
esta fase ya produjo, sin rediseñar nada del pipeline.
