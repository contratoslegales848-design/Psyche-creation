# Prueba real de producción — 10 temas nuevos desde el motor editorial (Parte XIII, 16-sep-2026)

PLANES/PROMPTS únicamente. Ningún proveedor de imagen fue invocado — ver `docs/auditoria-inteligencia-tematica-2026-09-16.md` §3 (ningún generador real conectado).

**Origen:** `universe.build_reserve(seed=20260916)` + `generator.seleccionar_lote()` (motor editorial real, no una lista redactada para la ocasión) + señal de mercado real (`market_signal.py`, 30 vacantes de Indeed MX capturadas el 16-sep-2026). 10 candidatos rechazados en el camino por hard gates antes de llegar a estos 10.

**QA de huella visual:** ACEPTADO en 4 intento(s) (10/10 huellas distintas, 6 medios distintos).

**Mezcla editorial por profundidad:** {'base': 3, 'media': 4, 'alta': 3, 'otra': 0} — dentro del rango sugerido.

## 1. CAND-0008 — mercantil / sociedades

1. **Tema:** sociedades — mostrar cómo se repara un daño
2. **Por qué fue seleccionado:** score compuesto 1.0 (novedad semántica 0.91, territorio 1.0, utilidad 1.0; señal de mercado +0.0800).
3. **Origen del candidato:** señal real de mercado (vacantes, market_signal.py) + banco editorial combinatorio
4. **Clasificación (taxonomía):** MERCANTIL — materia 'mercantil' determina la etiqueta.
5. **Nivel (profundidad):** media
6. **Jurisdicción:** panhispánica / conceptual por defecto (Capa A) — sin verificar todavía; la clasificación Capa A/B/C definitiva corresponde a `legalmente-legal-verification` sobre la pieza ya redactada, no a este candidato combinatorio (ver `docs/verificacion-mezcla-citas-jurisdiccion-2026-09-16.md`).
7. **Tensión jurídica:** daño sin restitución
8. **Regla/problema central:** ¿qué falla en la práctica en sociedades cuando alguien necesita reclamar?
9. **Metáfora visual:** una firma que se disuelve en la institucion que ayudo a crear
10. **visual_fingerprint completo:**
    - primary_direction: generative geometry
    - secondary_direction: (ninguna)
    - medium: digital_cgi_y_visualizacion
    - lighting: luz de atardecer neutro
    - palette: neones controlados sobre neutral
    - composition: perspectiva comprimida
    - materiality: hielo
    - camera_optics: 100 mm macro
    - realism: documental
    - visual_mechanism: equilibrio precario
11. **Prompt final:**

    > Una sola escena. una placa de bronce con un nombre a medio borrar junto a un libro de actas abierto. Entorno: archivo corporativo con estantes de expedientes societarios. Camara: 50mm, plano cerrado sobre la placa. Punto focal: el nombre a medio borrar. Familia visual: hiperrealismo editorial cinematografico. Componer nativamente para 1080x1920 completo aprovechando la verticalidad, pero mantener TODO el contenido semánticamente esencial (título, concepto jurídico, objeto o documento focal, metáfora principal, marca cuando corresponda) dentro del área central segura entre los píxeles 366 y 1554 desde arriba (equivalente al recorte 1080x1350, con margen interno conservador). Usar la extensión superior (0-285px) e inferior (1635-1920px) sólo para atmósfera, profundidad y expansión visual no indispensable — nunca para el mensaje jurídico. Direccion artistica: generative geometry. Medio: digital cgi y visualizacion. Composicion: perspectiva comprimida. Optica: 100 mm macro. Materialidad: hielo. Nivel de realismo: documental. Mecanismo visual: equilibrio precario. Metafora visual: una firma que se disuelve en la institucion que ayudo a crear. Luz: luz de atardecer neutro. Intencion de luminosidad: legible, sin empastar los negros. Paleta: neones controlados sobre neutral. El acento de color (neones controlados sobre neutral) debe proceder de un objeto fisico real de la escena: un sello corporativo de metal sin usar. La escena incluye lomo de libro con una superficie de marca reservada y COMPLETAMENTE VACIA (relieve, perspectiva, material y luz correctos para que algo se lea ahi, pero SIN NINGUN CARACTER). La marca se compone despues.

12. **Comprobación temática anti-repetición:** NUEVO — lo más parecido está a distancia 0.91 (umbral 0.25).
13. **Comprobación visual anti-repetición:** ver matriz de distancia al final del documento; huella incluida en el QA de lote (ACEPTADO).
14. **Safe zone 4:5 (tarea 78):** OK — ningún campo esencial declara una zona de riesgo.

## 2. CAND-0034 — mercantil / representacion_organica

1. **Tema:** representacion organica — mostrar a quién toca probar
2. **Por qué fue seleccionado:** score compuesto 1.0 (novedad semántica 0.89, territorio 1.0, utilidad 1.0; señal de mercado +0.0800).
3. **Origen del candidato:** señal real de mercado (vacantes, market_signal.py) + banco editorial combinatorio
4. **Clasificación (taxonomía):** MERCANTIL — materia 'mercantil' determina la etiqueta.
5. **Nivel (profundidad):** alta
6. **Jurisdicción:** panhispánica / conceptual por defecto (Capa A) — sin verificar todavía; la clasificación Capa A/B/C definitiva corresponde a `legalmente-legal-verification` sobre la pieza ya redactada, no a este candidato combinatorio (ver `docs/verificacion-mezcla-citas-jurisdiccion-2026-09-16.md`).
7. **Tensión jurídica:** expectativa invertida
8. **Regla/problema central:** ¿por qué ocurre en representacion organica cuando alguien necesita distinguir?
9. **Metáfora visual:** una linea recta interrumpida por un unico quiebre deliberado
10. **visual_fingerprint completo:**
    - primary_direction: fotografía cenital editorial
    - secondary_direction: (ninguna)
    - medium: fotografia
    - lighting: luz museográfica
    - palette: cobre oxidado y piedra
    - composition: plano general arquitectónico
    - materiality: malla
    - camera_optics: punto de vista bajo
    - realism: diagramático
    - visual_mechanism: transparencia
