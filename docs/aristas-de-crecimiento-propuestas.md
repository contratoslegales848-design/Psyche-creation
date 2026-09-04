# Aristas de crecimiento — propuesta, no ejecución

El fundador pidió que este repositorio actúe como sus "ojos" sobre ángulos
creativos y de investigación que él no puede ver todo a la vez, con
autorización pre-concedida siempre que haya **certeza probable de éxito**.

Este documento existe porque esa condición corta en los dos sentidos: para
la mayoría de lo de abajo, la certeza depende de una decisión o un dato que
solo el fundador tiene (estrategia de Drive, presupuesto, a qué se compromete
la marca). Construir sin eso no sería ejecutar con certeza — sería adivinar,
y esta sesión ya revirtió dos veces trabajo construido sobre una suposición
de alcance. Por eso esto es una lista priorizada para decisión, no código.

Las tres primeras filas SÍ tienen certeza suficiente para ejecutarse sin
más autorización que la que ya diste — están marcadas y son las siguientes
en la cola si no me rediriges.

## Alta certeza — ejecutables ya, sin más decisión del fundador

| # | Arista | Por qué hay certeza | Costo |
|---|---|---|---|
| 1 | Extender `rendimiento.py` (ya construido) a `content/linkedin/`: darle a cada pilar/tema de LinkedIn un campo `_rendimiento_documentado` con `SIN_DATO_HISTORICO` explícito (LinkedIn no tiene historial propio todavía) | Mismo patrón ya probado, mismo archivo fuente, cero riesgo de falsa universalización porque el alcance ya se declara honesto | bajo |
| 2 | Auditoría de la misma clase (campo cableado pero nunca poblado) sobre `visual/rotation.py`, `visual/memory.py`, `visual/route_engine.py` — no auditados todavía | Mismo método que ya encontró 2 defectos reales (`negative_space`, `acento_frio_objeto`) | bajo |
| 3 | Un script de "brecha de investigación": recorre `content/claim-packets/*.json` y lista, por claim, qué fuente sigue en `texto_exacto_consultado: false` — hoy eso se revisa a mano leyendo cada JSON | Es solo agregación de datos que ya existen en el repo, no genera afirmación jurídica nueva | bajo |

## Certeza condicionada — necesitan una decisión tuya primero

| # | Arista | Qué decisión falta | Por qué no adivino |
|---|---|---|---|
| 4 | Medición de rendimiento real para LinkedIn (no Facebook) | Acceso de solo lectura a analíticas de LinkedIn, o que tú pegues cifras reales de los primeros posts | Sin datos propios de esa superficie, cualquier ranking sería inventado — exactamente lo que `rendimiento.py` evita hacer con Facebook |
| 5 | Banco de variantes de copy A/B para un mismo claim ya aprobado | Que definas qué cuenta como "éxito" medible (guardados, compartidos, tiempo de lectura) y con qué volumen mínimo interpretas la señal | Sin criterio de éxito explícito, "A/B" degenera en producir contenido sin control — el mismo riesgo que ya identificó el "red-team de la cadena editorial" (`docs/red-team-cadena-editorial.md`) |
| 6 | Adaptar temas ya investigados (los que superan Capa A) a un segundo formato editorial (p.ej. un concepto ya investigado, además de pieza estática, como hilo de 3 piezas) | Si el fundador quiere multiplicar volumen de piezas por tema en vez de cobertura de temas nuevos — es una decisión editorial, no técnica | El propio §6 de CLAUDE.md limita producir bancos grandes mientras el piloto no esté medido; esto necesita ese permiso explícito |
| 7 | Investigación asistida más profunda: usar WebSearch para pre-poblar más rápido el `nivel_de_verificacion` de un claim antes de escalar a WebFetch/PDF | Confirmar que el fundador quiere que el modelo dedique tiempo de investigación proactiva a temas que aún no pidió, en vez de solo el que está en curso | Riesgo de producir investigación que nadie pidió y que compite por atención con lo que sí se pidió — mejor confirmarlo por lote, no en general |

## Descartadas explícitamente (no proponer de nuevo sin instrucción nueva)

- Higgsfield como proveedor de imagen — prohibición expresa del fundador.
- Cualquier cola de aprobación paralela a la cadena canónica ya existente.
- Publicación automática en cualquier plataforma — CLAUDE.md §6.
- Nueva superficie de negocio (web, app, asesorías) sin que el fundador la
  pida por su nombre — ya se contempló y se retiró una vez
  (`docs/superficies-y-crecimiento.md`, revertido).

## Cómo usar este documento

No es un plan cerrado. Es el mapa de lo que veo desde el código que tú no
tienes por qué revisar línea a línea. Dime qué filas de la tabla 2 quieres
desbloquear (con la decisión que piden) y sigo con las 3 de la tabla 1 mientras
tanto si no me dices lo contrario.
