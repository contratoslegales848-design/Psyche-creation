"""Raiz de almacenamiento runtime persistente. Nunca /tmp por defecto.

El registro de generaciones (visual/registry.py) acepta cualquier raiz — eso
ya estaba resuelto. Lo que faltaba era UN default real: hasta ahora cada
pasada usaba un directorio de /tmp elegido a mano, que desaparece con la
sesion. Este modulo define ese default sin tocar registry.py (que sigue sin
saber nada de configuracion global — sigue recibiendo una raiz, tal cual).

Separacion de responsabilidades (no se implementa aqui, solo se documenta):
  - Git (este repo)          canon, policies, schemas, decisiones humanas explicitas, contratos.
  - LEGALMENTE_RUNTIME_ROOT   assets crudos/compuestos, receipts, indice de generaciones/lineage.
  - Drive                     gobernanza, documentos, continuidad legible por humanos.
  - Base de datos             no existe todavia; no hace falta hasta que haya concurrencia real.
"""

import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Por defecto, un directorio DENTRO del repo pero fuera de git (ver .gitignore),
# nunca /tmp. Configurable via variable de entorno para despliegues reales.
_DEFAULT_ROOT = REPO / ".runtime" / "visual-registry"


def default_registry_root():
    """La raiz persistente real, o el override explicito de entorno.

    No crea el directorio: eso lo hace AssetRegistry.__init__ al usarla.
    """
    override = os.environ.get("LEGALMENTE_RUNTIME_ROOT")
    return Path(override).resolve() if override else _DEFAULT_ROOT
