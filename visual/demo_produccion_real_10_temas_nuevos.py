"""Prueba REAL de producción — Parte XIII del mandato "Fase post-
implementación: prueba real de producción + inteligencia temática"
(Founder, 16-sep-2026).

Diferencia central con la prueba de aceptación de la sesión anterior
(demo_prueba_aceptacion_10_temas.py): esos 10 temas se redactaron a mano
como fixtures de prueba del motor visual. Estos 10 salen del motor
editorial REAL — universe.build_reserve() + generator.seleccionar_lote()
(con señal de mercado real, market_signal.py) — nunca de una lista escrita
para la ocasión. Lo único que se redacta a mano es la dirección visual
concreta por pieza (subject/environment/metaphor/acento) — eso es
autoría creativa legítima sobre un tema ya seleccionado por el motor, no
una afirmación jurídica (que sigue NO_VERIFICADA, como todo candidato).

PLANES/PROMPTS únicamente. Ningún proveedor de imagen fue invocado
(ver docs/auditoria-inteligencia-tematica-2026-09-16.md §3: no hay
generador real conectado en este repositorio).

Uso: `cd visual && python3 demo_produccion_real_10_temas_nuevos.py`
"""

import json
from pathlib import Path

import arquetipo_compositivo as arq
import corpus_import as ci
import direccion_causal as dcau
import editorial
import generator
import market_signal as ms
import territory_explorer as te
import topic_classification as tc
import universe
import visual_distance as vdist
import visual_fingerprint as vf
from brief import VisualBrief, VisualPolicy
from compiler import compile_request
from memory import VisualMemoryEntry
from semantic_memory import SemanticMemory
from vacancy_radar import VacancyPosting
from visual_fingerprint_batch import generar_lote_visual

SEED_RESERVA = 20260916
POLICY = VisualPolicy.load()
CATALOGO = vf.MasterCatalog.load()
SUPERFICIES = POLICY.data["marca"]["superficies_permitidas"]
FAMILIA_ESTRUCTURAL = POLICY.familias[0]

