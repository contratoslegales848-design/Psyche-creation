"""Memoria visual y riesgo de repeticion.

La repeticion visual es un defecto SISTEMICO, no un descuido del fundador. Los
recursos gastados (balanza, mazo, tribunal, escritorio, libro) no quedan
prohibidos para siempre: se penalizan por recencia.

Determinista y auditable a proposito. Sin ML: el score se puede recalcular a
mano y explicar en una frase.
"""

import json
import unicodedata
from dataclasses import dataclass, field, asdict
from pathlib import Path

MEMORY_SCHEMA_VERSION = "1.0"

# Pesos del score. Suman 100 con todos los ejes repetidos y recientes.
PESO_ESCENA = 30
PESO_SUJETO = 30
PESO_CAMARA = 15
PESO_METAFORA = 15
PESO_OBJETO = 10

UMBRAL_ALTO = 60
UMBRAL_MEDIO = 30

# Cuantas veces puede aparecer el mismo sujeto en la ventana antes de saturar.
MAX_RECENT_OCCURRENCES = 2


def normaliza(texto):
    """Minusculas, sin tildes, sin puntuacion suelta. Compara conceptos, no cadenas."""
    if not texto:
        return ""
    t = unicodedata.normalize("NFKD", str(texto).strip().lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(c for c in t.replace("-", " ").split() if c.isalnum() or " " in c)


@dataclass
class VisualMemoryEntry:
    """Huella de una generacion. Se registra al aceptarse el asset, no antes."""

    content_id: str
    generation_id: str
    visual_family: str = ""
    scene_type: str = ""
    main_subject: str = ""
    secondary_objects: list = field(default_factory=list)
    camera_angle: str = ""
    shot_distance: str = ""
    lighting_type: str = ""
    dominant_materials: list = field(default_factory=list)
    dominant_palette: list = field(default_factory=list)
    metaphor: str = ""
    human_presence: str = ""
    architecture: str = ""
    brand_surface: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class RepetitionAssessment:
    score: int
    nivel: str                      # BAJO | MEDIO | ALTO
    razones: list = field(default_factory=list)
    evitar: list = field(default_factory=list)   # alimenta los negativos del compilador

    def to_dict(self):
        return asdict(self)


class VisualMemory:
    """Ventana de las ultimas N generaciones. Persistible en JSON, sin base de datos."""

    def __init__(self, entries=(), ventana=12):
        self._entries = list(entries)
        self.ventana = int(ventana)

    def __len__(self):
        return len(self._entries)

    def record(self, entry):
        self._entries.insert(0, entry)

    def recent(self, n=None):
        return self._entries[: (n if n is not None else self.ventana)]

    # --- persistencia ---
    def save(self, path):
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(
            {"schema_version": MEMORY_SCHEMA_VERSION,
             "ventana": self.ventana,
             "entries": [e.to_dict() for e in self._entries]},
            ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return p

    @classmethod
    def load(cls, path, ventana=12):
        p = Path(path)
        if not p.is_file():
            return cls(ventana=ventana)
        data = json.loads(p.read_text(encoding="utf-8"))
        if data.get("schema_version") != MEMORY_SCHEMA_VERSION:
            # Version desconocida: se ignora la memoria en vez de malinterpretarla.
            # Perder memoria degrada la variedad; malinterpretarla corrompe el score.
            return cls(ventana=ventana)
        entries = [VisualMemoryEntry(**e) for e in data.get("entries", [])]
        return cls(entries, ventana=data.get("ventana", ventana))

    # --- el score ---
    def assess(self, entry):
        """Riesgo de repeticion de `entry` frente a la ventana reciente."""
        recientes = self.recent()
        score, razones, evitar = 0, [], []

        if not recientes:
            return RepetitionAssessment(0, "BAJO", ["sin generaciones recientes con que comparar."], [])

        def ocurrencias(attr, valor):
            v = normaliza(valor)
            if not v:
                return 0
            return sum(1 for e in recientes if normaliza(getattr(e, attr)) == v)

        n_escena = ocurrencias("scene_type", entry.scene_type)
        if n_escena:
            score += min(PESO_ESCENA, PESO_ESCENA * n_escena // MAX_RECENT_OCCURRENCES)
            razones.append(f"escena {entry.scene_type!r} usada {n_escena} de las ultimas {len(recientes)}.")
            evitar.append(entry.scene_type)

        n_sujeto = ocurrencias("main_subject", entry.main_subject)
        if n_sujeto:
            score += min(PESO_SUJETO, PESO_SUJETO * n_sujeto // MAX_RECENT_OCCURRENCES)
            razones.append(f"sujeto {entry.main_subject!r} usado {n_sujeto} de las ultimas {len(recientes)}.")
            evitar.append(entry.main_subject)

        n_camara = ocurrencias("camera_angle", entry.camera_angle)
        if n_camara:
            score += min(PESO_CAMARA, PESO_CAMARA * n_camara // MAX_RECENT_OCCURRENCES)
            razones.append(f"camara {entry.camera_angle!r} usada {n_camara} de las ultimas {len(recientes)}.")

        n_metafora = ocurrencias("metaphor", entry.metaphor)
        if n_metafora:
            score += min(PESO_METAFORA, PESO_METAFORA * n_metafora // MAX_RECENT_OCCURRENCES)
            razones.append(f"metafora {entry.metaphor!r} repetida {n_metafora} veces.")
            evitar.append(entry.metaphor)

        objetos = {normaliza(o) for o in entry.secondary_objects if normaliza(o)}
        if objetos:
            repetidos = sorted({
                normaliza(o) for e in recientes for o in e.secondary_objects
                if normaliza(o) in objetos
            })
            if repetidos:
                score += min(PESO_OBJETO, PESO_OBJETO * len(repetidos) // max(1, len(objetos)))
                razones.append(f"objetos repetidos recientemente: {repetidos}.")
                evitar.extend(repetidos)

        score = min(100, score)
        nivel = "ALTO" if score >= UMBRAL_ALTO else "MEDIO" if score >= UMBRAL_MEDIO else "BAJO"
        if not razones:
            razones.append("ningun eje coincide con las generaciones recientes.")
        # La familia visual compartida NO es repeticion: es identidad de marca.
        return RepetitionAssessment(score, nivel, razones, sorted(set(x for x in evitar if x)))
