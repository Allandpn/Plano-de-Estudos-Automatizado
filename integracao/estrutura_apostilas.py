#!/usr/bin/env python3
"""
estrutura_apostilas.py — Como as apostilas do acervo são montadas? Medição SEM IA, antes de definir as
regras do catálogo de aulas (decisão de 2026-10-19: nenhuma chamada de IA antes de as regras estarem
definidas e testadas em tipos diferentes de curso).

Para uma amostra de aulas de cursos de tipos diferentes (curso regular, pós-edital, especialidade,
passo estratégico, bizu, lei), lê só o índice (indice.db) e mostra, por aula, as regras R1–R10 de
`docs/proposta-catalogo-aulas-e-modos.md` §4.1:

- o SUMÁRIO, em um de quatro formatos (nenhuma aula tem marcadores do PDF):
  A "N) Tema - Tipo [- Banca] ...... página" (regular, pós-edital): a extração devolve os pontos da
    pontilhada intercalados nas letras; tirados os pontos, a página fica grudada na última palavra
    ("Cesgranrio17") e é a posição no PDF (R1);
  B "N. Título 02" (aulas mais antigas) e C "Título ...... 2" (Passo Estratégico): página impressa;
    página que diminui começa outra sequência, com deslocamento próprio (R2);
  D Bizu: sem sumário com página; uma tabela "assunto → bizus 1 a 4 → link" e o corpo abre cada
    assunto com o primeiro bizu da faixa ("5. Classificações…") (R3);
- onde cada seção começa no PDF (o deslocamento que mais se repete, confirmado pelo tema escrito na
  página, inteiro ou em pedaços sem a primeira letra: "P IP 6 / ROTOCOLO V") e onde termina (R4, R5);
- o tipo de cada seção (teoria, resumo, questões, lista, gabarito, incidência, questionário…) (R6);
- a tabela de incidência por subassunto, com banca e período (Passo, Bizu) (R7);
- a banca da aula: do sumário, senão da incidência, senão a contagem no texto (R8);
- páginas ilegíveis (imagem com OCR lixo ou texto colado), que a busca nunca acha (R9);
- o número da aula, do conteúdo ("AULA 14"), não do nome do arquivo (R10);
- se o arquivo é aula (curto e sem sumário — aviso, orientação de estudos — fica fora).

E, no fim, o resumo por curso. É isso que diz se o catálogo pode sair do sumário, por regra, e onde
a IA ainda é necessária (casar os temas com os assuntos do edital).

Uso (no contêiner do worker, que tem o índice):

    docker compose exec -T planejamento python integracao/estrutura_apostilas.py > ~/estrutura.md
    docker compose exec -T planejamento python integracao/estrutura_apostilas.py --curso "Ciência de Dados" --aulas 5
"""

import argparse
import os
import re
import sqlite3
import unicodedata
from collections import Counter
from contextlib import closing

# Um curso de cada tipo; o LIKE casa o trecho com o nome da pasta.
AMOSTRA = [
    "00 - Curso Regular\\09 - Redes de Computadores",
    "Cursos Regulares\\22 - Curso Completo de Tecnologia da Informação",
    "Cursos Regulares\\50 - Especialidade TI - Ciência de Dados",
    "SEFAZ-CE 2026\\28 - Redes e Segurança",
    "TCE-SC 2026 - Pos Edital\\01 - Banco de Dados",
    "07 - TSE Unificado\\02 - Banco de Dados",
    "Cursos Regulares\\17 - Curso Básico de Português",
    "Cursos Regulares\\39 - Passo Estratégico Básico de Português",
    "Cursos Regulares\\41 - Passo Estratégico Básico de Tecnologia da Informação",
    "SEFAZ-CE 2026\\22 - Bizu Estratégico",
    "SEFAZ-CE 2026\\10 - Estatística Descritiva",
    "04 - SEFAZ-SC\\09 - Legislação Tributária de Santa Catarina - Parte 01",
]

BANCAS = {"FCC": r"\bFCC\b", "CEBRASPE": r"\bCEBRASPE\b|\bCESPE\b", "FGV": r"\bFGV\b",
          "VUNESP": r"\bVUNESP\b", "CESGRANRIO": r"\bCESGRANRIO\b", "IDECAN": r"\bIDECAN\b",
          "MULTIBANCAS": r"\bMULTIBANCAS?\b"}
