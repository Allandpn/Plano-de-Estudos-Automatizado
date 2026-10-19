#!/usr/bin/env python3
"""
catalogo_aulas.py — Ensaio do catálogo de aulas (`docs/proposta-catalogo-aulas-e-modos.md` §3.1 e §4):
uma ficha por aula, para ~30 aulas de cursos diferentes, conferida pelo aluno antes de rodar no acervo
inteiro.

O que sai por REGRA (estrutura_apostilas, R1–R10): seções do sumário com tipo e faixa de páginas, banca,
incidência, páginas ilegíveis, número da aula. O que sai da IA (uma chamada por aula, pelo proxy do SGE —
a assinatura do usuário): quais TEMAS a aula ensina, com os nomes que um edital usaria, os subtemas e
quais seções são de cada tema. A IA não dá página quando há sumário: a faixa de cada tema é a soma das
faixas das seções que ela apontou. Sem sumário, ela vê o começo de cada página e dá a faixa.

Saída em --saida: catalogo-ensaio.json (as fichas) e catalogo-ensaio.md (para conferir: cada tema com
um "[ ]"). Rodar de novo continua de onde parou: aula que já tem ficha não é perguntada outra vez.
Se a IA parar (limite da assinatura), o que já saiu fica gravado.

Uso (contêiner do worker: índice, rede e token do SGE):

    docker compose run --rm --no-deps -T -v ~/catalogo:/saida planejamento \\
        python integracao/catalogo_aulas.py --saida /saida --simular   # monta os pedidos, sem IA
    docker compose run --rm --no-deps -T -v ~/catalogo:/saida planejamento \\
        python integracao/catalogo_aulas.py --saida /saida
"""

import argparse
import json
import os
import sqlite3
import sys
from contextlib import closing
from pathlib import Path, PureWindowsPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estrutura_apostilas as ea  # noqa: E402
from acervo import inicio_da_pagina  # noqa: E402
from ia_comum import IaIndisponivel, completar_json  # noqa: E402

TIPOS_SEM_TEMA = {"apresentacao", "gabarito", "bibliografia"}
TIPOS_COM_TRECHO = {"teoria", "resumo", "incidencia", None}
NATUREZAS = {"aula", "revisao", "apresentacao", "outro"}

SISTEMA = """Você monta o catálogo de um acervo de apostilas de concurso público (Estratégia Concursos).
Para UMA aula, diga quais temas ela ensina, com os nomes que um edital de concurso usaria, e onde cada um está.
Responda só com JSON, sem texto fora dele."""

INSTRUCOES = """Responda neste formato:
{"natureza": "aula" | "revisao" | "apresentacao" | "outro",
 "temas": [{"tema": "nome curto, como num edital", "subtemas": ["ponto que a aula ensina", ...],
            "secoes": [números das seções deste tema]}],
 "observacao": "curta, só se houver dúvida"}

Regras:
- natureza: "revisao" para material de reta final (Passo Estratégico, Bizu, resumo); "apresentacao" se a aula
  só apresenta o curso ou o cronograma; "outro" se não é material de estudo.
- Um tema por assunto de edital (1 a 8). Questões comentadas, lista e resumo do mesmo tema entram no mesmo tema.
- Não invente tema que a aula não ensina; seção de apresentação, gabarito e bibliografia não entram em tema.
- subtemas: até 8, os pontos que a aula de fato cobre (do sumário e dos trechos).
- Se não houver seções numeradas abaixo, troque "secoes" por "paginas": [primeira, última] de cada tema."""


def caminho_windows(curso, nome):
    """'Cursos Regulares\\22 - …\\aula 03.pdf': o caminho relativo a apostilas/, como no Explorer."""
    return str(PureWindowsPath(curso or "", nome or ""))


