#!/usr/bin/env python3
"""
Testes de integracao/prova_questoes.py: das linhas da prova às questões.

Rodar (da raiz do repositório):
    python -m unittest discover -s integracao -p "test_*.py"

As fixtures são sintéticas, escritas no FORMATO que cada banca usa (amostra real de FGV, CEBRASPE,
IDECAN e FCC, 2026-10-18) — não o texto de provas de verdade. Cada teste nomeia a armadilha real
que protege.
"""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prova_pdf as pp  # noqa: E402
import prova_questoes as pq  # noqa: E402


def L(texto, pagina=1, conf=None, imagem=None):
    return pp.Linha(texto, pagina, imagem, conf)


def enun(n):
    """Um enunciado diferente por questão. Texto igual em todas viraria 'cabeçalho repetido' e seria filtrado."""
    return f"Enunciado sobre o tema {chr(97 + n % 26)}{chr(97 + n // 26)} sem repetição."


def alternativas(letras="ABCDE", prefixo="(%s)", pagina=1, conf=None, imagem=None):
    return [L(f"{prefixo % l} alternativa {l.lower()} com texto suficiente.", pagina, conf, imagem) for l in letras]


def pagina_fgv(numero_da_pagina, questoes):
    """Uma página de prova da FGV: cabeçalho e rodapé que se repetem, número da questão sozinho."""
    linhas = [L("DATAPREV - EMPRESA DE TECNOLOGIA", numero_da_pagina), L("FGV CONHECIMENTO", numero_da_pagina),
              L(f"TIPO 1 – PÁGINA {numero_da_pagina}", numero_da_pagina)]
    for n, enunciado in questoes:
        linhas += [L(str(n), numero_da_pagina), L(enunciado, numero_da_pagina)] + alternativas(pagina=numero_da_pagina)
    return linhas