# Dirección visual autoral por candidato — NO infraestructura, redacción
# humana (de esta sesión) sobre cada tema ya seleccionado por el motor
# real. Claves = candidate_id producido por la corrida con SEED_RESERVA
# (determinista: misma semilla, mismos 10 candidatos, ver comprobación
# en test_produccion_real_10_temas_nuevos.py).
DIRECCION_VISUAL = {
    "CAND-0008": dict(  # mercantil / representación orgánica — doctrina sin autor
        subject="una placa de bronce con un nombre a medio borrar junto a un libro de actas abierto",
        environment="archivo corporativo con estantes de expedientes societarios",
        camera="50mm, plano cerrado sobre la placa", focal_point="el nombre a medio borrar",
        metaphor="una firma que se disuelve en la institucion que ayudo a crear",
        acento_objeto="un sello corporativo de metal sin usar"),
    "CAND-0034": dict(  # mercantil / sociedades — regla tomada como absoluta
        # Re-autorado (continuación motor visual, 17-sep-2026, 3ª pasada):
        # la composición original ("sala de juntas" + documento) se
        # concentraba en el mismo arquetipo compositivo que otras 5 piezas
        # del lote (verificado con arquetipo_compositivo.py — Regla 3 del
        # banco artístico anterior, "no más de 3 del mismo arquetipo").
        # Mismo concepto jurídico, composición distinta: un objeto sellado
        # sobre una superficie despejada, no una mesa de reunión.
        subject="un sobre lacrado con el sello corporativo intacto, apoyado en el borde de un escritorio vacio",
        environment="oficina de actas societarias, el resto del escritorio despejado",
        camera="50mm, plano cerrado sobre el lacre", focal_point="el lacre sin romper",
        metaphor="quien debe abrir el sobre es quien debe probar lo que contiene",
        acento_objeto="una regla de metal apoyada junto al sobre"),
    "CAND-0107": dict(  # civil / donación — deber difuso en la empresa
        subject="una pila de recibos de donacion sin ninguna firma que los reclame",
        environment="oficina de finanzas corporativas al cierre del trimestre",
        camera="35mm, plano cenital sobre los recibos", focal_point="el espacio de firma vacio",
        metaphor="varias manos que se pasan una vela encendida sin que ninguna la sostenga el tiempo suficiente",
        acento_objeto="un sello de recibido sin fecha"),
    "CAND-0044": dict(  # historia_del_derecho / juristas — legalidad vs realidad
        subject="un libro de derecho antiguo abierto sobre un escritorio, su sombra cae fuera de la pagina",
        environment="biblioteca juridica historica al atardecer",
        camera="50mm, angulo bajo", focal_point="la sombra que rebasa el borde de la pagina",
        metaphor="un mapa cuyos limites no coinciden con el territorio que describe",
        acento_objeto="un compas de laton sobre el escritorio"),
    "CAND-0087": dict(  # seguridad_social / pensión — daño sin restitución
        subject="una libreta de pensiones con paginas en blanco donde deberian estar los registros",
        environment="ventanilla de tramites de seguridad social",
        camera="35mm, plano cerrado sobre la libreta", focal_point="las paginas en blanco",
        metaphor="una balanza con un platillo vacio, esperando un peso que se prometio",
        acento_objeto="un sello de fecha sin usar sobre el mostrador"),
    "CAND-0127": dict(  # transito / atestado — abstracción sin uso
        subject="un formulario de atestado vial llenado a un costado de la carretera",
        environment="borde de carretera de noche, luces de un vehiculo al fondo",
        camera="35mm, picada leve sobre el formulario", focal_point="la firma reciente en el formulario",
        metaphor="un boceto que debe sobrevivir a ser leido por alguien que nunca estuvo ahi",
        acento_objeto="una linterna de mano apoyada sobre el capó"),
    "CAND-0128": dict(  # ambiental / daño ambiental — techo de comprensión
        subject="frascos de muestras de suelo alineados, cada uno fechado, el ultimo vacio",
        environment="laboratorio de campo ambiental junto a un rio",
        camera="35mm, plano secuencial de los frascos", focal_point="el frasco vacio al final de la fila",
        metaphor="un horizonte que retrocede cada vez que el observador se acerca",
        acento_objeto="una pala pequeña de muestreo apoyada contra la mesa"),
    "CAND-0025": dict(  # salud_medico_legal / responsabilidad sanitaria — deber ignorado
        subject="un formulario de consentimiento informado con la linea de firma en blanco",
        environment="consultorio medico al final del turno",
        camera="35mm, plano medio sobre el formulario", focal_point="la linea de firma vacia",
        metaphor="una bata blanca colgada sobre una silla vacia",
        acento_objeto="un estetoscopio colgado junto a la puerta"),
    "CAND-0076": dict(  # ambiental / licencia ambiental — posición sin preparación
        # Re-autorado (continuación motor visual, 17-sep-2026, 3ª pasada):
        # ver nota en CAND-0034 — misma causa (arquetipo "escena de
        # escritorio" sobrerrepresentado). Se evita además reutilizar el
        # motivo de frascos/instrumental de laboratorio ya usado por
        # CAND-0050 en este mismo lote (ambos son "ambiental"): la nueva
        # composición es de terreno/deslinde, no de laboratorio.
        subject="un poste de deslinde a medio clavar en el limite de un terreno parcialmente desmontado",
        environment="borde de un terreno en desarrollo, vegetacion cortada de un lado e intacta del otro",
        camera="35mm, plano general bajo con el poste en primer termino",
        focal_point="el poste a medio clavar",
        metaphor="una obligacion que empezo a cumplirse y se detuvo a la mitad",
        acento_objeto="una cinta de señalizacion amarilla atada al poste"),
    "CAND-0003": dict(  # civil / obligaciones — ficción televisiva vs técnica
        subject="una lupa sobre una pagina de contrato rota, marcadores de evidencia numerados al lado",
        environment="mesa de trabajo pericial con luz de lampara de escritorio",
        camera="50mm, plano cerrado sobre la lupa", focal_point="el desgarro del contrato bajo la lupa",
        metaphor="un reflector de serie policiaca que se apaga hasta quedar la luz plana de un laboratorio real",
        acento_objeto="un marcador de evidencia numerado junto al contrato"),
    # Continuación pedagógica (17-sep-2026, 2ª pasada): el registro editorial
    # creció de 58 a 65 familias (7 altas reales). Bajo la misma semilla, el
    # candidato #N-ésimo de la reserva ahora es otro (universe.build_reserve
    # recorre un universo más grande) — 7 de los 10 candidate_id de este lote
    # cambiaron. No es una regresión del motor: es la consecuencia esperada
    # de una alta editorial real. Se re-autora la dirección visual para los
    # 7 nuevos candidate_id, con la misma disciplina (redacción creativa
    # sobre un tema ya seleccionado por el motor, nunca infraestructura).
    "CAND-0055": dict(  # civil / donación — recuperar el origen de una palabra
        subject="un diccionario etimologico abierto junto a una escritura de donacion manuscrita antigua",
        environment="archivo notarial con luz de ventana lateral",
        camera="50mm, plano cerrado sobre las dos paginas", focal_point="la raiz de la palabra subrayada a lapiz",
        metaphor="una palabra que atraviesa siglos y llega casi intacta hasta el documento de hoy",
        acento_objeto="una pluma antigua apoyada entre ambos textos"),
    "CAND-0119": dict(  # laboral / salario — estructurar un acuerdo antes del conflicto
        subject="dos propuestas salariales impresas, una junto a la otra, con un boligrafo sin tapar entre ambas",
        environment="sala de reuniones de recursos humanos antes de una firma",
        camera="35mm, plano cenital sobre las dos hojas", focal_point="el espacio vacio entre las dos propuestas",
        metaphor="dos orillas que todavia no han decidido donde poner el puente",
        acento_objeto="una calculadora de bolsillo apagada junto a las hojas"),
    "CAND-0050": dict(  # ambiental / principio precautorio — exponer una tensión estructural
        subject="una balanza de laboratorio con un platillo cargado y el otro con un espacio marcado pero vacio",
        environment="laboratorio ambiental con instrumental de medicion al fondo",
        camera="50mm, plano medio sobre la balanza", focal_point="el platillo vacio marcado",
        metaphor="decidir el peso de algo que todavia no se ha terminado de medir",
        acento_objeto="un frasco de muestra sin etiquetar junto a la balanza"),
    "CAND-0129": dict(  # salud_medico_legal / peritaje médico — entrar por una obra cultural
        subject="un tratado antiguo de medicina legal abierto junto a un instrumental forense contemporaneo",
        environment="vitrina de un museo de medicina legal, luz cenital controlada",
        camera="35mm, plano medio sobre la vitrina", focal_point="la pagina ilustrada junto al instrumental moderno",
        metaphor="dos epocas del mismo oficio mirandose desde lados opuestos del cristal",
        acento_objeto="una lupa de perito apoyada sobre el tratado"),
    "CAND-0041": dict(  # laboral / representación colectiva — tratar el rastro digital como prueba
        # Re-autorado DE NUEVO (continuación motor visual, 17-sep-2026, 4ª
        # pasada — "afinidad entre arquetipos cercanos"): la versión de la
        # 3ª pasada seguía siendo "interior institucional" (archivo) —
        # verificado con arquetipo_compositivo.verificar_afinidad_familias:
        # el lote llegó a tener 7/10 en esa familia perceptual pese a que
        # cada arquetipo individual respetaba su propio tope. Nueva
        # composición: registro industrial/laboral, no de oficina.
        subject="un tablon de anuncios con un aviso impreso pegado encima de uno antiguo despegado a medias",
        environment="area de casilleros de una planta industrial, luz de tubos fluorescentes",
        camera="50mm, plano cerrado sobre el tablon",
        focal_point="el aviso impreso pegado encima del antiguo",
        metaphor="una conversacion que dejo huella aunque nadie pensó que alguien la leeria despues",
        acento_objeto="un candado abierto colgado de un casillero cercano"),
    "CAND-0053": dict(  # sucesorio / legítima — señalar qué cambió
        # Re-autorado DE NUEVO (4ª pasada, "afinidad entre arquetipos
        # cercanos" — ver nota en CAND-0041). La metáfora ya declarada
        # ("un río que cambia de cauce sin dejar de ser el mismo río") no
        # tenía escena propia: se autoraba sobre un despacho con
        # archivadores. Se le da escena literal, coherente con su propia
        # metáfora, y se sale del registro "interior institucional".
        subject="un antiguo mojon de piedra medio hundido en la orilla de un cauce que cambio de curso",
        environment="orilla de un rio en terreno rural, el cauce viejo visible como una depresion seca cercana",
        camera="35mm, plano general bajo con el mojon en primer termino",
        focal_point="el mojon medio hundido",
        metaphor="un rio que cambia de cauce sin dejar de ser el mismo rio",
        acento_objeto="una fecha antigua apenas legible tallada en el mojon"),
    "CAND-0013": dict(  # familiar / tutela — mostrar la vía no contenciosa
        # Re-autorado DE NUEVO (4ª pasada — ver nota en CAND-0041): la
        # mesa de conciliación era el séptimo miembro de la familia
        # perceptual "interior institucional". Misma idea (un camino sin
        # ganador/perdedor), escena de jardín en vez de sala de reunión.
        subject="un sendero de jardin que se divide en dos y vuelve a unirse mas adelante, sin cerca entre ambos",
        environment="jardin privado con luz de tarde, sin simbolos judiciales visibles",
        camera="35mm, plano general bajo con el sendero en primer termino",
        focal_point="el punto donde el sendero vuelve a unirse",
        metaphor="un camino que se separa sin dejar de llevar al mismo lugar",
        acento_objeto="una puerta de jardin abierta y sin candado junto al sendero"),
}


