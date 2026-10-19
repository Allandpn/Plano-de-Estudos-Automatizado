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

    def _indice_com_dois_cursos(self):
        """Mesmas palavras em duas disciplinas: 'Conectivos' lógicos (muitas ocorrências, vence
        o bm25 sozinho) e conectivos gramaticais, em pastas de curso diferentes."""
        db = self.dir / "dois.db"
        conn = sqlite3.connect(db)
        conn.executescript(SCHEMA_INDICE)
        for i, (curso, nome, texto, paginas) in enumerate([
                ("10 - Cursos Regulares\\18 - Raciocínio Lógico e Matemática", "logica.pdf",
                 "conectivos logicos conectivos conectivos conjuncao disjuncao", 20),
                ("10 - Cursos Regulares\\17 - Curso Básico de Português", "gramatica.pdf",
                 "conectivos conjuncoes preposicoes", 5)], start=1):
            conn.execute("INSERT INTO arquivos (caminho, curso, nome_arquivo, n_paginas) VALUES (?, ?, ?, ?)",
                         (f"x{i}", curso, nome, paginas))
            for p in range(1, paginas + 1):
                conn.execute("INSERT INTO paginas (arquivo_id, pagina, texto) VALUES (?, ?, ?)", (i, p, texto))
        conn.commit()
        conn.close()
        return Acervo(db, self.acervo_dir)

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

    def test_disciplina_restringe_a_busca_aos_cursos_afins(self):
        acervo = self._indice_com_dois_cursos()
        termos = termos_de_busca("Conectivos")
        sem = [c["arquivo"] for c in acervo.candidatos(termos)]
        self.assertTrue(sem[0].endswith("logica.pdf"), "sem disciplina, o tema vizinho vence (o defeito)")
        com = [c["arquivo"] for c in acervo.candidatos(termos, disciplina="Língua Portuguesa")]
        self.assertEqual(1, len(com))
        self.assertTrue(com[0].endswith("gramatica.pdf"), "Portuguesa casa com Português")

    def test_disciplina_sem_curso_afim_ou_sem_resultado_cai_na_busca_geral(self):
        acervo = self._indice_com_dois_cursos()
        termos = termos_de_busca("Conectivos")
        geral = [c["arquivo"] for c in acervo.candidatos(termos)]
        self.assertEqual(geral, [c["arquivo"] for c in acervo.candidatos(termos, disciplina="Contabilidade")])
        # Curso afim existe, mas nele o termo não aparece: não devolve vazio, devolve o geral.
        so_logica = termos_de_busca("conjuncao disjuncao")
        self.assertEqual([c["arquivo"] for c in acervo.candidatos(so_logica)],
                         [c["arquivo"] for c in acervo.candidatos(so_logica, disciplina="Língua Portuguesa")])

    def test_radicais_e_afinidade(self):
        from acervo import radicais, cursos_da_disciplina
        self.assertEqual({"portug"}, radicais("Língua Portuguesa"))
        self.assertEqual({"portug"}, radicais("10 - Área Fiscal\\17 - Curso Básico de Português"))
        cursos = ["A\\Curso Básico de Direito Administrativo", "A\\Direito Constitucional", "A\\Português"]
        self.assertEqual(["A\\Curso Básico de Direito Administrativo", "A\\Direito Constitucional"],
                         cursos_da_disciplina(cursos, "Noções de Direito Administrativo"))
        self.assertEqual([], cursos_da_disciplina(cursos, "Contabilidade"))

    def _indice_redes(self):
        """O caso da auditoria (2026-10-18): um curso afim pelo nome que só fala de OSI, e o
        curso que ensina o resto ("Redes e Segurança") com um nome que não casa com a
        disciplina, e palavras comuns ("redes", "protocolos") espalhadas por toda parte."""
        db = self.dir / "redes.db"
        conn = sqlite3.connect(db)
        conn.executescript(SCHEMA_INDICE)
        arquivos = [
            ("Area Fiscal\\Ciencias da Computacao", "computacao.pdf",
             {range(1, 21): "redes protocolos redes protocolos modelo osi camadas tcp ip"}),
            ("TSE\\06 - Redes e Seguranca", "aula 04 vlan.pdf",
             {range(1, 6): "introducao", range(6, 16): "vlan 802.1q trunk switch redes",
              range(16, 26): "nat traducao de enderecos privados redes"}),
            ("TSE\\06 - Redes e Seguranca", "aula 09 vpn.pdf",
             {range(1, 16): "vpn ipsec tunel redes protocolos"}),
            ("Direito\\Constitucional", "cf.pdf", {range(1, 31): "redes protocolos de intencoes"}),
        ]
        for i, (curso, nome, paginas) in enumerate(arquivos, start=1):
            total = max(max(r) for r in paginas)
            conn.execute("INSERT INTO arquivos (caminho, curso, nome_arquivo, n_paginas) VALUES (?, ?, ?, ?)",
                         (f"x{i}", curso, nome, total))
            for faixa, texto in paginas.items():
                for p in faixa:
                    conn.execute("INSERT INTO paginas (arquivo_id, pagina, texto) VALUES (?, ?, ?)", (i, p, texto))
        conn.commit()
        conn.close()
        return Acervo(db, self.acervo_dir)

    def test_busca_por_parte_traz_um_arquivo_para_cada_parte(self):
        acervo = self._indice_redes()
        nome = "Infraestrutura e redes: modelos OSI, protocolos, VLAN, NAT, VPN"
        disciplina = "Conhecimentos Específicos - Ciências da Computação"
        from triagem_ia import partes_do_assunto

        antiga = [c["arquivo"] for c in acervo.candidatos(termos_de_busca(nome), disciplina=disciplina)]
        nova = acervo.candidatos_por_partes(partes_do_assunto(nome), disciplina=disciplina)

        self.assertEqual(["Area Fiscal/Ciencias da Computacao/computacao.pdf"], antiga,
                         "a busca de antes: só o curso afim pelo nome (o defeito)")
        por_arquivo = {c["arquivo"]: c["partes"] for c in nova}
        self.assertIn("VLAN", por_arquivo["TSE/06 - Redes e Seguranca/aula 04 vlan.pdf"])
        self.assertIn("NAT", por_arquivo["TSE/06 - Redes e Seguranca/aula 04 vlan.pdf"])
        self.assertIn("VPN", por_arquivo["TSE/06 - Redes e Seguranca/aula 09 vpn.pdf"])
        self.assertIn("Infraestrutura e redes: modelos OSI",
                      por_arquivo["Area Fiscal/Ciencias da Computacao/computacao.pdf"],
                      "o título antes dos dois-pontos não entra na busca da parte")
        # "protocolos" sozinho continua genérico ("protocolos de intenções" no Direito): parte
        # vaga do edital traz candidato errado, e é a IA que recusa. Por isso o nome do assunto
        # precisa ser fiel ao edital (que dizia "TCP, UDP, DNS, DHCP...", não "protocolos").

    def test_parte_com_varios_termos_exige_todos_na_pagina(self):
        acervo = self._indice_redes()
        nova = acervo.candidatos_por_partes(["modelos OSI"], disciplina=None)
        self.assertEqual("Area Fiscal/Ciencias da Computacao/computacao.pdf", nova[0]["arquivo"],
                         "'modelos OSI' em E: a página do OSI, não a que só diz 'modelo' ou 'redes'")

    def test_mapa_cobre_cada_regiao_de_ocorrencias(self):
        acervo = self._indice_redes()
        nova = acervo.candidatos_por_partes(["VLAN", "NAT"])
        aula = next(c for c in nova if c["arquivo"].endswith("aula 04 vlan.pdf"))
        paginas = [m["pagina"] for m in aula["mapa"]]
        self.assertIn(6, paginas)
        self.assertIn(25, paginas, "a região do NAT, depois da do VLAN, também aparece no mapa")

    def test_toda_parte_leva_pelo_menos_um_candidato(self):
        db = self.dir / "muitos.db"
        conn = sqlite3.connect(db)
        conn.executescript(SCHEMA_INDICE)
        arquivos = [(f"Redes\\aula {i:02d}", "vlan trunk switch quadro") for i in range(1, 15)] + \
                   [("Dev\\aula 09", "docker conteiner imagem")]
        for i, (curso, texto) in enumerate(arquivos, start=1):
            conn.execute("INSERT INTO arquivos (caminho, curso, nome_arquivo, n_paginas) VALUES (?, ?, 'a.pdf', 5)",
                         (f"x{i}", curso))
            for p in range(1, 6):
                conn.execute("INSERT INTO paginas (arquivo_id, pagina, texto) VALUES (?, ?, ?)",
                             (i, p, f"{texto} {'vlan ' * (20 - i) if i <= 14 else ''} p{i}-{p}"))
        conn.commit()
        conn.close()

        achados = Acervo(db, self.acervo_dir).candidatos_por_partes(["VLAN", "contêineres"], max_arquivos=2, min_arquivos=2)

        self.assertEqual(["VLAN", "contêineres"], [a["partes"][0] for a in achados])

    def test_mesma_aula_em_dois_cursos_entra_uma_vez(self):
        db = self.dir / "gemeas.db"
        conn = sqlite3.connect(db)
        conn.executescript(SCHEMA_INDICE)
        for i, curso in enumerate(["00 - Curso Regular\\09 - Redes", "58 - Especialidade TI - Redes"], start=1):
            conn.execute("INSERT INTO arquivos (caminho, curso, nome_arquivo, n_paginas) VALUES (?, ?, ?, 10)",
                         (f"x{i}", curso, f"aula 04 ({i}).pdf"))
            for p in range(1, 11):
                conn.execute("INSERT INTO paginas (arquivo_id, pagina, texto) VALUES (?, ?, ?)",
                             (i, p, f"{'TSE' if i == 1 else 'Curso Regular'} - Aula 04 - VLAN e 802.1Q" if p == 1
                                    else f"vlan trunk 802.1q secao {'abcdefghij'[p - 1]} do miolo"))
        conn.commit()
        conn.close()

        achados = Acervo(db, self.acervo_dir).candidatos_por_partes(["VLAN"])

        self.assertEqual(1, len(achados), "a gêmea de outro curso não ocupa vaga")
        self.assertIn("Aula 04 - VLAN", achados[0]["abertura"], "capas diferentes, miolo igual: é a mesma aula")

    def test_plural_do_edital_casa_o_singular_da_apostila(self):
        from acervo import radical_de_busca
        self.assertEqual(["modelo", "servidor", "conteiner", "configurac", "rede", "ataque", "processo", "acesso"],
                         [radical_de_busca(t) for t in ("modelos", "servidores", "conteineres", "configuracoes",
                                                        "redes", "ataques", "processos", "acesso")])
        acervo = self._indice_redes()
        achados = acervo.candidatos_por_partes(["camadas OSI"])  # o texto diz "camadas"
        self.assertTrue(achados)
        singular = acervo.candidatos_por_partes(["modelos OSI"])  # o texto diz "modelo"
        self.assertEqual("Area Fiscal/Ciencias da Computacao/computacao.pdf", singular[0]["arquivo"])

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

    def test_curso_afim_e_acervo_inteiro_vao_juntos_numa_rodada_so(self):
        recusa = {"sem_material": True, "motivo": "nao ensina"}
        sge = SgeFalso([assunto("Conectivos", disciplina="Língua Portuguesa")], [recusa])
        w = wk.Worker(sge, self._indice_com_dois_cursos(), self.material, self.dir / "trabalho")

        w.ciclo()

        self.assertEqual(1, len(sge.pedidos_ia), "o acervo inteiro não espera a recusa do recorte")
        self.assertIn("gramatica.pdf", sge.pedidos_ia[0])
        self.assertIn("logica.pdf", sge.pedidos_ia[0])
        self.assertLess(sge.pedidos_ia[0].index("gramatica.pdf"), sge.pedidos_ia[0].index("logica.pdf"),
                        "o curso afim vem primeiro")
        self.assertEqual([("chave-atos", "nao ensina")], sge.lacunas)

    def test_parte_sem_pagina_num_assunto_com_material_fica_registrada(self):
        com_lacuna = {"fontes": [{"arquivo": "A1", "paginas": "3-20", "cobre": ["Atos administrativos"]}],
                      "lacunas": [{"subitem": "requisitos", "motivo": "nenhuma apostila trata"}]}
        sge = SgeFalso([assunto()], [com_lacuna])

        self.worker(sge).ciclo()

        self.assertEqual(1, len(sge.importados), "o assunto ganha o material que existe")
        linhas = (self.dir / "trabalho" / "lacunas-parciais.jsonl").read_text(encoding="utf-8").splitlines()
        registro = json.loads(linhas[0])
        self.assertEqual(("chave-atos", "requisitos", "nenhuma apostila trata"),
                         (registro["chaveExterna"], registro["parte"], registro["motivo"]))

    def test_aula_inteira_vira_da_primeira_a_ultima_pagina(self):
        inteira = {"fontes": [{"arquivo": "A1", "inteira": True, "cobre": ["Atos administrativos", "requisitos"]}],
                   "lacunas": []}
        sge = SgeFalso([assunto()], [inteira])

        self.worker(sge).ciclo()

        self.assertEqual(1, len(sge.importados))
        manifesto = json.loads((self.dir / "trabalho" / "chave-atos.json").read_text(encoding="utf-8"))
        self.assertEqual("1-30", manifesto["fontes"][0]["paginas"], "a aula toda, com as questões e o resumo")
        self.assertIn("MELHOR PECAR POR EXCESSO", __import__("triagem_ia").SISTEMA)

    def test_aula_inteira_sem_faixa_e_lacuna_de_parte_coberta_nao_derrubam_a_escolha(self):
        resposta = {"fontes": [{"arquivo": "A1", "inteira": "true", "paginas": "", "cobre": ["Atos administrativos"]},
                               {"arquivo": "A1", "paginas": "inteira", "cobre": ["requisitos"]}],
                    "lacunas": [{"subitem": "requisitos", "motivo": "só de passagem"}]}
        from triagem_ia import interpretar
        tipo, valor = interpretar(json.dumps(resposta), [{"arquivo": "x.pdf", "n_paginas": 30}])
        self.assertEqual("manifesto", tipo)
        self.assertEqual(["1-30", "1-30"], [f["paginas"] for f in valor["fontes"]])
        self.assertEqual([], valor["lacunas"], "parte coberta por uma fonte não fica como lacuna")

    def test_ensaiar_sem_ia_so_lista_os_candidatos(self):
        sge = SgeFalso([])
        saida = []

        self.worker(sge).ensaiar("Atos administrativos, requisitos", "Direito Administrativo",
                                 saida=saida.append, sem_ia=True)

        self.assertEqual([], sge.pedidos_ia)
        self.assertIn("aula 03.pdf", "\n".join(saida))
        self.assertIn("partes sem nenhum candidato: nenhuma", "\n".join(saida))

    def test_sem_recorte_diferente_uma_rodada_so(self):
        sge = SgeFalso([assunto()], [{"sem_material": True, "motivo": "nao ensina"}])

        self.worker(sge).ciclo()

        self.assertEqual(1, len(sge.pedidos_ia), "mesmos candidatos: não gasta a IA duas vezes")

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
