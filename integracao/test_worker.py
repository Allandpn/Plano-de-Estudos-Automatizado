#!/usr/bin/env python3
"""
Testes do worker do material (integracao/worker.py), sem rede e sem IA de verdade.

Rodar (da raiz do repositório):
    python -m unittest discover -s integracao -p "test_*.py"

SGE falso em memória, IA falsa com respostas roteirizadas, PDFs sintéticos (mesmo gerador
de dias/test_montar_bloco.py) e um índice SQLite montado aqui com o schema de
indice/indexador.py — com o caminho absoluto de OUTRA máquina gravado, como acontece
quando o índice gerado no PC é copiado para o Pi.
"""

import csv
import io
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "integracao"))
sys.path.insert(0, str(RAIZ / "dias"))
from test_montar_bloco import criar_pdf  # noqa: E402
import worker as wk  # noqa: E402
from acervo import Acervo, caminho_relativo, termos_de_busca  # noqa: E402
from sge_api import ErroSge  # noqa: E402

SCHEMA_INDICE = """
CREATE TABLE arquivos (id INTEGER PRIMARY KEY AUTOINCREMENT, caminho TEXT UNIQUE NOT NULL, curso TEXT,
    nome_arquivo TEXT, n_paginas INTEGER, tamanho_bytes INTEGER, hash TEXT, mtime REAL,
    pagina_indice INTEGER, indexado_em REAL);
CREATE TABLE bookmarks (id INTEGER PRIMARY KEY AUTOINCREMENT, arquivo_id INTEGER NOT NULL, nivel INTEGER,
    titulo TEXT, pagina INTEGER);
CREATE TABLE paginas (id INTEGER PRIMARY KEY AUTOINCREMENT, arquivo_id INTEGER NOT NULL, pagina INTEGER, texto TEXT);
CREATE VIRTUAL TABLE paginas_fts USING fts5(texto, content='paginas', content_rowid='id');
CREATE TRIGGER paginas_ai AFTER INSERT ON paginas BEGIN
    INSERT INTO paginas_fts(rowid, texto) VALUES (new.id, new.texto);
END;
"""


class SgeFalso:
    def __init__(self, assuntos, respostas_ia=()):
        self.assuntos = assuntos
        self.respostas_ia = list(respostas_ia)
        self.pedidos_ia = []
        self.importados = []
        self.lacunas = []
        self.ativo = {"id": 7}

    def concurso_ativo(self):
        return self.ativo

    def planejamento(self, concurso_id):
        return {"slug": "trt-teste", "nome": "TRT Teste", "assuntos": self.assuntos}

    def completar(self, sistema, usuario):
        self.pedidos_ia.append(usuario)
        resposta = self.respostas_ia.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta if isinstance(resposta, str) else json.dumps(resposta)

    def importar_segmentos(self, csv_texto):
        self.importados.append(list(csv.DictReader(io.StringIO(csv_texto))))

    def registrar_lacuna(self, chave, motivo):
        self.lacunas.append((chave, motivo))


def assunto(nome="Atos administrativos, requisitos", chave="chave-atos", **extra):
    return {"disciplina": "Direito Administrativo", "assunto": nome, "peso": "MEDIO", "ordem": 1,
            "chaveExterna": chave, "segmentos": 0, "lacuna": None, **extra}


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.acervo_dir = self.dir / "apostilas"
        (self.acervo_dir / "Direito" / "Adm").mkdir(parents=True)
        criar_pdf(self.acervo_dir / "Direito" / "Adm" / "aula 03.pdf", 30, secoes=(1, 11))
        self.indice = self.dir / "indice.db"
        conn = sqlite3.connect(self.indice)
        conn.executescript(SCHEMA_INDICE)
        # Caminho absoluto do PC onde foi indexado; curso com barra invertida (Windows).
        conn.execute("INSERT INTO arquivos (caminho, curso, nome_arquivo, n_paginas) VALUES (?, ?, ?, ?)",
                     (r"G:\apostilas\Direito\Adm\aula 03.pdf", "Direito\\Adm", "aula 03.pdf", 30))
        for p in range(1, 31):
            texto = "atos administrativos requisitos competencia forma" if 3 <= p <= 20 else "outro tema qualquer"
            conn.execute("INSERT INTO paginas (arquivo_id, pagina, texto) VALUES (1, ?, ?)", (p, texto))
        conn.execute("INSERT INTO bookmarks (arquivo_id, nivel, titulo, pagina) VALUES (1, 1, 'Atos administrativos', 3)")
        conn.commit()
        conn.close()
        self.material = self.dir / "material"

    def tearDown(self):
        self._tmp.cleanup()

    def worker(self, sge):
        return wk.Worker(sge, Acervo(self.indice, self.acervo_dir), self.material, self.dir / "trabalho")


ESCOLHA_VALIDA = {"fontes": [{"arquivo": "A1", "paginas": "3-20", "rotulo": "Aula 03 — atos",
                              "cobre": ["Atos administrativos", "requisitos"], "tipo": "teoria"}],
                  "lacunas": []}


