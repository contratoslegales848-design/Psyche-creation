"""Producción real — Pasos 4 a 14 del mandato 'CALIBRACIÓN POSITIVA +
PRODUCCIÓN REAL' (Founder, 2026-09-14).

Encadena la reserva real (≥120), la selección multi-factor (Territory
Explorer influye vía `generator.puntuar_candidato`, nunca por separado), el
borrador de dirección de arte para los 10 seleccionados, el QA de dos ejes
(INTELECTUAL vs VISUAL) y el ciclo Founder simulado (selección → memoria →
segundo lote), reutilizando la cadena de `demo_reconciliation.py` en vez de
duplicarla.

BLOQUEO EXPLÍCITO, deliberado y documentado (no silencioso): este módulo NO
redacta escena, metáfora ni copy (`copyExact`), y NO genera imágenes reales.
Los tres son la misma clase de contenido — una afirmación con carga jurídica
traducida a texto o a imagen — y CLAUDE.md §4 es inequívoco: "Todo título,
hook, definición, lista, consejo o consecuencia con carga jurídica pasa por
verificación antes de generar arte" y "Ninguna IA (este modelo incluido) es
fuente jurídica." Ningún candidato de este repo ha pasado
`legalmente-legal-verification` — todos nacen y permanecen NO_VERIFICADO
(`semantic_memory.py`). `art_direction.py` ya trazó esta misma línea antes de
esta fase (ver su docstring: escena/metáfora son "contenido creativo
verificable, no infraestructura"); este módulo la mantiene y la extiende a
`copyExact` y a la generación de píxeles, en vez de inventar una excepción
para esta fase.

Lo que SÍ hace, porque es infraestructura/mecanismo y no afirmación
jurídica: reserva real, selección multi-factor con Territory Explorer,
perfil emocional causal, argumento visual y su función editorial,
composición/cámara/luz/material/superficie de marca (dirección de arte sin
carga jurídica propia), QA de dos ejes, y el ciclo de aprendizaje Founder.
"""

from dataclasses import dataclass, field

import corpus_enrichment as ce
import corpus_import as ci
import editorial
import families
import generator
import memoria_fuerte as mf
import organism
import provider_gate
import territory_explorer as te
import universe
import visual_distance as vdist
import visual_fingerprint as vf
from art_direction import PENDIENTE_CONTENIDO, draft_visual_brief, verificar_diversidad_de_estilos
from memory import VisualMemory, VisualMemoryEntry
from semantic_memory import SemanticMemory

RESERVA_MINIMA = 120

COPY_BLOQUEADO = ("BLOQUEADO_SIN_VERIFICACION — copyExact es afirmación jurídica textual "
                  "(CLAUDE.md §4): ningún candidato de este lote ha pasado "
                  "legalmente-legal-verification. No se redacta hasta que exista esa "
                  "verificación humana sobre la pieza concreta.")


def draft_a_entry_visual(candidato, draft):
    """Igual criterio que demo_reconciliation.py: escena/metáfora no se
    copian a la memoria visual porque son PENDIENTE_CONTENIDO — tratarlas
    como dato real haría que todas las piezas parecieran idénticas ahí."""
    return VisualMemoryEntry(
        content_id=candidato.candidate_id, generation_id=f"prod-{candidato.candidate_id}",
        visual_family=draft.familia_visual, dominant_materials=[draft.material_sugerido],
        lighting_type=draft.luz, brand_surface=draft.superficie_marca_sugerida,
        materia=candidato.materia, concepto=candidato.concepto_nucleo)


def producir_y_dirigir(reserva_seed, memoria, mapa, universo, materias, registro_familias,
                       n=10, factor_reserva=14, catalogo_maestro=None, señales_mercado=None,
                       memoria_fuerte=None):
    """Reserva real ≥ RESERVA_MINIMA (factor=14, n=10 -> 140) → selección
    multi-factor (territorio ya incluido en el score, no aparte) → dirección
    de arte acumulando huella visual (catálogo maestro, Parte XII) entre
    piezas del mismo lote.

    `memoria_fuerte` (fuente #5 del Contrato v4, ver `memoria_fuerte.py`) se
    consulta dentro de `draft_visual_brief()` — cada draft de este lote ya
    trae `bloqueado_memoria_fuerte`/`motivos_bloqueo_memoria_fuerte` antes de
    que exista ningún prompt compilado (Hotfix memoria fuerte, autorización
    del Founder, 16-sep-2026). `None` desactiva la comparación contra piezas
    reales; por omisión (`ejecutar()`/`cargar_contexto()`) se carga real."""
    reserva = universe.build_reserve(objetivo_lote=n, seed=reserva_seed, factor=factor_reserva)
    assert len(reserva) >= RESERVA_MINIMA, (
        f"reserva de {len(reserva)} < mínimo exigido {RESERVA_MINIMA}: sube factor_reserva.")

    seleccion, puntuaciones, rechazados = generator.seleccionar_lote(
        reserva, memoria, mapa, universo=universo, n=n, materias=materias,
        señales_mercado=señales_mercado)

    catalogo_maestro = catalogo_maestro or vf.MasterCatalog.load()
    memoria_huellas = vf.FingerprintMemory()
    memoria_visual = VisualMemory()
    drafts = []
    for c in seleccion:
        d = draft_visual_brief(c, c.perfil_emocional, catalogo_maestro,
                               memoria_huellas=memoria_huellas,
                               registro_familias=registro_familias, memoria_visual=memoria_visual,
                               memoria_fuerte=memoria_fuerte)
        drafts.append(d)
        memoria_visual.record(draft_a_entry_visual(c, d))
    return reserva, seleccion, puntuaciones, drafts, rechazados


