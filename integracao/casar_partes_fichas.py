#!/usr/bin/env python3
"""Casa as partes de um edital com os temas das fichas do catálogo pelos nós do QConcursos (sem IA).

Entradas: `<edital>-nos.json` (de `mapear_partes.py`: itens com `ia` e `natureza`, e `partes`) e `fichas-nos.jsonl` (de
`ligar_fichas.py`). Para cada parte, procura os temas de ficha cujo nó casa com o nó dela, nesta ordem de força:

  1. `exato`      — o tema está ligado ao mesmo nó da parte;
  2. `dentro`     — o tema está ligado a um nó abaixo do nó da parte (a parte é "mais ampla": o material é parte dela);
  3. `contem`     — o tema está ligado a um nó acima do da parte (o tema é mais amplo: o material contém a parte, mas
                    traz mais do que ela pede).

Disciplina (nível 1 da árvore) nunca casa sozinha. Devolve, por parte, os temas com arquivo e páginas, e um resumo de
cobertura: o que ficou sem material no acervo é lacuna real, vista antes de preparar qualquer segmento.

    python integracao/casar_partes_fichas.py EDITAL-nos.json --fichas fichas-nos.jsonl --saida DIR
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from casar_taxonomia import Arvore, carregar_arvore  # noqa: E402

FORCA = {"exato": 0, "dentro": 1, "contem": 2}
MAXIMO = 8  # temas guardados por parte


def relacao(arvore, nos_parte, nos_tema):
    """A relação mais forte entre os nós da parte e os do tema, ou None."""
    melhor = None
    for a in nos_parte:
        for b in nos_tema:
            if arvore.nos[a]["nivel"] <= 1 or arvore.nos[b]["nivel"] <= 1:
                continue
            if a == b:
                r = "exato"
            elif a in arvore.ancestrais(b):
                r = "dentro"
            elif b in arvore.ancestrais(a):
                r = "contem"
            else:
                continue
            if melhor is None or FORCA[r] < FORCA[melhor]:
                melhor = r
    return melhor


def indexar(arvore, temas):
    """{nó: [índices dos temas]} com o nó e todos os ancestrais (menos a disciplina), para achar sem varrer tudo."""
    indice = {}
    for k, t in enumerate(temas):
        for n in t.get("nos") or []:
            for anc in arvore.ancestrais(n):
                if arvore.nos[anc]["nivel"] > 1:
                    indice.setdefault(anc, set()).add(k)
    return indice


def casar(arvore, itens, partes, temas):
    """Para cada item de `mapear_partes`, os temas casados. Devolve {indice_do_item: [{..tema.., "relacao": ...}]}."""
    indice = indexar(arvore, temas)
    por_item = {}
    for k, it in enumerate(itens):
        achados = {}
        candidatos = set()
        for n in it.get("ia") or []:
            candidatos |= indice.get(n, set())
            # tema ligado a um ancestral da parte também casa ("contem"); o índice só guarda nós e ancestrais dos temas
        for n in it.get("ia") or []:
            for anc in arvore.ancestrais(n):
                candidatos |= indice.get(anc, set())
        for j in candidatos:
            r = relacao(arvore, it.get("ia") or [], temas[j].get("nos") or [])
            if r:
                chave = (temas[j]["caminho"], temas[j]["tema"])
                if chave not in achados or FORCA[r] < FORCA[achados[chave]["relacao"]]:
                    achados[chave] = {"caminho": temas[j]["caminho"], "tema": temas[j]["tema"],
                                      "paginas": temas[j].get("paginas"), "relacao": r}
        ordem = sorted(achados.values(), key=lambda a: (FORCA[a["relacao"]], a["caminho"]))
        por_item[k] = ordem[:MAXIMO]
    return por_item


def resumo(itens, por_item):
    """Cobertura por natureza do vínculo e a lista do que ficou sem material."""
    total = {}
    for k, it in enumerate(itens):
        nat = it.get("natureza") or "sem nó"
        forca = min((FORCA[a["relacao"]] for a in por_item.get(k, [])), default=None)
        faixa = "sem material" if forca is None else ["exato", "dentro", "contem"][forca]
        total.setdefault(nat, {}).setdefault(faixa, 0)
        total[nat][faixa] += 1
    return total


def relatorio(edital, itens, por_item, arvore, tot):
    caminho = lambda ids: "; ".join(" > ".join(arvore.nos[i]["caminho"]) for i in ids) or "sem nó"  # noqa: E731
    sem = [it for k, it in enumerate(itens) if not por_item.get(k)]
    linhas = [f"# {edital} — partes e material do acervo", "",
              f"{len(itens)} ligações de partes · {len(itens) - len(sem)} com material · {len(sem)} sem material no acervo", "",
              "| natureza do vínculo | exato | dentro | contém | sem material |", "|---|---:|---:|---:|---:|"]
    for nat, c in sorted(tot.items()):
        linhas.append(f"| {nat} | {c.get('exato', 0)} | {c.get('dentro', 0)} | {c.get('contem', 0)} | {c.get('sem material', 0)} |")
    linhas += ["", "## Sem material no acervo", ""]
    linhas += [f"- **{it['nome']}** _({it['disciplina']})_ → {caminho(it.get('ia') or [])}" for it in sem]
    return "\n".join(linhas)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("nos", help="<edital>-nos.json (ou -nos-refinado.json)")
    ap.add_argument("--fichas", required=True, help="fichas-nos.jsonl")
    ap.add_argument("--saida", required=True)
    args = ap.parse_args()
    arvore = Arvore(carregar_arvore()[0])
    dados = json.loads(Path(args.nos).read_text(encoding="utf-8"))
    temas = [json.loads(l) for l in Path(args.fichas).read_text(encoding="utf-8").splitlines() if l.strip()]
    temas = [t for t in temas if t.get("nos")]
    por_item = casar(arvore, dados["itens"], dados["partes"], temas)
    nome = Path(args.nos).name.split("-nos")[0]
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    tot = resumo(dados["itens"], por_item)
    (saida / f"{nome}-material.json").write_text(json.dumps(
        {"itens": [dict(nome=it["nome"], disciplina=it["disciplina"], nos=it.get("ia") or [], natureza=it.get("natureza"),
                        material=por_item.get(k, [])) for k, it in enumerate(dados["itens"])], "partes": dados["partes"],
         "cobertura": tot}, ensure_ascii=False, indent=1), encoding="utf-8")
    texto = relatorio(nome, dados["itens"], por_item, arvore, tot)
    (saida / f"{nome}-material.md").write_text(texto, encoding="utf-8")
    print(texto.splitlines()[2])


if __name__ == "__main__":
    main()
