#!/usr/bin/env python3
"""
Testes de integracao/prova_pdf.py: do PDF da prova às linhas, com OCR por bandas.

Rodar (da raiz do repositório):
    python -m unittest discover -s integracao -p "test_*.py"

Sem Tesseract de verdade: um Tesseract falso devolve o TSV que o real devolveria para cada
banda — inclusive o fragmento de lixo que ele produz quando a borda da banda parte uma linha.
O OCR de verdade é conferido no Pi (item 24.8 do SGE), com a prova da FCC.
"""

import sys
import tempfile
import unittest
from pathlib import Path

import fitz
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prova_pdf as pp  # noqa: E402


def montar_tsv(linhas):
    """[(texto, topo_px, altura_px[, conf])] -> o TSV do Tesseract (uma linha de texto por entrada)."""
    saida = ["level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext"]
    for i, item in enumerate(linhas, 1):
        texto, topo, altura = item[0], item[1], item[2]
        conf = item[3] if len(item) > 3 else 95.0
        for j, palavra in enumerate(texto.split(), 1):
            saida.append(f"5\t1\t1\t1\t{i}\t{j}\t{j * 50}\t{int(topo)}\t40\t{int(altura)}\t{conf}\t{palavra}")
    return "\n".join(saida)


def simular_ocr(faixas, verdade, altura=40):
    """verdade: [(texto, y_centro_px)] -> um TSV por banda, como o Tesseract devolveria: a linha
    inteira dentro da banda sai certa; a linha que a borda parte vira um fragmento de lixo."""
    tsvs = []
    for y0, y1 in faixas:
        linhas = []
        for texto, yc in verdade:
            topo, base = yc - altura / 2, yc + altura / 2
            if topo >= y0 and base <= y1:
                linhas.append((texto, topo - y0, altura))
            elif base > y0 and topo < y1:
                vis_topo, vis_base = max(topo, y0), min(base, y1)
                linhas.append(("lixo", vis_topo - y0, vis_base - vis_topo, 30.0))
        tsvs.append(montar_tsv(linhas))
    return tsvs


class TesseractFalso:
    def __init__(self, tsvs=(), disponivel=True):
        self.tsvs = list(tsvs)
        self._disponivel = disponivel
        self.chamadas = 0

    def disponivel(self):
        return self._disponivel

    def tsv(self, png):
        self.chamadas += 1
        assert png[:4] == b"\x89PNG", "o OCR recebe uma imagem PNG"
        return self.tsvs.pop(0)


def png_liso(largura=60, altura=60, tom=200):
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, largura, altura), False)
    pix.clear_with(tom)
    return pix.tobytes("png")


class TsvTest(unittest.TestCase):
    def test_palavras_viram_linha_na_ordem_e_com_confianca_media(self):
        tsv = montar_tsv([("Assinale a opção", 100, 30, 90.0), ("correta", 140, 30, 70.0)])

        linhas = pp.linhas_do_tsv(tsv)

        self.assertEqual(["Assinale a opção", "correta"], [l[0] for l in linhas])
        self.assertEqual((100, 130), (linhas[0][1], linhas[0][2]))
        self.assertAlmostEqual(70.0, linhas[1][3])

    def test_ruido_sem_confianca_e_palavra_vazia_ficam_de_fora(self):
        cabecalho = montar_tsv([]).splitlines()[0]
        tsv = "\n".join([cabecalho,
                         "5\t1\t1\t1\t1\t1\t0\t10\t40\t20\t-1\truido",
                         "5\t1\t1\t1\t1\t2\t50\t10\t40\t20\t95\tbom",
                         "5\t1\t1\t1\t1\t3\t90\t10\t40\t20\t95\t ",
                         "4\t1\t1\t1\t1\t0\t0\t10\t40\t20\t-1\t"])

        self.assertEqual(["bom"], [l[0] for l in pp.linhas_do_tsv(tsv)])


