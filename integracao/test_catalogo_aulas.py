#!/usr/bin/env python3
"""Testes de integracao/catalogo_aulas.py: o índice sintético dos testes da estrutura e uma IA falsa."""

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalogo_aulas as ca  # noqa: E402
from sge_api import ErroSge  # noqa: E402
from test_estrutura_apostilas import AULAS  # noqa: E402
from test_worker import SCHEMA_INDICE  # noqa: E402

CURSOS = ["Redes de Computadores", "Legislação Tributária", "Passo Estratégico", "Bizu"]


class IaFalsa:
    def __init__(self, respostas):
        self.respostas, self.pedidos = list(respostas), []

    def completar(self, sistema, usuario):
        self.pedidos.append(usuario)
        r = self.respostas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r if isinstance(r, str) else json.dumps(r)


REDES = {"natureza": "aula", "temas": [{"tema": "NAT e PAT", "subtemas": ["NAT", "PAT"], "secoes": [1, 2, 3]},
                                       {"tema": "IPv6", "subtemas": [], "secoes": [4]}]}


class CatalogoTest(unittest.TestCase):
    AULAS = AULAS

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.saida = Path(self._tmp.name) / "saida"
        self.conn = sqlite3.connect(Path(self._tmp.name) / "i.db")
        self.conn.executescript(SCHEMA_INDICE)
        for i, (curso, nome, paginas) in enumerate(self.AULAS, 1):
            self.conn.execute("INSERT INTO arquivos (caminho, curso, nome_arquivo, n_paginas, hash) VALUES (?, ?, ?, ?, ?)",
                              (f"x{i}", curso, nome, len(paginas), f"h{i}"))
            for p, t in enumerate(paginas, 1):
                self.conn.execute("INSERT INTO paginas (arquivo_id, pagina, texto) VALUES (?, ?, ?)", (i, p, t))
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        self._tmp.cleanup()

    def test_escolhe_uma_de_cada_curso_por_vez_e_deixa_de_fora_o_que_nao_e_aula(self):
        nomes = [a[2] for a in ca.escolher_aulas(self.conn, CURSOS, total=10)]
        self.assertEqual(["aula 06.pdf", "curso-226705-aula-00-639a-completo.pdf",
                          "curso-376803-aula-06-5dea-completo.pdf", "curso-383914-aula-11-02d5-completo.pdf"], nomes,
                         "aviso.pdf é curto e sem sumário")
        self.assertEqual(2, len(ca.escolher_aulas(self.conn, CURSOS, total=2)))

    def test_pedido_traz_secoes_com_faixa_e_trecho(self):
        _, pedido = ca.montar_pedido(self.conn, 1, AULAS[0][0], "aula 06.pdf")
        self.assertIn("1. NAT e PAT | teoria | p. 3–5 | «NAT E PAT teoria do NAT»", pedido)
        self.assertIn("3. NAT e PAT | lista_questoes | FCC | p. 8–9\n", pedido, "questões sem trecho")
        _, pedido = ca.montar_pedido(self.conn, 4, AULAS[3][0], AULAS[3][1])
        self.assertIn("Incidência por subassunto (da própria apostila): Tipologia textual e gêneros textuais 45.5%", pedido)

    def test_contexto_da_teoria_primeira_linha_ou_titulos(self):
        self.assertEqual(["NAT REVERSO E O BALANCEAMENTO DE CARGA", "P IP 6", "ROTOCOLO V", "2.3 Tipos de endereço"],
                         ca.titulos_da_pagina("NAT REVERSO E O BALANCEAMENTO DE CARGA\nOutro ponto que pode ser cobrado em "
                                              "provas é a questão\nP IP 6\nROTOCOLO V\nCESPE - 2018 - EMAP - ANALISTA\n"
                                              "2.3 Tipos de endereço\n1. (FCC - TRT)"))
        _, pedido = ca.montar_pedido(self.conn, 1, AULAS[0][0], "aula 06.pdf", contexto="titulos")
        self.assertIn("Páginas da teoria (títulos e subtítulos):\np. 3: NAT E PAT\n", pedido)
        self.assertNotIn("p. 6:", pedido, "páginas de questões ficam fora")
        _, pedido = ca.montar_pedido(self.conn, 1, AULAS[0][0], "aula 06.pdf", contexto="primeira_linha")
        self.assertIn("p. 4: mais teoria\np. 5: teoria\np. 10: PROTOCOLO IPV6 resumo", pedido)

    def test_interpreta_secoes_em_paginas_e_aponta_o_que_falta(self):
        a = ca.ea.analisar_aula(self.conn, 1)
        f = ca.interpretar({"temas": [{"tema": "NAT e PAT", "subtemas": ["NAT"], "secoes": [1, 2, 9]}]}, a)
        self.assertEqual([[3, 5]], f["temas"][0]["paginas"], "as questões não entram na faixa do tema")
        self.assertEqual(["teoria"], f["temas"][0]["tipos"])
        self.assertEqual([{"secao": 2, "tipo": "questoes_comentadas", "banca": "CEBRASPE", "paginas": [6, 7]},
                          {"secao": 3, "tipo": "lista_questoes", "banca": "FCC", "paginas": [8, 9]}],
                         f["temas"][0]["questoes"], "presas ao tema pelo nome no sumário")
        self.assertEqual([4], f["secoes_sem_tema"])
        with self.assertRaises(ValueError):
            ca.interpretar({"temas": [{"tema": "Só questões", "secoes": [2, 3]}]}, a)
        self.assertEqual(["NAT e PAT: seções inexistentes [9]"], f["problemas"])
        self.assertEqual("aula", f["natureza"])
        with self.assertRaises(ValueError):
            ca.interpretar({"temas": [{"tema": "X", "secoes": [99]}]}, a)
        with self.assertRaises(ValueError):
            ca.interpretar({"natureza": "aula"}, a)

    def test_sem_sumario_a_ia_da_as_paginas(self):
        a = {"entradas": [], "n": 20}
        f = ca.interpretar({"natureza": "revisao", "temas": [{"tema": "LRF", "paginas": [3, 12]}]}, a)
        self.assertEqual([[3, 12]], f["temas"][0]["paginas"])
        with self.assertRaises(ValueError):
            ca.interpretar({"temas": [{"tema": "LRF", "paginas": [3, 40]}]}, a)

    def test_ensaio_grava_continua_de_onde_parou_e_para_quando_a_ia_para(self):
        ia = IaFalsa([REDES, "não sei", {"temas": [{"tema": "Código do Contribuinte de SC", "secoes": [1, 2, 3]}]},
                      ErroSge(429, "LIMITE", "limite da janela")])
        fichas, parou = ca.ensaio(ia, self.conn, self.saida, CURSOS, total=4, log=lambda m: None)
        self.assertIn("limite da janela", parou)
        self.assertEqual(2, len(fichas))
        self.assertIn("Sua resposta anterior não serviu", ia.pedidos[2], "resposta sem JSON ganha segunda chance")
        md = (self.saida / "catalogo-ensaio.md").read_text(encoding="utf-8")
        self.assertIn("## 00 - Curso Regular\\09 - Redes de Computadores\\aula 06.pdf", md)
        self.assertIn("- [ ] **NAT e PAT** — p. 3–5 · seções 1 (teoria)\n  - NAT; PAT\n"
                      "  - questões (à parte): p. 6–7 questoes comentadas CEBRASPE; p. 8–9 lista questoes FCC", md)
        self.assertIn("- [ ] **Código do Contribuinte de SC** — p. 3–40", md)
        self.assertIn("- questões da aula, sem tema (à parte): p. 41–46 questoes comentadas; p. 47–50 lista questoes", md)
        ia2 = IaFalsa([{"natureza": "revisao", "temas": [{"tema": "Tipologia textual", "secoes": [4, 5, 6]}]},
                       {"natureza": "revisao", "temas": [{"tema": "Despesa pública", "secoes": [2]}]}])
        fichas, parou = ca.ensaio(ia2, self.conn, self.saida, CURSOS, total=4, log=lambda m: None)
        self.assertIsNone(parou)
        self.assertEqual(2, len(ia2.pedidos), "as duas primeiras não são perguntadas de novo")
        self.assertEqual(4, len(json.loads((self.saida / "catalogo-ensaio.json").read_text(encoding="utf-8"))))

    def test_campos_novos_e_pagina_do_subtema_conferida(self):
        a = ca.ea.analisar_aula(self.conn, 1)
        textos = dict(self.conn.execute("SELECT pagina, texto FROM paginas WHERE arquivo_id = 1").fetchall())
        f = ca.interpretar({"temas": [{"tema": "NAT e PAT", "disciplina": "Redes de Computadores",
                                       "termos": ["Network Address Translation", "Port Address Translation"],
                                       "secoes": [1],
                                       "subtemas": [{"nome": "Teoria do NAT", "pagina": 3},
                                                    {"nome": "Protocolo IPv6", "pagina": 4},
                                                    {"nome": "Mais", "pagina": 5},
                                                    {"nome": "NAT reverso", "pagina": 10},
                                                    {"nome": "PAT", "pagina": None}]}]}, a, textos)
        t = f["temas"][0]
        self.assertEqual(("Redes de Computadores", ["Network Address Translation", "Port Address Translation"]),
                         (t["disciplina"], t["termos"]))
        self.assertEqual([{"nome": "Teoria do NAT", "pagina": 3, "confirmada": True},
                          {"nome": "Protocolo IPv6", "pagina": 4, "confirmada": False},
                          {"nome": "Mais", "pagina": 4, "confirmada": True, "pagina_ia": 5},
                          {"nome": "NAT reverso", "pagina": None, "confirmada": False},
                          {"nome": "PAT", "pagina": None, "confirmada": False}], t["subtemas"],
                         "página fora da faixa do tema (p. 10) é descartada; palavras ausentes não confirmam; "
                         "a IA errou por uma página e a regra corrigiu (guarda a dela)")
        self.assertEqual(["RDP", "SQL", "PROTOCOLO"], ca.palavras_de("RDP, T-SQL e o protocolo"))
        md = ca.relatorio([dict(ca.ficha(None, self.conn, (1, AULAS[0][0], "aula 06.pdf"),
                                         resposta={"temas": [{"tema": "NAT e PAT", "disciplina": "Redes", "secoes": [1],
                                                              "subtemas": [{"nome": "Teoria do NAT", "pagina": 3}]}]}))])
        self.assertIn("Subtemas: 1; com página dada pela IA: 1; página confirmada no texto: 1", md)
        self.assertIn("- [ ] **NAT e PAT** · _Redes_ — p. 3–5", md)
        self.assertIn("  - Teoria do NAT (p. 3 ✓)", md)

    def test_ficha_traz_hash_origem_e_versao(self):
        f = ca.ficha(None, self.conn, (1, AULAS[0][0], "aula 06.pdf"), resposta=REDES, gemeas=["outro\\aula 06.pdf"])
        self.assertEqual(("h1", "acervo", ["outro\\aula 06.pdf"], ca.VERSAO_PEDIDO),
                         (f["hash"], f["origem"], f["gemeas"], f["versao_pedido"]))

    def test_reprocessar_refaz_a_regra_sem_chamar_a_ia(self):
        ia = IaFalsa([REDES])
        ca.ensaio(ia, self.conn, self.saida, CURSOS, total=1, log=lambda m: None)
        arquivo = self.saida / "catalogo-ensaio.json"
        fichas = json.loads(arquivo.read_text(encoding="utf-8"))
        self.assertEqual(REDES, fichas[0]["resposta"])
        del fichas[0]["resposta"]  # ficha antiga, de antes de a resposta ser guardada
        fichas[0]["temas"][0]["paginas"] = [[1, 99]]
        arquivo.write_text(json.dumps(fichas), encoding="utf-8")
        f = ca.reprocessar(self.conn, self.saida, log=lambda m: None)
        self.assertEqual([[3, 5]], f[0]["temas"][0]["paginas"])
        self.assertEqual(1, len(ia.pedidos))

    def test_simular_nao_chama_a_ia(self):
        fichas, _ = ca.ensaio(None, self.conn, self.saida, CURSOS, total=4, simular=True, log=lambda m: None)
        self.assertEqual(4, len(fichas))
        self.assertIn("Sem sumário" if not fichas[3]["secoes"] else "Seções", fichas[3]["pedido"])
        self.assertFalse((self.saida / "catalogo-ensaio.json").exists())