def escolher_aulas(conn, cursos, total=30):
    """Aulas espalhadas pelos cursos (1/4, 1/2 e 3/4 de cada um, para não repetir as da medição do passo 0,
    que olhou primeira, meio e última), uma de cada curso por vez até `total`. Arquivo que não é aula
    (curto e sem sumário) fica fora."""
    por_curso = []
    for padrao in cursos:
        arquivos = conn.execute("SELECT id, curso, nome_arquivo FROM arquivos WHERE curso LIKE ? ORDER BY nome_arquivo",
                                (f"%{padrao}%",)).fetchall()
        posicoes = sorted({int(len(arquivos) * f) for f in (0.25, 0.5, 0.75)}) if arquivos else []
        candidatas = [arquivos[i] for i in posicoes]
        candidatas += [a for a in arquivos if a not in candidatas]
        por_curso.append(candidatas)
    escolhidas = []
    while len(escolhidas) < total and any(por_curso):
        for fila in por_curso:
            while fila and len(escolhidas) < total:
                arquivo = fila.pop(0)
                if not ea.analisar_aula(conn, arquivo[0])["fora"]:
                    escolhidas.append(arquivo)
                    break
    return escolhidas


def montar_pedido(conn, arquivo_id, curso, nome, trecho=160, max_mapa=150):
    """A ficha por regra e o texto do pedido à IA. Seção = posição na lista do sumário (1, 2, …)."""
    a = ea.analisar_aula(conn, arquivo_id)
    paginas = dict(conn.execute("SELECT pagina, texto FROM paginas WHERE arquivo_id = ?", (arquivo_id,)).fetchall())
    linhas = [f"Curso: {curso}", f"Arquivo: {nome} ({a['n']} páginas)",
              f"Abertura: {' | '.join(inicio_da_pagina(paginas.get(p), 140) for p in (1, 2, 3) if paginas.get(p))}"]
    if a["incidencia"]:
        linhas.append("Incidência por subassunto (da própria apostila): "
                      + "; ".join(f"{s} {v:g}%" for s, v in a["incidencia"]["subassuntos"]))
    if a["entradas"]:
        linhas.append("Seções (do sumário da aula; tipo; páginas no PDF; começo da página):")
        for k, e in enumerate(a["entradas"], 1):
            faixa = f"p. {e['inicio']}–{e['fim']}" if e.get("inicio") else "p. ?"
            extra = f" | {e['rotulo']}" if e.get("rotulo") else ""
            texto = ""
            if e["tipo"] in TIPOS_COM_TRECHO and e.get("inicio"):
                texto = f" | «{inicio_da_pagina(paginas.get(e['inicio']), trecho)}»"
            linhas.append(f"{k}. {e['tema']} | {e['tipo'] or '?'}{extra} | {faixa}{texto}")
    else:
        linhas.append("Sem sumário. Começo de cada página:")
        linhas += [f"p. {p}: {inicio_da_pagina(paginas[p], 90)}" for p in sorted(paginas)[:max_mapa]]
    return a, "\n".join(linhas) + "\n\n" + INSTRUCOES


def _juntar(faixas):
    juntas = []
    for ini, fim in sorted(faixas):
        if juntas and ini <= juntas[-1][1] + 1:
            juntas[-1][1] = max(juntas[-1][1], fim)
        else:
            juntas.append([ini, fim])
    return juntas


