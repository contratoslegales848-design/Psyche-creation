# Revisión externa de arte (15-sep-2026) — verificación y corrección

**Origen:** revisión visual hecha por una sesión de Claude sin acceso a GitHub,
navegando `facebook.com/juridicoeinmobiliarioespecializado/photos`, a petición
del fundador. Documentos completos en Drive: "LegalMente — Revisión externa de
arte: evolución visual y corrección del motor de rotación"
(`1T-74QMW2ItP1JPGSazy3Eeh7S521Sr7wllUZiFyXuKA`) e "Instrucción para Claude
Code — corregir repetición de escenario y elevar piso de diseño"
(`13Ko0R3bxdKKGE-8Zoacus_1-iE0kkzqqVfNhPF4YzuU`). Esta sesión tenía acceso a
GitHub; este documento es la verificación pedida — "confirmar cada punto
contra el repositorio real antes de tratarlo como diagnóstico cerrado" — y
declara explícitamente qué se pudo confirmar y qué no.

Registro paralelo en Drive: "LegalMente — Bitácora — Adenda 15-sep-2026"
(`1yopa0iVEJKVcfIuNl70F5T43WrrOhvYjblg40ZEEHG0`), §13-16, ampliando
"LegalMente — Bitácora de cambios (ciclo 2026-09)".

## 1. La hipótesis de la instrucción no se sostuvo — la corregida sí

La instrucción preguntaba si las piezas fotográficas venían de
`scripts/generar-banco-prompts.mjs` + `config/catalogo-estilos.json`. Ninguno
de los dos existe en ningún repositorio accesible a esta cuenta:

- `contratoslegales848-design/Psyche-creation` (este repo): no existen.
- `contratoslegales848-design/legalmente-remotion`: no existen en `main` ni en
  ninguna de sus 7 ramas remotas (`chore/legalmente-carousel-preflight`,
  `claude/gemini-cli-install-csk1uu`, `claude/install-multiple-packages-klp26v`,
  `claude/legalmente-verified-execution-eeawus`,
  `claude/remotion-render-typography-test-1lf0ae`,
  `codex/batch-carrusel-frases-10`, `feature/web-astro-scaffold`).
- `legallmente-alt/legalmente-web`: no existen; su `src/lib/image-generator/`
  (rama `chatgpt/image-generator-reconciliation-v2-2026-09-13`, ya reconciliada
  en una fase previa de este mismo repo) es una capa de validación/contrato,
  no un generador con banco de escenarios propio.

`corpus/README.md` (de una fase anterior de este repo) ya documentaba que "el
repositorio histórico de Remotion... (`config/catalogo-estilos.json`...) no
está accesible" — y el propio `00 LEER PRIMERO §10` de Drive (7-sep) dice lo
mismo. Sigue siendo cierto hoy: el script que el banco v3 declara como su
origen no vive en ningún repositorio que esta cuenta pueda alcanzar.

## 2. Hallazgo real: un tercer canon, nunca reconciliado

`legalmente-remotion` **sí es accesible hoy** (se agregó y clonó en esta
sesión) — corrige la Bitácora §7 de Drive (7-sep), que registraba el repo como
no accesible. Es la primera vez que se inspecciona desde entonces.

