"""Auditoria de direccion de arte — lo comprobable del detalle artistico.

Por que existe
--------------
El pipeline ya sabia comprobar que una pieza esta autorizada, que el asset es un
PNG real, que el texto exacto no se altera y que la marca no se degrada a
watermark. No sabia comprobar nada de lo que hace que una pieza SE VEA BIEN:
que la escena no repita un recurso quemado, que haya UNA sola escuela, que
exista el mecanismo fisico que hace visible la idea, que el cuerpo de texto
respete el escalon aprobado, que el texto contraste de verdad con lo que tiene
debajo. Esos defectos no fallan ninguna prueba y arruinan igual la pieza.

Que NO es
---------
- No es criterio artistico. No elige escuela, ni metafora, ni encuadre: eso
  sigue siendo de la skill `legalmente-visual-system` y de una persona.
- No aprueba nada. El mejor desenlace de una auditoria es "sin bloqueos";
  jamas significa aprobado.
- No inventa reglas. Cada hallazgo cita el parametro de la politica visual que
  lo sostiene, y la politica a su vez cita la seccion de la skill de la que
  proviene. Si un dato no esta declarado, se dice que no se puede comprobar —
  no se supone cumplido ni incumplido.

Severidades
-----------
    BLOQUEA   contradice una prohibicion expresa (recurso quemado en la propia
              escena, dos escuelas en un prompt, texto sobre la marca).
    REVISION  no se puede afirmar que cumple, o incumple un parametro medible
              que admite decision humana (contraste, escalon, lineas).
    AVISO     preferencia declarada de la marca que conviene mirar.
"""

import unicodedata
from dataclasses import dataclass, field, asdict

BLOQUEA = "BLOQUEA"
REVISION = "REVISION_HUMANA"
AVISO = "AVISO"

ORDEN = {BLOQUEA: 0, REVISION: 1, AVISO: 2}


