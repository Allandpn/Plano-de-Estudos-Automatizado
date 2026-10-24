"""Testes de integracao/pdf_questoes.py: o PDF "Questões deste assunto" (capa + páginas), com avisos em vez de erro."""
import json
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader, PdfWriter

import pdf_questoes as pq


def pdf_de(caminho, paginas):
    w = PdfWriter()
    for _ in range(paginas):
        w.add_blank_page(width=200, height=200)
    with open(caminho, "wb") as f:
        w.write(f)


class MontarTest(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.pdf = str(self.t / "aula.pdf")
        pdf_de(self.pdf, 10)

    def test_capa_mais_paginas(self):
        r = pq.montar("Questões", [{"arquivo": self.pdf, "paginas": "2-4,8", "rotulo": "aula: questões de X"}], self.t / "o.pdf")
        self.assertEqual(4, r["paginas"])
        self.assertEqual([], r["avisos"])
        self.assertEqual(r["capa"] + 4, len(PdfReader(str(self.t / "o.pdf")).pages))
        self.assertFalse((self.t / "o.pdf.capa.pdf").exists())

    def test_pagina_fora_e_repetida_viram_aviso(self):
        faixas = [{"arquivo": self.pdf, "paginas": "9-12", "rotulo": "a"}, {"arquivo": self.pdf, "paginas": "10", "rotulo": "b"}]
        r = pq.montar("Q", faixas, self.t / "o.pdf")
        self.assertEqual(2, r["paginas"])
        self.assertEqual(3, len(r["avisos"]))

    def test_arquivo_inexistente_sem_nada_utilizavel(self):
        r = pq.montar("Q", [{"arquivo": str(self.t / "nao.pdf"), "paginas": "1", "rotulo": "a"}], self.t / "o.pdf")
        self.assertIsNone(r)
        self.assertFalse((self.t / "o.pdf").exists())

    def test_montar_todos(self):
        pasta = self.t / "ed"
        (pasta / "questoes").mkdir(parents=True)
        (pasta / "questoes" / "abc.json").write_text(json.dumps(
            [{"arquivo": self.pdf, "paginas": "1-3", "rotulo": "r"}]), encoding="utf-8")
        (pasta / "assuntos.json").write_text(json.dumps([{"chave": "abc", "disciplina": "D", "assunto": "A"}]), encoding="utf-8")
        r = pq.montar_todos(pasta)
        self.assertEqual([("abc", "abc.pdf", 3)], [(x["chave"], x["arquivo"], x["paginas"]) for x in r])
        self.assertTrue((pasta / "consulta" / "abc.pdf").exists())
        self.assertTrue((pasta / "consulta" / "consulta.json").exists())


if __name__ == "__main__":
    unittest.main()
