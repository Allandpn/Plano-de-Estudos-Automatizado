#!/usr/bin/env python3
"""
montar_bloco.py — Fatia o material de um assunto em pedaços de leitura de tempo
aproximadamente igual (~45-75min, "bloco de conteúdo" no vocabulário do SGE), em vez de
um PDF por dia de calendário como `montar_dia.py`. Ver
docs/requisitos-alinhamento-fatiamento-pdf-bloco.md pro motivo dessa divisão.

Uso:
    python montar_bloco.py manifesto_assunto.json --saida-dir dias/

Formato do manifesto (JSON):
{
    "assunto_uuid": "2f6e...",
    "edital": "SEFAZ-SC-2026",
    "titulo": "Governança e Qualidade de Dados",
    "minutos_por_pagina": 4,
    "minutos_por_bloco": 60,
    "fontes": [
        {"arquivo": "apostilas/aula_04.pdf", "paginas": "3-33", "rotulo": "Otimização (Aula 04 nova)"}
    ]
}

"paginas" aceita o mesmo formato de montar_dia.py: "3-33", "5", "3-10,15,20-22".
"minutos_por_pagina"/"minutos_por_bloco" são opcionais (default 4 e 60 — meio-termo do
45-75min que o SGE já usa como ponto de partida pro bloco de conteúdo). O corte é
determinístico: percorre as páginas de todas as fontes, na ordem, e fecha um pedaço sempre
que o tempo acumulado cruza minutos_por_bloco.

Saída, em <saida-dir>:
    blocos/<assunto-slug>/segmento-01.pdf, segmento-02.pdf, ...  (mesma capa de
        rastreabilidade que montar_dia.py gera, uma por segmento) — layout combinado
        com o SGE pra sincronização via Google Drive/rclone, ver
        docs/requisitos-alinhamento-fatiamento-pdf-bloco.md seção 5
    <assunto-slug>_pedacos.json — lista ordenada (ordem, caminho local do segmento
        relativo a <saida-dir>, página inicial/final originais, tempo estimado,
        chave_externa_segmento) pra alimentar
        `integracao/canonizar_assuntos.py --adicionar-pedacos`. O campo
        "arquivo" é local até o upload pro Drive — depois de compartilhar cada PDF,
        troque manualmente pelo link antes de rodar exportar_sge.py.

Nenhum pedaço/segmento é datado — não há "dia" nesse fluxo, só ordem. Quem decide
quando o candidato consome cada um é a escada do SGE.

Identidade de segmento (ver docs/requisitos-alinhamento-fatiamento-pdf-bloco.md §8):
cada pedaço ganha um `chave_externa_segmento` (UUID) na primeira vez que é gerado.
Reexecuções pro mesmo assunto reaproveitam a mesma chave pro pedaço que cobre exatamente
o mesmo conjunto de páginas (arquivo + página original), mesmo que a posição/ordem mude —
o "fingerprint" de páginas de cada pedaço anterior fica salvo no próprio
<assunto-slug>_pedacos.json e é lido de volta na próxima execução. Só ganha chave nova o
pedaço cujo conjunto de páginas realmente mudou (conteúdo novo).
"""

import argparse
import hashlib
import json
import re
import sys
import unicodedata
import uuid
from pathlib import Path

from pypdf import PdfReader, PdfWriter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from montar_dia import parse_paginas, gerar_capa  # noqa: E402

MINUTOS_POR_PAGINA_PADRAO = 4
MINUTOS_POR_BLOCO_PADRAO = 60


