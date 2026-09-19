"""Prueba de aceptación — 10 temas reales, Fase 13 del mandato "Súper Prompt"
(Founder, 16-sep-2026).

Genera 10 huellas visuales + 10 prompts compilados sobre temas jurídicos
reales (Capa A transversal, orden de materias de
`docs/direccion-basico-antes-que-complejo.md` §3: laboral, familia y
sucesiones, inmobiliario, digital y datos, contractual — 2 temas por
materia). Produce PLANES/PROMPTS únicamente — NUNCA imágenes (ningún
proveedor se invoca aquí; no hay huecos de proveedor que llenar).

No verifica Derecho: los temas son etiquetas de tema/tensión/metáfora para
probar el motor de dirección artística, no afirmaciones jurídicas
publicables (esas pasan por `legalmente-legal-verification` antes de
producción real, nunca aquí).

Uso: `cd visual && python3 demo_prueba_aceptacion_10_temas.py`
"""

import json
from pathlib import Path

import visual_fingerprint as vf
from brief import VisualBrief, VisualPolicy
from compiler import compile_request
from visual_fingerprint_batch import generar_lote_visual

POLICY = VisualPolicy.load()
CATALOGO = vf.MasterCatalog.load()

SUPERFICIES = POLICY.data["marca"]["superficies_permitidas"]
FAMILIA_ESTRUCTURAL = POLICY.familias[0]   # campo estructural obligatorio del brief; la variedad real viene de la huella, no de aqui.

TEMAS = [
    dict(content_id="ACEPT-01", materia="laboral",
         tema="Qué distingue un despido de una renuncia",
         subject="dos cartas sobre un escritorio, una firmada y otra a medio llenar",
         environment="oficina de recursos humanos al final del dia",
         camera="35mm, altura de escritorio", focal_point="la firma inconclusa",
         metaphor="una puerta entreabierta, no se sabe quien la empujo",
         acento_objeto="un sello de recibido sin fechar"),
    dict(content_id="ACEPT-02", materia="laboral",
         tema="Qué es una relación laboral, más allá del contrato firmado",
         subject="un gafete de acceso colgado junto a una agenda llena de horarios",
         environment="entrada de un lugar de trabajo antes del amanecer",
         camera="50mm, contrapicado leve", focal_point="el gafete sin nombre visible",
         metaphor="una cadena de eslabones desiguales, uno mas fino que los demas",
         acento_objeto="un reloj checador antiguo"),
    dict(content_id="ACEPT-03", materia="familia_y_sucesiones",
         tema="Qué pasa con los bienes si no hay testamento",
         subject="una caja de documentos familiares abierta sobre una mesa de comedor",
         environment="sala de una casa familiar en penumbra de tarde",
         camera="35mm, picada suave", focal_point="un sobre sin destinatario escrito",
         metaphor="una mesa con un lugar vacio, nadie decidio quien se sienta ahi",
         acento_objeto="un juego de llaves antiguas sin etiquetar"),
    dict(content_id="ACEPT-04", materia="familia_y_sucesiones",
         tema="Diferencia entre separación y divorcio",
         subject="dos anillos sobre una superficie de madera, uno junto al otro sin tocarse",
         environment="alcoba en silencio, luz de ventana lateral",
         camera="85mm, plano cerrado", focal_point="el espacio entre los dos anillos",
         metaphor="dos lineas paralelas que nunca se cruzan, pero tampoco se alejan del todo",
         acento_objeto="una fotografia familiar boca abajo"),
    dict(content_id="ACEPT-05", materia="inmobiliario",
         tema="Qué revisar antes de firmar un contrato de arrendamiento",
         subject="un juego de llaves nuevas sobre un contrato con clausulas subrayadas",
         environment="apartamento vacio en dia de entrega",
         camera="24mm, gran angular controlado", focal_point="las clausulas subrayadas",
         metaphor="una puerta que se abre antes de saber que hay del otro lado",
         acento_objeto="una cinta metrica extendida sobre el suelo"),
    dict(content_id="ACEPT-06", materia="inmobiliario",
         tema="Qué es un gravamen sobre un inmueble",
         subject="una escritura de propiedad con un sello superpuesto sobre una esquina",
         environment="archivo notarial con estantes de expedientes",
         camera="35mm, plano medio", focal_point="el sello superpuesto",
         metaphor="una sombra que se proyecta sobre un terreno que parecia limpio",
         acento_objeto="una lupa sobre el documento"),
    dict(content_id="ACEPT-07", materia="digital_y_datos",
         tema="Qué significa dar consentimiento para tus datos personales",
         subject="una huella dactilar reflejada en la pantalla apagada de un dispositivo",
         environment="escritorio domestico de noche, unica fuente de luz la pantalla",
         camera="50mm, plano cenital leve", focal_point="la huella reflejada",
         metaphor="una firma que se da sin ver del todo lo que se firma",
         acento_objeto="un cable USB enrollado junto al dispositivo"),
    dict(content_id="ACEPT-08", materia="digital_y_datos",
         tema="Quién es dueño de tu contenido en una plataforma digital",
         subject="una fotografia impresa junto a la misma imagen mostrada en una pantalla",
         environment="estudio domestico con dos superficies, papel y pantalla",
         camera="35mm, comparacion lateral", focal_point="el limite entre el papel y la pantalla",
         metaphor="una copia que se aleja tanto del original que ya no se sabe de quien es",
         acento_objeto="un marco vacio apoyado contra la pared"),
    dict(content_id="ACEPT-09", materia="contractual",
         tema="Por qué la fecha de un contrato importa tanto como su contenido",
         subject="un calendario de escritorio con un dia marcado junto a un contrato sin firmar",
         environment="oficina legal al mediodia, luz cenital",
         camera="35mm, plano medio", focal_point="el dia marcado en el calendario",
         metaphor="un reloj de arena detenido a la mitad, nadie sabe si ya corrio o no",
         acento_objeto="un cronometro de escritorio antiguo"),
    dict(content_id="ACEPT-10", materia="contractual",
         tema="Qué hace que una cláusula sea abusiva",
         subject="un contrato con una linea de texto resaltada en un tono distinto al resto",
         environment="mesa de reunion con documentos apilados",
         camera="50mm, plano cerrado sobre el texto", focal_point="la linea resaltada",
         metaphor="una balanza con un platillo cargado antes de que nadie pese nada",
         acento_objeto="una balanza de bolsillo sobre la mesa"),
]