class FgvTest(unittest.TestCase):
    def prova(self, paginas=4):
        linhas = [L("CONCURSO PÚBLICO DA EMPRESA", 1), L("NÍVEL SUPERIOR – TARDE", 1), L("TIPO 1", 1),
                  # A armadilha real da capa: uma linha que começa com o número da questão 2.
                  L("2 (duas) horas após o início da prova, é possível retirar-se da sala.", 1)]
        n = 1
        for pagina in range(2, paginas + 2):
            linhas += pagina_fgv(pagina, [(n, enun(n)), (n + 1, enun(n + 1))])
            n += 2
        return linhas

    def test_acha_todas_as_questoes_com_cinco_alternativas_apesar_da_capa(self):
        seg = pq.segmentar(self.prova())

        self.assertEqual("MULTIPLA_ESCOLHA", seg.formato)
        self.assertEqual(list(range(1, 9)), [q.numero for q in seg.questoes])
        self.assertTrue(all(q.motivo is None for q in seg.questoes))
        self.assertTrue(all([a for a, _ in q.alternativas] == list("ABCDE") for q in seg.questoes))
        self.assertEqual(enun(1), seg.questoes[0].enunciado,
                         "a linha da capa 'N (duas) horas...' não vira a questão 2 nem consome a numeração")

    def test_cabecalho_e_rodape_repetidos_nao_entram_na_ultima_alternativa(self):
        seg = pq.segmentar(self.prova())

        for q in seg.questoes:
            self.assertNotIn("PÁGINA", q.alternativas[-1][1])
            self.assertNotIn("FGV", q.alternativas[-1][1])

    def test_o_numero_sozinho_se_repete_70_vezes_e_nao_e_filtrado_como_cabecalho(self):
        linhas = []
        for n in range(1, 41):
            linhas += [L(str(n), 2 + n // 8), L(enun(n), 2 + n // 8)] + alternativas(pagina=2 + n // 8)

        seg = pq.segmentar(linhas)

        self.assertEqual(40, len(seg.questoes))
        self.assertTrue(all(q.motivo is None for q in seg.questoes))

    def test_cabecalho_de_disciplina_vai_para_a_questao_seguinte(self):
        linhas = [L("1", 2), L("Enunciado um."), *alternativas()]
        linhas[-1] = L("(E) última alternativa da questão um, que termina com ponto.")
        linhas += [L("Legislação e Código de Ética do MPES"), L("2", 2), L("Enunciado dois."), *alternativas()]

        seg = pq.segmentar(linhas)

        self.assertIsNone(seg.questoes[0].cabecalho)
        self.assertEqual("Legislação e Código de Ética do MPES", seg.questoes[1].cabecalho)
        self.assertNotIn("Legislação", seg.questoes[0].alternativas[-1][1], "o cabeçalho não gruda na alternativa E")

    def test_lista_numerada_no_enunciado_nao_abre_a_questao_seguinte(self):
        # O enunciado da questão 1 traz uma lista com "2." — igual ao número da próxima questão.
        linhas = [L("1"), L("Considere as afirmações:"), L("2. o segundo item da lista;"), L("3. o terceiro item."),
                  *alternativas(), L("2"), L("Enunciado dois."), *alternativas()]

        seg = pq.segmentar(linhas)

        self.assertEqual([1, 2], [q.numero for q in seg.questoes])
        self.assertIn("segundo item da lista", seg.questoes[0].enunciado)
        self.assertEqual("Enunciado dois.", seg.questoes[1].enunciado)

    def test_alternativa_que_quebra_em_varias_linhas_e_palavra_hifenizada(self):
        linhas = [L("1"), L("O contrato de manutenção, previsto no edi-"), L("tal, exige o quê?"),
                  L("(A) a divulgação obrigatória do contrato no PNCP constitui medida de"), L("transparência importante."),
                  *alternativas("BCDE")]

        q = pq.segmentar(linhas).questoes[0]

        self.assertEqual("O contrato de manutenção, previsto no edital, exige o quê?", q.enunciado)
        self.assertEqual("a divulgação obrigatória do contrato no PNCP constitui medida de transparência importante.", q.alternativas[0][1])

    def test_numero_que_nao_aparece_vira_questao_sem_texto_e_a_numeracao_segue(self):
        linhas = [L("1"), L("Um."), *alternativas(), L("3"), L("Três."), *alternativas()]

        seg = pq.segmentar(linhas)

        self.assertEqual([1, 2, 3], [q.numero for q in seg.questoes])
        self.assertEqual("SEM_TEXTO", seg.questoes[1].motivo, "o gabarito precisa de todos os números (D-82)")
        self.assertIsNone(seg.questoes[0].motivo)
        self.assertEqual("Três.", seg.questoes[2].enunciado)
        self.assertTrue(any("2" in a for a in seg.avisos))

    def test_total_do_gabarito_estende_a_numeracao_ate_o_fim(self):
        linhas = [L("1"), L("Um."), *alternativas(), L("2"), L("Dois."), *alternativas()]

        seg = pq.segmentar(linhas, total_esperado=4)

        self.assertEqual([1, 2, 3, 4], [q.numero for q in seg.questoes])
        self.assertEqual(["SEM_TEXTO", "SEM_TEXTO"], [q.motivo for q in seg.questoes[2:]])

    def test_alternativas_incompletas_saem_do_denominador(self):
        linhas = [L("1"), L("Um."), *alternativas("ABC"), L("2"), L("Dois."), *alternativas()]

        # Com só A, B, C a questão 1 não passa na validação de alternativas.
        seg = pq.segmentar(linhas)

        self.assertEqual("SEM_TEXTO", seg.questoes[0].motivo)
        self.assertIsNone(seg.questoes[1].motivo)

    def test_sem_nenhuma_questao_lanca_com_o_motivo(self):
        with self.assertRaises(ValueError) as e:
            pq.segmentar([L("Isto não é uma prova."), L("Só texto corrido sem questões.")])

        self.assertIn("nenhuma questão", str(e.exception))


class OcrTest(unittest.TestCase):
    """O que o OCR da FCC e do IDECAN trazem: ponto depois do número, 'A)' ou '(A)', rodapé e
    código de barras no meio, e algarismos romanos lidos como '1.', '11.', 'TI.'."""

    def prova_fcc(self, n_imagens=4, por_imagem=2):
        linhas, n = [], 1
        for img in range(1, n_imagens + 1):
            linhas.append(L("Caderno de Prova 'E05', Tipo 004", 1, 88.0, img))
            linhas.append(L("IIIIIIIIIIIIIIIIIIIIIIIII", 1, 12.0, img))  # código de barras: ruído de baixa confiança
            for _ in range(por_imagem):
                linhas.append(L(f"{n}. {enun(n)}", 1, 93.0, img))
                linhas += alternativas(pagina=1, conf=93.0, imagem=img)
                n += 1
            linhas.append(L(f"{img + 5} TJUCE-An.Jud.-Infraestrutura-Tec.Informação-E05", 1, 90.0, img))  # rodapé com número
        return linhas

    def test_ponto_apos_o_numero_rodape_com_numero_e_codigo_de_barras_nao_atrapalham(self):
        seg = pq.segmentar(self.prova_fcc())

        self.assertEqual(list(range(1, 9)), [q.numero for q in seg.questoes])
        self.assertTrue(all(q.motivo is None for q in seg.questoes), [q.motivo for q in seg.questoes])
        self.assertTrue(all(q.lida_por_ocr for q in seg.questoes))
        for q in seg.questoes:
            self.assertNotIn("TJUCE", q.alternativas[-1][1], "o rodapé repetido sai antes de grudar na alternativa E")
            self.assertNotIn("IIII", q.alternativas[-1][1], "o código de barras (baixa confiança) é ruído")

    def test_pagina_origem_e_a_imagem_onde_a_questao_comeca(self):
        seg = pq.segmentar(self.prova_fcc())

        self.assertEqual([1, 1, 2, 2, 3, 3, 4, 4], [q.pagina_origem for q in seg.questoes],
                         "o usuário confere o OCR olhando a imagem de onde a questão saiu (D-85)")

    def test_questao_cortada_na_emenda_das_imagens_se_junta(self):
        # O enunciado e as alternativas da questão 2 ficam metade numa imagem, metade na outra.
        linhas = [L("1. Primeira questão.", 1, 93.0, 1), *alternativas(conf=93.0, imagem=1),
                  L("2. Segunda questão, que começa no fim de uma imagem", 1, 93.0, 1),
                  L("e continua no começo da seguinte, sem perder nada.", 1, 93.0, 2),
                  *alternativas(conf=93.0, imagem=2), L("3. Terceira.", 1, 93.0, 2), *alternativas(conf=93.0, imagem=2)]

        seg = pq.segmentar(linhas)

        self.assertEqual(3, len(seg.questoes))
        self.assertEqual("Segunda questão, que começa no fim de uma imagem e continua no começo da seguinte, sem perder nada.",
                         seg.questoes[1].enunciado)
        self.assertEqual(1, seg.questoes[1].pagina_origem, "a imagem é a de onde a questão COMEÇA")

    def test_d85_algarismos_romanos_lidos_como_numeros_deixam_a_questao_duvidosa(self):
        linhas = [L("1. Em um Tribunal, três situações ocorreram:", 1, 92.0),
                  L("1. instabilidades recorrentes no sistema processual exigiram análise;", 1, 91.0),
                  L("11. o aumento do número de processos eletrônicos exigiu monitoramento;", 1, 90.0),
                  L("TI. a administração de TI implementou rotinas periódicas de análise.", 1, 90.0),
                  *alternativas(conf=92.0)]

        q = pq.segmentar(linhas).questoes[0]

        self.assertEqual("OCR_DUVIDOSO", q.motivo,
                         "a resposta depende de qual item é qual, e o OCR leu I, II, III como 1, 11, TI (D-85)")

    def test_romanos_lidos_certo_nao_sao_duvida(self):
        linhas = [L("1. Em um Tribunal, três situações ocorreram:", 1, 92.0),
                  L("I. instabilidades recorrentes no sistema processual exigiram análise;", 1, 91.0),
                  L("II. o aumento do número de processos eletrônicos exigiu monitoramento;", 1, 90.0),
                  L("III. a administração de TI implementou rotinas periódicas.", 1, 90.0),
                  *alternativas(conf=92.0)]

        self.assertIsNone(pq.segmentar(linhas).questoes[0].motivo)

    def test_d85_codigo_lido_com_baixa_confianca_deixa_a_questao_duvidosa(self):
        linhas = [L("1. Para otimizar as conexões, a DBA decidiu adotar a seguinte abordagem:", 1, 94.0),
                  L("(A) Definir max connections = Ono postgresal.conf para eliminar restrições.", 1, 52.0),
                  L("(B) Ajustar Listen adares es = *** no PostgreSQL, ampliando as conexões.", 1, 48.0),
                  L("(C) Alterar a configuração por meio da instrução ALTER srs SET.", 1, 55.0),
                  L("(D) Configurar um pool de conexões com PgBouncer no arquivo.", 1, 90.0),
                  L("(E) Modificar o arquivo po hba . cont para permitir conexões.", 1, 58.0)]

        self.assertEqual("OCR_DUVIDOSO", pq.segmentar(linhas).questoes[0].motivo)

    def test_questao_de_ocr_com_alternativas_incompletas_e_duvidosa_nao_ilegivel(self):
        linhas = [L("1. Enunciado.", 1, 93.0), *alternativas("ABC", conf=93.0), L("2. Dois.", 1, 93.0), *alternativas(conf=93.0)]

        seg = pq.segmentar(linhas)

        self.assertEqual("OCR_DUVIDOSO", seg.questoes[0].motivo)

    def test_idecan_A_parentese_e_ponto_depois_do_numero(self):
        linhas = []
        for n in range(1, 13):
            linhas.append(L(f"{n}. Assinale a alternativa correta da questão {n}.", 1, 91.0))
            linhas += [L(f"{l}) opção {l.lower()} da questão {n} com texto.", 1, 91.0) for l in "ABCDE"]

        seg = pq.segmentar(linhas)

        self.assertEqual(12, len(seg.questoes))
        self.assertTrue(all(q.motivo is None for q in seg.questoes))
        self.assertEqual("MULTIPLA_ESCOLHA", seg.formato)


class CebraspeTest(unittest.TestCase):
    """Itens certo/errado: sem alternativas, ligados a um texto-base citado pelo código."""

    def prova(self):
        return [
            L("CEBRASPE – UNEAL – Edital: 2026", 1),
            L("Texto CB1A1", 1),
            L("Entre as tecnologias criadas para imitar a cognição humana, a IA se destaca.", 1),
            L("Internet: <https://exemplo.org> (com adaptações).", 1),
            L("Julgue os itens seguintes, acerca das ideias veiculadas no", 1),
            L("texto CB1A1.", 1),
            L("1", 1), L("O rápido desenvolvimento da IA provocou aumento dos riscos.", 1),
            L("2", 1), L("No texto, é sugerido que a IA ainda não foi integrada.", 1),
            L("Julgue os itens a seguir, relativos ao vocabulário do texto CB1A1.", 1),
            L("3", 1), L("A palavra assegurada tem o sentido de garantida.", 1),
            L("4 No trecho citado, a vírgula é facultativa.", 1),
            L("Acerca de proteção de dados, julgue os itens que se seguem.", 2),
            L("5 O tratamento de dados pessoais pode ocorrer sem consentimento.", 2),
        ]

    def test_itens_com_o_numero_sozinho_ou_junto_do_texto(self):
        seg = pq.segmentar(self.prova())

        self.assertEqual("CERTO_ERRADO", seg.formato)
        self.assertEqual([1, 2, 3, 4, 5], [q.numero for q in seg.questoes])
        self.assertTrue(all(not q.alternativas and q.motivo is None for q in seg.questoes))
        self.assertEqual("O rápido desenvolvimento da IA provocou aumento dos riscos.", seg.questoes[0].enunciado)
        self.assertEqual("No trecho citado, a vírgula é facultativa.", seg.questoes[3].enunciado)

    def test_o_comando_julgue_nao_entra_no_item_e_vira_o_texto_base_dos_seguintes(self):
        seg = pq.segmentar(self.prova())

        self.assertEqual("No texto, é sugerido que a IA ainda não foi integrada.", seg.questoes[1].enunciado,
                         "o 'Julgue os itens a seguir...' que vem depois do item 2 não é do item 2")
        self.assertIn("Julgue os itens seguintes", seg.questoes[0].texto_base)
        self.assertIn("Julgue os itens a seguir", seg.questoes[2].texto_base)
        self.assertIn("Acerca de proteção de dados", seg.questoes[4].texto_base)

    def test_o_texto_citado_pelo_codigo_vai_junto_com_o_comando(self):
        seg = pq.segmentar(self.prova())

        for q in seg.questoes[:4]:
            self.assertIn("Texto CB1A1", q.texto_base)
            self.assertIn("imitar a cognição humana", q.texto_base, "o item 'infere-se do texto' precisa do texto")
        self.assertNotIn("imitar a cognição", seg.questoes[4].texto_base, "esse bloco não cita o texto CB1A1")


class CapaTest(unittest.TestCase):
    def test_banca_ano_tipo_e_cargo(self):
        capa = "CEBRASPE – UNEAL – Edital: 2026\nCARGO: 6 – ANALISTA DE SISTEMAS\nPROVA TIPO 1"

        meta = pq.metadados_da_capa(capa)

        self.assertEqual("CEBRASPE", meta["banca"])
        self.assertEqual(2026, meta["ano"])
        self.assertEqual("1", meta["tipo"])
        self.assertEqual("6 – ANALISTA DE SISTEMAS", meta["cargoProva"])

    def test_tipo_da_fcc_perde_os_zeros_e_o_da_idecan_e_letra(self):
        self.assertEqual("4", pq.metadados_da_capa("Caderno de Prova 'E05', Tipo 004")["tipo"])
        self.assertEqual("A", pq.metadados_da_capa("COD 9006 - TÉCNICO EM INFRAESTRUTURA – TIPO A")["tipo"])

    def test_o_ano_so_vem_da_capa_curta_mas_a_banca_vem_da_janela_ampla(self):
        meta = pq.metadados_da_capa("NÍVEL SUPERIOR – TARDE\nTIPO 1", capa_ampla="...muito depois... FGV CONHECIMENTO ... Lei de 2019 ...")

        self.assertEqual("FGV", meta["banca"])
        self.assertIsNone(meta["ano"], "uma data de lei pelo texto afora daria o ano errado")

    def test_cespe_e_chamada_de_cebraspe(self):
        self.assertEqual("CEBRASPE", pq.metadados_da_capa("CESPE/UnB - 2019")["banca"])

    def test_capa_sem_nada_nao_inventa(self):
        self.assertEqual({"banca": None, "ano": None, "tipo": None, "cargoProva": None}, pq.metadados_da_capa("texto qualquer"))


@unittest.skipUnless(os.environ.get("PROVAS_AMOSTRA_DIR"), "defina PROVAS_AMOSTRA_DIR para rodar contra as provas reais")
class AmostraRealTest(unittest.TestCase):
    """Contra as provas de verdade (o usuário as guarda; elas não vão para o repositório).
    PROVAS_AMOSTRA_DIR=<pasta> python -m unittest integracao.test_prova_questoes"""

    class SemOcr:
        def disponivel(self):
            return False

    def segmentar(self, nome):
        import tempfile
        with tempfile.TemporaryDirectory() as pasta:
            linhas = pp.ler_prova(Path(os.environ["PROVAS_AMOSTRA_DIR"]) / nome, pasta, self.SemOcr()).linhas
        return pq.segmentar(linhas)

    def test_fgv_dataprev_70_questoes(self):
        seg = self.segmentar("fgv-2026-dataprev-analista-de-tecnologia-da-informacao-desenvolvimento-de-software-prova.pdf")

        self.assertEqual(70, len(seg.questoes))
        self.assertTrue(all(q.motivo is None and len(q.alternativas) == 5 for q in seg.questoes))
        self.assertEqual("FGV", pq.metadados_da_capa(seg.capa, seg.capa_ampla)["banca"])

    def test_fgv_mpes_60_questoes(self):
        seg = self.segmentar("fgv-2026-mpe-es-agente-especializado-analista-de-sistemas-prova.pdf")

        self.assertEqual(60, len(seg.questoes))
        self.assertTrue(all(q.motivo is None and len(q.alternativas) == 5 for q in seg.questoes))

    def test_cebraspe_120_itens_certo_errado_com_o_texto_base(self):
        seg = self.segmentar("cespe-cebraspe-2026-uneal-analista-administrativo-area-analise-de-sistemas-prova.pdf")

        self.assertEqual("CERTO_ERRADO", seg.formato)
        self.assertEqual(120, len(seg.questoes))
        self.assertIn("Texto CB1A1", seg.questoes[0].texto_base)


if __name__ == "__main__":
    unittest.main()