def construir_reserva_y_seleccion():
    regs, _ = ci.construir_registros()
    universo = editorial.EditorialUniverse.load()
    _, materias = universe.cargar_materias()
    mapa = te.construir_mapa(regs, materias=materias, universo=universo)
    memoria = SemanticMemory()
    ci.importar(memoria, regs)

    data = json.loads((Path(__file__).resolve().parent.parent / "corpus" /
                       "vacantes-16-sep-2026.json").read_text(encoding="utf-8"))
    postings = [VacancyPosting(titulo=v["titulo"], empresa=v["empresa"], url=v["url"],
                               publicado=v["publicado"]) for v in data["vacantes"]]
    señales = ms.agrupar_por_concepto(ms.procesar_vacantes(postings))

    reserva = universe.build_reserve(objetivo_lote=10, seed=SEED_RESERVA, factor=14)
    # objetivo_conocimiento=None (Mandato Maestro §3, 17-sep-2026): este lote
    # es una referencia histórica CONGELADA del 16-sep-2026 —
    # DIRECCION_VISUAL abajo está autorada a mano por candidate_id exacto.
    # El ajuste de balance pedagógico (posterior a esta corrida) desplazaría
    # la selección y rompería esa correspondencia; se desactiva explícita y
    # deliberadamente para preservar la reproducibilidad exacta de ESTE lote
    # ya documentado (docs/prueba-real-produccion-10-temas-2026-09-16.md),
    # no porque el mecanismo esté desactivado en el motor real.
    seleccion, puntuaciones, rechazados = generator.seleccionar_lote(
        reserva, memoria, mapa, universo=universo, n=10, materias=materias,
        señales_mercado=señales, objetivo_conocimiento=None)
    return seleccion, puntuaciones, rechazados, memoria, señales