# Palavras curtas que todo texto em português tem; a página de OCR lixo quase não as tem (R9).
PARADAS = set("de a o que e do da em um uma para com não nao os as no na nos nas se por pelo pela ao aos "
              "dos das à ou mais como mas é são ser foi este esta esse essa isso".split())

# Casados no começo do tipo (formato A) ou do título (B, C); a ordem importa ("Lista de Questões" antes de "Questões").
TIPOS = [("teoria", r"teoria"), ("resumo", r"resumo|roteiro\s+de\s+revis|aposta\s+estrat"),
         ("mapa_mental", r"mapa\s+mental"),
         ("incidencia", r"o\s+que\s+[ée]\s+mais\s+cobrado|an[áa]lise\s+estat[íi]stica"),
         ("questionario", r"perguntas|question[áa]rio"),
         ("lista_questoes", r"lista\s+de\s+(quest|exerc)"),
         ("questoes_comentadas", r"(bateria\s+de\s+)?quest[õo]es(\s+comentadas|\s+estrat[ée]gicas)?|exerc[íi]cios\s+comentados"),
         ("gabarito", r"gabarito"), ("apresentacao", r"apresenta[çc][ãa]o"), ("flashcards", r"flash\s*cards?"),
         ("bibliografia", r"bibliografia|refer[êe]ncias")]
FAIXA_BIZU = re.compile(r"^(.*?)\s*\b(\d{1,3})(?:\s+(?:a|e)\s+(\d{1,3}))?\s+https?://\S+$")
INCIDENCIA = re.compile(r"^(.+?)\s+(\d{1,3}(?:,\d{1,2})?)\s?%$")
MIN_PAGINAS_AULA = 10


def sem_acento(texto):
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")


def pontilhada(linha):
    l = (linha or "").strip().replace("…", "...")
    return l.count(".") > len(l) / 4


def decodificar(linha):
    """'.1..). .N..A...T.. .e.. .P..A...T.. .-. .T..e..o..r.i.a...... 3' -> '1) NAT e PAT - Teoria 3': a linha
    pontilhada do sumário sai intercalada com as letras na extração; tirar os pontos devolve o texto."""
    l = (linha or "").strip().replace("…", "")
    if pontilhada(linha):
        l = l.replace(".", "")
    return re.sub(r"\s+", " ", l).strip()


def tipo_de(texto):
    return next((nome for nome, r in TIPOS if re.match(r, texto.strip(), re.IGNORECASE)), None)


def _pagina_colada(digitos, resto, anterior, n_paginas, historico):
    """Quantos dos dígitos grudados no fim são a página? Todos, se dão uma página possível (não menor que
    a anterior, dentro do PDF). Se não — o tema termina em número: 'NBR 27002-2022' + '17' —, o menor final
    que dá uma página possível e deixa no tema uma palavra já vista em outra entrada; senão o menor possível."""
    def possivel(s):
        return not s.startswith("0") and (anterior is None or int(s) >= anterior) and int(s) <= (n_paginas or 9999)
    if len(digitos) <= 4 and possivel(digitos):
        return digitos
    def ultima_palavra(final):
        palavras = (resto + digitos[:-len(final)]).split()
        return palavras[-1] if palavras else ""
    finais = [digitos[-k:] for k in range(1, min(4, len(digitos) - 1) + 1) if possivel(digitos[-k:])]
    vistos = [s for s in finais if ultima_palavra(s) in historico]
    return (vistos or finais or [None])[0]


