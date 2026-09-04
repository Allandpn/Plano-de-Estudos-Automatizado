#!/usr/bin/env python3
"""
montar_dia.py — Monta um PDF único pro dia de estudo, mesclando páginas
de várias apostilas na ordem de leitura sugerida, com capa de
rastreabilidade (mapeia cada trecho de volta ao arquivo/página original).

Uso:
    python montar_dia.py manifesto_dia.json --saida 2026-09-16.pdf

Formato do manifesto (JSON):
{
    "titulo": "Qua 16/09 — Transações, SGBDs, NoSQL/MongoDB",
    "fontes": [
        {"arquivo": "apostilas/aula_04.pdf", "paginas": "3-33", "rotulo": "Otimização (Aula 04 nova)"},
        {"arquivo": "apostilas/aula_07.pdf", "paginas": "3-29", "rotulo": "MySQL (Aula 07 nova)"},
        {"arquivo": "apostilas/aula_08.pdf", "paginas": "3-24", "rotulo": "PostgreSQL (Aula 08 nova)"}
    ]
}

"paginas" aceita: "3-33" (intervalo), "5" (página única), "3-10,15,20-22" (misto).
As páginas são copiadas como estão (imagem/diagrama incluído) — não há
reextração de texto aqui, só cópia de página, que é uma operação segura.
"""

import argparse
import json
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors


def parse_paginas(spec):
    """'3-10,15,20-22' -> [3,4,...,10,15,20,21,22] (1-indexed, como o usuário vê)."""
    paginas = []
    for parte in spec.split(","):
        parte = parte.strip()
        if "-" in parte:
            ini, fim = parte.split("-")
            paginas.extend(range(int(ini), int(fim) + 1))
        else:
            paginas.append(int(parte))
    return paginas


def gerar_capa(caminho_capa, titulo, mapa_rastreio):
    """Gera um PDF de capa listando de onde veio cada trecho (rastreabilidade)."""
    doc = SimpleDocTemplate(str(caminho_capa), pagesize=A4,
                             topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle("TituloDia", parent=styles["Title"], fontSize=16)
    corpo_style = styles["Normal"]

    story = [
        Paragraph(titulo, titulo_style),
        Spacer(1, 12),
        Paragraph("Sumário de fontes (rastreabilidade) — página mesclada → origem original:", corpo_style),
        Spacer(1, 10),
    ]

    dados_tabela = [["Pág. neste PDF", "Arquivo original", "Pág. original", "Seção"]]
    for item in mapa_rastreio:
        dados_tabela.append([
            str(item["pagina_mesclada"]),
            item["arquivo"],
            str(item["pagina_original"]),
            item["rotulo"],
        ])

    tabela = Table(dados_tabela, colWidths=[3*cm, 6*cm, 3*cm, 5*cm], repeatRows=1)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a2f8f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f0")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(tabela)

    doc.build(story)


def montar_dia(manifesto_path, saida_path):
    with open(manifesto_path, encoding="utf-8") as f:
        manifesto = json.load(f)

    titulo = manifesto.get("titulo", "Sessão de estudo")
    fontes = manifesto["fontes"]

    writer = PdfWriter()
    mapa_rastreio = []
    pagina_mesclada_atual = 1  # a capa vai ocupar a página 1, conteúdo começa na 2

    manifesto_dir = Path(manifesto_path).resolve().parent

    for fonte in fontes:
        arquivo = (manifesto_dir / fonte["arquivo"]).resolve() if not Path(fonte["arquivo"]).is_absolute() else Path(fonte["arquivo"])
        if not arquivo.exists():
            print(f"AVISO: arquivo não encontrado, pulando: {arquivo}", file=sys.stderr)
            continue

        reader = PdfReader(str(arquivo))
        paginas_1idx = parse_paginas(fonte["paginas"])

        for p in paginas_1idx:
            idx0 = p - 1
            if idx0 < 0 or idx0 >= len(reader.pages):
                print(f"AVISO: página {p} fora do intervalo em {arquivo.name} ({len(reader.pages)} págs)", file=sys.stderr)
                continue
            writer.add_page(reader.pages[idx0])
            pagina_mesclada_atual += 1
            mapa_rastreio.append({
                "pagina_mesclada": pagina_mesclada_atual,
                "arquivo": arquivo.name,
                "pagina_original": p,
                "rotulo": fonte.get("rotulo", ""),
            })

    if len(writer.pages) == 0:
        print("Nenhuma página válida encontrada — nada foi gerado.", file=sys.stderr)
        sys.exit(1)

    saida_path = Path(saida_path)
    saida_path.parent.mkdir(parents=True, exist_ok=True)

    capa_tmp = saida_path.with_suffix(".capa.tmp.pdf")
    gerar_capa(capa_tmp, titulo, mapa_rastreio)

    writer_final = PdfWriter()
    capa_reader = PdfReader(str(capa_tmp))
    for pg in capa_reader.pages:
        writer_final.add_page(pg)
    for pg in writer.pages:
        writer_final.add_page(pg)

    with open(saida_path, "wb") as f:
        writer_final.write(f)

    capa_tmp.unlink(missing_ok=True)

    print(f"Gerado: {saida_path}  ({len(writer_final.pages)} páginas, {len(mapa_rastreio)} páginas de conteúdo de {len(fontes)} fonte(s))")
    return saida_path


def main():
    ap = argparse.ArgumentParser(description="Monta o PDF mesclado de um dia de estudo.")
    ap.add_argument("manifesto", help="Caminho do manifesto JSON")
    ap.add_argument("--saida", required=True, help="Caminho do PDF de saída")
    args = ap.parse_args()
    montar_dia(args.manifesto, args.saida)


if __name__ == "__main__":
    main()
