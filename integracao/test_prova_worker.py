#!/usr/bin/env python3
"""
Testes de integracao/prova_worker.py: o ciclo das provas, de ponta a ponta, sem rede e sem IA de verdade.

Rodar (da raiz do repositório):
    python -m unittest discover -s integracao -p "test_*.py"

SGE falso em memória, IA falsa com respostas roteirizadas, PDFs gerados numa pasta temporária (a
prova, o gabarito em texto e os segmentos do material). Cada teste nomeia o tipo de problema que
protege: IA indisponível espera, prova ilegível falha com o motivo, gabarito que não serve faz a
prova esperar com o motivo ao lado.
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import fitz
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prova_worker as pw  # noqa: E402
from sge_api import ErroSge  # noqa: E402

TEMAS = ["contratos", "redes", "banco", "seguranca", "governanca", "processos", "arquitetura", "nuvem",
         "criptografia", "backup", "auditoria", "licitacao", "logica", "estatistica", "portugues", "ingles"]


def tema(n):
    return f"{TEMAS[n % len(TEMAS)]} {chr(97 + n // len(TEMAS))}"


class SgeFalso:
    def __init__(self, pendentes=(), dados=None, respostas_ia=(), julgamento=None):
        self.pendentes = pendentes if isinstance(pendentes, Exception) else list(pendentes)
        self.dados = dados
        self.respostas_ia = list(respostas_ia)
        self.julgamento = julgamento
        self.pedidos_ia = []
        self.tentativas_de_leitura, self.leituras, self.gabaritos, self.vereditos, self.falhas = [], [], [], [], []
        self.erro_na_primeira_leitura = None
        self.erro_em_dados = {}

    def provas_pendentes(self):
        if isinstance(self.pendentes, Exception):
            raise self.pendentes
        return self.pendentes

    def prova_dados_leitura(self, prova_id):
        if prova_id in self.erro_em_dados:
            raise self.erro_em_dados[prova_id]
        return self.dados

    def prova_entregar_leitura(self, prova_id, corpo):
        self.tentativas_de_leitura.append(corpo)
        if self.erro_na_primeira_leitura and len(self.tentativas_de_leitura) == 1:
            raise self.erro_na_primeira_leitura
        self.leituras.append((prova_id, corpo))

    def prova_entregar_gabarito(self, prova_id, corpo):
        self.gabaritos.append((prova_id, corpo))

    def prova_para_julgar(self, prova_id):
        return self.julgamento

    def prova_vereditos(self, prova_id, corpo):
        self.vereditos.append((prova_id, corpo))
        return {"gravados": len(corpo["itens"]), "rebaixados": [], "recusados": []}

    def prova_falha(self, prova_id, etapa, erro):
        self.falhas.append((prova_id, etapa, erro))

    def completar(self, sistema, usuario):
        self.pedidos_ia.append(usuario)
        resposta = self.respostas_ia.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta if isinstance(resposta, str) else json.dumps(resposta)


class TesseractFalso:
    def __init__(self, disponivel=False):
        self._disponivel = disponivel

    def disponivel(self):
        return self._disponivel


def gab(n, situacao="DEFINITIVO"):
    return {"encontrado": True, "situacao": situacao, "recorte": "Cargo X, tipo 1",
            "respostas": [{"numero": i, "resposta": "ABCDE"[(i - 1) % 5]} for i in range(1, n + 1)]}


def atrib(numeros, chave="a-redes", confianca="ALTA"):
    return {"atribuicoes": [{"numero": n, "assunto": chave, "confianca": confianca} for n in numeros]}


def pendente(prova_id=1, status="LENDO"):
    return {"id": prova_id, "status": status, "concursoId": 1, "nome": "prova.pdf", "tipo": None,
            "gabaritoArquivo": "gabarito.txt", "jaLida": False}


def dados_de_leitura(prova_id=1, gabarito="gabarito.txt", ja_lida=False, numeros=()):
    return {"id": prova_id, "status": "LENDO", "concursoId": 1, "nome": "prova.pdf", "tipo": None, "cargoProva": None,
            "formato": "MULTIPLA_ESCOLHA" if ja_lida else None, "arquivoProva": f"entrada/{prova_id}/prova.pdf",
            "gabaritoArquivo": gabarito, "jaLida": ja_lida, "numerosDasQuestoes": list(numeros),
            "assuntos": [{"chaveExterna": "a-redes", "nome": "Redes", "disciplina": "TI"},
                         {"chaveExterna": "a-lgpd", "nome": "LGPD", "disciplina": "Direito"}]}


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self._tmp.name)
        self.provas = self.raiz / "provas"
        self.material = self.raiz / "material"

    def tearDown(self):
        self._tmp.cleanup()

    def entrada(self, prova_id=1):
        pasta = self.provas / "entrada" / str(prova_id)
        pasta.mkdir(parents=True, exist_ok=True)
        return pasta

    def escrever_prova(self, prova_id=1, questoes=6):
        """Uma prova de texto no formato da FGV: número sozinho, enunciado, cinco alternativas."""
        c = canvas.Canvas(str(self.entrada(prova_id) / "prova.pdf"))
        y, pagina = 800, 1

        def cabecalho():
            nonlocal y
            c.drawString(60, 820, "FGV CONHECIMENTO")
            c.drawString(60, 806, f"TIPO 1 – PÁGINA {pagina}")
            y = 780

        cabecalho()
        for n in range(1, questoes + 1):
            if y < 140:
                c.showPage()
                pagina += 1
                cabecalho()
            c.drawString(60, y, str(n)); y -= 14
            c.drawString(60, y, f"Enunciado sobre {tema(n)} para conferir a leitura."); y -= 14
            for letra in "ABCDE":
                c.drawString(60, y, f"({letra}) alternativa {letra.lower()} sobre {tema(n + 3)}."); y -= 14
            y -= 6
        c.showPage()
        c.save()

    def escrever_gabarito(self, prova_id=1, texto="1 A 2 B 3 C"):
        (self.entrada(prova_id) / "gabarito.txt").write_text(texto, encoding="utf-8")

    def worker(self, sge, **kw):
        return pw.WorkerProvas(sge, self.provas, self.material, TesseractFalso(), **kw)


class LeituraTest(Base):
    def test_leitura_completa_entrega_questoes_gabarito_e_atribuicao(self):
        self.escrever_prova(questoes=6)
        self.escrever_gabarito()
        sge = SgeFalso([pendente()], dados_de_leitura(), [gab(6), atrib(range(1, 7))])

        feitas = self.worker(sge).ciclo()

        self.assertEqual(1, feitas)
        self.assertEqual([], sge.falhas)
        prova_id, corpo = sge.leituras[0]
        self.assertEqual(1, prova_id)
        self.assertEqual("MULTIPLA_ESCOLHA", corpo["formato"])
        self.assertEqual(6, len(corpo["questoes"]))
        self.assertEqual("DEFINITIVO", corpo["gabarito"]["situacao"])
        self.assertEqual(6, len(corpo["gabarito"]["respostas"]))
        self.assertIsNone(corpo["avisoGabarito"])
        for q in corpo["questoes"]:
            self.assertEqual(5, len(q["alternativas"]))
            self.assertEqual("a-redes", q["assuntoChaveExterna"])
            self.assertFalse(q["baixaConfianca"])
            self.assertIsNone(q["motivoNaoAvaliavel"])
        self.assertIn("Enunciado sobre", corpo["questoes"][0]["enunciado"])
        self.assertIn("TEXTO DO GABARITO", sge.pedidos_ia[0], "a primeira chamada é o gabarito")
        self.assertEqual(2, len(sge.pedidos_ia))

    def test_a_capa_fica_guardada_para_o_gabarito_que_chegar_depois(self):
        self.escrever_prova(questoes=3)
        sge = SgeFalso([pendente()], dados_de_leitura(gabarito=None), [atrib(range(1, 4))])

        self.worker(sge).ciclo()

        capa = (self.provas / "paginas" / "1" / "capa.txt").read_text(encoding="utf-8")
        self.assertIn("FGV CONHECIMENTO", capa)

    def test_a_banca_e_o_tipo_vem_da_capa_e_o_do_usuario_prevalece(self):
        self.escrever_prova(questoes=3)
        sge = SgeFalso([pendente()], dados_de_leitura(gabarito=None), [atrib(range(1, 4))])

        self.worker(sge).ciclo()

        corpo = sge.leituras[0][1]
        self.assertEqual("FGV", corpo["banca"])
        self.assertEqual("1", corpo["tipo"])

        sge2 = SgeFalso([pendente()], dict(dados_de_leitura(gabarito=None), tipo="3"), [atrib(range(1, 4))])
        self.worker(sge2).ciclo()
        self.assertEqual("3", sge2.leituras[0][1]["tipo"], "o tipo que o usuário informou vale mais que o da capa")

    def test_sem_arquivo_de_gabarito_a_prova_vai_sem_gabarito_e_sem_alarde(self):
        self.escrever_prova(questoes=3)
        sge = SgeFalso([pendente()], dados_de_leitura(gabarito=None), [atrib(range(1, 4))])

        self.worker(sge).ciclo()

        corpo = sge.leituras[0][1]
        self.assertIsNone(corpo["gabarito"])
        self.assertIsNone(corpo["avisoGabarito"])
        self.assertEqual(1, len(sge.pedidos_ia), "só a atribuição gasta IA")

    def test_d82_gabarito_de_total_muito_diferente_e_aviso_nunca_gabarito_errado(self):
        self.escrever_prova(questoes=6)
        self.escrever_gabarito()
        sge = SgeFalso([pendente()], dados_de_leitura(), [gab(20), atrib(range(1, 7))])

        self.worker(sge).ciclo()

        corpo = sge.leituras[0][1]
        self.assertIsNone(corpo["gabarito"])
        self.assertIn("20 respostas e a prova tem 6 questões", corpo["avisoGabarito"])

    def test_gabarito_com_poucas_a_mais_estende_a_numeracao_com_questoes_sem_texto(self):
        self.escrever_prova(questoes=6)
        self.escrever_gabarito()
        sge = SgeFalso([pendente()], dados_de_leitura(), [gab(8), atrib(range(1, 7))])

        self.worker(sge).ciclo()

        corpo = sge.leituras[0][1]
        self.assertEqual(8, len(corpo["questoes"]), "as questões 7 e 8 o segmentador não achou, mas o gabarito as tem")
        self.assertEqual(["SEM_TEXTO", "SEM_TEXTO"], [q["motivoNaoAvaliavel"] for q in corpo["questoes"][6:]])
        self.assertEqual(8, len(corpo["gabarito"]["respostas"]))

    def test_gabarito_que_a_ia_nao_acha_vira_aviso_com_o_motivo(self):
        self.escrever_prova(questoes=3)
        self.escrever_gabarito()
        sge = SgeFalso([pendente()], dados_de_leitura(), [{"encontrado": False, "motivo": "o cargo da capa não está no arquivo"},
                                                          atrib(range(1, 4))])

        self.worker(sge).ciclo()

        corpo = sge.leituras[0][1]
        self.assertIsNone(corpo["gabarito"])
        self.assertIn("o cargo da capa não está no arquivo", corpo["avisoGabarito"])

    def test_sge_que_recusa_o_gabarito_recebe_a_prova_sem_ele_e_com_o_motivo(self):
        self.escrever_prova(questoes=3)
        self.escrever_gabarito()
        sge = SgeFalso([pendente()], dados_de_leitura(), [gab(3), atrib(range(1, 4))])
        sge.erro_na_primeira_leitura = ErroSge(422, "GABARITO_NAO_CASA", "o gabarito traz 3 respostas e a prova 4 questões")

        self.worker(sge).ciclo()

        self.assertEqual(2, len(sge.tentativas_de_leitura))
        corpo = sge.leituras[0][1]
        self.assertIsNone(corpo["gabarito"])
        self.assertIn("GABARITO_NAO_CASA", corpo["avisoGabarito"])
        self.assertEqual([], sge.falhas, "gabarito ruim não derruba a prova")

    def test_gabarito_em_imagem_vira_aviso(self):
        self.escrever_prova(questoes=3)
        doc = fitz.open()
        pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 50, 50), False)
        pix.clear_with(200)
        doc.new_page().insert_image(fitz.Rect(0, 0, 200, 200), stream=pix.tobytes("png"))
        doc.save(str(self.entrada() / "gabarito.pdf"))
        sge = SgeFalso([pendente()], dados_de_leitura(gabarito="gabarito.pdf"), [atrib(range(1, 4))])

        self.worker(sge).ciclo()

        self.assertIn("imagem", sge.leituras[0][1]["avisoGabarito"])

    def test_d75_ia_indisponivel_para_o_ciclo_sem_gravar_nem_falhar(self):
        self.escrever_prova(questoes=3)
        self.escrever_gabarito()
        sge = SgeFalso([pendente(1), pendente(2)], dados_de_leitura(), [ErroSge(503, "IA_PAUSADA", "limite da janela de uso")])

        feitas = self.worker(sge).ciclo()

        self.assertEqual(0, feitas)
        self.assertEqual([], sge.leituras)
        self.assertEqual([], sge.falhas, "a assinatura parou: esperar, não falhar")
        self.assertEqual(1, len(sge.pedidos_ia), "o ciclo parou na primeira prova, sem insistir")

    def test_pdf_corrompido_vira_falha_da_etapa_com_o_motivo(self):
        (self.entrada() / "prova.pdf").write_bytes(b"isto nao e um pdf")
        sge = SgeFalso([pendente()], dados_de_leitura(gabarito=None))

        self.worker(sge).ciclo()

        self.assertEqual(1, len(sge.falhas))
        prova_id, etapa, erro = sge.falhas[0]
        self.assertEqual((1, "LENDO"), (prova_id, etapa))
        self.assertIn("não pôde ser aberto", erro)

    def test_prova_de_imagem_sem_ocr_vira_falha_falando_em_ocr(self):
        doc = fitz.open()
        pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 50, 50), False)
        pix.clear_with(200)
        doc.new_page().insert_image(fitz.Rect(0, 0, 400, 600), stream=pix.tobytes("png"))
        doc.save(str(self.entrada() / "prova.pdf"))
        sge = SgeFalso([pendente()], dados_de_leitura(gabarito=None))

        self.worker(sge).ciclo()

        self.assertIn("OCR", sge.falhas[0][2])

    def test_texto_sem_nenhuma_questao_vira_falha(self):
        c = canvas.Canvas(str(self.entrada() / "prova.pdf"))
        for i in range(5):
            c.drawString(60, 780 - i * 14, "Texto corrido de um documento qualquer que não é uma prova de concurso.")
        c.showPage()
        c.save()
        sge = SgeFalso([pendente()], dados_de_leitura(gabarito=None))

        self.worker(sge).ciclo()

        self.assertIn("separar as questões", sge.falhas[0][2])

    def test_erro_inesperado_numa_prova_vira_falha_e_nao_trava_as_outras(self):
        self.escrever_prova(2, questoes=3)
        sge = SgeFalso([pendente(1), pendente(2)], dados_de_leitura(2, gabarito=None), [atrib(range(1, 4))])
        sge.erro_em_dados[1] = RuntimeError("bug qualquer")

        feitas = self.worker(sge).ciclo()

        self.assertEqual(1, feitas)
        self.assertEqual(1, len(sge.falhas))
        self.assertIn("Erro inesperado", sge.falhas[0][2])
        self.assertEqual(2, sge.leituras[0][0], "a prova seguinte foi lida normalmente")

    def test_sge_fora_do_ar_sobe_para_quem_chama_esperar(self):
        sge = SgeFalso(ErroSge(None, "SEM_CONEXAO", "recusou a conexão"))

        with self.assertRaises(ErroSge):
            self.worker(sge).ciclo()


@unittest.skipUnless(shutil.which("tesseract"), "precisa do Tesseract (roda dentro da imagem do worker, ou onde ele estiver instalado)")
class OcrDeVerdadeTest(Base):
    """Uma prova SÓ de imagem, com o Tesseract de verdade: PDF -> OCR -> segmentador -> worker."""

    def escrever_prova_em_imagem(self, questoes=3):
        origem = fitz.open()
        pagina = origem.new_page(width=595, height=842)
        y = 60
        for n in range(1, questoes + 1):
            pagina.insert_text((50, y), f"{n}. Enunciado sobre {tema(n)} para a leitura por imagem.", fontsize=13)
            y += 24
            for letra in "ABCDE":
                pagina.insert_text((50, y), f"({letra}) alternativa {letra.lower()} sobre {tema(n + 2)}.", fontsize=13)
                y += 22
            y += 14
        png = pagina.get_pixmap(dpi=200).tobytes("png")
        alvo = fitz.open()
        alvo.new_page(width=595, height=842).insert_image(fitz.Rect(0, 0, 595, 842), stream=png)
        alvo.save(str(self.entrada() / "prova.pdf"))

    def test_prova_de_imagem_lida_por_ocr_de_verdade(self):
        self.escrever_prova_em_imagem(questoes=3)
        sge = SgeFalso([pendente()], dados_de_leitura(gabarito=None), [atrib(range(1, 4))])

        pw.WorkerProvas(sge, self.provas, self.material, pw.prova_pdf.Tesseract()).ciclo()

        self.assertEqual([], sge.falhas)
        corpo = sge.leituras[0][1]
        self.assertEqual("MULTIPLA_ESCOLHA", corpo["formato"])
        self.assertEqual(3, len(corpo["questoes"]))
        for q in corpo["questoes"]:
            self.assertEqual(5, len(q["alternativas"]), q)
            self.assertTrue(q["lidaPorOcr"], "a marca de OCR chega ao SGE (D-85)")
            self.assertEqual(1, q["paginaOrigem"], "a imagem da página fica para o usuário conferir")
            self.assertIsNone(q["motivoNaoAvaliavel"], q)
        self.assertIn("Enunciado sobre", corpo["questoes"][0]["enunciado"])
        self.assertTrue((self.provas / "paginas" / "1" / "01.png").is_file())


class SoOGabaritoTest(Base):
    def test_prova_ja_lida_que_esperava_o_gabarito_le_so_o_gabarito_com_a_capa_guardada(self):
        self.escrever_gabarito()
        capa = self.provas / "paginas" / "1"
        capa.mkdir(parents=True)
        (capa / "capa.txt").write_text("ANALISTA DE SISTEMAS\nPROVA TIPO 1", encoding="utf-8")
        sge = SgeFalso([pendente()], dados_de_leitura(ja_lida=True, numeros=range(1, 7)), [gab(6)])

        self.worker(sge).ciclo()

        self.assertEqual([], sge.leituras, "as questões já estão no SGE: não se relê a prova")
        prova_id, corpo = sge.gabaritos[0]
        self.assertEqual(6, len(corpo["gabarito"]["respostas"]))
        self.assertIsNone(corpo["avisoGabarito"])
        self.assertIn("ANALISTA DE SISTEMAS", sge.pedidos_ia[0], "a IA recebe a capa que a leitura guardou")

    def test_gabarito_que_nao_serve_de_novo_devolve_o_aviso_e_nada_de_gabarito(self):
        self.escrever_gabarito()
        sge = SgeFalso([pendente()], dados_de_leitura(ja_lida=True, numeros=range(1, 7)),
                       [{"encontrado": False, "motivo": "o tipo 4 não está no arquivo"}])

        self.worker(sge).ciclo()

        _, corpo = sge.gabaritos[0]
        self.assertIsNone(corpo["gabarito"])
        self.assertIn("tipo 4", corpo["avisoGabarito"])

    def test_total_diferente_do_das_questoes_ja_no_sge_e_aviso(self):
        self.escrever_gabarito()
        sge = SgeFalso([pendente()], dados_de_leitura(ja_lida=True, numeros=range(1, 7)), [gab(9)])

        self.worker(sge).ciclo()

        _, corpo = sge.gabaritos[0]
        self.assertIsNone(corpo["gabarito"])
        self.assertIn("9 respostas e a prova tem 6", corpo["avisoGabarito"])

    def test_sem_arquivo_de_gabarito_diz_que_nao_foi_enviado(self):
        sge = SgeFalso([pendente()], dados_de_leitura(gabarito=None, ja_lida=True, numeros=range(1, 4)))

        self.worker(sge).ciclo()

        self.assertIn("Nenhum gabarito", sge.gabaritos[0][1]["avisoGabarito"])


class JulgarTest(Base):
    def setUp(self):
        super().setUp()
        (self.material / "blocos" / "redes").mkdir(parents=True)
        c = canvas.Canvas(str(self.material / "blocos/redes/segmento-01.pdf"))
        for texto in ("Camada de transporte: o TCP oferece entrega confiavel.", "Camada de aplicacao: HTTP e DNS.",
                      "Seguranca: firewalls e criptografia simetrica."):
            c.drawString(60, 780, texto)
            c.showPage()
        c.save()

    def questao(self, n, segmentos=True):
        assunto = {"id": 7, "chaveExterna": "a-redes", "nome": "Redes", "disciplina": "TI",
                   "segmentos": [{"id": 12, "arquivo": "/material/blocos/redes/segmento-01.pdf", "ordem": 1}] if segmentos else []}
        return {"id": 100 + n, "numero": n, "enunciado": "Qual protocolo de transporte oferece entrega confiavel?", "textoBase": None,
                "alternativas": [{"letra": "A", "texto": "TCP"}, {"letra": "B", "texto": "ARP"}], "respostaGabarito": "A", "assunto": assunto}

    def julgamento(self, n, segmentos=True):
        return {"id": 1, "formato": "MULTIPLA_ESCOLHA", "questoes": [self.questao(i, segmentos) for i in range(1, n + 1)]}

    RESPONDIVEL = {"veredito": "RESPONDIVEL", "pagina": "S12-p1", "falta": None}

    def test_vereditos_entregues_em_lotes_de_cinco(self):
        sge = SgeFalso([pendente(status="JULGANDO")], julgamento=self.julgamento(7), respostas_ia=[self.RESPONDIVEL] * 7)

        self.worker(sge).ciclo()

        self.assertEqual([5, 2], [len(corpo["itens"]) for _, corpo in sge.vereditos])
        item = sge.vereditos[0][1]["itens"][0]
        self.assertEqual({"numero": 1, "veredito": "RESPONDIVEL", "segmentoId": 12, "paginaSegmento": 1, "falta": None}, item)

    def test_o_ciclo_respeita_o_orcamento_e_o_resto_fica_para_o_proximo(self):
        sge = SgeFalso([pendente(status="JULGANDO")], julgamento=self.julgamento(7), respostas_ia=[self.RESPONDIVEL] * 3)

        self.worker(sge, julgadas_por_ciclo=3).ciclo()

        self.assertEqual(3, sum(len(corpo["itens"]) for _, corpo in sge.vereditos))
        self.assertEqual(3, len(sge.pedidos_ia), "só as três do orçamento gastaram IA")

    def test_d75_ia_indisponivel_no_meio_entrega_o_que_ja_foi_julgado_e_nao_falha(self):
        sge = SgeFalso([pendente(status="JULGANDO")], julgamento=self.julgamento(4),
                       respostas_ia=[self.RESPONDIVEL, self.RESPONDIVEL, ErroSge(503, "IA_PAUSADA", "limite")])

        self.worker(sge).ciclo()

        self.assertEqual([2], [len(corpo["itens"]) for _, corpo in sge.vereditos], "as duas julgadas não se perdem")
        self.assertEqual([], sge.falhas)

    def test_assunto_sem_segmentos_e_nao_respondivel_sem_gastar_ia(self):
        sge = SgeFalso([pendente(status="JULGANDO")], julgamento=self.julgamento(2, segmentos=False))

        self.worker(sge).ciclo()

        itens = sge.vereditos[0][1]["itens"]
        self.assertEqual(["NAO_RESPONDIVEL"] * 2, [i["veredito"] for i in itens])
        self.assertEqual([], sge.pedidos_ia)

    def test_d75_resposta_ilegivel_pula_a_questao_e_so_na_terceira_volta_desiste_com_o_motivo(self):
        sge = SgeFalso([pendente(status="JULGANDO")], julgamento=self.julgamento(1), respostas_ia=["lixo", "lixo"] * 3)
        worker = self.worker(sge)

        worker.ciclo()
        worker.ciclo()
        self.assertEqual([], sge.vereditos, "duas voltas: a resposta ilegível da IA não é veredito")

        worker.ciclo()
        item = sge.vereditos[0][1]["itens"][0]
        self.assertEqual("NAO_RESPONDIVEL", item["veredito"])
        self.assertIn("Não foi possível julgar", item["falta"])

    def test_o_indice_de_paginas_nao_e_refeito_a_cada_questao(self):
        sge = SgeFalso([pendente(status="JULGANDO")], julgamento=self.julgamento(3), respostas_ia=[self.RESPONDIVEL] * 3)
        worker = self.worker(sge)

        worker.ciclo()

        self.assertEqual(1, len(worker.julgador._por_assunto))


if __name__ == "__main__":
    unittest.main()
