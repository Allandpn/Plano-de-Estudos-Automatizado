#!/usr/bin/env python3
"""Testes de integracao/estrutura_apostilas.py com um índice sintético."""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estrutura_apostilas as ea  # noqa: E402
from test_worker import SCHEMA_INDICE  # noqa: E402

PAGINAS = [
    "Redes de Computadores - Curso Regular\nAula 04 - VLAN",
    "SUMÁRIO\n802.1Q ........ 3\nQuestões Comentadas ........ 6\nResumo ........ 9",
    "802.1Q e VLANs\ntexto da teoria", "mais teoria sobre trunk", "teoria sobre o padrão 802.1Q", "Questões Comentadas\n1. (FCC - TRT) Sobre VLAN",
    "2. (FCC - TJ) ... 3. (CEBRASPE - PF) ...", "Gabarito\n1-A 2-B 3-C 4-D 5-E", "Resumo\nVLAN separa domínios", "",
]


class EstruturaTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        db = Path(self._tmp.name) / "i.db"
        self.conn = sqlite3.connect(db)
        self.conn.executescript(SCHEMA_INDICE)
        self.conn.execute("INSERT INTO arquivos (caminho, curso, nome_arquivo, n_paginas) VALUES "
                          "('x', '00 - Curso Regular\\09 - Redes de Computadores', 'aula 04.pdf', 10)")
        for p, t in enumerate(PAGINAS, 1):
            self.conn.execute("INSERT INTO paginas (arquivo_id, pagina, texto) VALUES (1, ?, ?)", (p, t))
        self.conn.execute("INSERT INTO bookmarks (arquivo_id, nivel, titulo, pagina) VALUES (1, 1, 'Questões', 6)")
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        self._tmp.cleanup()

    def test_acha_sumario_secoes_e_bancas(self):
        a = ea.analisar_aula(self.conn, 1)
        self.assertEqual(2, a["sumario"][0])
        self.assertEqual(6, a["inicio_questoes"], "o título da seção, não a linha do sumário que o cita")
        self.assertEqual([8], a["secoes"]["gabarito"])
        self.assertEqual([9], a["secoes"]["resumo"])
        self.assertEqual({"FCC": 2, "CEBRASPE": 1}, a["bancas"])
        self.assertEqual(1, a["vazias"])

    def test_relatorio_resume_por_curso(self):
        md = ea.relatorio(self.conn, ["Redes de Computadores", "Nao Existe"], 3)
        self.assertIn("| 00 - Curso Regular\\09 - Redes de Computadores | 1 | 1 | 1 | 1 | 1 |", md)
        self.assertIn("_nenhum arquivo casou_", md)


if __name__ == "__main__":
    unittest.main()
