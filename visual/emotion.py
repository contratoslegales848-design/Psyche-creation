"""Motor emocional — P1 del Handoff Founder 2026-09-13 §6.

"La emoción es clave y no puede agregarse al final como decoración." Por eso
el `EmotionalProfile` se calcula ANTES del arte y viaja hasta el brief: la
emoción modifica narrativa, metáfora, escala, composición, cámara, luz,
textura, ritmo y dirección artística.

Dos reglas duras del canon, implementadas como código y no como advertencia:

1. NO SE ASIGNAN AL AZAR. La emoción se DERIVA de necesidad + tensión
   editorial + consecuencia + rol del lector. `derivar()` es una función pura:
   mismas entradas, misma emoción, con las razones que la justifican.

2. NUNCA SE MODIFICA LA VERDAD JURÍDICA PARA PROVOCAR EMOCIÓN. Aquí eso es
   ejecutable: las emociones de alta intensidad (urgencia, indignación
   contenida, gravedad) EXIGEN que la pieza declare una consecuencia real. Sin
   consecuencia declarada no hay urgencia que dramatizar, y el motor degrada a
   la emoción sobria equivalente en vez de inventar alarma. Fail-closed.

Este módulo no toca claims, fuentes ni jurisdicción, y no abre ningún gate.
"""

from dataclasses import dataclass, field, asdict

from memory import normaliza

EMOTION_SCHEMA_VERSION = "1.0"

# --- catálogo emocional y su traducción a dirección de arte ---------------
# Cada estado declara CÓMO se ve, para que la emoción no sea una etiqueta
# decorativa sino un conjunto de decisiones visuales verificables.
EMOCIONES = {
    "curiosidad":            {"intensidad": 2, "escala": "humana",     "composicion": "descentrada_tension", "camara": "ligeramente elevada, objeto parcialmente revelado", "luz": "lateral suave con zona oculta", "textura": "limpia", "ritmo": "abierto", "narrativa": "abre una pregunta y no la cierra en el titular"},
    "claridad":              {"intensidad": 1, "escala": "humana",     "composicion": "centrada_axial",      "camara": "frontal a la altura del objeto",                 "luz": "difusa y uniforme",             "textura": "mate",   "ritmo": "sereno", "narrativa": "nombra una distinción con precisión"},
    "confianza":             {"intensidad": 1, "escala": "humana",     "composicion": "simetrica",           "camara": "frontal estable",                                "luz": "cálida envolvente",             "textura": "noble",  "ritmo": "sostenido", "narrativa": "afirma lo verificado y marca el límite"},
    "reflexion":             {"intensidad": 1, "escala": "intima",     "composicion": "vacio_dominante",     "camara": "plano general con aire",                         "luz": "tenue de ventana",              "textura": "porosa", "ritmo": "lento", "narrativa": "sostiene una tensión sin resolverla"},
    "empatia":               {"intensidad": 2, "escala": "intima",     "composicion": "descentrada_tension", "camara": "cercana, altura de los ojos",                    "luz": "suave y baja",                  "textura": "textil", "ritmo": "pausado", "narrativa": "parte de la persona antes que de la norma"},
    "asombro":               {"intensidad": 3, "escala": "monumental", "composicion": "simetrica",           "camara": "contrapicado amplio",                            "luz": "cenital dramática",             "textura": "pétrea", "ritmo": "amplio", "narrativa": "revela una magnitud inesperada"},
    "sorpresa":              {"intensidad": 3, "escala": "humana",     "composicion": "diagonal",            "camara": "angulo inusual, escorzo",                        "luz": "contrastada de un solo foco",   "textura": "pulida", "ritmo": "quebrado", "narrativa": "coloca el giro antes de la explicación"},
    "inquietud":             {"intensidad": 3, "escala": "humana",     "composicion": "descentrada_tension", "camara": "ligeramente inclinada",                          "luz": "contraluz con sombra larga",    "textura": "rugosa", "ritmo": "irregular", "narrativa": "muestra la señal antes que el daño"},
    "tension":               {"intensidad": 4, "escala": "humana",     "composicion": "diagonal",            "camara": "picado corto sobre el punto de quiebre",         "luz": "dura y direccional",            "textura": "metálica", "ritmo": "tenso", "narrativa": "enfrenta dos posiciones sin aún resolver"},
    "gravedad":              {"intensidad": 4, "escala": "monumental", "composicion": "centrada_axial",      "camara": "frontal baja, sujeto dominante",                 "luz": "lateral profunda, negros densos", "textura": "basáltica", "ritmo": "solemne", "narrativa": "expone la consecuencia en toda su escala"},
    "urgencia":              {"intensidad": 5, "escala": "humana",     "composicion": "diagonal",            "camara": "cercana y móvil, corte al detalle",              "luz": "alto contraste, foco único",    "textura": "áspera", "ritmo": "acelerado", "narrativa": "sitúa el plazo o la pérdida en primer plano"},
    "indignacion_contenida": {"intensidad": 5, "escala": "intima",     "composicion": "centrada_axial",      "camara": "fija, frontal, sin escape",                      "luz": "fría y plana",                  "textura": "seca",   "ritmo": "contenido", "narrativa": "muestra el desequilibrio sin levantar la voz"},
    "alivio":                {"intensidad": 2, "escala": "humana",     "composicion": "vacio_dominante",     "camara": "plano abierto tras el conflicto",                "luz": "amanecer suave",                "textura": "lavada", "ritmo": "distendido", "narrativa": "cierra mostrando la salida verificada"},
}

