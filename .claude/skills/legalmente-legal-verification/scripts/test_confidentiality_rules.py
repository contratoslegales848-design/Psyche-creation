#!/usr/bin/env python3
"""Pruebas del control determinista de confidencialidad.

Qué se protege: que una pieza basada en un caso reconocible, un cliente, un
expediente, un identificador personal, un importe concreto o un dato de contacto
**no pueda avanzar solo porque alguien rellenó un campo**. El control invierte la
carga de la prueba: si el texto dispara un indicador, la revisión humana deja de
ser opcional.

Lo que el control NO pretende: decidir si algo es confidencial. Decide cuándo un
humano está obligado a mirar. Por eso hay pruebas en las dos direcciones —
indicadores que deben disparar, y contenido educativo legítimo que NO debe
disparar, porque un control que marca todo se acaba desactivando.

Ningún revisor de prueba lleva nombre real (ver SKILL.md).
"""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import confidentiality_rules as cr  # noqa: E402
import test_validate_claim_packet as tvcp  # noqa: E402

vcp = tvcp.vcp
REVISOR_FICTICIO = tvcp.REVISOR_FICTICIO

OBSERVACIONES_REALES = (
    "Revisado el texto completo: la referencia es genérica, no identifica parte, "
    "operación ni expediente alguno. No procede de experiencia profesional privada."
)


def review(required, status, revisor=None, fecha=None, observaciones=None):
    return {
        "required": required,
        "status": status,
        "revisor": revisor,
        "fecha": fecha,
        "observaciones": observaciones,
    }


def claim_con(texto_o_campo, valor=None, **review_kwargs):
    """Claim sintético con un campo de texto concreto y una revisión dada."""
    campo, contenido = ("notas", texto_o_campo) if valor is None else (texto_o_campo, valor)
    c = tvcp.base_claim()
    c[campo] = contenido
    if review_kwargs:
        c["confidentiality_review"] = review(**review_kwargs)
    return c


# ---------------------------------------------------------------------------
# Sensibilidad: lo que DEBE disparar
# ---------------------------------------------------------------------------

CASOS_QUE_DISPARAN = [
    ("CASO_CONCRETO", "En un caso que llevé, la contraparte incumplió el plazo pactado."),
    ("CASO_PROPIO", "Mi cliente firmó sin leer la cláusula penal."),
    ("CASO_PROPIO", "En mi despacho vimos exactamente este supuesto el año pasado."),
    ("EXPERIENCIA_PRIMERA_PERSONA", "Asesoré a una constructora que perdió la garantía."),
    ("EXPERIENCIA_PRIMERA_PERSONA", "Represente a la parte vendedora en esa operación."),
    ("EXPEDIENTE", "El expediente 452/2023 resolvió justo lo contrario."),
    ("EXPEDIENTE", "La carpeta de investigación 118/2024 quedó archivada."),
    ("IDENTIFICADOR_PERSONAL", "Su RFC aparecía mal escrito en la factura."),
    ("IDENTIFICADOR_PERSONAL", "Bastó con el DNI para acreditar la representación."),
    ("SOCIEDAD_IDENTIFICABLE", "Constituyeron una S.A. de C.V. para blindar el activo."),
    ("MONTO_CONCRETO", "Se pactó una indemnización de 250.000 euros."),
    ("MONTO_CONCRETO", "La cláusula fijaba $1.500.000 pesos de penalización."),
    ("REGISTRO_O_ESCRITURA", "La escritura pública número 12.345 lo acredita."),
    ("REGISTRO_O_ESCRITURA", "Consta en el folio real de la finca."),
    ("CONTRATO_IDENTIFICABLE", "El contrato entre ambas sociedades preveía arbitraje."),
    ("DATOS_DE_CONTACTO", "Escribieron a alguien@ejemplo.com pidiendo la resolución."),
    ("TRATAMIENTO_Y_NOMBRE", "El Lic. Fernandez sostuvo la tesis contraria."),
    ("FECHA_DE_OPERACION", "Firmado el 14 de marzo, el acuerdo ya era inexigible."),
]

# Contenido educativo legítimo. Si esto disparase, el control sería ruido y
# acabaría desactivado — que es la forma más común en que muere un control.
CASOS_LIMPIOS = [
    "En el comodato se devuelve la misma cosa; en el mutuo, otro tanto equivalente.",
    "El expediente judicial es el conjunto ordenado de actuaciones de un proceso.",
    "La prescripción extintiva opera por el transcurso del tiempo y la inacción.",
    "El Código Civil español regula el comodato en el artículo 1740.",
    "Un cliente puede rescindir el contrato si concurre causa justificada.",
    "La cláusula penal sustituye a la indemnización de daños salvo pacto en contrario.",
    "El contrato de arrendamiento exige cosa, precio y consentimiento.",
    "La Suprema Corte de Justicia de la Nación fijó jurisprudencia sobre el punto.",
    "El plazo de la acción redhibitoria varía entre ordenamientos hispánicos.",
]


