#!/usr/bin/env python3
"""
buscar_indice.py — Busca full-text no índice de apostilas.

Uso:
    python buscar_indice.py "window function"
    python buscar_indice.py "window function" --db indice.db --limite 15
    python buscar_indice.py "window function" --curso "banco-de-dados"
    python buscar_indice.py --listar-cursos

Saída: lista de (arquivo, página, trecho) ranqueada por relevância,
pra decidir rápido onde vale abrir o PDF de verdade.
"""

import argparse
import sqlite3
import sys
from pathlib import Path


def montar_query_fts(termo):
    """
    Transforma "window function" numa query FTS5 tipo:
    'window* OR function*' — cada palavra vira prefixo, pra pegar
    variações (singular/plural, conjugação) sem exigir match exato.
    """
    palavras = [p for p in termo.strip().split() if p]
    if not palavras:
        return None
    return " OR ".join(f'"{p}"*' for p in palavras)


def buscar(db_path, termo, limite=10, curso=None):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    query_fts = montar_query_fts(termo)
    if query_fts is None:
        return []

    sql = """
        SELECT
            a.nome_arquivo,
            a.caminho,
            a.curso,
            p.pagina,
            snippet(paginas_fts, 0, '>>>', '<<<', '...', 16) AS trecho,
            bm25(paginas_fts) AS score
        FROM paginas_fts
        JOIN paginas p ON p.id = paginas_fts.rowid
        JOIN arquivos a ON a.id = p.arquivo_id
        WHERE paginas_fts MATCH ?
    """
    params = [query_fts]
    if curso:
        sql += " AND a.curso LIKE ?"
        params.append(f"%{curso}%")

    sql += " ORDER BY score LIMIT ?"
    params.append(limite)

    return conn.execute(sql, params).fetchall()


def listar_cursos(db_path):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT curso, COUNT(*) as n FROM arquivos GROUP BY curso ORDER BY n DESC"
    ).fetchall()
    return rows


def main():
    ap = argparse.ArgumentParser(description="Busca full-text no índice de apostilas.")
    ap.add_argument("termo", nargs="?", help='Termo de busca, ex: "window function"')
    ap.add_argument("--db", default="indice.db", help="Caminho do banco SQLite")
    ap.add_argument("--limite", type=int, default=10, help="Máximo de resultados (padrão 10)")
    ap.add_argument("--curso", default=None, help="Filtra por pasta/curso (busca parcial)")
    ap.add_argument("--listar-cursos", action="store_true", help="Lista os cursos indexados")
    args = ap.parse_args()

    if not Path(args.db).exists():
        print(f"Banco não encontrado: {args.db}. Rode o indexador.py primeiro.", file=sys.stderr)
        sys.exit(1)

    if args.listar_cursos:
        for curso, n in listar_cursos(args.db):
            print(f"{n:5d}  {curso or '(raiz)'}")
        return

    if not args.termo:
        print("Informe um termo de busca ou use --listar-cursos.", file=sys.stderr)
        sys.exit(1)

    resultados = buscar(args.db, args.termo, args.limite, args.curso)

    if not resultados:
        print(f"Nada encontrado para: {args.termo!r}")
        print("Dica: tente reformular com sinônimos/termos relacionados antes de abrir PDFs.")
        return

    print(f"{len(resultados)} resultado(s) para {args.termo!r}:\n")
    for r in resultados:
        print(f"📄 {r['nome_arquivo']}  (pág. {r['pagina']})  [{r['curso'] or 'raiz'}]")
        print(f"   {r['trecho']}")
        print(f"   caminho: {r['caminho']}")
        print()


if __name__ == "__main__":
    main()
