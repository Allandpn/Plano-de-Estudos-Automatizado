#!/usr/bin/env python3
"""Confirma por IA, entre os temas de ficha candidatos de cada parte do edital, os que de fato ensinam a parte (§3.2).

Entrada: o `<edital>-material.json` de `casar_partes_fichas.py` (cada parte com até 8 candidatos pelos nós) e o
`catalogo.db` (para dar à IA os termos e subtemas de cada tema, não só o título). A IA classifica cada candidato:

  ensina  — o tema ensina a parte (a parte é o tema, ou está inteira dentro dele);
  parcial — ensina só uma parte do que o edital pede;
  nao     — outro assunto (mesmo nó, mas não é isto).

Sem candidato que sirva, a parte é uma lacuna do acervo. Nada é inventado: a IA só escolhe entre os candidatos recebidos.

    python integracao/confirmar_material.py EDITAL-material.json --db catalogo.db --saida DIR [--amostra N] [--semente S]
"""
import argparse
import json
import os
import random
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ia_comum import IaIndisponivel, completar_json  # noqa: E402

LOTE = 10
SISTEMA = """Você confere se um material de estudo ensina um assunto de edital de concurso. Responda só com JSON."""
PEDIDO = """Para cada PARTE do edital abaixo há CANDIDATOS: temas de aulas de um acervo de apostilas, achados porque a árvore
de assuntos os põe no mesmo ramo. Muitos candidatos são de um assunto vizinho. Classifique cada candidato:

- "ensina": o tema ensina a parte (é a parte, ou ela está inteira dentro do tema);
- "parcial": ensina só uma porção do que a parte pede;
- "nao": é outro assunto, ainda que do mesmo ramo.

Use o contexto e o trecho do edital para entender a parte (uma sigla ou palavra solta só se entende por eles). Se nenhum
candidato serve, todos "nao". Não invente candidato.

Responda: {{"partes": [{{"parte": número, "candidatos": [{{"c": número do candidato, "veredito": "ensina" | "parcial" | "nao"}}]}}]}}

{partes}"""


def conhecimento(db, caminho, tema):
    """Os termos e subtemas que a ficha guarda para um tema, para a IA julgar com mais do que o título."""
    linha = db.execute("SELECT ficha FROM fichas WHERE caminho = ? AND situacao = 'ok'", (caminho,)).fetchone()
    if not linha:
        return [], []
    for t in json.loads(linha[0]).get("temas", []):
        if t.get("tema") == tema:
            return (t.get("termos") or [])[:8], [s["nome"] for s in t.get("subtemas", [])][:6]
    return [], []


def aula(caminho):
    partes = caminho.replace("\\", "/").split("/")
    return f"{partes[-2][:40]} / {partes[-1]}" if len(partes) > 1 else caminho


def pedido_do_lote(db, lote):
    linhas = []
    for k, (rotulo, it) in enumerate(lote, 1):
        linhas.append(f"PARTE {k}: {it['nome']}  [disciplina do edital: {it['disciplina']}]"
                      + (f"\n  contexto: {it['contexto']}" if it.get("contexto") else "")
                      + (f"\n  trecho do edital: {it['assunto'][:260]}" if it.get("assunto") else ""))
        for c, m in enumerate(it["material"], 1):
            termos, subs = conhecimento(db, m["caminho"], m["tema"])
            extra = (f" · termos: {', '.join(termos)}" if termos else "") + (f" · subtemas: {'; '.join(subs)}" if subs else "")
            linhas.append(f"  candidato {c}: «{m['tema']}» ({aula(m['caminho'])}){extra}")
    return PEDIDO.format(partes="\n".join(linhas))


def aplicar(lote, resposta):
    """Grava em cada parte `confirmado` = {indice do candidato: veredito}; o que a IA não disse fica sem veredito."""
    por_parte = {}
    for r in resposta.get("partes") or []:
        if isinstance(r, dict):
            por_parte[r.get("parte")] = r.get("candidatos") or []
    for k, (rotulo, it) in enumerate(lote, 1):
        vereditos = {}
        for c in por_parte.get(k, []):
            if isinstance(c, dict) and c.get("veredito") in ("ensina", "parcial", "nao") and isinstance(c.get("c"), int) \
                    and 1 <= c["c"] <= len(it["material"]):
                vereditos[c["c"] - 1] = c["veredito"]
        it["confirmado"] = vereditos
        for i, m in enumerate(it["material"]):
            m["veredito"] = vereditos.get(i)