def entrada_do_sumario(linha, anterior=None, n_paginas=None, historico=()):
    """Uma linha do sumário -> {n, tema, tipo, banca, rotulo, pagina, formato, titulo_tipo}; None se não é
    entrada. A: '1) NAT e PAT - Questões Comentadas - Cesgranrio17' (com pontilhada, os dígitos do fim são a
    página mesmo grudados — R1); B: '1. Introdução ao Código 02'; C: 'Tipologia Textual ....... 2'.
    'anterior' (página da entrada anterior), 'n_paginas' e 'historico' (palavras das entradas anteriores)
    só servem para separar a página de um tema que termina em número."""
    com_pontos, l = pontilhada(linha), decodificar(linha)
    m = re.match(r"^(\d{1,3})\s*\)\s*(.+)$", l)
    if m:
        formato, n, corpo = "A", int(m.group(1)), m.group(2)
    else:
        m = re.match(r"^(\d{1,3})\.\s+(\D.*)$", l)
        if m:
            formato, n, corpo = "B", int(m.group(1)), m.group(2)
        elif com_pontos and re.search(r"[A-Za-zÀ-ú]{3}", l):
            formato, n, corpo = "C", None, l
        else:
            return None
    pagina = None
    cauda = re.search(r"(\d+)$", corpo)
    if cauda and corpo[:cauda.start()].strip():
        resto, digitos = corpo[:cauda.start()], cauda.group(1)
        if resto[-1].isspace():
            achada = digitos if len(digitos) <= 4 else None
        else:
            achada = _pagina_colada(digitos, resto, anterior, n_paginas, historico) if com_pontos else None
        if achada:
            pagina, corpo = int(achada), corpo[:len(corpo) - len(achada)].strip()
    if formato != "A":
        if pagina is None:
            return None
        return {"n": n, "tema": corpo, "tipo": tipo_de(corpo), "banca": None, "rotulo": None, "pagina": pagina,
                "formato": formato, "titulo_tipo": None}
    partes = [p.strip() for p in re.split(r"\s+-\s+|\s-|-\s", corpo) if p.strip()]
    tipo, i_tipo = None, None
    for i, parte in enumerate(partes):
        tipo = tipo_de(parte)
        if tipo:
            i_tipo = i
            break
    if i_tipo == 0 and len(partes) > 1:
        # Tipo antes do tema (Passo de TI): '1) O que é mais cobrado no assunto - Apache Hadoop - MULTIBANCAS'.
        tema, resto = partes[1], " ".join(partes[2:])
    else:
        tema = " - ".join(partes[:i_tipo]) if i_tipo else (partes[0] if partes else "")
        resto = " ".join(partes[i_tipo + 1:]) if i_tipo is not None else ""
    banca = next((b for b, r in BANCAS.items() if re.search(r, resto, re.IGNORECASE)), None) if resto else None
    return {"n": n, "tema": tema, "tipo": tipo, "banca": banca, "rotulo": resto or None, "pagina": pagina,
            "formato": "A", "titulo_tipo": partes[i_tipo] if i_tipo is not None else None}


def sumario(paginas, primeiras=8):
    """As entradas do sumário: páginas 2 a 8 com pelo menos duas linhas que são entrada; para na
    primeira página sem entrada depois de achar alguma (o sumário ocupa mais de uma página nas aulas longas).
    Entrada sem tipo herda o da anterior nos formatos B e C (a primeira é teoria); no A, é título de teoria
    ('Encontros Vocálicos'). Página que diminui começa
    outra sequência ('seq'), porque o questionário anexado ao Passo recomeça a numeração (R2, R6).
    Um sumário A seguido de um detalhado (B, C) são duas listas ('lista') da mesma aula: cada uma é
    conferida e fechada à parte."""
    entradas, achou, anterior, historico = [], False, None, set()
    for p, texto in paginas[1:primeiras]:
        desta, ant, hist = [], anterior, set(historico)
        for linha in (texto or "").splitlines():
            e = entrada_do_sumario(linha, ant, len(paginas), hist)
            if e:
                e["no_sumario"] = p
                desta.append(e)
                ant = e["pagina"] if e["pagina"] is not None else ant
                hist |= set(f"{e['tema']} {e['rotulo'] or ''}".split())
        if len(desta) >= 2:
            entradas += desta
            achou, anterior, historico = True, ant, hist
        elif achou:
            break
    seq, lista, anterior, tipo, formato = 0, 0, None, "teoria", None
    for e in entradas:
        if formato is not None and (e["formato"] == "A") != (formato == "A"):
            seq, lista, anterior, tipo = seq + 1, lista + 1, None, "teoria"
        if not e["tipo"]:
            e["tipo"] = tipo if e["formato"] != "A" else "teoria"
        tipo = e["tipo"] or tipo
        if e["pagina"] is not None:
            if anterior is not None and e["pagina"] < anterior:
                seq += 1
            anterior = e["pagina"]
        e["seq"], e["lista"], formato = seq, lista, e["formato"]
    return entradas


