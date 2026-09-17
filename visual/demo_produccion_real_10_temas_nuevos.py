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

import corpus_import as ci
import editorial
import generator
import market_signal as ms
import territory_explorer as te
import topic_classification as tc
import universe
import visual_fingerprint as vf
from brief import VisualBrief, VisualPolicy
from compiler import compile_request
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
        subject="unos estatutos sociales impresos con una sola clausula marcada en rojo",
        environment="sala de juntas vacia tras una asamblea",
        camera="35mm, plano medio sobre el documento", focal_point="la clausula marcada",
        metaphor="una linea recta interrumpida por un unico quiebre deliberado",
        acento_objeto="una regla de metal apoyada junto al documento"),
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
        subject="dos sillas frente a frente en una mesa, solo una carpeta abierta del lado izquierdo",
        environment="sala de negociacion con ventanales hacia un terreno en desarrollo",
        camera="35mm, plano medio de la mesa", focal_point="la carpeta cerrada del lado derecho",
        metaphor="un puente construido desde un solo lado del rio",
        acento_objeto="una taza de cafe sin tocar del lado de la carpeta cerrada"),
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
        subject="una cadena de mensajes impresa con los nombres tachados, extendida sobre una mesa",
        environment="sala de juntas sindical con una pantalla apagada al fondo",
        camera="50mm, plano cenital sobre la cadena de mensajes", focal_point="la marca de tiempo visible de un mensaje",
        metaphor="una conversacion que dejo huella aunque nadie pensó que alguien la leeria despues",
        acento_objeto="un pendrive sin etiqueta junto a las hojas impresas"),
    "CAND-0053": dict(  # sucesorio / legítima — señalar qué cambió
        subject="dos versiones de una misma clausula testamentaria, una con una linea tachada y reescrita al margen",
        environment="despacho notarial con archivadores sucesorios al fondo",
        camera="35mm, plano cerrado sobre la clausula tachada", focal_point="la reescritura al margen",
        metaphor="un rio que cambia de cauce sin dejar de ser el mismo rio",
        acento_objeto="un sello notarial con fecha reciente junto al documento"),
    "CAND-0013": dict(  # familiar / tutela — mostrar la vía no contenciosa
        subject="una mesa redonda con dos sillas enfrentadas y una tercera silla vacia a la cabecera",
        environment="sala de conciliacion familiar con luz calida, sin simbolos judiciales visibles",
        camera="35mm, plano medio de la mesa completa", focal_point="la silla vacia de la cabecera",
        metaphor="un espacio construido para que nadie tenga que ganar para que el otro pierda",
        acento_objeto="una jarra de agua con dos vasos servidos sobre la mesa"),
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

        clasif_rep = tc.clasificar_repeticion(c, memoria)
        etiqueta_taxonomia, razon_taxonomia = tc.clasificar_taxonomia(c)
        origen = ("señal real de mercado (vacantes, market_signal.py) + banco editorial combinatorio"
                  if p.ajuste_senal_mercado > 0 else "banco editorial combinatorio (universe.py)")

        resultados.append(dict(
            candidato=c, puntuacion=p, direccion=direccion, huella=huella, compilado=compilado,
            brief=brief, clasif_repeticion=clasif_rep, etiqueta_taxonomia=etiqueta_taxonomia,
            razon_taxonomia=razon_taxonomia, origen=origen))

    mezcla = tc.reportar_mezcla_editorial(seleccion)
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
