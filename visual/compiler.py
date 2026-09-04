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

from composition import build_brand_plan
from plan import canonical_hash

COMPILER_VERSION = "2.0"


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
        })


def _paleta_texto(policy):
    req = policy.data.get("paleta", {}).get("requerida", {})
    return "; ".join(f"{k.replace('_', ' ')} ({', '.join(v)})" for k, v in req.items())


def compile_request(brief, policy, family=None, capabilities=None, repetition=None):
    """Compila la peticion visual. Lanza ValueError si el brief no valida."""
    errores = brief.validate(policy)
    if errores:
        raise ValueError("brief invalido:\n- " + "\n- ".join(errores))

    fmt = policy.formato(brief.formato)
    comp = policy.data.get("composicion", {})
    explicacion = []

    partes = [
        f"Una sola escena. {brief.subject}.",
        f"Entorno: {brief.environment}.",
        f"Camara: {brief.camera}. Punto focal: {brief.focal_point}.",
        f"Familia visual: {brief.visual_family.replace('_', ' ')}.",
    ]
    explicacion.append(f"familia visual: {brief.visual_family}")

    lighting = brief.key_light or ""
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

    partes.append(f"Paleta: {_paleta_texto(policy)}.")
    if brief.acento_frio_objeto:
        partes.append(
            f"El acento azul petroleo debe proceder de un objeto fisico real de la escena: "
            f"{brief.acento_frio_objeto}."
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

    return CompiledVisualRequest(
        positive_prompt=prompt,
        negative_constraints=negs,
        requested_aspect_ratio=fmt["aspect_ratio"],
        requested_dimensions=(fmt["width"], fmt["height"]),
        composition_intent=f"una escena, {brief.focal_point}",
        visual_family=brief.visual_family,
        lighting_intent=lighting,
        text_mode=brief.text_rendering_mode,
        brand_mode=brand_mode,
        brand_plan=brand_plan.to_dict(),
        provider_parameters=parametros,
        explanation=explicacion,
        metadata=metadata,
    )


