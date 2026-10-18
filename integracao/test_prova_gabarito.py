#!/usr/bin/env python3
"""
Testes de integracao/prova_gabarito.py: ler o gabarito e validar o que a IA devolve.

Rodar (da raiz do repositório):
    python -m unittest discover -s integracao -p "test_*.py"

IA falsa, com respostas roteirizadas. Contra os gabaritos de verdade (FGV, IDECAN, FCC), só a
ESCOLHA DA PÁGINA é conferida (é determinística); a leitura de cada layout pela IA de verdade é
o ensaio do item 24.8 do SGE.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prova_gabarito as pg  # noqa: E402
import prova_pdf as pp  # noqa: E402
import prova_questoes as pq  # noqa: E402
from ia_comum import IaIndisponivel  # noqa: E402
from sge_api import ErroSge  # noqa: E402


class SgeFalso:
    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.pedidos = []

    def completar(self, sistema, usuario):
        self.pedidos.append(usuario)
        resposta = self.respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta if isinstance(resposta, str) else json.dumps(resposta)


def resposta(n=5, **extra):
    base = {"encontrado": True, "situacao": "PRELIMINAR", "recorte": "Cargo X - Tipo 1",
            "respostas": [{"numero": i, "resposta": "ABCDE"[(i - 1) % 5]} for i in range(1, n + 1)]}
    base.update(extra)
    return base


def pagina(cargo, tipo, tamanho=1500):
    return f"CONCURSO PÚBLICO\n{cargo} PROVA TIPO {tipo}\n" + "1 2 3 4 5 B A C D E " * (tamanho // 20)


CAPA_DESENV = "CONCURSO PÚBLICO\nANALISTA DE TECNOLOGIA DA INFORMAÇÃO\nDESENVOLVIMENTO DE SOFTWARE\nPROVA OBJETIVA - TIPO 1"


class EscolherPaginasTest(unittest.TestCase):
    def test_gabarito_curto_vai_inteiro(self):
        paginas = ["página um do gabarito", "página dois"]

        self.assertEqual([(1, "página um do gabarito"), (2, "página dois")], pg.escolher_paginas(paginas, CAPA_DESENV))

    def test_gabarito_comprido_escolhe_a_pagina_do_cargo_e_do_tipo_certos(self):
        paginas = [pagina("ANALISTA DE PROCESSAMENTO", 1),
                   pagina("ANALISTA DE TECNOLOGIA DA INFORMAÇÃO - ADMINISTRAÇÃO E GOVERNANÇA", 1),
                   pagina("ANALISTA DE TECNOLOGIA DA INFORMAÇÃO - DESENVOLVIMENTO DE SOFTWARE", 1),
                   pagina("ANALISTA DE TECNOLOGIA DA INFORMAÇÃO - DESENVOLVIMENTO DE SOFTWARE", 3),
                   pagina("ANALISTA DE TECNOLOGIA DA INFORMAÇÃO - SEGURANÇA CIBERNÉTICA", 1)] * 4

        escolhidas = pg.escolher_paginas(paginas, CAPA_DESENV, limite=2000)

        numeros = [i for i, _ in escolhidas]
        self.assertLessEqual(len(numeros), pg.MAX_PAGINAS_ESCOLHIDAS)
        for i, texto in escolhidas:
            self.assertIn("DESENVOLVIMENTO DE SOFTWARE", texto)
            self.assertIn("TIPO 1", texto, "o tipo 3 tem o mesmo cargo e respostas diferentes: não pode ser escolhido")

    def test_o_tipo_decide_entre_duas_paginas_do_mesmo_cargo(self):
        paginas = [pagina("ANALISTA DE SISTEMAS", 1), pagina("ANALISTA DE SISTEMAS", 3)]
        capa_tipo_3 = "ANALISTA DE SISTEMAS\nPROVA TIPO 3"

        escolhidas = pg.escolher_paginas(paginas, capa_tipo_3, limite=100)

        self.assertEqual([2], [i for i, _ in escolhidas])

    def test_nenhuma_pagina_lembrando_a_capa_recusa_com_o_motivo(self):
        paginas = [pagina("ENFERMEIRO", 1), pagina("MÉDICO VETERINÁRIO", 1)]

        with self.assertRaises(pg.GabaritoNaoEncontrado) as e:
            pg.escolher_paginas(paginas, CAPA_DESENV, limite=100)
        self.assertIn("nenhuma página", str(e.exception))

    def test_tipo_com_zeros_da_fcc_casa_com_o_tipo_simples(self):
        paginas = [pagina("ANALISTA JUDICIÁRIO INFRAESTRUTURA DE TI", 1), pagina("ANALISTA JUDICIÁRIO INFRAESTRUTURA DE TI", 4)]

        escolhidas = pg.escolher_paginas(paginas, "ANALISTA JUDICIÁRIO INFRAESTRUTURA DE TI\nCaderno de Prova 'E05', Tipo 004", limite=100)

        self.assertEqual([2], [i for i, _ in escolhidas])


class InterpretarTest(unittest.TestCase):
    def test_resposta_valida_vira_o_formato_do_sge(self):
        g = pg.interpretar(resposta(5), "MULTIPLA_ESCOLHA", total_esperado=5)

        self.assertEqual("PRELIMINAR", g["situacao"])
        self.assertEqual("Cargo X - Tipo 1", g["recorte"])
        self.assertEqual([{"numero": 1, "resposta": "A", "anulada": False}], g["respostas"][:1])
        self.assertEqual(5, len(g["respostas"]))

    def test_anulada_por_flag_asterisco_ou_x_perde_a_letra(self):
        dados = resposta(4)
        dados["respostas"][0] = {"numero": 1, "resposta": None, "anulada": True}
        dados["respostas"][1] = {"numero": 2, "resposta": "*"}
        dados["respostas"][2] = {"numero": 3, "resposta": "x"}

        g = pg.interpretar(dados, "MULTIPLA_ESCOLHA")

        self.assertEqual([True, True, True, False], [r["anulada"] for r in g["respostas"]])
        self.assertEqual([None, None, None, "D"], [r["resposta"] for r in g["respostas"]])

    def test_certo_errado_so_aceita_C_e_E(self):
        dados = {"encontrado": True, "respostas": [{"numero": 1, "resposta": "C"}, {"numero": 2, "resposta": "E"}]}

        self.assertEqual(["C", "E"], [r["resposta"] for r in pg.interpretar(dados, "CERTO_ERRADO")["respostas"]])
        dados["respostas"][1]["resposta"] = "B"
        with self.assertRaises(ValueError) as e:
            pg.interpretar(dados, "CERTO_ERRADO")
        self.assertIn("questão 2", str(e.exception))

    def test_letra_fora_de_A_a_E_recusa(self):
        dados = resposta(3)
        dados["respostas"][1]["resposta"] = "F"

        with self.assertRaises(ValueError):
            pg.interpretar(dados, "MULTIPLA_ESCOLHA")

    def test_numeracao_com_buraco_ou_repetida_recusa(self):
        buraco = resposta(4)
        del buraco["respostas"][1]
        repetida = resposta(3)
        repetida["respostas"].append({"numero": 2, "resposta": "A"})

        with self.assertRaises(ValueError) as e1:
            pg.interpretar(buraco, "MULTIPLA_ESCOLHA")
        self.assertIn("contígua", str(e1.exception))
        with self.assertRaises(ValueError) as e2:
            pg.interpretar(repetida, "MULTIPLA_ESCOLHA")
        self.assertIn("duas vezes", str(e2.exception))

    def test_d82_total_diferente_do_da_prova_recusa_dizendo_os_dois_numeros(self):
        with self.assertRaises(ValueError) as e:
            pg.interpretar(resposta(59), "MULTIPLA_ESCOLHA", total_esperado=60)

        self.assertIn("59", str(e.exception))
        self.assertIn("60", str(e.exception))

    def test_cargo_nao_encontrado_nao_e_erro_de_formato(self):
        with self.assertRaises(pg.GabaritoNaoEncontrado) as e:
            pg.interpretar({"encontrado": False, "motivo": "o tipo 4 não está no arquivo"}, "MULTIPLA_ESCOLHA")

        self.assertIn("tipo 4", str(e.exception))

    def test_situacao_definitivo_e_o_padrao_preliminar(self):
        self.assertEqual("DEFINITIVO", pg.interpretar(resposta(2, situacao="definitivo"), "MULTIPLA_ESCOLHA")["situacao"])
        self.assertEqual("PRELIMINAR", pg.interpretar(resposta(2, situacao="algo estranho"), "MULTIPLA_ESCOLHA")["situacao"])
        dados = resposta(2)
        del dados["situacao"]
        self.assertEqual("PRELIMINAR", pg.interpretar(dados, "MULTIPLA_ESCOLHA")["situacao"], "na dúvida, provisório (D-84)")

    def test_resposta_que_nao_e_json_de_objeto_recusa(self):
        with self.assertRaises(ValueError):
            pg.interpretar(["A", "B"], "MULTIPLA_ESCOLHA")


class LerGabaritoTest(unittest.TestCase):
    def test_leitura_boa_devolve_o_gabarito_sem_aviso(self):
        sge = SgeFalso([resposta(5)])

        gabarito, aviso = pg.ler_gabarito(sge, ["1 A 2 B 3 C 4 D 5 E"], CAPA_DESENV, "MULTIPLA_ESCOLHA", total_esperado=5)

        self.assertIsNone(aviso)
        self.assertEqual(5, len(gabarito["respostas"]))
        self.assertIn("DESENVOLVIMENTO DE SOFTWARE", sge.pedidos[0], "a IA recebe a capa para casar o cargo")
        self.assertIn("1 A 2 B", sge.pedidos[0])

    def test_resposta_recusada_uma_vez_tenta_de_novo_dizendo_o_erro(self):
        sge = SgeFalso([resposta(4), resposta(5)])

        gabarito, aviso = pg.ler_gabarito(sge, ["gabarito"], CAPA_DESENV, "MULTIPLA_ESCOLHA", total_esperado=5)

        self.assertIsNone(aviso)
        self.assertEqual(2, len(sge.pedidos))
        self.assertIn("4 respostas", sge.pedidos[1], "a segunda tentativa leva o motivo da recusa")

    def test_recusada_duas_vezes_vira_aviso_com_o_motivo_e_sem_gabarito(self):
        sge = SgeFalso([resposta(4), resposta(4)])

        gabarito, aviso = pg.ler_gabarito(sge, ["gabarito"], CAPA_DESENV, "MULTIPLA_ESCOLHA", total_esperado=5)

        self.assertIsNone(gabarito)
        self.assertIn("4 respostas e a prova tem 5", aviso, "o usuário vê o motivo, nunca um silêncio")

    def test_cargo_nao_achado_pela_ia_vira_aviso_sem_gastar_outra_chamada(self):
        sge = SgeFalso([{"encontrado": False, "motivo": "o cargo da capa não está no arquivo"}])

        gabarito, aviso = pg.ler_gabarito(sge, ["gabarito de outro cargo"], CAPA_DESENV, "MULTIPLA_ESCOLHA")

        self.assertIsNone(gabarito)
        self.assertIn("cargo da capa", aviso)
        self.assertEqual(1, len(sge.pedidos), "'não achei' não melhora tentando de novo")

    def test_nenhuma_pagina_parecida_vira_aviso_sem_chamar_a_ia(self):
        sge = SgeFalso([])
        paginas = [pagina("ENFERMEIRO", 1, 30000), pagina("MÉDICO", 1, 30000)]

        gabarito, aviso = pg.ler_gabarito(sge, paginas, CAPA_DESENV, "MULTIPLA_ESCOLHA")

        self.assertIsNone(gabarito)
        self.assertIn("nenhuma página", aviso)
        self.assertEqual([], sge.pedidos)

    def test_ia_indisponivel_sobe_e_nao_vira_aviso(self):
        sge = SgeFalso([ErroSge(503, "IA_PAUSADA", "limite da janela de uso")])

        with self.assertRaises(IaIndisponivel):
            pg.ler_gabarito(sge, ["gabarito"], CAPA_DESENV, "MULTIPLA_ESCOLHA")

    def test_resposta_da_ia_com_texto_em_volta_do_json_serve(self):
        sge = SgeFalso(["Aqui está:\n```json\n" + json.dumps(resposta(3)) + "\n```\nPronto."])

        gabarito, aviso = pg.ler_gabarito(sge, ["g"], CAPA_DESENV, "MULTIPLA_ESCOLHA", total_esperado=3)

        self.assertIsNone(aviso)
        self.assertEqual(3, len(gabarito["respostas"]))


@unittest.skipUnless(os.environ.get("PROVAS_AMOSTRA_DIR"), "defina PROVAS_AMOSTRA_DIR para rodar contra as provas reais")
class AmostraRealTest(unittest.TestCase):
    """Os gabaritos de verdade: a página escolhida tem de ser a do cargo e do tipo da prova."""

    class SemOcr:
        def disponivel(self):
            return False

    def pasta(self):
        return Path(os.environ["PROVAS_AMOSTRA_DIR"])

    def capa(self, prova):
        with tempfile.TemporaryDirectory() as tmp:
            return pq.segmentar(pp.ler_prova(self.pasta() / prova, tmp, self.SemOcr()).linhas).capa

    def test_dataprev_escolhe_desenvolvimento_de_software_tipo_1(self):
        capa = self.capa("fgv-2026-dataprev-analista-de-tecnologia-da-informacao-desenvolvimento-de-software-prova.pdf")
        paginas = pp.texto_do_arquivo(self.pasta() / "fgv-2026-dataprev-analista-de-tecnologia-da-informacao-desenvolvimento-de-software-gabarito.pdf")

        escolhidas = pg.escolher_paginas(paginas, capa)

        self.assertEqual([13], [i for i, _ in escolhidas], "página 13 = Desenvolvimento de Software, Tipo 1 (a 14 é o Tipo 3)")

    def test_mpes_escolhe_analista_de_sistemas_tipo_1(self):
        capa = self.capa("fgv-2026-mpe-es-agente-especializado-analista-de-sistemas-prova.pdf")
        paginas = pp.texto_do_arquivo(self.pasta() / "fgv-2026-mpe-es-agente-especializado-analista-de-sistemas-gabarito.pdf")

        escolhidas = pg.escolher_paginas(paginas, capa)

        self.assertEqual([6], [i for i, _ in escolhidas], "página 6 = Agente Especializado – Analista de Sistemas, Tipo 1, Manhã")

    def test_gabaritos_curtos_da_idecan_e_da_fcc_vao_inteiros(self):
        for nome in ("idecan-2023-sefaz-rr-tecnico-em-infraestrutura-de-tecnologia-da-informacao-gabarito.pdf",
                     "fcc-2026-tj-ce-analista-judiciario-area-tecnico-administrativa-especialidade-infraestrutura-de-tecnologia-da-informacao-gabarito.pdf"):
            paginas = pp.texto_do_arquivo(self.pasta() / nome)

            escolhidas = pg.escolher_paginas(paginas, "qualquer capa")

            self.assertEqual(len(paginas), len(escolhidas), nome)


if __name__ == "__main__":
    unittest.main()
