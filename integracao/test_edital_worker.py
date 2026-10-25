#!/usr/bin/env python3
"""Testes de integracao/edital_worker.py: o ciclo do edital (Sprint 25 do SGE, ADR-047) com SGE falso e etapas falsas.

Cada teste nomeia o tipo de problema que protege: IA indisponível espera sem reportar, edital ilegível falha com a etapa
certa do contrato, o SGE que já seguiu em frente não vira falha, e reiniciar continua de onde parou."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edital_worker as ew  # noqa: E402
import preparar_edital as pe  # noqa: E402
from ia_comum import IaIndisponivel  # noqa: E402
from sge_api import ErroSge  # noqa: E402


class SgeFalso:
    def __init__(self, pendentes=None, dados=None, recusa=None):
        self.pendentes = [{"id": 7, "slug": "mppr-2024", "cargo": "Analista TI", "nomeArquivo": "mppr.pdf"}] if pendentes is None else pendentes
        self.dados = dados or {"id": 7, "pdf": "7/edital.pdf", "decisoes": [{"parte": "Kanban", "contexto": None, "nos": [3062], "natureza": "mais_amplo"}]}
        self.recusa = recusa
        self.arvores, self.entregas, self.falhas = [], [], []

    def editais_pendentes(self):
        return self.pendentes

    def edital_dados(self, analise_id):
        return self.dados

    def arvore_carregar(self, bytes_do_arquivo):
        self.arvores.append(len(bytes_do_arquivo))

    def edital_entregar(self, analise_id, texto):
        if self.recusa:
            raise self.recusa
        self.entregas.append((analise_id, json.loads(texto)))
        return {"partes": 3}

    def edital_falha(self, analise_id, etapa, mensagem, disciplina=None):
        self.falhas.append((analise_id, etapa, mensagem))


class EditalWorkerTest(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        base = Path(self._t.name)
        self.editais, self.trabalho, self.taxonomia = base / "editais", base / "trabalho", base / "taxonomia"
        (self.editais / "7").mkdir(parents=True)
        (self.editais / "7" / "edital.pdf").write_bytes(b"%PDF-1.4 falso")
        self.taxonomia.mkdir()
        (self.taxonomia / "qconcursos-2026-10-19.json").write_text('{"fonte": "qconcursos", "disciplinas": []}', encoding="utf-8")
        self.chamadas = []

        def falsa(nome, saida):
            def f(ctx):
                self.chamadas.append(nome)
                ctx.gravar(pe.SAIDA_DA_ETAPA[nome], saida)
                return f"feita {nome}"
            return f
        self.funcoes = {"extrair": falsa("extrair", {"linhas": []}), "quebrar": falsa("quebrar", []),
                        "ligar": falsa("ligar", {"itens": [], "partes": []}), "entrega": falsa("entrega", {"contrato": "edital-revisao/1"})}

    def tearDown(self):
        self._t.cleanup()

    def worker(self, sge):
        return ew.WorkerEditais(sge, self.editais, self.trabalho, funcoes=self.funcoes, taxonomia_dir=self.taxonomia,
                                log_etapa=lambda *_: None)

    def test_ciclo_entrega_a_leitura_carrega_a_arvore_uma_vez_e_leva_as_decisoes_da_pessoa(self):
        sge = SgeFalso()
        w = self.worker(sge)
        self.assertEqual(1, w.ciclo())
        self.assertEqual(["extrair", "quebrar", "ligar", "entrega"], self.chamadas)
        self.assertEqual([(7, {"contrato": "edital-revisao/1"})], sge.entregas)
        self.assertEqual(1, len(sge.arvores))
        decisoes = json.loads((self.trabalho / "editais" / "7" / "decisoes-do-sge.json").read_text(encoding="utf-8"))
        self.assertEqual([3062], decisoes["decisoes"][0]["nos"], "as decisões do SGE valem antes da IA")
        self.assertEqual("qconcursos-2026-10-19", decisoes["arvore"])
        w.ciclo()
        self.assertEqual(1, len(sge.arvores), "a árvore só sobe uma vez")

    def test_sem_edital_pendente_nada_acontece(self):
        sge = SgeFalso(pendentes=[])
        self.assertEqual(0, self.worker(sge).ciclo())
        self.assertEqual([], self.chamadas)

    def test_pdf_ausente_falha_na_extracao(self):
        sge = SgeFalso(dados={"id": 7, "pdf": "7/sumiu.pdf", "decisoes": []})
        self.assertEqual(0, self.worker(sge).ciclo())
        self.assertEqual("EXTRACAO", sge.falhas[0][1])
        self.assertEqual([], self.chamadas)

    def test_edital_ilegivel_falha_com_a_etapa_do_contrato(self):
        def sem_programa(ctx):
            raise pe.ErroDeEtapa("o edital não traz o conteúdo programático")
        self.funcoes["extrair"] = sem_programa
        sge = SgeFalso()
        self.worker(sge).ciclo()
        self.assertEqual([(7, "EXTRACAO", "o edital não traz o conteúdo programático")], sge.falhas)

    def test_quebra_sem_organizacao_e_organizacao_o_resto_e_quebra(self):
        def quebra_ruim(ctx):
            raise pe.ErroDeEtapa("a IA não organizou")
        self.funcoes["quebrar"] = quebra_ruim
        sge = SgeFalso()
        self.worker(sge).ciclo()
        self.assertEqual("ORGANIZACAO", sge.falhas[0][1])

        def quebra_depois_de_organizar(ctx):
            ctx.gravar("organizacao.json", [])
            raise pe.ErroDeEtapa("quebra recusada")
        self.funcoes["quebrar"] = quebra_depois_de_organizar
        sge2 = SgeFalso()
        self.worker(sge2).ciclo()
        self.assertEqual("QUEBRA", sge2.falhas[0][1])

    def test_ia_indisponivel_espera_sem_reportar_falha(self):
        def sem_ia(ctx):
            raise IaIndisponivel("a assinatura parou")
        self.funcoes["quebrar"] = sem_ia
        sge = SgeFalso()
        self.assertEqual(0, self.worker(sge).ciclo())
        self.assertEqual([], sge.falhas)
        self.assertEqual([], sge.entregas)

    def test_reiniciar_continua_de_onde_parou(self):
        def cai(ctx):
            raise IaIndisponivel("limite da janela")
        boa = self.funcoes["quebrar"]
        self.funcoes["quebrar"] = cai
        sge = SgeFalso()
        w = self.worker(sge)
        w.ciclo()
        self.assertEqual(["extrair"], self.chamadas)
        self.funcoes["quebrar"] = boa
        w.ciclo()
        self.assertEqual(["extrair", "quebrar", "ligar", "entrega"], self.chamadas, "a extração não se repete")

    def test_falha_inesperada_vira_falha_com_o_tipo_do_erro(self):
        def quebra(ctx):
            raise KeyError("campo")
        self.funcoes["ligar"] = quebra
        sge = SgeFalso()
        self.worker(sge).ciclo()
        self.assertEqual("LIGACAO", sge.falhas[0][1])
        self.assertIn("KeyError", sge.falhas[0][2])

    def test_sge_que_ja_seguiu_em_frente_nao_vira_falha(self):
        sge = SgeFalso(recusa=ErroSge(409, "ETAPA_INVALIDA", "a análise já está em conferência"))
        self.assertEqual(0, self.worker(sge).ciclo())
        self.assertEqual([], sge.falhas)

    def test_sge_que_recusa_o_conteudo_vira_falha_de_ligacao(self):
        sge = SgeFalso(recusa=ErroSge(422, "NO_INEXISTENTE", "O nó 9 não existe na árvore da execução."))
        self.worker(sge).ciclo()
        self.assertEqual("LIGACAO", sge.falhas[0][1])
        self.assertIn("NO_INEXISTENTE", sge.falhas[0][2])

    def test_sge_fora_do_ar_sobe_para_o_laco_principal(self):
        sge = SgeFalso(recusa=ErroSge(None, "SEM_CONEXAO", "recusou"))
        with self.assertRaises(ErroSge):
            self.worker(sge).ciclo()


if __name__ == "__main__":
    unittest.main()