def slugificar(texto):
    """'Governança e Qualidade de Dados' -> 'governanca-e-qualidade-de-dados'."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", sem_acento).strip("-").lower()
    return slug or "assunto"


def coletar_paginas(fontes, manifesto_dir):
    """Achata todas as fontes numa lista única de páginas na ordem de leitura, cada uma
    carregando de onde veio (arquivo, página original, rótulo)."""
    paginas = []
    for fonte in fontes:
        arquivo = (manifesto_dir / fonte["arquivo"]).resolve() if not Path(fonte["arquivo"]).is_absolute() else Path(fonte["arquivo"])
        if not arquivo.exists():
            print(f"AVISO: arquivo não encontrado, pulando: {arquivo}", file=sys.stderr)
            continue
        reader = PdfReader(str(arquivo))
        for p in parse_paginas(fonte["paginas"]):
            idx0 = p - 1
            if idx0 < 0 or idx0 >= len(reader.pages):
                print(f"AVISO: página {p} fora do intervalo em {arquivo.name} ({len(reader.pages)} págs)", file=sys.stderr)
                continue
            paginas.append({
                "arquivo": arquivo,
                "pagina_original": p,
                "rotulo": fonte.get("rotulo", ""),
            })
    return paginas


def fingerprint_bloco(bloco):
    """Identidade de conteúdo de um pedaço: hash do conjunto ordenado (arquivo, página
    original) que ele cobre — independe de posição/ordem, só muda se o conteúdo mudar."""
    chave = "|".join(f"{item['arquivo'].name}:{item['pagina_original']}" for item in bloco)
    return hashlib.sha1(chave.encode("utf-8")).hexdigest()


def carregar_chaves_anteriores(registro_path):
    """Lê <assunto-slug>_pedacos.json de uma execução anterior (se existir) e devolve
    {fingerprint: chave_externa_segmento} pra reaproveitar identidade de pedaços que não
    mudaram de conteúdo, mesmo que a ordem/posição tenha mudado."""
    if not registro_path.exists():
        return {}
    with open(registro_path, encoding="utf-8") as f:
        anterior = json.load(f)
    return {
        p["fingerprint"]: p["chave_externa_segmento"]
        for p in anterior.get("pedacos", [])
        if p.get("fingerprint") and p.get("chave_externa_segmento")
    }


def dividir_em_blocos(paginas, minutos_por_pagina, minutos_por_bloco):
    """Corta a lista achatada de páginas em blocos de ~minutos_por_bloco cada.
    Nunca deixa um bloco vazio; a última página de um assunto pequeno vira um bloco
    único mesmo que não feche o tempo alvo."""
    paginas_por_bloco = max(1, round(minutos_por_bloco / minutos_por_pagina))
    blocos = []
    for i in range(0, len(paginas), paginas_por_bloco):
        blocos.append(paginas[i:i + paginas_por_bloco])
    return blocos


def montar_pedaco(paginas_bloco, titulo_bloco, saida_pdf):
    writer = PdfWriter()
    mapa_rastreio = []
    pagina_mesclada_atual = 1  # capa ocupa a página 1

    leitores_cache = {}
    for item in paginas_bloco:
        arquivo = item["arquivo"]
        if arquivo not in leitores_cache:
            leitores_cache[arquivo] = PdfReader(str(arquivo))
        reader = leitores_cache[arquivo]
        writer.add_page(reader.pages[item["pagina_original"] - 1])
        pagina_mesclada_atual += 1
        mapa_rastreio.append({
            "pagina_mesclada": pagina_mesclada_atual,
            "arquivo": arquivo.name,
            "pagina_original": item["pagina_original"],
            "rotulo": item["rotulo"],
        })

    saida_pdf.parent.mkdir(parents=True, exist_ok=True)
    capa_tmp = saida_pdf.with_suffix(".capa.tmp.pdf")
    gerar_capa(capa_tmp, titulo_bloco, mapa_rastreio)

    writer_final = PdfWriter()
    for pg in PdfReader(str(capa_tmp)).pages:
        writer_final.add_page(pg)
    for pg in writer.pages:
        writer_final.add_page(pg)

    with open(saida_pdf, "wb") as f:
        writer_final.write(f)
    capa_tmp.unlink(missing_ok=True)


def montar_bloco(manifesto_path, saida_dir):
    manifesto_path = Path(manifesto_path)
    with open(manifesto_path, encoding="utf-8") as f:
        manifesto = json.load(f)

    titulo = manifesto.get("titulo", "Assunto")
    minutos_por_pagina = manifesto.get("minutos_por_pagina", MINUTOS_POR_PAGINA_PADRAO)
    minutos_por_bloco = manifesto.get("minutos_por_bloco", MINUTOS_POR_BLOCO_PADRAO)
    manifesto_dir = manifesto_path.resolve().parent

    paginas = coletar_paginas(manifesto["fontes"], manifesto_dir)
    if not paginas:
        print("Nenhuma página válida encontrada — nada foi gerado.", file=sys.stderr)
        sys.exit(1)

    blocos = dividir_em_blocos(paginas, minutos_por_pagina, minutos_por_bloco)

    slug = slugificar(titulo)
    saida_dir = Path(saida_dir)
    assunto_dir_rel = Path("blocos") / slug
    assunto_dir = saida_dir / assunto_dir_rel
    registro_path = saida_dir / f"{slug}_pedacos.json"
    chaves_anteriores = carregar_chaves_anteriores(registro_path)
    pedacos_registro = []
    reaproveitadas, novas = 0, 0

    for i, bloco in enumerate(blocos, 1):
        nome_arquivo = f"segmento-{i:02d}.pdf"
        saida_pdf = assunto_dir / nome_arquivo
        titulo_bloco = f"{titulo} — segmento {i}/{len(blocos)}"
        montar_pedaco(bloco, titulo_bloco, saida_pdf)

        fingerprint = fingerprint_bloco(bloco)
        chave_existente = chaves_anteriores.get(fingerprint)
        if chave_existente:
            chave_externa_segmento = chave_existente
            reaproveitadas += 1
        else:
            chave_externa_segmento = str(uuid.uuid4())
            novas += 1

        tempo_estimado_min = round(len(bloco) * minutos_por_pagina)
        pedacos_registro.append({
            "ordem": i,
            # caminho local, relativo a --saida-dir — trocar pelo link do Google Drive
            # (compartilhado) depois do upload, antes de rodar exportar_sge.py
            "arquivo": str((assunto_dir_rel / nome_arquivo).as_posix()),
            "pagina_inicial": bloco[0]["pagina_original"],
            "pagina_final": bloco[-1]["pagina_original"],
            "tempo_estimado_min": tempo_estimado_min,
            # identidade estável do segmento (docs/requisitos-alinhamento-fatiamento-pdf-bloco.md §8)
            "chave_externa_segmento": chave_externa_segmento,
            "fingerprint": fingerprint,
        })
        print(f"Gerado: {saida_pdf}  ({len(bloco) + 1} páginas, ~{tempo_estimado_min}min)")

    if chaves_anteriores:
        print(f"Identidade de segmentos: {reaproveitadas} reaproveitada(s), {novas} nova(s).")

    with open(registro_path, "w", encoding="utf-8") as f:
        json.dump({
            "assunto_uuid": manifesto.get("assunto_uuid"),
            "edital": manifesto.get("edital"),
            "pedacos": pedacos_registro,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n{len(blocos)} pedaço(s) gerado(s). Registro: {registro_path}")
    return registro_path


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Fatia o material de um assunto em pedaços de leitura (~45-75min cada).")
    ap.add_argument("manifesto", help="Caminho do manifesto JSON do assunto")
    ap.add_argument("--saida-dir", default="dias", help="Diretório de saída dos PDFs/registro (padrão: dias)")
    args = ap.parse_args()
    montar_bloco(args.manifesto, args.saida_dir)


if __name__ == "__main__":
    main()