def construir_brief(c, direccion, superficie):
    return VisualBrief(
        content_id=c.candidate_id, formato="VERTICAL_9_16", visual_family=FAMILIA_ESTRUCTURAL,
        subject=direccion["subject"], environment=direccion["environment"],
        camera=direccion["camera"], focal_point=direccion["focal_point"],
        metaphor=direccion["metaphor"], acento_objeto=direccion["acento_objeto"],
        marca_superficie=superficie)


def _entry_real(c, direccion, huella, superficie, significado):
    """`VisualMemoryEntry` con datos REALES de esta pieza — no de
    infraestructura pendiente. `scene_type`/`human_presence` reutilizan
    `direccion_causal.derivar_significado()` (ya calculado, auditable,
    misma disciplina que el resto del repo: nunca se fabrica un valor
    donde no hay evidencia). `subject`/`metaphor` vienen de la autoría real
    (`DIRECCION_VISUAL`), no de contenido PENDIENTE — a diferencia del flujo
    automatizado de `production_run.py`, aquí SÍ hay dato real para las 8
    dimensiones de `visual_distance.py`."""
    return VisualMemoryEntry(
        content_id=c.candidate_id, generation_id=f"prod-real-{c.candidate_id}",
        visual_family=huella.primary_direction, scene_type=significado.movimiento_juridico,
        main_subject=direccion["subject"], camera_angle=huella.camera_optics,
        shot_distance=direccion["camera"], lighting_type=huella.lighting,
        dominant_materials=[huella.materiality], dominant_palette=[huella.palette],
        metaphor=direccion["metaphor"], human_presence=significado.presencia_humana,
        brand_surface=superficie, materia=c.materia, concepto=c.concepto_nucleo)


