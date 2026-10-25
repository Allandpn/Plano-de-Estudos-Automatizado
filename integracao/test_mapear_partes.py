#!/usr/bin/env python3
"""Testes de integracao/mapear_partes.py: itens a partir das partes, sem IA."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import casar_taxonomia as ct  # noqa: E402
import mapear_partes as mp  # noqa: E402
from test_casar_taxonomia import ARVORE  # noqa: E402

DISCIPLINAS = [{"nome": "Redes", "assuntos": [
    {"texto": "NAT e OSPF", "partes": [{"texto": "NAT"}, {"texto": "OSPF", "contexto": "Roteamento"}]},
    {"texto": "Concordância verbal e nominal", "partes": [
        {"texto": "Concordância verbal"}, {"texto": "nominal", "herdado": "Concordância"}]},
    {"texto": "NAT", "partes": [{"texto": "nat"}]}]}]


class MapearPartesTest(unittest.TestCase):
    def test_item_por_parte_distinta_com_herdado_e_contexto(self):
        arvore = ct.Arvore(ARVORE)
        itens, partes = mp.itens_das_partes(DISCIPLINAS, arvore, {"Redes": [-3]})
        self.assertEqual(["NAT", "OSPF", "Concordância verbal", "Concordância nominal"], [i["nome"] for i in itens])
        self.assertEqual(5, len(partes), "toda parte do edital aponta para um item")
        self.assertEqual(partes[0]["item"], partes[4]["item"], "'NAT' e 'nat' na mesma disciplina valem uma ligação")
        self.assertEqual(["Roteamento"], itens[1]["termos"])
        self.assertEqual([-3], itens[0]["raizes"])

    def test_so_as_disciplinas_pedidas(self):
        itens, _ = mp.itens_das_partes(DISCIPLINAS, ct.Arvore(ARVORE), {}, so=["português"])
        self.assertEqual([], itens)

    def test_decisao_aprovada_vale_antes_da_ia_em_qualquer_edital(self):
        itens, _ = mp.itens_das_partes(DISCIPLINAS, ct.Arvore(ARVORE), {"Redes": [-3]})
        decisoes = [{"parte": "ospf", "contexto": "Roteamento", "nos": [321], "natureza": "exato", "origem": "revisão 2026-10-22"},
                    {"parte": "NAT", "contexto": "outro contexto", "nos": [31], "natureza": "exato"}]
        self.assertEqual(1, mp.aplicar_decisoes(itens, decisoes), "a chave é parte + contexto; contexto diferente não casa")
        self.assertEqual(([321], "exato", "revisão 2026-10-22"), (itens[1]["ia"], itens[1]["natureza"], itens[1]["decisao"]))
        self.assertNotIn("decisao", itens[0])

    def test_relatorio_conta_naturezas(self):
        arvore = ct.Arvore(ARVORE)
        itens, partes = mp.itens_das_partes(DISCIPLINAS, arvore, {"Redes": [-3]})
        itens[0].update(ia=[31], natureza="exato")
        itens[1].update(ia=[], natureza=None)
        texto = mp.relatorio("x", itens, partes, arvore, {"Redes": [-3]})
        self.assertIn("sem nó: 1", texto)
        self.assertIn("exato: 1", texto)
        self.assertIn("Redes de Computadores > NAT (Network Address Translation) · exato", texto)


if __name__ == "__main__":
    unittest.main()
