#!/usr/bin/env python3
"""
Testes de integracao/prova_atribuicao.py: a que assunto do edital pertence cada questão.

Rodar (da raiz do repositório):
    python -m unittest discover -s integracao -p "test_*.py"
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prova_atribuicao as pa  # noqa: E402
import prova_questoes as pq  # noqa: E402
from ia_comum import IaIndisponivel  # noqa: E402
from sge_api import ErroSge  # noqa: E402

ASSUNTOS = [
    {"chaveExterna": "a-redes", "disciplina": "Conhecimentos Específicos", "nome": "Redes de computadores"},
    {"chaveExterna": "a-lgpd", "disciplina": "Direito", "nome": "LGPD"},
    {"chaveExterna": "a-logica", "disciplina": "Raciocínio Lógico", "nome": "Proposições"},
]


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


def questao(n, enunciado="Qual protocolo opera na camada de transporte?", cabecalho=None, alternativas=None, motivo=None):
    return pq.QuestaoBruta(n, enunciado, alternativas if alternativas is not None else [("A", "TCP"), ("B", "ARP")],
                           cabecalho=cabecalho, motivo=motivo)


def atribui(*itens):
    return {"atribuicoes": [{"numero": n, "assunto": a, "confianca": c} for n, a, c in itens]}


class AtribuirTest(unittest.TestCase):
    def test_a_ia_escolhe_o_assunto_e_a_confianca(self):
        sge = SgeFalso([atribui((1, "a-redes", "ALTA"), (2, "a-lgpd", "BAIXA"))])

        resultado = pa.atribuir(sge, [questao(1), questao(2, "O controlador responde pelo tratamento?")], ASSUNTOS)

        self.assertEqual({1: ("a-redes", False), 2: ("a-lgpd", True)}, resultado)

    def test_o_pedido_leva_os_assuntos_as_questoes_e_o_cabecalho_como_pista(self):
        sge = SgeFalso([atribui((1, "a-redes", "ALTA"))])

        pa.atribuir(sge, [questao(1, cabecalho="Conhecimentos Específicos")], ASSUNTOS)

        pedido = sge.pedidos[0]
        self.assertIn("a-redes | Conhecimentos Específicos | Redes de computadores", pedido)
        self.assertIn("a-lgpd | Direito | LGPD", pedido)
        self.assertIn("Q1 [cabeçalho da prova: Conhecimentos Específicos]", pedido)
        self.assertIn("(A) TCP", pedido)

    def test_d74_nenhum_e_chave_fora_da_cobertura_viram_fora_do_edital_sem_inventar_assunto(self):
        sge = SgeFalso([atribui((1, None, "ALTA"), (2, "a-inventado", "ALTA"), (3, "", "ALTA"))])

        resultado = pa.atribuir(sge, [questao(1), questao(2), questao(3)], ASSUNTOS)

        self.assertEqual({1: (None, False), 2: (None, False), 3: (None, False)}, resultado,
                         '"nenhum" é resposta válida, e uma chave que não é da cobertura nunca vira assunto')

    def test_questao_sem_texto_nao_e_atribuida(self):
        sge = SgeFalso([atribui((2, "a-redes", "ALTA"))])

        resultado = pa.atribuir(sge, [questao(1, enunciado=None, alternativas=[], motivo="SEM_TEXTO"), questao(2)], ASSUNTOS)

        self.assertEqual({2: ("a-redes", False)}, resultado)
        self.assertNotIn("Q1", sge.pedidos[0], "sem texto não há o que classificar")

    def test_questoes_em_lotes_de_dez(self):
        questoes = [questao(n) for n in range(1, 24)]
        sge = SgeFalso([atribui(*[(n, "a-redes", "ALTA") for n in range(1, 11)]),
                        atribui(*[(n, "a-lgpd", "ALTA") for n in range(11, 21)]),
                        atribui(*[(n, "a-logica", "ALTA") for n in range(21, 24)])])

        resultado = pa.atribuir(sge, questoes, ASSUNTOS)

        self.assertEqual(3, len(sge.pedidos), "23 questões, três chamadas")
        self.assertEqual(23, len(resultado))
        self.assertEqual("a-logica", resultado[23][0])

    def test_questao_esquecida_pela_ia_e_perguntada_de_novo(self):
        sge = SgeFalso([atribui((1, "a-redes", "ALTA")), atribui((2, "a-lgpd", "ALTA"))])

        resultado = pa.atribuir(sge, [questao(1), questao(2)], ASSUNTOS)

        self.assertEqual({1: ("a-redes", False), 2: ("a-lgpd", False)}, resultado)
        self.assertEqual(2, len(sge.pedidos))
        self.assertIn("faltou responder as questões 2", sge.pedidos[1])
        self.assertNotIn("Q1:", sge.pedidos[1], "a segunda chamada só leva o que faltou")

    def test_questao_que_a_ia_nunca_responde_vira_fora_do_edital_para_revisar_e_nao_um_chute(self):
        sge = SgeFalso([atribui((1, "a-redes", "ALTA")), atribui((1, "a-redes", "ALTA"))])

        resultado = pa.atribuir(sge, [questao(1), questao(2)], ASSUNTOS)

        self.assertEqual((None, True), resultado[2])

    def test_resposta_ilegivel_tenta_de_novo_e_depois_desiste_com_seguranca(self):
        sge = SgeFalso(["não sei responder isso", "continuo sem JSON"])

        resultado = pa.atribuir(sge, [questao(1)], ASSUNTOS)

        self.assertEqual({1: (None, True)}, resultado)
        self.assertEqual(2, len(sge.pedidos))

    def test_ia_indisponivel_sobe_e_nada_e_atribuido(self):
        sge = SgeFalso([ErroSge(503, "IA_PAUSADA", "limite da janela de uso")])

        with self.assertRaises(IaIndisponivel):
            pa.atribuir(sge, [questao(1)], ASSUNTOS)

    def test_enunciado_longo_e_cortado_para_nao_gastar_cota(self):
        sge = SgeFalso([atribui((1, "a-redes", "ALTA"))])

        pa.atribuir(sge, [questao(1, enunciado="palavra " * 500)], ASSUNTOS)

        self.assertLess(len(sge.pedidos[0]), 2500)


if __name__ == "__main__":
    unittest.main()
