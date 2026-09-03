# Motor de candidatos — cómo se hace cumplir la dirección

**Qué es esto.** La implementación de la decisión registrada en
[`docs/direccion-basico-antes-que-complejo.md`](direccion-basico-antes-que-complejo.md), que es
el canon y manda sobre este archivo. Aquí solo se describe el mecanismo.

**Implementación:** `content/topics/` · **Estado:** vigente

## 1. Corrección de fondo: un tema tampoco es terreno neutral

La primera versión de este motor decía que un tema «no afirma nada jurídico» y que por eso
podía existir sin fuentes. **Eso era falso**, y el fundador lo señaló.

Un título, una pregunta, un contraste o una justificación **pueden contener una proposición
jurídica**. El catálogo original decía cosas como *«es común a toda la tradición civil»* o
*«existe en todas las jurisdicciones»*: eso es una afirmación sobre más de veinte
ordenamientos, hecha sin haber leído ninguno. Que no nombre un país no la vuelve inofensiva —
la vuelve más difícil de auditar.

Ahora esas justificaciones se guardan como `hipotesis_de_transversalidad`, en estado
`LEGAL_HYPOTHESIS`, con `evidencia_por_jurisdiccion` vacío en los 24. Ninguna está comprobada
en ninguna jurisdicción todavía, y el catálogo lo dice.

## 2. Escalera epistémica

| Estado | Qué significa |
|---|---|
| `TOPIC_CANDIDATE` | Pregunta humana que merece investigarse |
| `LEGAL_HYPOTHESIS` | Relación jurídica plausible, no demostrada |
| `VERIFIED_CLAIM` | Con fuente, territorio, vigencia y límites comprobados |
| `HUMAN_APPROVED_CONTENT` | Texto exacto aprobado por un humano, ligado por hash |

Ningún escalón se alcanza por el paso del tiempo ni por la ausencia de objeciones. **El motor
emite el primero y no puede conceder ninguno de los otros tres.**

## 3. Lo que el filtro demuestra, dicho con exactitud

```
NO_EXPLICIT_NATIONAL_ANCHOR
```

El **texto** del candidato no nombra país, ley nacional, moneda ni plazo. Eso es una propiedad
de la redacción, no del derecho.

**No demuestra `CAPA_A_TRANSVERSAL`.** La versión anterior hacía ese salto, y era exactamente
el error que pretendía evitar: cuatro de las diez piezas del último lote estaban escritas sin
un solo topónimo y describían el derecho de un único país. La capa jurisdiccional sale como
`NO_DETERMINADO` para los 24.

## 4. Cobertura comparada ≠ universalidad

Tres jurisdicciones con evidencia propia demuestran **cobertura comparada de esas tres**. Hay
más de veinte ordenamientos hispanohablantes; tres no son todos. El dictamen lo emite como
`cobertura_comparada_de: [...]` con `es_universalidad_panhispanica: false`, y añade
«No se extrapola al resto del ámbito hispanohablante».

La cobertura se cuenta resolviendo cada fuente contra el registro oficial, **nunca leyendo la
prosa**: sobre los packets del repositorio, el filtro de texto detecta 4 de los 9 mono-país; la
cobertura detecta los 9. Una fuente supranacional aporta contexto y no suma jurisdicción
nacional — si sumara, un solo tratado volvería transversal cualquier afirmación.

## 5. Diversidad editorial

El motor conocía cuatro arquetipos cerrados y **doce de los veinticuatro temas eran
`DIFERENCIAS`**. Un pozo así no puede producir un lote de diez con cinco formas distintas: el
motor empujaba a repetir.

Ahora el vocabulario está en `content/topics/lote.py` — trece formas, de `FRASE_O_MAXIMA` a
`GUIA_O_CHECKLIST`. Reglas por defecto para un lote de diez:

- mínimo **5** formas distintas;
- ninguna forma más de **2** veces, salvo serie expresamente solicitada;
- prohibido repetir simultáneamente **concepto + ángulo + situación humana + utilidad**.

El **soporte** (carrusel, short, copy, pieza estática) es un eje aparte a propósito: el mismo
contenido en otro soporte no es contenido nuevo, y mezclarlos en un solo eje habría permitido
justificar repetición cambiando de envase. La forma editorial real viaja a la taxonomía
(`content_type`); fijarlas todas como `"concepto"` borraba la única señal que permite ver que
un lote está repitiendo formato.

## 6. Memoria contra lo ya producido

Comprobar que los identificadores del lote nuevo son distintos **entre sí** no demuestra nada.
`lote.py` compara contra el inventario real: piezas de `content/`, claim packets y
`visual/inventory.py`.

Cuando el inventario no puede consultarse, la respuesta honesta no es «es nuevo»: es
`INVENTORY_NOT_CHECKED`, y **ningún candidato puede declararse nuevo**.

## 7. Orden del pipeline

```
pregunta humana → candidato → investigación → fuente y territorio → claim →
validación técnica → revisión humana → GATE DE ARTE → narrativa y formato →
imagen → QA → autorización humana de publicación
```

Este motor vive en `candidato`, **antes** del gate. Por eso lo que produce es una **ficha de
investigación** y no un prompt de producción: sale con `ejecutable: false`, y el prompt de
animación se guarda como `propuesta_de_prompt_NO_EJECUTABLE`. Un prompt con aspecto de listo,
junto a un gate cerrado, es una invitación a saltárselo.

## 8. Procedencia de las fórmulas

Las fórmulas visual, de animación (`HOOK → MICRO_EVENT → TENSION → REVEAL → RESOLUTION`) y de
copy provienen del documento del fundador **«LegalMente — Fórmula maestra de animación y copy
para imágenes»** (Drive `1a9aO9hOeFzPbYjJAglPEeqBnvJXtdv6DpG53YwdV6BA`). Están implementadas,
no reinventadas. Las familias visuales se leen de `visual/policy/visual-families-v1.json`.

## 9. Lo que sigue pendiente de humano

Buscar fuentes oficiales por jurisdicción para los candidatos; decidir sobre las cuatro piezas
mono-país declaradas panhispánicas; registrar `curia.europa.eu`. Nada de eso lo puede hacer
este motor.