class AcervoTest(CatalogoTest):
    """O acervo inteiro: a aula de Redes tem uma gêmea em outro curso e o aviso não é aula."""
    AULAS = AULAS + [("SEFAZ-CE 2026\\28 - Redes e Segurança", "aula 06.pdf", AULAS[0][2])]

    def test_gemeas_por_miolo(self):
        dono = ca.grupos_de_gemeas(self.conn, log=lambda m: None)
        copia = len(self.AULAS)
        self.assertEqual({**{i: i for i in range(1, copia)}, copia: 1}, dono,
                         "a cópia do SEFAZ-CE aponta a aula do Curso Regular, que vem antes na ordem dos cursos")

    def test_acervo_pula_gemea_e_o_que_nao_e_aula_continua_e_respeita_o_limite(self):
        db = ca.CatalogoDb(str(Path(self._tmp.name) / "catalogo.db"))
        respostas = [REDES, {"temas": [{"tema": "Código do Contribuinte de SC", "secoes": [1]}]},
                     {"natureza": "revisao", "temas": [{"tema": "Tipologia textual", "secoes": [4]}]},
                     {"natureza": "revisao", "temas": [{"tema": "Despesa pública", "secoes": [2]}]}]
        ia = IaFalsa(list(respostas))
        chamadas, parou = ca.catalogar_acervo(ia, self.conn, db, limite=2, log=lambda m: None)
        self.assertEqual((2, None), (chamadas, parou))
        chamadas, parou = ca.catalogar_acervo(ia, self.conn, db, log=lambda m: None)
        self.assertEqual((2, None), (chamadas, parou), "continua de onde parou")
        self.assertEqual(4, len(ia.pedidos), "a gêmea e o aviso não gastam chamada")
        situacao = dict(db.conn.execute("SELECT caminho, situacao FROM fichas").fetchall())
        self.assertEqual("fora", situacao["00 - Curso Regular\\09 - Redes de Computadores\\aviso.pdf"])
        gemea = [json.loads(f) for (f,) in db.conn.execute("SELECT ficha FROM fichas WHERE situacao = 'gemea'")]
        self.assertEqual(1, len(gemea))
        primeira = json.loads(db.conn.execute("SELECT ficha FROM fichas WHERE caminho = ?", (gemea[0]["gemea_de"],)).fetchone()[0])
        self.assertEqual([gemea[0]["caminho"]], primeira["gemeas"])
        self.assertEqual((0, None), ca.catalogar_acervo(ia, self.conn, db, log=lambda m: None), "nada a refazer")
        from datetime import datetime, timedelta
        texto = ca.progresso(self.conn, db, agora=datetime.now() + timedelta(minutes=5))
        self.assertIn("Arquivos processados: 6 de 6 (100%)", texto)
        self.assertIn("Aulas lidas pela IA: 4 de ~4 (100%)", texto)
        self.assertIn("Sem chamada: 1 gêmeas, 1 não são aula", texto)
        self.assertIn("~0 aulas", texto)
        self.assertIn("(há 5 min)", texto)
        db.conn.execute("UPDATE fichas SET versao_pedido = 1 WHERE situacao = 'ok'")
        ia.respostas = list(respostas)
        self.assertEqual(4, ca.catalogar_acervo(ia, self.conn, db, log=lambda m: None)[0], "pedido novo refaz as fichas")


if __name__ == "__main__":
    unittest.main()
