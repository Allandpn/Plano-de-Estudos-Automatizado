#!/usr/bin/env python3
"""
anki_gerar.py — Converte um rascunho de cards (JSON) num CSV pronto pra
importar no Anki, respeitando as regras de note-type do método:
    - "cloze"          -> leis, classificações, decoreba (completar lacuna)
    - "basic"          -> "quando usar X em vez de Y" (conceitos técnicos)
    - "basic_reversed" -> sigla <-> significado

Uso:
    python anki_gerar.py cards_bloco.json --saida deck_bloco.csv --deck "SEFAZ SC::Trilha 1 - Dados::SQL-BD"

Formato do JSON de entrada:
[
    {"tipo": "basic", "frente": "Quando usar EXISTS em vez de IN?",
     "verso": "Quando a subconsulta pode retornar muitas linhas e você só precisa checar existência — EXISTS para no primeiro match."},
    {"tipo": "cloze", "texto": "O teorema {{c1::CAP}} diz que um sistema distribuído só pode garantir 2 de 3: {{c1::Consistência}}, {{c1::Disponibilidade}} e {{c1::Tolerância a Partição}}."},
    {"tipo": "basic_reversed", "frente": "ACID", "verso": "Atomicidade, Consistência, Isolamento, Durabilidade"}
]

O CSV gerado usa o formato de importação em texto plano do Anki
(campos separados por tab, primeira linha com #separator e #notetype
como comentários que o Anki reconhece na tela de importação).
"""

import argparse
import csv
import json
import sys
from pathlib import Path


TIPOS_VALIDOS = {"basic", "cloze", "basic_reversed"}


def validar_card(card, i):
    tipo = card.get("tipo")
    if tipo not in TIPOS_VALIDOS:
        raise ValueError(f"Card {i}: tipo inválido {tipo!r} (use: {TIPOS_VALIDOS})")

    if tipo == "cloze":
        if "texto" not in card or "{{c" not in card.get("texto", ""):
            raise ValueError(f"Card {i}: cloze precisa de 'texto' com marcação {{{{c1::...}}}}")
    else:
        if not card.get("frente") or not card.get("verso"):
            raise ValueError(f"Card {i}: tipo {tipo!r} precisa de 'frente' e 'verso'")


def gerar_csv(cards, saida_path, deck):
    saida_path = Path(saida_path)
    saida_path.parent.mkdir(parents=True, exist_ok=True)

    linhas_basic = []
    linhas_basic_rev = []
    linhas_cloze = []

    for i, card in enumerate(cards):
        validar_card(card, i)
        tipo = card["tipo"]
        tags = card.get("tags", "")
        if tipo == "basic":
            linhas_basic.append([card["frente"], card["verso"], tags])
        elif tipo == "basic_reversed":
            linhas_basic_rev.append([card["frente"], card["verso"], tags])
        elif tipo == "cloze":
            linhas_cloze.append([card["texto"], card.get("extra", ""), tags])

    arquivos_gerados = []

    def escrever(sufixo, notetype, linhas, cabecalho):
        if not linhas:
            return
        caminho = saida_path.with_name(f"{saida_path.stem}_{sufixo}{saida_path.suffix}")
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write("#separator:tab\n")
            f.write(f"#notetype:{notetype}\n")
            f.write(f"#deck:{deck}\n")
            f.write("#tags column:3\n")
            writer = csv.writer(f, delimiter="\t")
            for linha in linhas:
                writer.writerow(linha)
        arquivos_gerados.append((caminho, len(linhas)))

    escrever("basic", "Basic", linhas_basic, ["Frente", "Verso", "Tags"])
    escrever("basic_reversed", "Basic (and reversed card)", linhas_basic_rev, ["Frente", "Verso", "Tags"])
    escrever("cloze", "Cloze", linhas_cloze, ["Texto", "Extra", "Tags"])

    return arquivos_gerados


def main():
    ap = argparse.ArgumentParser(description="Gera CSV de cards Anki a partir de um rascunho JSON.")
    ap.add_argument("entrada", help="JSON com a lista de cards")
    ap.add_argument("--saida", required=True, help="Caminho base do CSV de saída (um arquivo por tipo de note)")
    ap.add_argument("--deck", required=True, help='Nome do deck, ex: "SEFAZ SC::Trilha 1 - Dados::SQL-BD"')
    args = ap.parse_args()

    with open(args.entrada, encoding="utf-8") as f:
        cards = json.load(f)

    try:
        arquivos = gerar_csv(cards, args.saida, args.deck)
    except ValueError as e:
        print(f"Erro de validação: {e}", file=sys.stderr)
        sys.exit(1)

    if not arquivos:
        print("Nenhum card válido encontrado.", file=sys.stderr)
        sys.exit(1)

    print(f"{len(cards)} card(s) processado(s):")
    for caminho, n in arquivos:
        print(f"  {caminho}  ({n} cards) — importar no Anki: File > Import")


if __name__ == "__main__":
    main()
