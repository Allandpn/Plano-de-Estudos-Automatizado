#!/usr/bin/env python3
"""Segunda chance (D4 da proposta de material por casamento): a busca por palavras + triagem por IA, só para as partes que o
casamento não cobriu.

O catálogo pode não ter ficha de um assunto que a apostila trata de passagem. Para cada assunto "parcial" ou "sem material"
dos manifestos, busca no índice do acervo só as partes sem cobertura, pede à IA (pelo proxy do SGE) que escolha páginas e
junta o que ela achou ao manifesto. O fatiador valida o resultado; o que não passa fica como estava. Nunca se tira nada do
que o casamento já escolheu, e nenhuma página que ele usou entra de novo.

Diferença para a triagem antiga: aqui a IA não leva questões, lista nem gabarito (decisão 7). Toda fonte nova sai marcada com
`"origem": "segunda_chance"` e entra no fim da lista, depois do que o casamento escolheu.

    python integracao/segunda_chance.py DIR_DO_EDITAL --indice indice.db --acervo /acervo/apostilas
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dias"))
import triagem_ia  # noqa: E402
from entrega_revisao import chave_do_assunto  # noqa: E402
from selecao_material import MINUTOS_TEORIA, paginas_de, rotulos_unicos, texto_das_paginas  # noqa: E402

TENTATIVAS = 2
SISTEMA = triagem_ia.SISTEMA + """

ATENÇÃO — estas regras valem no lugar das que falam de aula inteira e de questões:
- Escolha só TEORIA, em faixas de páginas. Não use "inteira". Não inclua questões comentadas, lista de exercícios, questionário
  nem gabarito: as questões ficam em outro material.
- Só estas partes ainda não têm material; as outras já estão cobertas e não aparecem. Cubra só as listadas."""


def faixas_de(texto):
    return paginas_de([[int(x.split("-")[0]), int(x.split("-")[-1])] for x in texto.split(",") if x.strip()])


def tirar_paginas_usadas(fontes, usadas):
    """Remove de cada fonte nova as páginas que o casamento já usou (o validador recusa repetição); fonte que fica sem página
    sai. `usadas`: {arquivo: {páginas}}. Faixa ilegível passa adiante: o validador recusa com a mensagem certa."""
    saida = []
    for f in fontes:
        try:
            restantes = faixas_de(f["paginas"]) - usadas.get(f["arquivo"], set())
        except ValueError:
            saida.append(f)
            continue
        if restantes:
            saida.append(dict(f, paginas=texto_das_paginas(restantes)))
    return saida


def tentar(sge, acervo, disciplina, assunto, partes, manifesto, validar):
    """Uma segunda chance para um assunto. `partes`: nomes únicos de todas as partes; `manifesto`: o que o casamento montou, ou o
    cabeçalho vazio (sem fontes) quando não montou nada. Devolve (manifesto novo ou None, mensagem). `validar(manifesto)`
    devolve a lista de erros."""
    vazio = not manifesto["fontes"]
    faltam = [n for n in partes if vazio or n in {l["subitem"] for l in manifesto["lacunas"]}]
    if not faltam:
        return None, "nada a buscar"
    candidatos = acervo.candidatos_por_partes(faltam, disciplina=disciplina)
    if not candidatos:
        return None, "nenhuma página do acervo cita os termos"
    usadas = {}
    for f in manifesto["fontes"]:
        usadas.setdefault(f["arquivo"], set()).update(faixas_de(f["paginas"]))
    erros = None
    for _ in range(TENTATIVAS):
        resposta = sge.completar(SISTEMA, triagem_ia.montar_pedido(assunto, disciplina, faltam, candidatos, erros))
        try:
            tipo, valor = triagem_ia.interpretar(resposta, candidatos)
        except ValueError as e:
            erros = [f"resposta ilegível: {e}"]
            continue
        if tipo == "sem_material":
            return None, valor
        novas = [dict(f, arquivo=str(acervo.caminho(f["arquivo"])), origem="segunda_chance") for f in valor["fontes"]]
        novas = tirar_paginas_usadas(novas, usadas)
        if not novas:
            return None, "a IA só indicou páginas que o casamento já usa"
        cobertas = {p for f in novas for p in f["cobre"]} & set(faltam)
        antes = [{"subitem": n, "motivo": "nenhum tema do acervo ensina esta parte"} for n in partes] if vazio else manifesto["lacunas"]
        novo = dict(manifesto, fontes=list(manifesto["fontes"]) + novas,
                    lacunas=[l for l in antes if l["subitem"] not in cobertas])
        erros = validar(novo)
        if not erros:
            return novo, f"{len(novas)} fonte(s), cobre {len(cobertas)} de {len(faltam)} parte(s)"
    return None, "não passou na validação: " + "; ".join((erros or [])[:2])


def processar(slug, disciplinas, linhas, pasta, sge, acervo, validar, log=print):
    """Roda a segunda chance nos assuntos `parcial` e `sem material` de `linhas` (assuntos.json) e atualiza manifestos e linhas.
    Devolve a lista do que foi tentado: [{"chave", "resultado", "mensagem"}]."""
    por_chave = {l["chave"]: l for l in linhas}
    tentados = []
    for d in disciplinas:
        vistos = {}
        for a in d["assuntos"]:
            chave = chave_do_assunto(d["nome"], a["texto"], vistos)
            linha = por_chave.get(chave)
            if not linha or linha["situacao"] not in ("parcial", "sem material"):
                continue
            partes = rotulos_unicos([" ".join(x for x in (p.get("herdado"), p.get("texto")) if x).strip() for p in a["partes"]])
            caminho = Path(pasta) / "manifestos" / f"{chave}.json"
            manifesto = json.loads(caminho.read_text(encoding="utf-8")) if linha["fontes"] and caminho.exists() else \
                {"assunto_uuid": chave, "edital": slug, "titulo": f"{d['nome']} — {a['texto'][:90]}",
                 "subitens": partes, "lacunas": [], "descartes": [], "fontes": []}
            novo, mensagem = tentar(sge, acervo, d["nome"], a["texto"], partes, manifesto, validar)
            if novo is not None:
                caminho.parent.mkdir(parents=True, exist_ok=True)
                caminho.write_text(json.dumps(novo, ensure_ascii=False, indent=1), encoding="utf-8")
                extra = [f for f in novo["fontes"] if f.get("origem") == "segunda_chance"]
                linha["fontes"] = len(novo["fontes"])
                linha["lacunas"] = len(novo["lacunas"])
                linha["minutos"] += sum(len(faixas_de(f["paginas"])) for f in extra) * MINUTOS_TEORIA
                linha["situacao"] = "parcial" if novo["lacunas"] else "completo"
                linha["segunda_chance"] = mensagem
            tentados.append({"chave": chave, "assunto": a["texto"], "resultado": "achou" if novo is not None else "nada",
                             "mensagem": mensagem})
            log(f"  {a['texto'][:60]}: {mensagem}")
    return tentados
