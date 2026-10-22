#!/usr/bin/env python3
"""Liga as PARTES de um edital (saída de partes_edital.py) aos nós da árvore de assuntos do QConcursos.

Entrada: um <edital>-partes.json (lista de disciplinas com assuntos e partes). Cada parte vira um item
("herdado + texto", com o contexto como termo), as disciplinas do edital são ligadas às do QConcursos (uma
chamada) e as partes são ligadas por casar_taxonomia.ligar_com_ia, que devolve os nós e a NATUREZA do vínculo
(exato, mais_amplo ou parcial); depois, a segunda checagem (casar_taxonomia.refinar) olha a árvore inteira para os
'mais amplos', parciais e sem nó. Partes iguais na mesma disciplina e contexto valem uma ligação só.

Saída em --saida: <edital>-nos.json (um item por parte, na ordem do edital) e <edital>-nos.md (para conferir).

    python integracao/mapear_partes.py EDITAL-partes.json --saida DIR [--disciplinas "Banco de Dados" ...]
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from casar_taxonomia import Arvore, carregar_arvore, ligar_com_ia, mapear_disciplinas, palavras, refinar  # noqa: E402
from ia_comum import IaIndisponivel  # noqa: E402

NATUREZAS = ("exato", "mais_amplo", "parcial")


def itens_das_partes(disciplinas, arvore, mapa_disciplinas, so=None):
    """Um item por parte distinta (disciplina, nome, contexto) e, para cada parte do edital, a chave do item."""
    itens, por_chave, partes = [], {}, []
    for d in disciplinas:
        if so and not any(s.lower() in d["nome"].lower() for s in so):
            continue
        raizes = sorted(mapa_disciplinas.get(d["nome"]) or [])
        for ia, a in enumerate(d["assuntos"]):
            for ip, p in enumerate(a.get("partes") or []):
                nome = " ".join(x for x in (p.get("herdado"), p.get("texto")) if x).strip()
                contexto = p.get("contexto") or ""
                chave = (d["nome"], nome.lower(), contexto.lower())
                if chave not in por_chave:
                    termos = [contexto] if contexto else [a["texto"][:100]]
                    por_chave[chave] = len(itens)
                    itens.append({"tipo": "parte", "nome": nome, "disciplina": d["nome"], "termos": termos,
                                  "raizes": raizes,
                                  "candidatos": arvore.candidatos(nome, termos, d["nome"], raizes=set(raizes))})
                partes.append({"disciplina": d["nome"], "assunto": ia, "parte": ip, "item": por_chave[chave]})
    return itens, partes


def _chave(nome, contexto):
    return (" ".join(palavras(nome)), " ".join(palavras(contexto)))


def aplicar_decisoes(itens, decisoes):
    """Decisões já aprovadas por uma pessoa (lista de {parte, contexto, nos, natureza, origem}) valem antes da IA e
    do refino, em qualquer edital: a chave é a parte e o contexto, sem a disciplina. Devolve quantas aplicou."""
    por_chave = {_chave(d["parte"], d.get("contexto") or ""): d for d in decisoes}
    feitas = 0
    for it in itens:
        d = por_chave.get(_chave(it["nome"], it["termos"][0] if it.get("termos") else ""))
        if d:
            it.update(ia=list(d["nos"]), natureza=d.get("natureza"), decisao=d.get("origem") or "aprovada")
            feitas += 1
    return feitas


def relatorio(edital, itens, partes, arvore, mapa_disciplinas):
    caminho = lambda ids: "; ".join(" > ".join(arvore.nos[i]["caminho"]) for i in ids) or "**nenhum nó**"  # noqa: E731
    sem = sum(1 for it in itens if "ia" in it and not it["ia"])
    naturezas = {n: sum(1 for it in itens if it.get("natureza") == n) for n in NATUREZAS}
    saida = [f"# {edital} — partes ligadas à árvore do QConcursos", "",
             f"{len(partes)} partes no edital · {len(itens)} ligações distintas · sem nó: {sem} · "
             + " · ".join(f"{n}: {c}" for n, c in naturezas.items()), "",
             "Marque `[x]` se o nó confere, ou escreva ao lado o nó certo.", ""]
    ultima = None
    for it in itens:
        if it["disciplina"] != ultima:
            ultima = it["disciplina"]
            ligadas = "; ".join(arvore.nos[i]["nome"] for i in mapa_disciplinas.get(ultima) or []) or "**nenhuma**"
            saida += ["", f"## {ultima} → {ligadas}", ""]
        ctx = f" _(contexto: {it['termos'][0]})_" if it["termos"] and it["termos"][0] and len(it["termos"][0]) < 100 else ""
        saida.append(f"- [ ] **{it['nome']}**{ctx} → {caminho(it.get('ia', []))} · {it.get('natureza') or '?'}"
                     + (" · 2ª passada" if it.get("segunda_passada") else "")
                     + (f" · refinado (antes: {caminho(it['ia_antes'])})" if it.get("refinado") else "")
                     + (f" · decisão aprovada ({it['decisao']})" if it.get("decisao") else ""))
    return "\n".join(saida)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("partes")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--disciplinas", nargs="*", help="só as disciplinas cujo nome contém algum destes textos")
    ap.add_argument("--decisoes", help="JSON com as decisões já aprovadas por uma pessoa (valem antes da IA)")
    ap.add_argument("--sem-refino", action="store_true", help="não faz a segunda checagem dos 'mais amplos' e sem nó")
    ap.add_argument("--so-refinar", action="store_true",
                    help="não liga de novo: lê <edital>-nos.json já gravado, refina e grava <edital>-nos-refinado.*")
    args = ap.parse_args()
    from sge_api import SgeApi
    sge = SgeApi(os.environ.get("SGE_URL", "http://app:8080"), os.environ["INTERNAL_TOKEN"])
    arquivo = Path(args.partes)
    nome = arquivo.name.replace("-partes.json", "")
    disciplinas = json.loads(arquivo.read_text(encoding="utf-8"))
    if args.disciplinas:
        disciplinas = [d for d in disciplinas if any(s.lower() in d["nome"].lower() for s in args.disciplinas)]
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    arvore = Arvore(carregar_arvore()[0])
    mapa_arquivo = saida / f"{nome}-disciplinas.json"
    mapa = json.loads(mapa_arquivo.read_text(encoding="utf-8")) if mapa_arquivo.exists() else {}
    faltam = [d["nome"] for d in disciplinas if d["nome"] not in mapa]
    if faltam:
        mapa.update(mapear_disciplinas(sge, faltam, arvore))
        mapa_arquivo.write_text(json.dumps(mapa, ensure_ascii=False, indent=1), encoding="utf-8")
    respostas = []
    if args.so_refinar:
        gravado = json.loads((saida / f"{nome}-nos.json").read_text(encoding="utf-8"))
        itens, partes = gravado["itens"], gravado["partes"]
        nome_saida = f"{nome}-nos-refinado"
    else:
        itens, partes = itens_das_partes(disciplinas, arvore, mapa)
        print(f"{len(partes)} partes, {len(itens)} ligações distintas", flush=True)
        nome_saida = f"{nome}-nos"
        if args.decisoes:
            lido = json.loads(Path(args.decisoes).read_text(encoding='utf-8'))
            print(f"{aplicar_decisoes(itens, lido['decisoes'] if isinstance(lido, dict) else lido)} decisões aprovadas aplicadas",
                  flush=True)
        try:
            ligar_com_ia(sge, [it for it in itens if not it.get("decisao")], arvore, respostas=respostas)
        except IaIndisponivel as e:
            print(f"A IA parou: {e}")
    if not args.sem_refino:
        try:
            refinar(sge, itens, arvore, respostas=respostas)
        except IaIndisponivel as e:
            print(f"A IA parou no refino: {e}")
    (saida / f"{nome_saida}-respostas-ia.json").write_text(json.dumps(respostas, ensure_ascii=False, indent=1), encoding="utf-8")
    (saida / f"{nome_saida}.json").write_text(json.dumps({"itens": itens, "partes": partes}, ensure_ascii=False, indent=1),
                                              encoding="utf-8")
    texto = relatorio(nome, itens, partes, arvore, mapa)
    (saida / f"{nome_saida}.md").write_text(texto, encoding="utf-8")
    print(texto.splitlines()[2])


if __name__ == "__main__":
    main()
