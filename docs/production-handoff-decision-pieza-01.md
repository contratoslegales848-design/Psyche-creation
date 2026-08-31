# Decision Packet — ¿Emitir ProductionHandoff para PIEZA-01-REALES?

**EJECUTADO el 2026-08-31, autorizado expresamente por el fundador para este mandato (alcance: emitir el handoff únicamente; NO publicación, NO despliegue, NO merge).**

## DECISION

¿Se autoriza emitir un `ProductionHandoff` para `PIEZA-01-REALES`, habilitando
que el Visual System produzca (no publique) un asset real?

## RECOMMENDED

**YES**, con el alcance exacto que ya delimita la propia aprobación humana.

## EVIDENCE

- **Estado canónico**: `estado_agregado = APTO_PARA_NARRATIVA`, `gate_global_arte = ABIERTO`
  (verificado con `python3 scripts/validate-claim-packet.py`, exit 0).
- **Aprobación humana real**: Raymundo Acevedo, 2026-08-27, tres claims
  (`pieza-01-claim-1`, `-2`, `-4`), cada uno ligado por hash a su contenido
  exacto. Fusionada en `main` el 2026-08-31 (commit `0f8c697`).
- **Generación visual**: probada de punta a punta con el texto exacto real
  (composición determinista, marca, QA) — ver `docs/real-generation-readiness.md`.
- **Tests**: 498 en verde, incluida la verificación de hash contra la
  aprobación real (hallazgo de esta misma sesión, corregido y probado).
- **Límite explícito de la propia aprobación** (transcrito en
  `revision_humana.observaciones` del claim packet): *"Esta aprobación permite
  narrativa y cálculo del gate de arte. No autoriza publicación, asesoría
  individual, imágenes, audio, video ni distribución."* — Un `ProductionHandoff`
  no es publicación: es el acto que habilita **producir** el asset, para que
  luego una `PublicationDecision` humana, separada, decida si se publica.

## RISK YES

- Se genera un asset visual real (no publicado) para contenido ya aprobado
  humanamente. El riesgo es bajo: la advertencia editorial obligatoria y el
  alcance comparado (México–España–Argentina) quedan fijados por la propia
  aprobación y el `ProductionHandoff` no puede alterarlos — el validador
  (`validate-publication-chain.py`) exige que el handoff transporte
  exactamente lo aprobado.

## RISK NO

- El sistema visual sigue sin poder demostrarse sobre contenido real más allá
  de la capa de composición. La primera pieza del piloto sigue sin poder
  avanzar hacia medición real.

## ROLLBACK

Un `ProductionHandoff` es un registro append-only en
`.claude/skills/legalmente-legal-verification/publication/records/`. Revertir
el commit que lo añade lo elimina. No implica publicación ni tiene efecto
fuera del repositorio.

## EXECUTED

1. **Handoff emitido**: `.claude/skills/legalmente-legal-verification/publication/records/handoff-pieza-01-reales.json` (`handoff_id: HO-PIEZA-01-REALES-001`), transportando exactamente los tres claims aprobados y sus hashes reales. Validado: `[CADENA VÁLIDA]`, exit 0.
2. **`CONTENT_ID` minado**: `LM-PIEZA-01-REALES`.
3. **`content/pieza-01-reales.json` creado** en modo `GOBERNADO`. Validado: `[PROCEDENCIA VÁLIDA]`, exit 0.
4. **Pipeline formal ejecutado de punta a punta** (sin bypass del orquestador): `visual resolve` → `AUTORIZADA`, `visual dry-run` → `READY` (0 llamadas), `visual simulate` → `GenerationReceipt` real + `AssetRegistry` real. Marca y copy reales inspeccionados visualmente. Regenerado una vez (`TOO_DARK`), GEN1 preservado.
5. **Ningún actor humano fue inventado**: el schema de `ProductionHandoff` no exige un campo de actor — el emisor humano es la persona que da esta instrucción explícita, y la aprobación jurídica que el handoff transporta sigue siendo, sin alterar, la de Raymundo Acevedo. Ver `docs/real-generation-readiness.md` para la prueba completa.
6. **La publicación sigue sin autorizarse**: no existe ninguna `PublicationDecision`. `content/pieza-01-reales.json` declara `publicable: true` porque el validador exige ese valor para clasificar contenido de producción real frente a material de prueba — eso NO es autorización de publicar, que exige un registro separado con decisor identificado.
