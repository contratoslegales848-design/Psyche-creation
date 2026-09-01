# Dirección de contenido: lo básico antes que lo complejo

Registra una decisión expresa del fundador (mandato de voz, 2026-09-01), transcrita y
organizada aquí para que cualquier sesión de Claude Code — y cualquier agente futuro —
la lea antes de proponer o producir contenido. No sustituye al Drive como fuente de
verdad de estrategia (CLAUDE.md §2); es la versión operativa mientras se traslada allá.

**Pendiente explícito:** este documento debe reflejarse también en Drive. No se ha
hecho todavía — el fundador pidió "repo ahora, Drive después" — y sigue vigente la
regla de CLAUDE.md §6: no se modifica Drive sin autorización explícita para esa acción
concreta cuando llegue el momento.

## 1. Principio rector

El motor de LegalMente (route engine + fórmula visual + verificación jurídica) ya
funciona. Lo que falta no es más ingeniería del motor: es **materia prima** —
contenido básico, sólido, investigado, que alimente ese motor.

Hay dos capas de contenido jurídico, y el orden de producción importa:

1. **Lo básico transversal** (≈ Capa A del sistema de neutralidad jurisdiccional,
   CLAUDE.md §4): definiciones y conceptos que son esencialmente los mismos en
   cualquier jurisdicción panhispánica porque nacen de la misma lógica jurídica —
   qué es un hecho ilícito penal, qué es la patria potestad, qué es un contrato,
   qué es una prescripción. Estos son los cimientos: producirlos primero.
2. **Lo que se ramifica** (≈ Capas B y C): multas, plazos, procedimientos,
   cuantías, tribunales — todo lo que varía por país o requiere una cifra/artículo
   verificable. Esto se alimenta después, con más tiempo, y siempre con
   verificación jurídica caso por caso (nunca se salta la skill
   `legalmente-legal-verification`).

Enfoque actual: agotar lo básico universal en las materias con más vacío antes de
profundizar en ramificaciones nacionales de una sola materia.

## 2. Estado real verificado (no una suposición)

Verificado en el código y el contenido de este repositorio al momento de escribir
este documento:

- **Contenido real producido: una sola pieza** (`content/pieza-01-reales.json`,
  civil / derechos_reales / propiedad_y_posesión). Todo lo demás en `content/` es
  un ejemplo de plantilla (`ejemplo.json`), no una pieza real.
- **Materias mapeadas en el motor de rutas** (`visual/route_engine.py`,
  `VOCABULARIO_POR_MATERIA`): solo tres — `penal`, `civil`, `laboral`. No existe
  todavía `familia`, `sucesiones`, `inmobiliario`, `digital_y_datos` ni un módulo
  propio de `contratos`.
- La fórmula visual (`legalmente-visual-system`, sección 1) ya había identificado
  los mismos vacíos de forma independiente, por rendimiento real de la página:
  **laboral, familia y sucesiones, inmobiliario, digital y datos**. Coincide con
  lo que describe el fundador (dudas básicas muy frecuentes en materia laboral).

Diagnóstico: el "corazón" (motor) está listo; el cuerpo (contenido básico
transversal en las materias de mayor vacío) está casi vacío. Prioridad inmediata:
llenarlo, no seguir construyendo mecanismo.

## 3. Prioridad de materias para lo básico

En este orden, salvo instrucción expresa en contrario del fundador:

1. **Laboral** — mayor volumen de dudas básicas de la audiencia, muchas de las
   cuales ni siquiera nacen estrictamente del derecho pero se explican con él
   (p. ej. qué es una relación laboral, qué distingue un despido de una renuncia).
2. **Familia y sucesiones**
3. **Inmobiliario**
4. **Digital y datos**
5. **Contractual** (civil → contratos) — ver sección 4, tiene reglas propias.

Cada materia nueva necesita, como mínimo: entrada en `VOCABULARIO_POR_MATERIA`
(o `VOCABULARIO_POR_SUBMATERIA` si hace falta una anulación más específica, como
ya ocurrió con civil/derechos_reales en el fix de vocabulario de CAUSA), y piezas
de contenido reales verificadas con la skill `legalmente-legal-verification`
antes de cualquier producción visual — nunca al revés.

## 4. Módulo contractual (nace de civil, con lógica propia)

El fundador quiere abrir, además del feed general, un canal más profesional/
contractual (pensado para LinkedIn). La lógica de contenido para contratos:

