# Radar de temas desde vacantes — proceso continuo

Mandato del Founder (15-sep-2026), verbatim: "se deben ir actualizando los
temas jurídicos adicionalmente con lo que piden las vacantes jurídicas para
tener mayor temas de interés para abogados y personas en general quiero que
siempre se alimente y se vaya depurando lo menos importante."

## Qué es

`visual/vacancy_radar.py` — módulo real, probado (24 pruebas,
`visual/test_vacancy_radar.py`), que:

1. **Se alimenta**: clasifica vacantes jurídicas reales (título, y
   descripción cuando esté disponible) contra el vocabulario ya controlado
   de `visual/policy/materias-seed-v1.json`, y cruza la señal contra la
   cobertura real del corpus histórico (174 piezas, `corpus_import.py`) para
   proponer **temas nuevos** donde hay demanda real y poca o ninguna pieza
   producida todavía.
2. **Se va depurando**: propone **candidatos a retirar de la capa activa**
   — nunca a borrar — materias sin ninguna pieza real y sin ninguna señal
   de vacante en **al menos dos corridas consecutivas** (una sola corrida
   sin señal no prueba que un tema no importe). Las materias protegidas
   (`vr.MATERIAS_PROTEGIDAS` — Capa A transversal y disciplinas
   fundacionales, ver `docs/direccion-basico-antes-que-complejo.md`) nunca
   se proponen, por diseño, sin importar la señal.

Todo lo que produce es **propuesta para revisión humana** — nunca modifica
`materias-seed-v1.json`, el corpus, ni ningún banco de contenido. Un tema
con demanda real de vacantes sigue sin ser una afirmación jurídica: pasa
por `legalmente-legal-verification` igual que cualquier otro antes de
convertirse en pieza (CLAUDE.md §4).

## Precedentes (nunca implementados hasta hoy)

- Drive, "LegalMente — Temas legales de demanda real en México (vacantes,
  2026-09)" (6-sep): una corrida manual única, sin mecanismo repetible.
- Drive, "Aportación V2" §9 "Radar vivo de temas" (31-ago): propuesta de
  arquitectura, estado `AUXILIAR / NO_CANÓNICO / NOT_IMPLEMENTED` — nunca
  aprobada ni construida. Este módulo implementa la parte de "radar de
  temas" de esa propuesta (no el "Grafo de Restricciones Jurídicas"
  completo, que sigue sin aprobar y fuera de alcance aquí).

## Cómo correrlo de nuevo (la parte de "siempre")

`visual/demo_vacancy_radar.py` documenta la primera corrida real
(15-sep-2026, 28 vacantes reales de Indeed México, ver
`docs/radar-vacantes-2026-09-15.md`). Para la siguiente corrida:

1. Buscar vacantes reales (conector Indeed disponible en esta sesión;
   `mcp__Indeed__search_jobs`) — títulos de interés: "abogado", más las
   materias en foco del momento (ver `docs/direccion-basico-antes-que-complejo.md`
   §3) y cualquier especialidad que ya haya aparecido como señal creciente
   (compliance/PLD, REPSE/outsourcing en esta primera corrida).
2. Construir la lista de `VacancyPosting` (título, empresa, url — reales,
   nunca inventados) y llamar `vacancy_radar.ejecutar_radar(postings,
   fuente=..., historial_previo=vacancy_radar.cargar_historial())`.
3. `vacancy_radar.registrar_corrida(result)` — append-only, nunca sobrescribe
   corridas anteriores (`corpus/radar-vacantes-log.json`).
4. Revisar `candidatos_nuevos` y `candidatos_a_depurar` con criterio humano
   (docs/direccion-basico-antes-que-complejo.md §6: "proponer → registrar →
   evaluar → ejecutar o retirar") antes de tocar `materias-seed-v1.json` o
   producir contenido nuevo.

No hay una cadencia fija impuesta por el código — es una decisión operativa
del Founder (semanal, mensual, por lote). El mecanismo está listo para
cualquier cadencia que se decida.

## Primer resultado real (15-sep-2026)

28 vacantes analizadas (21 clasificadas). Señal más fuerte:
`corporativo_compliance` (7 — PLD/AML, cumplimiento normativo, incluidas
vacantes de empresas grandes como TikTok y Airwallex en México) y
`mercantil` (5 — corporativo, societario, REPSE/outsourcing). Ningún
`candidato_nuevo` ni `candidato_a_depurar` en esta primera corrida — es el
resultado honesto de un solo punto de datos: `corporativo_compliance` ya
tiene 5 piezas reales en el corpus (temas DUE-DILIGENCE), y ninguna materia
sin cobertura acumuló las dos corridas sin señal que exige la regla de
depuración. El valor del radar está en la **acumulación**, no en esta
primera fotografía — ver informe completo en
`docs/radar-vacantes-2026-09-15.md`.

7 vacantes quedaron `SIN_MATERIA_RECONOCIDA` (p. ej. "Legal Escalations
Specialist", "Legal Assistant (LATAM Remote)") — roles legal-adjacentes en
inglés/remoto que el vocabulario actual no cubre; quedan como señal de que
el vocabulario de `PALABRAS_CLAVE_POR_MATERIA` es abierto y debe ampliarse
con evidencia real, no como error del módulo.
