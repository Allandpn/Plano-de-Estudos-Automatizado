#!/usr/bin/env python3
"""
acervo.py — Busca candidatos no índice de apostilas para um assunto, no formato que a IA
da triagem automática lê (integracao/worker.py).

O índice (indice/indice.db, gerado por indice/indexador.py) guarda o caminho absoluto da
máquina onde foi indexado, mas também `curso` (pasta relativa à raiz) e `nome_arquivo`.
O arquivo é sempre reconstruído como <raiz do acervo>/<curso>/<nome_arquivo>: o índice
gerado no PC funciona no Pi sem conversão, só apontando a raiz certa.
"""

import re
import sqlite3
from contextlib import closing
import unicodedata
from pathlib import Path, PureWindowsPath

# Palavras que não ajudam a achar conteúdo: conectivos e termos genéricos de edital.
VAZIAS = {
    "a", "o", "as", "os", "e", "de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas",
    "um", "uma", "para", "por", "com", "sem", "sobre", "entre", "ou", "que", "seus", "suas",
    "conceitos", "conceito", "nocoes", "nocao", "principios", "aspectos", "tipos", "geral",
    "gerais", "basicos", "basicas", "fundamentos", "caracteristicas",
}


def sem_acento(texto):
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")


def radical_de_busca(termo):
    """'modelos' -> 'modelo', 'servidores' -> 'servidor', 'configuracoes' -> 'configurac': o plural
    do edital como prefixo FTS ("modelos"*) não casava "modelo" no texto da apostila — a parte
    "modelos OSI e TCP/IP" achava só listas de questões, nunca a teoria."""
    if len(termo) > 6 and termo.endswith(("oes", "aes", "aos")):
        return termo[:-3]
    if len(termo) > 6 and termo.endswith("es") and termo[-3] in "rzl":
        return termo[:-2]
    if len(termo) > 4 and termo.endswith("s") and not termo.endswith(("ss", "us", "is")):
        return termo[:-1]
    return termo


def termos_de_busca(*textos):
    """'Atos administrativos: conceito, requisitos' -> ['atos', 'administrativos', 'requisitos']."""
    termos = []
    for texto in textos:
        for palavra in re.findall(r"[A-Za-z0-9]+", sem_acento(texto or "").lower()):
            if len(palavra) >= 3 and palavra not in VAZIAS and palavra not in termos:
                termos.append(palavra)
    return termos


# Palavras que as pastas de curso e as disciplinas dos editais repetem sem dizer o assunto.
GENERICAS_DE_CURSO = {
    "conhecimentos", "especificos", "gerais", "nocoes", "nocao", "curso", "cursos", "basico",
    "passo", "estrategico", "especialidade", "regulares", "area", "fiscal", "lingua", "completo",
    "regular", "sem", "correcao", "discursiva", "para", "concursos", "pos", "edital",
}


def radicais(texto):
    """'Língua Portuguesa' -> {'portug'}: os 6 primeiros caracteres de cada palavra que diz
    algo, para 'Portuguesa' (edital) casar com 'Português' (pasta do curso)."""
    palavras = re.findall(r"[a-z0-9]+", sem_acento(texto or "").lower())
    return {p[:6] for p in palavras if len(p) >= 4 and p not in GENERICAS_DE_CURSO}


