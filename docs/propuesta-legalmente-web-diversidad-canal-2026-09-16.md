# Propuesta (no aplicada) — legalmente-web: diversidad de `visualGrammar` por canal

`legalmente-web` (cuenta `legallmente-alt`) es **solo lectura** para esta sesión
(CLAUDE.md §8). Este documento es el patch-series que ese hallazgo requiere
entregar sin tocar el repositorio ajeno — corrección del Hallazgo 5 de
`docs/auditoria-monotonia-visual-2026-09-16.md`, Fase 8-9 del mandato
"Súper Prompt" (Founder, 16-sep-2026).

## Corrección al hallazgo original

La auditoría (Fase 1) decía "un universo de solo 5 tokens en total". Al
escribir el patch se verificó el archivo real
(`src/lib/editorial-engine/index.ts`, rama
`chatgpt/image-generator-reconciliation-v2-2026-09-13`) y son **6**:

```ts
export const VISUAL_GRAMMARS = [
  "CINEMATIC_PHOTOGRAPHY",
  "EDITORIAL_STILL_LIFE",
  "CLASSICAL_REINTERPRETATION",   // <- nunca aparece en ningún perfil de canal
  "ARCHITECTURAL_MINIMALISM",
  "HISTORICAL_DOCUMENTARY",
  "CONCEPTUAL_SYMBOLISM",
] as const;
```

Hallazgo adicional, más grave que el original: `CLASSICAL_REINTERPRETATION`
es un valor **inalcanzable**. Ningún `ChannelStyleProfile.visualGrammars`
(`channel-strategy.ts`, los 4 canales) lo incluye, así que
`scoreChannelFit()` nunca le da puntaje de encaje por canal (`grammarFit`
siempre 0 para ese valor) — 1 de los 6 tokens del universo ya declarado es
código muerto en la práctica.

## Qué SÍ está bien y no se toca

`index.ts` ya tiene reglas de lote reales y correctas (no es el mismo
problema que Psyche-creation tenía sin regla de lote):

```ts
if (new Set(candidates.map((item) => item.visualGrammar)).size < 4) {
  errors.push("A 10-piece batch must use at least 4 visual grammars.");
}
...
if (previous.format === candidate.format && previous.visualGrammar === candidate.visualGrammar) {
  errors.push(`Adjacent pieces cannot repeat both format and visual grammar: ${candidate.id}.`);
}
```

Mínimo 4 grammars distintos por lote de 10 y sin repetición consecutiva de
`(format, visualGrammar)` — comparable a las reglas de
`visual_fingerprint_batch.py` de este repositorio. El problema no es el
mecanismo de lote; es que el universo de donde ese mecanismo elige tiene
6 tokens (5 alcanzables) repartidos en 4 canales de 3 cada uno, sin
ninguna conexión al catálogo maestro real de 504 direcciones + 263
auxiliares que este repositorio ya construyó (Fase 2-3).

## Patch propuesto

Ver `propuesta-legalmente-web-diversidad-canal-2026-09-16.patch` (mismo
directorio) — verificado con `git apply --check` contra el clon local real
en SHA `27df096e54e9ca4c5552eb26bbe60319d4ef70d5` (rama
`chatgpt/image-generator-reconciliation-v2-2026-09-13`, la misma verificada
en CLAUDE.md §7): aplica limpio. Además se aplicó temporalmente, se corrió
el nuevo test con `npx tsx --test` (pasa: 3/3), se revirtió el fix a mano
para confirmar que el test SÍ falla sin él (1/3 fallos, exactamente
`CLASSICAL_REINTERPRETATION` señalado como no alcanzable), y se restauró el
clon a su estado original (`git checkout -- .`, sin cambios dejados en el
repositorio de solo lectura). No es una propuesta sin probar.

Alcance deliberadamente mínimo (arreglar el bug real, no rediseñar el
motor editorial de un repo ajeno sin autorización):

1. `index.ts`: comentario junto a `VISUAL_GRAMMARS` documentando que es un
   universo reducido, pendiente de conectar al catálogo maestro de
   Psyche-creation (mismo patrón ya aplicado en `legalmente-remotion`,
   PR #5) — no se retira el enum ni se reemplaza por 504 valores sin que
   el fundador decida esa integración cross-repo.
2. `channel-strategy.ts`: `CLASSICAL_REINTERPRETATION` se añade al perfil
   `linkedin-founder` (coherente con su `visualDirection` ya declarada:
   "warmer copper, parchment or private-study variants... reflection") —
   deja de ser un valor muerto sin inventar un canal nuevo ni tocar los
   otros 3 perfiles.
3. Un test nuevo en `channel-strategy.test.ts` que falla si algún valor de
   `VISUAL_GRAMMARS` queda sin aparecer en ningún `visualGrammars` de
   canal — regresión directa de este hallazgo, para que no vuelva a pasar
   en silencio si se añade un séptimo token.

## Qué requiere decisión del fundador (no se decide aquí)

- Si `legalmente-web` debe eventualmente leer el catálogo maestro real
  (767 módulos) en lugar de su propio enum de 6 — es un cambio de
  arquitectura cross-repo, no un fix de hallazgo puntual.
- Si `CLASSICAL_REINTERPRETATION` pertenece a `linkedin-founder` (mi
  propuesta, justificada arriba) o a otro canal, o si el token debía
  eliminarse en vez de conectarse.

## Entrega

Patch-series en este archivo + el `.patch` adjunto, tal como exige
CLAUDE.md §8 para un repositorio de solo lectura. No se aplicó ningún
cambio en `legalmente-web`. No se pidió ni se usó ningún permiso de
escritura sobre ese repositorio.
