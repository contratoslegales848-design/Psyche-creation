"""Feedback humano -> cambios controlados de brief. Nunca toca el canon juridico.

Un codigo de feedback NO es texto libre: es una transformacion declarada,
auditable y probada. El fundador deja de cazar el mismo defecto a mano.
"""

from dataclasses import dataclass, field, asdict

FEEDBACK_CODES = {
    "TOO_DARK", "TOO_MURKY", "SEPIA_DOMINANT", "WRONG_FORMAT", "TEXT_ERROR",
    "AUTHOR_ERROR", "BRAND_ERROR", "BRAND_FLOATING", "WRONG_COMPOSITION",
    "REPETITIVE_SCENE", "REPETITIVE_OBJECT", "REPETITIVE_CAMERA", "TOO_GENERIC",
    "MORE_HYPERREALISTIC", "CHANGE_CAMERA", "CHANGE_METAPHOR", "WEAK_VISUAL_METAPHOR",
    "OTHER",
}

# Campos del brief que el feedback visual PUEDE tocar. Todo lo demas es canon.
CAMPOS_MUTABLES = {
    "brightness_intent", "key_light", "camera", "subject", "environment",
    "metaphor", "text_rendering_mode", "marca_texto_en_imagen", "negative_constraints",
    "constraints", "visual_family", "focal_point",
}

# Campos que ningun feedback puede alterar jamas.
CAMPOS_CANONICOS = {"content_id", "formato"}


class FeedbackViolatesCanonError(ValueError):
    pass


@dataclass
class FeedbackRecord:
    generation_id: str
    codes: list = field(default_factory=list)
    comment: str = ""
    revisor: str = ""

    def to_dict(self):
        return asdict(self)


def validate_codes(codes):
    desconocidos = [c for c in codes if c not in FEEDBACK_CODES]
    if desconocidos:
        raise ValueError(f"codigos de feedback desconocidos: {desconocidos}")
    return list(codes)


def apply_feedback(brief, codes, comment=""):
    """Devuelve (nuevo_brief, changed_fields). El brief original NO se muta."""
    import copy
    validate_codes(codes)
    nuevo = copy.deepcopy(brief)
    cambios = {}

    def set_(campo, valor):
        if campo in CAMPOS_CANONICOS:
            raise FeedbackViolatesCanonError(f"el feedback visual no puede alterar {campo!r}.")
        if campo not in CAMPOS_MUTABLES:
            raise FeedbackViolatesCanonError(f"campo no mutable por feedback: {campo!r}.")
        if getattr(nuevo, campo) != valor:
            cambios[campo] = {"antes": getattr(nuevo, campo), "despues": valor}
            setattr(nuevo, campo, valor)

    def add_negativo(*items):
        actuales = list(nuevo.negative_constraints)
        nuevos = [i for i in items if i not in actuales]
        if nuevos:
            set_("negative_constraints", actuales + nuevos)

    for c in codes:
        if c == "TOO_DARK":
            set_("brightness_intent", "exposicion mas alta, sombras abiertas, negros con detalle")
            add_negativo("pieza excesivamente oscura", "negros sin detalle")
        elif c == "TOO_MURKY":
            add_negativo("marron embarrado", "atmosfera turbia")
            set_("key_light", "luz mas limpia y direccional")
        elif c == "SEPIA_DOMINANT":
            add_negativo("sepia dominante", "viraje sepia", "monocromia calida")
        elif c == "TEXT_ERROR":
            set_("text_rendering_mode", "POST_COMPOSITE")
        elif c in ("BRAND_ERROR", "BRAND_FLOATING"):
            # El texto de marca vuelve a composicion determinista, siempre.
            set_("marca_texto_en_imagen", False)
            add_negativo("logo flotante", "watermark", "branding de esquina ajeno a la escena")
        elif c == "REPETITIVE_SCENE":
            add_negativo(f"repetir escena: {brief.environment}")
        elif c == "REPETITIVE_OBJECT":
            add_negativo(f"repetir objeto: {brief.subject}")
        elif c == "REPETITIVE_CAMERA":
            set_("camera", "encuadre distinto del anterior")
            add_negativo(f"repetir camara: {brief.camera}")
        elif c == "WRONG_COMPOSITION":
            add_negativo("collage", "grid", "storyboard", "split screen")
        elif c == "TOO_GENERIC":
            add_negativo("imagen de stock", "simbolo juridico generico")
        elif c == "MORE_HYPERREALISTIC":
            set_("visual_family", "hiperrealismo_editorial_cinematografico")
        elif c == "CHANGE_CAMERA":
            set_("camera", "encuadre distinto del anterior")
        elif c == "CHANGE_METAPHOR":
            set_("metaphor", "")
        elif c == "WEAK_VISUAL_METAPHOR":
            # Mecanico solamente: borra la metafora debil y marca la escena/objeto
            # actuales como evitables. La metafora nueva es contenido creativo y la
            # aporta quien construye el brief revisado (no este modulo mecanico).
            set_("metaphor", "")
            add_negativo(f"repetir escena generica: {brief.environment}")
        # WRONG_FORMAT y AUTHOR_ERROR no se autocorrigen: tocan canon o taxonomia
        # y exigen decision humana explicita, no una transformacion automatica.

    if cambios:
        try:
            mayor, menor = nuevo.brief_version.split(".")
            nuevo.brief_version = f"{mayor}.{int(menor) + 1}"
        except (ValueError, AttributeError):
            nuevo.brief_version = "1.1"
    return nuevo, cambios
