# Handoff — Lote de 10 claim packets v4

**Fecha:** 2026-09-03 · **Rama:** `claude/legalmente-integration-surgery-nap17t`
**Ubicación:** `content/claim-packets/` · **Estado global:** `NOT_PUBLISHED` · 10 piezas · **13 claims** · 10/10 gates `CERRADO`

> **Actualización 2026-09-04.** El directorio contiene ahora **11 piezas y 15 claims**: se añadió
> `LM-LN-REP-001`, la primera pieza de la superficie profesional de LinkedIn. Este documento sigue
> describiendo el lote de diez; la nueva pieza tiene su propia sección al final.

Los diez temas fueron declarados por el fundador con la etiqueta «QA PASSED» y copy exacto ya
aprobado. Ninguno lo estaba: no existían en el canon, no tenían claim packet, y los cuatro
documentos de Drive citados como evidencia no son accesibles desde la cuenta de esta sesión.
Este lote los convierte en expedientes trazables con una siguiente acción concreta cada uno.

## Matriz individual

| Packet | Claim | Fuente primaria | Jurisdicción | Estado | Gate | Razón |
|---|---|---|---|---|---|---|
| `LM-ACT-001` | `lm-act-001-claim-1` | STS 1250/2024 (CENDOJ) | España | `REQUIERE_INVESTIGACION` | `CERRADO` | Resolución no localizada: el enlace del CGPJ está tras CAPTCHA |
| `LM-ACT-001` | `lm-act-001-claim-2` | Convenio 158 OIT art. 7 | `NO_APLICA` | `REQUIERE_INVESTIGACION` | `CERRADO` | **Desdoblado**: un convenio internacional no es fuente de derecho interno por sí solo |
| `LM-ACT-003` | `lm-act-003-claim-1` | Ley 27.742 (Boletín Oficial AR) | Argentina | `REQUIERE_INVESTIGACION` | `CERRADO` | Falta el artículo derogatorio exacto: «derogó las multas» exige citar el artículo, no la ley entera |
| `LM-ACT-003` | `lm-act-003-claim-2` | LCT art. 245 (InfoLEG) | Argentina | `REQUIERE_INVESTIGACION` | `CERRADO` | «Sigue vigente» es una afirmación de vigencia; exige `vigencia_comprobada`, imposible sin lectura |
| `LM-ACT-004` | `lm-act-004-claim-1` | RGPD art. 7 (EUR-Lex) + AEPD + INAI + SIC | Capa A: ES, MX, CO | `REQUIERE_INVESTIGACION` | `CERRADO` | EUR-Lex sólo respalda «Unión Europea»: España queda sin fuente nacional propia. Techo = mínimo por país |
| `LM-ACT-008` | `lm-act-008-claim-1` | Ley 2191 de 2022 arts. 3-4 (Función Pública CO) | Colombia | `REQUIERE_INVESTIGACION` | `CERRADO` | «Constituye indicio de acoso» es consecuencia autónoma; puede proceder de la Ley 1010/2006, no de ésta |
| `LM-EVG-001` | `lm-evg-001-claim-1` | CCF MX art. 791 + CC ES art. 432 + CCyCN AR art. 1910 | Capa A: MX, ES, AR | `REQUIERE_INVESTIGACION` | `CERRADO` | **La más sólida del lote**: 3 países, 3 fuentes registradas. Sólo falta leer los textos |
| `LM-EVG-002` | `lm-evg-002-claim-1` | LFT arts. 33, 784 + Tesis 2a./J. 138/2012 (SCJN) | `NO_DETERMINADO` | `REQUIERE_INVESTIGACION` | `CERRADO` | Declarada panhispánica con fuentes de un solo país |
| `LM-EVG-003` | `lm-evg-003-claim-1` | CPEUM arts. 6-7 + CCF art. 1916 Bis | `NO_DETERMINADO` | `REQUIERE_INVESTIGACION` | `CERRADO` | Declarada panhispánica con fuentes de un solo país |
| `LM-CORP-002` | `lm-corp-002-claim-1` | LGSM arts. 16, 91-VII, 229-II + CCom art. 78 | `NO_DETERMINADO` | `REQUIERE_INVESTIGACION` | `CERRADO` | Declarada panhispánica con fuentes de un solo país |
| `LM-CORP-004` | `lm-corp-004-claim-1` | LFPPI arts. 79-82 | `NO_DETERMINADO` | `REQUIERE_INVESTIGACION` | `CERRADO` | Declarada panhispánica con fuentes de un solo país |
| `LM-HIS-005` | `lm-his-005-claim-1` | STS 9-5-2013 (CGPJ) | España | `REQUIERE_INVESTIGACION` | `CERRADO` | Nulidad por falta de transparencia material: lo que esa sentencia sí sostiene |
| `LM-HIS-005` | `lm-his-005-claim-2` | Jurisprudencia TJUE | España | `REQUIERE_INVESTIGACION` | `CERRADO` | **Desdoblado**: la restitución íntegra procede del TJUE, no de la STS de 2013, que limitó la retroactividad |

## El hallazgo que más pesa

