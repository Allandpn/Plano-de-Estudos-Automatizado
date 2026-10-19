#!/usr/bin/env python3
"""
exportar_taxonomia.py — Baixa (ou importa) a árvore de assuntos de uma plataforma de questões e a grava num
formato só, para o catálogo de aulas e o SGE falarem a mesma língua que o site onde o aluno resolve questões.

- QConcursos (onde o aluno resolve as questões; assinatura vitalícia): o filtro de questões do site busca
  as disciplinas em `brokk.qconcursos.com/product/1/disciplines` e os assuntos de cada uma em
  `.../subjects?use_separator=true&discipline_ids=N` (disciplina → assunto → subassunto). Uma requisição
  por disciplina, uma por segundo (~259, uns 5 minutos); não precisa de login.
- TEC Concursos (às vezes): importa o JSON exportado da árvore deles (`--arquivo`), só o domínio
  "Concursos Públicos". O download automático fica para quando o endereço for conhecido.

Grava `integracao/taxonomia/<fonte>-AAAA-MM-DD.json`:

    {"fonte": "qconcursos", "data": "2026-10-19", "quantidade_nos": N,
     "disciplinas": [{"id": 213, "nome": "...", "ordem": 1, "filhos": [{"id": 8745, "nome": "...", "ordem": 2,
                       "filhos": [...]}]}]}

e mostra o que mudou desde a exportação anterior da mesma fonte (nós novos, removidos, renomeados,
movidos de lugar), pelos ids — é isso que diz o que refazer na classificação das fichas.

Uso:
    python integracao/exportar_taxonomia.py --fonte qconcursos
    python integracao/exportar_taxonomia.py --fonte tec --arquivo taxonomia-2026-10-10.json
"""

import argparse
import json
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

PASTA = Path(__file__).resolve().parent / "taxonomia"
QCONCURSOS = "https://brokk.qconcursos.com/product/1"
AGENTE = "Mozilla/5.0 (X11; Linux aarch64) plano-de-estudos (uso pessoal, uma vez por mes)"


def baixar_json(url, tentativas=3, espera=5):
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept": "application/json"})
    for i in range(tentativas):
        try:
            with urllib.request.urlopen(pedido, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            if i == tentativas - 1:
                raise
            time.sleep(espera * (i + 1))


def _assunto_qc(s):
    return {"id": s["id"], "nome": s["name"].strip(), "ordem": s.get("sort"),
            "filhos": [_assunto_qc(f) for f in sorted(s.get("nested_subjects") or [], key=lambda x: x.get("sort") or 0)]}


def normalizar_qconcursos(disciplinas, assuntos_por_disciplina):
    """disciplinas: [{"id", "nome"}]; assuntos_por_disciplina: {id: resposta de /subjects ({"<id>": [...]})}."""
    saida = []
    for ordem, d in enumerate(disciplinas, 1):
        resposta = assuntos_por_disciplina.get(d["id"]) or {}
        assuntos = resposta.get(str(d["id"]), []) if isinstance(resposta, dict) else []
        saida.append({"id": d["id"], "nome": d["nome"].strip(), "ordem": ordem,
                      "filhos": [_assunto_qc(s) for s in sorted(assuntos, key=lambda x: x.get("sort") or 0)]})
    return saida


def baixar_qconcursos(pausa=1.0, log=print):
    disciplinas = baixar_json(f"{QCONCURSOS}/disciplines")
    assuntos = {}
    for i, d in enumerate(disciplinas, 1):
        time.sleep(pausa)
        assuntos[d["id"]] = baixar_json(f"{QCONCURSOS}/subjects?use_separator=true&discipline_ids={d['id']}")
        if i % 25 == 0:
            log(f"... {i} de {len(disciplinas)} disciplinas")
    return normalizar_qconcursos(disciplinas, assuntos)


def _no_tec(n):
    return {"id": n["id_no_taxonomico"], "nome": n["nome_no_taxonomico"].strip(), "ordem": n.get("ordem_exibicao"),
            "filhos": [_no_tec(f) for f in n.get("filhos") or []]}


def normalizar_tec(exportacao, dominio="CONCURSO_PUBLICO"):
    """O JSON exportado do TEC: domínios → conteúdos (árvore de nós). Fica só o domínio de concursos."""
    d = next(x for x in exportacao["dominios"] if x["codigo_dominio_taxonomico"] == dominio)
    return [_no_tec(n) for n in d["conteudos"]]


def nos(arvore, pai=None, caminho=()):
    """{id: (nome, id do pai, caminho de nomes)} da árvore inteira."""
    saida = {}
    for n in arvore:
        c = caminho + (n["nome"],)
        saida[n["id"]] = (n["nome"], pai, c)
        saida.update(nos(n["filhos"], n["id"], c))
    return saida


def diferencas(antiga, nova):
    """O que mudou entre duas árvores, pelos ids: novos, removidos, renomeados e movidos (pai mudou)."""
    a, n = nos(antiga), nos(nova)
    return {"novos": sorted(" > ".join(n[i][2]) for i in n.keys() - a.keys()),
            "removidos": sorted(" > ".join(a[i][2]) for i in a.keys() - n.keys()),
            "renomeados": sorted(f"{a[i][0]} → {n[i][0]} ({' > '.join(n[i][2][:-1])})"
                                 for i in a.keys() & n.keys() if a[i][0] != n[i][0]),
            "movidos": sorted(f"{n[i][0]}: {' > '.join(a[i][2][:-1])} → {' > '.join(n[i][2][:-1])}"
                              for i in a.keys() & n.keys() if a[i][1] != n[i][1])}


def gravar(fonte, arvore, pasta=PASTA, hoje=None):
    """Grava <fonte>-AAAA-MM-DD.json e devolve (caminho, diferenças em relação à exportação anterior ou None)."""
    pasta.mkdir(parents=True, exist_ok=True)
    hoje = hoje or date.today().isoformat()
    destino = pasta / f"{fonte}-{hoje}.json"
    anteriores = sorted(p for p in pasta.glob(f"{fonte}-*.json") if p != destino)
    dif = diferencas(json.loads(anteriores[-1].read_text(encoding="utf-8"))["disciplinas"], arvore) if anteriores else None
    destino.write_text(json.dumps({"fonte": fonte, "data": hoje, "quantidade_nos": len(nos(arvore)),
                                   "disciplinas": arvore}, ensure_ascii=False, indent=1), encoding="utf-8")
    return destino, dif


def main():
    ap = argparse.ArgumentParser(description="Exporta a árvore de assuntos (QConcursos ou TEC) num formato só.")
    ap.add_argument("--fonte", choices=("qconcursos", "tec"), required=True)
    ap.add_argument("--arquivo", help="tec: o JSON exportado da árvore do TEC")
    ap.add_argument("--pasta", default=str(PASTA))
    args = ap.parse_args()
    if args.fonte == "tec":
        if not args.arquivo:
            ap.error("--fonte tec pede --arquivo (o download automático do TEC ainda não existe)")
        arvore = normalizar_tec(json.loads(Path(args.arquivo).read_text(encoding="utf-8")))
    else:
        arvore = baixar_qconcursos()
    destino, dif = gravar(args.fonte, arvore, Path(args.pasta))
    print(f"{destino}: {len(arvore)} disciplinas, {len(nos(arvore))} nós")
    if dif is None:
        print("primeira exportação desta fonte")
    else:
        for chave, itens in dif.items():
            print(f"{chave}: {len(itens)}")
            for item in itens[:50]:
                print(f"  - {item}")


if __name__ == "__main__":
    sys.exit(main())
