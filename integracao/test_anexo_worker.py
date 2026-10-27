#!/usr/bin/env python3
"""Testes do ciclo do PDF anexado a uma lacuna (integracao/anexo_worker.py, D-97 do SGE): o manifesto sai certo, os segmentos entram
DEPOIS dos que o assunto já tem, o resultado volta ao SGE e a falha de um anexo não para os outros. Um teste usa o fatiador de verdade."""
import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dias"))
import anexo_worker as aw  # noqa: E402
from sge_api import ErroSge  # noqa: E402


def pendente(id=5, arquivo="anexos/lei.pdf", paginas=40, proxima=3):
    return {"id": id, "chaveExterna": "11111111-1111-1111-1111-111111111111", "assunto": "1. Lei Orgânica do MPPR",
            "parte": "Lei Orgânica e Estatuto do MPPR", "arquivo": arquivo, "paginas": paginas, "nome": "lei-organica.pdf", "proximaOrdem": proxima}


class SgeFalso:
    def __init__(self, pendentes):
        self.pendentes = pendentes
        self.importados, self.prontos, self.falhas = [], [], []

    def anexos_pendentes(self):
        return self.pendentes

    def importar_segmentos(self, csv_texto):
        self.importados.append(csv_texto)

    def anexo_pronto(self, anexo_id, segmentos, minutos):
        self.prontos.append((anexo_id, segmentos, minutos))

    def anexo_falha(self, anexo_id, erro):
        self.falhas.append((anexo_id, erro))


def segmentos_falsos(manifesto, destino):
    """Devolve o que montar_bloco devolveria: dois segmentos com ordem 1 e 2 (o ciclo renumera)."""
    return [{"ordem": 1, "arquivo": "blocos/x/segmento-01.pdf", "pagina_inicial": 1, "pagina_final": 20, "tempo_estimado_min": 60,
             "chave_externa_segmento": "aaaaaaaa-0000-0000-0000-000000000001"},
            {"ordem": 2, "arquivo": "blocos/x/segmento-02.pdf", "pagina_inicial": 21, "pagina_final": 40, "tempo_estimado_min": 55,
             "chave_externa_segmento": "aaaaaaaa-0000-0000-0000-000000000002"}]


class CicloDoAnexoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.editais = Path(self.tmp.name) / "editais"
        (self.editais / "anexos").mkdir(parents=True)
        (self.editais / "anexos" / "lei.pdf").write_bytes(b"%PDF-falso")
        self.material = Path(self.tmp.name) / "material"
        self.material.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_manifesto_de_uma_fonte_com_todas_as_paginas_e_destino_proprio(self):
        m = aw.manifesto_do_anexo(pendente(), Path("/x/lei.pdf"))
        self.assertEqual(m["subitens"], ["Lei Orgânica e Estatuto do MPPR"])
        self.assertEqual(m["lacunas"], [])
        self.assertEqual(m["fontes"][0]["paginas"], "1-40")
        self.assertEqual(m["fontes"][0]["cobre"], ["Lei Orgânica e Estatuto do MPPR"])
        self.assertEqual(m["assunto_uuid"], "anexo-5")
        self.assertTrue(m["titulo"].endswith("anexo 5"), "o id no título dá um destino só deste anexo")

    def test_segmentos_entram_depois_dos_que_o_assunto_ja_tem_e_o_sge_recebe_o_resultado(self):
        sge = SgeFalso([pendente(proxima=3)])
        self.assertEqual(aw.AnexosDeLacuna(sge, self.editais, self.material, fatiador=segmentos_falsos).ciclo(), 1)
        linhas = list(csv.DictReader(io.StringIO(sge.importados[0])))
        self.assertEqual([l["ordem"] for l in linhas], ["3", "4"], "a numeração continua a do assunto")
        self.assertTrue(all(l["chaveExternaAssunto"] == "11111111-1111-1111-1111-111111111111" for l in linhas))
        self.assertEqual(linhas[0]["arquivo"], "/material/blocos/x/segmento-01.pdf")
        self.assertEqual(sge.prontos, [(5, 2, 115)])
        self.assertEqual(sge.falhas, [])

    def test_pdf_ausente_vira_falha_com_o_motivo_e_nao_importa_nada(self):
        sge = SgeFalso([pendente(arquivo="anexos/sumiu.pdf")])
        self.assertEqual(aw.AnexosDeLacuna(sge, self.editais, self.material, fatiador=segmentos_falsos).ciclo(), 0)
        self.assertEqual(sge.importados, [])
        self.assertEqual(sge.prontos, [])
        self.assertEqual(len(sge.falhas), 1)
        self.assertIn("não está no volume", sge.falhas[0][1])

    def test_caminho_fora_do_volume_nao_e_aceito(self):
        sge = SgeFalso([pendente(arquivo="../../etc/passwd")])
        aw.AnexosDeLacuna(sge, self.editais, self.material, fatiador=segmentos_falsos).ciclo()
        self.assertEqual(sge.importados, [])
        self.assertEqual(len(sge.falhas), 1)

    def test_falha_do_fatiador_vira_falha_e_os_outros_anexos_seguem(self):
        (self.editais / "anexos" / "outro.pdf").write_bytes(b"%PDF-falso")
        sge = SgeFalso([pendente(id=5), pendente(id=6, arquivo="anexos/outro.pdf")])

        def fatiador(manifesto, destino):
            if json.loads(Path(manifesto).read_text(encoding="utf-8"))["assunto_uuid"] == "anexo-5":
                raise ValueError("página fora do PDF")
            return segmentos_falsos(manifesto, destino)

        self.assertEqual(aw.AnexosDeLacuna(sge, self.editais, self.material, fatiador=fatiador).ciclo(), 1)
        self.assertEqual(sge.falhas, [(5, "página fora do PDF")])
        self.assertEqual([p[0] for p in sge.prontos], [6])

    def test_sge_fora_do_ar_nao_vira_falha_do_pdf(self):
        class SgeCaido(SgeFalso):
            def importar_segmentos(self, csv_texto):
                raise ErroSge(503, "indisponivel", "SGE fora do ar")

        sge = SgeCaido([pendente()])
        with self.assertRaises(ErroSge):
            aw.AnexosDeLacuna(sge, self.editais, self.material, fatiador=segmentos_falsos).ciclo()
        self.assertEqual(sge.falhas, [], "o anexo continua pendente e tenta de novo no próximo ciclo")

    def test_sem_pendente_nao_faz_nada(self):
        sge = SgeFalso([])
        self.assertEqual(aw.AnexosDeLacuna(sge, self.editais, self.material, fatiador=segmentos_falsos).ciclo(), 0)
        self.assertEqual((sge.importados, sge.prontos, sge.falhas), ([], [], []))


class FatiadorDeVerdadeTest(unittest.TestCase):
    """O mesmo ciclo com `montar_bloco.py` de verdade e um PDF real: o corte sai em segmentos de ~60 min e os PDFs existem."""

    def test_pdf_real_vira_segmentos_de_uma_hora(self):
        from pypdf import PdfWriter
        with tempfile.TemporaryDirectory() as t:
            editais, material = Path(t) / "editais", Path(t) / "material"
            (editais / "anexos").mkdir(parents=True)
            material.mkdir()
            escritor = PdfWriter()
            for _ in range(70):
                escritor.add_blank_page(width=300, height=400)
            with open(editais / "anexos" / "lei.pdf", "wb") as f:
                escritor.write(f)
            sge = SgeFalso([pendente(paginas=70, proxima=1)])
            self.assertEqual(aw.AnexosDeLacuna(sge, editais, material).ciclo(), 1, sge.falhas)
            (anexo_id, n, minutos), = sge.prontos
            self.assertGreaterEqual(n, 3, "70 páginas a 3 min são 210 min: pelo menos 3 segmentos de ~60")
            self.assertEqual(minutos, 210)
            linhas = list(csv.DictReader(io.StringIO(sge.importados[0])))
            self.assertEqual([int(l["ordem"]) for l in linhas], list(range(1, n + 1)))
            for l in linhas:
                self.assertTrue((material / l["arquivo"].removeprefix("/material/")).is_file())


if __name__ == "__main__":
    unittest.main()