Cuatro de las diez piezas —`LM-EVG-002`, `LM-EVG-003`, `LM-CORP-002`, `LM-CORP-004`— se declararon
**«Panhispánico»** y aportan **fuentes de un solo país**. Ese es exactamente el patrón de falsa
universalización que la Capa A existe para impedir. Su alcance quedó en `NO_DETERMINADO` —falta de
investigación, no conclusión— con `riesgo_falsa_universalizacion: alto`.

Cada una tiene dos salidas: investigar el equivalente en al menos dos jurisdicciones más, o
reclasificarla como `CAPA_C_NACIONAL` y declarar México en el título.

Un segundo hallazgo, de fondo jurídico: `LM-HIS-005` afirma restitución «desde el origen» citando la
STS de 9 de mayo de 2013, que precisamente **limitó** la retroactividad. La restitución íntegra
procede de jurisprudencia posterior del TJUE. Publicar el copy con esa sola cita sería incorrecto.

## Registro oficial único — v1.0 → v1.1

Cuatro entradas añadidas por orden expresa del fundador, en el registro canónico
`.claude/skills/legalmente-legal-verification/references/official-source-registry.json`. No se creó
ningún registro paralelo.

| `id` | Organismo | Hostnames | Tipos permitidos | Ámbito |
|---|---|---|---|---|
| `aepd-es` | Agencia Española de Protección de Datos | `aepd.es` | `AUTORIDAD_PUBLICA_OFICIAL` | España |
| `inai-org-mx` | INAI | `inai.org.mx`, `home.inai.org.mx` | `AUTORIDAD_PUBLICA_OFICIAL` | México |
| `sic-gov-co` | Superintendencia de Industria y Comercio | `sic.gov.co` | `AUTORIDAD_PUBLICA_OFICIAL` | Colombia |
| `ilo-org` | Organización Internacional del Trabajo | `ilo.org`, `normlex.ilo.org` | `NORMA_OFICIAL`, `AUTORIDAD_PUBLICA_OFICIAL` | Internacional |

**Límite honesto registrado en cada entrada:** los hostnames no pudieron comprobarse en vivo
(`WebFetch` EGRESS_BLOCKED). Las entradas descansan en la orden humana, no en una verificación de
dominio hecha por el modelo. Deben revisarse antes de que ninguna fuente que las use alcance Nivel 1.

La entrada de la OIT lleva además una advertencia sustantiva: un convenio sólo obliga en el país que
lo **ratificó**, y su efecto interno depende de ese derecho nacional. Por eso sólo respalda el ámbito
internacional, nunca una jurisdicción concreta.

### Advertencias eliminadas y persistentes

Desaparecieron 4: OIT en `LM-ACT-001`; AEPD, INAI y SIC en `LM-ACT-004`.

**Persiste 1:** el **TJUE (`curia.europa.eu`)** no está en el registro. EUR-Lex está registrado para
normas, pero no hay entrada para la jurisdicción del Tribunal. Sin ella, `LM-HIS-005` no puede
alcanzar Nivel 1 aunque se lea el texto.

## Errores que el validador rechazó

Cinco, todos míos, ninguno simulado:

1. `Boletin Oficial de la Republica Argentina` sin acentos — la comparación con el registro es exacta tras normalizar, nunca por subcadena.
2. `Informacion Legislativa y Documental (InfoLeg)` — nombre canónico distinto.
3. `Organizacion Internacional del Trabajo` sin acentos.
4. `Departamento Administrativo de la Función Pública` — al canónico le falta `(Colombia) — Gestor Normativo`.
5. **EUR-Lex declarando cubrir «España».** El registro sólo lo autoriza a respaldar «Unión Europea». Es la misma regla que impide que una fuente española cubra a México, aplicada en dirección UE→país. Ese rechazo es lo que dejó a España sin fuente nacional en `LM-ACT-004`.

## Dependencias bloqueadas

`BLOCKED_EXTERNAL_ACCESS` — los documentos rectores de Drive citados como evidencia devuelven
`Requested entity was not found` con la cuenta de Drive de esta sesión: Manifiesto Visual Rector,
Catálogo Top 15, Expediente Tetris y Manifiesto Operativo de Agentes. **Precisión necesaria:** eso
significa *no accesibles desde esta cuenta*, no que no existan. No se sustituyeron por inferencias.

`EGRESS_BLOCKED` — `WebFetch` hacia dominios oficiales sigue bloqueado. Es la causa directa de que
los 11 claims estén en `REQUIERE_INVESTIGACION`: ningún booleano de verificación pudo marcarse.

## Decisiones que requieren al fundador

1. **Las cuatro piezas mal declaradas panhispánicas**: ¿ampliar a tres jurisdicciones o reclasificar a Capa C con México en el título?
2. **`LM-HIS-005`**: el copy afirma algo que su fuente citada contradice. ¿Corregir el copy o cambiar la fuente?
3. **Registrar `curia.europa.eu`** para desbloquear el techo del TJUE.
4. **Verificar los cuatro hostnames añadidos** — las entradas descansan hoy en una orden, no en comprobación de dominio.
5. **`LM-ACT-004`** lleva `platform_review.required: true` (biometría, menores, criptomonedas). Señalado, no ejecutado.

