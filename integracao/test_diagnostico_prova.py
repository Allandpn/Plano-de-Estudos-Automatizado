#!/usr/bin/env python3
"""Testes de integracao/diagnostico_prova.py, sem SGE nem PDF de verdade."""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import diagnostico_prova as dg  # noqa: E402
from test_worker import SCHEMA_INDICE  # noqa: E402

PDFS = {
    "seg-redes.pdf": ["Modelo OSI e suas camadas", "VLAN e o padrão 802.1Q", "Alta disponibilidade: cluster ativo-passivo"],
    "seg-nuvem.pdf": ["Nuvem pública, nuvem privada e nuvem híbrida"],
}


def abrir_falso(caminho):
    return PDFS[Path(caminho).name]


class DiagnosticoTest(unittest.TestCase):
    def setUp(self):
        self.material = dg.MaterialDoConcurso(
            {91: [{"id": 1, "arquivo": "/material/blocos/redes/seg-redes.pdf"}],
             92: [{"id": 2, "arquivo": "/material/blocos/nuvem/seg-nuvem.pdf"}]},
            "/nao/importa", abrir_pdf=abrir_falso)
        self._tmp = tempfile.TemporaryDirectory()
        self.indice = Path(self._tmp.name) / "indice.db"
        conn = sqlite3.connect(self.indice)
        conn.executescript(SCHEMA_INDICE)
        conn.execute("INSERT INTO arquivos (caminho, curso, nome_arquivo, n_paginas) VALUES ('x', 'TSE\\Redes', 'aula 05.pdf', 2)")
        conn.execute("INSERT INTO paginas (arquivo_id, pagina, texto) VALUES (1, 1, 'O protocolo BGP e o atributo LOCAL_PREF')")
        conn.commit()
        conn.close()
        self.nomes = {91: "Infraestrutura e redes", 92: "Computação em nuvem"}

    def tearDown(self):
        self._tmp.cleanup()

    def causa(self, conceitos, assunto_id=91):
        return dg.classificar({"numero": 1, "assuntoId": assunto_id}, conceitos, self.material, str(self.indice), self.nomes)

    def test_no_segmento_do_assunto_e_o_julgador_que_nao_viu(self):
        causa, evid = self.causa(["alta disponibilidade"])
        self.assertEqual("JULGADOR", causa)
        self.assertIn("S1-p3", evid[0][2][0])

    def test_no_material_de_outro_assunto_e_atribuicao(self):
        causa, evid = self.causa(["nuvem hibrida"])
        self.assertEqual("ATRIBUICAO", causa, "sem acento casa com acento")
        self.assertIn("Computação em nuvem", evid[0][2][0])

    def test_so_no_acervo_e_a_cadeia_e_em_lugar_nenhum_e_o_acervo(self):
        self.assertEqual("CADEIA", self.causa(["LOCAL_PREF"])[0])
        self.assertEqual("ACERVO", self.causa(["PgBouncer"])[0])

    def test_o_conceito_mais_longe_decide_a_questao(self):
        self.assertEqual("ACERVO", self.causa(["VLAN", "PgBouncer"])[0])
        self.assertEqual("SEM_TERMO", self.causa([])[0])

    def test_assunto_sem_segmento_cai_no_concurso_e_no_acervo(self):
        self.assertEqual("CADEIA", self.causa(["BGP"], assunto_id=10)[0])

    def test_relatorio_conta_as_causas(self):
        q = {"numero": 37, "veredito": "PARCIAL", "assunto": "Infraestrutura e redes", "assuntoId": 91}
        md = dg.relatorio_md({"provaId": 2, "nome": "TJ-CE"}, [(q, *self.causa(["VLAN"]))], [])
        self.assertIn("| JULGADOR | 1 |", md)
        self.assertIn("| 37 | PARCIAL |", md)


if __name__ == "__main__":
    unittest.main()
