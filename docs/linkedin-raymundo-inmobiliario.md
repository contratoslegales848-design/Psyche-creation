# LinkedIn Raymundo — banco de temas de experiencia profesional real (Inmobiliario)

**Estado:** BANCO DE TEMAS / NO VERIFICADO / NO PUBLICABLE. Este documento no es
una pieza jurídica, no tiene claim packet, no pasó por
`legalmente-legal-verification`, y ningún ítem de aquí puede convertirse en
copy, carrusel, imagen o post sin recorrer esa skill primero (`CLAUDE.md §4`).

**Por qué existe:** el fundador pidió (2026-09-11) completar la parte de
LinkedIn con su experiencia profesional real, ya documentada y anonimizada en
Drive, "para que se alimenten de temas". Este archivo la trae al repositorio
— la única fuente de verdad técnica — en vez de dejarla dispersa entre ~10
documentos y zips de Drive, varios de ellos preparados por agentes distintos
(Manus AI, Grok) y nunca verificados contra este repositorio.

## 1. Fuente

Documentado en Drive, carpeta raíz de LegalMente:
`LegalMente Artefacto 05 — LinkedIn Strategy` (autor declarado: Manus AI,
27-ago-2026, "documento no canónico") con una ampliación fechada 2-sep-2026
("EXPERIENCIA LABORAL APLICADA / DESARROLLOS RESIDENCIALES") y el paquete
`LEGALMENTE_RAYMUNDO_LINKEDIN_HELP_CONTRIBUTION_V1` (3-sep-2026), que ya
clasifica cada candidato como `SAFE_EDITORIAL_FRAME` o `REVIEW_REQUIRED`.

El propio documento fuente ya fija reglas que este archivo hereda sin
reinterpretarlas:

- **Provenance**: cada candidato debe enlazar a experiencia/documentación
  real; sin eso, queda como idea de investigación, nunca atribuida a
  Raymundo como experiencia propia.
- **Profundidad**: la experiencia práctica puede explicar arquitectura,
  dependencias y criterio profesional; **nunca convierte una experiencia en
  regla jurídica universal** — toda afirmación normativa necesita
  jurisdicción, fuente y vigencia, igual que cualquier otra pieza de
  LegalMente.
- **Confidencialidad** (idéntica a `CLAUDE.md §5`, y explícita en el
  documento fuente): nada de nombres de empresas, clientes, escrituras,
  notarías, fechas operativas, montos, cláusulas textuales ni datos
  bancarios. **Este documento cumple esa regla de forma literal**: el
  documento fuente en Drive sí menciona proyectos/desarrollos concretos por
  nombre en su sección de "fuentes de experiencia a vincular" — ese detalle
  se queda en Drive, deliberadamente, y no se reproduce aquí porque este
  repositorio es **público** (`docs/TECHNICAL_STATE.md §6`).

### 1.1 Qué NO es esta fuente (deslinde importante)

Existe en el mismo Drive una hoja de cálculo, **"Seguimiento Laboral Raymundo
2026"**, con su búsqueda de empleo real: empresas, ciudades, salarios
ofrecidos y nombres de archivos de CV. **Esa hoja no es fuente de contenido
para LegalMente bajo ninguna circunstancia** — es información personal y
laboral privada, exactamente el tipo de dato identificable que
`CLAUDE.md §5` prohíbe usar, y no fue tocada al preparar este documento. Si
en el futuro se le pide a un agente "usar la experiencia de Raymundo", debe
distinguir esta hoja (privada, no usar) del banco de conocimiento anonimizado
de esta sección (banco de temas, sujeto a las reglas de arriba).

## 2. Pilar: Derecho Aplicado / Arquitectura Jurídica de Operaciones Inmobiliarias

Encaja exactamente en el vacío de contenido que ya tenía identificado
`docs/direccion-basico-antes-que-complejo.md §3` (inmobiliario, prioridad 3,
sin materia propia todavía en el motor de rutas). Por eso esta sesión añadió
también una entrada `"inmobiliario"` a `VOCABULARIO_POR_MATERIA` en
`visual/route_engine.py` — vocabulario de navegación genérico (no una
afirmación jurídica de ningún país), siguiendo el mismo patrón que
`penal`/`civil`/`laboral`. Eso habilita rutas técnicas para esta materia; no
adelanta ninguna pieza en la cola general de producción, que sigue el orden
de `direccion-basico-antes-que-complejo.md §3` salvo para este canal
específico de LinkedIn, donde el fundador dio instrucción expresa hoy.

