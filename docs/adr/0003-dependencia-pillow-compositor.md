# ADR 0003 — Pillow como única dependencia, para el compositor determinista

**Estado: APROBADO (2026-08-31).** Decisión técnica reversible, tomada bajo la
autorización expresa del mandato V4 §20.

## Contexto

`TypographyPlan` y `BrandCompositionPlan` existían como contratos, pero el
rasterizado estaba declarado `CONTRACT_ONLY`: el repositorio no tenía ninguna
librería de imagen. Eso dejaba el eslabón más importante de la cadena visual —
el que pone el **texto jurídico exacto** y la **marca** — fuera del sistema, y por
tanto en manos de un paso manual.

## Decisión

Añadir **Pillow** (`Pillow>=10,<14`) como única dependencia del repositorio, usada
exclusivamente por `visual/compositor.py`.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Rasterizador propio en Python puro | Sin FreeType habría que embeber una fuente bitmap y escribir el motor de glifos. Mucho código frágil para peor resultado. |
| Delegar el texto al generador de imagen | Prohibido por el ADR 0002 y por la política vigente. |
| Delegar la composición a Canva | Convertiría a un proveedor en fuente de verdad. El mandato lo prohibe explícitamente (§41): Canva puede ser destino de exportación, nunca origen. |
| Dejarlo `CONTRACT_ONLY` | Deja el trabajo repetitivo en manos del fundador, que es justo lo que el sistema debe eliminar. |

## Por qué Pillow cumple los criterios de §20

- **Impacto bajo**: una dependencia, sin dependencias transitivas propias, aislada
  en un solo módulo. Todo lo demás del repo sigue siendo stdlib-only.
- **Licencia aceptable**: MIT-CMU, permisiva.
- **Sin conflicto arquitectónico**: vive detrás del compositor. El dominio
  (gates, policy, brief, memoria, compilador, receipts, registry) no la importa.
- **Determinismo**: verificado — la misma entrada produce el mismo `sha256`.

## Determinismo y fuentes

El compositor resuelve la fuente en orden explícito (DejaVu del sistema y, si no
está, la que Pillow trae) y **registra en el receipt cuál usó**. Las pruebas
comprueban **invariantes** (dimensiones, área segura, hash del compuesto distinto
del bruto, texto exacto intacto), **no capturas de píxeles**: la rasterización
varía entre plataformas y versiones de fuente, y un golden frágil produciría
fallos falsos.

## Consecuencias

- CI necesita instalar dependencias antes de las pruebas visuales. Ya añadido.
- Las suites jurídicas siguen corriendo sin instalar nada.
- Si un día conviene quitar Pillow, el punto de corte es un solo archivo.
