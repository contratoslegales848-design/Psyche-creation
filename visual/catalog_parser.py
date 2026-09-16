"""Parser del catálogo maestro de dirección artística — Fase 2-3 del mandato
"Súper Prompt" (Founder, 16-sep-2026).

Fuente canónica HUMANA: `policy/catalogo-maestro-v1.md` (767 módulos
visuales, copia literal del documento entregado por el Founder — nunca se
edita a mano, igual criterio que `corpus/README.md` para el banco v3).

Este módulo genera la representación machine-readable
(`policy/catalogo-maestro-v1.json`) por PARSEO AUTOMÁTICO del .md — nunca
una lista escrita a mano por un agente. Si el .md cambia, se re-ejecuta
este parser; el JSON se declara derivado, nunca se edita directamente
(mandato Fase 3: "generar una representación derivada automáticamente, no
una lista manual independiente").
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

CATALOGO_MD_PATH = Path(__file__).resolve().parent / "policy" / "catalogo-maestro-v1.md"
CATALOGO_JSON_PATH = Path(__file__).resolve().parent / "policy" / "catalogo-maestro-v1.json"

# Slugs para las subsecciones de "3. Direcciones artísticas base" — estas
# son las candidatas a primary_direction / secondary_direction.
SECCIONES_DIRECCIONES = {
    "3.1": "fotografia",
    "3.2": "pintura_y_tecnicas_pictoricas",
    "3.3": "dibujo_grabado_y_estampa",
    "3.4": "movimientos_y_lenguajes_historicos",
    "3.5": "editorial_diseno_grafico_y_sistemas_impresos",
    "3.6": "escultura_objeto_y_material",
    "3.7": "arquitectura_espacio_y_escenografia",
    "3.8": "digital_cgi_y_visualizacion",
    "3.9": "fotografia_optica_experimental",
    "3.10": "archivo_manuscrito_y_cultura_documental",
}

# Slugs para "4. Módulos auxiliares de huella visual" — mapean directo a
# las dimensiones de visual_fingerprint (mandato Fase 4).
SECCIONES_AUXILIARES = {
    "4.1": "lighting",
    "4.2": "composition",
    "4.3": "camera_optics",
    "4.4": "palette",
    "4.5": "materiality",
    "4.6": "realism",
    "4.7": "visual_mechanism",
}

RE_HEADER = re.compile(r"^### (\d+\.\d+)\s+(.+)$")
RE_BULLET = re.compile(r"^-\s+(.+?)\s*$")


@dataclass
class CatalogoParseado:
    version_fuente: str = ""
    fecha_fuente: str = ""
    direcciones: dict = field(default_factory=dict)     # categoria -> [entradas]
    auxiliares: dict = field(default_factory=dict)       # dimension -> [entradas]
    total_direcciones: int = 0
    total_auxiliares: int = 0

    def to_dict(self):
        return {
            "schema_version": "1.0",
            "fuente": "catalogo-maestro-v1.md",
            "version_fuente": self.version_fuente,
            "fecha_fuente": self.fecha_fuente,
            "generado_por": "catalog_parser.py — derivado automaticamente, no editar a mano",
            "direcciones": self.direcciones,
            "auxiliares": self.auxiliares,
            "total_direcciones": self.total_direcciones,
            "total_auxiliares": self.total_auxiliares,
        }


class CatalogParseError(ValueError):
    pass


def parse_catalogo(path=None):
    p = Path(path or CATALOGO_MD_PATH)
    if not p.is_file():
        raise CatalogParseError(f"catálogo maestro no encontrado: {p}")
    texto = p.read_text(encoding="utf-8")
    lineas = texto.splitlines()

    version_m = re.search(r"\*\*Versión:\*\*\s*(.+)", texto)
    fecha_m = re.search(r"\*\*Fecha:\*\*\s*(.+)", texto)

    direcciones = {v: [] for v in SECCIONES_DIRECCIONES.values()}
    auxiliares = {v: [] for v in SECCIONES_AUXILIARES.values()}

    seccion_actual = None
    modo_actual = None  # "direccion" | "auxiliar" | None
    for linea in lineas:
        m = RE_HEADER.match(linea)
        if m:
            numero, _titulo = m.group(1), m.group(2)
            if numero in SECCIONES_DIRECCIONES:
                seccion_actual = SECCIONES_DIRECCIONES[numero]
                modo_actual = "direccion"
            elif numero in SECCIONES_AUXILIARES:
                seccion_actual = SECCIONES_AUXILIARES[numero]
                modo_actual = "auxiliar"
            else:
                seccion_actual, modo_actual = None, None
            continue
        if linea.startswith("## ") or linea.startswith("# "):
            # cualquier encabezado de nivel superior cierra la subsección activa
            seccion_actual, modo_actual = None, None
            continue
        if modo_actual and seccion_actual:
            bm = RE_BULLET.match(linea)
            if bm:
                entrada = bm.group(1).strip()
                if entrada:
                    destino = direcciones if modo_actual == "direccion" else auxiliares
                    destino[seccion_actual].append(entrada)

    total_direcciones = sum(len(v) for v in direcciones.values())
    total_auxiliares = sum(len(v) for v in auxiliares.values())

    if total_direcciones < 100:
        raise CatalogParseError(
            f"parseo sospechoso: solo {total_direcciones} direcciones encontradas "
            "(se esperan cientos) — revisar el formato del .md antes de confiar en el JSON.")
    if any(len(v) == 0 for v in direcciones.values()):
        vacias = [k for k, v in direcciones.items() if not v]
        raise CatalogParseError(f"secciones de dirección sin ninguna entrada: {vacias}")
    if any(len(v) == 0 for v in auxiliares.values()):
        vacias = [k for k, v in auxiliares.items() if not v]
        raise CatalogParseError(f"secciones auxiliares sin ninguna entrada: {vacias}")

    return CatalogoParseado(
        version_fuente=(version_m.group(1).strip() if version_m else ""),
        fecha_fuente=(fecha_m.group(1).strip() if fecha_m else ""),
        direcciones=direcciones, auxiliares=auxiliares,
        total_direcciones=total_direcciones, total_auxiliares=total_auxiliares,
    )


def generar_json(path_md=None, path_json=None):
    """Parsea y escribe el JSON derivado. Devuelve el CatalogoParseado."""
    catalogo = parse_catalogo(path_md)
    destino = Path(path_json or CATALOGO_JSON_PATH)
    destino.write_text(json.dumps(catalogo.to_dict(), indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
    return catalogo


if __name__ == "__main__":
    c = generar_json()
    print(f"Direcciones: {c.total_direcciones} en {len(c.direcciones)} categorías.")
    for cat, entradas in c.direcciones.items():
        print(f"  {cat}: {len(entradas)}")
    print(f"Auxiliares: {c.total_auxiliares} en {len(c.auxiliares)} dimensiones.")
    for dim, entradas in c.auxiliares.items():
        print(f"  {dim}: {len(entradas)}")
    print(f"\nEscrito en {CATALOGO_JSON_PATH}")
