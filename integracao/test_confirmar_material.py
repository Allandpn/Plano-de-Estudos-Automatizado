#!/usr/bin/env python3
"""Testes de integracao/confirmar_material.py: a pergunta, a leitura da resposta e a amostra, sem IA."""

import json
import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import confirmar_material as cm  # noqa: E402


def banco():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE fichas (caminho TEXT, situacao TEXT, ficha TEXT)")
    ficha = {"temas": [{"tema": "Git", "termos": ["commit", "branch"], "subtemas": [{"nome": "Ramificação"}]}]}
    db.execute("INSERT INTO fichas VALUES (?, 'ok', ?)", ("00 - Curso\\06 - Engenharia\\aula 07.pdf", json.dumps(ficha)))
    return db


def parte():
    return {"nome": "SVN", "disciplina": "Gestão", "contexto": "Versionamento", "assunto": "Versionamento de código: SVN; Git.",
            "material": [{"caminho": "00 - Curso\\06 - Engenharia\\aula 07.pdf", "tema": "Git", "relacao": "exato"},
                         {"caminho": "x\\y.pdf", "tema": "CVS", "relacao": "dentro"}]}


class ConfirmarMaterialTest(unittest.TestCase):
    def test_pedido_traz_contexto_termos_e_subtemas(self):
        texto = cm.pedido_do_lote(banco(), [("alesc", parte())])
        self.assertIn("PARTE 1: SVN", texto)
        self.assertIn("contexto: Versionamento", texto)
        self.assertIn("trecho do edital: Versionamento de código", texto)
        self.assertIn("candidato 1: «Git»", texto)
        self.assertIn("termos: commit, branch", texto)
        self.assertIn("subtemas: Ramificação", texto)
        self.assertIn("candidato 2: «CVS»", texto)

    def test_aplicar_ignora_veredito_e_indice_invalidos(self):
        p = parte()
        cm.aplicar([("a", p)], {"partes": [{"parte": 1, "candidatos": [
            {"c": 1, "veredito": "ensina"}, {"c": 2, "veredito": "talvez"}, {"c": 9, "veredito": "nao"}]}]})
        self.assertEqual({0: "ensina"}, p["confirmado"])
        self.assertEqual(["ensina", None], [m["veredito"] for m in p["material"]])

    def test_resposta_vazia_deixa_sem_veredito(self):
        p = parte()
        cm.aplicar([("a", p)], {})
        self.assertEqual({}, p["confirmado"])

    def test_amostra_so_de_partes_com_candidato_e_repetivel(self):
        itens = [{"material": [1]}, {"material": []}, {"material": [1]}, {"material": [1]}]
        a = cm.amostrar(itens, 2, 3)
        self.assertEqual(a, cm.amostrar(itens, 2, 3))
        self.assertTrue(all(itens[i]["material"] for i in a))


if __name__ == "__main__":
    unittest.main()
