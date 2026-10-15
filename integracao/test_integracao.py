#!/usr/bin/env python3
"""
Testes do caminho canonizar → orçamento → publicar → exportar.

Rodar (da raiz do repositório):
    python -m unittest discover -s integracao -p "test_*.py"

O que mais importa aqui é o contrato com o SGE-Concursos: as colunas dos CSVs são as que
o SGE define (`especificacao/02_JORNADAS.md` J-1 de lá, espelhado em
docs/arquitetura-integracao-planejamento-sge.md §8.1). Se este teste quebrar porque o
contrato mudou, a mudança começa no documento, não aqui.
"""

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import calcular_orcamento as orc  # noqa: E402
import canonizar_assuntos as can  # noqa: E402
import exportar_sge as exp  # noqa: E402
import publicar_drive as pub  # noqa: E402

EDITAL = "EDITAL-TESTE"

# Contrato do SGE — copiado do documento, de propósito, e não importado do exportador:
# o teste existe pra pegar o exportador divergindo do contrato.
COLUNAS_ASSUNTOS_SGE = ["disciplina", "assunto", "peso", "ordem", "chaveExterna"]
COLUNAS_SEGMENTOS_SGE = ["chaveExternaSegmento", "chaveExternaAssunto", "ordem", "arquivo",
                         "paginaInicial", "paginaFinal", "tempoEstimadoMin"]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.conn = can.conectar_db(str(self.dir / "canonico.db"))

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def adicionar(self, disciplina, assunto, peso="NAO_DETERMINADO", paginas="1-10"):
        uuid_, _ = can.adicionar(self.conn, disciplina, assunto, EDITAL, assunto, peso, paginas, None, None)
        return uuid_

    def orcar(self):
        return orc.calcular(self.conn, EDITAL, dias=30, minutos_dia=120, minutos_pagina=4)

    def ordem_de(self, uuid_):
        return self.conn.execute(
            "SELECT ordem FROM edital_assunto WHERE edital = ? AND assunto_uuid = ?", (EDITAL, uuid_)
        ).fetchone()["ordem"]

    def pedacos(self, uuid_, arquivos):
        can.adicionar_pedacos(self.conn, EDITAL, uuid_, [
            {"ordem": i, "arquivo": a, "pagina_inicial": 1, "pagina_final": 5,
             "tempo_estimado_min": 50, "chave_externa_segmento": f"seg-{uuid_[:8]}-{i}"}
            for i, a in enumerate(arquivos, 1)
        ])


class OrdemTest(Base):
    def test_mesmo_peso_segue_a_ordem_do_mapa_nao_a_alfabetica(self):
        modelagem = self.adicionar("Banco de Dados", "Modelagem conceitual")
        normalizacao = self.adicionar("Banco de Dados", "Entidades e normalização")
        nosql = self.adicionar("Banco de Dados", "Bancos relacionais x NoSQL")

        self.orcar()

        self.assertEqual([1, 2, 3], [self.ordem_de(u) for u in (modelagem, normalizacao, nosql)])

    def test_peso_maior_vem_antes(self):
        baixo = self.adicionar("Português", "Crase", peso="BAIXO")
        alto = self.adicionar("Redes", "TCP/IP", peso="ALTO")

        self.orcar()

        self.assertLess(self.ordem_de(alto), self.ordem_de(baixo))

    def test_readicionar_nao_muda_a_posicao(self):
        primeiro = self.adicionar("Redes", "Camadas OSI")
        segundo = self.adicionar("Redes", "Roteamento")
        self.adicionar("Redes", "Camadas OSI")  # lote reexecutado: idempotente

        self.orcar()

        self.assertLess(self.ordem_de(primeiro), self.ordem_de(segundo))


class CanonicoTest(Base):
    def test_mesmo_nome_e_disciplina_nao_duplica(self):
        a = self.adicionar("Redes", "Roteamento")
        b = self.adicionar("Redes", "Roteamento")

        self.assertEqual(a, b)
        total = self.conn.execute("SELECT count(*) FROM assuntos_canonicos").fetchone()[0]
        self.assertEqual(1, total)

    def test_pedacos_sem_edital_assunto_recusa(self):
        with self.assertRaises(ValueError):
            can.adicionar_pedacos(self.conn, EDITAL, "uuid-inexistente", [])


