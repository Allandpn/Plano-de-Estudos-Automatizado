#!/usr/bin/env python3
"""Testes de integracao/estrutura_apostilas.py com um índice sintético no formato real das apostilas.
As linhas entre aspas vêm do texto cru do índice (`--bruto`) de quatro aulas: Redes aula 06 (formato A),
Legislação Tributária de SC (B), Passo Estratégico de Português aula 06 (C) e Bizu de Direito Financeiro (D)."""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estrutura_apostilas as ea  # noqa: E402
from test_worker import SCHEMA_INDICE  # noqa: E402


def pontilhar(texto, pagina, colada=False):
    """Como a extração devolve a linha do sumário: pontos intercalados com as letras; no índice real a
    página vem grudada nos pontos ('colada')."""
    return "." + "..".join(texto) + "." * 40 + ("" if colada else " ") + f"{pagina}"


SUMARIO = "\n".join(["Índice",
                     pontilhar("1). NAT e PAT - Teoria", 3),
                     pontilhar("2). NAT e PAT - Questões Comentadas - CEBRASPE", 6),
                     pontilhar("3). NAT e PAT - Lista de Questões - FCC", 8),
                     pontilhar("4). Protocolo IPv6 - Resumo", 10)])
PAGINAS = ["Redes de Computadores - Curso Regular\nAula 06", SUMARIO,
           "NAT E PAT\nteoria do NAT", "mais teoria", "teoria", "NAT e PAT - Q C - UESTÕES OMENTADAS\n1. (CEBRASPE - PF)",
           "2. (CEBRASPE - TCU)", "NAT e PAT - lista\n1. (FCC - TRT)", "Gabarito 1-A", "PROTOCOLO IPV6 resumo"]

# Formato A, linhas cruas de Redes aula 06 (a página fica grudada na última palavra).
A_TEORIA = ".1..). .N..A...T.. .e.. .P..A...T.. .-. .T..e..o..r.i.a" + "." * 105
A_CESGRANRIO = (".2..). .N..A...T.. .e.. .P..A...T.. .-. .Q...u..e..s..t.õ..e..s. .C...o..m...e..n..t.a..d..a..s.. .-. "
                ".C...e..s.g..r..a..n..r.i.o" + "." * 31)
A_FGV = (".1..4..). .P..r.o..t.o..c..o..l.o.. .I.P..v..6.. .-. .Q...u..e..s..t.õ..e..s.. .C..o..m...e..n..t.a..d..a..s.."
         " .-. .F..G...V" + "." * 36)

# Formato B: Legislação Tributária de SC, arquivo aula-00 que é a AULA 14.
LEI = ["SEFAZ-SC (Auditor Fiscal) Legislação\nTributária de Santa Catarina (parte I -\nProf. Rafael da Rocha)",
       "AULA 14\nSUMÁRIO PÁGINA\n1. Introdução ao Código do Contribuinte 02\n2. Dos Direitos do Contribuinte 12\n"
       "3. Das Obrigações do Contribuinte 21\n8. Bateria de Questões 40\n9. Lista de Questões 46\n10. Gabarito 50\n"
       "11. Bibliografia 51"]
LEI += ["texto corrido de lei"] * 51
LEI[2] = "1. Introdução ao Código do Contribuinte\nOlá, pessoal! A nossa aula teórica vai tratar do Código"
LEI[12] = "2. Dos Direitos do Contribuinte\nArt. 16. São direitos do contribuinte:"
LEI[21] = "3. Das Obrigações do Contribuinte\nArt. 28. São obrigações do contribuinte:"
LEI[40] = "8. BATERIA DE QUESTÕES\n1) (UEPA/AFRE-PA/2013/adaptada) A respeito do disposto"
LEI[46] = "9. LISTA DE QUESTÕES\n1) (UEPA/AFRE-PA/2013/adaptada) A respeito do disposto"
LEI[50] = "10. GABARITO\n01 E 02 B 03 C 04 B 05 C 06 B"
LEI[51] = "11. BIBLIOGRAFIA\nBRASIL. Constituição da República Federativa do Brasil."


def leader(texto, pagina):
    return texto + " " + "." * 60 + f" {pagina}"


