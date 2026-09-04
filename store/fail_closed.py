"""Guardian de escritura del almacen. Niega; nunca concede.

Por que existe si la migracion ya tiene restricciones: porque las
restricciones de la base de datos protegen la base de datos, y este modulo
protege el PASO ANTERIOR — decidir que se envia. Una fila rechazada por
Postgres ya viajo, ya se intento, y su mensaje de error es de Postgres, no del
dominio. Aqui se rechaza antes, con el vocabulario del proyecto.

Las dos barreras dicen lo mismo a proposito. Si alguna vez discrepan, la
discrepancia es el fallo: hay una prueba que compara ambas listas de campos
obligatorios.

Este modulo NO decide si algo esta aprobado. Eso lo decide
`scripts/validate-claim-packet.py` y un humano. Aqui solo se comprueba que lo
que se pretende registrar como aprobado llega COMPLETO: sin fuente, sin
jurisdiccion, sin hash, sin claim, sin evidencia, sin aprobacion humana o sin
el estado exigido, la escritura se rechaza.
"""

import re

HEX64 = re.compile(r"^[0-9a-f]{64}$")

ESTADOS_CLAIM = {"REQUIERE_INVESTIGACION", "APTO_CON_MATICES", "APTO_PARA_NARRATIVA",
                 "PENDIENTE_APROBACION_HUMANA", "BLOQUEADO"}
ALCANCES = {"CAPA_A_TRANSVERSAL", "CAPA_B_VARIABLE", "CAPA_C_NACIONAL",
            "NO_DETERMINADO", "NO_APLICA"}
GATES = {"CERRADO", "ABIERTO"}
REVISION = {"PENDIENTE", "APROBADO", "RECHAZADO"}
TIPOS_FUENTE_OFICIAL = {"NORMA_OFICIAL", "JURISPRUDENCIA_OFICIAL",
                        "AUTORIDAD_PUBLICA_OFICIAL"}

# Minimo de jurisdicciones para sostener Capa A. Mismo numero que
# content/topics/transversality.py: si alli cambia, aqui tambien.
MINIMO_JURISDICCIONES_CAPA_A = 3

# Campos sin los cuales una aprobacion humana no es verificable. Se comparan
# contra la restriccion `aprobacion_completa` de la migracion en las pruebas.
CAMPOS_APROBACION = ("revision_revisor", "revision_fecha", "revision_hash_sha256")


class EscrituraRechazada(Exception):
    """Lleva TODOS los motivos, no solo el primero: quien corrige la fila
    necesita ver la lista entera, no descubrirla de uno en uno."""

    def __init__(self, motivos):
        self.motivos = list(motivos)
        super().__init__("; ".join(self.motivos))


def _vacio(valor):
    return valor is None or not str(valor).strip()


def revisar_fuente(fuente):
    m = []
    if _vacio(fuente.get("fuente_id")):
        m.append("la fuente no declara fuente_id")
    tipo = fuente.get("tipo_fuente")
    if _vacio(fuente.get("organismo_autor")):
        m.append(f"{fuente.get('fuente_id')}: sin organismo_autor identificable")
    if tipo in TIPOS_FUENTE_OFICIAL and _vacio(fuente.get("localizador")):
        m.append(f"{fuente.get('fuente_id')}: fuente oficial sin localizador concreto "
                 "(la ley entera no sostiene una afirmacion sobre un articulo)")
    if tipo in TIPOS_FUENTE_OFICIAL and _vacio(fuente.get("registro_oficial_id")):
        m.append(f"{fuente.get('fuente_id')}: fuente oficial sin registro_oficial_id "
                 "(el organismo no esta en el registro oficial cerrado)")
    marcada = any(bool(fuente.get(c)) for c in
                  ("origen_oficial_confirmado", "texto_exacto_consultado", "vigencia_comprobada"))
    if marcada and _vacio(fuente.get("fecha_comprobacion")):
        m.append(f"{fuente.get('fuente_id')}: dice 'comprobado' sin fecha_comprobacion")
    return m


def es_nivel_1(fuente):
    """Nivel 1: los tres booleanos y, si es oficial, entrada en el registro."""
    if not (fuente.get("origen_oficial_confirmado")
            and fuente.get("texto_exacto_consultado")
            and fuente.get("vigencia_comprobada")):
        return False
    if fuente.get("tipo_fuente") in TIPOS_FUENTE_OFICIAL:
        return not _vacio(fuente.get("registro_oficial_id"))
    return True


