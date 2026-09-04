#!/usr/bin/env python3
"""
canonizar_assuntos.py — Registro canônico de assuntos, compartilhado entre editais.

Uso:
    python canonizar_assuntos.py --buscar "normaliza" [--disciplina "Banco de Dados"]
    python canonizar_assuntos.py --listar [--edital SEFAZ-SC-2026]
    python canonizar_assuntos.py --adicionar-lote assuntos_bloco.json

Formato do JSON de --adicionar-lote (lista de objetos):
[
    {
        "disciplina": "Bancos de Dados e SQL",
        "assunto": "Entidades, chaves, integridade, normalização",
        "edital": "SEFAZ-SC-2026",
        "redacao": "Entidades, chaves, integridade, normalização, tratamento de nulos",
        "peso": "NAO_DETERMINADO",
        "paginas": "3-57",
        "referencia": "10-Área Fiscal\\22, aulas 04-05",
        "uuid_existente": null
    }
]
Campos obrigatórios: disciplina, assunto, edital, redacao. peso (padrão
NAO_DETERMINADO), paginas, referencia e uuid_existente são opcionais.

O que faz:
    Mantém um registro de "assunto canônico" (nome + disciplina + UUID estável) que
    atravessa múltiplos editais — a canonicalização em si (decidir se um assunto novo é o
    mesmo conceito de um edital anterior, só escrito diferente) é julgamento humano/IA
    feito na conversa; este script só guarda o resultado dessa decisão e serve de lookup
    rápido pra apoiar ela (--buscar). Ver docs/arquitetura-integracao-planejamento-sge.md,
    seção 5 e 6, pro desenho completo.

    Entrada é sempre por arquivo JSON (não por flag de linha de comando), mesmo padrão de
    anki_gerar.py/montar_dia.py: no Windows, argumentos de linha de comando com acento
    chegam corrompidos ao Python nesta configuração de terminal (decodificação cp1252 em
    vez de UTF-8) — ler de arquivo evita esse problema. --buscar aceita termo direto na
    linha de comando por ser só um atalho de consulta (não grava nada); se o termo tiver
    acento e vier vazio/estranho, refaça sem acento (ex: "normaliza" em vez de
    "normalização") ou rode com a variável de ambiente PYTHONUTF8=1.

    Item sem uuid_existente: cria um assunto canônico novo (ou reaproveita, silenciosamente,
    se já existir exatamente a mesma disciplina+nome — reexecução idempotente). Com
    uuid_existente: liga a origem/peso/ordem desse edital a um canônico que já existia, sem
    duplicar.

    peso/ordem/referência de material/volume são atributos POR EDITAL (tabela
    edital_assunto), não do assunto canônico — o mesmo assunto pode ter peso ALTO num
    edital e BAIXO em outro.
"""

import argparse
import json
import sqlite3
import sys
import time
import uuid
from pathlib import Path

PESOS_VALIDOS = {"ALTO", "MEDIO", "BAIXO", "NAO_DETERMINADO"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS assuntos_canonicos (
    uuid TEXT PRIMARY KEY,
    nome_canonico TEXT NOT NULL,
    disciplina TEXT NOT NULL,
    criado_em REAL,
    UNIQUE(disciplina, nome_canonico)
);

CREATE TABLE IF NOT EXISTS assunto_origens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assunto_uuid TEXT NOT NULL REFERENCES assuntos_canonicos(uuid),
    edital TEXT NOT NULL,
    redacao_original TEXT,
    UNIQUE(assunto_uuid, edital)
);

