#!/usr/bin/env python3
"""
indexador.py — Indexa apostilas em PDF num banco SQLite com busca full-text.

Uso:
    python indexador.py /caminho/para/apostilas [--db indice.db] [--forcar]

O que faz:
    1. Varre recursivamente a pasta procurando .pdf
    2. Pra cada PDF novo ou alterado (por hash+mtime), extrai:
       - metadados (caminho, curso/pasta, nº páginas, tamanho)
       - texto por página, já limpo de cabeçalho/rodapé repetido
       - outline/bookmarks nativos do PDF, se existirem
    3. Grava tudo num SQLite com uma tabela FTS5 pra busca full-text
    4. É incremental: rodar de novo só processa arquivos novos/mudados

Requisitos:
    pip install pdfplumber --break-system-packages
"""

import argparse
import hashlib
import os
import re
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path

import pdfplumber


# ----------------------------------------------------------------------
# Extração de texto por página, com detecção real de colunas
# ----------------------------------------------------------------------

def eh_duas_colunas(pagina, limiar_gap=20, limiar_fracao=0.02):
    """
    Detecta 2 colunas de verdade olhando se palavras cruzam o eixo
    central da página. Texto de coluna única sempre tem palavras/linhas
    atravessando o meio (parágrafo vai de margem a margem); texto em
    2 colunas nunca atravessa.
    """
    largura = pagina.width
    meio = largura / 2

    try:
        palavras = pagina.extract_words()
    except Exception:
        return False

    if not palavras:
        return False

    total = len(palavras)
    cruzam = 0
    for w in palavras:
        x0, x1 = w["x0"], w["x1"]
        if x0 < meio - limiar_gap and x1 > meio + limiar_gap:
            cruzam += 1
        elif x0 < meio < x1:
            cruzam += 1

    return (cruzam / total) < limiar_fracao


def extrair_texto_pagina(pagina):
    """Extrai o texto de uma página, tratando 2 colunas quando detectado."""
    if eh_duas_colunas(pagina):
        largura, altura = pagina.width, pagina.height
        meio = largura / 2
        esq = pagina.crop((0, 0, meio, altura)).extract_text() or ""
        dir_ = pagina.crop((meio, 0, largura, altura)).extract_text() or ""
        return (esq + "\n" + dir_).strip()
    return (pagina.extract_text() or "").strip()


def normalizar_linha(linha):
    """
    Remove números soltos no início/fim da linha (numeração de página que
    fica grudada no rodapé, ex: "...Banco de Dados 3" -> "...Banco de Dados").
    Usada só pra COMPARAR frequência, não pra decidir o texto final.
    """
    l = re.sub(r"^\s*\d+\s*", "", linha)
    l = re.sub(r"\s*\d+\s*$", "", l)
    return l.strip()


def remover_boilerplate(paginas_texto, limiar_frequencia=0.6):
    """
    Detecta cabeçalho/rodapé automaticamente por frequência: linhas que
    se repetem em muitas páginas do MESMO pdf são ruído (nome de autor,
    site, curso, numeração) — sem precisar saber o nome do curso antes.
    Generaliza pra qualquer apostila, de qualquer curso/autor.

    Compara a versão NORMALIZADA (sem números soltos de página), porque
    o número de página costuma ficar grudado na mesma linha do rodapé
    (ex: "TSE - Concurso... Banco de Dados 3", "...Banco de Dados 4"),
    o que faria a linha nunca repetir exatamente igual.
    """
    contagem = Counter()
    linhas_por_pagina = []

    for texto in paginas_texto:
        linhas = [l.strip() for l in texto.split("\n") if l.strip()]
        linhas_por_pagina.append(linhas)
        for l in {normalizar_linha(x) for x in linhas}:
            if l:
                contagem[l] += 1

    n_paginas = max(len(paginas_texto), 1)
    boilerplate_normalizado = {
        linha for linha, freq in contagem.items()
        if freq / n_paginas >= limiar_frequencia and len(linha) > 2
    }
    # também descarta linhas que são só números (numeração de página solta)
    eh_so_numero = re.compile(r"^\d{1,4}$")

    limpo = []
    linhas_removidas_exemplo = set()
    for linhas in linhas_por_pagina:
        linhas_limpas = []
        for l in linhas:
            if eh_so_numero.match(l):
                continue
            if normalizar_linha(l) in boilerplate_normalizado:
                linhas_removidas_exemplo.add(l)
                continue
            linhas_limpas.append(l)
        limpo.append("\n".join(linhas_limpas))
    return limpo, linhas_removidas_exemplo


def achar_pagina_indice(paginas_limpas):
    """Acha a página do sumário pelo conteúdo (primeira linha == Índice/Sumário)."""
    for i, texto in enumerate(paginas_limpas):
        primeira_linha = texto.strip().split("\n")[0].strip().lower() if texto.strip() else ""
        if primeira_linha in ("índice", "indice", "sumário", "sumario"):
            return i + 1  # página 1-indexed
    return None