class TestSensibilidad(unittest.TestCase):

    def test_los_indicadores_disparan_donde_deben(self):
        for esperado, texto in CASOS_QUE_DISPARAN:
            with self.subTest(indicador=esperado):
                ids = [h[0] for h in cr.scan_text(texto)]
                self.assertIn(esperado, ids, f"{esperado} debía dispararse en: {texto!r}")

    def test_el_contenido_educativo_legitimo_no_dispara(self):
        for texto in CASOS_LIMPIOS:
            with self.subTest(texto=texto[:40]):
                self.assertEqual(
                    cr.scan_text(texto), [],
                    f"falso positivo — un control que marca todo se acaba desactivando: {texto!r}",
                )

    def test_los_acentos_no_permiten_esquivar_el_control(self):
        con = cr.scan_text("Asesoré a una empresa del sector.")
        sin = cr.scan_text("Asesore a una empresa del sector.")
        self.assertTrue(con and sin)
        self.assertEqual([h[0] for h in con], [h[0] for h in sin])

    def test_las_mayusculas_no_permiten_esquivar_el_control(self):
        self.assertTrue(cr.scan_text("MI CLIENTE FIRMÓ SIN LEER."))

    def test_el_informe_nunca_reproduce_el_fragmento(self):
        """Un error que citara el texto confidencial sería el mismo problema."""
        secreto = "El expediente 452/2023 de la empresa constructora."
        c = claim_con(secreto, required=False, status="NO_APLICA")
        errores, advertencias = cr.confidentiality_errors(c, "claims[0]")
        for mensaje in errores + advertencias:
            self.assertNotIn("452/2023", mensaje)
            self.assertNotIn("constructora", mensaje)

    def test_se_escanean_todos_los_campos_publicables(self):
        for campo in cr.SCANNED_FIELDS:
            with self.subTest(campo=campo):
                c = tvcp.base_claim()
                c[campo] = "Mi cliente no leyó la cláusula."
                self.assertTrue(cr.scan_claim(c), f"el campo {campo} no se está escaneando")

    def test_se_escanea_la_reformulacion_propuesta(self):
        c = tvcp.base_claim()
        c["reformulacion_propuesta"] = {
            "texto": "En un caso que llevé, la solución fue la contraria.",
            "verificada": False,
            "nuevo_claim_id": None,
        }
        campos = {f[0] for f in cr.scan_claim(c)}
        self.assertIn("reformulacion_propuesta.texto", campos)


# ---------------------------------------------------------------------------
# Reglas fail-closed
# ---------------------------------------------------------------------------

class TestReglasFailClosed(unittest.TestCase):

    def test_caso_reconocible_declarado_no_aplica_es_error(self):
        """Invariante 1 y 3: rellenar el campo no sustituye a revisarlo."""
        c = claim_con("Mi cliente firmó sin leer la cláusula penal.",
                      required=False, status="NO_APLICA")
        errores, _ = cr.confidentiality_errors(c, "claims[0]")
        self.assertTrue(any("'required' debe ser true" in e for e in errores))

    def test_caso_reconocible_con_revision_pendiente_es_valido_pero_no_abre_gate(self):
        """Invariante 1: no revisada no avanza, pero tampoco es un error de forma."""
        c = claim_con("Mi cliente firmó sin leer la cláusula penal.",
                      required=True, status="PENDIENTE")
        errores, advertencias = cr.confidentiality_errors(c, "claims[0]")
        self.assertEqual(errores, [])
        self.assertTrue(advertencias, "la revisión humana debe saber qué disparó")
        self.assertFalse(vcp.review_allows_gate(c["confidentiality_review"]))

    def test_confidencialidad_bloqueada_no_abre_gate(self):
        """Invariante 2."""
        c = claim_con("Mi cliente firmó sin leer.", required=True, status="RECHAZADO",
                      revisor=REVISOR_FICTICIO, fecha="2026-08-27",
                      observaciones="Bloqueado: el supuesto es reconocible y no puede anonimizarse.")
        self.assertFalse(vcp.review_allows_gate(c["confidentiality_review"]))

    def test_aprobacion_sin_constancia_es_error(self):
        for observaciones in (None, "", "   ", "Revisado.", "ok", "n/a", "sin observaciones"):
            with self.subTest(observaciones=observaciones):
                c = claim_con("Mi cliente firmó sin leer.", required=True, status="APROBADO",
                              revisor=REVISOR_FICTICIO, fecha="2026-08-27",
                              observaciones=observaciones)
                errores, _ = cr.confidentiality_errors(c, "claims[0]")
                self.assertTrue(any("observaciones" in e for e in errores),
                                f"{observaciones!r} no es constancia de revisión")

    def test_aprobacion_sin_revisor_es_error(self):
        c = claim_con("Mi cliente firmó sin leer.", required=True, status="APROBADO",
                      revisor="   ", fecha="2026-08-27", observaciones=OBSERVACIONES_REALES)
        errores, _ = cr.confidentiality_errors(c, "claims[0]")
        self.assertTrue(any("revisor" in e for e in errores))

    def test_bloqueo_sin_revisor_ni_motivo_es_error(self):
        """Bloquear también es una decisión con responsable."""
        c = claim_con("Mi cliente firmó sin leer.", required=True, status="RECHAZADO")
        errores, _ = cr.confidentiality_errors(c, "claims[0]")
        self.assertTrue(any("revisor" in e for e in errores))
        self.assertTrue(any("observaciones" in e for e in errores))

    def test_revision_firmada_y_motivada_es_valida(self):
        """Invariante 7: la ruta legítima existe y no está bloqueada."""
        c = claim_con("Mi cliente firmó sin leer.", required=True, status="APROBADO",
                      revisor=REVISOR_FICTICIO, fecha="2026-08-27",
                      observaciones=OBSERVACIONES_REALES)
        errores, _ = cr.confidentiality_errors(c, "claims[0]")
        self.assertEqual(errores, [])
        self.assertTrue(vcp.review_allows_gate(c["confidentiality_review"]))

    def test_texto_limpio_puede_declarar_no_aplica(self):
        """No se fuerza revisión donde legítimamente no hace falta."""
        c = claim_con("La prescripción extintiva opera por el transcurso del tiempo.",
                      required=False, status="NO_APLICA")
        errores, advertencias = cr.confidentiality_errors(c, "claims[0]")
        self.assertEqual(errores, [])
        self.assertEqual(advertencias, [])
        self.assertTrue(vcp.review_allows_gate(c["confidentiality_review"]))


