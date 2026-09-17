"""Prompt compiler V2 — deterministico, versionado y explicable.

El prompt es una SALIDA del sistema, no una entrada manual. Devuelve una
estructura (CompiledVisualRequest), no solo una cadena: una cadena sola
destruiria la trazabilidad.

Entradas: VisualBrief + VisualPolicy + VisualFamily + VisualMemory +
ProviderCapabilities. Salida: prompt, restricciones negativas, parametros,
metadata y una explicacion legible de POR QUE esta peticion y no otra.
"""

import hashlib
from dataclasses import dataclass, field, asdict

import safe_zone as sz
from composition import build_brand_plan
from plan import canonical_hash
from providers.base import GENERATION_MODE_TEXT_TO_IMAGE

COMPILER_VERSION = "2.1"


@dataclass
class CompiledVisualRequest:
    positive_prompt: str
    negative_constraints: list = field(default_factory=list)
    requested_aspect_ratio: str = ""
    requested_dimensions: tuple = ()
    composition_intent: str = ""
    visual_family: str = ""
    lighting_intent: str = ""
    text_mode: str = ""
    brand_mode: str = ""
    brand_plan: dict = field(default_factory=dict)
    provider_parameters: dict = field(default_factory=dict)
    explanation: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    # Contrato de salida text-to-image vs. image-edit (Hotfix, 16-sep-2026):
    # compile_request() no tiene ni tendrá aquí una vía de edición — sólo
    # compone piezas nuevas desde cero. generation_mode es SIEMPRE
    # TEXT_TO_IMAGE en este compilador; los otros tres campos existen para
    # que el contrato sea el mismo objeto que consume pipeline.py, nunca se
    # heredan de una generación anterior. Ver
    # docs/contrato-generacion-imagenes-legalmente.md.
    generation_mode: str = GENERATION_MODE_TEXT_TO_IMAGE
    source_image: bytes = None
    reference_images: tuple = ()
    edit_instruction: str = None
    # Safe zone multiformato 9:16 -> 4:5 (tarea 78, 17-sep-2026): informativo,
    # mismo patrón que `brand_plan`/`explanation` — nunca bloquea la
    # compilación por sí solo (heurística de texto declarado, no visión por
    # computadora: puede tener falsos positivos, ver safe_zone.py). Quien
    # orquesta (QA de lote, demo, gate humano) decide qué hacer con
    # `crop_safe_4_5_ok=False`, igual que con `memoria_fuerte_ok`.
    crop_safe_4_5_ok: bool = True
    crop_safe_4_5_detalle: dict = field(default_factory=dict)

    @property
    def negative_prompt(self):
        return ", ".join(self.negative_constraints)

    def to_dict(self):
        return asdict(self)

    def request_hash(self):
        return canonical_hash({
            "p": self.positive_prompt,
            "n": self.negative_constraints,
            "ar": self.requested_aspect_ratio,
            "d": list(self.requested_dimensions),
            "t": self.text_mode,
            "b": self.brand_mode,
            "gm": self.generation_mode,
        })


def _paleta_texto(policy, fingerprint=None):
    """La paleta de la ESCENA la aporta la huella visual (catalogo maestro,
    Fase 4/8 del mandato Superprompt) cuando hay una. Sin huella, se cae a la
    paleta de marca como referencia orientativa -- ya no como obligacion de
    4 colores fija repetida en cada pieza (Hallazgo 2 de la auditoria)."""
    if fingerprint is not None and fingerprint.palette:
        return fingerprint.palette
    ref = policy.data.get("paleta", {}).get("marca_de_referencia", {})
    if not ref:
        return ""
    return "; ".join(f"{k.replace('_', ' ')} ({', '.join(v)})" for k, v in ref.items())


def _direccion_artistica_texto(fingerprint):
    """Dimensiones del catalogo maestro (Fase 4) que no tienen ya una frase
    propia (paleta y lighting se tratan aparte)."""
    partes = [f"Direccion artistica: {fingerprint.primary_direction}"]
    if fingerprint.secondary_direction:
        partes.append(f" con acento de {fingerprint.secondary_direction}")
    partes.append(f". Medio: {fingerprint.medium.replace('_', ' ')}.")
    if fingerprint.composition:
        partes.append(f" Composicion: {fingerprint.composition}.")
    if fingerprint.camera_optics:
        partes.append(f" Optica: {fingerprint.camera_optics}.")
    if fingerprint.materiality:
        partes.append(f" Materialidad: {fingerprint.materiality}.")
    if fingerprint.realism:
        partes.append(f" Nivel de realismo: {fingerprint.realism}.")
    if fingerprint.visual_mechanism:
        partes.append(f" Mecanismo visual: {fingerprint.visual_mechanism}.")
    return "".join(partes)


