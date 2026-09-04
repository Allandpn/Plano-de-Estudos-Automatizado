#!/usr/bin/env python3
"""
calcular_orcamento.py — Orçamento determinístico de tempo/ordem por edital.

Uso:
    python calcular_orcamento.py --edital SEFAZ-SC-2026 --dias 60 --minutos-dia 120
    python calcular_orcamento.py --edital SEFAZ-SC-2026 --dias 60 --minutos-dia 120 --minutos-pagina 5

O que faz:
    Pra cada assunto já registrado em canonico.db (via canonizar_assuntos.py --adicionar)
    pro edital informado:
        1. tempo_necessario = volume_paginas × minutos_pagina — tempo real de leitura,
           não é "esticado" nem "encolhido" por peso. Peso não muda quantos minutos um
           assunto leva pra ler, só a prioridade de quem estuda primeiro / quem é
           candidato a corte.
        2. ordem = ordenado por peso desc (ALTO > MEDIO > NAO_DETERMINADO > BAIXO), depois
           por nome, dentro do mesmo peso.
        3. Se o total necessário couber no tempo disponível (dias × minutos-dia), grava
           tempo_estimado_min = tempo_necessario pra cada assunto — cobertura completa.
        4. Se estourar, NÃO decide sozinho o que cortar — grava tempo_estimado_min mesmo
           assim (valor de referência, sem compressão) e imprime um relatório de estouro,
           com os assuntos de menor peso destacados como candidatos a corte, pra decisão
           humana/IA na conversa (ver docs/arquitetura-integracao-planejamento-sge.md,
           seção 6).

    Assuntos sem volume_paginas definido (não foi passado --paginas no --adicionar) ficam
    de fora do cálculo de tempo, mas ainda recebem ordem — o relatório avisa quais são.
"""

import argparse
import sqlite3
import sys

PESO_PRIORIDADE = {"ALTO": 0, "MEDIO": 1, "NAO_DETERMINADO": 2, "BAIXO": 3}
MINUTOS_PAGINA_PADRAO = 4


def conectar_db(caminho_db):
    conn = sqlite3.connect(caminho_db)
    conn.row_factory = sqlite3.Row
    return conn


def carregar_assuntos(conn, edital):
    sql = """
        SELECT ea.id, ea.assunto_uuid, ea.peso, ea.volume_paginas,
               ac.disciplina, ac.nome_canonico
        FROM edital_assunto ea
        JOIN assuntos_canonicos ac ON ac.uuid = ea.assunto_uuid
        WHERE ea.edital = ?
    """
    return conn.execute(sql, (edital,)).fetchall()


def calcular(conn, edital, dias, minutos_dia, minutos_pagina):
    assuntos = carregar_assuntos(conn, edital)
    if not assuntos:
        raise ValueError(f"Nenhum assunto registrado pro edital {edital!r} em canonico.db")

    com_volume = [a for a in assuntos if a["volume_paginas"] is not None]
    sem_volume = [a for a in assuntos if a["volume_paginas"] is None]

    ordenados = sorted(
        assuntos,
        key=lambda a: (PESO_PRIORIDADE.get(a["peso"], 2), a["nome_canonico"]),
    )

    tempo_disponivel = dias * minutos_dia
    tempo_necessario_por_assunto = {
        a["id"]: a["volume_paginas"] * minutos_pagina for a in com_volume
    }
    tempo_total_necessario = sum(tempo_necessario_por_assunto.values())

    for i, a in enumerate(ordenados, 1):
        tempo_estimado = tempo_necessario_por_assunto.get(a["id"])
        conn.execute(
            "UPDATE edital_assunto SET ordem = ?, tempo_estimado_min = ? WHERE id = ?",
            (i, tempo_estimado, a["id"]),
        )
    conn.commit()

    return {
        "ordenados": ordenados,
        "sem_volume": sem_volume,
        "tempo_disponivel": tempo_disponivel,
        "tempo_total_necessario": tempo_total_necessario,
        "estourou": tempo_total_necessario > tempo_disponivel,
    }


def imprimir_relatorio(resultado, edital):
    print(f"Edital: {edital}")
    print(f"Tempo disponível: {resultado['tempo_disponivel']} min")
    print(f"Tempo necessário (assuntos com volume definido): {resultado['tempo_total_necessario']} min\n")

    print("Ordem de estudo:")
    for a in resultado["ordenados"]:
        vol = a["volume_paginas"] if a["volume_paginas"] is not None else "?"
        print(f"  [{a['peso']:<15}] [{a['disciplina']}] {a['nome_canonico']}  (vol={vol} pág)")

    if resultado["sem_volume"]:
        print(f"\n{len(resultado['sem_volume'])} assunto(s) sem volume_paginas definido — "
              f"fora do cálculo de tempo, receberam ordem mas não tempo_estimado_min:")
        for a in resultado["sem_volume"]:
            print(f"  [{a['disciplina']}] {a['nome_canonico']}")

    if resultado["estourou"]:
        excesso = resultado["tempo_total_necessario"] - resultado["tempo_disponivel"]
        print(f"\nESTOURO: {excesso} min além do disponível. Não foi feito corte automático.")
        print("Candidatos a corte/compressão, do menor peso pro maior (decidir na conversa):")
        for a in sorted(
            (a for a in resultado["ordenados"] if a["volume_paginas"] is not None),
            key=lambda a: -PESO_PRIORIDADE.get(a["peso"], 2),
        ):
            print(f"  [{a['peso']:<15}] [{a['disciplina']}] {a['nome_canonico']}")
    else:
        print("\nCobertura completa: o tempo disponível comporta todo o conteúdo com volume definido.")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Orçamento determinístico de tempo/ordem por edital.")
    ap.add_argument("--db", default="canonico.db", help="Caminho do banco SQLite (padrão: canonico.db)")
    ap.add_argument("--edital", required=True, help="Edital a calcular")
    ap.add_argument("--dias", type=int, required=True, help="Dias disponíveis até a prova")
    ap.add_argument("--minutos-dia", type=int, required=True, help="Minutos de estudo por dia")
    ap.add_argument("--minutos-pagina", type=float, default=MINUTOS_PAGINA_PADRAO,
                     help=f"Minutos estimados de leitura por página (padrão: {MINUTOS_PAGINA_PADRAO})")
    args = ap.parse_args()

    conn = conectar_db(args.db)
    try:
        resultado = calcular(conn, args.edital, args.dias, args.minutos_dia, args.minutos_pagina)
    except ValueError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)

    imprimir_relatorio(resultado, args.edital)


if __name__ == "__main__":
    main()