**Idea central (marco editorial, no un claim):** un desarrollo inmobiliario
no empieza con el contrato — empieza con el inmueble y con dos preguntas:
¿qué existe jurídicamente sobre esa tierra? y ¿qué puede desarrollarse
realmente sobre ella? La dirección jurídica acompaña el proyecto completo,
sin sustituir a las demás especialidades (urbanismo, ambiente, ingeniería,
fiscal, finanzas).

**Cadena maestra (marco de proceso, genérico, sin país):**

```
INMUEBLE → DUE DILIGENCE → VIABILIDAD URBANA/AMBIENTAL → ADQUISICIÓN/CONTROL
→ ESTRUCTURA CORPORATIVA → MASTER PLAN → FACTIBILIDADES
→ AUTORIZACIÓN DEL DESARROLLO/FRACCIONAMIENTO → PROYECTO EJECUTIVO
→ LICENCIAS DE CONSTRUCCIÓN/URBANIZACIÓN → INDIVIDUALIZACIÓN
→ COMERCIALIZACIÓN/PREVENTA → URBANIZACIÓN/CONSTRUCCIÓN
→ TERMINACIÓN/RECEPCIÓN → ESCRITURACIÓN → ENTREGA → COMUNIDAD/POSTVENTA
```

**Distinciones que el material fuente ya identifica como el núcleo editorial**
(cada una es una distinción de proceso, no una regla nacional — territorio y
fuente se investigan aparte, por país, si un post concreto la necesita):

- Propiedad no equivale a derecho de desarrollar/urbanizar.
- Autorización urbanística no equivale a autorización ambiental, ni viceversa.
- Fraccionar no es urbanizar; urbanizar no es escriturar; vender no significa
  que el lote ya pueda transmitirse.
- El proyecto ejecutivo traduce lo autorizado a planos y obra — no es el
  paso que autoriza.
- Marketing, proyecto autorizado y contrato deben describir la misma
  realidad.
- El rol de dirección legal es integrar especialidades (urbanismo, ambiente,
  ingeniería, fiscal, finanzas), no sustituirlas.

## 3. Banco de candidatos (consolidado, deduplicado)

Cada fila trae el estado que el propio material fuente ya le asignó en
`raymundo_content_readiness.csv` (Drive). **Ninguno de estos dos estados es
una aprobación**: `SAFE_EDITORIAL_FRAME` significa que la idea, tal como está
redactada, es un marco de proceso sin afirmación normativa aislada; no exime
de correr `legalmente-legal-verification` en cuanto el copy real cite una
norma, un plazo o una consecuencia jurídica concreta. `REVIEW_REQUIRED`
significa que el hook, tal como está, ya roza una afirmación territorial y
necesita fuente/jurisdicción antes de redactarse.

