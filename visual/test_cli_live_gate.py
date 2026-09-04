"""`simulate` nunca toca un proveedor real sin --live explicito, y --live
nunca cae de vuelta al proveedor falso en silencio si faltan credenciales.

El defecto que esto fija: cli.py NUNCA importaba HttpImageProvider.
`simulate`, `dry-run` y `batch-dry-run` llamaban siempre a FakeImageProvider(),
incluso con LEGALMENTE_IMAGE_PROVIDER_ENDPOINT y _API_KEY configurados. No
habia ningun camino de ejecucion real del CLI que pudiera producir arte real,
aunque providers/http_provider.py y provider_preflight.py ya existian y
estaban probados.

Sin red real: --live con endpoint apuntando a localhost usa un servidor HTTP
local, nunca un proveedor externo.
"""

import base64
import io
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CLI = AQUI / "cli.py"
ARTEFACTO = AQUI.parent / "content" / "pieza-01-reales.json"
HANDOFF = (AQUI.parent / ".claude" / "skills" / "legalmente-legal-verification" /
           "publication" / "records" / "handoff-pieza-01-reales.json")


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        w, h = body.get("width", 1080), body.get("height", 1920)
        # PNG minimo valido: 1x1 gris, sin dependencia de Pillow en el servidor de prueba.
        png_1x1 = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")
        resp = json.dumps({"data": [{"b64_json": base64.b64encode(png_1x1).decode()}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)

    def log_message(self, *a):
        pass


def _correr(*args, env_extra=None):
    import os
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run([sys.executable, str(CLI), *args], cwd=str(AQUI),
                          capture_output=True, text=True, env=env)


class TestSimulateSinLive(unittest.TestCase):
    def test_ignora_credenciales_configuradas_si_no_se_pide_live(self):
        """Config presente pero sin --live: sigue usando el proveedor falso."""
        r = _correr("simulate", str(ARTEFACTO), "--handoff", str(HANDOFF),
                    env_extra={"LEGALMENTE_IMAGE_PROVIDER_ENDPOINT": "http://127.0.0.1:1/no-se-llama",
                               "LEGALMENTE_IMAGE_PROVIDER_API_KEY": "x"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("--live", r.stdout)


class TestLiveFailaCerrado(unittest.TestCase):
    def test_live_sin_endpoint_no_envia_nada(self):
        r = _correr("simulate", str(ARTEFACTO), "--handoff", str(HANDOFF), "--live",
                    env_extra={"LEGALMENTE_IMAGE_PROVIDER_ENDPOINT": "",
                               "LEGALMENTE_IMAGE_PROVIDER_API_KEY": ""})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("NO SE PUEDE USAR --live", r.stdout)

    def test_live_sin_credencial_no_envia_nada(self):
        r = _correr("simulate", str(ARTEFACTO), "--handoff", str(HANDOFF), "--live",
                    env_extra={"LEGALMENTE_IMAGE_PROVIDER_ENDPOINT": "http://127.0.0.1:1/x",
                               "LEGALMENTE_IMAGE_PROVIDER_API_KEY": ""})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("NO SE PUEDE USAR --live", r.stdout)


class TestLiveUsaElProveedorReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), _Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_live_con_credenciales_llama_al_proveedor_configurado(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = _correr("simulate", str(ARTEFACTO), "--handoff", str(HANDOFF), "--live",
                        "--out", tmp,
                        env_extra={"LEGALMENTE_IMAGE_PROVIDER_ENDPOINT": f"http://127.0.0.1:{self.port}/gen",
                                   "LEGALMENTE_IMAGE_PROVIDER_API_KEY": "clave-de-prueba"})
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("usando el proveedor real", r.stdout)
            compuestos = list(Path(tmp).glob("**/composed/*.png"))
            self.assertTrue(compuestos, "no se encontro ningun asset compuesto tras --live")


if __name__ == "__main__":
    unittest.main()
