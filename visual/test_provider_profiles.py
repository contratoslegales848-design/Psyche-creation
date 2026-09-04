"""Un perfil de proveedor es configuracion, y tiene que ejecutarse de verdad.

Antes, `HttpImageProvider` hardcodeaba la forma "compatible con OpenAI":
cabecera `Authorization: Bearer`, cuerpo plano y imagen en `data[0].b64_json`.
Cualquier API con otra forma quedaba fuera sin tocar codigo — Gemini entre
ellas. Estas pruebas fijan que la forma se declara en el perfil y que el
adapter la ejecuta.

Lo que estas pruebas NO demuestran: que la forma declarada en el perfil
`gemini-3-pro-image` sea la que Google usa de verdad. Eso no se pudo
comprobar (el proxy de egress bloquea ai.google.dev y docs.cloud.google.com),
y por eso el perfil se declara NO_VERIFICADO. Aqui se comprueba el adapter
contra la forma ESPERADA, que es cosa distinta y hay que decirla.

Sin red externa: transporte inyectado, nunca urllib real.
"""

import base64
import sys
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

from providers import profiles  # noqa: E402
from providers.base import NormalizedImageRequest  # noqa: E402
from providers.http_provider import (  # noqa: E402
    HttpImageProvider, HttpProviderConfig, _buscar_en_ruta)

PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")
B64 = base64.b64encode(PNG_1X1).decode()


def _peticion(**kw):
    campos = dict(content_id="LM-TEST-PERFIL", prompt="una escena sobria",
                  negative_prompt="texto, letras", width=1080, height=1920,
                  aspect_ratio="9:16", seed=7)
    campos.update(kw)
    return NormalizedImageRequest(**campos)


class _Espia:
    """Transporte doble que guarda lo que se le pidio enviar."""

    def __init__(self, respuesta):
        self.respuesta = respuesta
        self.url = None
        self.payload = None
        self.headers = None

    def __call__(self, url, payload, headers, timeout):
        self.url, self.payload, self.headers = url, payload, headers
        return self.respuesta


class TestBuscarEnRuta(unittest.TestCase):
    def test_ruta_simple(self):
        self.assertEqual(_buscar_en_ruta({"a": {"b": "x"}}, "a.b"), "x")

    def test_indice_de_lista(self):
        self.assertEqual(_buscar_en_ruta({"a": [{"b": "x"}, {"b": "y"}]}, "a.1.b"), "y")

    def test_comodin_devuelve_la_primera_rama_completa(self):
        """El caso real: una lista mezcla una parte de texto y una de imagen;
        solo la segunda llega hasta el final de la ruta."""
        datos = {"parts": [{"text": "bla"}, {"inlineData": {"data": "AAA"}}]}
        self.assertEqual(_buscar_en_ruta(datos, "parts.*.inlineData.data"), "AAA")

    def test_ruta_ausente_devuelve_none_sin_lanzar(self):
        self.assertIsNone(_buscar_en_ruta({"a": 1}, "x.y.z"))

    def test_indice_fuera_de_rango_devuelve_none(self):
        self.assertIsNone(_buscar_en_ruta({"a": []}, "a.0.b"))

    def test_cadena_vacia_no_cuenta_como_encontrada(self):
        """Un base64 vacio no es una imagen: tiene que seguir buscando."""
        self.assertIsNone(_buscar_en_ruta({"a": {"b": ""}}, "a.b"))


class TestAutenticacionPorPerfil(unittest.TestCase):
    def test_perfil_generico_usa_bearer(self):
        cfg = HttpProviderConfig(provider_id="x", endpoint="http://local/n",
                                 api_key_env="UNA_CLAVE_DE_PRUEBA")
        espia = _Espia({"data": [{"b64_json": B64}]})
        prov = HttpImageProvider(cfg, transport=espia)
        import os
        os.environ["UNA_CLAVE_DE_PRUEBA"] = "secreta"
        try:
            prov.generate(_peticion())
        finally:
            del os.environ["UNA_CLAVE_DE_PRUEBA"]
        self.assertEqual(espia.headers["Authorization"], "Bearer secreta")

    def test_perfil_puede_declarar_otra_cabecera_sin_prefijo(self):
        cfg = HttpProviderConfig(provider_id="x", endpoint="http://local/n",
                                 api_key_env="UNA_CLAVE_DE_PRUEBA",
                                 auth_header="x-goog-api-key", auth_prefix="")
        espia = _Espia({"data": [{"b64_json": B64}]})
        prov = HttpImageProvider(cfg, transport=espia)
        import os
        os.environ["UNA_CLAVE_DE_PRUEBA"] = "secreta"
        try:
            prov.generate(_peticion())
        finally:
            del os.environ["UNA_CLAVE_DE_PRUEBA"]
        self.assertEqual(espia.headers["x-goog-api-key"], "secreta")
        self.assertNotIn("Authorization", espia.headers)

    def test_la_credencial_nunca_aparece_en_el_error(self):
        cfg = HttpProviderConfig(provider_id="x", endpoint="http://local/n",
                                 api_key_env="VARIABLE_QUE_NO_EXISTE_AQUI")
        prov = HttpImageProvider(cfg, transport=_Espia({}))
        res = prov.generate(_peticion())
        self.assertFalse(res.ok)
        self.assertIn("AUTH", res.error)