def revisar_claim(claim):
    m = []
    cid = claim.get("claim_id") or "<sin claim_id>"
    if _vacio(claim.get("claim_id")):
        m.append("el claim no declara claim_id")
    if _vacio(claim.get("texto_exacto")):
        m.append(f"{cid}: sin texto_exacto")

    estado = claim.get("estado")
    if estado not in ESTADOS_CLAIM:
        m.append(f"{cid}: estado invalido {estado!r}")

    alcance = claim.get("alcance")
    if alcance not in ALCANCES:
        m.append(f"{cid}: alcance invalido {alcance!r}")

    jurisdicciones = [j for j in (claim.get("jurisdiccion") or []) if str(j).strip()]
    if alcance == "CAPA_C_NACIONAL" and not jurisdicciones:
        m.append(f"{cid}: CAPA_C_NACIONAL sin jurisdiccion declarada "
                 "(falsa universalizacion esperando a ocurrir)")
    if alcance == "CAPA_A_TRANSVERSAL" and len(jurisdicciones) < MINIMO_JURISDICCIONES_CAPA_A:
        m.append(f"{cid}: CAPA_A_TRANSVERSAL con {len(jurisdicciones)} jurisdiccion(es); "
                 f"el minimo comparado es {MINIMO_JURISDICCIONES_CAPA_A}")

    fuentes = claim.get("fuentes") or []
    if not fuentes:
        m.append(f"{cid}: sin ninguna fuente")
    for f in fuentes:
        m.extend(revisar_fuente(f))

    if estado == "APTO_PARA_NARRATIVA" and not any(es_nivel_1(f) for f in fuentes):
        m.append(f"{cid}: APTO_PARA_NARRATIVA sin ninguna fuente de Nivel 1")

    rev = claim.get("revision_estado", "PENDIENTE")
    if rev not in REVISION:
        m.append(f"{cid}: revision_estado invalido {rev!r}")
    if rev == "APROBADO":
        faltan = [c for c in CAMPOS_APROBACION if _vacio(claim.get(c))]
        if faltan:
            m.append(f"{cid}: aprobacion humana incompleta, falta {', '.join(faltan)}")
        h = claim.get("revision_hash_sha256")
        if h and not HEX64.match(str(h)):
            m.append(f"{cid}: revision_hash_sha256 no es sha256 hexadecimal de 64 caracteres")

    gate = claim.get("gate_arte", "CERRADO")
    if gate not in GATES:
        m.append(f"{cid}: gate_arte invalido {gate!r}")
    if gate == "ABIERTO" and not (
            estado == "APTO_PARA_NARRATIVA" and rev == "APROBADO"
            and not _vacio(claim.get("revision_hash_sha256"))):
        m.append(f"{cid}: gate_arte ABIERTO sin la conjuncion exigida "
                 "(APTO_PARA_NARRATIVA + revision APROBADO + hash del contenido aprobado)")
    return m


def revisar_pieza(pieza):
    """Todos los motivos por los que esta pieza NO puede escribirse. [] = puede."""
    m = []
    if _vacio(pieza.get("content_id")):
        m.append("la pieza no declara content_id")
    if _vacio(pieza.get("titulo_de_trabajo")):
        m.append("la pieza no declara titulo_de_trabajo")
    if _vacio(pieza.get("materia")):
        m.append("la pieza no declara materia")

    h = pieza.get("contenido_hash_sha256")
    if h is not None and not HEX64.match(str(h)):
        m.append("contenido_hash_sha256 no es sha256 hexadecimal de 64 caracteres")

    claims = pieza.get("claims") or []
    if not claims:
        m.append("la pieza no tiene ningun claim (nada que sostenga lo que afirma)")
    for c in claims:
        m.extend(revisar_claim(c))

    gate_global = pieza.get("gate_global_arte", "CERRADO")
    if gate_global not in GATES:
        m.append(f"gate_global_arte invalido {gate_global!r}")
    if gate_global == "ABIERTO":
        if _vacio(h):
            m.append("gate_global_arte ABIERTO sin contenido_hash_sha256")
        cerrados = [c.get("claim_id") for c in claims if c.get("gate_arte") != "ABIERTO"]
        if cerrados:
            m.append("gate_global_arte ABIERTO con claims de gate CERRADO: "
                     f"{', '.join(str(x) for x in cerrados)} "
                     "(el techo de la pieza es el minimo de sus claims, no el maximo)")

    if pieza.get("publicacion") == "PUBLISHED":
        derivadas = pieza.get("derivadas") or []
        if not any(d.get("publicada_en") for d in derivadas):
            m.append("pieza marcada PUBLISHED sin ninguna derivada publicada")
        for d in derivadas:
            if d.get("publicada_en"):
                if d.get("autorizacion_publicacion") != "AUTORIZADA":
                    m.append("derivada publicada sin autorizacion humana AUTORIZADA")
                if _vacio(d.get("autorizacion_responsable")) or _vacio(d.get("autorizacion_fecha")):
                    m.append("derivada publicada sin responsable y fecha de autorizacion")
                if _vacio(d.get("url_publicada")):
                    m.append("derivada publicada sin url_publicada (no es trazable)")
    return m


def asegurar_escribible(pieza):
    """Lanza EscrituraRechazada con TODOS los motivos, o devuelve la pieza."""
    motivos = revisar_pieza(pieza)
    if motivos:
        raise EscrituraRechazada(motivos)
    return pieza