class AcervoTest(Base):
    def test_caminho_do_pc_vira_relativo_a_raiz_do_pi(self):
        self.assertEqual("Direito/Adm/aula 03.pdf", caminho_relativo("Direito\\Adm", "aula 03.pdf"))
        candidatos = Acervo(self.indice, self.acervo_dir).candidatos(termos_de_busca("Atos administrativos"))
        self.assertEqual("Direito/Adm/aula 03.pdf", candidatos[0]["arquivo"])
        self.assertTrue((self.acervo_dir / candidatos[0]["arquivo"]).is_file())
        self.assertEqual([{"titulo": "Atos administrativos", "pagina": 3}], candidatos[0]["sumario"])

    def test_mapa_mostra_onde_cada_pagina_comeca(self):
        candidatos = Acervo(self.indice, self.acervo_dir).candidatos(termos_de_busca("Atos administrativos"))
        mapa = {m["pagina"]: m["inicio"] for m in candidatos[0]["mapa"]}
        # Ocorrências nas p. 3-20; mapa com margem de 3 páginas: 1 a 23.
        self.assertEqual(1, min(mapa))
        self.assertEqual(23, max(mapa))
        self.assertTrue(mapa[22].startswith("outro tema"), "o mapa mostra onde o tema vizinho começa")

    def test_inicio_da_pagina_sem_numeracao_de_rodape(self):
        from acervo import inicio_da_pagina
        self.assertEqual("acerca de / a cerca de", inicio_da_pagina("17 39 acerca de / a cerca de"))

    def test_inicio_de_uma_pagina_pelo_caminho_relativo(self):
        a = Acervo(self.indice, self.acervo_dir)
        self.assertTrue(a.inicio("Direito/Adm/aula 03.pdf", 5).startswith("atos administrativos"))

    def test_termos_sem_conectivos_e_sem_acento(self):
        self.assertEqual(["atos", "administrativos", "requisitos"],
                         termos_de_busca("Atos administrativos: conceito e requisitos"))


class WorkerTest(Base):
    def test_escolha_valida_vira_segmentos_importados_no_sge(self):
        sge = SgeFalso([assunto()], [ESCOLHA_VALIDA])

        self.assertEqual(1, self.worker(sge).ciclo())

        self.assertEqual([], sge.lacunas)
        linhas = sge.importados[0]
        self.assertTrue(all(l["chaveExternaAssunto"] == "chave-atos" for l in linhas))
        self.assertTrue(all(l["arquivo"].startswith("/material/blocos/") for l in linhas))
        for l in linhas:
            self.assertTrue((self.material / l["arquivo"].removeprefix("/material/")).is_file(),
                            "o SGE serve /material/ do mesmo diretório em que o PDF foi gerado")
        self.assertIn("p. 3: ", sge.pedidos_ia[0], "a IA recebe as páginas que citam o assunto")
        self.assertIn("Início de cada página:", sge.pedidos_ia[0], "e o mapa de onde cada página começa")

    def test_ia_sem_material_registra_lacuna(self):
        sge = SgeFalso([assunto()], [{"sem_material": True, "motivo": "a apostila só cita o termo"}])

        self.worker(sge).ciclo()

        self.assertEqual([("chave-atos", "a apostila só cita o termo")], sge.lacunas)
        self.assertEqual([], sge.importados)

    def test_recusada_uma_vez_tenta_de_novo_com_os_erros(self):
        invalida = {"fontes": [{"arquivo": "A1", "paginas": "3-99", "cobre": ["Atos administrativos", "requisitos"]}]}
        sge = SgeFalso([assunto()], [invalida, ESCOLHA_VALIDA])

        self.worker(sge).ciclo()

        self.assertEqual(2, len(sge.pedidos_ia))
        self.assertIn("recusada pela validação", sge.pedidos_ia[1])
        self.assertEqual(1, len(sge.importados))

    def test_recusada_duas_vezes_vira_lacuna_nunca_material(self):
        sem_parte = {"fontes": [{"arquivo": "A1", "paginas": "3-20", "cobre": ["Atos administrativos"]}]}
        sge = SgeFalso([assunto()], [sem_parte, sem_parte])

        self.worker(sge).ciclo()

        self.assertEqual([], sge.importados)
        self.assertEqual(1, len(sge.lacunas))
        self.assertIn("não passou na validação", sge.lacunas[0][1])

    def test_sem_candidato_no_acervo_nem_chama_a_ia(self):
        sge = SgeFalso([assunto(nome="Criptografia quântica", chave="chave-cripto")])

        self.worker(sge).ciclo()

        self.assertEqual([], sge.pedidos_ia)
        self.assertEqual("chave-cripto", sge.lacunas[0][0])

    def test_pula_quem_ja_tem_material_ou_lacuna(self):
        sge = SgeFalso([assunto(segmentos=3), assunto(chave="outra", lacuna="já sabido")])

        self.assertEqual(0, self.worker(sge).ciclo())
        self.assertEqual([], sge.pedidos_ia)

    def test_ia_fora_do_ar_nao_marca_lacuna_e_para_o_ciclo(self):
        sge = SgeFalso([assunto(), assunto(chave="segunda")],
                       [ErroSge(503, "IA_INDISPONIVEL", "sem chave")])

        self.assertEqual(0, self.worker(sge).ciclo())
        self.assertEqual([], sge.lacunas, "IA fora do ar não é lacuna do assunto")
        self.assertEqual(1, len(sge.pedidos_ia), "o ciclo para no primeiro erro de IA")

    def test_sem_concurso_alvo_nao_faz_nada(self):
        sge = SgeFalso([assunto()])
        sge.ativo = None

        self.assertEqual(0, self.worker(sge).ciclo())


if __name__ == "__main__":
    unittest.main()
