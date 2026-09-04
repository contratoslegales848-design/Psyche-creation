# Cimientos de las superficies: web, aplicación, juegos

El fundador pidió ver los cimientos de la página web, la aplicación móvil y los
juegos. Este documento no propone productos: describe **sobre qué se apoyarían**,
qué de eso ya existe hoy, y cuál es la única regla que ninguna superficie puede
saltarse. Escrito el 2026-09-04 contra el estado real del repositorio y de los
conectores, no contra lo que se dijo en Drive.

---

## 1. El cimiento es uno solo, y ya está construido

No es la web, ni la app, ni el juego. Es esta cadena:

```
pregunta → candidato → investigación → fuente y territorio → claim →
validación técnica → revisión humana → GATE DE ARTE →
narrativa → imagen → QA → autorización humana de publicación
```

Cada superficie nueva es **una salida más** colgando del mismo tronco. Un juego
que enseña la diferencia entre posesión y propiedad está haciendo una afirmación
jurídica exactamente igual que un post; una app que responde "esto prescribe a
los X años" está afirmando derecho positivo de un país. Si una superficie puede
emitir una afirmación sin pasar por el gate, el gate deja de existir para todas.

**Regla de cimiento, no negociable:** ninguna superficie genera texto jurídico
propio. Toda superficie **consume** claims ya verificados y aprobados. La web, la
app y el juego son *lectores* del mismo almacén, nunca autores.

Esto ya tiene forma ejecutable: `contract/canonical_envelope.py` (Canonical
Envelope v1, 27 pruebas). Es el sobre que transporta una pieza aprobada hacia
fuera de este repositorio. **Está construido y nunca se ha usado**: ninguna
superficie lo consume todavía (auditado hoy — solo lo referencia el inventario de
`ecosystem/registry.py`, nadie lo instancia). Ese, y no otro, es el trabajo de
cimentación pendiente.

---

## 2. Qué existe hoy de verdad (verificado, no supuesto)

| Pieza | Estado real | Comprobado |
|---|---|---|
| Contrato canónico de salida | Implementado, **sin ningún consumidor** | `grep "CanonicalEnvelope("` → solo sus propias pruebas |
| `legalmente-web` (Next.js) | Repo **público**, cuenta `legallmente-alt` (otra cuenta) | `CLAUDE.md §8`; clonado anónimo verificado el 2026-08-31 |
| Consumidor web del contrato | Escrito y probado en local (23 pruebas), **entregado como patches, sin empujar** | `docs/legalmente-web-integration-pack.md`, `ecosystem/registry.py` |
| Base de datos | **Ya existe un proyecto Supabase** de la cuenta `legallmente-alt`, creado el 2026-08-27, Postgres 17, región `ca-central-1` | `list_projects` hoy: `ACTIVE_HEALTHY`, pero **hibernado por desuso** al consultarlo |
| Inventario materializado | Funcionando, regenerable (`scripts/inventory.py`) | rescatado del PR #16 hoy |
| Claim packets reales | 11, **todos con gate cerrado** | validados en CI desde hoy |
| Motor visual | 4 formatos, 8 familias, proveedor real conectable | `cli.py providers` |
| Aplicación móvil | **No existe nada.** Ni repo, ni esqueleto, ni decisión de stack | — |
| Juegos | **No existe nada.** Ni prototipo ni diseño | — |

El dato que probablemente sorprenda: **ya hay una base de datos pagada/activa
desde hace una semana que nadie ha usado**. Está hibernada porque nunca recibió
una consulta. No he creado nada en ella ni la he despertado: es de otra cuenta y
`CLAUDE.md §8` exige decisión expresa del fundador para cruzar esa frontera.

---

## 3. Los tres cimientos que faltan, en orden

Están en este orden porque cada uno depende del anterior. Saltarse el orden es lo
que produce una app bonita que publica derecho sin verificar.

### Cimiento 1 — El almacén de piezas aprobadas (bloquea a todo lo demás)

Hoy una pieza aprobada vive en un JSON dentro de este repositorio. Eso sirve para
producir; no sirve para que tres superficies la lean a la vez.

Lo que falta: una tabla de piezas publicables con el Canonical Envelope como
esquema, y una regla de escritura: **solo entra lo que ya pasó el gate**. La base
de datos ya existe (arriba). El contrato ya existe. Falta unirlos.

Riesgo real si se hace mal: si la tabla admite escritura desde cualquier sitio,
se convierte en la vía para publicar sin gate. La escritura tiene que ser
derivada de los claim packets, nunca manual.

### Cimiento 2 — La web como primer lector

`legalmente-web` ya es un consumidor estricto escrito y probado; falta empujarlo
(está en otra cuenta, se entrega por patches). Ser el primer lector real del
almacén es lo que demuestra que el contrato aguanta antes de que existan tres
superficies dependiendo de él.

Es además la superficie más barata: no necesita tienda de aplicaciones, ni
revisión de Apple, ni instalación.

### Cimiento 3 — App y juegos, sobre el mismo almacén

Solo después de que la web lea del almacén tiene sentido una app. Y el juego es
el caso **más delicado**, no el más ligero:

- Un juego de "¿esto prescribe o no?" con una respuesta correcta está afirmando
  derecho positivo, y la respuesta cambia por país: es Capa C casi siempre.
- Un juego sobre **distinguir figuras** (propiedad / posesión / tenencia) se
  sostiene en Capa A, que es justo donde el catálogo de 24 candidatos ya trabaja.
- Un juego con puntuación crea un incentivo perverso: premiar la respuesta rápida
  sobre la respuesta matizada, cuando "depende de la jurisdicción" suele ser la
  respuesta correcta.

Conclusión de diseño, no de código: **el juego debe puntuar la distinción, nunca
la regla nacional.** Es la misma disciplina de Capa A/B/C, aplicada a mecánica de
juego.

---

## 4. Lo que NO hay que hacer

- No crear una app ni un juego antes del Cimiento 1. Serían superficies
  generando su propio contenido jurídico, que es exactamente lo que el sistema
  entero existe para impedir.
- No dar a la app un modelo de lenguaje que responda dudas legales del usuario.
  Sería asesoría jurídica individual automatizada: prohibido por `CLAUDE.md §4`
  y por el propio `copy.prohibido` de cada brief.
- No duplicar el motor de verificación en otro repositorio. Un segundo motor es
  un segundo criterio, y entonces no hay criterio.
- No escribir en la base de datos de `legallmente-alt` desde este repositorio sin
  una decisión expresa: son cuentas distintas (`CLAUDE.md §8`).

---

## 5. La única decisión que hace falta ahora

Todo lo anterior está bloqueado por una sola pregunta que solo el fundador puede
responder:

> ¿El almacén de piezas aprobadas vive en el Supabase que ya existe de
> `legallmente-alt`, o se crea uno propio para LegalMente?

- **Si es el existente**: hace falta autorización explícita para que sesiones de
  este repositorio escriban ahí, porque cruza la frontera del `§8`.
- **Si es uno nuevo**: hace falta decidir en qué cuenta, y quién paga.

No hay forma de avanzar el Cimiento 1 sin esa respuesta, y sin el Cimiento 1 no
hay web con datos reales, ni app, ni juego. El resto — contrato, consumidor web,
inventario, motor visual, gate — **ya está construido y esperando**.