| # | Tema | Estado declarado en Drive | Nota | Claim packet (2026-09-12) |
|---|---|---|---|---|
| 1 | Un desarrollo inmobiliario no empieza con el contrato. | SAFE_EDITORIAL_FRAME | Marco de proceso. | `linkedin-ray-01-no-empieza-contrato.json` — REQUIERE_INVESTIGACION |
| 2 | Tener escritura no significa que puedas desarrollar. | REVIEW_REQUIRED | Hook fuerte; necesita jurisdicción/vigencia antes de publicarse. | — |
| 3 | Fraccionar, urbanizar y escriturar no son lo mismo. | REVIEW_REQUIRED | Distinción útil; necesita fuente/territorio. | — |
| 4 | Las dos vidas de un residencial: física y jurídica. | SAFE_EDITORIAL_FRAME | Marco, sin conclusión legal. | `linkedin-ray-04-dos-vidas-residencial.json` — REQUIERE_INVESTIGACION |
| 5 | El abogado de dirección como integrador de áreas, no sustituto del equipo técnico. | SAFE_EDITORIAL_FRAME | Posicionamiento profesional; sin credenciales más allá de la fuente. | `linkedin-ray-05-abogado-integrador.json` — REQUIERE_INVESTIGACION |
| 6 | Marketing, proyecto autorizado y contrato deben describir la misma realidad. | REVIEW_REQUIRED | Principio operativo; evitar garantía universal. | — |
| 7 | Por qué el abogado debe entrar antes de comprar la tierra. | SAFE_EDITORIAL_FRAME | Extiende el tema 1. | — (no estaba en la lista de 8 elegida) |
| 8 | Del predio matriz al lote individualizado. | REVIEW_REQUIRED | Requiere describir el procedimiento sin fijarlo a un solo país. | — |
| 9 | Qué conecta una licencia de fraccionamiento con la urbanización. | REVIEW_REQUIRED | Term. técnico varía por país — Capa B/C, no Capa A. | — |
| 10 | El proyecto ejecutivo como puente entre autorización y obra. | SAFE_EDITORIAL_FRAME | Marco de proceso. | — (no estaba en la lista de 8 elegida) |
| 11 | Pagar un lote no siempre significa que ya pueda escriturarse. | REVIEW_REQUIRED | Afirmación con riesgo de falsa universalización. | — |
| 12 | El contrato es un nodo del proyecto, no el proyecto completo. | SAFE_EDITORIAL_FRAME | Marco. | `linkedin-ray-12-contrato-nodo-proyecto.json` — REQUIERE_INVESTIGACION |
| 13 | Due diligence inmobiliario: verificar antes de diseñar y prometer. | SAFE_EDITORIAL_FRAME | Marco. | `linkedin-ray-13-due-diligence-antes-de-prometer.json` — REQUIERE_INVESTIGACION |
| 14 | La matriz de permisos como mapa de dependencias, no como lista burocrática. | SAFE_EDITORIAL_FRAME | Marco. | `linkedin-ray-14-matriz-permisos-dependencias.json` — REQUIERE_INVESTIGACION |
| 15 | La comunidad jurídica después de vender: reglamentos, cuotas, áreas comunes y administración. | REVIEW_REQUIRED | Depende del régimen de propiedad en condominio de cada país. | — |
| 16 | Un poder debe describir facultades y límites; el cargo por sí solo no prueba representación. | SAFE_EDITORIAL_FRAME | Extiende a Representación (pilar ya existente en Artefacto 05); la segunda mitad resultó una falsa universalización (ver §3.1). | `linkedin-ray-16-poder-facultades-y-limites.json` — 3 claims: mandato/poder (APTO_CON_MATICES), corolario original "el cargo no prueba representación" (BLOQUEADO — falso para el cargo de administrador), reformulación corregida (APTO_CON_MATICES); agregado de la pieza BLOQUEADO |
| 17 | La due diligence crea una línea base: documentar lo observado evita confundir problemas preexistentes con decisiones posteriores. | SAFE_EDITORIAL_FRAME | Marco. | `linkedin-ray-17-due-diligence-linea-base.json` — REQUIERE_INVESTIGACION |
| 18 | Una cláusula de no competencia exige revisar alcance, territorio, duración y compensación. | REVIEW_REQUIRED | Validez de la cláusula varía por país — necesita fuente antes de un hook normativo. | — |

### 3.1 Qué pasó al correr los 8 `SAFE_EDITORIAL_FRAME` por la skill (2026-09-12)