def _distancia_estricta_del_lote(resultados):
    """Wiring del HOTFIX 'distancia visual y anti-monotonía' (banco
    artístico anterior, 8-sep-2026 — Drive, Guía operativa del motor de
    dirección artística): 8 dimensiones, mínimo 5 cambiadas, 3 vecinos más
    cercanos. Esa regla YA estaba portada en `visual_distance.py`
    (reconciliación con legalmente-web), pero nunca se ejercitaba con datos
    reales — el flujo automatizado de `production_run.py` tiene
    `metaphor`/`scene_type` deliberadamente PENDIENTE, así que siempre
    reporta EVIDENCIA_INCOMPLETA. Este demo SÍ tiene autoría real completa:
    aquí la regla puede validar (o rechazar) de verdad."""
    entries = [_entry_real(r["candidato"], r["direccion"], r["huella"],
                           r["superficie"], r["significado"]) for r in resultados]
    return vdist.verificar_lote_contra_historia(entries, historia=())


def ejecutar():
    seleccion, puntuaciones, rechazados, memoria, señales = construir_reserva_y_seleccion()

    faltantes = [c.candidate_id for c in seleccion if c.candidate_id not in DIRECCION_VISUAL]
    if faltantes:
        raise RuntimeError(
            f"la corrida produjo candidatos sin direccion visual autorada: {faltantes} "
            "(la semilla cambio o el motor cambio de comportamiento -- revisar DIRECCION_VISUAL).")

    content_ids = [c.candidate_id for c in seleccion]
    huellas, reporte_lote_visual, intentos = generar_lote_visual(content_ids, catalogo=CATALOGO,
                                                                  canal="produccion-real")

    resultados = []
    for i, (c, p, huella) in enumerate(zip(seleccion, puntuaciones, huellas)):
        direccion = DIRECCION_VISUAL[c.candidate_id]
        superficie = SUPERFICIES[i % len(SUPERFICIES)]
        brief = construir_brief(c, direccion, superficie)
        compilado = compile_request(brief, POLICY, fingerprint=huella)
        significado = dcau.derivar_significado(c)

        clasif_rep = tc.clasificar_repeticion(c, memoria)
        etiqueta_taxonomia, razon_taxonomia = tc.clasificar_taxonomia(c)
        origen = ("señal real de mercado (vacantes, market_signal.py) + banco editorial combinatorio"
                  if p.ajuste_senal_mercado > 0 else "banco editorial combinatorio (universe.py)")

        resultados.append(dict(
            candidato=c, puntuacion=p, direccion=direccion, huella=huella, compilado=compilado,
            brief=brief, superficie=superficie, significado=significado,
            clasif_repeticion=clasif_rep, etiqueta_taxonomia=etiqueta_taxonomia,
            razon_taxonomia=razon_taxonomia, origen=origen))

    mezcla = tc.reportar_mezcla_editorial(seleccion)
    mezcla["distancia_estricta_lote"] = _distancia_estricta_del_lote(resultados).to_dict()
    piezas_arquetipo = [(r["candidato"].candidate_id, r["direccion"]["subject"],
                        r["direccion"]["environment"]) for r in resultados]
    mezcla["arquetipo_compositivo"] = arq.verificar_diversidad_arquetipos(piezas_arquetipo).to_dict()
    mezcla["afinidad_familias"] = arq.verificar_afinidad_familias(piezas_arquetipo).to_dict()
    piezas_ambientacion = [(r["candidato"].candidate_id, r["direccion"]["environment"])
                           for r in resultados]
    mezcla["redundancia_ambientacion"] = arq.verificar_redundancia_ambientacion(
        piezas_ambientacion).to_dict()
    return resultados, reporte_lote_visual, intentos, mezcla, rechazados, señales


