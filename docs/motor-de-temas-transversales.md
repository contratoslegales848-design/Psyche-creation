# Motor de temas transversales — cómo se hace cumplir la dirección

**Qué es esto.** La implementación de la decisión registrada en
[`docs/direccion-basico-antes-que-complejo.md`](direccion-basico-antes-que-complejo.md), que es
el canon y manda sobre este archivo. Aquí solo se describe el mecanismo.

**Procedencia del mecanismo:** orden del fundador de 2026-09-03 — «ya no está generando temas
legales y me genera de países en específico; por ahora no, vamos con lo general pero lo legal,
que es muy abierto».
**Implementación:** `content/topics/` · **Estado:** vigente

## 1. El problema, medido

No es una impresión. Sobre los claim packets que hay hoy en el repositorio, ejecutando
`content/topics/transversality.py` contra el registro oficial:

| Alcance sostenible por sus fuentes | Claims |
|---|---:|
| `CAPA_A_TRANSVERSAL` (3 jurisdicciones con fuente propia) | **2** |
| `CAPA_C_NACIONAL` (una sola jurisdicción) | **9** |
| `NO_DETERMINADO` (ninguna fuente cubre nada) | **2** |

Once de trece claims no pueden sostener nada panhispánico. Y cuatro de ellos —`LM-EVG-002`,
`LM-EVG-003`, `LM-CORP-002`, `LM-CORP-004`— se habían **declarado** panhispánicos aportando
fuentes de un solo país. Eso no es un tema mal elegido: es falsa universalización.

En el Bloque 1 de imágenes ocurrió lo mismo por otra vía. Las cuatro piezas en formato
**Listado** (`LM-B1-01` a `LM-B1-04`) fueron todas las que quedaron con territorio variable.
Enumerar obliga a nombrar elementos concretos, y los elementos concretos son justo lo que
cambia de país a país.

## 2. La regla

**Un tema entra al catálogo solo si la distinción existe en toda la tradición jurídica
hispanohablante aunque cambien el nombre, el plazo, el porcentaje y la formalidad.**

La prueba práctica: quita del tema todos los números, nombres de leyes y autoridades. Si lo
que queda sigue siendo un tema, es transversal. Si se queda vacío, no lo es.

Lo que varía y por tanto **no puede ser el tema**: plazos, montos, nombres de figuras,
autoridades competentes, requisitos formales, catálogos de cláusulas, baremos.

Lo que no varía y por tanto **sí puede serlo**: propiedad frente a posesión frente a tenencia;
nulidad frente a anulabilidad; dolo frente a culpa frente a caso fortuito; carga de la prueba;
forma para existir frente a forma para probar; obligación de medios frente a obligación de
resultado; accesoriedad de la garantía; buena fe subjetiva frente a objetiva.

## 3. Un tema no es una afirmación

Esta es la distinción que permite generar contenido sin fuentes y sin mentir.

- Un **tema** es una pregunta o una distinción que merece explicarse. No dice qué dice el
  derecho. Puede escribirse hoy, sin fuente, sin riesgo.
- Un **claim** es una afirmación sobre qué dice el derecho. No puede escribirse sin fuente
  oficial leída literalmente.

El catálogo `content/topics/catalogo-transversal-v1.json` contiene temas, nunca claims. Por eso
existe estando `WebFetch` bloqueado. Y por eso cada tema sale del motor con
`estado: REQUIERE_INVESTIGACION`, `gate_arte: CERRADO` y `publicacion: NOT_PUBLISHED`, sin
excepción y con prueba que lo impide.

Pasar la barrera significa una sola cosa: **que merece la pena buscarle fuentes**. Nada más.

## 4. Orden de materias

Primero el núcleo civil compartido —derechos reales, obligaciones, contratos, prueba,
responsabilidad—, porque es donde la Capa A es más ancha y el riesgo de deriva más bajo.
Después lo que se ramifica antes: laboral, consumo, datos personales. Lo procesal y lo
sancionador, al final, y normalmente ya como Capa C con el país visible desde el título.

Dentro de cada materia, el orden por formato editorial va de lo seguro a lo frágil:
**DIFERENCIAS** → **MITO** → **CONSECUENCIA** → **LISTADO**. Un Listado no se admite sin haber
comprobado antes que *todos* sus elementos existen en las tres jurisdicciones mínimas.

## 5. Protocolo para cualquier agente antes de contribuir

1. Leer `CLAUDE.md` y este documento.
2. Ejecutar `python3 content/topics/transversality.py` y ver qué pasa y qué no.
3. Proponer temas, no afirmaciones. Un tema que necesita un número para existir no es un tema.
4. No rellenar el copy. Los huecos del brief están vacíos a propósito.
5. No abrir gates, no marcar aprobaciones, no inventar fuentes ni vigencia.
6. Si el tema no pasa la barrera, reclasificarlo a Capa C con el país visible desde el título
   — que es una salida legítima— en vez de forzarlo a parecer transversal.

## 6. Lo que este documento no decide

El **orden de publicación**, la **selección del siguiente lote** y la **aprobación** de
cualquier pieza siguen siendo del fundador. Este documento fija qué puede proponerse; no
autoriza producir ni publicar nada.
