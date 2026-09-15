# Corpus histórico — snapshot inmutable

Copia literal del banco de prompts v3 de Drive, congelada para que la migración
sea **reproducible sin red**. Drive sigue siendo la fuente de verdad
(`CLAUDE.md §2`); esto es un espejo de lectura, no una segunda autoridad.

| Archivo | Origen (Drive) | Contenido |
|---|---|---|
| `banco-v3-doc1-sistema-y-catalogo.txt` | `1WOXtbYMQYx2yV2RlvCkV2J0hc6CMkqksuBpitZ67KK4` | Documento 1 v3 (2026-09-08): plantilla, paleta, reglas y las 174 metáforas con su tema y titular. |
| `guiones-doc1.json` | derivado del anterior | 174 guiones parseados: tema, slug, titular, metáfora. |
| `banco-v3-doc2-tabla.txt` | `1MmDn8-1RGk_wpx9BNWHIo7s3wSsg6SMxaj5ouCwc-p0` | Documento 2 v3: tabla LM-001..LM-174 con carril, escuela, escenario, encuadre, paleta, mecanismo, objeto de marca y aspecto. |
| `eval-umbral-candidato.json` | — | Conjunto de evaluación del umbral. **Etiquetado por el agente, NO por el Founder.** Pendiente de revisión humana. |
| `eval-umbral-founder.json` | — | Ground truth real del Founder sobre los 18 pares (2026-09-14). Ver `visual/calibration.py`. |
| `radar-vacantes-log.json` | — | **No es snapshot histórico ni inmutable** — log append-only del radar de temas desde vacantes (`visual/vacancy_radar.py`, 2026-09-15). Cada corrida se agrega, ninguna se reescribe. Ver `docs/radar-de-temas-desde-vacantes.md`. |

## Reglas

- **No se modifica.** `visual/corpus_import.py` sólo lee. Si el banco cambia en
  Drive, se vuelve a exportar el snapshot; no se edita a mano.
- Los dos documentos se **validan cruzadamente** al importar: 174 guiones en cada
  uno, unión por slug sin huérfanos por ninguno de los dos lados.
- El corpus **no es fuente jurídica**. Es el registro de lo que LegalMente ya
  produjo. Ninguna de sus filas afirma qué dice la ley de ningún país.
- Se importa con estado `HISTORICA`: producción pasada, **no** señal de que el
  Founder eligiera esas piezas. No alimenta `preferencias()`.

## Lo que NO contiene

**Actualización 15-sep-2026:** `contratoslegales848-design/legalmente-remotion`
SÍ es accesible desde esta cuenta (corrige la nota anterior de esta sección,
basada en `00 LEER PRIMERO §10`, 7-sep — ver `docs/revision-externa-arte-2026-09-15.md`).
No contiene, sin embargo, `config/catalogo-estilos.json` ni el motor de
18 canales/174 guiones que describen los Índices de Drive — contiene un
canon de marca y estilo distinto (`legalmente-marca-y-estilo.md`) nunca
reconciliado con el banco v3 de este corpus. Ese repositorio con los
guiones completos y métricas de rendimiento sigue sin localizarse. Por eso
el corpus aporta slug, titular, tema y capa visual, pero no el cuerpo del
guion ni métricas de rendimiento. Las 0 entradas con métricas siguen siendo
el cuello de botella del aprendizaje.
