#!/usr/bin/env python3
"""
triagem_ia.py — A triagem de um assunto feita por IA, para o worker do material
(integracao/worker.py; docs/arquitetura-integracao-planejamento-sge.md §9).

É o mesmo julgamento que o fluxo em chat do CLAUDE.md faz ("Fluxo de uma triagem de
bloco"), reduzido ao que o fatiador precisa: quais páginas de quais apostilas ensinam
cada parte do assunto. A IA só escolhe; quem decide se a escolha vale é o validador
estrito de dias/montar_bloco.py (página que não existe, parte do assunto sem página e
sem motivo, página repetida — tudo recusa). Nada é inventado: o que a IA não acha vira
lacuna com motivo.
"""

import json
import re

SISTEMA = """Você faz a triagem de material de estudo para concurso público.
Recebe um assunto do edital, dividido em partes, e trechos de apostilas encontrados por busca
no acervo do usuário. Escolhe as páginas que ENSINAM cada parte do assunto.

Regras:
- Use só os arquivos e as páginas listados. Páginas são a posição no PDF (1 = primeira).
- Prefira faixas contínuas ("12-30"). Não repita o mesmo conteúdo de duas apostilas: escolha a melhor.
- Use o "Início de cada página" para achar onde o tema COMEÇA e onde TERMINA: a faixa começa na
  página em que o tema começa e termina na página anterior àquela em que começa outro tema.
  Apostilas-resumo e listas de questões misturam temas lado a lado — pegue só o trecho deste
  assunto, mesmo que isso dê faixas curtas. Dentro do tema, pegue a explicação inteira, do começo
  ao fim, com as questões comentadas dela: deixe de fora só o que é de outro tema.
- Os arquivos vêm de buscas feitas PARTE POR PARTE ("Achado para"). Procure cobrir CADA parte com a
  melhor explicação disponível antes de declará-la lacuna.
- Não inclua páginas que só citam o termo de passagem, sumário, capa ou propaganda.
- "cobre" lista exatamente os nomes das partes (como vieram) que aquela faixa ensina.
- Toda parte precisa estar em "cobre" de alguma fonte OU em "lacunas" com motivo.
- Questões comentadas e resumos entram com "tipo": "fixacao"; teoria com "tipo": "teoria".
- Se nada no material ensina o assunto, responda {"sem_material": true, "motivo": "..."}.

Responda só JSON, neste formato:
{"fontes": [{"arquivo": "<id do arquivo>", "paginas": "12-30", "rotulo": "<curto>",
             "cobre": ["<parte>"], "tipo": "teoria"}],
 "lacunas": [{"subitem": "<parte>", "motivo": "<por que não há página>"}]}"""


def partes_do_assunto(nome):
    """As partes do assunto fino, como o mapa de assuntos separa: por vírgula e ponto e vírgula."""
    partes = [p.strip(" .") for p in re.split(r"[;,]", nome) if p.strip(" .")]
    return partes or [nome.strip()]


def montar_pedido(assunto, disciplina, partes, candidatos, erros_anteriores=None):
    linhas = [f"Disciplina: {disciplina}", f"Assunto: {assunto}", "Partes do assunto:"]
    linhas += [f"- {p}" for p in partes]
    linhas.append("\nArquivos candidatos:")
    for i, c in enumerate(candidatos, 1):
        linhas.append(f"\n[A{i}] {c['arquivo']} ({c['n_paginas']} páginas)")
        if c.get("partes"):
            linhas.append("Achado para: " + "; ".join(c["partes"]))
        if c.get("sumario"):
            linhas.append("Sumário: " + "; ".join(f"{s['titulo']} (p. {s['pagina']})" for s in c["sumario"]))
        linhas.append("Ocorrências dos termos:")
        for p in c["paginas"]:
            linhas.append(f"  p. {p['pagina']}: {p['trecho']}")
        if c.get("mapa"):
            linhas.append("Início de cada página:")
            linhas += [f"  p. {m['pagina']}: {m['inicio']}" for m in c["mapa"]]
    if erros_anteriores:
        linhas.append("\nSua resposta anterior foi recusada pela validação. Corrija:")
        linhas += [f"- {e}" for e in erros_anteriores]
    return "\n".join(linhas)


def interpretar(conteudo, candidatos):
    """Resposta da IA -> ("sem_material", motivo) ou ("manifesto", {fontes, lacunas}).
    Troca o id [An] pelo caminho relativo do arquivo. Lança ValueError se não der para ler."""
    try:
        dados = json.loads(conteudo)
    except json.JSONDecodeError:
        inicio, fim = conteudo.find("{"), conteudo.rfind("}")
        if inicio < 0 or fim < inicio:
            raise ValueError("a IA não devolveu JSON")
        dados = json.loads(conteudo[inicio:fim + 1])
    if dados.get("sem_material"):
        return "sem_material", (dados.get("motivo") or "a IA não achou material que ensine o assunto").strip()
    ids = {f"A{i}": c["arquivo"] for i, c in enumerate(candidatos, 1)}
    fontes = []
    for f in dados.get("fontes") or []:
        ident = str(f.get("arquivo", "")).strip().strip("[]")
        fontes.append({
            "arquivo": ids.get(ident, ident),  # id desconhecido: o validador recusa por arquivo inexistente
            "paginas": str(f.get("paginas", "")),
            "rotulo": str(f.get("rotulo") or ident)[:120],
            "cobre": [str(s) for s in f.get("cobre") or []],
            "tipo": f.get("tipo") if f.get("tipo") in ("teoria", "fixacao") else "teoria",
        })
    lacunas = [{"subitem": str(l.get("subitem", "")), "motivo": str(l.get("motivo", ""))}
               for l in dados.get("lacunas") or []]
    if not fontes:
        return "sem_material", "; ".join(f"{l['subitem']}: {l['motivo']}" for l in lacunas) \
            or "a IA não indicou nenhuma página"
    return "manifesto", {"fontes": fontes, "lacunas": lacunas}