# ---------------------------------------------------------------------------
# Paso 5: exploitation (afinidad Founder positiva) vs exploration (territorio
# poco cubierto) — nunca "rareza por sí misma": exploration se mide contra
# opportunity, que YA es novelty * coherencia (territory_explorer.py), no
# novelty sola.

@dataclass
class BalanceExploracion:
    n: int = 0
    exploitation: int = 0
    exploration: int = 0
    ninguno: int = 0
    detalle: list = field(default_factory=list)

    def to_dict(self):
        return {"n": self.n, "exploitation": self.exploitation, "exploration": self.exploration,
                "ninguno": self.ninguno, "detalle": list(self.detalle)}


def balance_exploracion(seleccion, puntuaciones, umbral_exploitation=0.0, umbral_exploration=0.5):
    """Por candidato: EXPLOITATION si tiene afinidad Founder positiva
    (señal ya aprendida de curaduría previa), EXPLORATION si su
    territory_coverage (novelty*coherencia) supera el umbral y no tiene
    afinidad, NINGUNO si no cumple ninguno de los dos con evidencia clara."""
    r = BalanceExploracion(n=len(seleccion))
    for c, p in zip(seleccion, puntuaciones):
        if p.ajuste_afinidad_founder > umbral_exploitation:
            r.exploitation += 1
            r.detalle.append((c.candidate_id, "EXPLOITATION",
                              f"afinidad Founder {p.ajuste_afinidad_founder:+.4f}"))
        elif p.territory_coverage >= umbral_exploration:
            r.exploration += 1
            r.detalle.append((c.candidate_id, "EXPLORATION",
                              f"territory_coverage {p.territory_coverage} (novelty*coherencia)"))
        else:
            r.ninguno += 1
            r.detalle.append((c.candidate_id, "NINGUNO",
                              f"afinidad {p.ajuste_afinidad_founder:+.4f}, "
                              f"territory_coverage {p.territory_coverage}"))
    return r


# ---------------------------------------------------------------------------
# Paso 9: ImageGenerationBrief-equivalente. escena/metafora/copyExact quedan
# explícitamente bloqueados — ver docstring del módulo.

@dataclass
class ImageGenerationBrief:
    content_id: str = ""
    materia: str = ""
    submateria: str = ""
    familia_editorial: str = ""
    necesidad: str = ""
    concepto_nucleo: str = ""
    pregunta_resuelta: str = ""
    emocion: str = ""
    visual_function: str = ""
    familia_visual: str = ""
    composicion: str = ""
    camara: str = ""
    luz: str = ""
    escala: str = ""
    textura: str = ""
    ritmo: str = ""
    material_sugerido: str = ""
    superficie_marca_sugerida: str = ""
    escena: str = PENDIENTE_CONTENIDO
    metafora: str = PENDIENTE_CONTENIDO
    copyExact: str = COPY_BLOQUEADO
    formato: str = "9:16"
    estado_verificacion_juridica: str = "NO_VERIFICADO"
    autorizado_para_produccion: bool = False

    def to_dict(self):
        from dataclasses import asdict
        return asdict(self)


def construir_brief(candidato, draft):
    return ImageGenerationBrief(
        content_id=candidato.candidate_id, materia=candidato.materia,
        submateria=candidato.submateria, familia_editorial=candidato.familia_editorial,
        necesidad=candidato.necesidad, concepto_nucleo=candidato.concepto_nucleo,
        pregunta_resuelta=candidato.pregunta_resuelta, emocion=candidato.emocion,
        visual_function=draft.visual_function, familia_visual=draft.familia_visual,
        composicion=draft.composicion, camara=draft.camara, luz=draft.luz,
        escala=draft.escala, textura=draft.textura, ritmo=draft.ritmo,
        material_sugerido=draft.material_sugerido,
        superficie_marca_sugerida=draft.superficie_marca_sugerida)


