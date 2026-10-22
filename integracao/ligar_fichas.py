#!/usr/bin/env python3
"""Liga os temas das fichas do catálogo (catalogo.db) aos nós da árvore do QConcursos, em blocos e de forma retomável.

É a primeira metade do casamento "parte do edital ↔ material do acervo": o nó é o pivô comum (proposta §3.7). A segunda
metade, que casa partes e fichas pelos nós, é por regra e está em `casar_partes_fichas.py`.

    python integracao/ligar_fichas.py --db /dados/catalogo.db --saida DIR [--bloco 80] [--esperar] [--limite N]

Grava `<saida>/fichas-nos.jsonl` (uma linha por tema: caminho, tema, páginas, nós, natureza) e `<saida>/fichas-disciplinas.json`
(o mapa de disciplinas das fichas para as do QConcursos). Rodar de novo continua de onde parou: a unidade é a ficha
(arquivo), e o que já está no `.jsonl` não é refeito. Com --esperar, quando a assinatura para o programa dorme até o horário
que a mensagem dá e continua.
"""
import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from casar_taxonomia import Arvore, carregar_arvore, itens_das_fichas, ligar_com_ia, mapear_disciplinas  # noqa: E402
from ia_comum import IaIndisponivel  # noqa: E402

BLOCO = 80  # fichas por bloco; uma ficha tem 2,5 temas em média, então ~200 temas por bloco


def caminhos_com_tema(db):
    """Os caminhos das fichas 'ok', na ordem do banco."""
    return [c for (c,) in db.execute("SELECT caminho FROM fichas WHERE situacao = 'ok' ORDER BY caminho")]


def feitos(arquivo):
    """Os caminhos que já têm todos os temas gravados (um bloco só grava depois de terminar)."""
    if not arquivo.exists():
        return set()
    return {json.loads(l)["caminho"] for l in arquivo.read_text(encoding="utf-8").splitlines() if l.strip()}


def linha_do_tema(it):
    return {"caminho": it["caminho"], "tema": it["nome"], "disciplina": it["disciplina"], "paginas": it.get("paginas"),
            "nos": it.get("ia") or [], "natureza": it.get("natureza"), "confianca": it.get("confianca"),
            "segunda_passada": bool(it.get("segunda_passada"))}


def ligar_bloco(sge, db, caminhos, arvore, mapa, log=print, respostas=None):
    itens = itens_das_fichas(db, caminhos, arvore, mapa)
    ligar_com_ia(sge, itens, arvore, log=log, respostas=respostas)
    return itens


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", required=True, help="catalogo.db")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--bloco", type=int, default=BLOCO)
    ap.add_argument("--limite", type=int, help="para depois de N blocos (ensaio)")
    ap.add_argument("--esperar", action="store_true", help="quando a assinatura parar, espera o horário e continua")
    args = ap.parse_args()
    from catalogo_aulas import segundos_ate_liberar
    from sge_api import SgeApi
    sge = SgeApi(os.environ.get("SGE_URL", "http://app:8080"), os.environ["INTERNAL_TOKEN"])
    arvore = Arvore(carregar_arvore()[0])
    db = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    jsonl = saida / "fichas-nos.jsonl"
    arq_disc = saida / "fichas-disciplinas.json"
    mapa = json.loads(arq_disc.read_text(encoding="utf-8")) if arq_disc.exists() else {}
    nomes = sorted({t.get("disciplina") for (f,) in db.execute("SELECT ficha FROM fichas WHERE situacao = 'ok'")
                    for t in json.loads(f)["temas"]} - {None})
    faltam = [n for n in nomes if n not in mapa]
    if faltam:
        mapa.update(mapear_disciplinas(sge, faltam, arvore))
        arq_disc.write_text(json.dumps(mapa, ensure_ascii=False, indent=1), encoding="utf-8")
    pendentes = [c for c in caminhos_com_tema(db) if c not in feitos(jsonl)]
    print(f"{len(pendentes)} fichas por ligar ({len(nomes)} disciplinas mapeadas)", flush=True)
    blocos = [pendentes[i:i + args.bloco] for i in range(0, len(pendentes), args.bloco)]
    for n, caminhos in enumerate(blocos[:args.limite] if args.limite else blocos, 1):
        while True:
            try:
                itens = ligar_bloco(sge, db, caminhos, arvore, mapa, log=lambda *_: None)
                break
            except IaIndisponivel as e:
                if not args.esperar:
                    print(f"A IA parou no bloco {n}: {e}")
                    return
                espera = segundos_ate_liberar(str(e))
                print(f"A IA parou ({e}); espero {espera // 60} min", flush=True)
                time.sleep(espera)
        # o bloco só é gravado depois de ligado por inteiro; ficha sem tema não gera linha (e não custa chamada)
        with jsonl.open("a", encoding="utf-8") as f:
            for it in itens:
                f.write(json.dumps(linha_do_tema(it), ensure_ascii=False) + "\n")
        print(f"bloco {n}/{len(blocos)}: {len(itens)} temas, {sum(1 for i in itens if i.get('ia'))} com nó", flush=True)


if __name__ == "__main__":
    main()
