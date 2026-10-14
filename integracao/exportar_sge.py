#!/usr/bin/env python3
"""
exportar_sge.py — Gera a pasta de importação de um edital pro SGE-Concursos.

Uso:
    python exportar_sge.py --edital SEFAZ-SC-2026 --nome "SEFAZ SC 2026" \\
        --data-prova 2026-11-22 --saida-dir SGE-Importacao/sefaz-sc-2026

A pasta de saída é a pasta do concurso dentro de `SGE-Importacao/` no Google Drive
(ADR-037 e ADR-039 do SGE). O nome dela é o slug que o SGE usa em `CONCURSO_ATIVO`.
Três arquivos, no formato que o SGE define (`especificacao/02_JORNADAS.md` J-1 do
SGE-Concursos — o contrato é do lado que consome; ver
docs/arquitetura-integracao-planejamento-sge.md §8.1):

assuntos.csv
    disciplina,assunto,peso,ordem,chaveExterna
    `chaveExterna` = uuid do assunto canônico. Sem coluna `id`: o SGE reimporta pela
    chaveExterna (atualiza peso/ordem/nome, mantém escada e histórico). Peso
    NAO_DETERMINADO sai vazio — o SGE trata vazio como MEDIO; "não determinado" seria
    recusado.

segmentos.csv  (só se algum assunto tiver pedaços de material registrados)
    chaveExternaSegmento,chaveExternaAssunto,ordem,arquivo,paginaInicial,paginaFinal,tempoEstimadoMin
    `arquivo` tem que ser o link compartilhável do Drive (CLAUDE.md, fluxo de PDF por
    bloco) — caminho local gera aviso, porque o SGE só guarda e exibe o texto.

concurso.json
    {"slug", "nome", "dataProva"} — o SGE guarda para o diagnóstico de edital e o modo
    reta final; ainda não lê.

Rode calcular_orcamento.py antes, pra popular `ordem` — exportar sem isso ainda funciona,
mas o SGE numera na ordem do arquivo e um aviso é impresso.
"""

import argparse
import csv
import json
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

CAMPOS_ASSUNTOS = ["disciplina", "assunto", "peso", "ordem", "chaveExterna"]
CAMPOS_SEGMENTOS = ["chaveExternaSegmento", "chaveExternaAssunto", "ordem", "arquivo",
                    "paginaInicial", "paginaFinal", "tempoEstimadoMin"]
PESOS_SGE = {"ALTO", "MEDIO", "BAIXO"}


def conectar_db(caminho_db):
    conn = sqlite3.connect(caminho_db)
    conn.row_factory = sqlite3.Row
    return conn


def carregar_export(conn, edital):
    sql = """
        SELECT ea.id AS edital_assunto_id, ac.uuid, ac.disciplina, ac.nome_canonico AS assunto,
               ea.peso, ea.ordem
        FROM edital_assunto ea
        JOIN assuntos_canonicos ac ON ac.uuid = ea.assunto_uuid
        WHERE ea.edital = ?
        ORDER BY ea.ordem IS NULL, ea.ordem, ac.disciplina, ac.nome_canonico
    """
    return conn.execute(sql, (edital,)).fetchall()


def carregar_pedacos(conn, edital_assunto_id):
    sql = """
        SELECT ordem, arquivo, pagina_inicial, pagina_final, tempo_estimado_min,
               chave_externa_segmento
        FROM material_pedacos
        WHERE edital_assunto_id = ?
        ORDER BY ordem
    """
    return conn.execute(sql, (edital_assunto_id,)).fetchall()


def peso_sge(peso):
    """NAO_DETERMINADO (ou vazio) vira vazio — o SGE assume MEDIO, nunca recusa."""
    return peso if peso in PESOS_SGE else ""


def eh_link(arquivo):
    return bool(re.match(r"^https?://", arquivo or ""))


