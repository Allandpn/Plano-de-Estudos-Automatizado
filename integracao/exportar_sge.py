#!/usr/bin/env python3
"""
exportar_sge.py — Gera o CSV de um edital pra importar no SGE-Concursos.

Uso:
    python exportar_sge.py --edital SEFAZ-SC-2026 --saida sefaz_sc_2026.csv

Formato de saída (ver docs/arquitetura-integracao-planejamento-sge.md, seção 8):
    uuid,disciplina,assunto,edital,peso,ordem,referencia_material

`uuid` vem sempre preenchido (identidade estável do assunto canônico, mintada em
canonizar_assuntos.py) — o import no SGE é sempre upsert por esse uuid, nunca
"criar quando vazio".

Rode calcular_orcamento.py antes, pra popular `ordem` — exportar sem isso ainda funciona,
mas o CSV sai com ordem vazia e um aviso é impresso.
"""

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

CAMPOS = ["uuid", "disciplina", "assunto", "edital", "peso", "ordem", "referencia_material"]


def conectar_db(caminho_db):
    conn = sqlite3.connect(caminho_db)
    conn.row_factory = sqlite3.Row
    return conn


def carregar_export(conn, edital):
    sql = """
        SELECT ac.uuid, ac.disciplina, ac.nome_canonico AS assunto,
               ea.edital, ea.peso, ea.ordem, ea.referencia_material
        FROM edital_assunto ea
        JOIN assuntos_canonicos ac ON ac.uuid = ea.assunto_uuid
        WHERE ea.edital = ?
        ORDER BY ea.ordem IS NULL, ea.ordem, ac.disciplina, ac.nome_canonico
    """
    return conn.execute(sql, (edital,)).fetchall()


def exportar(conn, edital, saida_path):
    linhas = carregar_export(conn, edital)
    if not linhas:
        raise ValueError(f"Nenhum assunto registrado pro edital {edital!r} em canonico.db")

    sem_ordem = [l for l in linhas if l["ordem"] is None]

    saida_path = Path(saida_path)
    saida_path.parent.mkdir(parents=True, exist_ok=True)
    with open(saida_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS)
        writer.writeheader()
        for l in linhas:
            writer.writerow({campo: (l[campo] if l[campo] is not None else "") for campo in CAMPOS})

    return len(linhas), len(sem_ordem)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Gera o CSV de um edital pra importar no SGE-Concursos.")
    ap.add_argument("--db", default="canonico.db", help="Caminho do banco SQLite (padrão: canonico.db)")
    ap.add_argument("--edital", required=True, help="Edital a exportar")
    ap.add_argument("--saida", required=True, help="Caminho do CSV de saída")
    args = ap.parse_args()

    conn = conectar_db(args.db)
    try:
        n, n_sem_ordem = exportar(conn, args.edital, args.saida)
    except ValueError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Exportado: {args.saida}  ({n} assunto(s))")
    if n_sem_ordem:
        print(f"AVISO: {n_sem_ordem} assunto(s) sem ordem definida — "
              f"rode calcular_orcamento.py antes de importar no SGE.", file=sys.stderr)


if __name__ == "__main__":
    main()
