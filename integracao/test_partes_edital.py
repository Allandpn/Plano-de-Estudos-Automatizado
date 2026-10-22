#!/usr/bin/env python3
"""Testes das regras de partes_edital.py (extração e conferência), com trechos reais da ALESC e do TJ-SC."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import partes_edital as pe  # noqa: E402

INFRA = ("Infraestrutura de TIC: Sistemas operacionais: fundamentos; gestão de processos; instalação, configuração e "
         "administração de sistemas operacionais Windows Server 2019 e 2022 e Linux Entrerprise Active Directory (AD).")


class PartesEditalTest(unittest.TestCase):
    def test_limpa_o_que_se_repete_em_varias_paginas(self):
        conteudo = ["Engenharia de Software: Requisitos", "Gestão de Projetos: PMBOK", "Bancos de Dados: SQL", "Redes: VLAN"]
        paginas = [f"ASSEMBLEIA LEGISLATIVA DO ESTADO DE SANTA CATARINA | CONCURSO PÚBLICO 2024 {n}\n"
                   f"https://sei.tjsc.jus.br/sei/controlador.php?acao=x {n}/45\n{conteudo[n - 1]}\n{n}" for n in range(1, 5)]
        self.assertEqual([(n, conteudo[n - 1]) for n in range(1, 5)], pe.limpar(paginas))
        meio = "\n".join(f"conteúdo {k}" for k in range(20))
        uma = [f"cabeçalho {n}\n{meio}\nhttps://www.gov.br/ana/pt-br/legislacao/resolucoes\n{meio}" for n in range(1, 2)]
        self.assertIn((1, "https://www.gov.br/ana/pt-br/legislacao/resolucoes"), pe.limpar(uma), "URL no conteúdo fica")

    def test_repeticao_no_meio_da_pagina_e_conteudo(self):
        """TCE-SC 2026: título de disciplina que volta noutro módulo e fim de linha quebrada não são ruído."""
        timbre = "PREFEITURA MUNICIPAL DA ESTÂNCIA TURÍSTICA DE TREMEMBÉ\n(Lei Estadual nº 8.506)\nRua 7 de Setembro, 701\nwww.tremembe.sp.gov.br\n"
        meio = "\n".join(f"linha de conteúdo {k} da página" for k in range(1, 12))
        paginas = [f"TRIBUNAL DE CONTAS DO ESTADO DE SANTA CATARINA | CONCURSO PÚBLICO 2026 {n}\n{timbre}"
                   f"{'LÍNGUA PORTUGUESA' if n <= 3 else 'INFORMÁTICA'}\n{meio}\n1. Lei Orgânica do Tribunal de Contas do "
                   f"Estado de Santa\nCatarina.\n{meio}\núltima {n}" for n in range(1, 9)]
        ruido = []
        linhas = [t for _, t in pe.limpar(paginas, ruido=ruido)]
        self.assertEqual(3, linhas.count("LÍNGUA PORTUGUESA"), "título em 3 de 8 páginas, perto do topo, é conteúdo")
        self.assertEqual(8, linhas.count("Catarina."))
        self.assertNotIn("Rua 7 de Setembro, 701", linhas, "timbre de 5 linhas em todas as páginas é ruído")
        self.assertIn((1, "www.tremembe.sp.gov.br"), ruido)
        self.assertNotIn("TRIBUNAL DE CONTAS DO ESTADO DE SANTA CATARINA | CONCURSO PÚBLICO 2026 1", linhas)

    def test_recorte_comeca_no_titulo_e_nao_na_frase_que_o_cita(self):
        linhas = [(1, "9.8 O conteúdo programático encontra-se disponível no Anexo I deste Edital."),
                  (40, "ANEXO I – CONTEÚDO PROGRAMÁTICO"), (40, "LÍNGUA PORTUGUESA: 1. Interpretação.")]
        self.assertEqual(linhas[1:], pe.recorte_do_programa(linhas))

    def test_programa_das_provas_ate_o_anexo_seguinte_e_programa_ausente(self):
        linhas = [(1, "1.9 O conteúdo programático das provas é o constante do Anexo 2 deste Edital."),
                  (40, "ANEXO 2 PROGRAMAS DAS PROVAS"), (40, "Língua Portuguesa: Ortografia."),
                  (40, "listadas nos programas das provas."),
                  (52, "ANEXO 3 ATRIBUIÇÕES"), (52, "Analista de Sistemas: desenvolver sistemas.")]
        self.assertEqual(linhas[1:4], pe.recorte_do_programa(linhas))
        with self.assertRaises(pe.ProgramaNaoEncontrado) as caso:
            pe.recorte_do_programa([(1, "1.9 Os conteúdos programáticos das provas encontram-se no Anexo II deste Edital."),
                                    (2, "2.1 Das inscrições.")])
        self.assertIn("Anexo II", str(caso.exception))

    def test_prefixo_herdado_e_palavra_inventada(self):
        assunto = {"texto": INFRA, "partes": [
            {"texto": "fundamentos", "contexto": "Sistemas operacionais"},
            {"texto": "gestão de processos", "contexto": "Sistemas operacionais"},
            {"texto": "instalação, configuração e administração de sistemas operacionais"},
            {"texto": "Windows Server 2019"}, {"texto": "2022", "herdado": "Windows Server"},
            {"texto": "Linux Entrerprise"}, {"texto": "Active Directory (AD)", "contexto": "Infraestrutura de TIC"}]}
        self.assertEqual([], pe.conferir_assunto(assunto, "x " + INFRA + " y"))
        assunto["partes"][5] = {"texto": "Linux Enterprise"}
        erros = pe.conferir_assunto(assunto, INFRA)
        self.assertTrue(any("enterprise" in e for e in erros), "o erro de digitação do edital não pode ser corrigido")
        self.assertTrue(any("entrerprise" in e for e in erros), "e a palavra original fica sem parte")

    def test_linhas_fora_de_qualquer_disciplina(self):
        extraido = {"linhas": [{"n": i, "pagina": 1 + i // 3, "texto": f"t{i}"} for i in range(1, 9)]}
        discs = [{"linha_inicio": 2, "linha_fim": 3}, {"linha_inicio": 6, "linha_fim": 6}]
        fora = pe.linhas_fora(extraido, discs)
        self.assertEqual([(1, 1), (4, 5), (7, 8)], [(b["linha_inicio"], b["linha_fim"]) for b in fora])
        self.assertEqual(["t4", "t5"], fora[1]["linhas"])
        texto = pe.relatorio("x.pdf", "Cargo", [], fora)
        self.assertIn("3 blocos de linhas fora de qualquer disciplina", texto)
        self.assertIn("L4–L5", texto)
        self.assertEqual([], pe.linhas_fora(extraido, [{"linha_inicio": 1, "linha_fim": 8}]))

    def test_adjetivo_solto_herda_o_prefixo(self):
        # TJ-SC, Língua Portuguesa: "nominal" sozinha foi apontada como errada na conferência
        texto = "Concordância verbal e nominal."
        certo = {"texto": texto, "partes": [{"texto": "Concordância verbal"},
                                            {"texto": "nominal", "herdado": "Concordância"}]}
        self.assertEqual([], pe.conferir_assunto(certo, texto))
        regras = pe.QUEBRAR.split("TEXTO DA DISCIPLINA")[0]
        self.assertIn("Concordância verbal e nominal", regras)

    def test_assunto_reescrito_e_trecho_sem_assunto(self):
        disciplina = ("Frameworks: Conceitos; Padrão MVC (Model-View-Controller) aplicado à web; Web Services SOAP e "
                      "REST; e Expressões regulares (padrão POSIX). Versionamento de código: Conceitos; SVN; Git; e Github.")
        reescrito = {"texto": "Frameworks: conceitos e padrão MVC", "partes": [{"texto": "conceitos e padrão MVC"}]}
        self.assertIn("o assunto não é trecho do edital (foi reescrito ou juntou pedaços)",
                      pe.conferir_assunto(reescrito, disciplina))
        sobras = pe.trechos_sem_assunto(disciplina, ["Versionamento de código: Conceitos; SVN; Git; e Github."])
        self.assertEqual(1, len(sobras))
        self.assertIn("mvc", sobras[0])

    def test_repeticao_e_cabecalho_da_disciplina(self):
        texto = ("Desenvolvimento de software: Linguagem PHP (versão 8+); Linguagem Java (versão 8+); "
                 "Linguagem PHP (versão 8+); HTML5.")
        assuntos = ["Linguagem PHP (versão 8+)", "Linguagem Java (versão 8+)", "Linguagem PHP (versão 8+)", "HTML5"]
        self.assertEqual([], pe.trechos_sem_assunto(texto, assuntos, cabecalho="Desenvolvimento de software"))
        self.assertEqual(1, len(pe.trechos_sem_assunto(texto, assuntos[:2] + assuntos[3:], minimo=2,
                                                       cabecalho="Desenvolvimento de software")))
        assunto = {"texto": "RACIOCÍNIO LÓGICO MATEMÁTICO: Proposições", "partes": [{"texto": "Proposições"}]}
        self.assertEqual([], pe.conferir_assunto(assunto, assunto["texto"], "RACIOCÍNIO LÓGICO MATEMÁTICO"))

    def test_referencia_e_contexto_do_assunto_anterior(self):
        ref = "Todo o conteúdo completo das disciplinas de Auditoria, de contabilidade Geral e de Legislação Tributária"
        assunto = {"texto": "Auditoria Fiscal: " + ref + ".", "partes": []}
        self.assertEqual([], pe.conferir_assunto(assunto, assunto["texto"], "Auditoria", [ref]))
        disciplina = "Gestão ágil de produtos e projetos digitais: Gerenciamento de Produto Digital. Gestão de Portfólios e Produtos."
        assunto = {"texto": "Gestão de Portfólios e Produtos.", "partes": [
            {"texto": "Gestão de Portfólios e Produtos", "contexto": "Gestão ágil de produtos e projetos digitais"}]}
        avisos = []
        self.assertEqual([], pe.conferir_assunto(assunto, disciplina, "", [], avisos))
        self.assertEqual(1, len(avisos))
        assunto["partes"][0]["contexto"] = "Kanban"
        self.assertTrue(pe.conferir_assunto(assunto, disciplina, "", [], []), "contexto que não está em lugar nenhum é erro")

    def test_numeracao_nao_precisa_de_parte(self):
        texto = "4 Domínio dos mecanismos de coesão textual: 4.1 Emprego de elementos de referenciação. 4.2 Emprego de tempos e modos verbais."
        assunto = {"texto": texto, "partes": [
            {"texto": "Emprego de elementos de referenciação", "contexto": "Domínio dos mecanismos de coesão textual"},
            {"texto": "Emprego de tempos e modos verbais", "contexto": "Domínio dos mecanismos de coesão textual"}]}
        self.assertEqual([], pe.conferir_assunto(assunto, texto))


if __name__ == "__main__":
    unittest.main()