# Formato C: Passo Estratégico de Português, aula 06; o questionário anexado recomeça a numeração.
PASSO = ["Concursos da Área Fiscal - Passo\nEstratégico Básico de Português\nAutor:",
         "\n".join(["L , T F", "INGUAGEM IPOLOGIA E ONÉTICA", leader("Linguagem, Tipologia e Fonética", 2),
                    leader("O que é mais cobrado dentro do assunto?", 2),
                    leader("Roteiro de Revisão e pontos do assunto que merecem destaque", 2),
                    leader("Tipologia Textual", 2), leader("Descrição", 4), leader("Linguagem", 6),
                    leader("Figuras de Linguagem", 10), leader("Figuras de Sintaxe", 12),
                    leader("Figuras de Pensamento", 14), leader("Aposta Estratégica", 20),
                    leader("Questões estratégicas", 22), leader("Questionário de revisão e aperfeiçoamento", 2),
                    leader("Perguntas", 3), "Perguntas e respostas" + "." * 60 + "3", leader("Gabarito", 5),
                    leader("Bibliografia", 5)]),
         "\n".join(["LINGUAGEM, TIPOLOGIA E FONÉTICA", "O QUE É MAIS COBRADO DENTRO DO ASSUNTO?",
                    "A análise a seguir refere-se a uma amostra de 268 questões, abrangendo provas realizadas pelas",
                    "bancas FGV, FCC e Cebraspe para nível superior no período de 2023 a 2026.",
                    "Até 1,9% Baixa a Mediana", "Subassunto %", "Tipologia textual e gêneros textuais 45,5%",
                    "Funções da linguagem 33,3%", "Fonética (reconhecimento de fonemas, encontros) 21,2%", "Total 100%",
                    "ROTEIRO DE REVISÃO E PONTOS DO ASSUNTO QUE MERECEM DESTAQUE", "TIPOLOGIA TEXTUAL"])]
PASSO += ["texto do passo"] * 37
PASSO[10] = "FIGURAS DE LINGUAGEM\nNas figuras de linguagem, as palavras apresentam sentidos expandidos,"
PASSO[12] = "FIGURAS DE SINTAXE\nNas figuras de sintaxe ou figuras de construção, as palavras sofrem mu"
PASSO[14] = "FIGURAS DE PENSAMENTO\nAs Figuras de Pensamento são recursos estilísticos utilizados"
PASSO[28] = 'Gabarito: Letra "B"\nQuestão 6: Denotação vs. Conotação\nSombra e água'
PASSO[34] = "BUARQUE, Chico. Phonogram, 1976.\nQUESTIONÁRIO DE REVISÃO E APERFEIÇOAMENTO"
PASSO[35] = "PERGUNTAS\n1. O que é tipologia textual?\n2. Qual é a diferença entre tipo e gênero textual?"

# Formato D: Bizu de Direito Financeiro (SEFAZ-CE), aula 11.
BIZU = ["02751121365 - A\nSEFAZ-CE (Auditor Fiscal da Receita\nEstadual - Gestão Fazendária e",
        "B E D F\nIZU STRATÉGICO DE IREITO INANCEIRO\nSEFAZ-CE\nOlá, prezado aluno. Tudo certo?",
        "A E\nNÁLISE STATÍSTICA\nConforme as últimas provas aplicadas pela banca FCC, vejamos a frequência com que os temas\n"
        "Direito Financeiro\nAssunto\n%\nDespesa Pública 13,20%\nInstrumentos Orçamentários 11,17%\n"
        "Créditos Ordinários e Adicionais 5,59%",
        "\n".join(["Direito Financeiro", "Assunto Bizus Caderno de Questões",
                   "Instrumentos Orçamentários 1 a 4 http://questo.es/9anrok", "Despesa Pública 5 e 6 http://questo.es/chaeby",
                   "Receita Pública 7 e 8 http://questo.es/y0nn1m", "Princípios Orçamentários 9 http://questo.es/12lgsj",
                   "Restos a Pagar, Despesas de Exercícios", "10 a 12 http://questo.es/hiya3b",
                   "Anteriores e Suprimento de Fundos", "Disposições Preliminares, Planejamento e",
                   "13 a 20 http://questo.es/krkaz2", "Orçamento na LRF", "Transparência, Controle e Fiscalização e",
                   "21 a 27 http://questo.es/x2hlhc", "Receita Pública na LRF", "28 a 37 http://questo.es/kpl4rq",
                   "Despesa Pública na LRF", "38 a 42 http://questo.es/fmz1qr", "Créditos Ordinários e Adicionais"])]