def interpretar(resposta, a):
    """A resposta da IA vira os temas da ficha, com a faixa de páginas de cada um calculada das seções
    apontadas (ou, sem sumário, a que ela deu, limitada ao PDF). Lança ValueError se não der para usar."""
    if not isinstance(resposta, dict) or not isinstance(resposta.get("temas"), list) or not resposta["temas"]:
        raise ValueError("a resposta não tem a lista 'temas'")
    entradas, temas, problemas = a["entradas"], [], []
    for t in resposta["temas"]:
        if not isinstance(t, dict) or not str(t.get("tema") or "").strip():
            raise ValueError("tema sem nome")
        tema = {"tema": str(t["tema"]).strip(), "subtemas": [str(s) for s in (t.get("subtemas") or [])][:8]}
        if entradas:
            secoes = [s for s in (t.get("secoes") or []) if isinstance(s, int)]
            fora = [s for s in secoes if not 1 <= s <= len(entradas)]
            if fora:
                problemas.append(f"{tema['tema']}: seções inexistentes {fora}")
            validas = [s for s in secoes if 1 <= s <= len(entradas)]
            tema["secoes"] = validas
            tema["tipos"] = sorted({entradas[s - 1]["tipo"] or "?" for s in validas})
            tema["paginas"] = _juntar([(entradas[s - 1]["inicio"], entradas[s - 1]["fim"]) for s in validas
                                       if entradas[s - 1].get("inicio")])
        else:
            p = t.get("paginas")
            if not (isinstance(p, list) and len(p) == 2 and all(isinstance(x, int) for x in p) and 1 <= p[0] <= p[1] <= a["n"]):
                raise ValueError(f"tema {tema['tema']!r} sem 'paginas' válidas (1 a {a['n']})")
            tema["paginas"] = [p]
        temas.append(tema)
    if entradas and not any(t["secoes"] for t in temas):
        raise ValueError("nenhum tema aponta seção existente")
    usadas = {s for t in temas for s in t.get("secoes", [])}
    sem_tema = [k for k, e in enumerate(entradas, 1) if k not in usadas and e["tipo"] not in TIPOS_SEM_TEMA]
    natureza = resposta.get("natureza") if resposta.get("natureza") in NATUREZAS else "aula"
    return {"natureza": natureza, "temas": temas, "secoes_sem_tema": sem_tema, "problemas": problemas,
            "observacao": str(resposta.get("observacao") or "").strip() or None}


def ficha(sge, conn, arquivo, simular=False):
    """Uma ficha: a estrutura por regra e os temas pela IA. Resposta ilegível ganha uma segunda chance com
    o erro; IaIndisponivel sobe (o ensaio para e grava o que tem)."""
    arquivo_id, curso, nome = arquivo
    a, pedido = montar_pedido(conn, arquivo_id, curso, nome)
    base = {"caminho": caminho_windows(curso, nome), "paginas": a["n"], "aula": a["aula"][0],
            "formato": a["formato"], "banca": a["banca"][0], "banca_origem": a["banca"][1],
            "ilegiveis": a["ilegiveis"], "incidencia": a["incidencia"],
            "secoes": [{"tema": e["tema"], "tipo": e["tipo"], "banca": e["banca"], "inicio": e.get("inicio"),
                        "fim": e.get("fim"), "confirmada": e.get("confirmada", False)} for e in a["entradas"]],
            "tamanho_pedido": len(pedido)}
    if simular:
        return dict(base, pedido=pedido)
    erro = None
    for _ in range(2):
        texto = pedido if erro is None else f"{pedido}\n\nSua resposta anterior não serviu: {erro}. Responda de novo."
        try:
            return dict(base, **interpretar(completar_json(sge, SISTEMA, texto), a))
        except ValueError as e:
            erro = str(e)
    return dict(base, falha=erro)


def _faixas(paginas):
    return ", ".join(f"{i}–{f}" if i != f else str(i) for i, f in paginas) or "?"


