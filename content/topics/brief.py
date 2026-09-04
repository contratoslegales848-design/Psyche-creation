"""De un tema transversal a un brief de producción — sin afirmar nada jurídico.

Qué produce este módulo y qué NO produce, porque la diferencia es la que evita
publicar sobre evidencia inexistente:

  PRODUCE  la ESTRUCTURA de la pieza: qué familia visual le toca, qué escena,
           qué micro-evento anima esa escena, y qué huecos tiene que rellenar el
           copy cuando existan fuentes.

  NO PRODUCE  el contenido jurídico. Los huecos se quedan huecos. Este módulo
           nunca escribe qué dice el derecho, ni un plazo, ni una consecuencia,
           ni un ejemplo con un país dentro. Un brief con el copy ya escrito
           sería una afirmación sin fuente disfrazada de plantilla.

Las fórmulas visual, de animación y de copy provienen del documento del fundador
«LegalMente — Fórmula maestra de animación y copy para imágenes» (Drive,
1a9aO9hOeFzPbYjJAglPEeqBnvJXtdv6DpG53YwdV6BA). Aquí están implementadas, no
reinventadas: si el documento cambia, este módulo queda desactualizado y debe
corregirse contra él, no al revés.

Sin red. Determinista: el mismo tema produce siempre el mismo brief.
"""

import json
from pathlib import Path

import transversality as T

AQUI = Path(__file__).resolve().parent

# Estructura narrativa de la animación, literal del documento del fundador.
ARCO_ANIMACION = ("HOOK", "MICRO_EVENT", "TENSION", "REVEAL", "RESOLUTION")

# Familias visuales del repositorio (visual/policy/visual-families-v1.json). No
# se declaran aquí a mano: se leen, para que añadir una familia no exija tocar
# este archivo y para que una familia retirada deje de asignarse sola.
FAMILIAS_PATH = AQUI.parent.parent / "visual" / "policy" / "visual-families-v1.json"

# Reglas de animación que NUNCA dependen del tema. Van en todos los briefs
# porque son las que más se incumplen cuando se anima deprisa.
INVARIANTES_ANIMACION = (
    "El texto montado no se borra, no se sustituye y no sale de cuadro.",
    "La frase principal permanece legible durante todo el clip.",
    "Una sola animación por imagen; un solo micro-evento.",
    "Cámara sutil: micro-acercamiento, paneo corto, parallax discreto o cambio de foco.",
    "Pausa breve antes del REVEAL; cierre estable, nunca caótico.",
    "Foley realista y sobrio; bajar ligeramente el sonido justo antes del punto clave.",
    "Voz adulta, neutra internacional, sobria, con tiempo para leer el texto.",
    "Prohibido: deformar objetos, manos sin propósito, transiciones de plantilla, collage.",
    "Prohibido: inventar frases nuevas dentro de la imagen o alterar su sentido jurídico.",
)