11. **Prompt final:**

    > Una sola escena. unos estatutos sociales impresos con una sola clausula marcada en rojo. Entorno: sala de juntas vacia tras una asamblea. Camara: 35mm, plano medio sobre el documento. Punto focal: la clausula marcada. Familia visual: hiperrealismo editorial cinematografico. Componer nativamente para 1080x1920 completo aprovechando la verticalidad, pero mantener TODO el contenido semánticamente esencial (título, concepto jurídico, objeto o documento focal, metáfora principal, marca cuando corresponda) dentro del área central segura entre los píxeles 366 y 1554 desde arriba (equivalente al recorte 1080x1350, con margen interno conservador). Usar la extensión superior (0-285px) e inferior (1635-1920px) sólo para atmósfera, profundidad y expansión visual no indispensable — nunca para el mensaje jurídico. Direccion artistica: fotografía cenital editorial. Medio: fotografia. Composicion: plano general arquitectónico. Optica: punto de vista bajo. Materialidad: malla. Nivel de realismo: diagramático. Mecanismo visual: transparencia. Metafora visual: una linea recta interrumpida por un unico quiebre deliberado. Luz: luz museográfica. Intencion de luminosidad: legible, sin empastar los negros. Paleta: cobre oxidado y piedra. El acento de color (cobre oxidado y piedra) debe proceder de un objeto fisico real de la escena: una regla de metal apoyada junto al documento. La escena incluye carpeta con una superficie de marca reservada y COMPLETAMENTE VACIA (relieve, perspectiva, material y luz correctos para que algo se lea ahi, pero SIN NINGUN CARACTER). La marca se compone despues.

12. **Comprobación temática anti-repetición:** NUEVO — lo más parecido está a distancia 0.89 (umbral 0.25).
13. **Comprobación visual anti-repetición:** ver matriz de distancia al final del documento; huella incluida en el QA de lote (ACEPTADO).
14. **Safe zone 4:5 (tarea 78):** OK — ningún campo esencial declara una zona de riesgo.

## 3. CAND-0055 — civil / donacion

1. **Tema:** donacion — recuperar el origen de una palabra
2. **Por qué fue seleccionado:** score compuesto 1.0 (novedad semántica 0.8866, territorio 1.0, utilidad 1.0; señal de mercado +0.0400).
3. **Origen del candidato:** señal real de mercado (vacantes, market_signal.py) + banco editorial combinatorio
4. **Clasificación (taxonomía):** CONTRACTUAL — materia 'civil' determina la etiqueta.
5. **Nivel (profundidad):** base
6. **Jurisdicción:** panhispánica / conceptual por defecto (Capa A) — sin verificar todavía; la clasificación Capa A/B/C definitiva corresponde a `legalmente-legal-verification` sobre la pieza ya redactada, no a este candidato combinatorio (ver `docs/verificacion-mezcla-citas-jurisdiccion-2026-09-16.md`).
7. **Tensión jurídica:** palabra vaciada de sentido
8. **Regla/problema central:** ¿qué es en donacion cuando alguien necesita recordar?
9. **Metáfora visual:** una palabra que atraviesa siglos y llega casi intacta hasta el documento de hoy
10. **visual_fingerprint completo:**
    - primary_direction: Nueva Objetividad
    - secondary_direction: (ninguna)
    - medium: movimientos_y_lenguajes_historicos
    - lighting: luz de hora azul
    - palette: ciruela y gris humo
    - composition: macro abstracto
    - materiality: polvo mineral
    - camera_optics: prisma delante de lente
    - realism: onírico controlado
    - visual_mechanism: estratificación
11. **Prompt final:**

    > Una sola escena. un diccionario etimologico abierto junto a una escritura de donacion manuscrita antigua. Entorno: archivo notarial con luz de ventana lateral. Camara: 50mm, plano cerrado sobre las dos paginas. Punto focal: la raiz de la palabra subrayada a lapiz. Familia visual: hiperrealismo editorial cinematografico. Componer nativamente para 1080x1920 completo aprovechando la verticalidad, pero mantener TODO el contenido semánticamente esencial (título, concepto jurídico, objeto o documento focal, metáfora principal, marca cuando corresponda) dentro del área central segura entre los píxeles 366 y 1554 desde arriba (equivalente al recorte 1080x1350, con margen interno conservador). Usar la extensión superior (0-285px) e inferior (1635-1920px) sólo para atmósfera, profundidad y expansión visual no indispensable — nunca para el mensaje jurídico. Direccion artistica: Nueva Objetividad. Medio: movimientos y lenguajes historicos. Composicion: macro abstracto. Optica: prisma delante de lente. Materialidad: polvo mineral. Nivel de realismo: onírico controlado. Mecanismo visual: estratificación. Metafora visual: una palabra que atraviesa siglos y llega casi intacta hasta el documento de hoy. Luz: luz de hora azul. Intencion de luminosidad: legible, sin empastar los negros. Paleta: ciruela y gris humo. El acento de color (ciruela y gris humo) debe proceder de un objeto fisico real de la escena: una pluma antigua apoyada entre ambos textos. La escena incluye placa de laton con una superficie de marca reservada y COMPLETAMENTE VACIA (relieve, perspectiva, material y luz correctos para que algo se lea ahi, pero SIN NINGUN CARACTER). La marca se compone despues.

