#!/usr/bin/env python3
"""Monta o PDF "Questões deste assunto" de cada assunto, a partir de `questoes/<chave>.json` (de manifesto_do_casamento.py).

As questões comentadas, listas e gabaritos das aulas escolhidas não são segmentos (decisão 7): ficam num material de
consulta por assunto, fora da escada. Cada PDF tem uma capa com a origem de cada página e depois as páginas, aula a aula.

    python integracao/pdf_questoes.py DIR_DO_EDITAL [--saida DIR]     # grava <saida>/<chave>.pdf (padrão: DIR/consulta)
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dias"))
from montar_bloco import parse_paginas_estrito  # noqa: E402
from montar_dia import gerar_capa  # noqa: E402
from pypdf import PdfReader, PdfWriter  # noqa: E402


def montar(titulo, faixas, destino, abrir=PdfReader):
    """Um PDF com as faixas na ordem dada. Página fora do PDF ou repetida entra como aviso, não derruba o assunto.
    Devolve {"paginas": n, "avisos": [...]} ou None se nenhuma página pôde ser usada."""
    escritor, rastro, avisos, vistos, leitores = PdfWriter(), [], [], set(), {}
    for f in faixas:
        try:
            numeros = parse_paginas_estrito(f["paginas"])
        except ValueError as e:
            avisos.append(f"{f['rotulo']}: {e}")
            continue
        try:
            leitor = leitores.setdefault(f["arquivo"], abrir(f["arquivo"]))
        except (OSError, ValueError) as e:
            avisos.append(f"{f['rotulo']}: não abriu {Path(f['arquivo']).name} ({e})")
            continue
        total = len(leitor.pages)
        for n in numeros:
            if n > total or (f["arquivo"], n) in vistos:
                avisos.append(f"{f['rotulo']}: página {n} " + ("fora do PDF" if n > total else "repetida"))
                continue
            vistos.add((f["arquivo"], n))
            escritor.add_page(leitor.pages[n - 1])
            rastro.append({"pagina_mesclada": len(rastro) + 1, "arquivo": Path(f["arquivo"]).name, "pagina_original": n,
                           "rotulo": f["rotulo"][:60]})
    if not rastro:
        return None
    capa = Path(str(destino) + ".capa.pdf")
    gerar_capa(capa, titulo, rastro)
    paginas_capa = len(PdfReader(str(capa)).pages)  # a capa ocupa páginas: o rastro conta a partir da primeira depois dela
    for r in rastro:
        r["pagina_mesclada"] += paginas_capa
    gerar_capa(capa, titulo, rastro)
    final = PdfWriter()
    for p in PdfReader(str(capa)).pages:
        final.add_page(p)
    for p in escritor.pages:
        final.add_page(p)
    with open(destino, "wb") as saida:
        final.write(saida)
    capa.unlink()
    return {"paginas": len(rastro), "capa": paginas_capa, "avisos": avisos}


def montar_todos(pasta, saida=None):
    """Um PDF por arquivo de `questoes/`. O título vem de `assuntos.json` (chave → disciplina e assunto)."""
    pasta = Path(pasta)
    saida = Path(saida) if saida else pasta / "consulta"
    saida.mkdir(parents=True, exist_ok=True)
    assuntos = {a["chave"]: a for a in json.loads((pasta / "assuntos.json").read_text(encoding="utf-8"))}
    resultado = []
    atuais = {a.stem for a in (pasta / "questoes").glob("*.json")}
    for velho in saida.glob("*.pdf"):  # PDF de rodada anterior de um assunto que já não tem questões
        if velho.stem not in atuais:
            velho.unlink()
    for arq in sorted((pasta / "questoes").glob("*.json")):
        chave = arq.stem
        a = assuntos.get(chave, {})
        titulo = f"Questões deste assunto — {a.get('disciplina', '')}: {a.get('assunto', chave)}"[:150]
        faixas = json.loads(arq.read_text(encoding="utf-8"))
        r = montar(titulo, faixas, saida / f"{chave}.pdf")
        resultado.append({"chave": chave, "arquivo": f"{chave}.pdf" if r else None, **(r or {"paginas": 0, "avisos": ["nenhuma página utilizável"]})})
    (saida / "consulta.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
    return resultado


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pasta")
    ap.add_argument("--saida")
    args = ap.parse_args()
    r = montar_todos(args.pasta, args.saida)
    print(f"{sum(1 for x in r if x['arquivo'])} PDFs, {sum(x['paginas'] for x in r)} páginas, "
          f"{sum(len(x['avisos']) for x in r)} avisos")


if __name__ == "__main__":
    main()
