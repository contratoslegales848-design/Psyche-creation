"""Datos sinteticos para desarrollo. Imposibles de confundir con lo real.

Requisito 9 de la decision: implementar primero el esquema minimo usando datos
sinteticos en desarrollo. Dos riesgos que este modulo evita a proposito:

  1. Que un dato de prueba se cuele como contenido real. Por eso TODO lleva el
     prefijo `LM-SINTETICO-`, las fuentes apuntan a `example.invalid` (dominio
     reservado por RFC 2606: no resuelve, nunca sera de nadie) y los revisores
     son roles ficticios explicitos, nunca personas.
  2. Que el seed ensene al sistema a mentir. Ninguna pieza sintetica llega a
     PUBLISHED con datos inventados de publicacion real, y la unica que abre el
     gate lo hace con la conjuncion COMPLETA, para que se pueda probar que el
     camino feliz existe de verdad y no solo el rechazo.

Ninguna afirmacion juridica de este archivo es utilizable: son frases de
relleno marcadas como tales. Este modulo no es un banco de temas.
"""

import hashlib

PREFIJO = "LM-SINTETICO-"
DOMINIO_INVALIDO = "https://example.invalid"
AVISO = ("DATO SINTETICO DE DESARROLLO — no es una afirmacion juridica, "
         "no es citable, no es publicable")


def _hash(texto):
    """Hash real sobre el texto real: si el texto cambia, el hash cambia.

    Escribir un hash constante haria pasar la prueba del camino feliz sin
    demostrar nada, que es justo lo que la regla del hash existe para impedir.
    """
    return hashlib.sha256(str(texto).encode("utf-8")).hexdigest()


def pieza_bloqueada():
    """El caso normal HOY: investigacion pendiente, gate cerrado."""
    texto = f"{AVISO}. Frase de relleno A."
    return {
        "content_id": f"{PREFIJO}001",
        "version": 1,
        "titulo_de_trabajo": "Pieza sintetica bloqueada",
        "materia": "civil",
        "estado_agregado": "REQUIERE_INVESTIGACION",
        "gate_global_arte": "CERRADO",
        "capa_jurisdiccional": "NO_DETERMINADO",
        "contenido_hash_sha256": None,
        "publicacion": "NOT_PUBLISHED",
        "claims": [{
            "claim_id": f"{PREFIJO}001-claim-1",
            "texto_exacto": texto,
            "tipo": "definicion",
            "ubicacion": "descripcion_tema",
            "alcance": "NO_DETERMINADO",
            "jurisdiccion": [],
            "estado": "REQUIERE_INVESTIGACION",
            "gate_arte": "CERRADO",
            "revision_estado": "PENDIENTE",
            "fuentes": [{
                "fuente_id": f"{PREFIJO}001-src-1",
                "tipo_fuente": "SECUNDARIA_ESPECIALIZADA",
                "organismo_autor": "Organismo Sintetico de Pruebas",
                "titulo": "Documento sintetico sin valor juridico",
                "url": f"{DOMINIO_INVALIDO}/sintetico-1",
                "localizador": "seccion 1",
                "registro_oficial_id": None,
                "jurisdicciones_cubiertas": [],
                "origen_oficial_confirmado": False,
                "texto_exacto_consultado": False,
                "vigencia_comprobada": False,
                "fecha_comprobacion": None,
            }],
            "investigaciones": [{
                "hallazgo": f"{AVISO}. No se localizo texto oficial.",
                "metodo": "BUSQUEDA_WEB",
                "autor": "rol:investigador-sintetico",
            }],
        }],
        "derivadas": [],
    }