12. **Comprobación temática anti-repetición:** NUEVO — lo más parecido está a distancia 0.8866 (umbral 0.25).
13. **Comprobación visual anti-repetición:** ver matriz de distancia al final del documento; huella incluida en el QA de lote (ACEPTADO).
14. **Safe zone 4:5 (tarea 78):** OK — ningún campo esencial declara una zona de riesgo.

## 4. CAND-0119 — laboral / salario

1. **Tema:** salario — estructurar un acuerdo antes del conflicto
2. **Por qué fue seleccionado:** score compuesto 1.0 (novedad semántica 0.9072, territorio 1.0, utilidad 1.0; señal de mercado +0.0400).
3. **Origen del candidato:** señal real de mercado (vacantes, market_signal.py) + banco editorial combinatorio
4. **Clasificación (taxonomía):** LABORAL — materia 'laboral' determina la etiqueta.
5. **Nivel (profundidad):** media
6. **Jurisdicción:** panhispánica / conceptual por defecto (Capa A) — sin verificar todavía; la clasificación Capa A/B/C definitiva corresponde a `legalmente-legal-verification` sobre la pieza ya redactada, no a este candidato combinatorio (ver `docs/verificacion-mezcla-citas-jurisdiccion-2026-09-16.md`).
7. **Tensión jurídica:** posición sin preparación
8. **Regla/problema central:** ¿a quién le pasó en salario cuando alguien necesita acordar?
9. **Metáfora visual:** dos orillas que todavia no han decidido donde poner el puente
10. **visual_fingerprint completo:**
    - primary_direction: litografía científica
    - secondary_direction: (ninguna)
    - medium: dibujo_grabado_y_estampa
    - lighting: luz institucional neutra
    - palette: verde salvia y grafito
    - composition: marco dentro del marco
    - materiality: terracota
    - camera_optics: ortográfico
    - realism: científico
    - visual_mechanism: erosión
11. **Prompt final:**

    > Una sola escena. dos propuestas salariales impresas, una junto a la otra, con un boligrafo sin tapar entre ambas. Entorno: sala de reuniones de recursos humanos antes de una firma. Camara: 35mm, plano cenital sobre las dos hojas. Punto focal: el espacio vacio entre las dos propuestas. Familia visual: hiperrealismo editorial cinematografico. Componer nativamente para 1080x1920 completo aprovechando la verticalidad, pero mantener TODO el contenido semánticamente esencial (título, concepto jurídico, objeto o documento focal, metáfora principal, marca cuando corresponda) dentro del área central segura entre los píxeles 366 y 1554 desde arriba (equivalente al recorte 1080x1350, con margen interno conservador). Usar la extensión superior (0-285px) e inferior (1635-1920px) sólo para atmósfera, profundidad y expansión visual no indispensable — nunca para el mensaje jurídico. Direccion artistica: litografía científica. Medio: dibujo grabado y estampa. Composicion: marco dentro del marco. Optica: ortográfico. Materialidad: terracota. Nivel de realismo: científico. Mecanismo visual: erosión. Metafora visual: dos orillas que todavia no han decidido donde poner el puente. Luz: luz institucional neutra. Intencion de luminosidad: legible, sin empastar los negros. Paleta: verde salvia y grafito. El acento de color (verde salvia y grafito) debe proceder de un objeto fisico real de la escena: una calculadora de bolsillo apagada junto a las hojas. La escena incluye placa de bronce con una superficie de marca reservada y COMPLETAMENTE VACIA (relieve, perspectiva, material y luz correctos para que algo se lea ahi, pero SIN NINGUN CARACTER). La marca se compone despues.

12. **Comprobación temática anti-repetición:** NUEVO — lo más parecido está a distancia 0.9072 (umbral 0.25).
13. **Comprobación visual anti-repetición:** ver matriz de distancia al final del documento; huella incluida en el QA de lote (ACEPTADO).
14. **Safe zone 4:5 (tarea 78):** OK — ningún campo esencial declara una zona de riesgo.

## 5. CAND-0050 — ambiental / principio_precautorio

1. **Tema:** principio precautorio — exponer una tensión estructural
2. **Por qué fue seleccionado:** score compuesto 1.0 (novedad semántica 1.0, territorio 1.0, utilidad 1.0; señal de mercado +0.0000).
3. **Origen del candidato:** banco editorial combinatorio (universe.py)
4. **Clasificación (taxonomía):** REGULATORIO — materia 'ambiental' determina la etiqueta.
5. **Nivel (profundidad):** alta
6. **Jurisdicción:** panhispánica / conceptual por defecto (Capa A) — sin verificar todavía; la clasificación Capa A/B/C definitiva corresponde a `legalmente-legal-verification` sobre la pieza ya redactada, no a este candidato combinatorio (ver `docs/verificacion-mezcla-citas-jurisdiccion-2026-09-16.md`).
7. **Tensión jurídica:** legalidad vs realidad
8. **Regla/problema central:** ¿cómo cambia según el sistema en principio precautorio cuando alguien necesita reflexionar?
9. **Metáfora visual:** decidir el peso de algo que todavia no se ha terminado de medir
10. **visual_fingerprint completo:**
    - primary_direction: fotografía topográfica
    - secondary_direction: (ninguna)
    - medium: fotografia
    - lighting: luz prismática
    - palette: azul ultramar y marfil
    - composition: composición vertical ascendente
    - materiality: textil tejido
    - camera_optics: isométrico
    - realism: conceptual abstracto
    - visual_mechanism: sombra que oculta información