class BandasTest(unittest.TestCase):
    def test_pagina_que_cabe_vai_inteira(self):
        self.assertEqual([(0, 2339)], pp.bandas(2339))

    def test_pagina_alta_vira_bandas_que_se_sobrepoem_e_cobrem_tudo(self):
        faixas = pp.bandas(6666)

        self.assertEqual(0, faixas[0][0])
        self.assertEqual(6666, faixas[-1][1])
        for (a0, a1), (b0, b1) in zip(faixas, faixas[1:]):
            self.assertEqual(pp.SOBREPOSICAO_PX, a1 - b0, "cada banda começa a uma sobreposição do fim da anterior")
            self.assertLessEqual(a1 - a0, pp.BANDA_PX)

    def test_d_l_linha_partida_pela_emenda_sai_uma_vez_inteira_e_sem_lixo(self):
        altura = 6666
        faixas = pp.bandas(altura)
        # Linhas ao longo da página, entre elas as que caem exatamente nas emendas.
        verdade = [(f"linha{n}", y) for n, y in enumerate([30, 500, 1790, 1800, 1900, 2000, 2030, 2100, 3000,
                                                            3590, 3700, 3900, 5400, 5500, 6600])]

        tsvs = simular_ocr(faixas, verdade)
        unidas = pp.unir_bandas(faixas, [pp.linhas_do_tsv(t) for t in tsvs])

        self.assertEqual([t for t, _ in verdade], [t for t, _, _ in unidas],
                         "cada linha aparece uma vez, na ordem, e o lixo das emendas some")

    def test_a_ordem_de_leitura_do_tesseract_dentro_da_banda_e_preservada(self):
        # Duas colunas: o Tesseract lê a esquerda inteira e depois a direita (y se repete).
        faixas = [(0, 2339)]
        tsv = montar_tsv([("coluna esquerda 1", 100, 30), ("coluna esquerda 2", 200, 30),
                          ("coluna direita 1", 100, 30), ("coluna direita 2", 200, 30)])

        unidas = pp.unir_bandas(faixas, [pp.linhas_do_tsv(tsv)])

        self.assertEqual(["coluna esquerda 1", "coluna esquerda 2", "coluna direita 1", "coluna direita 2"],
                         [t for t, _, _ in unidas], "nunca se reordena por y: isso intercalaria as colunas")


class LerProvaTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def pdf_com_texto(self):
        caminho = self.dir / "texto.pdf"
        c = canvas.Canvas(str(caminho))
        for pagina in (1, 2):
            for i in range(6):
                c.drawString(72, 750 - i * 20, f"Linha {i + 1} da pagina {pagina} com texto suficiente para contar")
            c.showPage()
        c.save()
        return caminho

    def pdf_de_imagens_empilhadas(self, fatias=3, altura_fatia=800):
        """Uma página alta com `fatias` imagens empilhadas, como a prova da FCC."""
        caminho = self.dir / "tira.pdf"
        doc = fitz.open()
        pagina = doc.new_page(width=595, height=altura_fatia * fatias)
        for k in range(fatias):
            pagina.insert_image(fitz.Rect(0, k * altura_fatia, 595, (k + 1) * altura_fatia), stream=png_liso(tom=180 + k * 20))
        doc.save(str(caminho))
        return caminho

    def test_pdf_com_texto_nao_usa_ocr_nem_guarda_imagem(self):
        tesseract = TesseractFalso()

        leitura = pp.ler_prova(self.pdf_com_texto(), self.dir / "paginas", tesseract)

        self.assertFalse(leitura.usou_ocr)
        self.assertEqual(0, tesseract.chamadas)
        self.assertEqual([], leitura.imagens)
        self.assertEqual(12, len(leitura.linhas))
        self.assertTrue(all(not l.ocr and l.imagem is None for l in leitura.linhas))
        self.assertEqual({1, 2}, {l.pagina for l in leitura.linhas})
        self.assertFalse((self.dir / "paginas").exists())

    def test_pdf_de_imagem_usa_ocr_guarda_as_imagens_e_diz_de_qual_veio_cada_linha(self):
        caminho = self.pdf_de_imagens_empilhadas()
        escala = pp.DPI / 72
        faixas = pp.bandas(int(2400 * escala))
        # Linhas nas três imagens (cada uma com 800 pt): y em pontos -> px.
        verdade = [("na primeira imagem", 100 * escala), ("na segunda imagem", 900 * escala),
                   ("na emenda da segunda com a terceira", 1595 * escala), ("na terceira imagem", 2000 * escala)]
        tesseract = TesseractFalso(simular_ocr(faixas, verdade))

        leitura = pp.ler_prova(caminho, self.dir / "paginas", tesseract)

        self.assertTrue(leitura.usou_ocr)
        self.assertEqual(len(faixas), tesseract.chamadas)
        self.assertEqual(["01.png", "02.png", "03.png"], leitura.imagens)
        for nome in leitura.imagens:
            self.assertTrue((self.dir / "paginas" / nome).is_file(), "a imagem fica para o usuário conferir (D-85)")
        self.assertEqual([t for t, _ in verdade], [l.texto for l in leitura.linhas])
        self.assertEqual([1, 2, 2, 3], [l.imagem for l in leitura.linhas])
        self.assertTrue(all(l.ocr and l.confianca > 0 for l in leitura.linhas))

    def test_prova_de_texto_com_pagina_em_branco_nao_vira_prova_de_imagem(self):
        # A FGV entrega páginas em branco e de figura no meio de uma prova de texto.
        caminho = self.dir / "hibrido.pdf"
        c = canvas.Canvas(str(caminho))
        for pagina in (1, 2, 3):
            for i in range(6):
                c.drawString(72, 750 - i * 20, f"Linha {i + 1} da pagina {pagina} com texto suficiente para contar")
            c.showPage()
        c.showPage()  # página 4, em branco
        c.save()

        leitura = pp.ler_prova(caminho, self.dir / "paginas", TesseractFalso(disponivel=False))

        self.assertFalse(leitura.usou_ocr)
        self.assertEqual(18, len(leitura.linhas), "a página em branco não dá linha nem exige OCR")

    def test_pagina_de_imagem_sem_tesseract_recusa_com_o_motivo(self):
        with self.assertRaises(pp.ProvaIlegivel) as e:
            pp.ler_prova(self.pdf_de_imagens_empilhadas(), self.dir / "paginas", TesseractFalso(disponivel=False))

        self.assertIn("OCR", str(e.exception))

    def test_arquivo_que_nao_e_pdf_recusa(self):
        ruim = self.dir / "ruim.pdf"
        ruim.write_bytes(b"isto nao e um pdf")

        with self.assertRaises(pp.ProvaIlegivel):
            pp.ler_prova(ruim, self.dir / "paginas", TesseractFalso())

    def test_tesseract_real_ausente_vira_mensagem_clara(self):
        t = pp.Tesseract(executavel="tesseract-que-nao-existe")

        self.assertFalse(t.disponivel())
        with self.assertRaises(pp.ProvaIlegivel) as e:
            t.tsv(png_liso())
        self.assertIn("não está instalado", str(e.exception))


class TextoDoArquivoTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_texto_colado_e_uma_pagina(self):
        arquivo = self.dir / "gabarito.txt"
        arquivo.write_text("1 A\n2 B\n3 *", encoding="utf-8")

        self.assertEqual(["1 A\n2 B\n3 *"], pp.texto_do_arquivo(arquivo))

    def test_pdf_com_texto_uma_pagina_cada(self):
        caminho = self.dir / "g.pdf"
        c = canvas.Canvas(str(caminho))
        c.drawString(72, 750, "GABARITO pagina um")
        c.showPage()
        c.drawString(72, 750, "GABARITO pagina dois")
        c.showPage()
        c.save()

        paginas = pp.texto_do_arquivo(caminho)

        self.assertEqual(2, len(paginas))
        self.assertIn("pagina dois", paginas[1])

    def test_gabarito_em_imagem_recusa_com_o_motivo(self):
        caminho = self.dir / "imagem.pdf"
        doc = fitz.open()
        doc.new_page().insert_image(fitz.Rect(0, 0, 300, 300), stream=png_liso())
        doc.save(str(caminho))

        with self.assertRaises(pp.ProvaIlegivel) as e:
            pp.texto_do_arquivo(caminho)
        self.assertIn("imagem", str(e.exception))


if __name__ == "__main__":
    unittest.main()
