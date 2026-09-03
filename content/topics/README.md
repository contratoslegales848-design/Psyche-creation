# Motor de temas transversales

Genera **temas**, no afirmaciones. Un tema es una pregunta o una distinción; no dice qué dice
el derecho, y por eso puede existir sin fuentes. Un claim sí las necesita, y este motor nunca
produce uno.

Dirección de contenido: [`docs/direccion-basico-antes-que-complejo.md`](../../docs/direccion-basico-antes-que-complejo.md).

## Qué hay aquí

| Archivo | Qué es |
|---|---|
| `catalogo-transversal-v1.json` | 24 temas Capa A: 12 `DIFERENCIAS`, 6 `MITO`, 6 `CONSECUENCIA` |
| `transversality.py` | La barrera: filtro de texto **y** cobertura real por fuentes |
| `brief.py` | Tema → brief de producción: imagen, animación y huecos de copy |
| `test_topics.py` | 31 pruebas |

## Uso

```bash
python3 content/topics/transversality.py          # qué pasa la barrera y qué no
python3 content/topics/brief.py                   # los 24 briefs, resumidos
python3 content/topics/brief.py --tema LM-T-001 --json
cd content/topics && python3 -m unittest test_topics
```

## La barrera tiene dos mitades, y hace falta que sean dos

**Texto.** Rechaza el tema que nombra un país, una ley nacional, una autoridad nacional, una
moneda, un plazo o un porcentaje. Comparación por palabra completa y sin tildes, para que
`perutenencia` no dispare nada y `MÉXICO` no se escape.

**Cobertura.** El filtro de texto solo caza el caso evidente. El peligroso es el contrario: una
pieza que no nombra ningún país, se declara panhispánica y se apoya en fuentes de uno solo.
Sobre los diez claim packets del repositorio, el filtro de texto detecta cuatro; la cobertura
detecta los nueve. Por eso los países se cuentan resolviendo cada fuente contra el registro
oficial, nunca leyendo la prosa.

Una fuente supranacional aporta contexto y **no** suma jurisdicción nacional. Si sumara, un
solo tratado convertiría en transversal cualquier afirmación.

## Lo que un brief no es

Un brief tiene aspecto de estar listo y no lo está. Todos salen con `gate_arte: CERRADO`,
`estado_juridico: REQUIERE_INVESTIGACION`, `revision_humana: PENDIENTE` y
`publicacion: NOT_PUBLISHED`, y hay pruebas que lo impiden cambiar.

El copy se entrega **vacío**. Solo viene escrito el cierre jurisdiccional, porque no afirma
nada: advierte. Rellenar los huecos sin fuente sería una afirmación sin respaldo disfrazada de
plantilla.

## Procedencia de las fórmulas

Las fórmulas visual, de animación (`HOOK → MICRO_EVENT → TENSION → REVEAL → RESOLUTION`) y de
copy provienen del documento del fundador **«LegalMente — Fórmula maestra de animación y copy
para imágenes»** (Drive `1a9aO9hOeFzPbYjJAglPEeqBnvJXtdv6DpG53YwdV6BA`). Aquí están
implementadas, no reinventadas: si el documento cambia, este módulo queda desactualizado y se
corrige contra él, no al revés.

Las familias visuales se leen de `visual/policy/visual-families-v1.json`: no se duplican aquí,
para que añadir o retirar una familia no exija tocar este módulo.
