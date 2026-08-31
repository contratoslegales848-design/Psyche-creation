"""Prompt compiler — deterministico y versionado.

Convierte (ContentUnit + VisualBrief + VisualPolicy + capacidades + memoria
visual reciente) en un prompt compilado. El sistema deja de depender de
mega-prompts pegados a mano: el prompt es una SALIDA, no una entrada.
"""

import hashlib

from brief import VisualPolicy  # noqa: F401  (re-export util para consumidores)

COMPILER_VERSION = "1.0"


def _paleta_texto(policy):
    req = policy.data.get("paleta", {}).get("requerida", {})
    return "; ".join(f"{k.replace('_', ' ')} ({', '.join(v)})" for k, v in req.items())


def compile_prompt(brief, policy, capabilities=None, recent_memory=()):
    """Devuelve (prompt, negative_prompt, parametros, metadata).

    Lanza ValueError si el brief no valida contra la politica: no se compila un
    prompt a partir de un brief que la politica rechaza.
    """
    errores = brief.validate(policy)
    if errores:
        raise ValueError("brief invalido:\n- " + "\n- ".join(errores))

    fmt = policy.formato(brief.formato)
    comp = policy.data.get("composicion", {})

    partes = [
        f"Una sola escena. {brief.subject}.",
        f"Entorno: {brief.environment}.",
        f"Camara: {brief.camera}. Punto focal: {brief.focal_point}.",
        f"Familia visual: {brief.visual_family.replace('_', ' ')}.",
    ]
    if brief.metaphor:
        partes.append(f"Metafora visual: {brief.metaphor}.")
    if brief.negative_space:
        partes.append(f"Espacio negativo reservado: {brief.negative_space}.")
    if brief.key_light or brief.brightness_intent:
        partes.append(
            f"Luz: {brief.key_light or 'clave definida'}. Intencion de luminosidad: "
            f"{brief.brightness_intent or 'legible, sin empastar los negros'}."
        )
    partes.append(f"Paleta: {_paleta_texto(policy)}.")
    partes.append(
        f"El acento azul petroleo debe proceder de un objeto fisico real de la escena: {brief.acento_frio_objeto}."
    )

    marca = policy.data.get("marca", {})
    if marca.get("integracion_fisica_requerida"):
        if brief.marca_texto_en_imagen and policy.marca_escribe_generador == "SI":
            partes.append(
                f"La palabra 'LegalMente' aparece grabada fisicamente en {brief.marca_superficie}, "
                "respetando perspectiva, material, reflejo, luz y desgaste."
            )
        else:
            partes.append(
                f"La escena incluye {brief.marca_superficie} con una superficie de marca reservada y "
                "COMPLETAMENTE VACIA (relieve, perspectiva y luz correctos para que algo se lea ahi, "
                "pero sin ningun caracter). La marca se monta despues."
            )
    if brief.constraints:
        partes.append("Restricciones: " + "; ".join(brief.constraints) + ".")

    prompt = " ".join(partes)

    negativos = list(comp.get("prohibido", []))
    negativos += list(policy.data.get("paleta", {}).get("prohibida", []))
    negativos += list(marca.get("prohibido", []))
    negativos += list(brief.negative_constraints)
    if brief.text_rendering_mode != "NATIVE_TEXT":
        negativos += ["texto", "letras", "tipografia", "numeracion", "firma", "subtitulos"]

    # Memoria visual: no repetir escena/objeto/composicion recientes.
    uni = policy.data.get("unicidad", {})
    if uni.get("evitar_escena_repetida") and recent_memory:
        ventana = list(recent_memory)[: int(uni.get("ventana_memoria_visual", 12))]
        evitar = sorted({str(x) for x in ventana if str(x).strip()})
        if evitar:
            negativos += [f"repetir: {e}" for e in evitar]

    # dedup preservando orden
    vistos, negs = set(), []
    for n in negativos:
        if n not in vistos:
            vistos.add(n)
            negs.append(n)
    negative_prompt = ", ".join(negs)

    caps = capabilities
    parametros = {
        "width": fmt["width"],
        "height": fmt["height"],
        "aspect_ratio": fmt["aspect_ratio"],
        "full_bleed": fmt.get("full_bleed", True),
    }
    if caps is None or caps.supports_seed:
        parametros["seed"] = int(
            hashlib.sha256(f"{brief.content_id}|{prompt}".encode("utf-8")).hexdigest()[:8], 16
        )

    metadata = {
        "prompt_compiler_version": COMPILER_VERSION,
        "visual_policy_version": policy.version,
        "visual_brief_version": brief.brief_version,
        "text_rendering_mode": brief.text_rendering_mode,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "negative_prompt_sha256": hashlib.sha256(negative_prompt.encode("utf-8")).hexdigest(),
    }
    return prompt, negative_prompt, parametros, metadata