# Micro-eventos por formato editorial. Cada uno nace de la metáfora, no del
# adorno: el movimiento tiene que significar lo mismo que la distinción jurídica.
MICROEVENTOS = {
    "DIFERENCIAS": (
        "dos objetos idénticos se separan unos milímetros y la luz cae distinta sobre cada uno",
        "una llave gira en una cerradura y se detiene sin abrir",
        "un sello baja una sola vez sobre uno de dos documentos gemelos",
    ),
    "MITO": (
        "una superficie pulida revela una grieta cuando la luz la cruza",
        "el agua descubre una filigrana que contradice lo que estaba impreso",
        "una sombra alcanza el objeto equivocado",
    ),
    "CONSECUENCIA": (
        "una pluma termina un trazo y la tinta se asienta",
        "una página se desplaza unos milímetros y deja ver lo que había debajo",
        "una puerta se cierra despacio mientras la cámara avanza unos centímetros",
    ),
    "CONCEPTO": (
        "una lámpara se enciende y define el contorno de un solo objeto",
        "el polvo se posa y deja limpia una única superficie",
    ),
    "APRENDIZAJE": (
        "una mano retira un objeto y deja la marca que había debajo",
        "una página ya escrita se alisa con la palma",
    ),
    "ERROR_FRECUENTE": (
        "una gota cae sobre tinta todavía fresca",
        "un papel firmado resbala unos centímetros fuera de la carpeta",
    ),
    "PREGUNTA_COMUN": (
        "un sobre cerrado gira lentamente sin llegar a abrirse",
        "una lámpara parpadea una vez sobre un documento sin firmar",
    ),
    "REFLEXION": (
        "la luz recorre despacio una superficie de madera vieja",
        "el reflejo de una ventana cruza la mesa sin tocar los papeles",
    ),
    "SITUACION_HUMANA": (
        "dos manos empujan el mismo documento en direcciones opuestas",
        "una silla vacía queda en el encuadre mientras la luz cambia",
    ),
    "GUIA_O_CHECKLIST": (
        "una pluma marca una casilla y se detiene antes de la siguiente",
        "un cajón se abre lo justo para mostrar el borde de unos papeles",
    ),
    "PASOS": (
        "tres objetos se alinean uno tras otro con un chasquido seco",
        "una regla se desliza y encuadra un solo renglón",
    ),
    "FRASE_O_MAXIMA": (
        "una letra grabada en piedra recibe luz rasante",
        "el lacre se enfría y fija su relieve",
    ),
    "PRESENTACION_INSTITUCIONAL": (
        "una placa metálica gira hasta quedar frontal a la cámara",
        "una carpeta de cuero se cierra con un chasquido discreto",
    ),
}

# Paleta y superficies de marca, del documento del fundador. La marca va SIEMPRE
# integrada en un objeto físico de la escena, nunca como marca de agua flotante.
PALETA = ("marfil / crema", "nogal / caoba", "latón / oro viejo", "azul petróleo")
SUPERFICIES_DE_MARCA = (
    "chapa metálica", "sello seco", "lacre", "placa de puerta", "carpeta de cuero",
    "marca de fuego", "filigrana integrada", "tampón integrado", "placa de portón",
)

FORMATO_9_16 = {"aspecto": "9:16", "ancho": 1080, "alto": 1920, "full_bleed": True}


def cargar_familias(path=None):
    p = Path(path) if path else FAMILIAS_PATH
    datos = json.loads(p.read_text(encoding="utf-8"))
    return sorted((datos.get("familias") or {}).keys())


def _indice_estable(tema_id, n):
    """Reparto determinista y sin repetición cíclica evidente.

    Se usa el id del tema, no un contador: así insertar un tema en medio del
    catálogo no reasigna la familia visual de todos los demás.
    """
    return sum(ord(c) for c in str(tema_id)) % max(n, 1)


# Orden del pipeline. Antes del gate de arte solo caben estructuras de
# investigacion y propuestas NO EJECUTABLES:
#
#   pregunta humana -> candidato -> investigacion -> fuente y territorio ->
#   claim -> validacion tecnica -> revision humana -> GATE DE ARTE ->
#   narrativa y formato -> imagen -> QA -> autorizacion humana de publicacion
#
# Este modulo vive ANTES del gate. Por eso lo que produce se llama ficha de
# investigacion y no prompt de produccion: un prompt con aspecto de listo, junto
# a un gate cerrado, es una invitacion a saltarselo.
PIPELINE = (
    "pregunta_humana", "candidato", "investigacion", "fuente_y_territorio",
    "claim", "validacion_tecnica", "revision_humana", "gate_de_arte",
    "narrativa_y_formato", "imagen", "qa", "autorizacion_humana_de_publicacion",
)
ETAPA_DE_ESTE_MODULO = "candidato"