class ExportacaoTest(Base):
    def exportar(self):
        saida = self.dir / "SGE-Importacao" / "edital-teste"
        exp.exportar(self.conn, EDITAL, saida, "Edital de Teste", "2027-03-01")
        return saida

    def ler_csv(self, caminho):
        with open(caminho, encoding="utf-8", newline="") as f:
            leitor = csv.DictReader(f)
            return leitor.fieldnames, list(leitor)

    def test_assuntos_csv_no_formato_do_sge(self):
        u = self.adicionar("Redes", "Roteamento")
        self.orcar()

        colunas, linhas = self.ler_csv(self.exportar() / "assuntos.csv")

        self.assertEqual(COLUNAS_ASSUNTOS_SGE, colunas)
        self.assertNotIn("id", colunas, "sem id: o SGE reimporta pela chaveExterna")
        self.assertEqual(u, linhas[0]["chaveExterna"])
        self.assertEqual("1", linhas[0]["ordem"])

    def test_peso_nao_determinado_sai_vazio(self):
        self.adicionar("Redes", "Roteamento", peso="NAO_DETERMINADO")
        self.adicionar("Redes", "TCP/IP", peso="ALTO")
        self.orcar()

        _, linhas = self.ler_csv(self.exportar() / "assuntos.csv")

        self.assertEqual({"Roteamento": "", "TCP/IP": "ALTO"}, {l["assunto"]: l["peso"] for l in linhas})

    def test_segmentos_csv_no_formato_do_sge(self):
        u = self.adicionar("Redes", "Roteamento")
        self.orcar()
        self.pedacos(u, ["https://drive.google.com/a", "https://drive.google.com/b"])

        colunas, linhas = self.ler_csv(self.exportar() / "segmentos.csv")

        self.assertEqual(COLUNAS_SEGMENTOS_SGE, colunas)
        self.assertEqual(["1", "2"], [l["ordem"] for l in linhas])
        self.assertTrue(all(l["chaveExternaAssunto"] == u for l in linhas))

    def test_sem_pedacos_nao_gera_segmentos_e_apaga_o_antigo(self):
        u = self.adicionar("Redes", "Roteamento")
        self.orcar()
        self.pedacos(u, ["https://drive.google.com/a"])
        saida = self.exportar()
        self.conn.execute("DELETE FROM material_pedacos")
        self.conn.commit()

        self.exportar()

        self.assertFalse((saida / "segmentos.csv").exists())

    def test_concurso_json(self):
        self.adicionar("Redes", "Roteamento")
        self.orcar()

        dados = json.loads((self.exportar() / "concurso.json").read_text(encoding="utf-8"))

        self.assertEqual({"slug": "edital-teste", "nome": "Edital de Teste", "dataProva": "2027-03-01"}, dados)

    def test_caminho_local_gera_aviso(self):
        u = self.adicionar("Redes", "Roteamento")
        self.orcar()
        self.pedacos(u, ["blocos/roteamento/segmento-01.pdf"])

        _, _, avisos = exp.montar_linhas(self.conn, EDITAL)

        self.assertTrue(any("não é link" in a for a in avisos))


class RcloneFalso:
    def __init__(self, falhar_em=None):
        self.chamadas = []
        self.falhar_em = falhar_em

    def __call__(self, *args):
        self.chamadas.append(args)
        if self.falhar_em and args[-1].endswith(self.falhar_em):
            raise pub.FalhaRclone("simulada")
        if args[0] == "link":
            return f"https://drive.google.com/open?id={args[-1].rsplit('/', 1)[-1]}"
        return ""


class PublicacaoTest(Base):
    def setUp(self):
        super().setUp()
        self.saida = self.dir / "dias"
        self.uuid = self.adicionar("Redes", "Roteamento")
        self.orcar()
        self.arquivos = ["blocos/roteamento/segmento-01.pdf", "blocos/roteamento/segmento-02.pdf"]
        for a in self.arquivos:
            (self.saida / a).parent.mkdir(parents=True, exist_ok=True)
            (self.saida / a).write_bytes(b"%PDF-1.4")
        self.pedacos(self.uuid, self.arquivos)

    def arquivos_no_banco(self):
        return [r["arquivo"] for r in self.conn.execute("SELECT arquivo FROM material_pedacos ORDER BY ordem")]

    def test_sobe_e_grava_o_link(self):
        rclone = RcloneFalso()

        n = pub.publicar(self.conn, EDITAL, self.saida, "gdrive:Material", rclone, saida=lambda *_: None)

        self.assertEqual(2, n)
        self.assertEqual(("copyto", str(self.saida / self.arquivos[0]), "gdrive:Material/blocos/roteamento/segmento-01.pdf"),
                         rclone.chamadas[0])
        self.assertTrue(all(a.startswith("https://") for a in self.arquivos_no_banco()))

    def test_segunda_vez_nao_sobe_de_novo(self):
        pub.publicar(self.conn, EDITAL, self.saida, "gdrive:Material", RcloneFalso(), saida=lambda *_: None)
        rclone = RcloneFalso()

        n = pub.publicar(self.conn, EDITAL, self.saida, "gdrive:Material", rclone, saida=lambda *_: None)

        self.assertEqual(0, n)
        self.assertEqual([], rclone.chamadas)

    def test_falha_no_meio_mantem_o_que_ja_subiu(self):
        rclone = RcloneFalso(falhar_em="segmento-02.pdf")

        with self.assertRaises(pub.FalhaRclone):
            pub.publicar(self.conn, EDITAL, self.saida, "gdrive:Material", rclone, saida=lambda *_: None)

        primeiro, segundo = self.arquivos_no_banco()
        self.assertTrue(primeiro.startswith("https://"))
        self.assertEqual(self.arquivos[1], segundo, "sem link, continua o caminho local")

    def test_pdf_faltando_nao_sobe_nada(self):
        (self.saida / self.arquivos[1]).unlink()
        rclone = RcloneFalso()

        with self.assertRaises(FileNotFoundError):
            pub.publicar(self.conn, EDITAL, self.saida, "gdrive:Material", rclone, saida=lambda *_: None)

        self.assertEqual([], rclone.chamadas)

    def test_simular_nao_chama_nem_grava(self):
        rclone = RcloneFalso()

        pub.publicar(self.conn, EDITAL, self.saida, "gdrive:Material", rclone, simular=True, saida=lambda *_: None)

        self.assertEqual([], rclone.chamadas)
        self.assertEqual(self.arquivos, self.arquivos_no_banco())

    def test_publicado_sai_no_segmentos_csv_sem_aviso(self):
        pub.publicar(self.conn, EDITAL, self.saida, "gdrive:Material", RcloneFalso(), saida=lambda *_: None)

        _, segmentos, avisos = exp.montar_linhas(self.conn, EDITAL)

        self.assertEqual([], [a for a in avisos if "não é link" in a])
        self.assertTrue(all(s["arquivo"].startswith("https://") for s in segmentos))


if __name__ == "__main__":
    unittest.main()
