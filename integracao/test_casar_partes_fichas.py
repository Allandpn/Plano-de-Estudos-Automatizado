#!/usr/bin/env python3
"""Testes de integracao/casar_partes_fichas.py: partes x temas de fichas pelos nós, sem IA."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import casar_partes_fichas as cp  # noqa: E402
import casar_taxonomia as ct  # noqa: E402
from test_casar_taxonomia import ARVORE  # noqa: E402

TEMAS = [{"caminho": "a.pdf", "tema": "NAT", "paginas": [[1, 2]], "nos": [31]},
         {"caminho": "b.pdf", "tema": "OSPF", "paginas": [[3, 9]], "nos": [321]},
         {"caminho": "c.pdf", "tema": "Roteamento", "paginas": [[1, 40]], "nos": [32]},
         {"caminho": "d.pdf", "tema": "Redes (disciplina inteira)", "paginas": [[1, 90]], "nos": [-3]},
         {"caminho": "e.pdf", "tema": "Verbos", "paginas": [[5, 6]], "nos": [21]}]


class CasarPartesFichasTest(unittest.TestCase):
    def setUp(self):
        self.arvore = ct.Arvore(ARVORE)

    def test_relacao_exato_dentro_contem(self):
        r = lambda a, b: cp.relacao(self.arvore, a, b)  # noqa: E731
        self.assertEqual("exato", r([321], [321]))
        self.assertEqual("dentro", r([32], [321]), "tema abaixo do nó da parte")
        self.assertEqual("contem", r([321], [32]), "tema acima do nó da parte")
        self.assertIsNone(r([31], [321]), "ramos irmãos não casam")
        self.assertIsNone(r([-3], [-3]), "disciplina sozinha nunca casa")

    def test_casar_ordena_pela_forca_e_ignora_outra_disciplina(self):
        itens = [{"nome": "OSPF", "ia": [321], "natureza": "exato"}, {"nome": "Roteamento", "ia": [32], "natureza": "mais_amplo"},
                 {"nome": "Algo sem nó", "ia": [], "natureza": None}]
        por = cp.casar(self.arvore, itens, [], TEMAS)
        self.assertEqual([("b.pdf", "exato"), ("c.pdf", "contem")], [(a["caminho"], a["relacao"]) for a in por[0]])
        self.assertEqual([("c.pdf", "exato"), ("b.pdf", "dentro")], [(a["caminho"], a["relacao"]) for a in por[1]])
        self.assertEqual([], por[2])

    def test_reserva_por_nome_so_para_parte_sem_casamento_por_no(self):
        itens = [{"nome": "noções de probabilidade", "ia": [12], "natureza": "mais_amplo"},   # nó sem ficha
                 {"nome": "OSPF", "ia": [321], "natureza": "exato"},                          # já casa por nó
                 {"nome": "Algoritmos genéticos", "ia": [11], "natureza": "exato"}]
        temas = TEMAS + [{"caminho": "f.pdf", "tema": "Teoria da Probabilidade", "paginas": [[1, 5]], "nos": [21]}]
        por = cp.casar(self.arvore, itens, [], temas)
        self.assertEqual(([], 1), (por[0], len([a for a in por[1] if a["relacao"] == "exato"])))
        self.assertEqual(1, cp.casar_por_nome(itens, por, temas), "só a parte de probabilidade ganha material")
        self.assertEqual([("f.pdf", "nome")], [(a["caminho"], a["relacao"]) for a in por[0]])
        self.assertEqual("exato", por[1][0]["relacao"], "quem já tinha casamento por nó não muda")
        self.assertEqual([], por[2])

    def test_reserva_por_nome_ignora_palavra_curta_e_comum_sozinha(self):
        itens = [{"nome": "valor", "ia": [], "natureza": None}, {"nome": "MVC", "ia": [], "natureza": None}]
        temas = [{"caminho": "a.pdf", "tema": "P-Valor", "nos": [31]}, {"caminho": "b.pdf", "tema": "ASP.NET MVC", "nos": [31]}]
        por = {}
        self.assertEqual(1, cp.casar_por_nome(itens, por, temas))
        self.assertNotIn(0, por)
        self.assertEqual("b.pdf", por[1][0]["caminho"])

    def test_resumo_e_relatorio_listam_o_que_ficou_sem_material(self):
        itens = [{"nome": "OSPF", "ia": [321], "natureza": "exato", "disciplina": "Redes"},
                 {"nome": "NAT", "ia": [31], "natureza": "mais_amplo", "disciplina": "Redes"},
                 {"nome": "Verbos", "ia": [21], "natureza": "exato", "disciplina": "Esp"}]
        por = cp.casar(self.arvore, itens, [], TEMAS[:2])
        tot = cp.resumo(itens, por)
        self.assertEqual({"exato": {"exato": 1, "sem material": 1}, "mais_amplo": {"exato": 1}}, tot)
        texto = cp.relatorio("x", itens, por, self.arvore, tot)
        self.assertIn("1 sem material no acervo", texto)
        self.assertIn("**Verbos**", texto)


if __name__ == "__main__":
    unittest.main()