def chave(texto, n=10):
    return re.sub(r"[^A-Z]", "", sem_acento(texto or "").upper())[:n]


def _pagina(texto):
    """O que a conferência olha numa página: a chave de cada linha e a das três primeiras juntas."""
    linhas = [l for l in (texto or "").splitlines() if l.strip()]
    return {"linhas": {chave(l, 10 ** 6) for l in linhas}, "topo": [chave(l, 10 ** 6) for l in linhas[:3]],
            "topo_junto": chave(" ".join(linhas[:3]), 10 ** 6)}


def conferir(tema, pagina, estrito=False):
    """O tema está nesta página? (R4) Sim se é uma linha dela; ou, nas três primeiras linhas, o tema de
    mais de uma palavra está inteiro, ou estão os pedaços das palavras sem a primeira letra — o título
    sai com a inicial grande separada ('P IP 6 / ROTOCOLO V', 'G / ABARITO'). 'estrito' (quando não há
    página do sumário para guiar): só como título — uma linha própria ou o começo de uma das três primeiras."""
    if isinstance(pagina, str):
        pagina = _pagina(pagina)
    tk = chave(tema, 10 ** 6)
    if len(tk) < 4:
        return False
    if tk in pagina["linhas"]:
        return True
    if estrito:
        return any(l.startswith(tk) for l in pagina["topo"])
    palavras = (tema or "").split()
    if len(palavras) >= 2 and len(tk) >= 5 and tk in pagina["topo_junto"]:
        return True
    pedacos = [k[1:] for k in (chave(p, 10 ** 6) for p in palavras) if len(k) >= 4]
    if len(pedacos) >= 2:
        return all(p in pagina["topo_junto"] for p in pedacos)
    if len(pedacos) == 1 and len(pedacos[0]) >= 5:
        return any(l.startswith(pedacos[0]) for l in pagina["topo"])
    return False


def _confere(e, vista, estrito=False):
    """A entrada está nesta página: pelo tema ou, no formato A, pelo texto do tipo ('Q C / UESTÕES OMENTADAS')."""
    return vista is not None and (conferir(e["tema"], vista, estrito)
                                  or bool(e.get("titulo_tipo")) and conferir(e["titulo_tipo"], vista, estrito))


def deslocamentos(paginas, entradas, alcance=3):
    """Para cada sequência do sumário, o deslocamento (página do PDF - página do sumário) que mais
    confirma entradas: de -3 a +3 na primeira de cada lista; nas seguintes, qualquer um depois do fim da
    anterior. Entrada sem página no sumário é procurada no corpo, em ordem, pelo tema.
    Grava 'inicio' (página do PDF) e 'confirmada' em cada entrada; devolve {seq: (d, confirmadas, testadas)}."""
    vistas = {p: _pagina(t) for p, t in paginas}
    n, piso, res, lista = len(paginas), 0, {}, None
    for seq in sorted({e["seq"] for e in entradas}):
        da_seq = [e for e in entradas if e["seq"] == seq]
        es = [e for e in da_seq if e["pagina"] is not None]
        nova_lista = da_seq[0]["lista"] != lista
        lista, piso = da_seq[0]["lista"], 0 if nova_lista else piso
        testaveis = [e for e in es if max(len(chave(e["tema"], 10 ** 6)), len(chave(e.get("titulo_tipo"), 10 ** 6))) >= 4]
        if not testaveis:
            res[seq] = (None, 0, 0)
            continue
        faixa = range(-alcance, alcance + 1) if nova_lista else range(piso - es[0]["pagina"] + 1, n - es[0]["pagina"] + 1)
        placar = {d: sum(1 for e in testaveis if _confere(e, vistas.get(e["pagina"] + d))) for d in faixa}
        melhor = max(placar, key=lambda d: (placar[d], -abs(d))) if placar else None
        if melhor is None or (not nova_lista and not placar[melhor]):
            res[seq] = (None, 0, len(testaveis))
            continue
        res[seq] = (melhor, placar[melhor], len(testaveis))
        for e in es:
            e["inicio"] = e["pagina"] + melhor
            e["confirmada"] = _confere(e, vistas.get(e["inicio"]))
        piso = max(e["inicio"] for e in es)
    sem_pagina = [e for e in entradas if e["pagina"] is None]
    if sem_pagina:
        depois = max(e["no_sumario"] for e in entradas)
        for e in entradas:
            if e["pagina"] is None:
                e["inicio"] = next((p for p, _ in paginas if p > depois and _confere(e, vistas[p], True)), None)
                e["confirmada"] = e["inicio"] is not None
            depois = e.get("inicio") or depois
        for seq in {e["seq"] for e in sem_pagina}:
            d, conf, test = res.get(seq, (None, 0, 0))
            achadas = [e for e in sem_pagina if e["seq"] == seq]
            res[seq] = (d, conf + sum(e["confirmada"] for e in achadas), test + len(achadas))
    return res


