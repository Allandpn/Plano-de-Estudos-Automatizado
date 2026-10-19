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

Formato da ficha: proposta §3.1 (0.4.0). Da IA: natureza; temas com disciplina, termos (sinônimos, siglas),
seções e subtemas com a página onde começam (a regra confere a página). Da regra: o resto, mais hash do PDF,
origem (acervo ou apostila do aluno) e gêmeas (a mesma aula em outros cursos).

Ensaio (--saida): catalogo-ensaio.json (as fichas) e catalogo-ensaio.md (para conferir: cada tema com
um "[ ]"). Acervo inteiro (--acervo --db): uma ficha por aula única no catalogo.db; gêmea e arquivo que
não é aula não gastam chamada. Nos dois, rodar de novo continua de onde parou; se a IA parar (limite
da assinatura), o que já saiu fica gravado. Cada ficha guarda a resposta da IA: --reprocessar refaz a
parte da regra (regra nova) sem perguntar de novo.

Uso (contêiner do worker: índice, rede e token do SGE):

    docker compose run --rm --no-deps -T -v ~/catalogo:/saida planejamento \\
        python integracao/catalogo_aulas.py --saida /saida --simular   # monta os pedidos, sem IA
    docker compose run --rm --no-deps -T -v ~/catalogo:/saida planejamento \\
        python integracao/catalogo_aulas.py --saida /saida
    docker compose run --rm --no-deps -T planejamento \
        python integracao/catalogo_aulas.py --acervo --db /dados/material/catalogo.db --limite 200
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from contextlib import closing
from pathlib import Path, PureWindowsPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estrutura_apostilas as ea  # noqa: E402
from acervo import inicio_da_pagina  # noqa: E402
from ia_comum import IaIndisponivel, completar_json  # noqa: E402

TIPOS_SEM_TEMA = {"apresentacao", "gabarito", "bibliografia"}
# Questões ficam fora da faixa do tema: as sessões de questões são feitas no QConcursos/TEC (decisão do usuário,
# 2026-10-19). Elas são registradas à parte, presas ao tema por regra, para uma eventual apostila de questões.
TIPOS_QUESTOES = {"questoes_comentadas", "lista_questoes", "gabarito"}
TIPOS_COM_TRECHO = {"teoria", "resumo", "incidencia", None}
NATUREZAS = {"aula", "revisao", "apresentacao", "outro"}
# Sobe quando muda o que se pede à IA: ficha de versão anterior é perguntada de novo no --acervo.
VERSAO_PEDIDO = 2
PASTA_DO_ALUNO = "99 - Minhas apostilas"
GENERICAS = {"questoes", "comentadas", "conceito", "conceitos", "gerais", "geral", "basicos", "principais",
             "tipos", "sobre", "lista", "caracteristicas", "aplicacoes", "funcionamento", "definicao"}

SISTEMA = """Você monta o catálogo de um acervo de apostilas de concurso público (Estratégia Concursos).
Para UMA aula, diga quais temas ela ensina, com os nomes que um edital de concurso usaria, e onde cada um está.
Responda só com JSON, sem texto fora dele."""