def montar_linhas(conn, edital):
    """Devolve (linhas_assuntos, linhas_segmentos, avisos). Lança ValueError em erro que
    o SGE recusaria de qualquer jeito — melhor falhar aqui do que lá, em silêncio."""
    linhas = carregar_export(conn, edital)
    if not linhas:
        raise ValueError(f"Nenhum assunto registrado pro edital {edital!r} em canonico.db")

    assuntos, segmentos, avisos = [], [], []
    sem_ordem = 0
    for l in linhas:
        if l["ordem"] is None:
            sem_ordem += 1
        assuntos.append({
            "disciplina": l["disciplina"],
            "assunto": l["assunto"],
            "peso": peso_sge(l["peso"]),
            "ordem": "" if l["ordem"] is None else l["ordem"],
            "chaveExterna": l["uuid"],
        })
        for p in carregar_pedacos(conn, l["edital_assunto_id"]):
            if not p["chave_externa_segmento"]:
                raise ValueError(
                    f"Pedaço {p['ordem']} de {l['assunto']!r} sem chave_externa_segmento — "
                    f"o SGE exige (D-53). Regere com dias/montar_bloco.py.")
            if not eh_link(p["arquivo"]):
                avisos.append(f"{l['assunto']!r} pedaço {p['ordem']}: 'arquivo' não é link "
                              f"({p['arquivo']}) — suba no Drive e atualize antes de importar.")
            segmentos.append({
                "chaveExternaSegmento": p["chave_externa_segmento"],
                "chaveExternaAssunto": l["uuid"],
                "ordem": p["ordem"],
                "arquivo": p["arquivo"],
                "paginaInicial": "" if p["pagina_inicial"] is None else p["pagina_inicial"],
                "paginaFinal": "" if p["pagina_final"] is None else p["pagina_final"],
                "tempoEstimadoMin": "" if p["tempo_estimado_min"] is None else p["tempo_estimado_min"],
            })
    if sem_ordem:
        avisos.append(f"{sem_ordem} assunto(s) sem ordem definida — rode calcular_orcamento.py "
                      f"antes de importar no SGE.")
    return assuntos, segmentos, avisos


def escrever_csv(caminho, campos, linhas):
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas)


def exportar(conn, edital, saida_dir, nome, data_prova):
    assuntos, segmentos, avisos = montar_linhas(conn, edital)

    saida_dir = Path(saida_dir)
    saida_dir.mkdir(parents=True, exist_ok=True)
    escrever_csv(saida_dir / "assuntos.csv", CAMPOS_ASSUNTOS, assuntos)
    caminho_segmentos = saida_dir / "segmentos.csv"
    if segmentos:
        escrever_csv(caminho_segmentos, CAMPOS_SEGMENTOS, segmentos)
    elif caminho_segmentos.exists():
        caminho_segmentos.unlink()  # sobra de exportação anterior apontaria pra pedaços que não existem mais

    concurso = {"slug": saida_dir.name, "nome": nome, "dataProva": data_prova}
    with open(saida_dir / "concurso.json", "w", encoding="utf-8") as f:
        json.dump(concurso, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return len(assuntos), len(segmentos), avisos


def validar_data(texto):
    if texto is None:
        return None
    try:
        return date.fromisoformat(texto).isoformat()
    except ValueError:
        raise argparse.ArgumentTypeError(f"data inválida (use AAAA-MM-DD): {texto}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Gera a pasta de importação de um edital pro SGE-Concursos.")
    ap.add_argument("--db", default="canonico.db", help="Caminho do banco SQLite (padrão: canonico.db)")
    ap.add_argument("--edital", required=True, help="Edital a exportar")
    ap.add_argument("--saida-dir", required=True,
                    help="Pasta do concurso (o nome dela é o slug usado em CONCURSO_ATIVO no SGE)")
    ap.add_argument("--nome", required=True, help="Nome de exibição do concurso")
    ap.add_argument("--data-prova", type=validar_data, default=None,
                    help="Data da prova, AAAA-MM-DD (omita se ainda não saiu)")
    args = ap.parse_args()

    conn = conectar_db(args.db)
    try:
        n_assuntos, n_segmentos, avisos = exportar(conn, args.edital, args.saida_dir, args.nome, args.data_prova)
    except ValueError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Exportado em {args.saida_dir}: {n_assuntos} assunto(s), {n_segmentos} segmento(s)")
    for aviso in avisos:
        print(f"AVISO: {aviso}", file=sys.stderr)


if __name__ == "__main__":
    main()