11. **Prompt final:**

    > Una sola escena. una balanza de laboratorio con un platillo cargado y el otro con un espacio marcado pero vacio. Entorno: laboratorio ambiental con instrumental de medicion al fondo. Camara: 50mm, plano medio sobre la balanza. Punto focal: el platillo vacio marcado. Familia visual: hiperrealismo editorial cinematografico. Componer nativamente para 1080x1920 completo aprovechando la verticalidad, pero mantener TODO el contenido semánticamente esencial (título, concepto jurídico, objeto o documento focal, metáfora principal, marca cuando corresponda) dentro del área central segura entre los píxeles 366 y 1554 desde arriba (equivalente al recorte 1080x1350, con margen interno conservador). Usar la extensión superior (0-285px) e inferior (1635-1920px) sólo para atmósfera, profundidad y expansión visual no indispensable — nunca para el mensaje jurídico. Direccion artistica: fotografía topográfica. Medio: fotografia. Composicion: composición vertical ascendente. Optica: isométrico. Materialidad: textil tejido. Nivel de realismo: conceptual abstracto. Mecanismo visual: sombra que oculta información. Metafora visual: decidir el peso de algo que todavia no se ha terminado de medir. Luz: luz prismática. Intencion de luminosidad: legible, sin empastar los negros. Paleta: azul ultramar y marfil. El acento de color (azul ultramar y marfil) debe proceder de un objeto fisico real de la escena: un frasco de muestra sin etiquetar junto a la balanza. La escena incluye vidrio con una superficie de marca reservada y COMPLETAMENTE VACIA (relieve, perspectiva, material y luz correctos para que algo se lea ahi, pero SIN NINGUN CARACTER). La marca se compone despues.

12. **Comprobación temática anti-repetición:** NUEVO — ningún registro reciente es semánticamente equivalente.
13. **Comprobación visual anti-repetición:** ver matriz de distancia al final del documento; huella incluida en el QA de lote (ACEPTADO).
14. **Safe zone 4:5 (tarea 78):** OK — ningún campo esencial declara una zona de riesgo.

## 6. CAND-0076 — ambiental / dano_ambiental

1. **Tema:** dano ambiental — hacer visible un deber
2. **Por qué fue seleccionado:** score compuesto 0.9933 (novedad semántica 0.9778, territorio 1.0, utilidad 1.0; señal de mercado +0.0000).
3. **Origen del candidato:** banco editorial combinatorio (universe.py)
4. **Clasificación (taxonomía):** REGULATORIO — materia 'ambiental' determina la etiqueta.
5. **Nivel (profundidad):** base
6. **Jurisdicción:** panhispánica / conceptual por defecto (Capa A) — sin verificar todavía; la clasificación Capa A/B/C definitiva corresponde a `legalmente-legal-verification` sobre la pieza ya redactada, no a este candidato combinatorio (ver `docs/verificacion-mezcla-citas-jurisdiccion-2026-09-16.md`).
7. **Tensión jurídica:** deber ignorado
8. **Regla/problema central:** ¿cómo se evita en dano ambiental cuando alguien necesita cumplir?
9. **Metáfora visual:** un puente construido desde un solo lado del rio
10. **visual_fingerprint completo:**
    - primary_direction: aberración cromática mínima
    - secondary_direction: pintura arqueológica reconstructiva
    - medium: fotografia_optica_experimental
    - lighting: luz de proyector
    - palette: azul tinta y papel natural
    - composition: composición de archivo abierto
    - materiality: cera
    - camera_optics: 135 mm comprimido
    - realism: realista editorial
    - visual_mechanism: palimpsesto
11. **Prompt final:**

    > Una sola escena. dos sillas frente a frente en una mesa, solo una carpeta abierta del lado izquierdo. Entorno: sala de negociacion con ventanales hacia un terreno en desarrollo. Camara: 35mm, plano medio de la mesa. Punto focal: la carpeta cerrada del lado derecho. Familia visual: hiperrealismo editorial cinematografico. Componer nativamente para 1080x1920 completo aprovechando la verticalidad, pero mantener TODO el contenido semánticamente esencial (título, concepto jurídico, objeto o documento focal, metáfora principal, marca cuando corresponda) dentro del área central segura entre los píxeles 366 y 1554 desde arriba (equivalente al recorte 1080x1350, con margen interno conservador). Usar la extensión superior (0-285px) e inferior (1635-1920px) sólo para atmósfera, profundidad y expansión visual no indispensable — nunca para el mensaje jurídico. Direccion artistica: aberración cromática mínima con acento de pintura arqueológica reconstructiva. Medio: fotografia optica experimental. Composicion: composición de archivo abierto. Optica: 135 mm comprimido. Materialidad: cera. Nivel de realismo: realista editorial. Mecanismo visual: palimpsesto. Metafora visual: un puente construido desde un solo lado del rio. Luz: luz de proyector. Intencion de luminosidad: legible, sin empastar los negros. Paleta: azul tinta y papel natural. El acento de color (azul tinta y papel natural) debe proceder de un objeto fisico real de la escena: una taza de cafe sin tocar del lado de la carpeta cerrada. La escena incluye piedra con una superficie de marca reservada y COMPLETAMENTE VACIA (relieve, perspectiva, material y luz correctos para que algo se lea ahi, pero SIN NINGUN CARACTER). La marca se compone despues.