INSTRUCOES = """Responda neste formato:
{"natureza": "aula" | "revisao" | "apresentacao" | "outro",
 "temas": [{"tema": "nome curto, como num edital",
            "disciplina": "disciplina de edital a que o tema pertence (ex.: Redes de Computadores, Banco de Dados,
                           Língua Portuguesa, Direito Tributário)",
            "termos": ["outros nomes, siglas e sinônimos do tema", ...],
            "secoes": [números das seções deste tema],
            "subtemas": [{"nome": "ponto que a aula ensina", "pagina": página do PDF onde ele começa}, ...]}],
 "observacao": "curta, só se houver dúvida"}

Regras:
- natureza: "revisao" para material de reta final (Passo Estratégico, Bizu, resumo); "apresentacao" se a aula
  só apresenta o curso ou o cronograma; "outro" se não é material de estudo.
- Um tema por assunto de edital (1 a 8). O resumo do tema entra no mesmo tema.
- Seções de questões comentadas, lista de questões, gabarito, apresentação e bibliografia NÃO entram em tema
  (as questões são separadas depois, por regra). Não crie tema só de questões.
- Não invente tema que a aula não ensina.
- subtemas: até 8, os pontos que a aula de fato cobre, tirados só do texto acima (sumário, trechos, páginas);
  não complete com o que o tema costuma ter. "pagina" é o número "p. N" onde o ponto aparece acima; se não
  souber, use null.
- termos: até 8, só os que alguém usaria para pedir o mesmo assunto (sigla por extenso, nome antigo, sinônimo).
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


CONTEXTOS = ("inicio", "primeira_linha", "titulos")
# Teste de 2026-10-19 (proposta §4.2): com a primeira linha de cada página da teoria a IA tira subtemas
# específicos do texto; só com o começo de cada seção, poucos (ou completa pelo que o tema costuma ter).
CONTEXTO_PADRAO = "primeira_linha"


def _e_de_questao(linha):
    return any(re.search(r, linha, re.IGNORECASE) for r in ea.BANCAS.values())


def titulos_da_pagina(texto):
    """As linhas com cara de título: curtas, quase só maiúsculas ('NAT REVERSO E O BALANCEAMENTO DE CARGA',
    'P IP 6 / ROTOCOLO V') ou numeradas ('2.3 Tipos de endereço'); sem as de cabeçalho de questão (ano, banca)."""
    saida = []
    for l in (texto or "").splitlines():
        l = " ".join(l.split())
        letras = [c for c in l if c.isalpha()]
        if not 3 <= len(l) <= 80 or len(letras) < 3 or re.search(r"\b(19|20)\d\d\b", l) or _e_de_questao(l):
            continue
        if sum(c.isupper() for c in letras) / len(letras) >= 0.7 or re.match(r"^\d+(\.\d+)*\.?\s+[A-ZÀ-Ú][a-zà-ú]", l):
            saida.append(l)
    return saida


def _contexto_da_teoria(a, paginas, contexto, max_linhas=260):
    """Para cada página das seções de teoria e resumo: a primeira linha, ou as linhas de título."""
    linhas, vistas = [], set()
    for e in a["entradas"]:
        if e["tipo"] in TIPOS_QUESTOES | TIPOS_SEM_TEMA or not e.get("inicio"):
            continue
        for p in range(e["inicio"], e["fim"] + 1):
            if p in vistas:
                continue
            vistas.add(p)
            if contexto == "primeira_linha":
                texto = inicio_da_pagina(paginas.get(p), 90)
            else:
                texto = " | ".join(titulos_da_pagina(paginas.get(p)))
            if texto:
                linhas.append(f"p. {p}: {texto}")
    return linhas[:max_linhas]


def montar_pedido(conn, arquivo_id, curso, nome, trecho=160, max_mapa=150, contexto=CONTEXTO_PADRAO):
    """A ficha por regra e o texto do pedido à IA. Seção = posição na lista do sumário (1, 2, …).
    'contexto': além do começo de cada seção, a primeira linha de cada página da teoria ('primeira_linha',
    o padrão) ou as linhas de título dela ('titulos'); 'inicio' é só o começo de cada seção."""
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
        if contexto != "inicio":
            extra = _contexto_da_teoria(a, paginas, contexto)
            if extra:
                linhas.append("Páginas da teoria (" + ("primeira linha" if contexto == "primeira_linha"
                                                        else "títulos e subtítulos") + "):")
                linhas += extra
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


def palavras_de(texto):
    """As palavras que identificam um subtema: 4 letras ou mais, ou sigla em maiúsculas ('RDP', 'SQL' de 'T-SQL')."""
    saida = []
    for p in re.findall(r"\w+", texto or ""):
        w = ea.chave(p, 10 ** 6)
        if (len(w) >= 4 and w not in GENERICAS) or (len(w) == 3 and p.isupper()):
            saida.append(w)
    return saida


def _subtemas(lista, faixas, textos, perto=3):
    """[{nome, pagina, confirmada[, pagina_ia]}]. A página da IA é confirmada se cai na faixa do tema e metade
    ou mais das palavras do subtema estão nela ou na seguinte (o título pode ficar no pé da página). Se não,
    vale a página mais próxima, até 'perto' antes ou depois e dentro da faixa, que confirma (a IA erra por
    pouco: ensaio de 2026-10-19); a página que ela deu fica em 'pagina_ia'. Aceita a resposta antiga, em que
    o subtema era só o nome."""
    def confirma(pagina, palavras):
        texto = ea.chave((textos.get(pagina) or "") + " " + (textos.get(pagina + 1) or ""), 10 ** 6)
        return bool(palavras) and sum(w in texto for w in palavras) / len(palavras) >= 0.5

    def na_faixa(pagina):
        return any(i <= pagina <= f for i, f in faixas)
    saida = []
    for s in (lista or [])[:8]:
        nome, pagina = (s.get("nome"), s.get("pagina")) if isinstance(s, dict) else (s, None)
        nome = str(nome or "").strip()
        if not nome:
            continue
        pagina = pagina if isinstance(pagina, int) and na_faixa(pagina) else None
        item = {"nome": nome, "pagina": pagina, "confirmada": False}
        if pagina is not None and textos:
            palavras = palavras_de(nome)
            vizinhas = sorted((q for q in range(pagina - perto, pagina + perto + 1) if na_faixa(q)),
                              key=lambda q: (abs(q - pagina), q))
            achada = next((q for q in vizinhas if confirma(q, palavras)), None)
            if achada is not None:
                item.update(pagina=achada, confirmada=True)
                if achada != pagina:
                    item["pagina_ia"] = pagina
        saida.append(item)
    return saida


def interpretar(resposta, a, textos=None):
    """A resposta da IA vira os temas da ficha, com a faixa de páginas de cada um calculada das seções
    apontadas (ou, sem sumário, a que ela deu, limitada ao PDF), e a página de cada subtema conferida no
    texto ('textos': página -> texto). Lança ValueError se não der para usar."""
    if not isinstance(resposta, dict) or not isinstance(resposta.get("temas"), list) or not resposta["temas"]:
        raise ValueError("a resposta não tem a lista 'temas'")
    entradas, temas, problemas = a["entradas"], [], []

    def de_teoria(s):
        return entradas[s - 1]["tipo"] not in TIPOS_QUESTOES
    for t in resposta["temas"]:
        if not isinstance(t, dict) or not str(t.get("tema") or "").strip():
            raise ValueError("tema sem nome")
        tema = {"tema": str(t["tema"]).strip(), "disciplina": str(t.get("disciplina") or "").strip() or None,
                "termos": [str(x).strip() for x in (t.get("termos") or []) if str(x).strip()][:8]}
        if entradas:
            secoes = [s for s in (t.get("secoes") or []) if isinstance(s, int)]
            fora = [s for s in secoes if not 1 <= s <= len(entradas)]
            if fora:
                problemas.append(f"{tema['tema']}: seções inexistentes {fora}")
            validas = [s for s in secoes if 1 <= s <= len(entradas) and de_teoria(s)]
            tema["secoes"] = validas
            tema["tipos"] = sorted({entradas[s - 1]["tipo"] or "?" for s in validas})
            tema["paginas"] = _juntar([(entradas[s - 1]["inicio"], entradas[s - 1]["fim"]) for s in validas
                                       if entradas[s - 1].get("inicio")])
        else:
            p = t.get("paginas")
            if not (isinstance(p, list) and len(p) == 2 and all(isinstance(x, int) for x in p) and 1 <= p[0] <= p[1] <= a["n"]):
                raise ValueError(f"tema {tema['tema']!r} sem 'paginas' válidas (1 a {a['n']})")
            tema["paginas"] = [p]
        tema["subtemas"] = _subtemas(t.get("subtemas"), tema["paginas"], textos)
        temas.append(tema)
    temas = [t for t in temas if not entradas or t["secoes"]]
    if entradas and not temas:
        raise ValueError("nenhum tema aponta seção de teoria existente")
    usadas = {s for t in temas for s in t.get("secoes", [])}
    sem_tema = [k for k, e in enumerate(entradas, 1)
                if k not in usadas and e["tipo"] not in TIPOS_SEM_TEMA | TIPOS_QUESTOES]
    questoes_da_aula = []
    for k, e in enumerate(entradas, 1):
        if e["tipo"] not in TIPOS_QUESTOES or e["tipo"] == "gabarito" or not e.get("inicio"):
            continue
        # O sumário A diz o tema das questões ('NAT e PAT - Questões Comentadas - FCC'): vão para o tema da IA
        # que tem a teoria com esse mesmo nome; senão, ficam como questões da aula.
        dono = next((t for t in temas if any(ea.chave(entradas[s - 1]["tema"], 10 ** 6) == ea.chave(e["tema"], 10 ** 6)
                                             for s in t["secoes"])), None) if ea.chave(e["tema"], 10 ** 6) else None
        destino = dono.setdefault("questoes", []) if dono else questoes_da_aula
        destino.append({"secao": k, "tipo": e["tipo"], "banca": e["banca"], "paginas": [e["inicio"], e["fim"]]})
    natureza = resposta.get("natureza") if resposta.get("natureza") in NATUREZAS else "aula"
    return {"natureza": natureza, "temas": temas, "secoes_sem_tema": sem_tema, "questoes_da_aula": questoes_da_aula,
            "problemas": problemas,
            "observacao": str(resposta.get("observacao") or "").strip() or None}


def ficha(sge, conn, arquivo, simular=False, contexto=CONTEXTO_PADRAO, resposta=None, gemeas=()):
    """Uma ficha: a estrutura por regra e os temas pela IA. Resposta ilegível ganha uma segunda chance com
    o erro; IaIndisponivel sobe (o ensaio para e grava o que tem). Com 'resposta' (a que a IA já deu),
    só refaz a parte da regra, sem perguntar de novo. 'gemeas': caminhos das outras cópias da aula."""
    arquivo_id, curso, nome = arquivo
    a, pedido = montar_pedido(conn, arquivo_id, curso, nome, contexto=contexto)
    textos = dict(conn.execute("SELECT pagina, texto FROM paginas WHERE arquivo_id = ?", (arquivo_id,)).fetchall())
    hash_pdf = (conn.execute("SELECT hash FROM arquivos WHERE id = ?", (arquivo_id,)).fetchone() or [None])[0]
    base = {"caminho": caminho_windows(curso, nome), "hash": hash_pdf,
            "origem": "aluno" if PASTA_DO_ALUNO in (curso or "") else "acervo", "gemeas": list(gemeas),
            "versao_pedido": VERSAO_PEDIDO, "paginas": a["n"], "aula": a["aula"][0],
            "formato": a["formato"], "banca": a["banca"][0], "banca_origem": a["banca"][1],
            "ilegiveis": a["ilegiveis"], "incidencia": a["incidencia"],
            "secoes": [{"tema": e["tema"], "tipo": e["tipo"], "banca": e["banca"], "inicio": e.get("inicio"),
                        "fim": e.get("fim"), "confirmada": e.get("confirmada", False)} for e in a["entradas"]],
            "tamanho_pedido": len(pedido)}
    if simular:
        return dict(base, pedido=pedido)
    if resposta is not None:
        return dict(base, resposta=resposta, contexto=contexto, **interpretar(resposta, a, textos))
    erro = None
    for _ in range(2):
        texto = pedido if erro is None else f"{pedido}\n\nSua resposta anterior não serviu: {erro}. Responda de novo."
        try:
            resposta = completar_json(sge, SISTEMA, texto)
            return dict(base, resposta=resposta, contexto=contexto, **interpretar(resposta, a, textos))
        except ValueError as e:
            erro = str(e)
    return dict(base, falha=erro)


def resposta_gravada(f):
    """A resposta da IA guardada na ficha; fichas antigas (sem ela) são remontadas dos temas."""
    if f.get("resposta"):
        return f["resposta"]
    return {"natureza": f.get("natureza"), "observacao": f.get("observacao"),
            "temas": [{k: t[k] for k in ("tema", "disciplina", "termos", "subtemas", "secoes", "paginas") if k in t}
                      if t.get("secoes") else {"tema": t["tema"], "subtemas": t["subtemas"], "paginas": t["paginas"][0]}
                      for t in f.get("temas", [])]}


def reprocessar(conn, saida, contexto=CONTEXTO_PADRAO, log=print):
    """Refaz a parte da regra das fichas já gravadas (regra nova, mesma resposta da IA), sem chamar a IA."""
    sufixo = "" if contexto == CONTEXTO_PADRAO else f"-{contexto}"
    arquivo_json = Path(saida) / f"catalogo-ensaio{sufixo}.json"
    fichas = []
    for f in json.loads(arquivo_json.read_text(encoding="utf-8")):
        if f.get("falha"):
            fichas.append(f)
            continue
        p = PureWindowsPath(f["caminho"])
        linha = conn.execute("SELECT id, curso, nome_arquivo FROM arquivos WHERE curso = ? AND nome_arquivo = ?",
                             (str(p.parent), p.name)).fetchone()
        try:
            fichas.append(ficha(None, conn, linha, contexto=f.get("contexto", contexto), resposta=resposta_gravada(f)))
        except ValueError as e:
            fichas.append(dict(f, falha=f"reprocessada: {e}"))
            log(f"{f['caminho']}: {e}")
    arquivo_json.write_text(json.dumps(fichas, ensure_ascii=False, indent=1), encoding="utf-8")
    (Path(saida) / f"catalogo-ensaio{sufixo}.md").write_text(relatorio(fichas), encoding="utf-8")
    return fichas


def _faixas(paginas):
    return ", ".join(f"{i}–{f}" if i != f else str(i) for i, f in paginas) or "?"


def _questoes(qs):
    return "; ".join(f"p. {q['paginas'][0]}–{q['paginas'][1]} {q['tipo'].replace('_', ' ')}"
                     + (f" {q['banca']}" if q["banca"] else "") for q in qs)


def _subtema(s):
    if isinstance(s, str):
        return s
    if s["pagina"] is None:
        return s["nome"]
    return f"{s['nome']} (p. {s['pagina']} {'✓' if s['confirmada'] else '?'})"


def relatorio(fichas):
    subs = [s for f in fichas for t in f.get("temas", []) for s in t.get("subtemas", []) if isinstance(s, dict)]
    com_pagina = [s for s in subs if s["pagina"] is not None]
    saida = ["# Ensaio do catálogo de aulas", "",
             "Cada tema com um `[ ]`: marque `[x]` se confere, ou escreva ao lado o que está errado "
             "(tema que a aula não ensina, nome ruim, faixa de páginas errada, tema faltando).", ""]
    if subs:
        saida += [f"Subtemas: {len(subs)}; com página dada pela IA: {len(com_pagina)}; página confirmada no texto: "
                  f"{sum(s['confirmada'] for s in com_pagina)} (✓ confirmada, ? não confirmada).", ""]
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
            disciplina = f" · _{t['disciplina']}_" if t.get("disciplina") else ""
            saida.append(f"- [ ] **{t['tema']}**{disciplina} — p. {_faixas(t['paginas'])}{secoes}")
            if t.get("termos"):
                saida.append(f"  - termos: {'; '.join(t['termos'])}")
            if t["subtemas"]:
                saida.append(f"  - {'; '.join(_subtema(s) for s in t['subtemas'])}")
            if t.get("questoes"):
                saida.append(f"  - questões (à parte): {_questoes(t['questoes'])}")
        if f.get("secoes_sem_tema"):
            nomes = [f"{k}. {f['secoes'][k - 1]['tema']} ({f['secoes'][k - 1]['tipo']})" for k in f["secoes_sem_tema"]]
            saida.append(f"- seções sem tema: {'; '.join(nomes)}")
        if f.get("questoes_da_aula"):
            saida.append(f"- questões da aula, sem tema (à parte): {_questoes(f['questoes_da_aula'])}")
        for p in f.get("problemas", []):
            saida.append(f"- problema: {p}")
        if f.get("observacao"):
            saida.append(f"- observação da IA: {f['observacao']}")
        saida.append("")
    return "\n".join(saida)


def ensaio(sge, conn, saida, cursos, total=30, simular=False, log=print, contexto=CONTEXTO_PADRAO, so=None):
    """Pergunta à IA pelas aulas que ainda não têm ficha em saida/catalogo-ensaio.json e regrava o .json e
    o .md a cada aula. Devolve (fichas, parou_por) — parou_por é a mensagem se a IA parou."""
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    sufixo = "" if contexto == CONTEXTO_PADRAO else f"-{contexto}"
    arquivo_json = saida / (f"catalogo-simulado{sufixo}.json" if simular else f"catalogo-ensaio{sufixo}.json")
    fichas = json.loads(arquivo_json.read_text(encoding="utf-8")) if arquivo_json.exists() and not simular else []
    feitas = {f["caminho"] for f in fichas if not f.get("falha")}
    fichas = [f for f in fichas if f["caminho"] in feitas]
    parou = None
    for arquivo in escolher_aulas(conn, cursos, total):
        caminho = caminho_windows(arquivo[1], arquivo[2])
        if caminho in feitas or (so and not any(t in caminho for t in so)):
            continue
        try:
            f = ficha(sge, conn, arquivo, simular, contexto)
        except IaIndisponivel as e:
            parou = str(e)
            log(f"A IA parou em {caminho}: {e}. O que já saiu está gravado; rode de novo depois.")
            break
        fichas.append(f)
        log(f"{len(fichas):2d}. {caminho} — " + (f"pedido de {f['tamanho_pedido']} caracteres" if simular else
                                                f"{len(f.get('temas', []))} temas" if not f.get("falha") else f"FALHA: {f['falha']}"))
        arquivo_json.write_text(json.dumps(fichas, ensure_ascii=False, indent=1), encoding="utf-8")
        if not simular:
            (saida / f"catalogo-ensaio{sufixo}.md").write_text(relatorio(fichas), encoding="utf-8")
    return fichas, parou


def grupos_de_gemeas(conn, log=print):
    """{arquivo_id: id da primeira cópia} para o acervo inteiro: mesma aula = metade ou mais das páginas 3 a 14
    iguais (a regra de acervo.py), numa passada só pelo índice (consulta por aula varreria tudo de novo)."""
    t0, por_arquivo = time.time(), {}
    for aid, p, t in conn.execute("SELECT arquivo_id, pagina, texto FROM paginas WHERE pagina BETWEEN 3 AND 14"):
        assinatura = re.sub(r"[\d\s]+", "", (t or "").lower())[:400]
        if assinatura:
            por_arquivo.setdefault(aid, set()).add(assinatura)
    dono, indice, unicas = {}, {}, {}
    for (aid,) in conn.execute("SELECT id FROM arquivos ORDER BY curso, nome_arquivo"):
        miolo = por_arquivo.get(aid, set())
        contagem = {}
        for m in miolo:
            for u in indice.get(m, ()):
                contagem[u] = contagem.get(u, 0) + 1
        igual = next((u for u, c in contagem.items() if c >= max(2, min(len(miolo), len(unicas[u])) // 2)), None)
        if igual is not None:
            dono[aid] = igual
            continue
        dono[aid] = aid
        unicas[aid] = miolo
        for m in miolo:
            indice.setdefault(m, []).append(aid)
    log(f"gêmeas: {len(dono) - len(unicas)} cópias de {len(unicas)} aulas únicas ({time.time() - t0:.0f}s)")
    return dono


class CatalogoDb:
    """catalogo.db: uma ficha por arquivo (JSON), com hash e versão do pedido para saber o que refazer."""

    def __init__(self, caminho):
        self.conn = sqlite3.connect(caminho)
        self.conn.execute("CREATE TABLE IF NOT EXISTS fichas (arquivo_id INTEGER PRIMARY KEY, caminho TEXT NOT NULL, "
                          "hash TEXT, versao_pedido INTEGER, situacao TEXT NOT NULL, ficha TEXT NOT NULL, "
                          "atualizado_em TEXT NOT NULL)")
        self.conn.commit()

    def feita(self, arquivo_id, hash_pdf):
        linha = self.conn.execute("SELECT hash, versao_pedido, situacao FROM fichas WHERE arquivo_id = ?",
                                  (arquivo_id,)).fetchone()
        if not linha or linha[0] != hash_pdf:
            return False
        return linha[2] in ("fora", "gemea") or (linha[2] == "ok" and linha[1] == VERSAO_PEDIDO)

    def gravar(self, arquivo_id, f, situacao):
        self.conn.execute("INSERT OR REPLACE INTO fichas VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (arquivo_id, f["caminho"], f.get("hash"), f.get("versao_pedido"), situacao,
                           json.dumps(f, ensure_ascii=False), time.strftime("%Y-%m-%d %H:%M:%S")))
        self.conn.commit()

    def fichas(self):
        return [json.loads(t) for (t,) in self.conn.execute("SELECT ficha FROM fichas ORDER BY caminho")]


def catalogar_acervo(sge, conn, db, limite=None, log=print, contexto=CONTEXTO_PADRAO):
    """Uma ficha por aula única do acervo. Arquivo que não é aula e gêmea são gravados sem chamar a IA (a
    gêmea aponta a primeira cópia, que lista todas). Para quando a IA para ou depois de 'limite' chamadas.
    Devolve (chamadas, parou_por)."""
    dono = grupos_de_gemeas(conn, log)
    copias = {}
    arquivos = conn.execute("SELECT id, curso, nome_arquivo, hash FROM arquivos ORDER BY curso, nome_arquivo").fetchall()
    for aid, curso, nome, _ in arquivos:
        if dono.get(aid, aid) != aid:
            copias.setdefault(dono[aid], []).append(caminho_windows(curso, nome))
    caminhos = {aid: caminho_windows(curso, nome) for aid, curso, nome, _ in arquivos}
    chamadas, t0, parou = 0, time.time(), None
    for aid, curso, nome, hash_pdf in arquivos:
        if db.feita(aid, hash_pdf):
            continue
        base = {"caminho": caminhos[aid], "hash": hash_pdf, "versao_pedido": VERSAO_PEDIDO}
        if dono.get(aid, aid) != aid:
            db.gravar(aid, dict(base, gemea_de=caminhos[dono[aid]]), "gemea")
            continue
        if ea.analisar_aula(conn, aid)["fora"]:
            db.gravar(aid, dict(base, fora="curto e sem sumário: não é aula"), "fora")
            continue
        if limite is not None and chamadas >= limite:
            log(f"limite de {limite} chamadas: pare aqui e rode de novo para continuar")
            break
        try:
            f = ficha(sge, conn, (aid, curso, nome), contexto=contexto, gemeas=copias.get(aid, []))
        except IaIndisponivel as e:
            parou = str(e)
            log(f"A IA parou em {caminhos[aid]}: {e}. O que já saiu está gravado; rode de novo depois.")
            break
        chamadas += 1
        db.gravar(aid, f, "falha" if f.get("falha") else "ok")
        log(f"{chamadas}. {caminhos[aid]} — " + (f"FALHA: {f['falha']}" if f.get("falha") else
                                               f"{len(f['temas'])} temas") + f" ({(time.time() - t0) / chamadas:.0f}s por aula)")
    return chamadas, parou


def main():
    ap = argparse.ArgumentParser(description="Ensaio do catálogo de aulas (estrutura por regra, temas pela IA).")
    ap.add_argument("--saida", help="pasta do catalogo-ensaio.json e .md (ensaio)")
    ap.add_argument("--total", type=int, default=30)
    ap.add_argument("--curso", action="append", help="trecho do nome da pasta (repetível); padrão: a amostra do passo 0")
    ap.add_argument("--simular", action="store_true", help="monta os pedidos (catalogo-simulado.json) sem chamar a IA")
    ap.add_argument("--contexto", choices=CONTEXTOS, default=CONTEXTO_PADRAO,
                    help="o que a IA vê das páginas da teoria além do começo de cada seção (padrão: a primeira linha)")
    ap.add_argument("--so", action="append", help="só as aulas cujo caminho tem este trecho (repetível)")
    ap.add_argument("--reprocessar", action="store_true",
                    help="refaz a parte da regra das fichas gravadas, com a mesma resposta da IA (sem chamá-la)")
    ap.add_argument("--acervo", action="store_true", help="catalogar o acervo inteiro no --db (aulas únicas)")
    ap.add_argument("--db", help="catalogo.db (com --acervo)")
    ap.add_argument("--limite", type=int, help="com --acervo: no máximo N chamadas à IA nesta rodada")
    ap.add_argument("--indice", default=os.environ.get("INDICE_DB"))
    args = ap.parse_args()
    if not args.acervo and not args.saida:
        ap.error("--saida é obrigatório fora do --acervo")
    if args.acervo and not args.db:
        ap.error("--acervo pede --db")
    if args.reprocessar:
        with closing(sqlite3.connect(f"file:{args.indice}?mode=ro", uri=True)) as conn:
            reprocessar(conn, args.saida, args.contexto)
        return
    sge = None
    if not args.simular:
        from sge_api import SgeApi
        sge = SgeApi(os.environ.get("SGE_URL", "http://app:8080"), os.environ["INTERNAL_TOKEN"])
    with closing(sqlite3.connect(f"file:{args.indice}?mode=ro", uri=True)) as conn:
        if args.acervo:
            _, parou = catalogar_acervo(sge, conn, CatalogoDb(args.db), args.limite, contexto=args.contexto)
        else:
            _, parou = ensaio(sge, conn, args.saida, args.curso or ea.AMOSTRA, args.total, args.simular,
                              contexto=args.contexto, so=args.so)
    sys.exit(2 if parou else 0)


if __name__ == "__main__":
    main()
