"""Eventos estructurados. Sin secretos, nunca.

No hay framework de logging: una lista de eventos serializables que el pipeline
acumula y el receipt puede transportar.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

EVENTOS = (
    "visual.input.accepted", "visual.gate.rejected", "visual.brief.created",
    "visual.prompt.compiled", "visual.provider.selected", "visual.generation.started",
    "visual.generation.completed", "visual.generation.failed", "visual.qa.completed",
    "visual.regeneration.created", "visual.batch.completed",
)

# Claves que jamas se registran, aunque alguien las pase por descuido.
PROHIBIDAS = {"api_key", "apikey", "token", "secret", "authorization", "password", "credential"}


@dataclass
class EventLog:
    events: list = field(default_factory=list)

    def emit(self, name, **campos):
        if name not in EVENTOS:
            raise ValueError(f"evento no declarado: {name!r}")
        limpio = {k: v for k, v in campos.items() if k.lower() not in PROHIBIDAS}
        self.events.append({
            "event": name,
            "at": datetime.now(timezone.utc).isoformat(),
            **limpio,
        })
        return self.events[-1]

    def names(self):
        return [e["event"] for e in self.events]

    def to_list(self):
        return list(self.events)