12. **Comprobación temática anti-repetición:** NUEVO — lo más parecido está a distancia 0.9778 (umbral 0.25).
13. **Comprobación visual anti-repetición:** ver matriz de distancia al final del documento; huella incluida en el QA de lote (ACEPTADO).
14. **Safe zone 4:5 (tarea 78):** OK — ningún campo esencial declara una zona de riesgo.

## 7. CAND-0129 — salud_medico_legal / peritaje_medico

1. **Tema:** peritaje medico — entrar por una obra cultural
2. **Por qué fue seleccionado:** score compuesto 0.9897 (novedad semántica 0.9656, territorio 1.0, utilidad 1.0; señal de mercado +0.0000).
3. **Origen del candidato:** banco editorial combinatorio (universe.py)
4. **Clasificación (taxonomía):** SALUD / RESPONSABILIDAD PROFESIONAL — materia 'salud_medico_legal' determina la etiqueta.
5. **Nivel (profundidad):** base
6. **Jurisdicción:** panhispánica / conceptual por defecto (Capa A) — sin verificar todavía; la clasificación Capa A/B/C definitiva corresponde a `legalmente-legal-verification` sobre la pieza ya redactada, no a este candidato combinatorio (ver `docs/verificacion-mezcla-citas-jurisdiccion-2026-09-16.md`).
7. **Tensión jurídica:** el Derecho como algo ajeno
8. **Regla/problema central:** ¿qué falla en la práctica en peritaje medico cuando alguien necesita reflexionar?
9. **Metáfora visual:** dos epocas del mismo oficio mirandose desde lados opuestos del cristal
10. **visual_fingerprint completo:**
    - primary_direction: pintura botánica de gabinete
    - secondary_direction: (ninguna)
    - medium: pintura_y_tecnicas_pictoricas
    - lighting: luz de galería
    - palette: azul cobalto y piedra
    - composition: composición museográfica
    - materiality: lino
    - camera_optics: reflejo por espejo
    - realism: arqueológico reconstructivo
    - visual_mechanism: sello/impresión
11. **Prompt final:**

    > Una sola escena. un tratado antiguo de medicina legal abierto junto a un instrumental forense contemporaneo. Entorno: vitrina de un museo de medicina legal, luz cenital controlada. Camara: 35mm, plano medio sobre la vitrina. Punto focal: la pagina ilustrada junto al instrumental moderno. Familia visual: hiperrealismo editorial cinematografico. Componer nativamente para 1080x1920 completo aprovechando la verticalidad, pero mantener TODO el contenido semánticamente esencial (título, concepto jurídico, objeto o documento focal, metáfora principal, marca cuando corresponda) dentro del área central segura entre los píxeles 366 y 1554 desde arriba (equivalente al recorte 1080x1350, con margen interno conservador). Usar la extensión superior (0-285px) e inferior (1635-1920px) sólo para atmósfera, profundidad y expansión visual no indispensable — nunca para el mensaje jurídico. Direccion artistica: pintura botánica de gabinete. Medio: pintura y tecnicas pictoricas. Composicion: composición museográfica. Optica: reflejo por espejo. Materialidad: lino. Nivel de realismo: arqueológico reconstructivo. Mecanismo visual: sello/impresión. Metafora visual: dos epocas del mismo oficio mirandose desde lados opuestos del cristal. Luz: luz de galería. Intencion de luminosidad: legible, sin empastar los negros. Paleta: azul cobalto y piedra. El acento de color (azul cobalto y piedra) debe proceder de un objeto fisico real de la escena: una lupa de perito apoyada sobre el tratado. La escena incluye madera con una superficie de marca reservada y COMPLETAMENTE VACIA (relieve, perspectiva, material y luz correctos para que algo se lea ahi, pero SIN NINGUN CARACTER). La marca se compone despues.

12. **Comprobación temática anti-repetición:** NUEVO — lo más parecido está a distancia 0.9656 (umbral 0.25).
13. **Comprobación visual anti-repetición:** ver matriz de distancia al final del documento; huella incluida en el QA de lote (ACEPTADO).
14. **Safe zone 4:5 (tarea 78):** OK — ningún campo esencial declara una zona de riesgo.

## 8. CAND-0041 — laboral / representacion_colectiva

