#!/usr/bin/env python3
"""Testes de integracao/preparar_edital.py: a ordem, o pular o que já está feito, --ate e --refazer, com etapas falsas."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import preparar_edital as pe  # noqa: E402


class PrepararEditalTest(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.ctx = pe.Contexto("x.pdf", "s", "c", self._t.name, log=lambda *_: None)
        self.chamadas = []

        def falsa(nome):
            def f(ctx):
                self.chamadas.append(nome)
                ctx.gravar(pe.SAIDA_DA_ETAPA[nome], {"nome": nome})
                return f"feita {nome}"
            return f
        self.funcoes = {n: falsa(n) for n in pe.ETAPAS}

    def tearDown(self):
        self._t.cleanup()

    def roda(self, **kw):
        self.chamadas.clear()
        return pe.executar(self.ctx, funcoes=self.funcoes, **kw)

    def test_roda_todas_na_ordem_e_depois_pula_tudo(self):
        self.roda()
        self.assertEqual(pe.ETAPAS, self.chamadas)
        r = self.roda()
        self.assertEqual([], self.chamadas)
        self.assertEqual({"já feita"}, set(r.values()))

    def test_ate_para_depois_da_etapa(self):
        self.roda(ate="ligar")
        self.assertEqual(["extrair", "quebrar", "ligar"], self.chamadas)
        self.roda()
        self.assertEqual(["casar", "confirmar", "manifestos", "segunda", "consulta", "entrega"], self.chamadas, "retoma de onde parou")

    def test_refazer_refaz_a_etapa_e_todas_as_seguintes(self):
        self.roda()
        self.roda(refazer="casar")
        self.assertEqual(["casar", "confirmar", "manifestos", "segunda", "consulta", "entrega"], self.chamadas)

    def test_etapa_desconhecida(self):
        with self.assertRaises(ValueError):
            pe.executar(self.ctx, ate="inexistente", funcoes=self.funcoes)

    def test_decisoes_padrao_le_o_arquivo_da_arvore(self):
        d = pe.decisoes_padrao("qconcursos-2026-10-19")
        self.assertTrue(d and all("parte" in x and "nos" in x for x in d))
        self.assertEqual([], pe.decisoes_padrao("arvore-que-nao-existe"))


if __name__ == "__main__":
    unittest.main()


class DescricaoTest(unittest.TestCase):
    def test_descricao_traz_cargo_e_amostra_dos_assuntos(self):
        d = {"nome": "Conhecimentos específicos", "assuntos": [{"texto": f"Assunto {i}."} for i in range(30)]}
        txt = pe.descricao_da_disciplina("Analista de TI", d, quantos=3)
        self.assertEqual("cargo: Analista de TI; assuntos: Assunto 0; Assunto 1; Assunto 2", txt)

    def test_pedido_de_disciplinas_leva_a_descricao_e_mapa_vazio_pergunta_de_novo(self):
        import json as _json
        import casar_taxonomia as ct
        from test_casar_taxonomia import ARVORE, IaFalsa
        ia = IaFalsa([{"disciplinas": {"Conhecimentos específicos": [3]}}])
        r = ct.mapear_disciplinas(ia, ["Conhecimentos específicos"], ct.Arvore(ARVORE), {"Conhecimentos específicos": "cargo: TI; assuntos: redes"})
        self.assertEqual({"Conhecimentos específicos": [3]}, r)
        self.assertIn("- Conhecimentos específicos  [cargo: TI; assuntos: redes]", ia.pedidos[0])
