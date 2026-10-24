#!/usr/bin/env python3
"""Testes de integracao/manifesto_do_casamento.py: do edital revisado e dos candidatos confirmados ao manifesto, sem PDF."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import manifesto_do_casamento as mc  # noqa: E402

FICHAS = {"A\\aula1.pdf": {"temas": [{"tema": "Git", "paginas": [[3, 12]]}],
                           "secoes": [{"tema": "Git", "tipo": "resumo", "inicio": 30, "fim": 31},
                                      {"tema": "Git", "tipo": "questoes_comentadas", "inicio": 16, "fim": 24}]}}
DISC = [{"nome": "Eng", "assuntos": [
    {"texto": "Versionamento: Git e Mercurial.", "partes": [{"texto": "Git", "contexto": "Versionamento"}, {"texto": "Mercurial"}]},
    {"texto": "Assunto sem material.", "partes": [{"texto": "Nada"}]}]}]
MAT = {"partes": [{"disciplina": "Eng", "assunto": 0, "parte": 0, "item": 0}, {"disciplina": "Eng", "assunto": 0, "parte": 1, "item": 1},
                  {"disciplina": "Eng", "assunto": 1, "parte": 0, "item": 2}]}
CONF = [{"indice": 0, "material": [{"caminho": "A\\aula1.pdf", "tema": "Git", "veredito": "ensina"}]},
        {"indice": 1, "material": [{"caminho": "A\\aula1.pdf", "tema": "Git", "veredito": "nao"}]},
        {"indice": 2, "material": []}]


class ManifestoDoCasamentoTest(unittest.TestCase):
    def test_um_manifesto_por_assunto_com_material_e_questoes_fora(self):
        with tempfile.TemporaryDirectory() as t:
            saida = Path(t)
            linhas = mc.processar("ed", DISC, MAT, CONF, FICHAS.get, "/acervo", "completo", lambda c: [], saida)
            self.assertEqual(["parcial", "sem material"], [l["situacao"] for l in linhas])
            m = json.loads(next((saida / "manifestos").iterdir()).read_text(encoding="utf-8"))
            self.assertEqual(["Git", "Mercurial"], m["subitens"])
            self.assertEqual([{"subitem": "Mercurial", "motivo": "nenhum tema do acervo ensina esta parte"}], m["lacunas"])
            self.assertEqual(["teoria", "fixacao"], [f["tipo"] for f in m["fontes"]])
            self.assertEqual("/acervo/A/aula1.pdf", m["fontes"][0]["arquivo"])
            self.assertEqual(3, m["fontes"][1]["minutos_por_pagina"])
            self.assertEqual(1, len(list((saida / "manifestos").iterdir())), "assunto sem material não gera manifesto")
            q = json.loads(next((saida / "questoes").iterdir()).read_text(encoding="utf-8"))
            self.assertEqual("16-24", q[0]["paginas"])
            self.assertEqual(linhas[0]["chave"], m["assunto_uuid"])

    def test_recusa_do_fatiador_vira_situacao_recusado(self):
        with tempfile.TemporaryDirectory() as t:
            linhas = mc.processar("ed", DISC, MAT, CONF, FICHAS.get, "/acervo", "completo", lambda c: ["página 99 fora do PDF"],
                                  Path(t))
            self.assertEqual("recusado", linhas[0]["situacao"])
            self.assertIn("recusado", mc.relatorio("ed", "completo", linhas))
            self.assertIn("página 99 fora do PDF", mc.relatorio("ed", "completo", linhas))


if __name__ == "__main__":
    unittest.main()
