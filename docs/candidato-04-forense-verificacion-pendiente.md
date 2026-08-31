# Verificación pendiente — CANDIDATO-04-FORENSE

Runbook operativo, no canon. Complementa
`.claude/skills/legalmente-legal-verification/pilot/candidates/pieza-04-forense-candidato.json`.

**Estado real**: no es un claim packet todavía — es un candidato con una
hipótesis de trabajo explícitamente marcada NO_VERIFICADA. `EGRESS_BLOCKED`
confirmado de nuevo hoy contra `diputados.gob.mx` (esta vez con la URL
específica del CNPP). Nadie ha podido abrir ninguna de las 3 fuentes
candidatas desde esta sesión.

## Hipótesis de trabajo (a confirmar o refutar, no a dar por cierta)

> En los sistemas procesales de tradición continental que rigen a México,
> España y Argentina, la prueba pericial se valora junto con el resto del
> material probatorio según reglas de sana crítica o libre valoración
> razonada — no vincula automáticamente al juzgador ni sustituye su
> valoración.

Esto es doctrina procesal ampliamente aceptada en términos generales, **pero
el nombre exacto del estándar, el artículo que lo recoge y sus excepciones
varían por país y por materia (penal vs. civil) dentro del mismo país** — no
se puede convertir en un claim con `texto_exacto` sin verificar cada uno.

## Qué verificar por país

### México — Código Nacional de Procedimientos Penales
- URL candidata: `https://www.diputados.gob.mx/LeyesBiblio/pdf/CNPP.pdf`
- Qué buscar: el artículo que regula la valoración de la prueba (buscar
  "libre valoración", "sana crítica" o "apreciación de la prueba" dentro
  del documento — el CNPP mexicano usa terminología propia que hay que
  confirmar, no asumir que es "sana crítica").
- Qué confirmar: número de artículo exacto, texto literal, si distingue
  prueba pericial de otras pruebas, si sigue vigente.

### España — Ley de Enjuiciamiento Criminal / Ley de Enjuiciamiento Civil
- URL candidata: `https://www.boe.es/buscar/act.php?id=BOE-A-1882-6036` (LECrim)
- Nota: España tiene DOS códigos procesales relevantes (penal y civil) con
  reglas de valoración de prueba pericial potencialmente distintas — hay que
  decidir si el claim cubre ambos o se limita a uno, y decirlo explícitamente.
- Qué buscar: "sana crítica" es el término más probable en el ámbito civil
  español (art. 348 LEC para pericial), pero debe confirmarse el número
  exacto y el texto.

### Argentina — Código Procesal Penal Federal / CPCyN
- URL candidata: `https://servicios.infoleg.gob.ar/infolegInternet/anexos/230000-234999/234362/norma.htm`
- Qué buscar: artículo sobre valoración de la prueba pericial — Argentina
  también distingue procesal penal federal de procesal civil y comercial,
  y además tiene códigos provinciales que pueden diferir del federal.
- Decisión previa necesaria: ¿el claim se limita al fuero federal, o intenta
  cubrir el patrón general? Si es lo segundo, el riesgo de falsa
  universalización es alto — mejor limitarlo a federal y decirlo.

## Antes de escribir el claim

1. Verificar las 3 fuentes (origen oficial, texto exacto, vigencia).
2. Decidir el alcance exacto: ¿penal, civil, o ambos? ¿nacional/federal o
   también subnacional?
3. Redactar el `texto_exacto` del claim citando el artículo real confirmado
   — nunca antes de tener el texto verificado.
4. Correr `validate-claim-packet.py` sobre el nuevo claim packet una vez
   creado (todavía no existe — el candidato pasa a claim packet real solo
   después de este paso).

## Cómo registrar el resultado

Igual que PIEZA-02/03: actualizar `verificacion_fuente` de cada fuente en
el candidato (o ya en el claim packet, si se crea) con
`origen_oficial_confirmado`, `texto_exacto_consultado`, `vigencia_comprobada`,
`fecha_comprobacion`, `metodo_o_evidencia`, `observaciones`.