def matriz_similitud_visual(resultados):
    n = len(resultados)
    filas = []
    for i in range(n):
        fila = []
        for j in range(n):
            if i == j:
                fila.append(None)
                continue
            d, k = vf.distancia(resultados[i]["huella"], resultados[j]["huella"])
            fila.append(f"{d}/{k}")
        filas.append(fila)
    return filas


# Categorías representativas del mandato ("DEMO REAL", tarea 78): una
# figura jurídica, una pieza probatoria/procesal, una pieza conceptual. Se
# eligen por `familia_editorial` real (no por candidate_id fijo — esos ya
# demostraron poder desplazarse cuando el registro editorial crece), con un
# fallback posicional si ninguna coincide en un lote futuro distinto.
_FAMILIAS_FIGURA_JURIDICA = ("obligacion", "derecho", "requisito", "responsabilidad")
_FAMILIAS_PROBATORIA_PROCESAL = ("carga_de_la_prueba", "evidencia_digital", "prueba",
                                "etapa_procesal", "proceso")
_FAMILIAS_CONCEPTUAL = ("etimologia", "concepto", "definicion_operativa", "paradoja_tension")


def _elegir_representativo(resultados, familias, usados):
    for r in resultados:
        if r["candidato"].candidate_id in usados:
            continue
        if r["candidato"].familia_editorial in familias:
            return r
    for r in resultados:
        if r["candidato"].candidate_id not in usados:
            return r
    return resultados[0]


def _seccion_safe_zone(resultados):
    usados = set()
    seleccionados = []
    for etiqueta, familias in (
        ("figura jurídica", _FAMILIAS_FIGURA_JURIDICA),
        ("pieza probatoria/procesal", _FAMILIAS_PROBATORIA_PROCESAL),
        ("pieza conceptual", _FAMILIAS_CONCEPTUAL),
    ):
        r = _elegir_representativo(resultados, familias, usados)
        usados.add(r["candidato"].candidate_id)
        seleccionados.append((etiqueta, r))

    lineas = [
        "## Safe zone multiformato 9:16 → 4:5 (tarea 78, evidencia real)",
        "",
        "Regla canónica: \"9:16 visualmente amplio; 4:5 semánticamente completo\" — "
        "`safe_zone.py`, aplicada aquí sobre 3 piezas reales de este mismo lote (no un "
        "ejemplo aparte). PLAN/PROMPT únicamente: no se rasteriza ninguna imagen — la "
        "evidencia es estructural, sobre el `VisualBrief` real de cada pieza.",
        "",
    ]
    for etiqueta, r in seleccionados:
        c, brief, comp = r["candidato"], r["brief"], r["compilado"]
        geo = comp.metadata.get("safe_zone_geometry") or {}
        detalle = comp.crop_safe_4_5_detalle
        lineas += [
            f"### {etiqueta}: {c.candidate_id} — {c.concepto_nucleo}",
            "",
            f"- **Permanece dentro del crop (elementos esenciales declarados):** "
            f"subject={brief.subject!r}; focal_point={brief.focal_point!r}; "
            f"metaphor={brief.metaphor!r}; acento_objeto={brief.acento_objeto!r}; "
            f"marca_superficie={brief.marca_superficie!r}.",
            f"- **Puede perderse arriba (0–{geo.get('crop_top', '?')}px) o abajo "
            f"({geo.get('crop_bottom', '?')}–{geo.get('canvas_height', '?')}px) sin cambiar el "
            f"mensaje (elementos decorativos declarados):** environment={brief.environment!r}; "
            f"camera={brief.camera!r}.",
            f"- **Por qué el mensaje sigue íntegro:** ningún elemento esencial depende de la "
            "extensión superior/inferior — el concepto jurídico, el objeto/documento focal, la "
            "metáfora y la marca viven, por declaración estructural, en `subject`/`focal_point`/"
            "`metaphor`/`acento_objeto`/`marca_superficie`, nunca en `environment`/`camera` "
            "(ver `safe_zone.CAMPOS_ESENCIALES`/`CAMPOS_DECORATIVOS`).",
            f"- **`crop_safe_4_5()`:** {'PASS' if comp.crop_safe_4_5_ok else 'FAIL'} "
            f"({'sin coincidencias de riesgo en campos esenciales' if comp.crop_safe_4_5_ok else detalle.get('campos_esenciales_en_riesgo')}).",
            "",
        ]
    return lineas