BIZU += ["texto do bizu"] * 43
BIZU[4] = "Apresentação\nOlá, futuro servidor público!"
BIZU[5] = "Instrumentos Orçamentários\n1. Leis Orçamentárias\ni. Leis Orçamentárias: leis ordinárias"
BIZU[8] = "Despesa Pública\n5. Classificações da Despesa Pública\ni. Forma de ingresso:"
BIZU[13] = "PessoalCivil\nPessoalMilitar\nMaterialdeConsumo"
BIZU[14] = "Receita Pública\n7. Conceito\n➢ Sentido amplo: Receita Pública = Receitas Orçamentárias + Receitas"
BIZU[17] = "Princípios Orçamentários\n9. Princípios impostos ao orçamento"
BIZU[19] = "Restos a Pagar, Despesas de Exercícios Anteriores e\nSuprimento de Fundos\n10. Restos a Pagar"
BIZU[24] = "Disposições Preliminares na LRF\n13. Princípios da LRF\nPrincipiosdaIRF"
BIZU[25] = "r\ns*ptppi|dnpsesepinpxa\n(cid:127)"
BIZU[29] = "Transparência, Controle e Fiscalização na LRF\n21. Instrumentos de transparência"
BIZU[36] = "Da Despesa Pública na LRF\n28. Geração de despesa"
BIZU[42] = "Créditos Ordinários e Adicionais\n38. Créditos Ordinários"

AULAS = [("00 - Curso Regular\\09 - Redes de Computadores", "aula 06.pdf", PAGINAS),
         ("00 - Curso Regular\\09 - Redes de Computadores", "aviso.pdf", ["AVISO IMPORTANTE", "texto"]),
         ("04 - SEFAZ-SC\\09 - Legislação Tributária de Santa Catarina - Parte 01",
          "curso-226705-aula-00-639a-completo.pdf", LEI),
         ("Cursos Regulares\\39 - Passo Estratégico Básico de Português", "curso-376803-aula-06-5dea-completo.pdf", PASSO),
         ("SEFAZ-CE 2026\\22 - Bizu Estratégico", "curso-383914-aula-11-02d5-completo.pdf", BIZU)]


class EstruturaTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.conn = sqlite3.connect(Path(self._tmp.name) / "i.db")
        self.conn.executescript(SCHEMA_INDICE)
        for i, (curso, nome, paginas) in enumerate(AULAS, 1):
            self.conn.execute("INSERT INTO arquivos (caminho, curso, nome_arquivo, n_paginas) VALUES (?, ?, ?, ?)",
                              (f"x{i}", curso, nome, len(paginas)))
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
                          "rotulo": "CEBRASPE", "pagina": 6, "formato": "A", "titulo_tipo": "Questões Comentadas"}, e)
        self.assertEqual("CEBRASPE", ea.entrada_do_sumario("3) Redes - Questões Comentadas - Cebraspe 9")["banca"])
        self.assertIsNone(ea.entrada_do_sumario("texto corrido da aula"))

    def test_r1_pagina_grudada_na_ultima_palavra(self):
        self.assertEqual("1) NAT e PAT - Teoria", ea.decodificar(A_TEORIA))
        e = ea.entrada_do_sumario(A_TEORIA + "4")
        self.assertEqual(("NAT e PAT", "teoria", None, 4), (e["tema"], e["tipo"], e["banca"], e["pagina"]))
        e = ea.entrada_do_sumario(A_CESGRANRIO + "17")
        self.assertEqual(("questoes_comentadas", "CESGRANRIO", 17), (e["tipo"], e["banca"], e["pagina"]))
        e = ea.entrada_do_sumario(A_FGV + "109")
        self.assertEqual(("Protocolo IPv6", "FGV", 109), (e["tema"], e["banca"], e["pagina"]))

    def test_r2_r6_formatos_b_e_c(self):
        e = ea.entrada_do_sumario("1. Introdução ao Código do Contribuinte 02")
        self.assertEqual(("B", 1, "Introdução ao Código do Contribuinte", 2), (e["formato"], e["n"], e["tema"], e["pagina"]))
        self.assertEqual("questoes_comentadas", ea.entrada_do_sumario("8. Bateria de Questões 40")["tipo"])
        self.assertEqual("bibliografia", ea.entrada_do_sumario("11. Bibliografia 51")["tipo"])
        self.assertIsNone(ea.entrada_do_sumario("1. Kurose - Redes de Computadores e a Internet - Uma abordagem Top Dow"))
        self.assertIsNone(ea.entrada_do_sumario("SUMÁRIO PÁGINA"))
        tipos = {t: ea.entrada_do_sumario(leader(t, 2))["tipo"] for t in
                 ["O que é mais cobrado dentro do assunto?", "Roteiro de Revisão e pontos do assunto que merecem destaque",
                  "Aposta Estratégica", "Questões estratégicas", "Perguntas e respostas", "Linguagem"]}
        self.assertEqual(["incidencia", "resumo", "resumo", "questoes_comentadas", "questionario", None], list(tipos.values()))
        e = ea.entrada_do_sumario("Perguntas e respostas" + "." * 60 + "3")
        self.assertEqual(("C", None, 3), (e["formato"], e["n"], e["pagina"]))

    def test_r1_tema_que_termina_em_numero(self):
        """Passo de TI, aula 28: 'NBR 27002-2022' + página grudada; o tipo vem antes do tema."""
        linhas = [pontilhar(t, p, colada=True) for t, p in [
            ("1). O que é mais cobrado no assunto - NBR 27002-2022 - MULTIBANCAS", 3),
            ("2). Roteiro de Revisão - NBR 27002-2022", 4), ("3). Aposta Estratégica - NBR 27002-2022", 17),
            ("4). Questões Estratégicas - NBR 27002-2022 - MULTIBANCAS", 19),
            ("5). Questionário de Revisão - NBR 27002-2022", 25)]]
        e = ea.sumario([(1, "capa"), (2, "\n".join(linhas))] + [(p, "") for p in range(3, 35)])
        self.assertEqual([3, 4, 17, 19, 25], [x["pagina"] for x in e])
        self.assertEqual({"NBR 27002-2022"}, {x["tema"] for x in e})
        self.assertEqual(["incidencia", "resumo", "resumo", "questoes_comentadas", "questionario"], [x["tipo"] for x in e])
        self.assertEqual("MULTIBANCAS", e[0]["banca"])
        self.assertEqual({0}, {x["seq"] for x in e}, "sem página lida errada, nada de sequência nova")
        paginas = [(1, "capa"), (2, "\n".join(linhas)), (3, "O QUE É MAIS COBRADO NO ASSUNTO?\nNBR 27002"),
                   (4, "ROTEIRO DE REVISÃO\ntexto")] + [(p, "") for p in range(5, 35)]
        self.assertEqual((0, 2, 5), ea.deslocamentos(paginas, e)[0], "o tema 'NBR' é curto; confere pelo tipo")
        a = ea.entrada_do_sumario(pontilhar("4). Encontros Vocálicos", 8, colada=True))
        self.assertIsNone(a["tipo"])
        self.assertEqual("teoria", ea.sumario([(1, ""), (2, "\n".join([pontilhar("1). Ortografia - Lista de Questões", 3), pontilhar(
            "2). Encontros Vocálicos", 8)]))])[1]["tipo"], "no formato A, título sem tipo é teoria, não herda")

    def test_r4_tipo_confirma_titulo_sem_o_tema_inteiro(self):
        """Redes aula 06, p. 37: o título diz 'NAT PAT' (sem o E); o tipo 'Lista de Questões' confirma."""
        paginas = [(1, "capa"), (2, pontilhar("6). NAT e PAT - Lista de Questões - Cesgranrio", 3, colada=True) + "\n"
                   + pontilhar("7). NAT e PAT - Lista de Questões - Cebraspe", 4, colada=True)),
                   (3, "L Q – NAT PAT - CESGRANRIO\nISTA DE UESTÕES E\n1. CESGRANRIO - 2018 - Transpetro"),
                   (4, "L Q – NAT E PAT - CESPE\nISTA DE UESTÕES\n1. CESPE / CEBRASPE - 2024 - STJ")]
        e = ea.sumario(paginas)
        self.assertEqual({0: (0, 2, 2)}, ea.deslocamentos(paginas, e))

    def test_sumario_a_seguido_de_detalhado_c_sao_duas_listas(self):
        """Ciência de Dados, aula 07: Índice A de 3 entradas e, na p. 3, o conteúdo detalhado (C)."""
        paginas = [(1, "capa"),
                   (2, "Índice\n" + pontilhar("1). Redes Neurais e Deep Learning", 4, colada=True) + "\n"
                    + pontilhar("2). Questões Comentadas - Cesgranrio", 9, colada=True) + "\n"
                    + pontilhar("3). Lista de Questões - Cesgranrio", 10, colada=True)),
                   (3, "\n".join([leader("Conteúdo da aula", 3), leader("O Perceptron", 5), leader("Redes de Hopfield", 7)])),
                   (4, "CONTEÚDO DA AULA\nREDES NEURAIS E DEEP LEARNING"), (5, "texto"), (6, "O PERCEPTRON\ntexto"),
                   (7, "texto"), (8, "REDES DE HOPFIELD\ntexto"), (9, "Q C – CESGRANRIO\nUESTÕES OMENTADAS"),
                   (10, "L Q – CESGRANRIO\nISTA DE UESTÕES")]
        e = ea.sumario(paginas)
        self.assertEqual([0, 0, 0, 1, 1, 1], [x["lista"] for x in e])
        self.assertEqual("teoria", e[4]["tipo"], "a lista nova não herda o tipo da anterior")
        res = ea.deslocamentos(paginas, e)
        self.assertEqual((0, 3, 3), res[0])
        self.assertEqual((1, 3, 3), res[1])
        ea.fechar_secoes(e, 10)
        # o último item do detalhado para no fim da teoria do índice principal (p. 8), não engole as questões
        self.assertEqual([(4, 8), (9, 9), (10, 10), (4, 5), (6, 7), (8, 8)], [(x["inicio"], x["fim"]) for x in e])

    def test_entrada_sem_pagina_e_procurada_no_corpo(self):
        """Bizu de Economia (SEFAZ-CE, aula 22): '1) Conceitos fundamentais' sem página no índice."""
        paginas = [(1, "capa"), (2, "Segue índice da aula\n1) Conceitos fundamentais\n2) Princípios econômicos"),
                   (3, "Microeconomia: Conceitos Fundamentais 5,80%"), (4, "CONCEITOS FUNDAMENTAIS\ntexto"),
                   (5, "texto"), (6, "PRINCÍPIOS ECONÔMICOS\ntexto")]
        e = ea.sumario(paginas)
        self.assertEqual({0: (None, 2, 2)}, ea.deslocamentos(paginas, e))
        self.assertEqual([4, 6], [x["inicio"] for x in e])

    def test_r4_confere_titulo_mutilado(self):
        self.assertTrue(ea.conferir("Protocolo IPv6", "P IP 6\nROTOCOLO V\nO protocolo IPv6 surgiu como evolução"))
        self.assertTrue(ea.conferir("NAT e PAT", "Q C – NAT E PAT - CESGRANRIO\nUESTÕES OMENTADAS\n1. CESGRANRIO - 2018"))
        self.assertTrue(ea.conferir("Gabarito", "G\nABARITO\n01 02 03 04 05 06"))
        self.assertFalse(ea.conferir("Gabarito", 'Gabarito: Letra "B"\nQuestão 6: Denotação vs. Conotação'))
        self.assertTrue(ea.conferir("Do Sistema Estadual de Ética Tributária",
                                    "7. Do Sistema Estadual da Ética Tributária\nArt. 47. Fica instituído"))

    def test_aula_le_tema_tipo_banca_e_confere_a_pagina(self):
        a = ea.analisar_aula(self.conn, 1)
        self.assertEqual(["teoria", "questoes_comentadas", "lista_questoes", "resumo"], [e["tipo"] for e in a["entradas"]])
        self.assertEqual("FCC", a["entradas"][2]["banca"])
        self.assertEqual((0, 4, 4), a["deslocamento"], "a página do sumário é a do PDF; o tema está escrito nela")
        self.assertEqual([(3, 5), (6, 7), (8, 9), (10, 10)], [(e["inicio"], e["fim"]) for e in a["entradas"]])
        self.assertEqual((["CEBRASPE", "FCC"], "sumário"), a["banca"])
        self.assertEqual((6, "conteúdo"), a["aula"])
        self.assertFalse(a["fora"])

    def test_formato_b_desloca_um_e_le_a_aula_do_conteudo(self):
        a = ea.analisar_aula(self.conn, 3)
        self.assertEqual("B", a["formato"])
        self.assertEqual((1, 7, 7), a["deslocamento"])
        self.assertEqual((14, "conteúdo"), a["aula"], "o arquivo diz aula-00")
        e = {x["tema"]: x for x in a["entradas"]}
        self.assertEqual((41, 46), (e["Bateria de Questões"]["inicio"], e["Bateria de Questões"]["fim"]))
        self.assertEqual("teoria", e["Dos Direitos do Contribuinte"]["tipo"])
        self.assertEqual((52, 53), (e["Bibliografia"]["inicio"], e["Bibliografia"]["fim"]))

    def test_formato_c_numeracao_que_recomeca_e_incidencia(self):
        a = ea.analisar_aula(self.conn, 4)
        self.assertEqual("C", a["formato"])
        self.assertEqual(1, a["sequencias"][0][0])
        self.assertEqual(33, a["sequencias"][1][0], "Perguntas 3 é a p. 36 do PDF")
        e = {x["tema"]: x for x in a["entradas"]}
        self.assertEqual("resumo", e["Figuras de Sintaxe"]["tipo"], "herda do Roteiro de Revisão")
        self.assertEqual((36, True), (e["Perguntas"]["inicio"], e["Perguntas"]["confirmada"]))
        inc = a["incidencia"]
        self.assertEqual(3, inc["pagina"])
        self.assertEqual(("Tipologia textual e gêneros textuais", 45.5), inc["subassuntos"][0])
        self.assertEqual(3, len(inc["subassuntos"]))
        self.assertEqual((["FCC", "CEBRASPE", "FGV"], "2023–2026"), (inc["bancas"], inc["periodo"]))
        self.assertEqual((["FCC", "CEBRASPE", "FGV"], "incidência"), a["banca"])

    def test_formato_d_bizu_pela_tabela_de_faixas(self):
        itens = ea.tabela_bizus([(p, t) for p, t in enumerate(BIZU, 1)])
        self.assertEqual(9, len(itens))
        self.assertEqual({"tema": "Restos a Pagar, Despesas de Exercícios Anteriores e Suprimento de Fundos",
                          "bizus": (10, 12)}, itens[4])
        self.assertEqual("Transparência, Controle e Fiscalização e Receita Pública na LRF", itens[6]["tema"])
        self.assertEqual(("Despesa Pública na LRF", (28, 37)), (itens[7]["tema"], itens[7]["bizus"]))
        self.assertEqual("Créditos Ordinários e Adicionais", itens[8]["tema"])
        a = ea.analisar_aula(self.conn, 5)
        self.assertEqual("D", a["formato"])
        self.assertEqual([6, 9, 15, 18, 20, 25, 30, 37, 43], [e["inicio"] for e in a["entradas"]])
        self.assertEqual((6, 8), (a["entradas"][0]["inicio"], a["entradas"][0]["fim"]))
        self.assertEqual([14, 26], a["ilegiveis"])
        self.assertEqual([("Despesa Pública", 13.2), ("Instrumentos Orçamentários", 11.17),
                          ("Créditos Ordinários e Adicionais", 5.59)], a["incidencia"]["subassuntos"])
        self.assertEqual((["FCC"], "incidência"), a["banca"])

    def test_bizu_com_nome_partido_na_tabela_e_bizu_no_meio_da_pagina(self):
        """Bizu de Contabilidade Geral (SEFAZ-CE, aula 12): o nome ocupa várias linhas em volta da faixa e os
        bizus 2 a 4 começam no meio da página."""
        tabela = "\n".join(["Contabilidade Geral", "Assunto Bizus Caderno de Questões",
                            "Estoques: Componentes do custo. Critérios de", "valoração, apuração do custo das mercadorias",
                            "vendidas e métodos de avaliação (Preço específico,", "1 http://questo.es/xi8xnp",
                            "PEPS, Média Ponderada Móvel). Tipos de inventário.", "Tratamento contábil dos tributos incidentes em",
                            "operações comerciais.", "Ativo imobilizado: Reconhecimento. Mensuração",
                            "inicial e mensuração subsequente. Depreciação:", "2 http://questo.es/joa6f5",
                            "cálculo e contabilização. Tratamento do resultado na", "venda e da baixa do ativo."])
        paginas = [(1, "capa"), (2, "bizu"), (3, "análise"), (4, tabela), (5, "Apresentação"),
                   (6, "1. Estoques: Componentes do custo. Critérios de valoração,\napuração do custo"),
                   (7, "texto\n2) a lista de exemplos não conta\n2. depois de minúscula também não"),
                   (8, "• lucro maior\ntexto\nmais texto\n2. Ativo imobilizado: Reconhecimento. Mensuração inicial"),
                   (9, "texto")]
        e = ea.secoes_do_bizu(paginas, ea.tabela_bizus(paginas))
        self.assertEqual([("Estoques", 6), ("Ativo imobilizado", 8)], [(x["tema"], x["inicio"]) for x in e])

    def test_r9_pagina_ilegivel(self):
        self.assertTrue(ea.ilegivel("r\ns*ptppi|dnpsesepinpxa\n(cid:127)"))
        self.assertTrue(ea.ilegivel("PessoalCivil\nPessoalMilitar\nMaterialdeConsumo"))
        self.assertFalse(ea.ilegivel("É sabido que a quantidade de endereços IP é limitada frente às diversas combinações e"))
        self.assertFalse(ea.ilegivel(""))
        self.assertFalse(ea.ilegivel("\n".join([A_CESGRANRIO + "17", A_FGV + "109", A_TEORIA + "4"])), "a pontilhada não conta")
        p21 = ("No caso deestimativa ,sao possfveis duassituagoes:;\nValor real > valor inscrito em RP: a diferenga sera "
               "empenhada a conta de\n.\ndespesas de exercicios anteriores\nValor real <valor insoritoemRP:: osaldo existente "
               "sera cancelado.\nAredu(iooucancelamento,noexercicio Aimportancecorrespondent*\n(cid:127)\nfinanceiro,"
               "decomprommoquecaracteriiouo serarevertIdaarespective\nempenho.implicatesuaanulafiopare(*loutotal. "
               "dota^aoor(amenta/ia\nconuderarso-arece/taor(amentanadoanoemqueseefettvar.")
        self.assertTrue(ea.ilegivel(p21))

    def test_bruto_mostra_a_pagina_crua_e_decodificada(self):
        md = ea.bruto(self.conn, "aula 06")
        self.assertIn("NAT e PAT - Teoria 3", md)
        self.assertIn("- p. 6: NAT e PAT - Q C - UESTÕES OMENTADAS", md)
        self.assertIn("nenhum arquivo casou", ea.bruto(self.conn, "nao existe"))

    def test_arquivo_curto_sem_sumario_fica_fora(self):
        self.assertTrue(ea.analisar_aula(self.conn, 2)["fora"])

    def test_relatorio_resume_por_curso(self):
        md = ea.relatorio(self.conn, ["Redes de Computadores", "Bizu", "Nao Existe"], 3)
        self.assertIn("| 2 | 1 | 1 | 4 | 100% | 50% | +0 (4/4) | A | 0/12 | 0 |", md)
        self.assertIn("| D | 2/47 | 1 |", md)
        self.assertIn("p. 6–8 ✓", md)
        self.assertIn("_nenhum arquivo casou_", md)


if __name__ == "__main__":
    unittest.main()