## Producción visual

De las tres piezas del piloto, sólo **`pieza-01-reales` tiene el gate `ABIERTO`**. `pieza-02-laboral`
y `pieza-03-honor` están `CERRADO` en `REQUIERE_INVESTIGACION`. Ninguna de las diez de este lote es
elegible: los diez gates están cerrados.

## Siguiente acción única

**Conseguir acceso de lectura a las fuentes oficiales** —levantar el bloqueo de `WebFetch` o
depositar los textos en Drive— empezando por los tres artículos de `LM-EVG-001`, que es la única
pieza del lote con cobertura estructural completa en tres países y la primera capaz de subir de estado.

---

## Actualización 2026-09-03 — desdobles y salidas

Dos piezas se desdoblaron para que ninguna afirmación viajara mezclada con otra que no la sostiene.
`LM-ACT-001` separa el Convenio 158 OIT de la jurisprudencia española; `LM-HIS-005` separa lo que la
STS de 2013 sí sostiene de lo que procede del TJUE, y corrige el copy además de la tabla de fuentes.
El lote pasa de 11 a **13 claims**; los diez gates siguen `CERRADO`.

### Salidas de autoridad: cero

`scripts/report_blocked_packets.py` deriva de los propios packets qué falta por claim. Resultado
actual: **13 claims, 13 bloqueados, 0 salidas de autoridad permitidas**. Ningún packet puede producir
`copy_social.md`, `visual_prompt.json` ni `handshake_web.json` mientras su gate esté cerrado — hay
prueba que lo impide en `scripts/test_report_blocked_packets.py`.

Motivo dominante, en los 13: ninguna fuente alcanza Nivel 1 (texto no leído, vigencia no comprobada)
y la revisión humana está `PENDIENTE`. En los cuatro monopaís se suma el alcance sin determinar.

---

## Primera pieza de la superficie profesional — `LM-LN-REP-001`

**Fecha:** 2026-09-04 · Pilar **Representación** del banco de LinkedIn · gate `CERRADO`

Tema de origen en Drive: «El puesto no prueba facultades».

### El hallazgo: el tema de origen, tal como estaba redactado, es incorrecto

La verificación encontró un contraejemplo decisivo en la primera jurisdicción consultada. El
**art. 234 de la Ley de Sociedades de Capital** española extiende la representación del
administrador a **todos los actos comprendidos en el objeto social**, y declara **ineficaces frente
a terceros** las limitaciones de sus facultades *aunque estén inscritas* en el Registro Mercantil.

Es decir: en España, para el administrador, **el cargo sí acredita representación** dentro de ese
ámbito. La formulación amplia «el puesto no prueba facultades» es falsa al menos en uno de los tres
ordenamientos examinados, y quedó registrada en `redaccion_prohibida`.

Lo que las fuentes sí sostienen es una **distinción**, no una negación: hay dos vías por las que
alguien puede obligar a una sociedad —la que deriva del cargo y la que deriva de un poder— y cada
una tiene su propio alcance.

### Los dos claims

| Claim | Alcance | Fuentes | Estado |
|---|---|---|---|
| `claim-1` — dos vías de representación: la del cargo y la del poder | `CAPA_A_TRANSVERSAL` (ES · MX · AR) | LSC 234 · CCF 2554 · CCyCN 375 | `REQUIERE_INVESTIGACION` |
| `claim-2` — un poder en términos generales no habilita actos de disposición | `CAPA_C_NACIONAL` (MX · AR) | CCF 2554 · CCyCN 375 | `REQUIERE_INVESTIGACION` |

España queda **fuera** del `claim-2` a propósito: no se examinó el art. 1713 CC ni su relación con
el art. 234 LSC. Añadirla exigiría una fuente propia.

Y las técnicas mexicana y argentina **no coinciden**: el CCF exige otorgar el poder *con el carácter*
de actos de dominio; el CCyCN exige *facultad expresa*. Presentarlas como la misma regla sería
inexacto, y así consta en `redaccion_prohibida`.

### Por qué el gate está cerrado

`WebFetch` sigue bloqueado. Las tres fuentes son oficiales, con URL real, localizador concreto y
`registro_oficial_id` coherente —`boe-es`, `diputados-gob-mx`, `infoleg-gob-ar`— pero ninguna tiene
`texto_exacto_consultado: true`: se localizaron por `WebSearch`, no se leyeron literalmente. Sin esa
lectura ninguna pasa de Nivel 2.

La cobertura por fuentes del `claim-1` da `COBERTURA_COMPARADA_VERIFICADA` en tres jurisdicciones —
**no universalidad panhispánica**: hay más de veinte ordenamientos hispanohablantes.

Además, `confidentiality_review.required: true` en ambos claims: la superficie profesional se
alimenta de experiencia práctica y esa revisión es obligatoria antes de producir arte, aunque el
texto de estos claims sea conceptual.

### Siguiente acción única

Leer literalmente los tres artículos y comprobar su vigencia. Es lo único que separa esta pieza de
poder someterse a revisión humana.
