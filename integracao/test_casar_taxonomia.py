#!/usr/bin/env python3
"""Testes de integracao/casar_taxonomia.py com uma árvore pequena no formato normalizado e uma IA falsa."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import casar_taxonomia as ct  # noqa: E402

ARVORE = [
    {"id": 1, "nome": "Português", "ordem": 1, "filhos": [
        {"id": 11, "nome": "Sintaxe", "ordem": 1, "filhos": [
            {"id": 111, "nome": "Vozes Verbais", "ordem": 1, "filhos": []}]},
        {"id": 12, "nome": "Pontuação", "ordem": 2, "filhos": []}]},
    {"id": 2, "nome": "Espanhol", "ordem": 2, "filhos": [{"id": 21, "nome": "Verbos", "ordem": 1, "filhos": []}]},
    {"id": 3, "nome": "Redes de Computadores", "ordem": 3, "filhos": [
        {"id": 31, "nome": "NAT (Network Address Translation)", "ordem": 1, "filhos": []},
        {"id": 32, "nome": "Protocolos de Roteamento", "ordem": 2, "filhos": [
            {"id": 321, "nome": "OSPF", "ordem": 1, "filhos": []}]}]}]


class IaFalsa:
    def __init__(self, respostas):
        self.respostas, self.pedidos = list(respostas), []

    def completar(self, sistema, usuario):
        self.pedidos.append(usuario)
        return json.dumps(self.respostas.pop(0))


class CasarTaxonomiaTest(unittest.TestCase):
    def setUp(self):
        self.arvore = ct.Arvore(ARVORE)

    def test_refino_troca_o_no_atual_por_candidato_melhor(self):
        itens = [{"nome": "OSPF", "disciplina": "Redes", "termos": [], "ia": [32], "natureza": "mais_amplo"},
                 {"nome": "NAT", "disciplina": "Redes", "termos": [], "ia": [31], "natureza": "exato"},
                 {"nome": "Roteamento", "disciplina": "Redes", "termos": [], "ia": [32], "natureza": "mais_amplo"}]
        ia = IaFalsa([{"ligacoes": [{"item": 1, "nos": [321, 999], "natureza": "exato"},
                                    {"item": 2, "nos": [32], "natureza": "exato"}]}])
        ct.refinar(ia, itens, self.arvore, log=lambda *_: None)
        self.assertEqual(([321], "exato", [32], True), (itens[0]["ia"], itens[0]["natureza"], itens[0]["ia_antes"],
                                                    itens[0]["refinado"]), "id fora da lista é descartado")
        self.assertEqual(([31], "exato"), (itens[1]["ia"], itens[1]["natureza"]), "item exato nem entra no refino")
        self.assertNotIn("refinado", itens[2], "a IA devolveu o atual: não muda")
        self.assertEqual(1, len(ia.pedidos))
        self.assertIn("ATUAL: 32:", ia.pedidos[0])

    def test_refino_marca_candidato_de_fora_das_disciplinas_e_pula_decisao(self):
        itens = [{"nome": "Verbos", "disciplina": "Redes", "termos": [], "ia": [32], "natureza": "mais_amplo", "raizes": [3]},
                 {"nome": "Verbos", "disciplina": "Redes", "termos": [], "ia": [], "natureza": None, "raizes": [3],
                  "decisao": "aprovada"}]
        ia = IaFalsa([{"ligacoes": [{"item": 1, "nos": [32], "natureza": "mais_amplo"}]}])
        ct.refinar(ia, itens, self.arvore, log=lambda *_: None)
        self.assertIn("21: Espanhol > Verbos [fora das disciplinas do edital]", ia.pedidos[0])
        self.assertIn("RAMO:", ia.pedidos[0])
        self.assertEqual([], itens[1]["ia"], "item com decisão aprovada não vai para o refino")

    def test_resposta_ilegivel_tenta_de_novo_e_depois_deixa_para_a_segunda_passada(self):
        class Ruim:
            def __init__(self, respostas):
                self.respostas, self.chamadas = list(respostas), 0

            def completar(self, sistema, usuario):
                self.chamadas += 1
                r = self.respostas.pop(0)
                return r if isinstance(r, str) else json.dumps(r)
        itens = [{"nome": "NAT", "disciplina": "Redes", "termos": [], "raizes": [3]}]
        ia = Ruim(["isto não é json", {"ligacoes": [{"item": 1, "nos": [31], "natureza": "exato"}]}])
        ct.ligar_com_ia(ia, itens, self.arvore, log=lambda *_: None)
        self.assertEqual(([31], 2), (itens[0]["ia"], ia.chamadas), "a segunda tentativa funcionou")
        itens = [{"nome": "NAT", "disciplina": "Redes", "termos": [], "raizes": [3]}]
        ia = Ruim(["lixo", "lixo", "lixo", "lixo", "lixo", "lixo"])
        ct.ligar_com_ia(ia, itens, self.arvore, log=lambda *_: None)
        self.assertEqual([], itens[0]["ia"], "falhou duas vezes: fica sem nó, sem derrubar a rodada")

    def test_sigla_colada_na_versao(self):
        # ALESC, 'Fundamentos ITILv4' ficou sem nó porque 'itilv4' não casava com o nó 'ITIL 4'
        self.assertEqual(["fundamento", "itil"], ct.palavras("Fundamentos ITILv4"))
        self.assertEqual(ct.palavras("ITIL 4"), ct.palavras("ITILv4"))
        self.assertEqual(["iso", "27001"], ct.palavras("ISO27001"))
        self.assertEqual(["ipv"], ct.palavras("IPv6"))
        self.assertEqual(["nbr", "27002", "2022"], ct.palavras("NBR 27002-2022"))

    def test_palavras_sem_acento_vazias_e_plural(self):
        self.assertEqual(["voze", "verbai"], ct.palavras("Vozes Verbais"))
        self.assertEqual(["protocolo", "roteamento"], ct.palavras("Noções de Protocolos de Roteamento"))

    def test_candidatos_restritos_a_disciplina(self):
        sem = [i for _, i in self.arvore.candidatos("Vozes do verbo")]
        com = [i for _, i in self.arvore.candidatos("Vozes do verbo", raizes={1})]
        self.assertIn(111, com)
        self.assertNotIn(21, com, "Espanhol fica de fora quando a disciplina é Português")
        self.assertTrue(set(sem) >= set(com))
        self.assertEqual(31, self.arvore.candidatos("NAT", ["Network Address Translation"], raizes={3})[0][1])
        self.assertEqual([], self.arvore.candidatos("de da do"))

    def test_casam_por_no_ou_dentro_dele_mas_nao_pela_disciplina(self):
        self.assertTrue(ct.casam(self.arvore, 32, 321))
        self.assertTrue(ct.casam(self.arvore, 321, 32))
        self.assertFalse(ct.casam(self.arvore, 31, 321), "irmãos na mesma disciplina não casam")
        self.assertFalse(ct.casam(self.arvore, 3, 31), "a disciplina inteira não conta")

    def test_regra_decide_so_com_candidato_forte_e_isolado(self):
        self.assertEqual(31, ct.regra_decide({"candidatos": [(0.9, 31), (0.5, 32)]}))
        self.assertIsNone(ct.regra_decide({"candidatos": [(0.9, 31), (0.85, 32)]}))
        self.assertIsNone(ct.regra_decide({"candidatos": [(0.6, 31)]}))

    def test_ia_escolhe_so_entre_os_candidatos(self):
        itens = [{"nome": "NAT e PAT", "disciplina": "Redes", "termos": [], "candidatos": [(0.9, 31), (0.4, 32)]},
                 {"nome": "Lei 6.745/1985", "disciplina": "Regionais", "termos": [], "candidatos": [(0.3, 12)]}]
        ia = IaFalsa([{"ligacoes": [{"item": 1, "nos": [31, 999], "confianca": "alta"}, {"item": 2, "nos": []}]}])
        ct.ligar_com_ia(ia, itens, self.arvore, log=lambda m: None)
        self.assertEqual(([31], "alta"), (itens[0]["ia"], itens[0]["confianca"]), "id fora dos candidatos é descartado")
        self.assertEqual([], itens[1]["ia"])
        self.assertIn("31: Redes de Computadores > NAT (Network Address Translation)", ia.pedidos[0])

    def test_ia_ve_a_arvore_inteira_da_disciplina_ligada(self):
        itens = [{"nome": "Coordenação e subordinação", "disciplina": "Língua Portuguesa", "termos": [], "raizes": [1],
                  "candidatos": []},
                 {"nome": "NAT", "disciplina": "?", "termos": [], "raizes": [], "candidatos": [(0.9, 31)]}]
        ia = IaFalsa([{"ligacoes": [{"item": "1", "nos": ["11", 31], "confianca": "media"}]},
                      {"ligacoes": [{"item": 1, "nos": [31]}]},
                      {"ligacoes": []}])
        ct.ligar_com_ia(ia, itens, self.arvore, log=lambda m: None)
        self.assertEqual([11], itens[0]["ia"], "nó de outra disciplina (31) é descartado")
        self.assertIn("111: Português > Sintaxe > Vozes Verbais", ia.pedidos[0])
        self.assertNotIn("Espanhol", ia.pedidos[0])
        self.assertEqual([31], itens[1]["ia"], "sem disciplina ligada, vai pelos candidatos")
        self.assertEqual([11, 111, 12], self.arvore.subarvore([1]))

    def test_segunda_passada_na_arvore_inteira_para_quem_ficou_sem_no(self):
        itens = [{"nome": "Vozes Verbais", "disciplina": "Redes", "termos": [], "raizes": [3], "candidatos": []}]
        ia = IaFalsa([{"ligacoes": [{"item": 1, "nos": []}]}, {"ligacoes": [{"item": 1, "nos": [111], "confianca": "alta"}]}])
        ct.ligar_com_ia(ia, itens, self.arvore, log=lambda m: None)
        self.assertEqual(([111], True), (itens[0]["ia"], itens[0]["segunda_passada"]))
        self.assertIn("111: Português > Sintaxe > Vozes Verbais", ia.pedidos[1])

    def test_disciplina_enorme_so_com_os_ramos_da_disciplina_do_item(self):
        estados = [{"id": 900 + k, "nome": f"Legislação do Estado de {uf}", "ordem": k, "filhos": [
            {"id": 9000 + k * 400 + j, "nome": f"Lei {j}", "ordem": j, "filhos": []} for j in range(200)]}
            for k, uf in enumerate(["Santa Catarina", "Paraná"], 1)]
        a = ct.Arvore([{"id": 9, "nome": "Legislação Estadual", "ordem": 1, "filhos": estados}])
        ids = a.subarvore([9], "Conhecimentos Regionais de Santa Catarina")
        self.assertIn(901, ids)
        self.assertNotIn(902, ids)
        self.assertEqual(201, len(ids))

    def test_disciplinas_ligadas_numa_chamada(self):
        ia = IaFalsa([{"disciplinas": {"Língua Portuguesa": [1], "Ciências da Computação": [3, 77]}}])
        m = ct.mapear_disciplinas(ia, ["Língua Portuguesa", "Ciências da Computação", "Regionais de SC"], self.arvore)
        self.assertEqual({"Língua Portuguesa": [1], "Ciências da Computação": [3], "Regionais de SC": []}, m)

    def test_edital_usa_a_disciplina_ligada(self):
        itens = ct.itens_do_edital({"assuntos": [{"assunto": "Vozes do verbo", "disciplina": "Língua Portuguesa",
                                                  "chaveExterna": "x"}]}, self.arvore, {"Língua Portuguesa": [1]})
        self.assertIn(111, [i for _, i in itens[0]["candidatos"]])
        self.assertNotIn(21, [i for _, i in itens[0]["candidatos"]])


if __name__ == "__main__":
    unittest.main()