# ---------------------------------------------------------------------------
# Paso 10: QA de dos ejes. INTELECTUAL = de qué habla el lote (huella
# semántica y editorial); VISUAL = cómo se ve (familia/estilo, distancia
# visual estricta cuando hay evidencia, prueba perceptual con títulos
# ocultos). Nunca se mezclan en un solo número.

@dataclass
class QADosEjes:
    intelectual_ok: bool = False
    intelectual_detalle: dict = field(default_factory=dict)
    visual_ok: bool = False
    visual_detalle: dict = field(default_factory=dict)
    prueba_titulos_ocultos_ok: bool = False
    prueba_titulos_ocultos_detalle: str = ""
    memoria_fuerte_ok: bool = True
    memoria_fuerte_detalle: dict = field(default_factory=dict)

    @property
    def aceptado(self):
        return (self.intelectual_ok and self.visual_ok and self.prueba_titulos_ocultos_ok
               and self.memoria_fuerte_ok)

    def to_dict(self):
        return {"aceptado": self.aceptado, "intelectual_ok": self.intelectual_ok,
                "intelectual_detalle": self.intelectual_detalle, "visual_ok": self.visual_ok,
                "visual_detalle": self.visual_detalle,
                "prueba_titulos_ocultos_ok": self.prueba_titulos_ocultos_ok,
                "prueba_titulos_ocultos_detalle": self.prueba_titulos_ocultos_detalle,
                "memoria_fuerte_ok": self.memoria_fuerte_ok,
                "memoria_fuerte_detalle": self.memoria_fuerte_detalle}


def _prueba_titulos_ocultos(drafts):
    """'Ocultando los títulos': compara SOLO los campos visuales que ya
    existen (hook/hoy PENDIENTE de todos modos no puede sesgar nada) —
    familia_visual + composicion + camara + luz + material. Si 4 o más
    piezas comparten exactamente esa combinación, el lote falla: se verían
    de la misma sesión aunque el título cambiara."""
    firmas = {}
    for d in drafts:
        clave = (d.familia_visual, d.composicion, d.camara, d.luz, d.material_sugerido)
        firmas.setdefault(clave, []).append(d.content_id)
    peor = max(firmas.values(), key=len) if firmas else []
    ok = len(peor) < 4
    detalle = (f"combinación visual más repetida: {len(peor)} piezas ({peor}). "
              f"{'OK' if ok else 'FALLA'} — el límite es 4 antes de leerse como "
              "'misma sesión' con los títulos ocultos.")
    return ok, detalle


def qa_dos_ejes(seleccion, drafts, catalogo_maestro=None, historicas_visuales=()):
    fps = [c.fingerprint() for c in seleccion]

    ejes_intelectuales = ("materia", "familia_editorial", "necesidad", "angulo", "emocion")
    distintos = {eje: len({getattr(fp, eje, "") for fp in fps if getattr(fp, eje, "")})
                for eje in ejes_intelectuales}
    intelectual_ok = all(v >= 2 for v in distintos.values())

    catalogo_maestro = catalogo_maestro or vf.MasterCatalog.load()
    ok_estilos, detalle_estilos = verificar_diversidad_de_estilos(
        drafts, catalogo_maestro, n_esperado=len(seleccion))
    entries = [draft_a_entry_visual(c, d) for c, d in zip(seleccion, drafts)]
    verificacion = vdist.verificar_lote_contra_historia(entries, historia=list(historicas_visuales))

    titulos_ok, titulos_detalle = _prueba_titulos_ocultos(drafts)

    bloqueados = [d.content_id for d in drafts if d.bloqueado_memoria_fuerte]
    memoria_fuerte_ok = not bloqueados
    memoria_fuerte_detalle = {
        "bloqueados": bloqueados,
        "motivos": {d.content_id: d.motivos_bloqueo_memoria_fuerte
                   for d in drafts if d.bloqueado_memoria_fuerte},
        "nota": ("informativo — misma disciplina que el resto de este QA: no vuelve a "
                "generar ni descarta por sí solo; señala qué pieza debe regenerarse o "
                "descartarse antes de compilar su prompt final (mandato: 'antes de "
                "generar, no después')."),
    }

    return QADosEjes(
        intelectual_ok=intelectual_ok,
        intelectual_detalle={"distintos_por_eje": distintos},
        visual_ok=ok_estilos,
        visual_detalle={"diversidad_estilos": detalle_estilos,
                        "distancia_visual_estricta": verificacion.to_dict()},
        prueba_titulos_ocultos_ok=titulos_ok,
        prueba_titulos_ocultos_detalle=titulos_detalle,
        memoria_fuerte_ok=memoria_fuerte_ok,
        memoria_fuerte_detalle=memoria_fuerte_detalle)