def construir_brief(tema, familias=None):
    """Ficha de investigacion de un candidato. NO es un prompt de produccion.

    Un tema no transversal no recibe brief: producir arte para él sería gastar
    en una pieza que después habría que reclasificar o tirar.
    """
    dictamen = T.evaluar_tema(tema)
    if not dictamen["admisible_como_tema"]:
        return {
            "tema_id": tema.get("id"),
            "brief": None,
            "motivo": "el tema no supera la barrera de transversalidad",
            "dictamen": dictamen,
        }

    fams = familias if familias is not None else cargar_familias()
    familia = fams[_indice_estable(tema["id"], len(fams))]
    formato = tema["forma_editorial"]
    micros = MICROEVENTOS[formato]
    micro = micros[_indice_estable(tema["id"] + "m", len(micros))]
    superficie = SUPERFICIES_DE_MARCA[
        _indice_estable(tema["id"] + "s", len(SUPERFICIES_DE_MARCA))]

    prompt_animacion = (
        "Animar esta imagen de LegalMente respetando por completo su composición y "
        "su texto. Mantener todo el texto visible, estable y legible; no borrar, "
        "sustituir ni recortar palabras. Iniciar con un movimiento de cámara muy "
        "sutil que refuerce el punto focal. Introducir un micro-evento físico y "
        "creíble relacionado con la metáfora de la escena. Generar una breve "
        "tensión visual antes del concepto principal y hacer una pausa mínima "
        "antes del reveal. Resolver con cámara estable y lectura limpia. Foley "
        "realista acorde con la escena y ligera reducción de sonido justo antes "
        "del punto clave. Voz adulta, neutra internacional y sobria. Evitar "
        "movimientos gratuitos, manos genéricas, deformaciones, objetos "
        "antinaturales y zooms que oculten el texto. "
        f"Instrucción específica de esta pieza: {micro}."
    )

    return {
        "tema_id": tema["id"],
        "titulo_de_trabajo": tema["titulo_de_trabajo"],
        "formato_editorial": formato,
        "taxonomia": {
            "materia": tema["materia"],
            "submateria": tema.get("submateria", ""),
            "concepto": tema["concepto"],
            "situacion_humana": tema.get("situacion_humana", ""),
            # La forma editorial real viaja aqui. Fijarlas todas como "concepto"
            # borraba la unica senal que permite detectar que un lote esta
            # repitiendo formato.
            #
            # HASTA DONDE LLEGA ESTE CAMPO, con exactitud. Llega a este brief y
            # al control de diversidad de lote (content/topics/lote.py), que es
            # sincrono y no persiste nada. NO llega a la memoria visual:
            # visual/memory.py registra materia y concepto de una pieza REAL de
            # content/*.json, no content_type, y solo al aceptarse un asset
            # generado — un brief no entra ahi. Podria llegar a canonical.py y
            # composition.py, que si leen taxonomia.content_type, pero solo
            # cuando el candidato se convierta en artefacto de contenido real, lo
            # que exige recorrer toda la cadena. Hoy no hay ninguno.
            #
            # Una version anterior de la documentacion afirmaba que "la forma
            # editorial real viaja a la memoria". Era falso: viaja al brief.
            "content_type": formato,
            "_alcance_de_content_type": (
                "brief y control de diversidad de lote; NO alimenta memoria "
                "persistente"),
            "angulo": tema.get("angulo", ""),
            "utilidad": tema.get("utilidad", ""),
            "conexion_juridica": tema.get("conexion_juridica", ""),
        },
        "imagen": {
            **FORMATO_9_16,
            "familia_visual": familia,
            "escena": "una sola escena; nunca collage, grid, mosaico ni storyboard",
            "paleta": list(PALETA),
            "marca": {
                "regla": "«LegalMente» integrado físicamente en un objeto real de la escena, "
                         "respetando perspectiva, textura, luz y desgaste",
                "superficie_sugerida": superficie,
                "prohibido": "marca de agua flotante",
            },
            "tipografia": "clásica, sobria, jerarquía muy clara, cuerpo legible en móvil, "
                          "sin cajas opacas ni bandas genéricas",
            "rechazos": ["sepia dominante", "imagen turbia u oscura en exceso",
                         "recuadros tipo diapositiva escolar", "estética genérica de plantilla",
                         "repetir escena o encuadre de otra pieza"],
        },
        "animacion": {
            "arco": list(ARCO_ANIMACION),
            "micro_evento": micro,
            "invariantes": list(INVARIANTES_ANIMACION),
            # Se guarda como propuesta, no como prompt listo: mientras el gate
            # este cerrado no hay imagen que animar, y un campo llamado "prompt"
            # invita a usarlo.
            "propuesta_de_prompt_NO_EJECUTABLE": prompt_animacion,
            "duracion_de_referencia_s": [10, 11],
        },
        # Los huecos se entregan VACÍOS a propósito. Rellenarlos sin fuente sería
        # inventar derecho; rellenarlos con un ejemplo nacional sería reintroducir
        # justo la deriva que este motor existe para frenar.
        "copy": {
            "estructura": ["apertura", "explicacion", "por_que_importa",
                           "en_la_practica", "remate", "cierre_jurisdiccional", "hashtags"],
            "apertura": "",
            "explicacion": "",
            "por_que_importa": "",
            "en_la_practica": "",
            "remate": "",
            "cierre_jurisdiccional": "Las reglas concretas pueden variar según la jurisdicción.",
            "hashtags": ["#LegalMente", f"#{tema['materia'].capitalize()}", "#EducaciónJurídica"],
            "_nota": "Huecos vacíos a propósito: el copy se escribe DESPUÉS de tener fuentes. "
                     "Ninguna plantilla puede sustituir la lectura del texto jurídico.",
            "lenguaje_obligatorio": ["puede", "suele", "depende de", "según la ley aplicable"],
            "prohibido": ["afirmar que algo ocurre 'siempre'",
                          "dar una cifra, un plazo o un porcentaje",
                          "nombrar un país como si la regla fuera solo suya o de todos",
                          "convertir el post en asesoría jurídica individual"],
        },
        "pendiente_antes_de_producir": {
            "jurisdicciones_comparadas_minimas": T.MINIMO_JURISDICCIONES_COMPARADAS,
            "advertencia_del_tema": tema["advertencia"],
            "riesgo_de_deriva_nacional": tema["riesgo_de_deriva_nacional"],
        },
        # Invariantes. Una ficha de investigación no autoriza nada.
        "ejecutable": False,
        "etapa_del_pipeline": ETAPA_DE_ESTE_MODULO,
        "etapas_pendientes_antes_del_arte": list(
            PIPELINE[PIPELINE.index(ETAPA_DE_ESTE_MODULO) + 1:PIPELINE.index("gate_de_arte") + 1]),
        "estado_epistemico": T.TOPIC_CANDIDATE,
        "estado_juridico": "REQUIERE_INVESTIGACION",
        "gate_arte": "CERRADO",
        "revision_humana": "PENDIENTE",
        "publicacion": "NOT_PUBLISHED",
    }


def construir_todos(path=None):
    fams = cargar_familias()
    return [construir_brief(t, fams)
            for t in T.cargar_catalogo(path).get("temas", [])]


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--tema", help="construir solo este id de tema")
    args = ap.parse_args(argv)

    briefs = construir_todos()
    if args.tema:
        briefs = [b for b in briefs if b.get("tema_id") == args.tema]
        if not briefs:
            print(f"tema no encontrado: {args.tema}")
            return 1
    if args.json:
        print(json.dumps(briefs, ensure_ascii=False, indent=2))
        return 0

    print(f"{'TEMA':<10} {'FORMATO':<14} {'FAMILIA VISUAL':<40} GATE")
    print("-" * 80)
    for b in briefs:
        if b.get("brief", "") is None:
            print(f"{b['tema_id']:<10} {'—':<14} {'RECHAZADO':<40} —")
            continue
        print(f"{b['tema_id']:<10} {b['formato_editorial']:<14} "
              f"{b['imagen']['familia_visual']:<40} {b['gate_arte']}")
    print(f"\n{len(briefs)} briefs. Todos con gate CERRADO y copy sin rellenar: "
          "falta la evidencia primaria, no la plantilla.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