def pieza_con_gate_abierto():
    """El camino feliz COMPLETO: tres jurisdicciones, fuentes Nivel 1,
    aprobacion humana ligada por hash. Sirve para demostrar que el sistema
    tambien deja pasar lo que debe pasar, no solo que rechaza."""
    texto = f"{AVISO}. Frase de relleno B, sostenida por fuentes sinteticas."
    h = _hash(texto)
    fuente_base = {
        "tipo_fuente": "NORMA_OFICIAL",
        "origen_oficial_confirmado": True,
        "texto_exacto_consultado": True,
        "vigencia_comprobada": True,
        "fecha_comprobacion": "2026-09-01",
    }
    return {
        "content_id": f"{PREFIJO}002",
        "version": 1,
        "titulo_de_trabajo": "Pieza sintetica con gate abierto",
        "materia": "civil",
        "estado_agregado": "APTO_PARA_NARRATIVA",
        "gate_global_arte": "ABIERTO",
        "capa_jurisdiccional": "CAPA_A_TRANSVERSAL",
        "contenido_hash_sha256": h,
        "publicacion": "NOT_PUBLISHED",
        "claims": [{
            "claim_id": f"{PREFIJO}002-claim-1",
            "texto_exacto": texto,
            "tipo": "definicion",
            "ubicacion": "texto_imagen",
            "alcance": "CAPA_A_TRANSVERSAL",
            "jurisdiccion": ["Sinteticolandia", "Pruebalia", "Ficticia"],
            "estado": "APTO_PARA_NARRATIVA",
            "gate_arte": "ABIERTO",
            "revision_estado": "APROBADO",
            "revision_revisor": "rol:revisor-humano-sintetico",
            "revision_fecha": "2026-09-02T10:00:00Z",
            "revision_hash_sha256": h,
            "fuentes": [
                {**fuente_base, "fuente_id": f"{PREFIJO}002-src-1",
                 "organismo_autor": "Boletin Sintetico de Sinteticolandia",
                 "titulo": "Norma sintetica 1", "url": f"{DOMINIO_INVALIDO}/n1",
                 "localizador": "articulo 1", "registro_oficial_id": "sintetico-01",
                 "jurisdicciones_cubiertas": ["Sinteticolandia"]},
                {**fuente_base, "fuente_id": f"{PREFIJO}002-src-2",
                 "organismo_autor": "Diario Sintetico de Pruebalia",
                 "titulo": "Norma sintetica 2", "url": f"{DOMINIO_INVALIDO}/n2",
                 "localizador": "articulo 2", "registro_oficial_id": "sintetico-02",
                 "jurisdicciones_cubiertas": ["Pruebalia"]},
                {**fuente_base, "fuente_id": f"{PREFIJO}002-src-3",
                 "organismo_autor": "Gaceta Sintetica de Ficticia",
                 "titulo": "Norma sintetica 3", "url": f"{DOMINIO_INVALIDO}/n3",
                 "localizador": "articulo 3", "registro_oficial_id": "sintetico-03",
                 "jurisdicciones_cubiertas": ["Ficticia"]},
            ],
            "investigaciones": [{
                "hallazgo": f"{AVISO}. Tres textos sinteticos leidos.",
                "metodo": "LECTURA_TEXTO_OFICIAL",
                "autor": "rol:investigador-sintetico",
            }],
        }],
        "derivadas": [{
            "superficie": "WEB",
            "formato": "SOCIAL_1_1",
            "asset_sha256": _hash("asset sintetico"),
            "url_publicada": None,
            "publicada_en": None,
            "autorizacion_publicacion": "PENDIENTE",
        }],
    }


def piezas():
    """El seed completo. Ninguna llega a PUBLISHED: publicar es una decision
    humana externa, y un seed que la simule ensena al sistema a saltarsela."""
    return [pieza_bloqueada(), pieza_con_gate_abierto()]


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import fail_closed

    datos = piezas()
    for p in datos:
        motivos = fail_closed.revisar_pieza(p)
        marca = "OK" if not motivos else "RECHAZADA"
        print(f"[{marca}] {p['content_id']} — gate={p['gate_global_arte']}")
        for m in motivos:
            print(f"    ! {m}")
    print()
    print(json.dumps(datos, ensure_ascii=False, indent=2)[:400] + " ...")
