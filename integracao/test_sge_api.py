#!/usr/bin/env python3
"""
Testes de integracao/sge_api.py contra um servidor HTTP local de verdade: o multipart do
segmentos.csv, o token só nas rotas internas e o erro do SGE (RFC 9457) virando ErroSge.
"""

import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sge_api import ErroSge, SgeApi  # noqa: E402

RECEBIDOS = []


class Manipulador(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _responder(self, status, corpo=None, tipo="application/json"):
        bruto = json.dumps(corpo).encode() if corpo is not None else b""
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(bruto)))
        self.end_headers()
        self.wfile.write(bruto)

    def do_GET(self):
        RECEBIDOS.append(("GET", self.path, dict(self.headers), b""))
        if self.path == "/api/concursos/ativo":
            self._responder(204)
        else:
            self._responder(404, {"detail": "Concurso não encontrado.", "codigo": "CONCURSO_INEXISTENTE"},
                            "application/problem+json")

    def do_POST(self):
        corpo = self.rfile.read(int(self.headers["Content-Length"]))
        RECEBIDOS.append(("POST", self.path, dict(self.headers), corpo))
        if self.path == "/internal/ia/completar":
            self._responder(200, {"conteudo": "{}", "modelo": "m"})
        elif self.path == "/internal/material/lacunas":
            self._responder(204)
        else:
            self._responder(200, {"novos": 1})


class SgeApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servidor = HTTPServer(("127.0.0.1", 0), Manipulador)
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()
        cls.api = SgeApi(f"http://127.0.0.1:{cls.servidor.server_port}", "tok-123")

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()

    def setUp(self):
        RECEBIDOS.clear()

    def test_204_vira_nenhum_concurso(self):
        self.assertIsNone(self.api.concurso_ativo())
        self.assertNotIn("X-Internal-Token", RECEBIDOS[0][2], "rota pública não leva token")

    def test_erro_do_sge_vira_ErroSge_com_codigo(self):
        with self.assertRaises(ErroSge) as erro:
            self.api.planejamento(99)
        self.assertEqual(404, erro.exception.status)
        self.assertEqual("CONCURSO_INEXISTENTE", erro.exception.codigo)

    def test_segmentos_vao_como_multipart_no_campo_arquivo(self):
        self.api.importar_segmentos("chaveExternaSegmento,ordem\nabc,1\n")
        _, caminho, cabecalhos, corpo = RECEBIDOS[0]
        self.assertEqual("/api/segmentos/importacoes/confirmar", caminho)
        self.assertTrue(cabecalhos["Content-Type"].startswith("multipart/form-data; boundary="))
        self.assertIn(b'name="arquivo"; filename="segmentos.csv"', corpo)
        self.assertIn(b"abc,1", corpo)

    def test_rotas_internas_levam_token(self):
        self.assertEqual("{}", self.api.completar("s", "u"))
        self.api.registrar_lacuna("chave", "motivo")
        for _, _, cabecalhos, _ in RECEBIDOS:
            self.assertEqual("tok-123", cabecalhos["X-Internal-Token"])
        self.assertEqual({"chaveExterna": "chave", "motivo": "motivo"}, json.loads(RECEBIDOS[1][3]))

    def test_sem_conexao(self):
        with self.assertRaises(ErroSge) as erro:
            SgeApi("http://127.0.0.1:9", "t", tempo_maximo=2).concurso_ativo()
        self.assertEqual("SEM_CONEXAO", erro.exception.codigo)


if __name__ == "__main__":
    unittest.main()