def fechar_secoes(entradas, n_paginas):
    """Cada seção vai até a página antes da próxima da mesma lista que começa depois dela; a última, até o
    fim (R5)."""
    for lista in {e.get("lista", 0) for e in entradas}:
        com_inicio = [e for e in entradas if e.get("inicio") and e.get("lista", 0) == lista]
        for i, e in enumerate(com_inicio):
            prox = next((x["inicio"] for x in com_inicio[i + 1:] if x["inicio"] > e["inicio"]), n_paginas + 1)
            e["fim"] = max(e["inicio"], prox - 1)


def tabela_bizus(paginas, primeiras=6):
    """Formato D (Bizu, R3): a tabela 'Assunto | Bizus | Caderno' das primeiras páginas. O nome do assunto
    pode vir na linha da faixa ('Receita Pública 7 e 8 http://…') ou partido em volta dela
    ('Restos a Pagar, … Exercícios' / '10 a 12 http://…' / 'Anteriores e Suprimento de Fundos')."""
    itens = []
    for _, texto in paginas[1:primeiras]:
        linhas = [l.strip() for l in (texto or "").splitlines() if l.strip()]
        if not any(FAIXA_BIZU.match(l) for l in linhas):
            continue
        pendente, aguardando = [], None
        for l in linhas:
            m = FAIXA_BIZU.match(l)
            if m:
                ini, fim = int(m.group(2)), int(m.group(3) or m.group(2))
                nome = m.group(1).strip() or (pendente[-1] if pendente else "")
                item = {"tema": nome, "bizus": (ini, fim)}
                itens.append(item)
                aguardando = None if m.group(1).strip() else item
                pendente = []
            elif aguardando is not None:
                aguardando["tema"] = (aguardando["tema"] + " " + l).strip()
                aguardando = None
            elif not re.match(r"assunto\b", l, re.IGNORECASE):
                pendente.append(l)
    return itens


def secoes_do_bizu(paginas, itens):
    """No corpo, cada assunto do Bizu abre a página com o primeiro bizu da faixa ('5. Classificações…')
    numa das três primeiras linhas."""
    entradas, depois = [], 1
    for item in itens:
        ini = item["bizus"][0]
        achada = next((p for p, t in paginas if p > depois and any(
            re.match(rf"{ini}\.\s", l.strip()) for l in (t or "").splitlines()[:3])), None)
        entradas.append({"n": ini, "tema": item["tema"], "tipo": "resumo", "banca": None,
                         "rotulo": "bizus {}–{}".format(*item["bizus"]), "pagina": None, "formato": "D", "seq": 0,
                         "inicio": achada, "confirmada": achada is not None})
        depois = achada or depois
    return entradas


def incidencia(paginas, primeiras=6):
    """A tabela 'Subassunto  NN,N%' do Passo e do Bizu, com a banca e o período citados na página (R7)."""
    for p, texto in paginas[1:primeiras]:
        linhas = (l.strip() for l in (texto or "").splitlines())
        casadas = (INCIDENCIA.match(l) for l in linhas)
        sub = [(m.group(1).lstrip("´`'\"•- "), float(m.group(2).replace(",", "."))) for m in casadas
               if m and not m.group(1).lower().startswith("total")]
        cabecalho = re.search(r"subassunto|mais\s+cobrado|incid[êe]ncia|n[áa]lise\s+e?stat|frequ[êe]ncia", texto,
                              re.IGNORECASE)
        if len(sub) >= 2 and cabecalho:
            periodo = re.search(r"(20\d\d)\s+a\s+(20\d\d)", texto)
            return {"pagina": p, "subassuntos": sub,
                    "bancas": [b for b, r in BANCAS.items() if re.search(r, texto, re.IGNORECASE)],
                    "periodo": f"{periodo.group(1)}–{periodo.group(2)}" if periodo else None}
    return None


