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
no acervo do usuário. Escolhe o material que ENSINA cada parte do assunto.

O princípio: É MELHOR PECAR POR EXCESSO DO QUE POR FALTA. Um subtema que fica de fora pode custar a
questão que reprova; uma página a mais custa só minutos de leitura.

Regras:
- Use só os arquivos listados. Páginas são a posição no PDF (1 = primeira).
- A unidade preferida é a AULA INTEIRA. Se o arquivo é uma aula sobre a parte (pela abertura, pelo
  sumário ou porque o tema ocupa boa parte dela), devolva "inteira": true: entra a aula toda, com
  teoria, questões comentadas, lista de exercícios e resumo. Não recorte uma aula que é do tema.
- Faixa de páginas só em arquivo que mistura temas sem relação (resumo de várias matérias, simulado,
  lei comentada, curso "passo estratégico"): a faixa começa onde o tema começa e vai até onde começa
  outro tema, com as questões dele. Use o "Início de cada página" para achar esses pontos. Na dúvida
  sobre uma página, INCLUA.
- Os arquivos vêm de buscas feitas PARTE POR PARTE ("Achado para"). Cubra CADA parte; só declare
  lacuna depois de olhar todos os arquivos.
- Cursos diferentes costumam ter a mesma aula: não inclua duas vezes o mesmo conteúdo. Se uma segunda
  aula traz algo que a primeira não traz, inclua as duas.
- Não use arquivo que só cita o termo de passagem.
- "cobre" lista exatamente os nomes das partes (como vieram) que aquela fonte ensina.
- Toda parte precisa estar em "cobre" de alguma fonte OU em "lacunas" com motivo.
- Aula inteira e teoria: "tipo": "teoria". Faixa só de questões comentadas ou resumo: "tipo": "fixacao".
- Se nada no material ensina o assunto, responda {"sem_material": true, "motivo": "..."}.

Responda só JSON, neste formato:
{"fontes": [{"arquivo": "<id do arquivo>", "inteira": true, "rotulo": "<curto>", "cobre": ["<parte>"],
             "tipo": "teoria"},
            {"arquivo": "<id do arquivo>", "paginas": "12-30", "rotulo": "<curto>", "cobre": ["<parte>"],
             "tipo": "teoria"}],
 "lacunas": [{"subitem": "<parte>", "motivo": "<por que não há material>"}]}"""


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
        if c.get("abertura"):
            linhas.append("Abertura (p. 1-2): " + c["abertura"])
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
    total = {f"A{i}": c.get("n_paginas") for i, c in enumerate(candidatos, 1)}
    fontes = []
    for f in dados.get("fontes") or []:
        ident = str(f.get("arquivo", "")).strip().strip("[]")
        if f.get("inteira") is True and total.get(ident):
            f = dict(f, paginas=f"1-{total[ident]}")  # aula inteira: da primeira à última página
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