def construir_brief(t, superficie):
    return VisualBrief(
        content_id=t["content_id"], formato="VERTICAL_9_16",
        visual_family=FAMILIA_ESTRUCTURAL, subject=t["subject"],
        environment=t["environment"], camera=t["camera"], focal_point=t["focal_point"],
        metaphor=t["metaphor"], acento_objeto=t["acento_objeto"], marca_superficie=superficie,
    )


def ejecutar():
    """El lote se CONSTRUYE ya validado (Fase 6-7: rechazar es regenerar,
    nunca rellenar) -- generar_lote_visual() reintenta hasta que el lote
    completo pasa evaluar_lote_visual(), nunca se entrega un lote crudo sin
    pasar el QA de sistema."""
    content_ids = [t["content_id"] for t in TEMAS]
    huellas, reporte_lote, intentos = generar_lote_visual(content_ids, catalogo=CATALOGO, canal="linkedin")
    if not reporte_lote.aceptado:
        raise RuntimeError(
            f"el lote de aceptacion no convergio en {intentos} intentos: {reporte_lote.incumplimientos}")

    resultados = []
    for i, (t, huella) in enumerate(zip(TEMAS, huellas)):
        superficie = SUPERFICIES[i % len(SUPERFICIES)]
        brief = construir_brief(t, superficie)
        compilado = compile_request(brief, POLICY, fingerprint=huella)
        resultados.append(dict(tema=t, huella=huella, compilado=compilado))
    return resultados, reporte_lote, intentos


def matriz_similitud(resultados):
    n = len(resultados)
    filas = []
    for i in range(n):
        fila = []
        for j in range(n):
            if i == j:
                fila.append(None)
                continue
            distintas, conocidas = vf.distancia(resultados[i]["huella"], resultados[j]["huella"])
            fila.append(f"{distintas}/{conocidas}")
        filas.append(fila)
    return filas


def reporte_markdown(resultados, lote_qa, intentos):
    lineas = [
        "# Prueba de aceptación — 10 temas reales (Fase 13, 16-sep-2026)",
        "",
        "PLANES/PROMPTS únicamente. Ningún proveedor de imagen fue invocado.",
        "",
        f"**QA de lote:** {lote_qa.veredicto} en {intentos} intento(s) "
        f"({lote_qa.telemetria['huellas_distintas']}/10 huellas distintas, "
        f"{lote_qa.telemetria['medios_distintos']} medios distintos)",
    ]
    if lote_qa.incumplimientos:
        lineas.append("")
        lineas.append("Incumplimientos:")
        lineas.extend(f"- {m}" for m in lote_qa.incumplimientos)
    lineas.append("")
    for r in resultados:
        t, h, c = r["tema"], r["huella"], r["compilado"]
        lineas += [
            f"## {t['content_id']} — {t['tema']}",
            "",
            f"- **Materia:** {t['materia']}",
            f"- **Tensión/concepto:** {t['tema']}",
            f"- **Metáfora visual:** {t['metaphor']}",
            f"- **primary_direction:** {h.primary_direction}",
            f"- **secondary_direction:** {h.secondary_direction or '(ninguna)'}",
            f"- **medium:** {h.medium}",
            f"- **lighting:** {h.lighting}",
            f"- **palette:** {h.palette}",
            f"- **composition:** {h.composition}",
            f"- **materiality:** {h.materiality}",
            f"- **camera_optics:** {h.camera_optics}",
            f"- **realism:** {h.realism}",
            f"- **visual_mechanism:** {h.visual_mechanism}",
            "",
            "**Prompt compilado:**",
            "",
            f"> {c.positive_prompt}",
            "",
        ]
    lineas += ["## Matriz de distancia entre las 10 huellas (dimensiones distintas / dimensiones conocidas)", ""]
    ids = [t["content_id"].replace("ACEPT-", "") for t in TEMAS]
    lineas.append("| | " + " | ".join(ids) + " |")
    lineas.append("|---" * (len(ids) + 1) + "|")
    m = matriz_similitud(resultados)
    for i, fila in enumerate(m):
        celdas = ["—" if v is None else v for v in fila]
        lineas.append(f"| **{ids[i]}** | " + " | ".join(celdas) + " |")
    return "\n".join(lineas) + "\n"


if __name__ == "__main__":
    resultados, lote_qa, intentos = ejecutar()
    md = reporte_markdown(resultados, lote_qa, intentos)
    destino = Path(__file__).resolve().parent.parent / "docs" / "prueba-aceptacion-10-temas-2026-09-16.md"
    destino.write_text(md, encoding="utf-8")
    print(md)
    print(f"\nEscrito en {destino}")