1. **Tema:** representacion colectiva — tratar el rastro digital como prueba
2. **Por qué fue seleccionado:** score compuesto 0.9781 (novedad semántica 0.7938, territorio 1.0, utilidad 1.0; señal de mercado +0.0400).
3. **Origen del candidato:** señal real de mercado (vacantes, market_signal.py) + banco editorial combinatorio
4. **Clasificación (taxonomía):** LABORAL — materia 'laboral' determina la etiqueta.
5. **Nivel (profundidad):** media
6. **Jurisdicción:** panhispánica / conceptual por defecto (Capa A) — sin verificar todavía; la clasificación Capa A/B/C definitiva corresponde a `legalmente-legal-verification` sobre la pieza ya redactada, no a este candidato combinatorio (ver `docs/verificacion-mezcla-citas-jurisdiccion-2026-09-16.md`).
7. **Tensión jurídica:** rastro perdido o inválido
8. **Regla/problema central:** ¿qué significaba la palabra en representacion colectiva cuando alguien necesita prepararse?
9. **Metáfora visual:** una conversacion que dejo huella aunque nadie pensó que alguien la leeria despues
10. **visual_fingerprint completo:**
    - primary_direction: arte helenístico
    - secondary_direction: telegráfica visual
    - medium: movimientos_y_lenguajes_historicos
    - lighting: luz polarizada
    - palette: púrpura profundo y marfil
    - composition: repetición modular
    - materiality: madera clara
    - camera_optics: refracción por vidrio
    - realism: semi-realista
    - visual_mechanism: revelado fotográfico
11. **Prompt final:**

    > Una sola escena. una cadena de mensajes impresa con los nombres tachados, extendida sobre una mesa. Entorno: sala de juntas sindical con una pantalla apagada al fondo. Camara: 50mm, plano cenital sobre la cadena de mensajes. Punto focal: la marca de tiempo visible de un mensaje. Familia visual: hiperrealismo editorial cinematografico. Componer nativamente para 1080x1920 completo aprovechando la verticalidad, pero mantener TODO el contenido semánticamente esencial (título, concepto jurídico, objeto o documento focal, metáfora principal, marca cuando corresponda) dentro del área central segura entre los píxeles 366 y 1554 desde arriba (equivalente al recorte 1080x1350, con margen interno conservador). Usar la extensión superior (0-285px) e inferior (1635-1920px) sólo para atmósfera, profundidad y expansión visual no indispensable — nunca para el mensaje jurídico. Direccion artistica: arte helenístico con acento de telegráfica visual. Medio: movimientos y lenguajes historicos. Composicion: repetición modular. Optica: refracción por vidrio. Materialidad: madera clara. Nivel de realismo: semi-realista. Mecanismo visual: revelado fotográfico. Metafora visual: una conversacion que dejo huella aunque nadie pensó que alguien la leeria despues. Luz: luz polarizada. Intencion de luminosidad: legible, sin empastar los negros. Paleta: púrpura profundo y marfil. El acento de color (púrpura profundo y marfil) debe proceder de un objeto fisico real de la escena: un pendrive sin etiqueta junto a las hojas impresas. La escena incluye sello de lacre con una superficie de marca reservada y COMPLETAMENTE VACIA (relieve, perspectiva, material y luz correctos para que algo se lea ahi, pero SIN NINGUN CARACTER). La marca se compone despues.

12. **Comprobación temática anti-repetición:** NUEVO — lo más parecido está a distancia 0.7938 (umbral 0.25).
13. **Comprobación visual anti-repetición:** ver matriz de distancia al final del documento; huella incluida en el QA de lote (ACEPTADO).
14. **Safe zone 4:5 (tarea 78):** OK — ningún campo esencial declara una zona de riesgo.

## 9. CAND-0053 — sucesorio / legitima

1. **Tema:** legitima — señalar qué cambió
2. **Por qué fue seleccionado:** score compuesto 0.973 (novedad semántica 0.91, territorio 1.0, utilidad 1.0; señal de mercado +0.0000).
3. **Origen del candidato:** banco editorial combinatorio (universe.py)
4. **Clasificación (taxonomía):** ESPECIALIZADO — sin materia con etiqueta directa; profundidad 'alta' determina el nivel genérico.
5. **Nivel (profundidad):** alta
6. **Jurisdicción:** panhispánica / conceptual por defecto (Capa A) — sin verificar todavía; la clasificación Capa A/B/C definitiva corresponde a `legalmente-legal-verification` sobre la pieza ya redactada, no a este candidato combinatorio (ver `docs/verificacion-mezcla-citas-jurisdiccion-2026-09-16.md`).
7. **Tensión jurídica:** conocimiento envejecido
8. **Regla/problema central:** ¿por qué ocurre en legitima cuando alguien necesita actualizar?
9. **Metáfora visual:** un rio que cambia de cauce sin dejar de ser el mismo rio
10. **visual_fingerprint completo:**
    - primary_direction: pintura tonalista
    - secondary_direction: (ninguna)
    - medium: pintura_y_tecnicas_pictoricas
    - lighting: luz volumétrica
    - palette: paleta de archivo
    - composition: balance de masas
    - materiality: vidrio esmerilado
    - camera_optics: lente macro
    - realism: naturalista
    - visual_mechanism: sello/impresión