# Emoción base por NECESIDAD humana. Es el ancla: qué necesita quien lee.
BASE_POR_NECESIDAD = {
    "entender": "claridad", "distinguir": "claridad", "corregir": "sorpresa",
    "prevenir": "inquietud", "prepararse": "confianza", "decidir": "tension",
    "actuar": "urgencia", "reclamar": "indignacion_contenida", "cumplir": "gravedad",
    "detectar": "inquietud", "acordar": "confianza", "recordar": "asombro",
    "aplicar": "claridad", "actualizar": "urgencia", "reflexionar": "reflexion",
}

# Ajuste por FAMILIA EDITORIAL: la función editorial matiza el ancla.
AJUSTE_POR_FAMILIA = {
    "mito": "sorpresa", "confusion_habitual": "claridad", "creencia_popular": "sorpresa",
    "rareza_juridica": "asombro", "etimologia": "curiosidad", "historia_del_derecho": "asombro",
    "jurista": "asombro", "caso_historico": "asombro", "caso_cotidiano": "empatia",
    "paradoja_tension": "reflexion", "pregunta_avanzada": "reflexion", "doctrina": "reflexion",
    "senal_de_alerta": "inquietud", "error_frecuente": "inquietud", "riesgo": "inquietud",
    "plazo_prescripcion": "urgencia", "actualizacion_normativa": "urgencia",
    "consecuencia": "gravedad", "responsabilidad": "gravedad", "incumplimiento": "gravedad",
    "reparacion": "alivio", "conciliacion_mediacion": "alivio", "prevencion": "confianza",
    "checklist": "confianza", "herramienta_practica": "confianza", "primeros_pasos": "confianza",
    "derecho": "indignacion_contenida", "cultura_juridica": "curiosidad",
    "lenguaje_juridico_explicado": "claridad", "diferencia": "claridad",
    "clausula_bajo_lupa": "tension", "carga_de_la_prueba": "tension",
}

# El rol PROFESIONAL atempera: un especialista no necesita que le dramaticen
# el dato. Sustituye la emoción alta por su equivalente sobria.
ATEMPERADO_PROFESIONAL = {
    "urgencia": "tension", "indignacion_contenida": "gravedad",
    "sorpresa": "curiosidad", "asombro": "reflexion",
}

# Degradación fail-closed cuando la pieza NO declara consecuencia: no se
# fabrica alarma sobre nada.
DEGRADACION_SIN_CONSECUENCIA = {
    "urgencia": "claridad", "indignacion_contenida": "reflexion", "gravedad": "claridad",
}
INTENSIDAD_EXIGE_CONSECUENCIA = 4


# `normaliza()` trata "_" como separador de palabra (ver memory.py), así que
# una clave literal "plazo_prescripcion" NUNCA casaría contra el valor
# normalizado "plazo prescripcion". Las tablas se indexan normalizadas una vez
# al cargar el módulo, en vez de confiar en que las claves coincidan por azar.
_BASE_NORM = {normaliza(k): v for k, v in BASE_POR_NECESIDAD.items()}
_AJUSTE_NORM = {normaliza(k): v for k, v in AJUSTE_POR_FAMILIA.items()}


class EmotionError(ValueError):
    pass


@dataclass
class EmotionalProfile:
    emocion: str = ""
    intensidad: int = 0
    narrativa: str = ""
    escala: str = ""
    composicion: str = ""
    camara: str = ""
    luz: str = ""
    textura: str = ""
    ritmo: str = ""
    razones: list = field(default_factory=list)
    schema_version: str = EMOTION_SCHEMA_VERSION

    def to_dict(self):
        return asdict(self)


def _perfil(emocion, razones):
    d = EMOCIONES[emocion]
    return EmotionalProfile(
        emocion=emocion, intensidad=d["intensidad"], narrativa=d["narrativa"],
        escala=d["escala"], composicion=d["composicion"], camara=d["camara"],
        luz=d["luz"], textura=d["textura"], ritmo=d["ritmo"], razones=list(razones))


