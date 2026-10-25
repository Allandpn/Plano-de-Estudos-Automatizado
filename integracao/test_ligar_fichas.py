#!/usr/bin/env python3
"""Testes de integracao/ligar_fichas.py com um catálogo pequeno e uma IA falsa."""

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import casar_taxonomia as ct  # noqa: E402
import ligar_fichas as lf  # noqa: E402
from test_casar_taxonomia import ARVORE, IaFalsa  # noqa: E402


def banco():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE fichas (caminho TEXT, situacao TEXT, ficha TEXT)")
    fichas = {"b/aula1.pdf": {"temas": [{"tema": "OSPF", "disciplina": "Redes de Computadores", "paginas": [[3, 9]],
                                         "termos": ["roteamento"]}]},
              "a/aula0.pdf": {"temas": [{"tema": "NAT", "disciplina": "Redes de Computadores", "paginas": [[1, 2]]}]},
              "c/vazia.pdf": {"temas": []}}
    for c, f in fichas.items():
        db.execute("INSERT INTO fichas VALUES (?, 'ok', ?)", (c, json.dumps(f)))
    db.execute("INSERT INTO fichas VALUES ('d/gemea.pdf', 'gemea', '{}')")
    return db


class LigarFichasTest(unittest.TestCase):
    def test_so_fichas_ok_em_ordem(self):
        self.assertEqual(["a/aula0.pdf", "b/aula1.pdf", "c/vazia.pdf"], lf.caminhos_com_tema(banco()))

    def test_ligar_bloco_e_linha_gravada(self):
        arvore = ct.Arvore(ARVORE)
        ia = IaFalsa([{"ligacoes": [{"item": 1, "nos": [31], "natureza": "exato"}, {"item": 2, "nos": [321], "natureza": "exato"}]}])
        itens = lf.ligar_bloco(ia, banco(), ["a/aula0.pdf", "b/aula1.pdf"], arvore, {"Redes de Computadores": [-3]})
        linhas = [lf.linha_do_tema(i) for i in itens]
        self.assertEqual([("a/aula0.pdf", "NAT", [31]), ("b/aula1.pdf", "OSPF", [321])],
                         [(l["caminho"], l["tema"], l["nos"]) for l in linhas])
        self.assertEqual([[1, 2]], linhas[0]["paginas"])

    def test_feitos_le_o_jsonl(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "fichas-nos.jsonl"
            self.assertEqual(set(), lf.feitos(f))
            f.write_text(json.dumps({"caminho": "a/aula0.pdf"}) + "\n\n" + json.dumps({"caminho": "a/aula0.pdf"}) + "\n")
            self.assertEqual({"a/aula0.pdf"}, lf.feitos(f))


if __name__ == "__main__":
    unittest.main()