11. **Prompt final:**

    > Una sola escena. dos versiones de una misma clausula testamentaria, una con una linea tachada y reescrita al margen. Entorno: despacho notarial con archivadores sucesorios al fondo. Camara: 35mm, plano cerrado sobre la clausula tachada. Punto focal: la reescritura al margen. Familia visual: hiperrealismo editorial cinematografico. Componer nativamente para 1080x1920 completo aprovechando la verticalidad, pero mantener TODO el contenido semánticamente esencial (título, concepto jurídico, objeto o documento focal, metáfora principal, marca cuando corresponda) dentro del área central segura entre los píxeles 366 y 1554 desde arriba (equivalente al recorte 1080x1350, con margen interno conservador). Usar la extensión superior (0-285px) e inferior (1635-1920px) sólo para atmósfera, profundidad y expansión visual no indispensable — nunca para el mensaje jurídico. Direccion artistica: pintura tonalista. Medio: pintura y tecnicas pictoricas. Composicion: balance de masas. Optica: lente macro. Materialidad: vidrio esmerilado. Nivel de realismo: naturalista. Mecanismo visual: sello/impresión. Metafora visual: un rio que cambia de cauce sin dejar de ser el mismo rio. Luz: luz volumétrica. Intencion de luminosidad: legible, sin empastar los negros. Paleta: paleta de archivo. El acento de color (paleta de archivo) debe proceder de un objeto fisico real de la escena: un sello notarial con fecha reciente junto al documento. La escena incluye cuaderno con una superficie de marca reservada y COMPLETAMENTE VACIA (relieve, perspectiva, material y luz correctos para que algo se lea ahi, pero SIN NINGUN CARACTER). La marca se compone despues.

12. **Comprobación temática anti-repetición:** NUEVO — lo más parecido está a distancia 0.91 (umbral 0.25).
13. **Comprobación visual anti-repetición:** ver matriz de distancia al final del documento; huella incluida en el QA de lote (ACEPTADO).
14. **Safe zone 4:5 (tarea 78):** OK — ningún campo esencial declara una zona de riesgo.

## 10. CAND-0013 — familiar / tutela

1. **Tema:** tutela — mostrar la vía no contenciosa
2. **Por qué fue seleccionado:** score compuesto 0.9722 (novedad semántica 0.9072, territorio 1.0, utilidad 1.0; señal de mercado +0.0000).
3. **Origen del candidato:** banco editorial combinatorio (universe.py)
4. **Clasificación (taxonomía):** FAMILIAR — materia 'familiar' determina la etiqueta.
5. **Nivel (profundidad):** media
6. **Jurisdicción:** panhispánica / conceptual por defecto (Capa A) — sin verificar todavía; la clasificación Capa A/B/C definitiva corresponde a `legalmente-legal-verification` sobre la pieza ya redactada, no a este candidato combinatorio (ver `docs/verificacion-mezcla-citas-jurisdiccion-2026-09-16.md`).
7. **Tensión jurídica:** litigio como único camino
8. **Regla/problema central:** ¿cómo se hace en tutela cuando alguien necesita acordar?
9. **Metáfora visual:** un espacio construido para que nadie tenga que ganar para que el otro pierda
10. **visual_fingerprint completo:**
    - primary_direction: holografía conceptual
    - secondary_direction: rúbrica notarial
    - medium: digital_cgi_y_visualizacion
    - lighting: silhouette controlada
    - palette: monocromía roja
    - composition: nadir
    - materiality: acero cepillado
    - camera_optics: cenital absoluto
    - realism: simbólico
    - visual_mechanism: huella/impresión
11. **Prompt final:**

    > Una sola escena. una mesa redonda con dos sillas enfrentadas y una tercera silla vacia a la cabecera. Entorno: sala de conciliacion familiar con luz calida, sin simbolos judiciales visibles. Camara: 35mm, plano medio de la mesa completa. Punto focal: la silla vacia de la cabecera. Familia visual: hiperrealismo editorial cinematografico. Componer nativamente para 1080x1920 completo aprovechando la verticalidad, pero mantener TODO el contenido semánticamente esencial (título, concepto jurídico, objeto o documento focal, metáfora principal, marca cuando corresponda) dentro del área central segura entre los píxeles 366 y 1554 desde arriba (equivalente al recorte 1080x1350, con margen interno conservador). Usar la extensión superior (0-285px) e inferior (1635-1920px) sólo para atmósfera, profundidad y expansión visual no indispensable — nunca para el mensaje jurídico. Direccion artistica: holografía conceptual con acento de rúbrica notarial. Medio: digital cgi y visualizacion. Composicion: nadir. Optica: cenital absoluto. Materialidad: acero cepillado. Nivel de realismo: simbólico. Mecanismo visual: huella/impresión. Metafora visual: un espacio construido para que nadie tenga que ganar para que el otro pierda. Luz: silhouette controlada. Intencion de luminosidad: legible, sin empastar los negros. Paleta: monocromía roja. El acento de color (monocromía roja) debe proceder de un objeto fisico real de la escena: una jarra de agua con dos vasos servidos sobre la mesa. La escena incluye chapa numerada con una superficie de marca reservada y COMPLETAMENTE VACIA (relieve, perspectiva, material y luz correctos para que algo se lea ahi, pero SIN NINGUN CARACTER). La marca se compone despues.

12. **Comprobación temática anti-repetición:** NUEVO — lo más parecido está a distancia 0.9072 (umbral 0.25).
13. **Comprobación visual anti-repetición:** ver matriz de distancia al final del documento; huella incluida en el QA de lote (ACEPTADO).
14. **Safe zone 4:5 (tarea 78):** OK — ningún campo esencial declara una zona de riesgo.

## Safe zone multiformato 9:16 → 4:5 (tarea 78, evidencia real)

Regla canónica: "9:16 visualmente amplio; 4:5 semánticamente completo" — `safe_zone.py`, aplicada aquí sobre 3 piezas reales de este mismo lote (no un ejemplo aparte). PLAN/PROMPT únicamente: no se rasteriza ninguna imagen — la evidencia es estructural, sobre el `VisualBrief` real de cada pieza.

### figura jurídica: CAND-0076 — dano ambiental — hacer visible un deber