def normaliza(texto):
    """Compara conceptos, no cadenas: sin tildes, sin mayusculas, sin dobles espacios."""
    if not texto:
        return ""
    t = unicodedata.normalize("NFKD", str(texto).strip().lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(t.replace("-", " ").replace("_", " ").split())


@dataclass
class Hallazgo:
    codigo: str
    severidad: str
    mensaje: str
    fuente: str = ""

    def to_dict(self):
        return asdict(self)

    def __str__(self):
        return f"[{self.severidad}] {self.codigo}: {self.mensaje}"


@dataclass
class ArtDirectionReport:
    hallazgos: list = field(default_factory=list)
    comprobado: list = field(default_factory=list)   # que se pudo comprobar de verdad
    no_comprobable: list = field(default_factory=list)

    @property
    def bloqueos(self):
        return [h for h in self.hallazgos if h.severidad == BLOQUEA]

    @property
    def revisiones(self):
        return [h for h in self.hallazgos if h.severidad == REVISION]

    @property
    def avisos(self):
        return [h for h in self.hallazgos if h.severidad == AVISO]

    @property
    def sin_bloqueos(self):
        """No hay prohibicion contradicha. NO significa aprobado: nada lo significa."""
        return not self.bloqueos

    def motivos(self):
        """Lineas para el receipt, ordenadas por severidad."""
        return [str(h) for h in sorted(self.hallazgos, key=lambda h: (ORDEN[h.severidad], h.codigo))]

    def to_dict(self):
        return {
            "hallazgos": [h.to_dict() for h in sorted(
                self.hallazgos, key=lambda h: (ORDEN[h.severidad], h.codigo))],
            "bloqueos": len(self.bloqueos),
            "revisiones": len(self.revisiones),
            "avisos": len(self.avisos),
            "comprobado": list(self.comprobado),
            "no_comprobable": list(self.no_comprobable),
            "sin_bloqueos": self.sin_bloqueos,
            "nota": "una auditoria sin bloqueos no es una aprobacion: la aprobacion visual es humana.",
        }


def _añade(rep, codigo, severidad, mensaje, fuente=""):
    rep.hallazgos.append(Hallazgo(codigo, severidad, mensaje, fuente))


def _texto_del_brief(brief):
    """Todo lo que describe la escena POSITIVAMENTE. El prompt negativo no cuenta:
    si la escena pide una balanza, la prohibicion no la quita."""
    campos = ("subject", "environment", "focal_point", "metaphor", "mecanismo_revelacion",
              "key_light", "negative_space", "escuela")
    partes = [str(getattr(brief, c, "") or "") for c in campos]
    partes += [str(x) for x in (getattr(brief, "constraints", None) or [])]
    return normaliza(" | ".join(partes))


# --------------------------------------------------------------- brief

def auditar_brief(brief, policy, family=None, memoria_reciente=()):
    """Audita la direccion de arte ANTES de gastar una sola llamada al proveedor."""
    rep = ArtDirectionReport()
    da = policy.data.get("direccion_de_arte", {})
    escena = _texto_del_brief(brief)

    # 1. Recursos quemados EN LA PROPIA ESCENA.
    terminos = da.get("recursos_quemados_terminos", {}) or {}
    for termino in terminos.get("bloqueantes", []):
        if normaliza(termino) in escena:
            _añade(rep, "RECURSO_QUEMADO_EN_LA_ESCENA", BLOQUEA,
                   f"la escena descrita contiene un recurso quemado: {termino!r}. Prohibirlo en el "
                   "prompt negativo no lo impide, porque la descripcion positiva manda.",
                   "direccion_de_arte.recursos_quemados (skill §5)")
    for termino in terminos.get("dudosos", []):
        if normaliza(termino) in escena:
            _añade(rep, "RECURSO_GASTADO_DUDOSO", REVISION,
                   f"la escena usa un recurso gastado del feed historico: {termino!r}. Puede ser "
                   "legitimo, pero lo decide una persona.",
                   "direccion_de_arte.recursos_quemados (skill §5)")
    rep.comprobado.append("recursos quemados en la descripcion positiva")

    # 2. Una sola escuela, declarada y viva.
    if da.get("una_escuela_por_pieza"):
        if not str(getattr(brief, "escuela", "") or "").strip():
            _añade(rep, "ESCUELA_NO_DECLARADA", REVISION,
                   "el brief no declara escuela artistica: no se puede comprobar la regla de UNA "
                   "escuela por pieza ni la rotacion. Sin escuela declarada el generador promedia.",
                   "direccion_de_arte.una_escuela_por_pieza (skill §4)")
            rep.no_comprobable.append("rotacion de escuela")
        else:
            rep.comprobado.append("escuela declarada")
            ventana = int(da.get("ventana_no_repetir_escuela", 5))
            # Una sola implementacion de la regla: la de rotation.py.
            from rotation import verificar_rotacion_de_escuela
            check = verificar_rotacion_de_escuela(brief.escuela, memoria_reciente, ventana)
            if check.repetida:
                _añade(rep, "ESCUELA_REPETIDA_EN_VENTANA", REVISION,
                       check.detalle + " La rotacion existe para que el feed no se aplane.",
                       "direccion_de_arte.ventana_no_repetir_escuela (skill §4)")
            carril_escuela = policy.carril_de(brief.escuela)
            carril_familia = getattr(family, "carril", "") if family is not None else ""
            if carril_escuela and carril_familia and carril_escuela != carril_familia:
                _añade(rep, "CARRILES_MEZCLADOS", REVISION,
                       f"la escuela pertenece al carril {carril_escuela} y la familia visual al "
                       f"carril {carril_familia}. Mezclar carriles en una misma serie rompe la "
                       "coherencia del feed.",
                       "escuelas.nota_carriles (skill §4)")

    # 3. El argumento visual.
    if da.get("mecanismo_revelacion_requerido"):
        if not str(getattr(brief, "mecanismo_revelacion", "") or "").strip():
            _añade(rep, "SIN_MECANISMO_DE_REVELACION", REVISION,
                   "no se declara el fenomeno fisico que hace visible la idea (luz que cruza una "
                   "grieta, tinta que se seca, sedimento que se asienta). Sin el, la pieza ilustra "
                   "objetos en vez de argumentar.",
                   "direccion_de_arte.mecanismo_revelacion_requerido (skill §5.3)")
            rep.no_comprobable.append("mecanismo de revelacion")
        else:
            rep.comprobado.append("mecanismo de revelacion declarado")

    # 4. Escenario: sacar la escena del despacho.
    if da.get("escenario_cotidiano_preferido"):
        entorno = normaliza(getattr(brief, "environment", ""))
        gastados = [g for g in da.get("entornos_juridicos_gastados", []) if normaliza(g) in entorno]
        if gastados:
            alternativas = list(getattr(family, "everyday_environments", ()) or ())
            sugerencia = (" Alternativas cotidianas de esta familia: "
                          + ", ".join(alternativas) + ".") if alternativas else ""
            _añade(rep, "ENTORNO_JURIDICO_GASTADO", AVISO,
                   f"el entorno vuelve al escenario juridico ({', '.join(gastados)}). Sacar la "
                   "escena del despacho es lo que mas diferencia una pieza de otra." + sugerencia,
                   "direccion_de_arte.escenario_cotidiano_preferido (skill §5.2)")

    # 5. Presencia humana.
    ph = da.get("presencia_humana", {}) or {}
    prohibidos = [p for p in ph.get("prohibido_sin_justificacion", []) if normaliza(p) in escena]
    if prohibidos and not str(getattr(brief, "justificacion_presencia_humana", "") or "").strip():
        _añade(rep, "PRESENCIA_HUMANA_SIN_JUSTIFICAR", BLOQUEA,
               f"la escena incluye {', '.join(prohibidos)} sin justificacion declarada. Por defecto "
               "la presencia humana es objeto, gesto o rastro.",
               "direccion_de_arte.presencia_humana (skill §5)")

    # 6. Superficie de marca: no repetir siempre el sello de lacre.
    marca = policy.data.get("marca", {})
    if marca.get("evitar_superficie_repetida") and getattr(brief, "marca_superficie", ""):
        ventana = int(marca.get("ventana_no_repetir_superficie", 5))
        recientes = [normaliza(getattr(e, "brand_surface", "")) for e in list(memoria_reciente)[-ventana:]]
        if normaliza(brief.marca_superficie) in [r for r in recientes if r]:
            _añade(rep, "SUPERFICIE_DE_MARCA_REPETIDA", AVISO,
                   f"la superficie de marca {brief.marca_superficie!r} se repite dentro de las "
                   f"ultimas {ventana} piezas; el objeto de integracion tambien rota.",
                   "marca.evitar_superficie_repetida (skill §5.4)")

    # 7. ¿Tiene la familia detalle que aportar?
    if family is not None and not getattr(family, "tiene_detalle_artistico", False):
        _añade(rep, "FAMILIA_SIN_DETALLE_ARTISTICO", AVISO,
               f"la familia {getattr(family, 'name', '')!r} no declara profundidad de campo, "
               "acabado ni curva de contraste: el prompt saldra sin detalle de ejecucion.",
               "registro de familias >= 1.1")

    # 8. Fuente de luz unica y justificada.
    luz = da.get("fuente_de_luz", {}) or {}
    if luz.get("unica"):
        declarada = str(getattr(brief, "key_light", "") or "")
        heredada = getattr(family, "lighting_intent", "") if family is not None else ""
        if not declarada and not heredada:
            _añade(rep, "SIN_CLAVE_DE_LUZ", REVISION,
                   "no hay clave de luz ni en el brief ni en la familia: el nucleo de marca exige "
                   "una sola fuente dramatica justificada dentro de la escena.",
                   "direccion_de_arte.fuente_de_luz (skill §3)")
            rep.no_comprobable.append("clave de luz")

    return rep


# ---------------------------------------------------------- tipografia

def auditar_tipografia(plan, policy, exact_copy=""):
    """Audita el PLAN tipografico contra los parametros aprobados."""
    rep = ArtDirectionReport()
    if plan is None:
        rep.no_comprobable.append("tipografia (la pieza no lleva texto compuesto)")
        return rep

    tip = policy.data.get("tipografia", {})
    quote = next((b for b in plan.blocks if b.role == "QUOTE"), None)

    if quote is not None:
        piso = int(getattr(quote, "min_size_px", 0) or 0)
        if piso and quote.size_px < piso:
            _añade(rep, "CUERPO_BAJO_EL_ESCALON", REVISION,
                   f"el bloque principal quedo a {quote.size_px}px, por debajo del minimo "
                   f"aprobado para su longitud ({piso}px).",
                   "tipografia.escalones_principal (skill §6)")
        max_lineas = int(getattr(plan, "max_lineas", 0) or tip.get("max_lineas", 0) or 0)
        if max_lineas and len(quote.lines) > max_lineas:
            _añade(rep, "EXCEDE_MAXIMO_DE_LINEAS", REVISION,
                   f"{len(quote.lines)} lineas frente a un maximo aprobado de {max_lineas}. "
                   "La salida no es encoger la letra: es dividir la pieza o acortar el texto EN LA "
                   "FUENTE, con verificacion juridica de nuevo.",
                   "tipografia.max_lineas (skill §6)")
        from composition import es_huerfana
        if es_huerfana(quote.lines):
            _añade(rep, "LINEA_HUERFANA", AVISO,
                   "la ultima linea del bloque principal queda con una sola palabra.",
                   "tipografia.prohibido_huerfana_de_una_palabra")
        escalones = tip.get("escalones_principal") or []
        tope = int(escalones[-1]["max_caracteres"]) if escalones else 0
        if tope and len(quote.text) > tope:
            _añade(rep, "COPIA_FUERA_DE_TABLA", REVISION,
                   f"el texto tiene {len(quote.text)} caracteres y la tabla tipografica aprobada "
                   f"llega a {tope}. Fuera de tabla no hay cuerpo minimo aprobado.",
                   "tipografia.nota_fuera_de_tabla (skill §6)")
        rep.comprobado.append("escalon, lineas y reparto del bloque principal")

    if getattr(plan, "safe_area_origen", "") == "ratio_por_defecto":
        _añade(rep, "ZONA_SEGURA_NO_MEDIDA", AVISO,
               "este formato no tiene zona segura medida en el feed: se uso el margen proporcional "
               "por defecto. Lo que se recorta en esta relacion de aspecto no esta comprobado.",
               "tipografia.nota_zona_segura")
        rep.no_comprobable.append("zona segura real del feed")

    from composition import zona_visible_tras_recorte
    visible = zona_visible_tras_recorte(plan.canvas[0], plan.canvas[1], policy)
    if visible:
        sx, sy, sw, sh = plan.safe_area
        if not (sx >= visible[0] and sy >= visible[1]
                and sx + sw <= visible[2] and sy + sh <= visible[3]):
            _añade(rep, "TEXTO_FUERA_DE_LA_ZONA_VISIBLE", BLOQUEA,
                   "el area de texto se sale de la banda que el feed deja ver: parte de la pieza "
                   "se publicaria recortada.",
                   "formatos.zona_visible_tras_recorte (skill §6)")
        else:
            rep.comprobado.append("area de texto dentro de la banda visible del feed")
    return rep


# --------------------------------------------------------- composicion

CODIGOS_COMPOSICION = {
    "TEXT_CONTRAST_BELOW_MINIMUM": (
        REVISION, "el texto no alcanza el contraste minimo sobre el fondo real. Prohibido "
                  "resolverlo con una caja opaca: se resuelve con la luz de la escena."),
    "TEXT_OVER_BRAND_SURFACE": (
        BLOQUEA, "hay texto sobre el objeto de marca; la regla vigente lo prohibe."),
    "BRAND_CONTRAST_BELOW_MINIMUM": (
        REVISION, "la marca no se lee sobre la superficie elegida."),
    "BRAND_SURFACE_OUTSIDE_VISIBLE_AREA": (
        REVISION, "la superficie de marca puede quedar recortada por el feed."),
    "BRAND_SURFACE_NOT_DECLARED": (
        REVISION, "no se declaro superficie reservada: la marca no se compuso."),
    "BRAND_SURFACE_NOT_FLAT": (
        REVISION, "el plano de la marca no es utilizable: o la superficie se declaro no plana sin "
                  "dar sus cuatro esquinas, o las esquinas dadas no describen un plano. No se "
                  "inventa una perspectiva."),
    "BRAND_DOES_NOT_FIT": (
        REVISION, "la marca no cabe en la superficie reservada."),
    "BRAND_DELEGATED_TO_GENERATOR": (
        BLOQUEA, "se delego la marca al generador, contra la decision vigente."),
}


def auditar_composicion(resultado, policy):
    """Traduce las medidas reales del compositor a hallazgos de direccion de arte."""
    rep = ArtDirectionReport()
    if resultado is None:
        rep.no_comprobable.append("composicion (no se compuso la pieza)")
        return rep

    for codigo in getattr(resultado, "reason_codes", ()) or ():
        sev, mensaje = CODIGOS_COMPOSICION.get(codigo, (REVISION, "codigo de composicion no mapeado."))
        _añade(rep, codigo, sev, mensaje, "compositor (medida real sobre pixels)")

    medidas = getattr(resultado, "text_contrast", {}) or {}
    if medidas:
        rep.comprobado.append(
            "contraste real bajo el texto: "
            + ", ".join(f"{rol} min {m['min']}:1" for rol, m in sorted(medidas.items())))
    else:
        rep.no_comprobable.append("contraste del texto (no hubo bloques medidos)")
    return rep


# ------------------------------------------------------------- union

def auditar(brief=None, policy=None, family=None, memoria_reciente=(),
            typography_plan=None, composition_result=None, exact_copy=""):
    """Auditoria completa. Une lo que haya disponible; nunca supone lo ausente."""
    if policy is None:
        raise ValueError("la auditoria de arte necesita la politica visual vigente.")
    total = ArtDirectionReport()
    for parcial in (
        auditar_brief(brief, policy, family, memoria_reciente) if brief is not None else None,
        auditar_tipografia(typography_plan, policy, exact_copy) if typography_plan is not None else None,
        auditar_composicion(composition_result, policy) if composition_result is not None else None,
    ):
        if parcial is None:
            continue
        total.hallazgos.extend(parcial.hallazgos)
        total.comprobado.extend(parcial.comprobado)
        total.no_comprobable.extend(parcial.no_comprobable)
    return total