def compile_request(brief, policy, family=None, capabilities=None, repetition=None, fingerprint=None):
    """Compila la peticion visual. Lanza ValueError si el brief no valida."""
    errores = brief.validate(policy)
    if errores:
        raise ValueError("brief invalido:\n- " + "\n- ".join(errores))

    fmt = policy.formato(brief.formato)
    comp = policy.data.get("composicion", {})
    explicacion = []

    # Safe zone multiformato 9:16 -> 4:5 (tarea 78): sólo se calcula/instruye
    # cuando el formato pedido declara `crop_safe_for` en la política — nunca
    # se fuerza sobre un formato que el Founder pidió explícitamente distinto.
    safe_zone_geometria = None
    if fmt.get("crop_safe_for"):
        safe_zone_geometria = sz.calcular_geometria(policy, formato_maestro=brief.formato)
        explicacion.append(
            f"safe zone: {brief.formato!r} declara crop_safe_for={fmt['crop_safe_for']!r}; "
            f"área segura entre px {safe_zone_geometria.safe_top} y "
            f"{safe_zone_geometria.safe_bottom} desde arriba.")
    crop_safe_ok, crop_safe_reasons, crop_safe_detalle = sz.crop_safe_4_5(
        brief, policy=policy, geometria=safe_zone_geometria)
    if not crop_safe_ok:
        explicacion.extend(f"safe zone 4:5: {r}" for r in crop_safe_reasons)

    partes = [
        f"Una sola escena. {brief.subject}.",
        f"Entorno: {brief.environment}.",
        f"Camara: {brief.camera}. Punto focal: {brief.focal_point}.",
        f"Familia visual: {brief.visual_family.replace('_', ' ')}.",
    ]
    explicacion.append(f"familia visual: {brief.visual_family}")

    if safe_zone_geometria is not None:
        partes.append(sz.instruccion_compilada(safe_zone_geometria))

    if fingerprint is not None:
        partes.append(_direccion_artistica_texto(fingerprint))
        explicacion.append(
            f"direccion artistica (huella {fingerprint.content_id}): "
            f"{fingerprint.primary_direction} / medio: {fingerprint.medium}")
        explicacion.extend(fingerprint.explanation)

    lighting = brief.key_light or ""
    if not lighting and fingerprint is not None and fingerprint.lighting:
        lighting = fingerprint.lighting
        explicacion.append(f"luz tomada de la huella: {fingerprint.lighting}")
    if family is not None:
        if not lighting:
            lighting = family.lighting_intent
            explicacion.append(f"luz tomada de la familia: {family.lighting_intent}")
        if family.material_vocabulary:
            partes.append("Vocabulario material: " + ", ".join(family.material_vocabulary) + ".")

    if brief.metaphor:
        partes.append(f"Metafora visual: {brief.metaphor}.")
    if brief.negative_space:
        partes.append(f"Espacio negativo reservado: {brief.negative_space}.")
    partes.append(
        f"Luz: {lighting or 'clave definida'}. Intencion de luminosidad: "
        f"{brief.brightness_intent or 'legible, sin empastar los negros'}."
    )
    if brief.brightness_intent:
        explicacion.append(f"luminosidad: {brief.brightness_intent}")

    paleta_texto = _paleta_texto(policy, fingerprint=fingerprint)
    if paleta_texto:
        partes.append(f"Paleta: {paleta_texto}.")
    if brief.acento_objeto:
        # Prompt compacto (recuperación motor anterior, tarea 78 continuación):
        # antes se repetía `paleta_texto` completo aquí de nuevo ("El acento
        # de color (X) debe proceder..." justo después de "Paleta: X.") —
        # misma información, el doble de texto. Se refiere a la paleta ya
        # declarada en vez de repetirla verbatim.
        referencia_paleta = ("esa misma paleta" if paleta_texto
                             else "un tono coherente con la direccion artistica declarada")
        partes.append(
            f"El acento de color ({referencia_paleta}) debe proceder de un objeto fisico real de la "
            f"escena: {brief.acento_objeto}."
        )

    # --- marca: la politica manda, el brief pide ---
    brand_plan = build_brand_plan(policy, brief.marca_superficie,
                                  requested_generator_text=brief.marca_texto_en_imagen)
    if brand_plan.required:
        if brand_plan.generator_writes_text:
            partes.append(
                f"La palabra '{brand_plan.text}' aparece grabada fisicamente en "
                f"{brief.marca_superficie}, respetando perspectiva, material, reflejo, luz y desgaste."
            )
            brand_mode = "GENERATOR_TEXT"
        else:
            partes.append(
                f"La escena incluye {brief.marca_superficie} con una superficie de marca reservada y "
                "COMPLETAMENTE VACIA (relieve, perspectiva, material y luz correctos para que algo se "
                "lea ahi, pero SIN NINGUN CARACTER). La marca se compone despues."
            )
            brand_mode = "POST_COMPOSITE"
            explicacion.append(
                f"marca: superficie {brief.marca_superficie} reservada; texto del generador desactivado")
        if brand_plan.coercion_note:
            explicacion.append("marca: " + brand_plan.coercion_note)
    else:
        brand_mode = "NONE"

    if brief.constraints:
        partes.append("Restricciones: " + "; ".join(brief.constraints) + ".")

    prompt = " ".join(partes)

    # --- negativos ---
    negativos = list(comp.get("prohibido", []))
    negativos += list(policy.data.get("paleta", {}).get("prohibida", []))
    negativos += list(policy.data.get("marca", {}).get("prohibido", []))
    negativos += list(brief.negative_constraints)
    if family is not None:
        negativos += [f"tropo gastado: {t}" for t in family.forbidden_tropes]
    if brief.text_rendering_mode != "NATIVE_TEXT":
        negativos += ["texto", "letras", "tipografia", "numeracion", "firma", "subtitulos"]

    if repetition is not None and repetition.evitar:
        negativos += [f"repetir: {e}" for e in repetition.evitar]
        explicacion.extend(f"repeticion: {r}" for r in repetition.razones)
        explicacion.append(f"riesgo de repeticion: {repetition.nivel} ({repetition.score}/100)")

    vistos, negs = set(), []
    for n in negativos:
        if n not in vistos:
            vistos.add(n)
            negs.append(n)

    # --- parametros ---
    parametros = {
        "width": fmt["width"], "height": fmt["height"],
        "aspect_ratio": fmt["aspect_ratio"], "full_bleed": fmt.get("full_bleed", True),
        "content_id": brief.content_id,
    }
    if capabilities is None or capabilities.supports_seed:
        parametros["seed"] = int(
            hashlib.sha256(f"{brief.content_id}|{prompt}".encode("utf-8")).hexdigest()[:8], 16)

    metadata = {
        "prompt_compiler_version": COMPILER_VERSION,
        "visual_policy_version": policy.version,
        "visual_brief_version": brief.brief_version,
        "text_rendering_mode": brief.text_rendering_mode,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "negative_prompt_sha256": hashlib.sha256(", ".join(negs).encode("utf-8")).hexdigest(),
    }
    if fingerprint is not None:
        metadata["visual_fingerprint"] = fingerprint.to_dict()
    if safe_zone_geometria is not None:
        metadata["safe_zone_geometry"] = safe_zone_geometria.to_dict()

    composition_intent = f"una escena, {brief.focal_point}"
    if fingerprint is not None and fingerprint.composition:
        composition_intent += f"; composicion: {fingerprint.composition}"

    return CompiledVisualRequest(
        positive_prompt=prompt,
        negative_constraints=negs,
        requested_aspect_ratio=fmt["aspect_ratio"],
        requested_dimensions=(fmt["width"], fmt["height"]),
        composition_intent=composition_intent,
        visual_family=brief.visual_family,
        lighting_intent=lighting,
        text_mode=brief.text_rendering_mode,
        brand_mode=brand_mode,
        brand_plan=brand_plan.to_dict(),
        provider_parameters=parametros,
        explanation=explicacion,
        metadata=metadata,
        crop_safe_4_5_ok=crop_safe_ok,
        crop_safe_4_5_detalle=crop_safe_detalle,
    )