def reporte_markdown(resultados, reporte_lote_visual, intentos, mezcla, rechazados, señales):
    lineas = [
        "# Prueba real de producción — 10 temas nuevos desde el motor editorial (Parte XIII, 16-sep-2026)",
        "",
        "PLANES/PROMPTS únicamente. Ningún proveedor de imagen fue invocado — ver "
        "`docs/auditoria-inteligencia-tematica-2026-09-16.md` §3 (ningún generador real conectado).",
        "",
        f"**Origen:** `universe.build_reserve(seed={SEED_RESERVA})` + "
        "`generator.seleccionar_lote()` (motor editorial real, no una lista redactada para "
        "la ocasión) + señal de mercado real (`market_signal.py`, 30 vacantes de Indeed MX "
        "capturadas el 16-sep-2026). "
        f"{len(rechazados)} candidatos rechazados en el camino por hard gates antes de llegar a estos 10.",
        "",
        f"**QA de huella visual:** {reporte_lote_visual.veredicto} en {intentos} intento(s) "
        f"({reporte_lote_visual.telemetria['huellas_distintas']}/10 huellas distintas, "
        f"{reporte_lote_visual.telemetria['medios_distintos']} medios distintos).",
        "",
        f"**Mezcla editorial por profundidad:** {mezcla['conteo_por_profundidad']}"
        + (f" — avisos: {'; '.join(mezcla['avisos'])}" if mezcla["avisos"] else " — dentro del rango sugerido."),
        "",
        f"**Distancia visual estricta (8 dims, mínimo 5 cambiadas, banco artístico anterior — "
        f"HOTFIX 8-sep-2026, ver `visual_distance.py`):** "
        f"{'OK' if mezcla['distancia_estricta_lote']['ok'] else 'FALLA'} — "
        f"{mezcla['distancia_estricta_lote']['total_revisadas']} comparaciones revisadas (3 vecinos "
        "más cercanos por pieza, sólo ámbito LOTE), datos reales de este lote (no PENDIENTE_CONTENIDO)."
        + ("" if mezcla["distancia_estricta_lote"]["ok"] else
           " Problemas: " + "; ".join(mezcla["distancia_estricta_lote"]["problemas"])),
        "",
        f"**Diversidad de arquetipo compositivo (Regla 3, máx. "
        f"{mezcla['arquetipo_compositivo']['max_por_arquetipo']}/10 del mismo, ver "
        f"`arquetipo_compositivo.py`):** {'OK' if mezcla['arquetipo_compositivo']['ok'] else 'FALLA'} — "
        f"{mezcla['arquetipo_compositivo']['conteo']}.",
        "",
        f"**Afinidad entre arquetipos cercanos (Regla 9 — familias perceptuales, máx. "
        f"{mezcla['afinidad_familias']['max_por_familia']}/10 combinado):** "
        f"{'OK' if mezcla['afinidad_familias']['ok'] else 'FALLA'} — {mezcla['afinidad_familias']['conteo']}.",
        "",
        f"**Redundancia de vocabulario de ambientación (eje distinto del arquetipo, máx. "
        f"{mezcla['redundancia_ambientacion']['max_por_familia']}/10 del mismo tipo de lugar):** "
        f"{'OK' if mezcla['redundancia_ambientacion']['ok'] else 'FALLA'} — "
        f"{mezcla['redundancia_ambientacion']['conteo']}.",
        "",
    ]

    for i, r in enumerate(resultados, 1):
        c, p, d, h, comp = (r["candidato"], r["puntuacion"], r["direccion"], r["huella"],
                            r["compilado"])
        lineas += [
            f"## {i}. {c.candidate_id} — {c.materia} / {c.submateria}",
            "",
            f"1. **Tema:** {c.concepto_nucleo}",
            f"2. **Por qué fue seleccionado:** score compuesto {p.score_compuesto} "
            f"(novedad semántica {p.semantic_novelty}, territorio {p.territory_coverage}, "
            f"utilidad {p.utility}; señal de mercado {p.ajuste_senal_mercado:+.4f}).",
            f"3. **Origen del candidato:** {r['origen']}",
            f"4. **Clasificación (taxonomía):** {r['etiqueta_taxonomia']} — {r['razon_taxonomia']}",
            f"5. **Nivel (profundidad):** {c.profundidad}",
            "6. **Jurisdicción:** panhispánica / conceptual por defecto (Capa A) — sin verificar "
            "todavía; la clasificación Capa A/B/C definitiva corresponde a "
            "`legalmente-legal-verification` sobre la pieza ya redactada, no a este candidato "
            "combinatorio (ver `docs/verificacion-mezcla-citas-jurisdiccion-2026-09-16.md`).",
            f"7. **Tensión jurídica:** {c.relacion}",
            f"8. **Regla/problema central:** {c.pregunta_resuelta}",
            f"9. **Metáfora visual:** {d['metaphor']}",
            "10. **visual_fingerprint completo:**",
            f"    - primary_direction: {h.primary_direction}",
            f"    - secondary_direction: {h.secondary_direction or '(ninguna)'}",
            f"    - medium: {h.medium}",
            f"    - lighting: {h.lighting}",
            f"    - palette: {h.palette}",
            f"    - composition: {h.composition}",
            f"    - materiality: {h.materiality}",
            f"    - camera_optics: {h.camera_optics}",
            f"    - realism: {h.realism}",
            f"    - visual_mechanism: {h.visual_mechanism}",
            "11. **Prompt final:**",
            "",
            f"    > {comp.positive_prompt}",
            "",
            f"12. **Comprobación temática anti-repetición:** {r['clasif_repeticion'].etiqueta} — "
            f"{r['clasif_repeticion'].motivo}",
            "13. **Comprobación visual anti-repetición:** ver matriz de distancia al final del "
            f"documento; huella incluida en el QA de lote ({reporte_lote_visual.veredicto}).",
            f"14. **Safe zone 4:5 (tarea 78):** {'OK' if comp.crop_safe_4_5_ok else 'FALLA'} — "
            f"{'ningún campo esencial declara una zona de riesgo.' if comp.crop_safe_4_5_ok else '; '.join(comp.crop_safe_4_5_detalle.get('campos_esenciales_en_riesgo', {}))}",
            "",
        ]

    lineas += _seccion_safe_zone(resultados)

    lineas += ["## Matriz de distancia visual entre las 10 huellas (dimensiones distintas / conocidas)", ""]
    ids = [r["candidato"].candidate_id.replace("CAND-", "") for r in resultados]
    lineas.append("| | " + " | ".join(ids) + " |")
    lineas.append("|---" * (len(ids) + 1) + "|")
    m = matriz_similitud_visual(resultados)
    for i, fila in enumerate(m):
        celdas = ["—" if v is None else v for v in fila]
        lineas.append(f"| **{ids[i]}** | " + " | ".join(celdas) + " |")

    return "\n".join(lineas) + "\n"


if __name__ == "__main__":
    resultados, reporte_lote_visual, intentos, mezcla, rechazados, señales = ejecutar()
    md = reporte_markdown(resultados, reporte_lote_visual, intentos, mezcla, rechazados, señales)
    destino = (Path(__file__).resolve().parent.parent / "docs" /
              "prueba-real-produccion-10-temas-2026-09-16.md")
    destino.write_text(md, encoding="utf-8")
    print(md)
    print(f"\nEscrito en {destino}")
