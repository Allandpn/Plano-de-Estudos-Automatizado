#!/usr/bin/env python3
"""Testes de integracao/estrutura_apostilas.py com um índice sintético no formato real das apostilas."""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estrutura_apostilas as ea  # noqa: E402
from test_worker import SCHEMA_INDICE  # noqa: E402


def pontilhar(texto, pagina):
    """Como a extração devolve a linha do sumário: pontos intercalados com as letras."""
    return "." + "..".join(texto) + "." * 40 + f" {pagina}"


SUMARIO = "\n".join(["Índice",
                     pontilhar("1). NAT e PAT - Teoria", 3),
                     pontilhar("2). NAT e PAT - Questões Comentadas - CEBRASPE", 6),
                     pontilhar("3). NAT e PAT - Lista de Questões - FCC", 8),
                     pontilhar("4). Protocolo IPv6 - Resumo", 10)])
PAGINAS = ["Redes de Computadores - Curso Regular\nAula 06", SUMARIO,
           "NAT E PAT\nteoria do NAT", "mais teoria", "teoria", "NAT e PAT - Q C - UESTÕES OMENTADAS\n1. (CEBRASPE - PF)",
           "2. (CEBRASPE - TCU)", "NAT e PAT - lista\n1. (FCC - TRT)", "Gabarito 1-A", "PROTOCOLO IPV6 resumo"]


class EstruturaTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.conn = sqlite3.connect(Path(self._tmp.name) / "i.db")
        self.conn.executescript(SCHEMA_INDICE)
        for i, (nome, paginas) in enumerate([("aula 06.pdf", PAGINAS), ("aviso.pdf", ["AVISO IMPORTANTE", "texto"])], 1):
            self.conn.execute("INSERT INTO arquivos (caminho, curso, nome_arquivo, n_paginas) VALUES (?, ?, ?, ?)",
                              (f"x{i}", "00 - Curso Regular\\09 - Redes de Computadores", nome, len(paginas)))
            for p, t in enumerate(paginas, 1):
                self.conn.execute("INSERT INTO paginas (arquivo_id, pagina, texto) VALUES (?, ?, ?)", (i, p, t))
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        self._tmp.cleanup()

    def test_decodifica_a_linha_pontilhada_do_sumario(self):
        self.assertEqual("1) NAT e PAT - Teoria 3", ea.decodificar(pontilhar("1). NAT e PAT - Teoria", 3)))
        e = ea.entrada_do_sumario(pontilhar("2). NAT e PAT - Questões Comentadas - CEBRASPE", 6))
        self.assertEqual({"n": 2, "tema": "NAT e PAT", "tipo": "questoes_comentadas", "banca": "CEBRASPE",
                          "rotulo": "CEBRASPE", "pagina": 6}, e)
        self.assertEqual("CEBRASPE", ea.entrada_do_sumario("3) Redes - Questões Comentadas - Cebraspe 9")["banca"])
        self.assertIsNone(ea.entrada_do_sumario("texto corrido da aula"))

    def test_aula_le_tema_tipo_banca_e_confere_a_pagina(self):
        a = ea.analisar_aula(self.conn, 1)
        self.assertEqual(["teoria", "questoes_comentadas", "lista_questoes", "resumo"], [e["tipo"] for e in a["entradas"]])
        self.assertEqual("FCC", a["entradas"][2]["banca"])
        self.assertEqual((0, 4, 4), a["deslocamento"], "a página do sumário é a do PDF; o tema está escrito nela")
        self.assertFalse(a["fora"])

    def test_bruto_mostra_a_pagina_crua_e_decodificada(self):
        md = ea.bruto(self.conn, "aula 06")
        self.assertIn("NAT e PAT - Teoria 3", md)
        self.assertIn("- p. 6: NAT e PAT - Q C - UESTÕES OMENTADAS", md)
        self.assertIn("nenhum arquivo casou", ea.bruto(self.conn, "nao existe"))

    def test_arquivo_curto_sem_sumario_fica_fora(self):
        self.assertTrue(ea.analisar_aula(self.conn, 2)["fora"])

    def test_relatorio_resume_por_curso(self):
        md = ea.relatorio(self.conn, ["Redes de Computadores", "Nao Existe"], 3)
        self.assertIn("| 2 | 1 | 1 | 4 | 100% | 50% | +0 (4/4) |", md)
        self.assertIn("_nenhum arquivo casou_", md)


if __name__ == "__main__":
    unittest.main()
