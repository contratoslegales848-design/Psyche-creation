# Verificación pendiente — PIEZA-02-LABORAL y PIEZA-03-HONOR

Runbook operativo. No es canon: es la lista exacta de qué falta comprobar
para que estas dos piezas puedan avanzar. Generado por
`visual/source_verification.py` contra los claim packets reales
(`.claude/skills/legalmente-legal-verification/pilot/claim-packets/`).

**Qué significa "PENDIENTE"**: esta sesión no tiene acceso de red
(`EGRESS_BLOCKED` confirmado contra 4 dominios oficiales distintos). No es que
falte trabajo — es que solo un humano (o una sesión con red distinta) puede
abrir estas URLs y confirmar.

**Qué hacer con cada fuente**: abrir la URL, localizar el artículo/sentencia
exacto, y confirmar tres cosas:
1. **origen oficial** — ¿la URL es realmente del organismo que dice ser?
2. **texto exacto** — ¿el artículo/localizador citado existe con ese número y dice lo que el claim afirma?
3. **vigencia** — ¿sigue vigente, o fue derogado/modificado?

Una vez confirmado (o refutado), se registra en `verificacion_fuente` de esa
fuente en el claim packet — nunca se toca `texto_exacto` del claim sin pasar
por el mecanismo de reformulación existente.

---

## PIEZA-02-LABORAL (14 fuentes pendientes, 6 ya verificadas)

### México (7 fuentes, 1 URL compartida)
Ley Federal del Trabajo: `https://www.diputados.gob.mx/LeyesBiblio/pdf/LFT.pdf`
- `SRC-P02-MX-LFT-01` — art. 47 (rescisión sin responsabilidad para el patrón)
- `SRC-P02-MX-LFT-02` — arts. 48 y 50 (reinstalación/indemnización)
- `SRC-P02-MX-LFT-03` — arts. 51 y 52 (rescisión imputable al patrón)
- `SRC-P02-MX-LFT-04` — art. 53, fracción I (mutuo consentimiento)

Constitución: `https://www.diputados.gob.mx/LeyesBiblio/pdf/CPEUM.pdf`
- `SRC-P02-MX-CPEUM-01` — art. 5 (libertad de trabajo)

### España (3 fuentes)
- `SRC-P02-ES-ET-01` — `https://www.boe.es/buscar/pdf/2015/BOE-A-2015-11430-consolidado.pdf` — Estatuto de los Trabajadores, arts. 49.1.d y 50
- `SRC-P02-ES-JUR-01` — `https://www.poderjudicial.es/search/openDocument/f8c0da1866ba8219/20120925` — STS 3504/2011
- `SRC-P02-ES-JUR-02` — `https://www.poderjudicial.es/search/openDocument/37c541c888d3f668/20201117` — STS 2486/2018

### Argentina (1 fuente pendiente — el resto de LCT ya está verificado)
- `SRC-P02-AR-JUR-01` — `https://aldiaargentina.microjuris.com/2023/12/13/...` — Sentencia CNAT Sala I, 13/12/2023. **Nota**: fuente secundaria (blog jurídico), no un repositorio oficial — verificar si hay un repositorio de jurisprudencia oficial argentino con el mismo fallo antes de aceptar esta.

### Colombia (3 fuentes)
- `SRC-P02-CO-CST-01` — `https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=199983` — arts. 61 y 62 literal B
- `SRC-P02-CO-CST-02` — mismo dominio — art. 64
- `SRC-P02-CO-CST-03` — `https://www.secretariasenado.gov.co/senado/basedoc/codigo_sustantivo_trabajo_pr001.html` — arts. 61, 62B, 64. **Nota**: el validador ya marcó `secretariasenado.gov.co` como hostname fuera del registro oficial cerrado — si es legítimo, hay que añadirlo a `references/official-source-registry.json` con `registro_oficial_id`.

---

## PIEZA-03-HONOR (12 fuentes pendientes, 1 ya verificada)

