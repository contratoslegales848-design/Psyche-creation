# Registros reales de la cadena post-aprobación

Aquí viven los registros **reales** (`ProductionHandoff`, `PublicationDecision`,
`PublicationRecord`, `MeasurementRecord`, `Learning`), uno o varios por archivo JSON.

Hoy está vacío a propósito: **no hay todavía ninguna pieza en producción gobernada**.
Que esté vacío es información, no una carencia pendiente de rellenar.

Quién lee este directorio:

- `scripts/validate-publication-chain.py` (con `--dir`), para validar la cadena.
- `scripts/validate-content-provenance.py` (en la raíz del repositorio), que busca
  aquí el `ProductionHandoff` que respalda cada artefacto de `content/` en modo
  `GOBERNADO`.

Un handoff que no valida **no se indexa**: el artefacto que lo invoque quedará sin
procedencia, que es exactamente el resultado correcto.

Recordatorio: un handoff válido habilita **producir**. Publicar exige además una
`PublicationDecision` humana AUTORIZADA. Ver `../README.md`.