# ---------------------------------------------------------------------------
# Integración con el validador canónico
# ---------------------------------------------------------------------------

class TestIntegracionConElValidador(unittest.TestCase):

    # El texto se pasa como override para que el hash de aprobación se calcule
    # sobre el contenido definitivo: mutar el claim después de aprobarlo lo
    # invalidaría por otra razón (hash), y la prueba dejaría de medir lo suyo.
    FUGA = "En un caso que llevé, el prestatario devolvió otro bien."

    def test_el_validador_rechaza_el_caso_reconocible_sin_revision(self):
        c = tvcp.approved_claim(notas=self.FUGA)
        errores, _w, _e, _gate = vcp.validate_claim(c, "claims[0]")
        self.assertTrue(any("required' debe ser true" in e for e in errores))

    def test_el_validador_cierra_el_gate_con_confidencialidad_pendiente(self):
        c = tvcp.approved_claim(notas=self.FUGA,
                                confidentiality_review=review(True, "PENDIENTE"))
        errores, _w, _e, gate = vcp.validate_claim(c, "claims[0]")
        self.assertEqual(gate, "CERRADO")
        self.assertTrue(any("gate_arte" in e for e in errores),
                        "declarar ABIERTO con confidencialidad pendiente debe ser un error")

    def test_el_validador_abre_el_gate_con_confidencialidad_revisada(self):
        """Invariante 7: la ruta legítima sigue existiendo."""
        c = tvcp.approved_claim(
            notas=self.FUGA,
            confidentiality_review=review(True, "APROBADO", REVISOR_FICTICIO,
                                          "2026-08-27", OBSERVACIONES_REALES))
        errores, _w, _e, gate = vcp.validate_claim(c, "claims[0]")
        self.assertEqual(errores, [])
        self.assertEqual(gate, "ABIERTO")

    def test_las_fixtures_de_confidencialidad_son_rechazadas(self):
        import subprocess
        skill_root = Path(__file__).resolve().parent.parent
        negativos = sorted((skill_root / "fixtures" / "negativos").glob("bad-4[789]-confidencialidad*.json"))
        self.assertTrue(negativos, "faltan las fixtures negativas de confidencialidad")
        for path in negativos:
            with self.subTest(fixture=path.name):
                proc = subprocess.run(
                    [sys.executable, str(skill_root / "scripts" / "validate-claim-packet.py"), str(path)],
                    capture_output=True, text=True)
                self.assertEqual(proc.returncode, 1, f"{path.name} debía rechazarse")
                self.assertIn("confidentiality_review", proc.stdout)

    def test_ninguna_pieza_real_ni_fixture_valida_dispara_indicadores(self):
        """Estado de partida: el control no rompe nada de lo que ya existe."""
        import json
        skill_root = Path(__file__).resolve().parent.parent
        for carpeta in ("fixtures/piezas", "pilot/claim-packets"):
            for path in sorted((skill_root / carpeta).glob("*.json")):
                data = json.loads(path.read_text(encoding="utf-8"))
                for claim in data.get("claims", []):
                    with self.subTest(fixture=path.name, claim=claim.get("claim_id")):
                        self.assertEqual(
                            cr.scan_claim(claim), [],
                            f"{path.name} dispara indicadores — revisar antes de dar por bueno el control",
                        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