def extrair_outline(pdf_path):
    """Tenta extrair bookmarks/outline nativo do PDF, se existir (via pypdf)."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        outline = reader.outline
        resultado = []

        def percorrer(itens, nivel=0):
            for item in itens:
                if isinstance(item, list):
                    percorrer(item, nivel + 1)
                else:
                    try:
                        pagina = reader.get_destination_page_number(item) + 1
                    except Exception:
                        pagina = None
                    resultado.append((nivel, str(item.title), pagina))

        percorrer(outline)
        return resultado
    except Exception:
        return []


# ----------------------------------------------------------------------
# Banco SQLite
# ----------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS arquivos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caminho TEXT UNIQUE NOT NULL,
    curso TEXT,
    nome_arquivo TEXT,
    n_paginas INTEGER,
    tamanho_bytes INTEGER,
    hash TEXT,
    mtime REAL,
    pagina_indice INTEGER,
    indexado_em REAL
);

CREATE TABLE IF NOT EXISTS bookmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_id INTEGER NOT NULL,
    nivel INTEGER,
    titulo TEXT,
    pagina INTEGER,
    FOREIGN KEY (arquivo_id) REFERENCES arquivos(id)
);

CREATE TABLE IF NOT EXISTS paginas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_id INTEGER NOT NULL,
    pagina INTEGER,
    texto TEXT,
    FOREIGN KEY (arquivo_id) REFERENCES arquivos(id)
);

CREATE VIRTUAL TABLE IF NOT EXISTS paginas_fts USING fts5(
    texto,
    content='paginas',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS paginas_ai AFTER INSERT ON paginas BEGIN
    INSERT INTO paginas_fts(rowid, texto) VALUES (new.id, new.texto);
END;

CREATE TRIGGER IF NOT EXISTS paginas_ad AFTER DELETE ON paginas BEGIN
    INSERT INTO paginas_fts(paginas_fts, rowid, texto) VALUES ('delete', old.id, old.texto);
END;
"""


def conectar_db(caminho_db):
    conn = sqlite3.connect(caminho_db)
    conn.executescript(SCHEMA)
    return conn


def hash_arquivo(caminho, bloco=65536):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        while True:
            dado = f.read(bloco)
            if not dado:
                break
            h.update(dado)
    return h.hexdigest()


def arquivo_ja_indexado(conn, caminho, mtime):
    row = conn.execute(
        "SELECT mtime FROM arquivos WHERE caminho = ?", (str(caminho),)
    ).fetchone()
    return row is not None and abs(row[0] - mtime) < 1.0


def indexar_pdf(conn, caminho_pdf, pasta_raiz):
    caminho_pdf = Path(caminho_pdf)
    stat = caminho_pdf.stat()

    with pdfplumber.open(caminho_pdf) as pdf:
        paginas_texto_bruto = [extrair_texto_pagina(p) for p in pdf.pages]

    paginas_limpas, _boilerplate = remover_boilerplate(paginas_texto_bruto)
    pagina_indice = achar_pagina_indice(paginas_limpas)
    outline = extrair_outline(caminho_pdf)

    # "curso" = caminho da pasta relativa à raiz indexada, ex:
    # "Estrategia/TI-Banco-de-Dados" — preserva sua organização por
    # concurso/tema em múltiplos níveis, não só o primeiro nível.
    caminho_relativo = caminho_pdf.relative_to(pasta_raiz)
    curso = str(caminho_relativo.parent) if caminho_relativo.parent != Path(".") else ""

    conn.execute("DELETE FROM arquivos WHERE caminho = ?", (str(caminho_pdf),))
    cur = conn.execute(
        """INSERT INTO arquivos
           (caminho, curso, nome_arquivo, n_paginas, tamanho_bytes, hash, mtime, pagina_indice, indexado_em)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            str(caminho_pdf), curso, caminho_pdf.name, len(paginas_limpas),
            stat.st_size, hash_arquivo(caminho_pdf), stat.st_mtime,
            pagina_indice, time.time(),
        ),
    )
    arquivo_id = cur.lastrowid

    for nivel, titulo, pagina in outline:
        conn.execute(
            "INSERT INTO bookmarks (arquivo_id, nivel, titulo, pagina) VALUES (?, ?, ?, ?)",
            (arquivo_id, nivel, titulo, pagina),
        )

    for i, texto in enumerate(paginas_limpas):
        conn.execute(
            "INSERT INTO paginas (arquivo_id, pagina, texto) VALUES (?, ?, ?)",
            (arquivo_id, i + 1, texto),
        )

    conn.commit()
    return len(paginas_limpas), len(outline)


def main():
    ap = argparse.ArgumentParser(description="Indexa apostilas PDF num SQLite com busca full-text.")
    ap.add_argument("pasta", help="Pasta raiz com os PDFs (varre recursivamente)")
    ap.add_argument("--db", default="indice.db", help="Caminho do banco SQLite (padrão: indice.db)")
    ap.add_argument("--forcar", action="store_true", help="Reindexa mesmo arquivos já indexados")
    args = ap.parse_args()

    pasta_raiz = Path(args.pasta).resolve()
    if not pasta_raiz.is_dir():
        print(f"Pasta não encontrada: {pasta_raiz}", file=sys.stderr)
        sys.exit(1)

    conn = conectar_db(args.db)

    pdfs = sorted(pasta_raiz.rglob("*.pdf"))
    print(f"Encontrados {len(pdfs)} PDFs em {pasta_raiz}")

    novos, pulados, erros = 0, 0, 0
    for i, caminho_pdf in enumerate(pdfs, 1):
        try:
            mtime = caminho_pdf.stat().st_mtime
            if not args.forcar and arquivo_ja_indexado(conn, caminho_pdf, mtime):
                pulados += 1
                continue
            n_pag, n_bookmarks = indexar_pdf(conn, caminho_pdf, pasta_raiz)
            novos += 1
            print(f"[{i}/{len(pdfs)}] OK  {caminho_pdf.name}  ({n_pag} pág, {n_bookmarks} bookmarks)")
        except Exception as e:
            erros += 1
            print(f"[{i}/{len(pdfs)}] ERRO {caminho_pdf.name}: {e}", file=sys.stderr)

    print(f"\nConcluído: {novos} indexados, {pulados} já em dia, {erros} com erro.")
    print(f"Banco: {Path(args.db).resolve()}")


if __name__ == "__main__":
    main()