def relatorio(fichas):
    saida = ["# Ensaio do catálogo de aulas", "",
             "Cada tema com um `[ ]`: marque `[x]` se confere, ou escreva ao lado o que está errado "
             "(tema que a aula não ensina, nome ruim, faixa de páginas errada, tema faltando).", ""]
    for f in fichas:
        saida += [f"## {f['caminho']}", "",
                  f"{f['paginas']} págs · aula {f['aula'] if f['aula'] is not None else '?'} · formato "
                  f"{f['formato'] or '—'} · banca {', '.join(f['banca']) or '—'} ({f['banca_origem'] or '—'})"
                  + (f" · natureza **{f['natureza']}**" if f.get("natureza") else "")
                  + (f" · {len(f['ilegiveis'])} págs ilegíveis" if f["ilegiveis"] else ""), ""]
        if f.get("falha"):
            saida += [f"**A IA não deu resposta utilizável:** {f['falha']}", ""]
            continue
        for t in f.get("temas", []):
            secoes = f" · seções {', '.join(map(str, t['secoes']))} ({', '.join(t['tipos'])})" if t.get("secoes") else ""
            saida.append(f"- [ ] **{t['tema']}** — p. {_faixas(t['paginas'])}{secoes}")
            if t["subtemas"]:
                saida.append(f"  - {'; '.join(t['subtemas'])}")
        if f.get("secoes_sem_tema"):
            nomes = [f"{k}. {f['secoes'][k - 1]['tema']} ({f['secoes'][k - 1]['tipo']})" for k in f["secoes_sem_tema"]]
            saida.append(f"- seções sem tema: {'; '.join(nomes)}")
        for p in f.get("problemas", []):
            saida.append(f"- problema: {p}")
        if f.get("observacao"):
            saida.append(f"- observação da IA: {f['observacao']}")
        saida.append("")
    return "\n".join(saida)


def ensaio(sge, conn, saida, cursos, total=30, simular=False, log=print):
    """Pergunta à IA pelas aulas que ainda não têm ficha em saida/catalogo-ensaio.json e regrava o .json e
    o .md a cada aula. Devolve (fichas, parou_por) — parou_por é a mensagem se a IA parou."""
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    arquivo_json = saida / ("catalogo-simulado.json" if simular else "catalogo-ensaio.json")
    fichas = json.loads(arquivo_json.read_text(encoding="utf-8")) if arquivo_json.exists() and not simular else []
    feitas = {f["caminho"] for f in fichas if not f.get("falha")}
    fichas = [f for f in fichas if f["caminho"] in feitas]
    parou = None
    for arquivo in escolher_aulas(conn, cursos, total):
        caminho = caminho_windows(arquivo[1], arquivo[2])
        if caminho in feitas:
            continue
        try:
            f = ficha(sge, conn, arquivo, simular)
        except IaIndisponivel as e:
            parou = str(e)
            log(f"A IA parou em {caminho}: {e}. O que já saiu está gravado; rode de novo depois.")
            break
        fichas.append(f)
        log(f"{len(fichas):2d}. {caminho} — " + (f"pedido de {f['tamanho_pedido']} caracteres" if simular else
                                                f"{len(f.get('temas', []))} temas" if not f.get("falha") else f"FALHA: {f['falha']}"))
        arquivo_json.write_text(json.dumps(fichas, ensure_ascii=False, indent=1), encoding="utf-8")
        if not simular:
            (saida / "catalogo-ensaio.md").write_text(relatorio(fichas), encoding="utf-8")
    return fichas, parou


def main():
    ap = argparse.ArgumentParser(description="Ensaio do catálogo de aulas (estrutura por regra, temas pela IA).")
    ap.add_argument("--saida", required=True, help="pasta do catalogo-ensaio.json e .md")
    ap.add_argument("--total", type=int, default=30)
    ap.add_argument("--curso", action="append", help="trecho do nome da pasta (repetível); padrão: a amostra do passo 0")
    ap.add_argument("--simular", action="store_true", help="monta os pedidos (catalogo-simulado.json) sem chamar a IA")
    ap.add_argument("--indice", default=os.environ.get("INDICE_DB"))
    args = ap.parse_args()
    sge = None
    if not args.simular:
        from sge_api import SgeApi
        sge = SgeApi(os.environ.get("SGE_URL", "http://app:8080"), os.environ["INTERNAL_TOKEN"])
    with closing(sqlite3.connect(f"file:{args.indice}?mode=ro", uri=True)) as conn:
        _, parou = ensaio(sge, conn, args.saida, args.curso or ea.AMOSTRA, args.total, args.simular)
    sys.exit(2 if parou else 0)


if __name__ == "__main__":
    main()