- Los contratos comparten una naturaleza básica transversal: **validez** (los
  requisitos que hacen que un contrato exista y obligue) y **redacción sin
  parámetros abiertos** — objeto y alcance definidos, qué se promete, qué se
  entrega, qué se recibe, término, y las cláusulas que suelen quedar vagas.
- El análisis contractual empieza por **fecha y objeto**: eso ya da la mayor
  parte del contexto necesario (naturaleza del contrato, materia aplicable,
  riesgos típicos de esa figura).
- Esto es contenido básico transversal igual que el resto (Capa A): los
  requisitos de validez de un contrato no cambian sustancialmente entre
  jurisdicciones panhispánicas por la misma razón que las definiciones civiles
  no cambian — nace de la misma lógica jurídica. Lo que sí es Capa B/C es la
  forma exacta en que cada país regula un tipo de contrato específico
  (arrendamiento, compraventa, etc.) — eso se ramifica después.
- Técnicamente: probablemente amerite una materia propia `contratos` (o una
  submateria de `civil`) en el motor de rutas, con su propio vocabulario de
  navegación — no existe todavía. Queda como trabajo futuro, no ejecutado en
  este documento.

## 5. Todo vinculado — nunca contenido aislado

El fundador insiste: LegalMente no funciona analizando cada pieza de forma
aislada, sino vinculando todo. Esto ya es, en esencia, lo que hace el motor de
rutas (`route_engine.py` + `route_sync.py`): cada pieza de contenido nace de un
`content_id` real, avanza por nodos conectados (`CAUSA → CONSECUENCIA →
RESPONSABILIDAD → PRUEBA → ...`), y cada nodo hereda materia/submateria/concepto
del mismo origen. La instrucción del fundador confirma que este diseño es
correcto y debe mantenerse: **ninguna pieza nueva debería crearse fuera de una
ruta**, y toda materia nueva que se agregue debe integrarse al grafo de
categorías existente (`GRAFO_CATEGORIAS`), no vivir aparte.

Igualmente aplica a la calidad ejecutiva del contenido: precisión sin excederse
en extensión, siempre con fuente verificable — nunca "amplio" a costa de exactitud.

## 6. Protocolo para cualquier agente que entre a contribuir

Instrucción expresa del fundador, para registrar como regla operativa:

1. **Estudiar primero.** Cualquier agente (Claude Code u otro) que entre a
   trabajar en LegalMente debe leer primero este documento, `CLAUDE.md`, y el
   estado real del contenido y el motor (no asumir nada por lo que diga Drive
   sin verificarlo en el código, tal como ya exige CLAUDE.md §2) antes de
   proponer o producir nada.
2. **Contribuir con criterio, no con dogma.** Un agente puede argumentar con
   información, corregir información existente, o proponer ideas nuevas. No hay
   que "cegarse en interpretaciones": toda idea razonada es bienvenida para
   evaluación, incluida una que cuestione algo ya hecho.
3. **Toda contribución queda registrada como constancia** de quién la propuso y
   cuándo — en un PR, un commit, o un documento como este, nunca solo en una
   conversación que se pierde.
4. **Evaluación y filtro humano.** Las contribuciones se analizan para decidir
   si son ejecutables. Las que sí, se ejecutan (con la misma disciplina de este
   repositorio: rama aislada, pruebas, PR, aprobación humana antes de fusionar).
   Las que no son viables, se retiran — sin que eso invalide el ejercicio de
   haberlas propuesto.
5. Esta misma lógica de "proponer → registrar → evaluar → ejecutar o retirar"
   aplica a todo el proyecto, no solo al contenido: código, arquitectura,
   estrategia de publicación.

## 7. Qué NO cambia con este documento

- Ninguna afirmación jurídica se da por verificada aquí. Este documento es
  dirección editorial y de producto, no un claim jurídico.
- No se abre ningún gate de arte ni de publicación.
- No se modifica Drive todavía (ver nota de "Pendiente explícito" arriba).
- No se ejecuta todavía la limpieza de contenido "que ya no es LegalMente" en
  Drive — el fundador indicó explícitamente que eso queda para más adelante.
- No se crea contenido nuevo de ninguna materia en este documento — es
  dirección, no producción.

## 8. Siguiente paso ejecutable

Cuando el fundador lo indique: elegir una materia de la lista de la sección 3
(recomendado: laboral, por ser la de mayor vacío confirmado en dos fuentes
independientes) y producir la primera pieza real siguiendo el ciclo completo ya
existente en el motor — investigación y verificación con
`legalmente-legal-verification` primero, producción visual después, nunca al
revés.
