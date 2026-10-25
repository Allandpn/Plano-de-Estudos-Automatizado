#!/usr/bin/env python3
"""Testes do ciclo do material por casamento em integracao/edital_worker.py (Sprint 26 do SGE), com SGE falso, etapas falsas e
fatiador falso: as entradas saem do que a PESSOA conferiu, o SGE nunca recebe segmento duas vezes e cada situação chega certa."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edital_worker as ew  # noqa: E402
import preparar_edital as pe  # noqa: E402
from ia_comum import IaIndisponivel  # noqa: E402


def pendente():
    return {"analiseId": 7, "slug": "mppr-2024", "cargo": "Analista TI", "concursoNome": "MPPR", "assuntos": [
        {"chave": "aaaa000000000001", "chaveExterna": "11111111-1111-1111-1111-111111111111", "disciplina": "Banco de Dados",
         "texto": "SQL: window function, álgebra relacional", "temSegmentos": False, "partes": [
             {"texto": "window function", "contexto": None, "herdado": "SQL", "natureza": "EXATO", "nos": [121]},
             {"texto": "álgebra relacional", "contexto": None, "herdado": None, "natureza": "MAIS_AMPLO", "nos": [12, 99999]}]},
        {"chave": "aaaa000000000002", "chaveExterna": "22222222-2222-2222-2222-222222222222", "disciplina": "Banco de Dados",
         "texto": "Arquitetura de BD", "temSegmentos": True, "partes": [
             {"texto": "Arquitetura de BD", "contexto": None, "herdado": None, "natureza": None, "nos": []}]},
        {"chave": "aaaa000000000003", "chaveExterna": "33333333-3333-3333-3333-333333333333", "disciplina": "Redes",
         "texto": "Protocolos", "temSegmentos": False, "partes": [
             {"texto": "Protocolos", "contexto": "Camada", "herdado": None, "natureza": "PARCIAL", "nos": [5]}]},
        {"chave": "aaaa000000000004", "chaveExterna": "44444444-4444-4444-4444-444444444444", "disciplina": "Redes",
         "texto": "Cabeamento", "temSegmentos": False, "partes": [
             {"texto": "Cabeamento", "contexto": None, "herdado": None, "natureza": "EXATO", "nos": [6]}]}]}


class SgeFalso:
    def __init__(self, lotes=None):
        self.lotes = [pendente()] if lotes is None else lotes
        self.importados, self.lacunas, self.entregas = [], [], []

    def edital_material_pendentes(self):
        return self.lotes

    def importar_segmentos(self, csv):
        self.importados.append(csv)

    def registrar_lacuna(self, chave, motivo):
        self.lacunas.append((chave, motivo))

    def edital_material_entregar(self, analise_id, assuntos):
        self.entregas.append((analise_id, assuntos))


class EntradasTest(unittest.TestCase):
    def test_entradas_saem_do_que_a_pessoa_conferiu_e_a_chave_vem_pronta(self):
        disciplinas, nos = ew.entradas_do_material(pendente(), nos_validos={121, 12, 5, 6})
        self.assertEqual(["Banco de Dados", "Redes"], [d["nome"] for d in disciplinas])
        self.assertEqual(["aaaa000000000001", "aaaa000000000002"], [a["chave"] for a in disciplinas[0]["assuntos"]])
        self.assertEqual(5, len(nos["itens"]))
        self.assertEqual([121], nos["itens"][0]["ia"])
        self.assertEqual("SQL window function", nos["itens"][0]["nome"])
        self.assertEqual([12], nos["itens"][1]["ia"], "nó que não existe na árvore do planejamento é descartado")
        self.assertEqual("mais_amplo", nos["itens"][1]["natureza"])
        self.assertIsNone(nos["itens"][2]["natureza"])
        self.assertEqual(["Camada"], nos["itens"][3]["termos"])
        self.assertEqual({"disciplina": "Redes", "assunto": 0, "parte": 0, "item": 3}, nos["partes"][3])

    def test_parte_repetida_vira_uma_ligacao_so(self):
        p = pendente()
        p["assuntos"][3]["partes"][0].update(texto="Protocolos", contexto="Camada")
        _, nos = ew.entradas_do_material(p)
        self.assertEqual(4, len(nos["itens"]))
        self.assertEqual(nos["partes"][3]["item"], nos["partes"][4]["item"])


class MaterialDoEditalTest(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        base = Path(self._t.name)
        self.trabalho, self.material = base / "trabalho", base / "material"
        self.catalogo, self.fichas = base / "catalogo.db", base / "fichas-nos.jsonl"
        self.catalogo.write_bytes(b"")
        self.fichas.write_text("", encoding="utf-8")
        self.chamadas, self.fatiados = [], []

        def etapa(nome, escrever):
            def f(ctx):
                self.chamadas.append(nome)
                escrever(ctx)
                return "feita"
            return f

        def casar(ctx): ctx.gravar("material.json", {"itens": [], "partes": []})  # noqa: E704
        def confirmar(ctx): ctx.gravar("confirmado.json", [])  # noqa: E704

        def manifestos(ctx):
            ctx.gravar("manifestos/aaaa000000000001.json", {"lacunas": [{"subitem": "álgebra relacional", "motivo": "nenhum tema ensina"}]})
            ctx.gravar("manifestos/aaaa000000000003.json", {"lacunas": []})
            ctx.gravar("assuntos.json", [
                {"chave": "aaaa000000000001", "situacao": "parcial", "minutos": 150, "fontes": 3, "erros": []},
                {"chave": "aaaa000000000002", "situacao": "completo", "minutos": 60, "fontes": 1, "erros": []},
                {"chave": "aaaa000000000003", "situacao": "completo", "minutos": 30, "fontes": 1, "erros": []},
                {"chave": "aaaa000000000004", "situacao": "sem material", "minutos": 0, "fontes": 0, "erros": []}])
            ctx.arquivo("relatorio.md").write_text("x", encoding="utf-8")

        def consulta(ctx):
            ctx.gravar("consulta/consulta.json", [{"chave": "aaaa000000000001", "arquivo": "aaaa000000000001.pdf", "paginas": 12, "avisos": []}])
            (ctx.pasta / "consulta" / "aaaa000000000001.pdf").write_bytes(b"%PDF-1.4 consulta")

        self.funcoes = {"casar": etapa("casar", casar), "confirmar": etapa("confirmar", confirmar), "manifestos": etapa("manifestos", manifestos),
                        "segunda": etapa("segunda", lambda ctx: ctx.gravar("segunda.json", [])), "consulta": etapa("consulta", consulta)}

        def fatiar(manifesto, destino):
            self.fatiados.append(Path(manifesto).stem)
            return [{"chave_externa_segmento": "seg-1", "ordem": 1, "arquivo": "blocos/x/segmento-01.pdf", "pagina_inicial": 3,
                     "pagina_final": 30, "tempo_estimado_min": 60}]
        self.fatiar = fatiar

    def tearDown(self):
        self._t.cleanup()

    def worker(self, sge, **kw):
        return ew.MaterialDoEdital(sge, self.trabalho, self.material, kw.get("catalogo", self.catalogo), self.fichas, "/acervo", "/indice.db",
                                   funcoes=self.funcoes, fatiador=self.fatiar, log_etapa=lambda *_: None)

    def test_ciclo_importa_so_o_que_nao_tem_segmento_e_entrega_cada_situacao(self):
        sge = SgeFalso()
        self.assertEqual(4, self.worker(sge).ciclo())
        self.assertEqual(["casar", "confirmar", "manifestos", "segunda", "consulta"], self.chamadas)
        # o 1 e o 3 têm material e nenhum segmento: importam; o 2 já tem segmento (o SGE nunca apaga): não importa; o 4 não tem fonte
        self.assertEqual(["aaaa000000000001", "aaaa000000000003"], self.fatiados)
        self.assertEqual(2, len(sge.importados))
        self.assertIn("11111111-1111-1111-1111-111111111111", sge.importados[0], "o CSV leva a chave externa do assunto no SGE")
        self.assertEqual([("44444444-4444-4444-4444-444444444444", "nenhum tema do acervo ensina as partes deste assunto (casamento por partes)")], sge.lacunas)
        analise, assuntos = sge.entregas[0]
        self.assertEqual(7, analise)
        por = {a["chave"]: a for a in assuntos}
        self.assertEqual("PARCIAL", por["aaaa000000000001"]["situacao"])
        self.assertEqual([{"parte": "álgebra relacional", "motivo": "nenhum tema ensina"}], por["aaaa000000000001"]["lacunas"])
        self.assertEqual({"arquivo": "consulta/aaaa000000000001.pdf", "paginas": 12}, por["aaaa000000000001"]["consulta"])
        self.assertTrue((self.material / "consulta" / "aaaa000000000001.pdf").is_file(), "a consulta fica onde o SGE serve (/material/)")
        self.assertEqual("SEM_MATERIAL", por["aaaa000000000004"]["situacao"])
        self.assertEqual([{"parte": "Cabeamento", "motivo": ew.MOTIVO_SEM_TEMA}], por["aaaa000000000004"]["lacunas"])
        self.assertNotIn("consulta", por["aaaa000000000003"])

    def test_sem_lote_ou_sem_catalogo_nada_acontece(self):
        self.assertEqual(0, self.worker(SgeFalso(lotes=[])).ciclo())
        self.assertEqual(0, self.worker(SgeFalso(), catalogo=self.trabalho / "nao-existe.db").ciclo())
        self.assertEqual([], self.chamadas)

    def test_ia_indisponivel_espera_o_proximo_ciclo_e_nao_entrega(self):
        def cai(ctx):
            raise IaIndisponivel("limite da janela")
        self.funcoes["confirmar"] = cai
        sge = SgeFalso()
        self.assertEqual(0, self.worker(sge).ciclo())
        self.assertEqual([], sge.entregas)
        self.assertEqual([], sge.importados)

    def test_lote_que_mudou_descarta_o_trabalho_antigo(self):
        sge = SgeFalso()
        w = self.worker(sge)
        w.ciclo()
        self.chamadas.clear()
        w.ciclo()  # mesmo lote: tudo já feito, só entrega de novo (idempotente no SGE)
        self.assertEqual([], self.chamadas)
        sge.lotes = [dict(pendente(), assuntos=pendente()["assuntos"][:3])]
        w.ciclo()
        self.assertEqual(["casar", "confirmar", "manifestos", "segunda", "consulta"], self.chamadas, "lote novo, trabalho novo")


if __name__ == "__main__":
    unittest.main()