CREATE TABLE IF NOT EXISTS edital_assunto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    edital TEXT NOT NULL,
    assunto_uuid TEXT NOT NULL REFERENCES assuntos_canonicos(uuid),
    peso TEXT,
    ordem INTEGER,
    referencia_material TEXT,
    volume_paginas INTEGER,
    tempo_estimado_min INTEGER,
    UNIQUE(edital, assunto_uuid)
);
"""


def conectar_db(caminho_db):
    conn = sqlite3.connect(caminho_db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def contar_paginas(spec):
    """'3-50,60,70-72' -> 50 (quantidade de páginas, não a lista)."""
    total = 0
    for parte in spec.split(","):
        parte = parte.strip()
        if not parte:
            continue
        if "-" in parte:
            ini, fim = parte.split("-")
            total += int(fim) - int(ini) + 1
        else:
            total += 1
    return total


def buscar(conn, termo, disciplina=None):
    sql = """
        SELECT ac.uuid, ac.disciplina, ac.nome_canonico,
               GROUP_CONCAT(DISTINCT ao.edital) AS editais
        FROM assuntos_canonicos ac
        LEFT JOIN assunto_origens ao ON ao.assunto_uuid = ac.uuid
        WHERE (ac.nome_canonico LIKE ? OR ac.disciplina LIKE ?)
    """
    params = [f"%{termo}%", f"%{termo}%"]
    if disciplina:
        sql += " AND ac.disciplina LIKE ?"
        params.append(f"%{disciplina}%")
    sql += " GROUP BY ac.uuid ORDER BY ac.disciplina, ac.nome_canonico"
    return conn.execute(sql, params).fetchall()


def listar(conn, edital=None):
    sql = """
        SELECT ac.uuid, ac.disciplina, ac.nome_canonico,
               ea.edital, ea.peso, ea.ordem, ea.volume_paginas, ea.referencia_material
        FROM edital_assunto ea
        JOIN assuntos_canonicos ac ON ac.uuid = ea.assunto_uuid
    """
    params = []
    if edital:
        sql += " WHERE ea.edital = ?"
        params.append(edital)
    sql += " ORDER BY ea.edital, ea.ordem IS NULL, ea.ordem, ac.disciplina"
    return conn.execute(sql, params).fetchall()


def achar_por_nome(conn, disciplina, nome_canonico):
    row = conn.execute(
        "SELECT uuid FROM assuntos_canonicos WHERE disciplina = ? AND nome_canonico = ?",
        (disciplina, nome_canonico),
    ).fetchone()
    return row[0] if row else None


def adicionar(conn, disciplina, assunto, edital, redacao, peso, paginas, referencia, uuid_existente):
    if peso not in PESOS_VALIDOS:
        raise ValueError(f"peso inválido {peso!r} (use: {PESOS_VALIDOS})")

    if uuid_existente:
        row = conn.execute(
            "SELECT uuid FROM assuntos_canonicos WHERE uuid = ?", (uuid_existente,)
        ).fetchone()
        if row is None:
            raise ValueError(f"--uuid-existente {uuid_existente!r} não encontrado em assuntos_canonicos")
        assunto_uuid = uuid_existente
        criado = False
    else:
        assunto_uuid = achar_por_nome(conn, disciplina, assunto)
        if assunto_uuid:
            criado = False
        else:
            assunto_uuid = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO assuntos_canonicos (uuid, nome_canonico, disciplina, criado_em) VALUES (?, ?, ?, ?)",
                (assunto_uuid, assunto, disciplina, time.time()),
            )
            criado = True

    conn.execute(
        """INSERT INTO assunto_origens (assunto_uuid, edital, redacao_original)
           VALUES (?, ?, ?)
           ON CONFLICT(assunto_uuid, edital) DO UPDATE SET redacao_original = excluded.redacao_original""",
        (assunto_uuid, edital, redacao),
    )

    volume_paginas = contar_paginas(paginas) if paginas else None
    conn.execute(
        """INSERT INTO edital_assunto (edital, assunto_uuid, peso, referencia_material, volume_paginas)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(edital, assunto_uuid) DO UPDATE SET
               peso = excluded.peso,
               referencia_material = excluded.referencia_material,
               volume_paginas = excluded.volume_paginas""",
        (edital, assunto_uuid, peso, referencia, volume_paginas),
    )
    conn.commit()
    return assunto_uuid, criado


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Registro canônico de assuntos, compartilhado entre editais.")
    ap.add_argument("--db", default="canonico.db", help="Caminho do banco SQLite (padrão: canonico.db)")

    ap.add_argument("--buscar", metavar="TERMO", help="Busca assuntos canônicos parecidos (LIKE)")
    ap.add_argument("--disciplina", help="Filtra --buscar/--listar, ou define a disciplina em --adicionar")

    ap.add_argument("--listar", action="store_true", help="Lista o que já está registrado")
    ap.add_argument("--edital", help="Filtra --listar")

    ap.add_argument("--adicionar-lote", metavar="ARQUIVO.json",
                     help="Cria/atualiza assuntos canônicos a partir de um JSON (ver docstring)")

    args = ap.parse_args()
    conn = conectar_db(args.db)

    if args.buscar:
        resultados = buscar(conn, args.buscar, args.disciplina)
        if not resultados:
            print(f"Nada encontrado para: {args.buscar!r}")
            return
        print(f"{len(resultados)} candidato(s) pra {args.buscar!r}:\n")
        for r in resultados:
            print(f"  {r['uuid']}  [{r['disciplina']}] {r['nome_canonico']}")
            print(f"    já usado em: {r['editais'] or '(nenhum edital ainda)'}")
        return

    if args.listar:
        linhas = listar(conn, args.edital)
        if not linhas:
            print("Nada registrado ainda.")
            return
        for r in linhas:
            ordem = r["ordem"] if r["ordem"] is not None else "-"
            vol = r["volume_paginas"] if r["volume_paginas"] is not None else "-"
            print(f"[{r['edital']}] #{ordem}  {r['peso']:<15} vol={vol:<4} [{r['disciplina']}] {r['nome_canonico']}")
            print(f"    uuid={r['uuid']}  ref={r['referencia_material'] or '-'}")
        return

    if args.adicionar_lote:
        with open(args.adicionar_lote, encoding="utf-8") as f:
            itens = json.load(f)

        criados, atualizados, erros = 0, 0, 0
        for i, item in enumerate(itens):
            faltando = [n for n in ("disciplina", "assunto", "edital", "redacao") if not item.get(n)]
            if faltando:
                print(f"[{i}] ERRO: faltando {', '.join(faltando)}", file=sys.stderr)
                erros += 1
                continue
            try:
                assunto_uuid, criado = adicionar(
                    conn, item["disciplina"], item["assunto"], item["edital"], item["redacao"],
                    item.get("peso", "NAO_DETERMINADO"), item.get("paginas"),
                    item.get("referencia"), item.get("uuid_existente"),
                )
            except ValueError as e:
                print(f"[{i}] ERRO: {e}", file=sys.stderr)
                erros += 1
                continue
            if criado:
                criados += 1
            else:
                atualizados += 1
            acao = "criado" if criado else "atualizado/reaproveitado"
            print(f"[{i}] {acao}: {assunto_uuid}  [{item['disciplina']}] {item['assunto']}")

        print(f"\n{criados} criado(s), {atualizados} atualizado(s)/reaproveitado(s), {erros} erro(s).")
        if erros:
            sys.exit(1)
        return

    print("Informe --buscar, --listar ou --adicionar-lote.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