Su `main` (HEAD `f656a92`, última actividad real 9-sep) no contiene el motor
de 18 canales / 55-174 guiones que describen los Índices de Drive. Contiene un
canon de marca **distinto y nunca conectado al de Drive/banco-v3**:
`legalmente-marca-y-estilo.md` (v1.0, agosto 2026) — 5 pilares de contenido
(no de arte), un solo registro visual fotorrealista (sin distinción Carril
A/B), y su propio catálogo de objetos-escena (§3.6), sin un solo escenario de
ubicación real. Tres de los cuatro títulos que la revisión externa citó como
evidencia de repetición ("El depósito no es renta adelantada", "Poder
autoriza vender", "Todo contrato es un convenio...") **no aparecen en el
banco v3** (174 filas, verificado por grep) — confirma que la producción
reciente sale de este segundo canon, no del que este repo modela en `visual/`.

**Causa técnica exacta** (no una hipótesis): `legalmente-marca-y-estilo.md`
§3.2 ("Flujo A", el prompt real de fondo) llevaba fijo, en las 175 piezas del
proyecto, `"Warm olive-khaki gradient studio backdrop"` — sin importar qué
dijera `[ESCENA]`. El banco de 15 escenarios reales sí existe, pero solo en el
catálogo v3 de Drive; nunca se portó al documento que de verdad alimenta la
producción.

## 3. Lo que no se pudo verificar

Esta sesión intentó `WebFetch` directo sobre
`facebook.com/juridicoeinmobiliarioespecializado/photos`: bloqueado por el
proxy de red del entorno (`EGRESS_BLOCKED`, dominio Facebook). No hay forma de
confirmar de manera independiente cuántas de las últimas 15-20 piezas
publicadas repiten escenario. Esta corrección se apoya en la confirmación
visual directa ya hecha por el fundador y por la revisión externa, y en la
causa técnica real encontrada en el repositorio — no en una verificación
propia del feed.

## 4. Corrección aplicada

Rama `claude/revision-externa-arte-sep2026` en `legalmente-remotion`, creada
desde `main`, **pusheada, sin merge**:

- §3.2: fondo de estudio fijo → variable, toma el banco de escenarios reales.
- Nuevo §3.7 "Banco de escenarios reales": los 15 escenarios verificados
  contra el banco v3 (`mercado al amanecer`, `taller mecánico`, `garita de
  aduana`, `patio de vecindad`, `azotea urbana`, `cocina familiar`, `aula
  vacía`, `estudio fotográfico de principios de siglo`, `gabinete de mapas y
  cartografía`, `imprenta de valores y documentos oficiales`, `notaría de
  pueblo`, `obra parada`, `sala de máquinas`, `taller de imprenta`, `vagón
  nocturno`) más una lista ampliable citada por el Founder, marcada
  explícitamente como no verificada todavía.
- Regla de anti-repetición contra las **últimas 5 piezas publicadas** (no la
  anterior, no lo generado) en §5.1 y §5.3, con la advertencia de que hoy no
  existe ningún registro de escenario por pieza publicada — sin ese registro
  la regla es declarativa, no ejecutable.
- Mecanismo de intervención en espacio real ("Vigencia y eficacia") generalizado
  como tercer modo de escena, con prompt propio.
- Integración física de marca (§2.6): confirmada ya vigente y bien resuelta;
  extendida al modo de intervención en espacio real.
- Carril A "óleo dramático" / Carril B fotográfico: **no resuelto aquí**.
  `legalmente-marca-y-estilo.md` no declara esa distinción; introducirla es
  una decisión de dirección de arte del Founder, no una corrección técnica.

## 5. Banco de 100 prompts nuevos — decisión

Verificado contra el archivo real (no solo contra su índice): 100 filas, 100
slugs únicos, **0 traslapes** contra los 174 slugs del banco v3 (confirmado
programáticamente). Materias: Inmobiliario 14, Procesal-Penal 12, Laboral 12,
Familia y sucesiones 10, Digital y datos 10, Derecho y Literatura 8,
Mercantil-Societario 8, Contratos 8, Consumidor 6, Fiscal 4, Administrativo 4,
Principios 4. Carril B 64 / A 36. Mismo esquema de 13 columnas que el v3.

**Decisión: lote independiente, no integrado a v3→v4/274.** CLAUDE.md §6:
"no producir nuevos bancos grandes... mientras el lote piloto activo no se
haya publicado y medido, salvo orden expresa del fundador" — sin evidencia de
que ese lote piloto esté publicado/medido (y con el hallazgo de este mismo
documento de que la producción reciente ni siquiera sale del banco v3), la
ruta conservadora es no activarlo todavía. Ambas rutas siguen siendo válidas;
esta queda declarada y no cierra la puerta a integrarlo después.

## 6. Pendientes sin resolver

- **44 prompts de LinkedIn** (15-sep): no se encontró como archivo persistido
  en Drive — se entregó "en el chat". Queda `PENDIENTE_DE_ARCHIVO`; sin el
  archivo real no se puede registrar junto a LM-LI-001–004 / `linkedin-ray-16`.
- Los 5 "lotes" de 175 piezas que `legalmente-marca-y-estilo.md` dice tener
  versionados en el mismo repositorio no están ahí ni se encontraron en Drive
  bajo esos nombres.
- Existe una **tercera** línea de producción activa en `legalmente-web`
  (`production-policy` / `visual-argument` / "convergencia", PRs #43–#55, sin
  mergear) que esta sesión no audita ni reconcilia — queda declarada como
  complejidad conocida, no ignorada.

**ESTADO: NO MERGE. NO DEPLOY. NO PUBLICACIÓN.**
