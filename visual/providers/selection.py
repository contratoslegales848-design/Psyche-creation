"""Seleccion y negociacion explicita de proveedor.

Tres desenlaces, nunca una degradacion silenciosa:

    ACCEPT  el proveedor atiende la peticion tal cual
    ADAPT   puede atenderla con un ajuste seguro y declarado (p. ej. reescalado
            dentro del mismo aspect ratio)
    REJECT  no puede sin romper una regla esencial
"""

from .base import negotiate

ACCEPT, ADAPT, REJECT = "ACCEPT", "ADAPT", "REJECT"


def evaluate(request, capabilities):
    """Devuelve (decision, notas). No degrada reglas esenciales."""
    problemas = negotiate(request, capabilities)
    if not problemas:
        return ACCEPT, []

    # ADAPT solo cuando el aspect ratio (regla esencial) se conserva y lo unico
    # que cambia es la resolucion, que el pipeline puede reescalar sin mentir.
    solo_tamano = all("ancho" in p or "alto" in p for p in problemas)
    if solo_tamano and capabilities.aspect_ratios and request.aspect_ratio in capabilities.aspect_ratios:
        return ADAPT, ["resolucion ajustada dentro del mismo aspect ratio: " + "; ".join(problemas)]

    return REJECT, problemas


class ProviderRegistry:
    """Registro de proveedores disponibles. Hoy solo el falso; el core admite mas."""

    def __init__(self, providers=()):
        self._providers = {p.id: p for p in providers}

    def register(self, provider):
        self._providers[provider.id] = provider

    def ids(self):
        return sorted(self._providers)

    def get(self, pid):
        return self._providers.get(pid)

    def select(self, request, preferred=None):
        """Elige el primer proveedor que ACCEPT; si ninguno, el mejor ADAPT.

        Devuelve (provider, decision, notas). (None, REJECT, notas) si ninguno sirve.
        """
        orden = ([preferred] if preferred else []) + [p for p in self.ids() if p != preferred]
        mejor_adapt, notas_totales = None, []
        for pid in orden:
            p = self._providers.get(pid)
            if p is None:
                continue
            decision, notas = evaluate(request, p.capabilities())
            if decision == ACCEPT:
                return p, ACCEPT, notas
            if decision == ADAPT and mejor_adapt is None:
                mejor_adapt = (p, notas)
            notas_totales.extend(notas)
        if mejor_adapt:
            return mejor_adapt[0], ADAPT, mejor_adapt[1]
        return None, REJECT, notas_totales
