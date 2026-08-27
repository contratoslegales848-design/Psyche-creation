# Artefactos de contenido

Cada `*.json` de este directorio es una pieza que el renderizador de Remotion puede
convertir en video. `src/content.ts` los carga y los valida en tiempo de bundle.

## Procedencia: obligatoria, sin modo por defecto

Todo artefacto declara `procedencia`. Un JSON sin ella **no se renderiza**.

| `modo` | Qué significa | Qué exige |
|---|---|---|
| `GOBERNADO` | hay un `ProductionHandoff` válido detrás | `handoff_id`, `piece_id`, `claims[]` con `approved_claim_hash`, `jurisdiction_layer` igual al alcance del claim, `production_status: APROBADO_QA` |
| `NO_APLICA` | por decisión de gobernanza no hay afirmación jurídica que verificar | `motivo_no_aplica` tipificado, `justificacion_no_aplica`, `autorizado_por`, `fecha_autorizacion`, `jurisdiction_layer: NO_APLICA` |
| `EJEMPLO_TECNICO` | material de prueba del pipeline | `publicable: false` |

Motivos tipificados de `NO_APLICA` (lista cerrada): `CITA_HISTORICA`,
`FORMATO_DE_GOBERNANZA`, `CONTENIDO_NO_JURIDICO`. "No aplica" sin motivo tipificado
sería una vía de escape, y por eso no se admite.

## Taxonomía: obligatoria en contenido publicable

`materia`, `submateria`, `concepto`, `situacion_humana`, `content_type`. Es también
la clave anti-duplicados: dos piezas publicables no pueden ocupar la misma casilla
de `materia/submateria/concepto`.

## Dónde se comprueba qué

- **Forma**, en tiempo de bundle: `src/content.ts`. Falla cerrado.
- **Fondo**, en CI: `scripts/validate-content-provenance.py`. Resuelve el handoff,
  valida la cadena, recalcula los hashes contra el claim packet y comprueba que la
  capa jurisdiccional no se haya reetiquetado.

```bash
python3 scripts/validate-content-provenance.py
```

## Lo que la procedencia NO significa

Que un artefacto sea `GOBERNADO` y válido significa que **puede producirse** y que
su origen es verificable. **No** significa que pueda publicarse: publicar exige una
`PublicationDecision` humana AUTORIZADA. Ver
`.claude/skills/legalmente-legal-verification/publication/README.md`.