def amostrar(itens, n, semente):
    """n partes com candidatos, misturando as de poucos e as de muitos candidatos (onde o nó é amplo)."""
    com = [i for i, it in enumerate(itens) if it["material"]]
    random.Random(semente).shuffle(com)
    return sorted(com[:n])


def confirmar(sge, db, trabalho, log=print):
    """Confirma por IA, em lotes, as partes de `trabalho` ([(rotulo, item)]). Grava `confirmado` e o veredito em cada candidato.
    Devolve False se a IA parou no meio (as partes seguintes ficam sem `confirmado`)."""
    for ini in range(0, len(trabalho), LOTE):
        lote = trabalho[ini:ini + LOTE]
        try:
            resposta = completar_json(sge, SISTEMA, pedido_do_lote(db, lote))
        except ValueError:
            resposta = {}
        except IaIndisponivel as e:
            log(f"A IA parou: {e}")
            return False
        aplicar(lote, resposta)
        log(f"... {min(ini + LOTE, len(trabalho))} de {len(trabalho)}")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("material", help="<edital>-material.json")
    ap.add_argument("--db", required=True, help="catalogo.db")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--amostra", type=int, help="só N partes sorteadas (ensaio)")
    ap.add_argument("--semente", type=int, default=7)
    ap.add_argument("--assuntos", help="<edital>-partes.json: acrescenta o trecho do edital à pergunta")
    args = ap.parse_args()
    from sge_api import SgeApi
    sge = SgeApi(os.environ.get("SGE_URL", "http://app:8080"), os.environ["INTERNAL_TOKEN"])
    dados = json.loads(Path(args.material).read_text(encoding="utf-8"))
    db = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    itens = dados["itens"]
    # a conferência pelo contexto precisa do termo de contexto e do trecho: vêm do -nos.json e do -partes.json irmãos
    nome = Path(args.material).name.replace("-material.json", "")
    nos = Path(args.material).parent.parent / f"{nome}-nos-refinado.json"
    if nos.exists():
        for it, base in zip(itens, json.loads(nos.read_text(encoding="utf-8"))["itens"]):
            it["contexto"] = (base.get("termos") or [""])[0]
    if args.assuntos:
        anexar_trechos(itens, dados.get("partes", []), json.loads(Path(args.assuntos).read_text(encoding="utf-8")))
    escolha = amostrar(itens, args.amostra, args.semente) if args.amostra else [i for i, it in enumerate(itens) if it["material"]]
    trabalho = [(nome, itens[i]) for i in escolha]
    print(f"{len(trabalho)} partes para confirmar", flush=True)
    confirmar(sge, db, trabalho, log=lambda m: print(m, flush=True))
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    feitos = [dict(itens[i], indice=i) for i in escolha if "confirmado" in itens[i]]
    (saida / f"{nome}-confirmado.json").write_text(json.dumps(feitos, ensure_ascii=False, indent=1), encoding="utf-8")
    print(resumo(feitos))


def anexar_trechos(itens, partes, disciplinas):
    """Acrescenta a cada item o texto do assunto do edital onde a parte aparece (a primeira ocorrência vale)."""
    textos = {d["nome"]: d["assuntos"] for d in disciplinas}
    for p in reversed(partes):
        if p["disciplina"] in textos:
            itens[p["item"]]["assunto"] = textos[p["disciplina"]][p["assunto"]]["texto"]


def resumo(feitos):
    contagem = {"ensina": 0, "parcial": 0, "nao": 0}
    sem_ensina = 0
    for it in feitos:
        v = list(it["confirmado"].values())
        for x in v:
            contagem[x] += 1
        sem_ensina += 0 if any(x in ("ensina", "parcial") for x in v) else 1
    return (f"{len(feitos)} partes: candidatos ensina {contagem['ensina']} · parcial {contagem['parcial']} · nao {contagem['nao']} · "
            f"partes sem nenhum que sirva {sem_ensina}")


if __name__ == "__main__":
    main()
