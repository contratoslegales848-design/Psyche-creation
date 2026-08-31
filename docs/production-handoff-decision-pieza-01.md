# Decision Packet — ¿Emitir ProductionHandoff para PIEZA-01-REALES?

**No es una decisión técnica. Requiere al fundador.**

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

## EXACT ACTION

1. El fundador (o quien tenga autoridad delegada) decide `YES` / `NO`.
2. Si `YES`: una sesión (esta u otra) construye el `ProductionHandoff` con
   `validate-publication-chain.py` como referencia de forma, transportando
   **exactamente** los tres claims aprobados y sus hashes — sin alterar nada.
3. Tras el handoff, crear `content/pieza-01-reales.json` en modo `GOBERNADO`
   con `piece_id`, `handoff_id` y los `approved_claim_hash`.
4. Sólo entonces `visual dry-run` y `visual simulate` producirán un
   `GenerationReceipt` real, registrado en `AssetRegistry`.
5. La publicación sigue siendo un acto humano posterior y separado
   (`PublicationDecision`), fuera del alcance de cualquier sesión técnica.