# ---------------------------------------------------------------------------
# Ciclo completo — orquesta lo anterior sobre datos reales.

def cargar_contexto():
    regs, _ = ci.construir_registros()
    enr = ce.enriquecer(regs)
    universo = editorial.EditorialUniverse.load()
    _, materias = universe.cargar_materias()
    registro_familias = families.VisualFamilyRegistry.load()
    mapa = te.construir_mapa(regs, materias=materias, universo=universo)
    memoria = SemanticMemory()
    ci.importar(memoria, regs)
    # Memoria fuerte real (fuente #5, Contrato v4) — deliberadamente una
    # instancia SEPARADA de `memoria` (memoria de ejecución/corpus histórico
    # arriba): mezclarlas confundiría "esto ya se contó en esta corrida" con
    # "esto ya lo aprobó el Founder de verdad" (ver memoria_fuerte.py).
    memoria_fuerte = mf.cargar_memoria_fuerte()
    return {"regs": regs, "enr": enr, "universo": universo, "materias": materias,
            "registro_familias": registro_familias, "mapa": mapa, "memoria": memoria,
            "memoria_fuerte": memoria_fuerte}


def ejecutar(seed_lote1=9101, seed_lote2=9102, elegidos_idx=(0, 4, 8)):
    ctx = cargar_contexto()
    reserva1, sel1, pts1, drafts1, rechazados1 = producir_y_dirigir(
        seed_lote1, ctx["memoria"], ctx["mapa"], ctx["universo"], ctx["materias"],
        ctx["registro_familias"], memoria_fuerte=ctx["memoria_fuerte"])

    balance = balance_exploracion(sel1, pts1)
    briefs = [construir_brief(c, d) for c, d in zip(sel1, drafts1)]
    qa = qa_dos_ejes(sel1, drafts1)

    for c in sel1:
        provider_gate.verificar_proveedor_permitido("generic-http-image-v1")

    lote1 = organism.CurationBatch(lote_id="produccion-real-1", estado=organism.CURATION_READY,
                                   candidatos=sel1, reserva_total=len(reserva1))
    elegidos_ids = [sel1[i].candidate_id for i in elegidos_idx if i < len(sel1)]
    resumen_curaduria = organism.registrar_curaduria(lote1, elegidos_ids, ctx["memoria"])

    reserva2, sel2, pts2, drafts2, rechazados2 = producir_y_dirigir(
        seed_lote2, ctx["memoria"], ctx["mapa"], ctx["universo"], ctx["materias"],
        ctx["registro_familias"], memoria_fuerte=ctx["memoria_fuerte"])

    fp1 = [c.fingerprint() for c in sel1]
    fp2 = [c.fingerprint() for c in sel2]
    repite = [(a.content_id, b.content_id) for a in fp2 for b in fp1 if a.equivalente_a(b)]

    materias_descartadas = {c.materia for c in sel1 if c.candidate_id not in elegidos_ids}
    reaparecen = {c.materia for c in sel2} & materias_descartadas
    con_afinidad = [p.ajuste_afinidad_founder for p in pts2 if p.ajuste_afinidad_founder > 0]

    return {
        "reserva1_size": len(reserva1), "reserva1_minimo_cumplido": len(reserva1) >= RESERVA_MINIMA,
        "seleccion1": sel1, "puntuaciones1": pts1, "drafts1": drafts1,
        "rechazados1": len(rechazados1), "balance_exploracion": balance.to_dict(),
        "briefs": [b.to_dict() for b in briefs], "qa_dos_ejes": qa.to_dict(),
        "elegidos_ids": elegidos_ids, "resumen_curaduria": resumen_curaduria,
        "reserva2_size": len(reserva2), "seleccion2_size": len(sel2),
        "no_repeticion_semantica_inmediata": len(repite),
        "materias_descartadas_reaparecen": f"{len(reaparecen)}/{len(materias_descartadas)}",
        "afinidad_heredada": f"{len(con_afinidad)}/{len(sel2)}",
    }


if __name__ == "__main__":
    import json
    r = ejecutar()
    print(f"reserva 1: {r['reserva1_size']} (>= {RESERVA_MINIMA}: {r['reserva1_minimo_cumplido']})")
    print(f"balance exploración/explotación: {r['balance_exploracion']}")
    print(f"QA dos ejes: aceptado={r['qa_dos_ejes']['aceptado']}")
    print(json.dumps(r["qa_dos_ejes"], indent=2, ensure_ascii=False))
