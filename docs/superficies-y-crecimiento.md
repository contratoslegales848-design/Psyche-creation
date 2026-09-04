# Superficies de LegalMente — qué existe, qué falta y en qué orden

**Fecha:** 2026-09-04 · **Estado:** mapa de trabajo, no canon. La dirección de contenido sigue
siendo [`direccion-basico-antes-que-complejo.md`](direccion-basico-antes-que-complejo.md).

Este documento existe porque el fundador pidió contemplar «la página web, aplicación, asesorías
y muchas cosas más». Contemplarlas no es construirlas: es dejar por escrito qué se apoya en qué,
para que ninguna se construya dos veces ni por delante de lo que necesita.

## 1. Lo que hay hoy, verificado

| Superficie | Estado | Evidencia |
|---|---|---|
| Motor de verificación jurídica | **funciona** | 270 pruebas |
| Pipeline visual + route engine | **funciona** | 369 pruebas |
| Motor de candidatos temáticos | **funciona** | 48 pruebas |
| Cola de aprobación en lote | **nuevo** | 17 pruebas |
| Superficie profesional (LinkedIn) | **nuevo** | 19 pruebas |
| Proveedor de imagen real (Higgsfield) | **cableado, sin presupuesto** | 14 pruebas |
| Web pública (`legalmente-web`) | existe, otra cuenta | 8 módulos, 3.051 líneas |
| Aplicación | **no existe** | — |
| Asesorías | **no existe** | — |

**Contenido real aprobado: una pieza.** El motor está muy por delante del material. Esa
desproporción es el hecho central que ordena todo lo demás.

## 2. El cuello de botella real, y qué se hizo con él

No es la tecnología. Es que **una sola persona tiene que aprobar todo**, y mientras aprueba, nada
avanza.

La solución **no** es quitar la aprobación —un sistema de educación jurídica que se auto-aprueba
deja de valer para lo único que sirve— sino separar dos cosas que estaban pegadas:

- **Preparar:** todo lo que no requiere juicio humano. Lo hace el agente, hasta el último
  milímetro. Puede llevar un lote del 0 % al 99 % sin preguntar nada.
- **Decidir:** el juicio humano. Sigue siendo indispensable, pero deja de ser veinte decisiones
  dispersas para ser **una** sobre un lote revisable.

`approval/cola.py` implementa eso. Aprobar diez piezas cuesta una decisión, no diez. Y sigue
siendo una decisión informada, no un cheque en blanco: cada ítem viaja con el hash de su
contenido exacto, y **si el texto cambia después, la decisión deja de valer para ese ítem**.

Dos reglas que no se negocian y están probadas: no existe ninguna función que apruebe, y el
silencio **caduca** la solicitud en vez de convertirla en un sí.

## 3. Motor de imagen — cableado, y bloqueado por presupuesto

`visual/providers/higgsfield.py`. Catálogo verificado contra la API en vivo el 2026-09-03, no
de memoria: `nano_banana_pro`, `gpt_image_2`, `nano_banana`, `soul_2`.

**Bloqueo real y comprobado:** `balance` devuelve `{"credits": 0, "plan": "free"}` y
`unlim.available: false`. **Hoy no se puede generar ninguna imagen.** No es un fallo de código:
la petición sale formada y validada; falta presupuesto.

El modelo por defecto es `nano_banana_pro` por una razón concreta: es el único del catálogo
verificado que declara a la vez renderizado fiable de texto y 9:16. LegalMente monta texto
jurídico exacto sobre la imagen, y un modelo que deforma letras no sirve por muy bueno que sea
el fondo.

Freno que no depende del dinero: **el proveedor se niega a generar si el gate de arte no está
`ABIERTO`**, aunque haya créditos y despachador. Tener presupuesto no es una autorización.

## 4. Orden recomendado para lo que falta

El criterio no es cuál suena mejor, sino **qué se apoya en qué**.

**Primero — contenido verificado.** Todo lo demás lo consume. Una app sin contenido es una
carcasa; una asesoría sin material verificado es un riesgo. `WebSearch` funciona y `WebFetch`
no: se puede localizar y citar, no leer el texto literal. Depositar los PDF oficiales en Drive
sigue siendo el desbloqueo más barato del sistema entero.

**Segundo — la web pública.** Ya existe y es la superficie con menor coste marginal: consume el
canon sin poder alterarlo. Antes de tocarla hay que propagarle `NO_DETERMINADO` (ver §5).

**Tercero — la superficie profesional.** Ya tiene motor. Necesita material propio, no traducido
del público: si solo cambia el vocabulario, no hace falta.

**Cuarto — asesorías.** Es la primera superficie que toca personas concretas y datos reales, y
por eso la que más gobernanza necesita antes de existir: consentimiento, retención, límite entre
información y asesoría jurídica individual. **No debe construirse antes que el control de
confidencialidad**, que hoy existe en `surfaces/linkedin.py` pero solo para texto propio.

**Quinto — aplicación.** Es la más cara y la que menos aporta hasta que haya volumen. Una app
sin contenido no es un producto.

## 5. Deudas conocidas que bloquean lo siguiente

| Deuda | Bloquea | Quién puede resolverla |
|---|---|---|
| `WebFetch` bloqueado | que cualquier claim alcance Nivel 1 | depositar PDF en Drive, o levantar el bloqueo |
| Higgsfield sin créditos | generar imágenes | decisión de presupuesto |
| `NO_DETERMINADO` ausente en `knowledge-pilot` | la web puede tratar «no sabemos» como «no aplica» | patch entregable; otra cuenta, sin push |
| `curia.europa.eu` sin registrar | techo del TJUE | añadir entrada al registro |
| Cuatro piezas mono-país declaradas panhispánicas | el lote de diez | decisión editorial |

## 6. Lo que este documento no decide

El orden de publicación, el presupuesto, la contratación y la aprobación de cualquier pieza
siguen siendo del fundador. Aquí solo se dice qué depende de qué.