def cursos_da_disciplina(cursos, disciplina):
    """Das pastas de curso do acervo, as mais afins à disciplina do edital: as que dividem
    pelo menos metade (arredondada para cima) dos radicais do melhor casamento. Vazio se
    nenhuma divide palavra com a disciplina."""
    alvo = radicais(disciplina)
    pontos = {c: len(alvo & radicais(c)) for c in cursos}
    melhor = max(pontos.values(), default=0)
    if melhor == 0:
        return []
    corte = -(-melhor // 2)
    return [c for c, p in pontos.items() if p >= corte]


def caminho_relativo(curso, nome_arquivo):
    """Junta curso + nome no padrão POSIX, aceitando curso gravado com barra invertida (Windows)."""
    partes = [p for p in PureWindowsPath(curso or "").parts if p not in ("", ".")]
    return "/".join(partes + [nome_arquivo])


class Acervo:
    def __init__(self, indice_db, raiz):
        self.indice_db = str(indice_db)
        self.raiz = Path(raiz)

    def _conectar(self):
        conn = sqlite3.connect(f"file:{self.indice_db}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def caminho(self, relativo):
        return self.raiz / Path(relativo)

    def candidatos(self, termos, max_arquivos=6, max_paginas_por_arquivo=12, limite_hits=150,
                   margem_mapa=3, max_mapa=45, disciplina=None):
        """Os arquivos com mais páginas citando os termos, cada um com as páginas que citam
        (e o trecho), o sumário (bookmarks) e o **mapa**: o início de cada página da região
        das ocorrências. Sem o mapa, a IA não via onde um tema termina e o vizinho começa, e
        as faixas transbordavam (acentuação dentro de crase — achado na primeira preparação
        real, 2026-10-17). Ordem: mais relevante primeiro.

        Com `disciplina`, a busca se restringe primeiro aos cursos afins a ela (cursos_da_disciplina).
        Sem isso, assunto de nome genérico ("Conectivos", "Morfossintaxe") trazia os 6 melhores
        arquivos de outra disciplina e a IA, certa, devolvia "não ensina" — 12 falsos
        sem-material na primeira preparação real (SEFAZ SC, 2026-10-17). Sem curso afim, ou se
        a busca restrita não acha nada, vale a busca no acervo inteiro."""
        if not termos:
            return []
        query = " OR ".join(f'"{t}"*' for t in termos)
        # closing: o `with` de sqlite3 só faz commit, não fecha a conexão.
        with closing(self._conectar()) as conn:
            linhas = []
            if disciplina:
                cursos = cursos_da_disciplina(
                    [r[0] for r in conn.execute("SELECT DISTINCT curso FROM arquivos") if r[0]], disciplina)
                if cursos:
                    linhas = self._hits(conn, query, limite_hits, cursos)
            if not linhas:
                linhas = self._hits(conn, query, limite_hits)
            por_arquivo = {}
            for l in linhas:
                item = por_arquivo.setdefault(l["id"], {
                    "arquivo": caminho_relativo(l["curso"], l["nome_arquivo"]),
                    "n_paginas": l["n_paginas"], "score": 0.0, "paginas": [], "_todas": set(),
                })
                item["score"] += -l["score"]  # bm25: menor é melhor
                item["_todas"].add(l["pagina"])  # região do mapa: todas as ocorrências, não só as listadas
                if len(item["paginas"]) < max_paginas_por_arquivo:
                    item["paginas"].append({"pagina": l["pagina"], "trecho": l["trecho"]})
            escolhidos = sorted(por_arquivo.items(), key=lambda kv: -kv[1]["score"])[:max_arquivos]
            resultado = []
            for arquivo_id, item in escolhidos:
                item["paginas"].sort(key=lambda p: p["pagina"])
                item["sumario"] = [
                    {"titulo": b["titulo"], "pagina": b["pagina"]}
                    for b in conn.execute(
                        "SELECT titulo, pagina FROM bookmarks WHERE arquivo_id = ? AND nivel <= 2 ORDER BY pagina LIMIT 40",
                        (arquivo_id,))
                ]
                del item["score"]
                item["mapa"] = self._mapa(conn, arquivo_id, sorted(item.pop("_todas")), item["n_paginas"], margem_mapa, max_mapa)
                resultado.append(item)
            return resultado

    def candidatos_por_partes(self, partes, disciplina=None, min_arquivos=6, max_arquivos=12,
                              paginas_por_parte=8, max_paginas_por_arquivo=16, limite_hits=60,
                              margem_mapa=3, max_mapa=60):
        """Uma busca por PARTE do assunto, não uma pelo nome inteiro. Os arquivos que ensinam
        cada parte entram juntos no mesmo pedido à IA, cada um dizendo para quais partes foi
        achado ("partes").

        Por quê (auditoria da cadeia do material, SGE `docs/AUDITORIA-CADEIA-MATERIAL.md`,
        2026-10-18): "Infraestrutura e redes: servidores, virtualização, contêineres, ..." virava
        12 termos em OU que casavam 24% do acervo, e o orçamento fixo de 6 arquivos × 12 páginas
        ficava com quem citava "redes" e "protocolos" mais vezes — o resto das partes sumia.

        Em cada parte:
        - a consulta exige todos os termos da parte na mesma página (E); só cai para OU se o E
          não achar nada;
        - os arquivos vêm dos cursos afins à disciplina E do acervo inteiro: o recorte por nome
          de pasta deixava de fora os cursos certos ("Ciências da Computação" não casa com
          "Redes e Segurança"), e só a rodada recusada consultava o acervo inteiro;
        - orçamento proporcional: cada parte leva pelo menos 2 arquivos, e o total cresce com o
          número de partes (de `min_arquivos` a `max_arquivos`).
        O mapa cobre cada região de ocorrências (não só 45 páginas a partir da primeira)."""
        # "Infraestrutura e redes: servidores" busca só "servidores": o título antes dos dois-pontos
        # é o tema do item inteiro, e na mesma página que cada parte ele só tira o E do sério.
        alvo = {p: (p.rsplit(":", 1)[-1] if termos_de_busca(p.rsplit(":", 1)[-1]) else p) for p in partes}
        partes = [p for p in partes if termos_de_busca(alvo[p])]
        if not partes:
            return []
        por_parte = max(2, -(-min_arquivos // len(partes)))
        with closing(self._conectar()) as conn:
            afins = []
            if disciplina:
                afins = cursos_da_disciplina(
                    [r[0] for r in conn.execute("SELECT DISTINCT curso FROM arquivos") if r[0]], disciplina)
            arquivos = {}
            for parte in partes:
                termos = list(dict.fromkeys(radical_de_busca(t) for t in termos_de_busca(alvo[parte])))
                for operador in (" AND ", " OR "):
                    query = operador.join(f'"{t}"*' for t in termos)
                    afim = self._hits(conn, query, limite_hits, afins) if afins else []
                    geral = self._hits(conn, query, limite_hits)
                    if afim or geral:
                        break
                    if len(termos) == 1:
                        break
                escolhidos = self._melhores(afim, por_parte - 1 if geral else por_parte)
                escolhidos += [a for a in self._melhores(geral, por_parte) if a not in escolhidos]
                escolhidos = escolhidos[:por_parte]
                for l in afim + geral:
                    if l["id"] not in escolhidos:
                        continue
                    item = arquivos.setdefault(l["id"], {
                        "arquivo": caminho_relativo(l["curso"], l["nome_arquivo"]),
                        "n_paginas": l["n_paginas"], "partes": [], "score": 0.0, "_afim": l["curso"] in afins,
                        "_paginas": {}, "_por_parte": {},
                    })
                    if parte not in item["partes"]:
                        item["partes"].append(parte)
                    if l["pagina"] in item["_paginas"]:
                        continue
                    n = item["_por_parte"].get(parte, 0)
                    if n >= paginas_por_parte:
                        continue
                    item["_por_parte"][parte] = n + 1
                    item["score"] += -l["score"]
                    item["_paginas"][l["pagina"]] = l["trecho"]
            limite = min(max_arquivos, max(min_arquivos, 2 * len(partes)))
            ordenados = sorted(arquivos.items(), key=lambda kv: (-len(kv[1]["partes"]), not kv[1]["_afim"], -kv[1]["score"]))
            resultado, vistos = [], {}
            for arquivo_id, item in ordenados:
                # A mesma aula aparece em vários cursos (mesmo PDF, nome diferente): fica a primeira,
                # com as partes das duas, e a vaga vai para outro arquivo.
                abertura = self._abertura(conn, arquivo_id)
                gemea = vistos.get((item["n_paginas"], abertura)) if abertura else None
                if gemea is not None:
                    gemea["partes"] += [p for p in item["partes"] if p not in gemea["partes"]]
                    continue
                if len(resultado) >= limite:
                    break
                vistos[(item["n_paginas"], abertura)] = item
                item["abertura"] = abertura
                todas = sorted(item.pop("_paginas").items())
                item["paginas"] = [{"pagina": p, "trecho": t} for p, t in todas[:max_paginas_por_arquivo]]
                item["sumario"] = [
                    {"titulo": b["titulo"], "pagina": b["pagina"]}
                    for b in conn.execute(
                        "SELECT titulo, pagina FROM bookmarks WHERE arquivo_id = ? AND nivel <= 2 ORDER BY pagina LIMIT 40",
                        (arquivo_id,))
                ]
                item["mapa"] = self._mapa_regioes(conn, arquivo_id, [p for p, _ in todas], item["n_paginas"],
                                                  margem_mapa, max_mapa)
                del item["score"], item["_por_parte"], item["_afim"]
                resultado.append(item)
            return resultado

    @staticmethod
    def _abertura(conn, arquivo_id, tamanho=110):
        """O começo das páginas 1 e 2: título e apresentação da aula, para a IA saber do que ela trata."""
        textos = [inicio_da_pagina(t, tamanho) for (t,) in conn.execute(
            "SELECT texto FROM paginas WHERE arquivo_id = ? AND pagina IN (1, 2) ORDER BY pagina", (arquivo_id,))]
        return " | ".join(t for t in textos if t)

    @staticmethod
    def _melhores(linhas, n):
        """Os ids dos `n` arquivos de maior pontuação somada (bm25: menor é melhor)."""
        if n <= 0:
            return []
        soma = {}
        for l in linhas:
            soma[l["id"]] = soma.get(l["id"], 0.0) - l["score"]
        return [a for a, _ in sorted(soma.items(), key=lambda kv: -kv[1])[:n]]

    @staticmethod
    def _mapa_regioes(conn, arquivo_id, paginas, n_paginas, margem, maximo, juntar=8):
        """Início de cada página das regiões de ocorrência: cada ocorrência com `margem` páginas
        antes e depois, regiões a menos de `juntar` páginas viram uma só (o tema inteiro, sem
        buraco). Se passar de `maximo` linhas, as regiões perdem a margem e o fim é cortado."""
        if not paginas:
            return []
        ultima = n_paginas or (max(paginas) + margem)

        def regioes(m):
            faixas = []
            for p in sorted(paginas):
                ini, fim = max(1, p - m), min(ultima, p + m)
                if faixas and ini - faixas[-1][1] <= juntar:
                    faixas[-1][1] = max(faixas[-1][1], fim)
                else:
                    faixas.append([ini, fim])
            return faixas

        faixas = regioes(margem)
        if sum(f - i + 1 for i, f in faixas) > maximo:
            faixas = regioes(0)
        escolhidas = [p for i, f in faixas for p in range(i, f + 1)][:maximo]
        if not escolhidas:
            return []
        textos = dict(conn.execute(
            "SELECT pagina, texto FROM paginas WHERE arquivo_id = ? AND pagina BETWEEN ? AND ?",
            (arquivo_id, escolhidas[0], escolhidas[-1])).fetchall())
        return [{"pagina": p, "inicio": inicio_da_pagina(textos.get(p))} for p in escolhidas if p in textos]

    @staticmethod
    def _hits(conn, query, limite, cursos=None):
        filtro = f"AND a.curso IN ({','.join('?' * len(cursos))})" if cursos else ""
        return conn.execute(
            f"""SELECT a.id, a.curso, a.nome_arquivo, a.n_paginas, p.pagina,
                       snippet(paginas_fts, 0, '[', ']', '…', 24) AS trecho,
                       bm25(paginas_fts) AS score
                FROM paginas_fts
                JOIN paginas p ON p.id = paginas_fts.rowid
                JOIN arquivos a ON a.id = p.arquivo_id
                WHERE paginas_fts MATCH ? {filtro}
                ORDER BY score LIMIT ?""",
            (query, *(cursos or ()), limite),
        ).fetchall()

    def inicio(self, relativo, pagina):
        """Começo do texto de uma página de um arquivo do acervo (para conferir uma escolha)."""
        partes = relativo.rsplit("/", 1)
        curso, nome = (partes[0], partes[1]) if len(partes) == 2 else ("", partes[0])
        with closing(self._conectar()) as conn:
            for c, texto in conn.execute(
                    """SELECT a.curso, p.texto FROM paginas p JOIN arquivos a ON a.id = p.arquivo_id
                       WHERE a.nome_arquivo = ? AND p.pagina = ?""", (nome, pagina)):
                if caminho_relativo(c, "") .rstrip("/") == curso:
                    return inicio_da_pagina(texto)
        return ""

    @staticmethod
    def _mapa(conn, arquivo_id, paginas, n_paginas, margem, maximo):
        """Primeira linha útil de cada página entre a primeira e a última ocorrência (com
        margem), limitada a `maximo` páginas a partir do começo da região."""
        if not paginas:
            return []
        inicio = max(1, paginas[0] - margem)
        fim = min(n_paginas or paginas[-1] + margem, paginas[-1] + margem, inicio + maximo - 1)
        mapa = []
        for pagina, texto in conn.execute(
                "SELECT pagina, texto FROM paginas WHERE arquivo_id = ? AND pagina BETWEEN ? AND ? ORDER BY pagina",
                (arquivo_id, inicio, fim)):
            mapa.append({"pagina": pagina, "inicio": inicio_da_pagina(texto)})
        return mapa


def inicio_da_pagina(texto, tamanho=90):
    """O começo do texto da página, sem o número de página/rodapé repetido que costuma
    vir na primeira linha das apostilas ("17 39 ...")."""
    linha = " ".join((texto or "").split())
    linha = re.sub(r"^(\d+\s+){1,3}", "", linha)
    return linha[:tamanho]
