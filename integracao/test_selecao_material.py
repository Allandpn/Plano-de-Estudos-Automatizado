#!/usr/bin/env python3
"""Testes de integracao/selecao_material.py: política, cobertura, páginas sem repetição, fixação e questões à parte."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import selecao_material as sm  # noqa: E402

FICHAS = {
    "A\\aula1.pdf": {"temas": [{"tema": "Git", "paginas": [[3, 12]]}, {"tema": "SVN e CVS", "paginas": [[13, 15]]}],
                     "secoes": [{"tema": "Git", "tipo": "teoria", "inicio": 3, "fim": 12},
                                {"tema": "Git", "tipo": "resumo", "inicio": 30, "fim": 31},
                                {"tema": "Git", "tipo": "questoes_comentadas", "inicio": 16, "fim": 24},
                                {"tema": "Git", "tipo": "lista_questoes", "inicio": 25, "fim": 28},
                                {"tema": "Gabarito", "tipo": "gabarito", "inicio": 29, "fim": 29},
                                {"tema": "Git", "tipo": "incidencia", "inicio": 2, "fim": 2}]},
    "B\\aula9.pdf": {"temas": [{"tema": "Controle de versão", "paginas": [[1, 40]]}], "secoes": []},
    "C\\resumo.pdf": {"temas": [{"tema": "Git em 1 página", "paginas": [[5, 5]]}], "secoes": []},
    "D\\sobreposta.pdf": {"temas": [{"tema": "Parte 1", "paginas": [[1, 10]]}, {"tema": "Parte 2", "paginas": [[8, 20]]}],
                          "secoes": []},
}


def ficha_de(c):
    return FICHAS.get(c)


def cand(caminho, tema, v):
    return {"caminho": caminho, "tema": tema, "veredito": v}


PARTES = [
    {"nome": "Git", "candidatos": [cand("A\\aula1.pdf", "Git", "ensina"), cand("B\\aula9.pdf", "Controle de versão", "ensina"),
                                   cand("C\\resumo.pdf", "Git em 1 página", "parcial"), cand("A\\aula1.pdf", "SVN e CVS", "nao")]},
    {"nome": "SVN", "candidatos": [cand("A\\aula1.pdf", "SVN e CVS", "ensina"), cand("B\\aula9.pdf", "Controle de versão", "parcial")]},
    {"nome": "Mercurial", "candidatos": [cand("A\\aula1.pdf", "Git", "nao")]},
]


class SelecaoTest(unittest.TestCase):
    def test_completo_leva_tudo_que_serve_e_declara_a_lacuna(self):
        r = sm.selecionar(PARTES, ficha_de, "completo")
        teoria = [(f["arquivo"], f["tema"]) for f in r["fontes"] if f["tipo"] == "teoria"]
        self.assertEqual([("A\\aula1.pdf", "Git"), ("B\\aula9.pdf", "Controle de versão"), ("C\\resumo.pdf", "Git em 1 página"),
                          ("A\\aula1.pdf", "SVN e CVS")], teoria)
        self.assertEqual(["Mercurial"], [l["subitem"] for l in r["lacunas"]])
        self.assertEqual(["Git", "SVN", "Mercurial"], r["subitens"])

    def test_compacto_cobre_cada_parte_com_o_conjunto_mais_curto(self):
        r = sm.selecionar(PARTES[:2], ficha_de, "compacto")
        teoria = [f for f in r["fontes"] if f["tipo"] == "teoria"]
        self.assertEqual({("A\\aula1.pdf", "Git"), ("A\\aula1.pdf", "SVN e CVS")}, {(f["arquivo"], f["tema"]) for f in teoria})
        self.assertEqual([], r["lacunas"])
        completo = sm.selecionar(PARTES[:2], ficha_de, "completo")
        self.assertLess(r["estimativa_min"], completo["estimativa_min"])

    def test_fixacao_depois_da_teoria_e_questoes_fora_das_fontes(self):
        r = sm.selecionar(PARTES[:1], ficha_de, "compacto")
        self.assertEqual(["teoria", "fixacao"], [f["tipo"] for f in r["fontes"]])
        self.assertEqual("30-31", r["fontes"][1]["paginas"])
        self.assertEqual("3-12", r["fontes"][0]["paginas"])
        self.assertEqual(["16-28", "29"], [q["paginas"] for q in r["questoes"]], "questões e lista juntas; gabarito à parte")
        usadas = {p for f in r["fontes"] for p in range(int(f["paginas"].split("-")[0]), int(f["paginas"].split("-")[-1]) + 1)}
        self.assertFalse(usadas & set(range(16, 30)), "nenhuma página de questão vira segmento")
        self.assertNotIn("2", [q["paginas"] for q in r["questoes"]], "incidência não entra em lugar nenhum")

    def test_nenhuma_pagina_se_repete_e_a_sobreposicao_une_o_que_cobre(self):
        partes = [{"nome": "p1", "candidatos": [cand("D\\sobreposta.pdf", "Parte 1", "ensina")]},
                  {"nome": "p2", "candidatos": [cand("D\\sobreposta.pdf", "Parte 2", "ensina")]}]
        r = sm.selecionar(partes, ficha_de, "completo")
        self.assertEqual(["1-10", "11-20"], [f["paginas"] for f in r["fontes"]])
        self.assertEqual(["p1", "p2"], r["fontes"][0]["cobre"], "as páginas 8-10 ensinam as duas partes")
        self.assertEqual(["p2"], r["fontes"][1]["cobre"])

    def test_secao_sem_posicao_conhecida_e_ignorada(self):
        fichas = {"E\\x.pdf": {"temas": [{"tema": "T", "paginas": [[1, 5]]}],
                              "secoes": [{"tema": "T", "tipo": "resumo", "inicio": None, "fim": None},
                                         {"tema": "T", "tipo": "questoes_comentadas", "inicio": 6, "fim": None},
                                         {"tema": "G", "tipo": "gabarito", "inicio": None, "fim": None}]}}
        r = sm.selecionar([{"nome": "t", "candidatos": [cand("E\\x.pdf", "T", "ensina")]}], fichas.get)
        self.assertEqual(["teoria"], [f["tipo"] for f in r["fontes"]])
        self.assertEqual([], r["questoes"])

    def test_tema_com_pagina_alem_do_pdf_nao_e_usado_e_vira_aviso(self):
        fichas = {"F\\y.pdf": {"paginas": 40, "temas": [{"tema": "Bom", "paginas": [[1, 10]]}, {"tema": "Ruim", "paginas": [[4, 226]]}],
                              "secoes": [{"tema": "Bom", "tipo": "resumo", "inicio": 38, "fim": 41},
                                         {"tema": "Bom", "tipo": "questoes_comentadas", "inicio": 11, "fim": 20}]}}
        partes = [{"nome": "a", "candidatos": [cand("F\\y.pdf", "Bom", "ensina"), cand("F\\y.pdf", "Ruim", "ensina")]}]
        r = sm.selecionar(partes, fichas.get)
        self.assertEqual(["1-10"], [f["paginas"] for f in r["fontes"]], "o resumo passa do fim do PDF e fica de fora")
        self.assertEqual([("F\\y.pdf", "Ruim")], [(a["arquivo"], a["tema"]) for a in r["avisos"]])
        self.assertIn("40", r["avisos"][0]["motivo"])
        self.assertEqual(["11-20"], [q["paginas"] for q in r["questoes"]])

    def test_nomes_repetidos_ganham_rotulo_unico(self):
        self.assertEqual(["Kanban", "Kanban (2)", "XP"], sm.rotulos_unicos(["Kanban", "Kanban", "XP"]))

    def test_texto_das_paginas(self):
        self.assertEqual("3-5,9,11-12", sm.texto_das_paginas({3, 4, 5, 9, 11, 12}))

    def test_modo_invalido_e_candidato_sem_pagina_na_ficha(self):
        with self.assertRaises(ValueError):
            sm.selecionar(PARTES, ficha_de, "meio-termo")
        r = sm.selecionar([{"nome": "x", "candidatos": [cand("A\\aula1.pdf", "Tema que sumiu", "ensina")]}], ficha_de)
        self.assertEqual(([], ["x"]), (r["fontes"], [l["subitem"] for l in r["lacunas"]]))


if __name__ == "__main__":
    unittest.main()
