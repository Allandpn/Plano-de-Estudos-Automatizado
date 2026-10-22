#!/usr/bin/env python3
"""Testes de integracao/entrega_revisao.py: o JSON de entrega 'edital-revisao/1', sem IA."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import entrega_revisao as er  # noqa: E402

DISCIPLINAS = [{"nome": "Gestão de Projetos", "restricao": None, "paginas": [31], "linha_inicio": 127, "linha_fim": 128,
                "tentativas": 1, "referencias": [], "trechos_sem_assunto": ["sobra"], "assuntos": [
    {"texto": "Conceitos de metodologias ágeis: Scrum, Kanban e XP.", "erros": [], "avisos": ["repetição"], "partes": [
        {"texto": "Scrum", "contexto": "Conceitos de metodologias ágeis"}, {"texto": "Kanban", "contexto": "Conceitos de metodologias ágeis"},
        {"texto": "Kanban", "contexto": "Conceitos de metodologias ágeis"}]},
    {"texto": "Concordância verbal e nominal", "erros": ["palavras do assunto sem parte: nominal"], "partes": [
        {"texto": "Concordância verbal"}, {"texto": "nominal", "herdado": "Concordância"}]}]}]
NOS = {"itens": [{"nome": "Scrum", "ia": [5943], "natureza": "exato"},
                 {"nome": "Kanban", "ia": [3062], "natureza": "mais_amplo", "refinado": True, "ia_antes": [99]},
                 {"nome": "Concordância verbal", "ia": [], "natureza": None, "decisao": "revisão"}],
       "partes": [{"disciplina": "Gestão de Projetos", "assunto": 0, "parte": 0, "item": 0},
                  {"disciplina": "Gestão de Projetos", "assunto": 0, "parte": 1, "item": 1},
                  {"disciplina": "Gestão de Projetos", "assunto": 0, "parte": 2, "item": 1},
                  {"disciplina": "Gestão de Projetos", "assunto": 1, "parte": 0, "item": 2}]}


class EntregaTest(unittest.TestCase):
    def entrega(self, **extra):
        return er.montar_entrega("alesc-2024", "Analista de Sistemas", "alesc", DISCIPLINAS, NOS,
                                 {"Gestão de Projetos": [21]}, [{"linha_inicio": 1, "linha_fim": 2}], **extra)

    def test_estrutura_e_resumo(self):
        e = self.entrega()
        self.assertEqual("edital-revisao/1", e["contrato"])
        self.assertEqual({"disciplinas": 1, "assuntos": 2, "partes": 5, "sem_no": 1, "assuntos_recusados": 1,
                          "trechos_sem_assunto": 1, "blocos_fora": 1}, e["resumo"])
        d = e["disciplinas"][0]
        self.assertEqual([21], d["qconcursos"])
        self.assertEqual(["repetição"], d["assuntos"][0]["alertas"])

    def test_ligacao_com_origem(self):
        a, b = self.entrega()["disciplinas"][0]["assuntos"]
        self.assertEqual({"nos": [5943], "natureza": "exato", "origem": "ia"}, a["partes"][0]["ligacao"])
        self.assertEqual({"nos": [3062], "natureza": "mais_amplo", "origem": "refino", "antes": [99]}, a["partes"][1]["ligacao"])
        self.assertEqual("decisao", b["partes"][0]["ligacao"]["origem"])

    def test_chaves_unicas_e_estaveis(self):
        e1, e2 = self.entrega(), self.entrega()
        chaves = [p["chave"] for a in e1["disciplinas"][0]["assuntos"] for p in a["partes"]]
        self.assertEqual(len(chaves), len(set(chaves)), "o Kanban repetido no mesmo assunto ganha chave própria")
        self.assertEqual(chaves, [p["chave"] for a in e2["disciplinas"][0]["assuntos"] for p in a["partes"]])
        outra = er.chave_da_parte("Gestão de Projetos", "x", {"texto": "Scrum"}, {})
        self.assertNotEqual(outra, chaves[0])

    def test_chave_ignora_acento_e_caixa(self):
        a = er.chave_da_parte("Gestão", "Assunto X", {"texto": "Concordância"}, {})
        b = er.chave_da_parte("GESTAO", "assunto x", {"texto": "concordancia"}, {})
        self.assertEqual(a, b)

    def test_sem_ligacao_quando_nao_ha_nos(self):
        e = er.montar_entrega("s", "c", "p", DISCIPLINAS)
        self.assertIsNone(e["disciplinas"][0]["assuntos"][0]["partes"][0]["ligacao"])
        self.assertEqual(0, e["resumo"]["sem_no"])


if __name__ == "__main__":
    unittest.main()
