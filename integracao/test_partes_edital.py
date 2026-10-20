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
                   f"https://sei.tjsc.jus.br/sei/controlador.php?acao=x\n{conteudo[n - 1]}\n{n}" for n in range(1, 5)]
        self.assertEqual([(n, conteudo[n - 1]) for n in range(1, 5)], pe.limpar(paginas))

    def test_recorte_comeca_no_titulo_e_nao_na_frase_que_o_cita(self):
        linhas = [(1, "9.8 O conteúdo programático encontra-se disponível no Anexo I deste Edital."),
                  (40, "ANEXO I – CONTEÚDO PROGRAMÁTICO"), (40, "LÍNGUA PORTUGUESA: 1. Interpretação.")]
        self.assertEqual(linhas[1:], pe.recorte_do_programa(linhas))

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

    def test_assunto_reescrito_e_trecho_sem_assunto(self):
        disciplina = ("Frameworks: Conceitos; Padrão MVC (Model-View-Controller) aplicado à web; Web Services SOAP e "
                      "REST; e Expressões regulares (padrão POSIX). Versionamento de código: Conceitos; SVN; Git; e Github.")
        reescrito = {"texto": "Frameworks: conceitos e padrão MVC", "partes": [{"texto": "conceitos e padrão MVC"}]}
        self.assertIn("o assunto não é trecho do edital (foi reescrito ou juntou pedaços)",
                      pe.conferir_assunto(reescrito, disciplina))
        sobras = pe.trechos_sem_assunto(disciplina, ["Versionamento de código: Conceitos; SVN; Git; e Github."])
        self.assertEqual(1, len(sobras))
        self.assertIn("mvc", sobras[0])

    def test_numeracao_nao_precisa_de_parte(self):
        texto = "4 Domínio dos mecanismos de coesão textual: 4.1 Emprego de elementos de referenciação. 4.2 Emprego de tempos e modos verbais."
        assunto = {"texto": texto, "partes": [
            {"texto": "Emprego de elementos de referenciação", "contexto": "Domínio dos mecanismos de coesão textual"},
            {"texto": "Emprego de tempos e modos verbais", "contexto": "Domínio dos mecanismos de coesão textual"}]}
        self.assertEqual([], pe.conferir_assunto(assunto, texto))


if __name__ == "__main__":
    unittest.main()