Instrucción del fundador: "Empieza por los 8 SAFE_EDITORIAL_FRAME". Los 8
temas (#1, 4, 5, 12, 13, 14, 16, 17) ahora tienen claim packet real en
`.claude/skills/legalmente-legal-verification/pilot/claim-packets/`, todos
validados con `scripts/validate-claim-packet.py` y
`scripts/check_pilot_governance.py` — 0 errores estructurales, gate
`CERRADO` en los 8 (correcto: ninguno tiene revisión humana todavía).

- **7 de los 8** (todo menos #16) resultaron ser marcos de proceso/metodología
  profesional, no afirmaciones sobre lo que exige la ley de ningún país — al
  extraerlos como claim (Etapa 1-2), ninguno pasó la prueba de "esto es una
  proposición verificable con una fuente" que exige la skill. Quedan
  `alcance: NO_DETERMINADO` / `estado: REQUIERE_INVESTIGACION`, `fuentes: []`
  — no por `EGRESS_BLOCKED`, sino porque no hay una fuente que pudiera
  confirmarlos o refutarlos: son recomendaciones profesionales, no hechos. Lo
  que falta no es investigación jurídica externa: es que el fundador confirme
  que cada formulación describe honestamente su práctica real y no desliza,
  sin decirlo, un requisito legal país-dependiente. Cada packet lo explica en
  su campo `notas`.
- **#16 sí tenía contenido jurídico real** ("un poder debe describir
  facultades y límites") — la Etapa 1 lo separó en dos claims, como exige la
  skill cuando una afirmación mezcla dos cosas:
  - `linkedin-ray-16-claim-1-mandato`: investigado de verdad vía `WebSearch`
    (WebFetch confirmó de nuevo `EGRESS_BLOCKED`, esta vez también contra
    `es.wikipedia.org`, no solo dominios `.gob.mx`) contra 4 fuentes oficiales
    reales — Código Civil Federal de México (`diputados.gob.mx`, arts.
    2554-2555), Código Civil de España (`boe.es`, art. 1709), Código Civil y
    Comercial de Argentina (`servicios.infoleg.gob.ar`, arts. 362-363) y
    Código Civil de Colombia (`secretariasenado.gov.co`, art. 2142). Las
    cuatro convergen en que la representación nace de un acto de
    apoderamiento con alcance propio. Techo: `APTO_CON_MATICES` (Capa A,
    Nivel 2 en los 4 países — ninguna fuente tiene `texto_exacto_consultado`
    en `true` porque `WebFetch` no pudo leer el documento íntegro).
  - `linkedin-ray-16-claim-2-cargo-no-acredita`: el corolario societario ("el
    cargo no prueba representación") sí se investigó en una segunda ronda
    (2026-09-12) contra la ley societaria/mercantil de los mismos 4 países —
    Ley General de Sociedades Mercantiles (México, art. 10), Ley de
    Sociedades de Capital (España, art. 233), Ley General de Sociedades
    19.550 (Argentina, art. 58) y Código de Comercio (Colombia, art. 196).
    **Resultado: la formulación original es una falsa universalización.**
    Las 4 leyes coinciden en que el cargo *formalmente designado* de
    administrador (o representante legal equivalente) **sí** confiere
    representación por sí solo, por ley — sin poder aparte. Lo que
    necesita un poder expreso es *otro* cargo distinto (gerente en México,
    apoderado en España), no "el cargo" en general. Por eso este claim
    queda `alcance: CAPA_A_TRANSVERSAL` / `estado: BLOQUEADO` (la
    investigación concluyó algo firme, no una duda) con una
    `reformulacion_propuesta` verificada que apunta a un nuevo claim
    corregido.
  - `linkedin-ray-16-claim-3-administrador-vs-otros-cargos` (nuevo, añadido
    en esta ronda): la versión corregida y sí sostenida por las 4 fuentes —
    "la representación de una sociedad corresponde por ley a quien ocupa el
    cargo formalmente designado de administrador; cualquier otro cargo
    necesita un poder expreso". Capa A, `APTO_CON_MATICES` (mismo techo
    Nivel 2 que los demás claims de esta pieza, por `EGRESS_BLOCKED`).
  - El agregado de la pieza es `BLOQUEADO` (un claim bloqueado bloquea toda
    la pieza, máxima prioridad en el cálculo) — a pesar de que dos de sus
    tres claims llegaron a `APTO_CON_MATICES`. Esto es correcto y esperado:
    la pieza completa no avanza hasta que se retire o repare el claim
    bloqueado, y ya está reparado vía reformulación (claim 3).

**Ningún packet tiene `revision_humana.estado: APROBADO`** — nace `PENDIENTE`
en los 8, como exige la skill. **Ningún gate está `ABIERTO`.** Nada de esto
puede pasar a `legalmente-visual-system` todavía.

## 4. Siguiente paso ejecutable (para cada candidato, en orden)

1. El fundador elige cuáles de estos 18 avanzan primero (no hay obligación de
   producir los 18, ni de producirlos en este orden — es un banco, no una
   cola).
2. Para cada uno elegido: activar `legalmente-legal-verification` (Etapas
   1-6). Los marcados `REVIEW_REQUIRED` necesitan como mínimo una fuente
   oficial por país que se mencione; los `SAFE_EDITORIAL_FRAME` pueden
   generar un claim packet más simple (`alcance: NO_APLICA` o
   `CAPA_A_TRANSVERSAL` según el caso), pero **igual necesitan pasar por la
   skill** — un título corto también puede llevar una afirmación falsa
   (`CLAUDE.md §4`).
3. Solo con `gate_arte: ABIERTO` en el claim packet correspondiente entra a
   `legalmente-visual-system` para el canal `linkedin-founder` (4:5,
   estructura profesional, per el Índice v18 de Drive).
4. Nada de esto se publica automáticamente — la publicación sigue siendo una
   decisión humana separada y externa a este repositorio.