def ilegivel(texto):
    """Página de imagem com OCR lixo ('s*ptppi|dnpsesepinpxa', '(cid:127)') ou texto colado
    ('MaterialdeConsumo') (R9). Calibrado no Bizu de Direito Financeiro (SEFAZ-CE, aula 11): um quarto das
    palavras longas, coladas ou com símbolo; ou um sétimo delas e pouca palavra curta comum ('de', 'que'),
    que o texto colado engole. A pontilhada do sumário não conta."""
    palavras = [w for w in (texto or "").split() if not pontilhada(w)]
    if len(palavras) < 3:
        return False
    ruins = sum(1 for w in palavras if len(w) >= 18 or re.search(r"[\^|*£<>]|\(cid:|[a-zà-ÿ][A-ZÀ-Ý]", w)) / len(palavras)
    paradas = sum(1 for w in palavras if w.lower().strip(".,;:()") in PARADAS) / len(palavras)
    return ruins >= 0.25 or (ruins >= 0.15 and paradas <= 0.21)


def numero_aula(paginas, nome_arquivo):
    """'AULA 14' nas três primeiras páginas; o nome do arquivo só na falta — 'aula-00' pode ser a aula 14 (R10)."""
    for _, t in paginas[:3]:
        m = re.search(r"^\s*AULA\s+(\d{1,3})\b", t or "", re.MULTILINE | re.IGNORECASE)
        if m:
            return int(m.group(1)), "conteúdo"
    m = re.search(r"aula[\s_-]*(\d{1,3})", nome_arquivo or "", re.IGNORECASE)
    return (int(m.group(1)), "arquivo") if m else (None, None)


def banca_da_aula(entradas, inc, bancas_texto):
    """Do sumário ('Multibancas' não diz qual); senão da incidência; senão a contagem no texto (R8).
    -> ([bancas], origem)."""
    do_sumario = Counter(e["banca"] for e in entradas if e["banca"] and e["banca"] != "MULTIBANCAS")
    if do_sumario:
        return [b for b, _ in do_sumario.most_common()], "sumário"
    if inc and inc["bancas"]:
        return inc["bancas"], "incidência"
    if bancas_texto:
        return sorted(bancas_texto, key=bancas_texto.get, reverse=True), "texto"
    return [], None


def analisar_aula(conn, arquivo_id):
    nome = (conn.execute("SELECT nome_arquivo FROM arquivos WHERE id = ?", (arquivo_id,)).fetchone() or [""])[0]
    paginas = conn.execute("SELECT pagina, texto FROM paginas WHERE arquivo_id = ? ORDER BY pagina",
                           (arquivo_id,)).fetchall()
    marcadores = conn.execute("SELECT nivel, titulo, pagina FROM bookmarks WHERE arquivo_id = ? ORDER BY pagina",
                              (arquivo_id,)).fetchall()
    entradas = sumario(paginas)
    seqs = deslocamentos(paginas, entradas)
    if not entradas:
        entradas = secoes_do_bizu(paginas, tabela_bizus(paginas))
        seqs = {0: (None, sum(e["confirmada"] for e in entradas), len(entradas))} if entradas else {}
    fechar_secoes(entradas, len(paginas))
    bancas = {b: sum(len(re.findall(r, t or "")) for _, t in paginas) for b, r in BANCAS.items()}
    bancas_texto = {b: n for b, n in bancas.items() if n}
    inc = incidencia(paginas)
    return {
        "n": len(paginas),
        "vazias": sum(1 for _, t in paginas if len((t or "").strip()) < 20),
        "ilegiveis": [p for p, t in paginas if ilegivel(t)],
        "marcadores": marcadores,
        "abertura": " | ".join(" ".join(linhas_uteis(t, 3)) for _, t in paginas[:1])[:200],
        "aula": numero_aula(paginas, nome),
        "entradas": entradas,
        "formato": "".join(sorted({e["formato"] for e in entradas})) or None,
        "deslocamento": (seqs.get(0, (None,))[0], sum(s[1] for s in seqs.values()), sum(s[2] for s in seqs.values())),
        "sequencias": seqs,
        "incidencia": inc,
        "banca": banca_da_aula(entradas, inc, bancas_texto),
        "fora": len(paginas) < MIN_PAGINAS_AULA and not entradas,
        "bancas_texto": bancas_texto,
    }


