#!/usr/bin/env python3
"""
Testes de integracao/prova_julgamento.py: o material sustenta a alternativa do gabarito?

Rodar (da raiz do repositório):
    python -m unittest discover -s integracao -p "test_*.py"

PDFs de segmento sintéticos (reportlab) numa pasta temporária e IA falsa com respostas roteirizadas.
O julgamento de verdade, com a IA de verdade, é o ensaio do item 24.8 do SGE.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prova_julgamento as pj  # noqa: E402
from ia_comum import IaIndisponivel  # noqa: E402
from sge_api import ErroSge  # noqa: E402


class SgeFalso:
    def __init__(self, respostas=()):
        self.respostas = list(respostas)
        self.pedidos = []

    def completar(self, sistema, usuario):
        self.pedidos.append(usuario)
        resposta = self.respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta if isinstance(resposta, str) else json.dumps(resposta)


def pdf(caminho, paginas):
    c = canvas.Canvas(str(caminho))
    for texto in paginas:
        y = 780
        for linha in texto.split("\n"):
            c.drawString(60, y, linha)
            y -= 16
        c.showPage()
    c.save()


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.material = Path(self._tmp.name)
        (self.material / "blocos" / "redes").mkdir(parents=True)
        pdf(self.material / "blocos/redes/segmento-01.pdf", [
            "Introdução às redes de computadores\nUma rede interliga dispositivos para trocar dados.",
            "Camada de transporte\nO protocolo TCP oferece entrega confiável e orientada a conexão.\nO UDP não garante entrega.",
            "Camada de aplicação\nHTTP e DNS operam na camada de aplicação.",
        ])
        pdf(self.material / "blocos/redes/segmento-02.pdf", [
            "Segurança em redes\nFirewalls filtram o tráfego entre redes.",
            "Criptografia\nA criptografia simétrica usa a mesma chave para cifrar e decifrar.",
        ])

    def tearDown(self):
        self._tmp.cleanup()

    def assunto(self, segmentos=True):
        return {"id": 7, "chaveExterna": "a-redes", "nome": "Redes de computadores", "disciplina": "Conhecimentos Específicos",
                "segmentos": [{"id": 12, "arquivo": "/material/blocos/redes/segmento-01.pdf", "ordem": 1, "paginaInicial": 1, "paginaFinal": 3},
                              {"id": 13, "arquivo": "/material/blocos/redes/segmento-02.pdf", "ordem": 2, "paginaInicial": 4, "paginaFinal": 5}]
                if segmentos else []}

    def questao(self, numero=1, enunciado="Qual protocolo da camada de transporte oferece entrega confiável?",
                resposta="A", assunto=None):
        return {"id": 100 + numero, "numero": numero, "enunciado": enunciado, "textoBase": None,
                "alternativas": [{"letra": "A", "texto": "TCP"}, {"letra": "B", "texto": "ARP"}, {"letra": "C", "texto": "DNS"},
                                 {"letra": "D", "texto": "HTTP"}, {"letra": "E", "texto": "ICMP"}],
                "respostaGabarito": resposta, "assunto": assunto or self.assunto()}

    def julgador(self, respostas=()):
        sge = SgeFalso(respostas)
        return pj.Julgador(sge, self.material), sge


class PaginasTest(Base):
    def test_busca_acha_a_pagina_pelo_conteudo_e_diz_o_segmento_e_a_pagina_dentro_dele(self):
        paginas = pj.PaginasDoAssunto(self.assunto()["segmentos"], self.material)

        achadas = paginas.buscar(["protocolo", "transporte", "confiavel"], k=3)

        self.assertEqual(5, paginas.total)
        self.assertEqual((12, 2), achadas[0][:2], "a página 2 do segmento 12 é a da camada de transporte")

    def test_acento_nao_atrapalha_a_busca(self):
        paginas = pj.PaginasDoAssunto(self.assunto()["segmentos"], self.material)

        self.assertEqual((12, 2), paginas.buscar(["confiavel"])[0][:2], "'confiável' no PDF, 'confiavel' na busca")
        self.assertEqual((12, 1), paginas.buscar(["introducao"])[0][:2])

    def test_pdf_ausente_nao_derruba_os_outros_segmentos(self):
        segmentos = self.assunto()["segmentos"] + [{"id": 99, "arquivo": "/material/blocos/redes/nao-existe.pdf"}]

        paginas = pj.PaginasDoAssunto(segmentos, self.material)

        self.assertEqual(5, paginas.total)
        self.assertEqual(1, len(paginas.ilegiveis))

    def test_sem_termos_nao_ha_o_que_buscar(self):
        self.assertEqual([], pj.PaginasDoAssunto(self.assunto()["segmentos"], self.material).buscar([]))


class InterpretarTest(unittest.TestCase):
    OFERECIDAS = {(12, 2), (13, 1)}

    def test_respondivel_com_pagina_oferecida_vale(self):
        self.assertEqual(("RESPONDIVEL", (12, 2), None),
                         pj.interpretar({"veredito": "RESPONDIVEL", "pagina": "S12-p2", "falta": None}, self.OFERECIDAS))

    def test_d68_respondivel_com_pagina_que_nao_foi_oferecida_rebaixa(self):
        veredito, citada, falta = pj.interpretar({"veredito": "RESPONDIVEL", "pagina": "S12-p9"}, self.OFERECIDAS)

        self.assertEqual("NAO_RESPONDIVEL", veredito)
        self.assertIsNone(citada)
        self.assertIn("não estava entre as oferecidas", falta)

    def test_d68_respondivel_sem_pagina_rebaixa(self):
        veredito, citada, _ = pj.interpretar({"veredito": "RESPONDIVEL", "pagina": None}, self.OFERECIDAS)

        self.assertEqual(("NAO_RESPONDIVEL", None), (veredito, citada))

    def test_parcial_guarda_a_pagina_e_o_que_falta(self):
        self.assertEqual(("PARCIAL", (13, 1), "falta a exceção do UDP"),
                         pj.interpretar({"veredito": "parcial", "pagina": "[S13-p1]", "falta": " falta a exceção do UDP "}, self.OFERECIDAS))

    def test_parcial_com_pagina_inventada_perde_so_a_pagina(self):
        self.assertEqual(("PARCIAL", None, "falta algo"),
                         pj.interpretar({"veredito": "PARCIAL", "pagina": "S1-p1", "falta": "falta algo"}, self.OFERECIDAS))

    def test_nao_respondivel_nao_tem_pagina(self):
        self.assertEqual(("NAO_RESPONDIVEL", None, "o material não traz isso"),
                         pj.interpretar({"veredito": "NAO_RESPONDIVEL", "pagina": "S12-p2", "falta": "o material não traz isso"}, self.OFERECIDAS))

    def test_veredito_invalido_ou_resposta_que_nao_e_objeto_lanca(self):
        with self.assertRaises(ValueError):
            pj.interpretar({"veredito": "TALVEZ"}, self.OFERECIDAS)
        with self.assertRaises(ValueError):
            pj.interpretar(["RESPONDIVEL"], self.OFERECIDAS)

    def test_pagina_mal_escrita_e_tratada_como_ausente(self):
        for ruim in ("p2", "S12", "S-p2", "SAB-pX", 12, None, ""):
            veredito, citada, _ = pj.interpretar({"veredito": "RESPONDIVEL", "pagina": ruim}, self.OFERECIDAS)
            self.assertEqual(("NAO_RESPONDIVEL", None), (veredito, citada), repr(ruim))


class JulgarTest(Base):
    def test_respondivel_com_a_pagina_certa(self):
        julgador, sge = self.julgador([{"veredito": "RESPONDIVEL", "pagina": "S12-p2", "falta": None}])

        item = julgador.julgar(self.questao(), "MULTIPLA_ESCOLHA")

        self.assertEqual({"numero": 1, "veredito": "RESPONDIVEL", "segmentoId": 12, "paginaSegmento": 2, "falta": None}, item)

    def test_o_pedido_traz_a_alternativa_do_gabarito_e_as_paginas_com_o_id_para_citar(self):
        julgador, sge = self.julgador([{"veredito": "PARCIAL", "pagina": "S12-p2", "falta": "x"}])

        julgador.julgar(self.questao(), "MULTIPLA_ESCOLHA")

        pedido = sge.pedidos[0]
        self.assertIn("ALTERNATIVA DO GABARITO: A — TCP", pedido)
        self.assertIn("[S12-p2]", pedido)
        self.assertIn("entrega confiável e orientada a conexão", pedido)
        self.assertIn("Redes de computadores (Conhecimentos Específicos)", pedido)

    def test_d68_ia_que_cita_pagina_fora_das_oferecidas_rebaixa(self):
        julgador, _ = self.julgador([{"veredito": "RESPONDIVEL", "pagina": "S13-p2"}])  # existe no PDF, mas não foi oferecida

        item = julgador.julgar(self.questao(enunciado="Qual protocolo da camada de transporte oferece entrega confiável?"), "MULTIPLA_ESCOLHA")

        self.assertEqual("NAO_RESPONDIVEL", item["veredito"])
        self.assertIsNone(item["segmentoId"])

    def test_assunto_sem_segmento_e_nao_respondivel_sem_gastar_ia(self):
        julgador, sge = self.julgador()

        item = julgador.julgar(self.questao(assunto=self.assunto(segmentos=False)), "MULTIPLA_ESCOLHA")

        self.assertEqual("NAO_RESPONDIVEL", item["veredito"])
        self.assertIn("sem segmentos", item["falta"])
        self.assertEqual([], sge.pedidos, "D-65: o assunto sem material não custa uma chamada")

    def test_nenhuma_pagina_cita_os_termos_e_nao_respondivel_sem_gastar_ia(self):
        julgador, sge = self.julgador()

        item = julgador.julgar(self.questao(enunciado="Como funciona a fotossíntese nas plantas?", resposta="B"), "MULTIPLA_ESCOLHA")

        self.assertEqual("NAO_RESPONDIVEL", item["veredito"])
        self.assertIn("Nenhuma página", item["falta"])
        self.assertEqual([], sge.pedidos)

    def test_pdf_do_segmento_ausente_e_nao_respondivel_com_o_motivo(self):
        assunto = self.assunto()
        assunto["segmentos"] = [{"id": 1, "arquivo": "/material/blocos/redes/nao-existe.pdf"}]
        julgador, sge = self.julgador()

        item = julgador.julgar(self.questao(assunto=assunto), "MULTIPLA_ESCOLHA")

        self.assertEqual("NAO_RESPONDIVEL", item["veredito"])
        self.assertIn("não pôde ser lido", item["falta"])
        self.assertEqual([], sge.pedidos)

    def test_resposta_ilegivel_tenta_de_novo_levando_o_erro(self):
        julgador, sge = self.julgador(["isto não é JSON", {"veredito": "PARCIAL", "pagina": "S12-p2", "falta": "falta o UDP"}])

        item = julgador.julgar(self.questao(), "MULTIPLA_ESCOLHA")

        self.assertEqual("PARCIAL", item["veredito"])
        self.assertEqual(2, len(sge.pedidos))
        self.assertIn("recusada", sge.pedidos[1])

    def test_d75_ilegivel_duas_vezes_nao_vira_veredito(self):
        julgador, _ = self.julgador(["lixo", "mais lixo"])

        with self.assertRaises(pj.JulgamentoFalhou) as e:
            julgador.julgar(self.questao(), "MULTIPLA_ESCOLHA")
        self.assertIn("questão 1", str(e.exception))

    def test_d75_ia_indisponivel_sobe_e_nao_vira_veredito(self):
        julgador, _ = self.julgador([ErroSge(503, "IA_PAUSADA", "limite da janela de uso")])

        with self.assertRaises(IaIndisponivel):
            julgador.julgar(self.questao(), "MULTIPLA_ESCOLHA")

    def test_certo_errado_leva_o_texto_base_e_certo_ou_errado_no_lugar_da_letra(self):
        julgador, sge = self.julgador([{"veredito": "RESPONDIVEL", "pagina": "S12-p2"}])
        q = self.questao(enunciado="O protocolo TCP oferece entrega confiável.", resposta="C")
        q["alternativas"] = []
        q["textoBase"] = "Julgue os itens a seguir, acerca de redes."

        julgador.julgar(q, "CERTO_ERRADO")

        pedido = sge.pedidos[0]
        self.assertIn("ALTERNATIVA DO GABARITO: C — Certo", pedido)
        self.assertIn("TEXTO-BASE DO ITEM:", pedido)
        self.assertIn("Julgue os itens a seguir", pedido)

    def test_o_indice_de_paginas_do_assunto_e_reaproveitado_entre_as_questoes(self):
        julgador, _ = self.julgador([{"veredito": "PARCIAL", "pagina": "S12-p2", "falta": "x"}] * 2)

        julgador.julgar(self.questao(1), "MULTIPLA_ESCOLHA")
        julgador.julgar(self.questao(2), "MULTIPLA_ESCOLHA")

        self.assertEqual(1, len(julgador._por_assunto), "os PDFs do assunto são abertos uma vez")

    def test_pagina_longa_e_cortada_para_nao_gastar_cota(self):
        pdf(self.material / "blocos/redes/segmento-01.pdf", ["protocolo transporte confiavel\n" + ("texto longo " * 400)])
        julgador, sge = self.julgador([{"veredito": "PARCIAL", "pagina": "S12-p1", "falta": "x"}])

        julgador.julgar(self.questao(), "MULTIPLA_ESCOLHA")

        self.assertLess(len(sge.pedidos[0]), pj.MAX_CARACTERES_PAGINA * pj.PAGINAS_POR_QUESTAO + 2000)


if __name__ == "__main__":
    unittest.main()
