#!/usr/bin/env python3
"""O arquivo de vetores que o SGE também testa tem de ser o que o código de hoje gera (ver vetores_conferencia.py)."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vetores_conferencia as vc  # noqa: E402


class VetoresConferenciaTest(unittest.TestCase):
    def test_arquivo_commitado_e_o_que_o_codigo_gera(self):
        gravado = json.loads(vc.ARQUIVO.read_text(encoding="utf-8"))
        self.assertEqual(vc.gerar(), gravado, "regra mudou: rode `python integracao/vetores_conferencia.py` e leve o arquivo ao SGE")

    def test_cobre_os_ramos_da_conferencia(self):
        erros = " ".join(" ".join(c["erros"]) for c in vc.gerar()["conferencias"])
        for trecho in ("não é trecho do edital", "assunto sem partes", "usa palavras que não estão", "prefixo herdado",
                       "não está no assunto nem no texto", "palavras do assunto sem parte"):
            self.assertIn(trecho, erros)
        self.assertTrue(any(c["alertas"] for c in vc.gerar()["conferencias"]))


if __name__ == "__main__":
    unittest.main()