### México (5 fuentes)
- `SRC-P03-MX-CPEUM-01` — `https://www.diputados.gob.mx/LeyesBiblio/pdf/CPEUM.pdf` — arts. 6 y 7 (libertad de expresión, censura previa)
- `SRC-P03-MX-CCF-01` — `https://www.diputados.gob.mx/LeyesBiblio/pdf/CCF.pdf` — arts. 1916 y 1916 Bis (daño moral)
- `SRC-P03-MX-SCJN-JUR-01` — `https://sjf2.scjn.gob.mx/detalle/tesis/2003303` — Jurisprudencia 1a./J. 38/2013
- `SRC-P03-MX-SCJN-02` — `https://sjf2.scjn.gob.mx/detalle/tesis/2003643` — Tesis 1a. CXXXVIII/2013
- `SRC-P03-MX-SCJN-COMP-01` — `https://sjf2.scjn.gob.mx/detalle/tesis/2030841` — **número de tesis pendiente de identificar incluso antes de verificar**, resolver primero
- `SRC-P03-MX-QROO-PEN-01` — `https://documentos.congresoqroo.gob.mx/historial/11_legislatura/decretos/index.htm` — Decreto 151/2007, derogación arts. 132-141

### España (3 fuentes)
- `SRC-P03-ES-CP-01` — `https://www.boe.es/buscar/pdf/1995/BOE-A-1995-25444-consolidado.pdf` — Código Penal, arts. 205 y 208 (calumnia/injuria)
- `SRC-P03-ES-LO-01` — `https://www.boe.es/buscar/pdf/1982/BOE-A-1982-11196-consolidado.pdf` — LO 1/1982, arts. 7.7 y 9.3
- `SRC-P03-ES-TC-01` — `https://hj.tribunalconstitucional.es/es/Resolucion/Show/1048` — STC 107/1988
- `SRC-P03-ES-TC-02` — `https://hj.tribunalconstitucional.es/es/Resolucion/Show/6823` — STC 41/2011

### Argentina (3 fuentes pendientes, art. 109-110 CP ya verificado)
- `SRC-P03-AR-LEY-01` — `https://servicios.infoleg.gob.ar/infolegInternet/anexos/160000-164999/160757/norma.htm` — arts. 1-3
- `SRC-P03-AR-CSJN-01` — `https://sjconsulta.csjn.gov.ar/sjconsulta/fallos/verFallo.html?id=23773` — Fallos 308:789
- `SRC-P03-AR-CSJN-02` — `https://sjconsulta.csjn.gov.ar/sjconsulta/fallos/verFallo.html?id=125301` — Fallos 331:1530

### Sistema Interamericano (4 fuentes)
- `SRC-P03-CIDH-CADH-01` — `https://www.oas.org/dil/esp/tratados_b-32_convencion_americana_sobre_derechos_humanos.htm` — arts. 11 y 13
- `SRC-P03-CIDH-KIMEL-01` — `https://www.corteidh.or.cr/docs/casos/articulos/seriec_177_esp.pdf` — Caso Kimel, Serie C n.º 177
- `SRC-P03-CIDH-HERRERA-01` — `https://www.corteidh.or.cr/docs/casos/articulos/seriec_107_esp.pdf` — Caso Herrera Ulloa, Serie C n.º 107
- `SRC-P03-CIDH-ALVAREZ-01` — `https://www.corteidh.or.cr/docs/casos/articulos/seriec_380_esp.pdf` — Serie C n.º 380

---

## Orden sugerido (por menor esfuerzo / mayor desbloqueo)

1. **México LFT/CPEUM** (comparte 2 URLs para 5 fuentes de PIEZA-02) — abrir 2 PDFs, confirmar 5 artículos.
2. **México CPEUM/CCF/SCJN** (PIEZA-03) — 3 PDFs/páginas distintas, 5 fuentes.
3. **España** (7 fuentes entre ambas piezas) — BOE + Poder Judicial + Tribunal Constitucional.
4. **Argentina** (4 fuentes restantes) — resto de LCT + CSJN.
5. **Colombia** (3 fuentes) — incluye resolver si `secretariasenado.gov.co` debe añadirse al registro oficial.
6. **CIDH** (4 fuentes) — las más largas de leer (sentencias completas), dejar al final.

## Cómo registrar el resultado

Una vez verificada una fuente, actualizar su `verificacion_fuente` en el
claim packet correspondiente:

```json
"verificacion_fuente": {
  "origen_oficial_confirmado": true,
  "texto_exacto_consultado": true,
  "vigencia_comprobada": true,
  "fecha_comprobacion": "AAAA-MM-DD",
  "metodo_o_evidencia": "descripción de cómo se verificó y por quién",
  "observaciones": "..."
}
```

Después correr `python3 .claude/skills/legalmente-legal-verification/scripts/validate-claim-packet.py <archivo>`
para confirmar que el packet sigue siendo válido, y `python3 visual/cli.py system-queue`
para ver si la pieza avanza de `BLOCKED_BY_SOURCE_ACCESS`.