def derivar(necesidad="", familia_editorial="", consecuencia="", rol_lector="", evitar=()):
    """Deriva el perfil emocional. Función pura, sin azar.

    `evitar` son emociones usadas recientemente: si la derivada está en esa
    lista, se rota a la alternativa más cercana en intensidad que respete las
    mismas reglas. Rotar NO es aleatorizar — la alternativa sigue siendo
    coherente con la necesidad y la consecuencia declaradas.
    """
    razones = []
    nec, fam = normaliza(necesidad), normaliza(familia_editorial)
    rol, cons = normaliza(rol_lector), normaliza(consecuencia)

    emocion = _BASE_NORM.get(nec)
    if emocion:
        razones.append(f"necesidad {nec!r} ancla en {emocion!r}.")
    ajuste = _AJUSTE_NORM.get(fam)
    if ajuste:
        razones.append(f"familia editorial {fam!r} ajusta a {ajuste!r}.")
        emocion = ajuste
    if not emocion:
        # Sin necesidad ni familia declaradas no hay de dónde derivar. Se
        # devuelve un perfil vacío en vez de inventar una emoción: una emoción
        # sin origen es exactamente la decoración que el canon prohíbe.
        return EmotionalProfile(razones=[
            "sin necesidad ni familia editorial declaradas: no hay de dónde derivar "
            "una emoción. No se asigna ninguna (el canon prohíbe la emoción decorativa)."])

    if rol == "profesional" and emocion in ATEMPERADO_PROFESIONAL:
        nuevo = ATEMPERADO_PROFESIONAL[emocion]
        razones.append(f"rol profesional atempera {emocion!r} -> {nuevo!r}.")
        emocion = nuevo

    if EMOCIONES[emocion]["intensidad"] >= INTENSIDAD_EXIGE_CONSECUENCIA and not cons:
        nuevo = DEGRADACION_SIN_CONSECUENCIA.get(emocion, "claridad")
        razones.append(
            f"{emocion!r} exige una consecuencia declarada y la pieza no la tiene: "
            f"degradado a {nuevo!r}. No se fabrica alarma sin consecuencia real.")
        emocion = nuevo

    evitar_norm = {normaliza(e) for e in evitar if normaliza(e)}
    if normaliza(emocion) in evitar_norm:
        alternativa = _rotar(emocion, evitar_norm, exige_consecuencia=bool(cons))
        if alternativa:
            razones.append(f"{emocion!r} usada recientemente: rota a {alternativa!r} "
                           "(misma coherencia, no azar).")
            emocion = alternativa
        else:
            razones.append(f"{emocion!r} usada recientemente pero no hay alternativa "
                           "coherente: se conserva antes que falsear la emoción.")
    return _perfil(emocion, razones)


def _rotar(emocion, evitar_norm, exige_consecuencia):
    """Alternativa más próxima en intensidad que no esté vetada."""
    objetivo = EMOCIONES[emocion]["intensidad"]
    candidatas = []
    for nombre, d in EMOCIONES.items():
        if normaliza(nombre) in evitar_norm or nombre == emocion:
            continue
        if d["intensidad"] >= INTENSIDAD_EXIGE_CONSECUENCIA and not exige_consecuencia:
            continue                       # misma regla fail-closed en la rotación
        candidatas.append((abs(d["intensidad"] - objetivo), nombre))
    return sorted(candidatas)[0][1] if candidatas else ""


def aplicar_a_brief(brief, perfil):
    """Traslada el perfil emocional al VisualBrief. NO muta el original.

    Sólo toca campos de dirección de arte. `content_id`, `formato` y todo lo
    que sea canon jurídico quedan intactos: la emoción cambia cómo se ve una
    verdad, nunca cuál es.
    """
    import copy
    if not perfil or not perfil.emocion:
        return brief, {}
    nuevo, cambios = copy.deepcopy(brief), {}

    def set_(campo, valor):
        if campo in ("content_id", "formato", "tiene_carga_juridica"):
            raise EmotionError(f"la emoción no puede alterar {campo!r}.")
        if getattr(nuevo, campo, None) != valor:
            cambios[campo] = {"antes": getattr(nuevo, campo, None), "despues": valor}
            setattr(nuevo, campo, valor)

    set_("camera", perfil.camara)
    set_("key_light", perfil.luz)
    set_("brightness_intent", f"{perfil.luz}; intención emocional: {perfil.emocion}")
    set_("negative_space", perfil.composicion)
    constraints = list(nuevo.constraints)
    for c in (f"escala {perfil.escala}", f"composición {perfil.composicion}",
              f"textura {perfil.textura}", f"ritmo {perfil.ritmo}"):
        if c not in constraints:
            constraints.append(c)
    set_("constraints", constraints)
    return nuevo, cambios
