#!/usr/bin/env python3
"""
Testes de dias/montar_bloco.py — o fatiador não pode perder página em silêncio.

Rodar:  python -m unittest dias/test_montar_bloco.py   (da raiz do repositório)
Só biblioteca padrão + pypdf/reportlab, que o projeto já usa.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
import montar_bloco as mb  # noqa: E402


def criar_pdf(caminho, n_paginas, secoes=()):
    """PDF de teste com 'pagina N' escrito em cada página e marcadores nas páginas dadas."""
    tmp = caminho.with_suffix(".tmp.pdf")
    c = canvas.Canvas(str(tmp))
    for i in range(1, n_paginas + 1):
        c.drawString(100, 750, f"pagina {i}")
        c.showPage()
    c.save()
    writer = PdfWriter()
    for pg in PdfReader(str(tmp)).pages:
        writer.add_page(pg)
    for p in secoes:
        writer.add_outline_item(f"Seção {p}", p - 1)
    with open(caminho, "wb") as f:
        writer.write(f)
    tmp.unlink()


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.saida = self.dir / "saida"
        criar_pdf(self.dir / "aula.pdf", 40)

    def tearDown(self):
        self._tmp.cleanup()

    def manifesto(self, **campos):
        dados = {
            "assunto_uuid": "uuid-teste",
            "edital": "TESTE",
            "titulo": "Assunto de teste",
            "subitens": ["A", "B"],
            "fontes": [{"arquivo": "aula.pdf", "paginas": "1-10", "cobre": ["A", "B"]}],
        }
        dados.update(campos)
        caminho = self.dir / "m.json"
        caminho.write_text(json.dumps(dados), encoding="utf-8")
        return caminho

    def rodar(self, refatiar=False, **campos):
        return mb.montar_bloco(self.manifesto(**campos), self.saida, refatiar=refatiar)

    def erros(self, **campos):
        with self.assertRaises(mb.ManifestoInvalido) as ctx:
            self.rodar(**campos)
        self.assertFalse(self.saida.exists(), "com erro, nada pode ser gerado")
        return "\n".join(ctx.exception.erros)


class Validacao(Base):
    def test_faixa_invertida_e_erro(self):
        self.assertIn("faixa invertida", self.erros(fontes=[{"arquivo": "aula.pdf", "paginas": "30-20", "cobre": ["A", "B"]}]))

    def test_arquivo_inexistente_e_erro(self):
        self.assertIn("arquivo não encontrado", self.erros(fontes=[{"arquivo": "nao.pdf", "paginas": "1-3", "cobre": ["A", "B"]}]))

    def test_pagina_fora_do_pdf_e_erro(self):
        self.assertIn("não existem", self.erros(fontes=[{"arquivo": "aula.pdf", "paginas": "38-45", "cobre": ["A", "B"]}]))

    def test_sobreposicao_e_erro(self):
        msg = self.erros(fontes=[
            {"arquivo": "aula.pdf", "paginas": "1-12", "cobre": ["A"]},
            {"arquivo": "aula.pdf", "paginas": "10-14", "cobre": ["B"]},
        ])
        self.assertIn("aparece duas vezes", msg)

    def test_descarte_nao_pode_sobrepor_fonte(self):
        msg = self.erros(descartes=[{"arquivo": "aula.pdf", "paginas": "5-20", "motivo": "repetido"}])
        self.assertIn("aparece duas vezes", msg)

    def test_subitem_sem_cobertura_e_erro(self):
        msg = self.erros(subitens=["A", "B", "C"])
        self.assertIn("'C' sem nenhuma página", msg)

    def test_cobre_subitem_desconhecido_e_erro(self):
        msg = self.erros(fontes=[{"arquivo": "aula.pdf", "paginas": "1-10", "cobre": ["A", "B", "Z"]}])
        self.assertIn("'Z', que não está em 'subitens'", msg)

    def test_subitens_obrigatorio(self):
        self.assertIn("'subitens' é obrigatório", self.erros(subitens=[]))

    def test_lacuna_declarada_cobre_o_subitem(self):
        _, segmentos = self.rodar(subitens=["A", "B", "C"], lacunas=[{"subitem": "C", "motivo": "não há no acervo"}])
        self.assertEqual(1, len(segmentos))

    def test_lacuna_sem_motivo_e_erro(self):
        self.assertIn("sem 'motivo'", self.erros(subitens=["A", "B", "C"], lacunas=[{"subitem": "C"}]))

    def test_todos_os_erros_de_uma_vez(self):
        msg = self.erros(subitens=["A", "B", "C"], fontes=[
            {"arquivo": "aula.pdf", "paginas": "30-20", "cobre": ["A"]},
            {"arquivo": "nao.pdf", "paginas": "1-3", "cobre": ["B"]},
        ])
        for trecho in ("faixa invertida", "arquivo não encontrado", "'C' sem nenhuma página"):
            self.assertIn(trecho, msg)


class Corte(Base):
    def paginas_geradas(self, segmentos):
        return [p["pagina_original"] for sg in segmentos for p in sg["_bloco"]]

    def test_nenhuma_pagina_se_perde_nem_se_repete(self):
        fontes = [{"arquivo": "aula.pdf", "paginas": "1-12,20-33,38-40", "cobre": ["A", "B"]}]
        _, segmentos = self.rodar(fontes=fontes)
        esperado = list(range(1, 13)) + list(range(20, 34)) + list(range(38, 41))
        self.assertEqual(esperado, self.paginas_geradas(segmentos))

    def test_corta_na_troca_de_fonte(self):
        criar_pdf(self.dir / "outra.pdf", 10)
        fontes = [
            {"arquivo": "aula.pdf", "paginas": "1-10", "cobre": ["A"]},
            {"arquivo": "outra.pdf", "paginas": "1-10", "cobre": ["B"]},
        ]
        _, segmentos = self.rodar(fontes=fontes)  # 80 min -> 2 blocos de 40, corte na troca de arquivo
        self.assertEqual([1], [len({p["arquivo"] for p in sg["_bloco"]}) for sg in segmentos[:1]])
        self.assertEqual(2, len(segmentos))
        self.assertEqual([], segmentos[0]["alertas"])

    def test_corta_no_inicio_de_secao_do_pdf(self):
        criar_pdf(self.dir / "secoes.pdf", 20, secoes=(9,))
        _, segmentos = self.rodar(fontes=[{"arquivo": "secoes.pdf", "paginas": "1-20", "cobre": ["A", "B"]}])
        self.assertEqual(8, len(segmentos[0]["_bloco"]), "corta antes da página 9, onde começa a seção")
        self.assertEqual([], segmentos[0]["alertas"])

    def test_sem_fronteira_corta_no_alvo_e_avisa(self):
        _, segmentos = self.rodar(fontes=[{"arquivo": "aula.pdf", "paginas": "1-40", "cobre": ["A", "B"]}])
        self.assertIn("corte no meio de seção", segmentos[0]["alertas"])
        self.assertEqual(40, len(self.paginas_geradas(segmentos)))

    def test_fixacao_nunca_se_mistura_com_teoria(self):
        fontes = [
            {"arquivo": "aula.pdf", "paginas": "1-5", "cobre": ["A", "B"]},
            {"arquivo": "aula.pdf", "paginas": "30-32", "cobre": ["A"], "tipo": "fixacao"},
        ]
        _, segmentos = self.rodar(fontes=fontes)  # só 32 min no total, mas tipos diferentes
        self.assertEqual(["teoria", "fixacao"], [sg["tipo"] for sg in segmentos])

    def test_minutos_por_pagina_por_fonte(self):
        fontes = [{"arquivo": "aula.pdf", "paginas": "1-10", "cobre": ["A", "B"], "minutos_por_pagina": 2}]
        _, segmentos = self.rodar(fontes=fontes)
        self.assertEqual(20, segmentos[0]["tempo_estimado_min"])


class Registro(Base):
    def test_faixas_reais_e_intervalo_so_quando_continuo(self):
        fontes = [{"arquivo": "aula.pdf", "paginas": "1-3,8-9", "cobre": ["A", "B"]}]
        registro, _ = self.rodar(fontes=fontes)
        pedaco = json.loads(registro.read_text(encoding="utf-8"))["pedacos"][0]
        self.assertEqual([{"arquivo": "aula.pdf", "paginas": "1-3,8-9"}], pedaco["faixas"])
        self.assertIsNone(pedaco["pagina_inicial"], "1-3 e 8-9 não podem virar 'páginas 1 a 9'")
        self.assertIsNone(pedaco["pagina_final"])

    def test_intervalo_preenchido_quando_continuo(self):
        registro, _ = self.rodar()
        pedaco = json.loads(registro.read_text(encoding="utf-8"))["pedacos"][0]
        self.assertEqual((1, 10), (pedaco["pagina_inicial"], pedaco["pagina_final"]))

    def test_relatorio_de_cobertura_gerado(self):
        self.rodar(subitens=["A", "B", "C"], lacunas=[{"subitem": "C", "motivo": "sem material"}],
                   descartes=[{"arquivo": "aula.pdf", "paginas": "11-20", "motivo": "repete aula 02"}])
        texto = (self.saida / "assunto-de-teste_cobertura.md").read_text(encoding="utf-8")
        self.assertIn("❌ lacuna — sem material", texto)
        self.assertIn("repete aula 02", texto)
        self.assertIn("pagina 1", texto, "mostra o começo do texto da primeira página da faixa")

    def test_assunto_todo_em_lacuna_nao_gera_segmento(self):
        registro, segmentos = self.rodar(fontes=[], lacunas=[
            {"subitem": "A", "motivo": "sem material"}, {"subitem": "B", "motivo": "sem material"}])
        self.assertEqual([], segmentos)
        self.assertEqual([], json.loads(registro.read_text(encoding="utf-8"))["pedacos"])


class Refatiar(Base):
    def test_reexecutar_igual_mantem_as_chaves(self):
        r1, _ = self.rodar()
        chave1 = json.loads(r1.read_text(encoding="utf-8"))["pedacos"][0]["chave_externa_segmento"]
        r2, _ = self.rodar()
        chave2 = json.loads(r2.read_text(encoding="utf-8"))["pedacos"][0]["chave_externa_segmento"]
        self.assertEqual(chave1, chave2)

    def test_mudar_o_corte_exige_refatiar(self):
        self.rodar(fontes=[{"arquivo": "aula.pdf", "paginas": "1-30", "cobre": ["A", "B"]}])
        with self.assertRaises(mb.ManifestoInvalido) as ctx:
            self.rodar(fontes=[{"arquivo": "aula.pdf", "paginas": "1-30", "cobre": ["A", "B"]}], minutos_por_bloco=30)
        self.assertIn("--refatiar", "\n".join(ctx.exception.erros))

    def test_refatiar_remove_pdfs_que_sobraram(self):
        self.rodar(fontes=[{"arquivo": "aula.pdf", "paginas": "1-30", "cobre": ["A", "B"]}], minutos_por_bloco=30)
        pasta = self.saida / "blocos" / "assunto-de-teste"
        antes = len(list(pasta.glob("segmento-*.pdf")))
        _, segmentos = self.rodar(refatiar=True, fontes=[{"arquivo": "aula.pdf", "paginas": "1-30", "cobre": ["A", "B"]}])
        self.assertGreater(antes, len(segmentos))
        self.assertEqual(len(segmentos), len(list(pasta.glob("segmento-*.pdf"))))

    def test_mudar_o_titulo_exige_refatiar(self):
        self.rodar()
        with self.assertRaises(mb.ManifestoInvalido):
            self.rodar(titulo="Outro título")


if __name__ == "__main__":
    unittest.main()