- **Permanece dentro del crop (elementos esenciales declarados):** subject='dos sillas frente a frente en una mesa, solo una carpeta abierta del lado izquierdo'; focal_point='la carpeta cerrada del lado derecho'; metaphor='un puente construido desde un solo lado del rio'; acento_objeto='una taza de cafe sin tocar del lado de la carpeta cerrada'; marca_superficie='piedra'.
- **Puede perderse arriba (0–285px) o abajo (1635–1920px) sin cambiar el mensaje (elementos decorativos declarados):** environment='sala de negociacion con ventanales hacia un terreno en desarrollo'; camera='35mm, plano medio de la mesa'.
- **Por qué el mensaje sigue íntegro:** ningún elemento esencial depende de la extensión superior/inferior — el concepto jurídico, el objeto/documento focal, la metáfora y la marca viven, por declaración estructural, en `subject`/`focal_point`/`metaphor`/`acento_objeto`/`marca_superficie`, nunca en `environment`/`camera` (ver `safe_zone.CAMPOS_ESENCIALES`/`CAMPOS_DECORATIVOS`).
- **`crop_safe_4_5()`:** PASS (sin coincidencias de riesgo en campos esenciales).

### pieza probatoria/procesal: CAND-0034 — representacion organica — mostrar a quién toca probar

- **Permanece dentro del crop (elementos esenciales declarados):** subject='unos estatutos sociales impresos con una sola clausula marcada en rojo'; focal_point='la clausula marcada'; metaphor='una linea recta interrumpida por un unico quiebre deliberado'; acento_objeto='una regla de metal apoyada junto al documento'; marca_superficie='carpeta'.
- **Puede perderse arriba (0–285px) o abajo (1635–1920px) sin cambiar el mensaje (elementos decorativos declarados):** environment='sala de juntas vacia tras una asamblea'; camera='35mm, plano medio sobre el documento'.
- **Por qué el mensaje sigue íntegro:** ningún elemento esencial depende de la extensión superior/inferior — el concepto jurídico, el objeto/documento focal, la metáfora y la marca viven, por declaración estructural, en `subject`/`focal_point`/`metaphor`/`acento_objeto`/`marca_superficie`, nunca en `environment`/`camera` (ver `safe_zone.CAMPOS_ESENCIALES`/`CAMPOS_DECORATIVOS`).
- **`crop_safe_4_5()`:** PASS (sin coincidencias de riesgo en campos esenciales).

### pieza conceptual: CAND-0055 — donacion — recuperar el origen de una palabra

- **Permanece dentro del crop (elementos esenciales declarados):** subject='un diccionario etimologico abierto junto a una escritura de donacion manuscrita antigua'; focal_point='la raiz de la palabra subrayada a lapiz'; metaphor='una palabra que atraviesa siglos y llega casi intacta hasta el documento de hoy'; acento_objeto='una pluma antigua apoyada entre ambos textos'; marca_superficie='placa de laton'.
- **Puede perderse arriba (0–285px) o abajo (1635–1920px) sin cambiar el mensaje (elementos decorativos declarados):** environment='archivo notarial con luz de ventana lateral'; camera='50mm, plano cerrado sobre las dos paginas'.
- **Por qué el mensaje sigue íntegro:** ningún elemento esencial depende de la extensión superior/inferior — el concepto jurídico, el objeto/documento focal, la metáfora y la marca viven, por declaración estructural, en `subject`/`focal_point`/`metaphor`/`acento_objeto`/`marca_superficie`, nunca en `environment`/`camera` (ver `safe_zone.CAMPOS_ESENCIALES`/`CAMPOS_DECORATIVOS`).
- **`crop_safe_4_5()`:** PASS (sin coincidencias de riesgo en campos esenciales).

## Matriz de distancia visual entre las 10 huellas (dimensiones distintas / conocidas)

| | 0008 | 0034 | 0055 | 0119 | 0050 | 0076 | 0129 | 0041 | 0053 | 0013 |
|---|---|---|---|---|---|---|---|---|---|---|
| **0008** | — | 9/9 | 9/9 | 9/9 | 9/9 | 9/9 | 8/8 | 9/9 | 8/8 | 7/8 |
| **0034** | 9/9 | — | 9/9 | 9/9 | 8/9 | 9/9 | 8/8 | 9/9 | 8/8 | 8/8 |
| **0055** | 9/9 | 9/9 | — | 9/9 | 9/9 | 9/9 | 8/8 | 8/9 | 8/8 | 8/8 |
| **0119** | 9/9 | 9/9 | 9/9 | — | 9/9 | 9/9 | 8/8 | 9/9 | 8/8 | 8/8 |
| **0050** | 9/9 | 8/9 | 9/9 | 9/9 | — | 9/9 | 8/8 | 9/9 | 8/8 | 8/8 |
| **0076** | 9/9 | 9/9 | 9/9 | 9/9 | 9/9 | — | 8/8 | 10/10 | 8/8 | 9/9 |
| **0129** | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | — | 8/8 | 7/8 | 8/8 |
| **0041** | 9/9 | 9/9 | 8/9 | 9/9 | 9/9 | 10/10 | 8/8 | — | 8/8 | 9/9 |
| **0053** | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | 7/8 | 8/8 | — | 8/8 |
| **0013** | 7/8 | 8/8 | 8/8 | 8/8 | 8/8 | 9/9 | 8/8 | 9/9 | 8/8 | — |