def linhas_uteis(texto, n=25):
    return [l.strip() for l in (texto or "").splitlines() if len(l.strip()) > 3][:n]


def _faixa(e):
    if not e.get("inicio"):
        return "p. ?"
    return f"p. {e['inicio']}–{e['fim']} {'✓' if e.get('confirmada') else '?'}"


def relatorio(conn, cursos, aulas_por_curso):
    saida, resumo = ["# Estrutura das apostilas (amostra, sem IA)", ""], []
    for padrao in cursos:
        arquivos = conn.execute("SELECT id, curso, nome_arquivo, n_paginas FROM arquivos WHERE curso LIKE ? "
                                "ORDER BY nome_arquivo", (f"%{padrao}%",)).fetchall()
        if not arquivos:
            saida += [f"## {padrao}", "", "_nenhum arquivo casou_", ""]
            continue
        # Espalhadas pelo curso: primeira, meio e última por padrão.
        passo = max(1, (len(arquivos) - 1) // max(1, aulas_por_curso - 1))
        amostra = sorted({min(i, len(arquivos) - 1) for i in range(0, len(arquivos), passo)})[:aulas_por_curso]
        saida += [f"## {arquivos[0][1]}  ({len(arquivos)} arquivos)", ""]
        c = {"com_sumario": 0, "entradas": 0, "com_tipo": 0, "com_banca": 0, "fora": 0, "conf": 0, "test": 0,
             "ilegiveis": 0, "paginas": 0, "incidencia": 0}
        desloc, tipos_vistos, bancas_vistas, formatos = {}, set(), set(), set()
        for i in amostra:
            arquivo_id, _, nome, _ = arquivos[i]
            a = analisar_aula(conn, arquivo_id)
            e = a["entradas"]
            d, conf, test = a["deslocamento"]
            c["com_sumario"] += bool(e)
            c["entradas"] += len(e)
            c["com_tipo"] += sum(1 for x in e if x["tipo"])
            c["com_banca"] += sum(1 for x in e if x["banca"])
            c["fora"] += a["fora"]
            c["conf"] += conf
            c["test"] += test
            c["ilegiveis"] += len(a["ilegiveis"])
            c["paginas"] += a["n"]
            c["incidencia"] += bool(a["incidencia"])
            if test and d is not None:
                desloc[d] = desloc.get(d, 0) + 1
            tipos_vistos |= {x["tipo"] for x in e if x["tipo"]}
            bancas_vistas |= {x["banca"] for x in e if x["banca"]}
            formatos |= set(a["formato"] or "")
            n_aula, origem = a["aula"]
            seqs = ", ".join(f"{'?' if s[0] is None else f'{s[0]:+d}'} ({s[1]}/{s[2]})" for s in a["sequencias"].values())
            saida += [f"### {nome} — {a['n']} págs, {a['vazias']} sem texto, {len(a['ilegiveis'])} ilegíveis, "
                      f"{len(a['marcadores'])} marcadores" + (" — FORA (curto e sem sumário)" if a["fora"] else ""),
                      f"- abertura: {a['abertura']}",
                      f"- aula: {n_aula if n_aula is not None else '?'} ({origem or '—'})",
                      f"- sumário: {len(e)} entradas, formato {a['formato'] or '—'}; deslocamento por sequência "
                      f"(conferidas): {seqs or '—'}"]
            for x in e[:40]:
                saida.append(f"    - {x['n'] if x['n'] is not None else '·'}) {x['tema'][:60]} | {x['tipo'] or '?'} | "
                             f"{x['banca'] or x['rotulo'] or ''} | sumário p. {x['pagina'] or '?'} | {_faixa(x)}")
            if len(e) > 40:
                saida.append(f"    - … mais {len(e) - 40}")
            if a["incidencia"]:
                inc = a["incidencia"]
                saida.append(f"- incidência (p. {inc['pagina']}; {', '.join(inc['bancas']) or 'banca ?'}; "
                             f"{inc['periodo'] or 'período ?'}): "
                             + "; ".join(f"{s} {v:g}%" for s, v in inc["subassuntos"]))
            bancas, origem = a["banca"]
            saida.append(f"- banca da aula: {', '.join(bancas) or '—'} ({origem or '—'}); no texto: {a['bancas_texto'] or '—'}")
            if a["ilegiveis"]:
                saida.append(f"- páginas ilegíveis: {', '.join(map(str, a['ilegiveis'][:30]))}")
            saida.append("")
        n = len(amostra)
        moda = max(desloc, key=desloc.get) if desloc else None
        resumo.append(f"| {arquivos[0][1][-55:]} | {n} | {c['fora']} | {c['com_sumario']} | {c['entradas']} | "
                      f"{100 * c['com_tipo'] // max(1, c['entradas'])}% | {100 * c['com_banca'] // max(1, c['entradas'])}% | "
                      f"{'—' if moda is None else f'{moda:+d}'} ({c['conf']}/{c['test']}) | "
                      f"{''.join(sorted(formatos)) or '—'} | {c['ilegiveis']}/{c['paginas']} | {c['incidencia']} | "
                      f"{', '.join(sorted(tipos_vistos)) or '—'} | {', '.join(sorted(bancas_vistas)) or '—'} |")
    saida += ["## Resumo por curso", "",
              "| Curso | Aulas | Fora | Com sumário | Entradas | Com tipo | Com banca | Deslocamento (conferidas) | "
              "Formatos | Ilegíveis | Com incidência | Tipos | Bancas |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|", *resumo]
    return "\n".join(saida)


def bruto(conn, trecho, paginas_max=80, linhas_sumario=40):
    """O texto como está no índice, para escrever as regras: p. 2-4 inteiras (cruas e decodificadas)
    e as 3 primeiras linhas de cada página (onde ficam os títulos de seção)."""
    linha = conn.execute("SELECT id, curso, nome_arquivo FROM arquivos WHERE curso || '/' || nome_arquivo LIKE ? "
                         "ORDER BY curso, nome_arquivo LIMIT 1", (f"%{trecho}%",)).fetchone()
    if not linha:
        return f"_nenhum arquivo casou com {trecho!r}_"
    paginas = conn.execute("SELECT pagina, texto FROM paginas WHERE arquivo_id = ? ORDER BY pagina", (linha[0],)).fetchall()
    saida = [f"# {linha[1]}/{linha[2]} — {len(paginas)} págs", ""]
    for p, t in paginas[1:4]:
        saida += [f"## p. {p} (crua → decodificada)", ""]
        for l in (t or "").splitlines()[:linhas_sumario]:
            saida.append(f"    {l[:160]!r}  →  {decodificar(l)[:120]!r}")
        saida.append("")
    saida += ["## Começo de cada página", ""]
    for p, t in paginas[:paginas_max]:
        saida.append(f"- p. {p}: " + " ⏎ ".join(l.strip()[:70] for l in (t or "").splitlines()[:3]))
    return "\n".join(saida)


def main():
    ap = argparse.ArgumentParser(description="Estrutura das apostilas (amostra, sem IA).")
    ap.add_argument("--curso", action="append", help="trecho do nome da pasta (repetível); padrão: a amostra")
    ap.add_argument("--aulas", type=int, default=3, help="aulas por curso (padrão 3: primeira, meio, última)")
    ap.add_argument("--indice", default=os.environ.get("INDICE_DB"))
    ap.add_argument("--bruto", metavar="TRECHO", help="mostra o texto cru de UMA aula (trecho de curso/arquivo)")
    args = ap.parse_args()
    with closing(sqlite3.connect(f"file:{args.indice}?mode=ro", uri=True)) as conn:
        print(bruto(conn, args.bruto) if args.bruto else relatorio(conn, args.curso or AMOSTRA, args.aulas))


if __name__ == "__main__":
    main()
