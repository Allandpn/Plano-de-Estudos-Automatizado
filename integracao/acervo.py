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


def termos_de_busca(*textos):
    """'Atos administrativos: conceito, requisitos' -> ['atos', 'administrativos', 'requisitos']."""
    termos = []
    for texto in textos:
        for palavra in re.findall(r"[A-Za-z0-9]+", sem_acento(texto or "").lower()):
            if len(palavra) >= 3 and palavra not in VAZIAS and palavra not in termos:
                termos.append(palavra)
    return termos


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

    def candidatos(self, termos, max_arquivos=6, max_paginas_por_arquivo=12, limite_hits=150):
        """Os arquivos com mais páginas citando os termos, cada um com as páginas que citam
        (e o trecho) e o sumário (bookmarks). Ordem: mais relevante primeiro."""
        if not termos:
            return []
        query = " OR ".join(f'"{t}"*' for t in termos)
        # closing: o `with` de sqlite3 só faz commit, não fecha a conexão.
        with closing(self._conectar()) as conn:
            linhas = conn.execute(
                """SELECT a.id, a.curso, a.nome_arquivo, a.n_paginas, p.pagina,
                          snippet(paginas_fts, 0, '[', ']', '…', 24) AS trecho,
                          bm25(paginas_fts) AS score
                   FROM paginas_fts
                   JOIN paginas p ON p.id = paginas_fts.rowid
                   JOIN arquivos a ON a.id = p.arquivo_id
                   WHERE paginas_fts MATCH ?
                   ORDER BY score LIMIT ?""",
                (query, limite_hits),
            ).fetchall()
            por_arquivo = {}
            for l in linhas:
                item = por_arquivo.setdefault(l["id"], {
                    "arquivo": caminho_relativo(l["curso"], l["nome_arquivo"]),
                    "n_paginas": l["n_paginas"], "score": 0.0, "paginas": [],
                })
                item["score"] += -l["score"]  # bm25: menor é melhor
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
                resultado.append(item)
            return resultado