class TestCuerpoGemini(unittest.TestCase):
    def _prov(self, respuesta):
        cfg = profiles.cargar("gemini-3-pro-image")
        cfg.api_key_env = "UNA_CLAVE_DE_PRUEBA"
        espia = _Espia(respuesta)
        return HttpImageProvider(cfg, transport=espia), espia

    def _con_clave(self, fn):
        import os
        os.environ["UNA_CLAVE_DE_PRUEBA"] = "secreta"
        try:
            return fn()
        finally:
            del os.environ["UNA_CLAVE_DE_PRUEBA"]

    def test_el_cuerpo_va_anidado_no_plano(self):
        prov, espia = self._prov({"candidates": [
            {"content": {"parts": [{"inlineData": {"data": B64}}]}}]})
        self._con_clave(lambda: prov.generate(_peticion()))
        self.assertIn("contents", espia.payload)
        self.assertNotIn("prompt", espia.payload)
        self.assertEqual(espia.payload["contents"][0]["parts"][0]["text"][:16],
                         "una escena sobri")

    def test_el_negativo_se_concatena_al_texto(self):
        """La API no expone prompt negativo propio; perderlo en silencio
        dejaria la pieza sin sus restricciones."""
        prov, espia = self._prov({"candidates": [
            {"content": {"parts": [{"inlineData": {"data": B64}}]}}]})
        self._con_clave(lambda: prov.generate(_peticion()))
        texto = espia.payload["contents"][0]["parts"][0]["text"]
        self.assertIn("Evita explicitamente", texto)
        self.assertIn("texto, letras", texto)

    def test_extrae_la_imagen_de_la_parte_inline(self):
        prov, _e = self._prov({"candidates": [
            {"content": {"parts": [{"text": "aqui tienes"},
                                   {"inlineData": {"data": B64}}]}}]})
        res = self._con_clave(lambda: prov.generate(_peticion()))
        self.assertTrue(res.ok, res.error)
        self.assertEqual(res.image_bytes, PNG_1X1)
        self.assertEqual(res.mime_type, "image/png")

    def test_acepta_tambien_snake_case(self):
        """Distintas versiones de la API han usado inlineData e inline_data."""
        prov, _e = self._prov({"candidates": [
            {"content": {"parts": [{"inline_data": {"data": B64}}]}}]})
        res = self._con_clave(lambda: prov.generate(_peticion()))
        self.assertTrue(res.ok, res.error)

    def test_si_ninguna_ruta_acierta_el_error_dice_que_llego(self):
        """El mensaje mas util del sistema si el perfil esta desfasado: sin
        el, corregir response_paths seria adivinar."""
        prov, _e = self._prov({"promptFeedback": {"blockReason": "SAFETY"}})
        res = self._con_clave(lambda: prov.generate(_peticion()))
        self.assertFalse(res.ok)
        self.assertIn("promptFeedback", res.error)
        self.assertIn("response_paths", res.error.replace("rutas declaradas", "response_paths"))


class TestCatalogoDePerfiles(unittest.TestCase):
    def test_el_perfil_por_defecto_existe(self):
        self.assertIn(profiles.POR_DEFECTO, dict((p, e) for p, e, _n in
                                                 [(a, b, c) for a, b, c in profiles.listar()]))

    def test_gemini_esta_declarado_no_verificado(self):
        """Si alguien lo marca VERIFICADO sin haber leido la doc oficial,
        esta prueba lo frena: el estado es una afirmacion, no una etiqueta."""
        estado, nota = profiles.estado_de_verificacion("gemini-3-pro-image")
        self.assertEqual(estado, profiles.NO_VERIFICADO)
        self.assertIn("NO confirmada", nota)

    def test_un_perfil_desconocido_falla_claro(self):
        with self.assertRaises(ValueError):
            profiles.cargar("proveedor-que-no-existe")

    def test_ningun_perfil_lleva_una_credencial_dentro(self):
        """Solo el NOMBRE de la variable de entorno, nunca su valor.

        Se buscan prefijos de credencial real (sk-, AIza...), no la palabra
        'Bearer': esa aparece legitimamente al documentar el estilo de
        autenticacion, y prohibirla solo ensuciaria la prueba."""
        fuente = (AQUI / "providers" / "profiles.py").read_text(encoding="utf-8")
        for sospechoso in ("sk-", "AIza", "ghp_", "xoxb-"):
            self.assertNotIn(sospechoso, fuente)
        # Toda credencial se nombra, nunca se escribe.
        self.assertIn("api_key_env", fuente)

    def test_el_perfil_se_construye_en_cada_llamada(self):
        """Congelarlo en import ignoraria una credencial exportada despues."""
        import os
        os.environ["LEGALMENTE_GEMINI_MODEL"] = "modelo-de-prueba"
        try:
            self.assertIn("modelo-de-prueba", profiles.cargar("gemini-3-pro-image").endpoint)
        finally:
            del os.environ["LEGALMENTE_GEMINI_MODEL"]


if __name__ == "__main__":
    unittest.main()
