#!/usr/bin/env python3
"""
partes_edital.py — Protótipo da leitura do edital em assuntos e partes, com conferência por regra
(`docs/proposta-catalogo-aulas-e-modos.md` §3.7; documento "Editais: como vamos quebrar e mapear os assuntos").

Etapas (cada uma conferida antes da seguinte):

1. Extração (regra, no Pi, com pdftotext): o texto por página, sem o ruído que se repete (cabeçalho, rodapé,
   timbre, URL do SEI, número de página), e o recorte do conteúdo programático.
2. Organização (IA): quais disciplinas valem para o cargo, por NÚMERO DE LINHA — o recorte do texto é feito
   pela regra, então nenhuma palavra da disciplina é reescrita.
3. Quebra (IA, uma chamada por disciplina): assuntos copiados do edital e, em cada um, as partes com o
   contexto (a cabeça ou o pai numerado) e o prefixo herdado ("Windows Server" na parte "2022").
4. Conferência (regra): o assunto é trecho do edital; o que sobra do texto da disciplina vira "trecho sem
   assunto"; cada parte passa pela COBERTURA (toda palavra do assunto está numa parte ou no contexto) e pela
   FIDELIDADE (a parte só usa palavras do assunto). Quebra recusada é refeita uma vez com os erros; recusada
   de novo, fica marcada para a revisão humana.

    python3 integracao/partes_edital.py extrair edital.pdf --saida /tmp/x/alesc.json          # no Pi
    docker compose run ... python integracao/partes_edital.py quebrar /saida/alesc.json \\
        --cargo "Analista de Sistemas" --saida /saida                                         # contêiner (IA)
"""

import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

VAZIAS = set("de da do das dos e em a o as os para com por no na nos nas ao aos um uma sua seu suas seus ou que "
             "se sobre entre como pela pelo pelas pelos".split())
INICIO_PROGRAMA = re.compile(r"conte[uú]dos?\s+program[aá]tico|objetos?\s+de\s+avalia[cç][aã]o|programas?\s+das?\s+provas?",
                             re.IGNORECASE)
TITULO_DE_ANEXO = re.compile(r"^ANEXO\s+([IVXL]+|\d+)\b")


class ProgramaNaoEncontrado(Exception):
    """O PDF não traz o conteúdo programático (ex.: MPPR 2024 remete ao Anexo II, publicado em outro arquivo).
    Seguir com o edital inteiro seria afirmar uma completude que não existe."""


# ---------------------------------------------------------------- 1. extração (regra)

def paginas_do_pdf(pdf):
    saida = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    return saida.split("\f")


def _assinatura(linha):
    return re.sub(r"[\d\W_]+", "", unicodedata.normalize("NFKD", linha).encode("ascii", "ignore").decode().lower())


def limpar(paginas, borda=8, fracao=0.5, ruido=None):
    """As linhas de cada página sem o ruído: cabeçalho e rodapé (linha que, sem números, aparece perto da borda
    — até `borda` linhas do topo ou do pé — em pelo menos `fracao` das páginas, e no mínimo em 3; a URL e a
    data do SEI caem aqui) e número de página sozinho. URL no meio do conteúdo fica (TCE-SC cita resolução
    por link). Repetição em poucas páginas ou no meio delas é conteúdo: título de
    disciplina que volta noutro módulo, pedaço de linha quebrada ('Catarina.') (TCE-SC 2026). Toda linha
    descartada vai para `ruido` [(página, linha)], para a revisão. Devolve [(página, linha)]."""
    def borda_de(p):
        cheias = [l for l in p.splitlines() if _assinatura(l)]
        return set(cheias[:borda] + cheias[-borda:])
    bordas = [borda_de(p) for p in paginas]
    contagem = Counter()
    for b in bordas:
        contagem.update({_assinatura(l) for l in b})
    corte = max(3, fracao * len([p for p in paginas if p.strip()]))
    repetidas = {a for a, n in contagem.items() if n >= corte and len(a) >= 6}
    saida = []
    for numero, (p, b) in enumerate(zip(paginas, bordas), 1):
        for l in p.splitlines():
            texto = " ".join(l.split())
            if not texto:
                continue
            if (l in b and _assinatura(texto) in repetidas) or re.match(r"^\d{1,4}$", texto):
                if ruido is not None:
                    ruido.append((numero, texto))
                continue
            saida.append((numero, texto))
    return saida


def recorte_do_programa(linhas):
    """Do título do conteúdo programático (a última linha curta que o anuncia, não a frase que o cita) até o
    título do anexo seguinte (atribuições, cronograma), ou o fim. Sem título, ProgramaNaoEncontrado."""
    candidatos = [i for i, (_, l) in enumerate(linhas) if INICIO_PROGRAMA.search(l) and len(l) <= 80
                  and (l.isupper() or l.strip().upper().startswith(("ANEXO", "15")) or len(l.split()) <= 6)]
    if not candidatos:
        remissao = next((l for _, l in linhas if INICIO_PROGRAMA.search(l)), None)
        raise ProgramaNaoEncontrado("conteúdo programático não encontrado neste PDF"
                                    + (f"; o edital diz: {remissao!r}" if remissao else ""))
    titulos = [i for i in candidatos if linhas[i][1].isupper() or linhas[i][1].strip().upper().startswith("ANEXO")]
    inicio = (titulos or candidatos)[-1]
    fim = next((i for i in range(inicio + 1, len(linhas)) if TITULO_DE_ANEXO.match(linhas[i][1])
                and not INICIO_PROGRAMA.search(linhas[i][1])), len(linhas))
    return linhas[inicio:fim]


def extrair(pdf):
    ruido = []
    linhas = recorte_do_programa(limpar(paginas_do_pdf(pdf), ruido=ruido))
    paginas = {p for p, _ in linhas}
    return {"pdf": Path(pdf).name, "linhas": [{"n": i + 1, "pagina": p, "texto": t} for i, (p, t) in enumerate(linhas)],
            "ruido": [{"pagina": p, "texto": t} for p, t in ruido if p in paginas]}


# ---------------------------------------------------------------- conferência (regra)

def normalizar(texto):
    """Para comparar trechos: sem acento, minúsculas, sem hífen de quebra de linha, só letras/números e espaço."""
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().lower()
    t = re.sub(r"(\w)-\s+(\w)", r"\1\2", t)
    return " ".join(re.findall(r"[a-z0-9]+", t))


def palavras(texto):
    saida = set()
    for w in normalizar(texto).split():
        if w in VAZIAS:
            continue
        saida.add(w[:-1] if len(w) > 4 and w.endswith("s") else w)
    return saida


def trechos_sem_assunto(texto_disciplina, assuntos, minimo=3, cabecalho=""):
    """O texto da disciplina que nenhum assunto cobre (por posição na forma normalizada), em pedaços com pelo
    menos `minimo` palavras relevantes. Assunto que não é trecho do texto não cobre nada; assunto repetido no
    edital cobre a próxima ocorrência ainda livre (a ALESC repete 'Linguagem PHP (versão 8+)'). O cabeçalho
    da disciplina (nome e restrição de cargo) não é assunto e não conta como sobra."""
    base = normalizar(texto_disciplina)
    coberto = [False] * len(base)
    for a in assuntos:
        alvo = normalizar(a)
        i = base.find(alvo) if alvo else -1
        while i >= 0 and all(coberto[i:i + len(alvo)]):
            i = base.find(alvo, i + 1)
        if i >= 0:
            for k in range(i, i + len(alvo)):
                coberto[k] = True
    sobras, atual = [], []
    for ch, c in zip(base, coberto):
        if not c:
            atual.append(ch)
        elif atual:
            sobras.append("".join(atual))
            atual = []
    if atual:
        sobras.append("".join(atual))
    do_cabecalho = palavras(cabecalho)
    return [s.strip() for s in sobras if len(palavras(s) - do_cabecalho) >= minimo]


def conferir_assunto(assunto, texto_disciplina, cabecalho="", referencias=(), alertas=None):
    """Erros de um assunto e das partes dele (lista vazia = aceito). As palavras do cabeçalho da disciplina
    (nome e restrição de cargo) não precisam de parte: o assunto às vezes vem com o título junto. Assunto que
    é inteiro uma referência ('todo o conteúdo das disciplinas X e Y') não precisa de parte. Contexto que vem
    de fora do assunto mas está no texto da disciplina (a cabeça de uma lista partida em vários assuntos) não
    é erro: vira alerta em 'alertas', para a revisão."""
    erros = []
    alertas = alertas if alertas is not None else []
    if any(normalizar(r) and normalizar(r) in normalizar(assunto["texto"])
           and len(palavras(r)) >= 0.8 * len(palavras(assunto["texto"]) - palavras(cabecalho)) for r in referencias):
        return erros
    if normalizar(assunto["texto"]) not in normalizar(texto_disciplina):
        erros.append("o assunto não é trecho do edital (foi reescrito ou juntou pedaços)")
    do_assunto = palavras(assunto["texto"])
    partes = assunto.get("partes") or []
    if not partes:
        return erros + ["assunto sem partes"]
    cobertas = set()
    for p in partes:
        herdado = palavras(p.get("herdado") or "")
        contexto = palavras(p.get("contexto") or "")
        alheias = palavras(p.get("texto")) - do_assunto
        if alheias:
            erros.append(f"parte {p.get('texto')!r} usa palavras que não estão no assunto: {', '.join(sorted(alheias))}")
        if herdado - do_assunto:
            erros.append(f"prefixo herdado {p.get('herdado')!r} não está no assunto")
        if contexto - do_assunto:
            if contexto <= palavras(texto_disciplina):
                aviso = f"contexto {p.get('contexto')!r} vem de fora do assunto (de um assunto anterior)"
                if aviso not in alertas:
                    alertas.append(aviso)
            else:
                erros.append(f"contexto {p.get('contexto')!r} não está no assunto nem no texto da disciplina")
        cobertas |= palavras(p.get("texto")) | contexto | herdado
    faltam = {w for w in do_assunto - cobertas - palavras(cabecalho) if not (w.isdigit() and len(w) <= 2)}  # 4.1, 5.3
    if faltam:
        erros.append(f"palavras do assunto sem parte: {', '.join(sorted(faltam))}")
    return erros


# ---------------------------------------------------------------- 2 e 3. organização e quebra (IA)

SISTEMA = """Você lê o conteúdo programático de editais de concurso público brasileiro.
Responda só com JSON, sem texto fora dele."""

ORGANIZAR = """Abaixo está o conteúdo programático de um edital, uma linha por número (Lnnn).
Cargo escolhido: {cargo}

Liste as disciplinas que valem para esse cargo — inclusive conhecimentos gerais/comuns que o edital aplica a
ele —, cada uma com a primeira e a última linha do texto dela. Regras:
- não inclua bloco que o edital restringe a outros cargos (ex.: "Apenas para o cargo/especialidades: ..." que
  não cite este cargo);
- não inclua observações gerais, critérios de prova ou atribuições do cargo;
- a linha do nome da disciplina entra no intervalo; o nome do cargo ou do grupo ("CONHECIMENTOS GERAIS") não.

Responda: {{"disciplinas": [{{"nome": "como no edital", "linha_inicio": 12, "linha_fim": 30,
  "comum": true, "restricao": "texto da restrição de cargo, se houver, senão null"}}]}}

{linhas}"""

QUEBRAR = """Disciplina "{disciplina}" de um edital de concurso. Quebre o texto em ASSUNTOS e cada assunto em PARTES.

ASSUNTO = um tópico do edital (um item numerado com seus subitens, ou uma frase entre pontos). Copie o texto
do assunto EXATAMENTE como está no edital (pode incluir os subitens); não reescreva, não corrija, não junte
pedaços distantes. Todo o texto da disciplina deve cair em algum assunto, menos o nome da disciplina.

PARTE = cada assunto de estudo distinto dentro do assunto:
- lista sob uma cabeça ("SQL: DDL, DML, DCL") → uma parte por elemento; a cabeça vai em "contexto";
- item numerado com subitens ("4 Coesão: 4.1 ... 4.2 ...") → os subitens são partes; o pai vai em "contexto";
- "e" só separa assuntos distintos ("Concordância nominal e concordância verbal" → 2 partes;
  "Kubernetes e Docker", "direitos e deveres", "interpretação e compreensão" → 1 parte);
- parêntese que descreve (nome de lei, sigla) fica na parte; parêntese que lista ("Power BI (Power Query, M,
  DAX)") vira partes com o que está fora dele no "contexto";
- elemento que depende do anterior herda o prefixo: "Windows Server 2019 e 2022" → partes "Windows Server
  2019" e "2022" com "herdado": "Windows Server"; nunca uma parte só "2022" sem o herdado;
- número de lei, versão, decimal, abreviatura (art., nº), URL, código ("0000, 0150"), faixa de artigos e edição
  ("PMBOK 6ª edição") nunca são separadores; uma LISTA de códigos, registros, artigos ou campos ("EFD
  REGISTROS 0000, 0150, C100, C170"; "registros B, C, D, H") é UMA parte só, nunca uma parte por código;
- repetição que está no edital fica (duas partes iguais), com um alerta;
- "todo o conteúdo das disciplinas X e Y" é referência, não parte: vai em "referencias".
A parte é texto copiado do assunto (sem a cabeça, que vai no contexto). Não invente palavras.

Responda: {{"assuntos": [{{"texto": "texto exato do edital", "partes": [{{"texto": "...", "contexto": null,
  "herdado": null}}], "alertas": []}}], "referencias": [], "restricoes": []}}

TEXTO DA DISCIPLINA:
<<<
{texto}
>>>"""


def texto_das_linhas(linhas, ini, fim):
    return " ".join(l["texto"] for l in linhas if ini <= l["n"] <= fim)


def organizar(sge, extraido, cargo):
    from ia_comum import completar_json
    corpo = "\n".join(f"L{l['n']}: {l['texto']}" for l in extraido["linhas"])
    resposta = completar_json(sge, SISTEMA, ORGANIZAR.format(cargo=cargo, linhas=corpo))
    n = len(extraido["linhas"])
    saida = []
    for d in resposta.get("disciplinas") or []:
        ini, fim = d.get("linha_inicio"), d.get("linha_fim")
        if isinstance(ini, int) and isinstance(fim, int) and 1 <= ini <= fim <= n:
            saida.append(dict(d, texto=texto_das_linhas(extraido["linhas"], ini, fim),
                              paginas=sorted({l["pagina"] for l in extraido["linhas"] if ini <= l["n"] <= fim})))
    return saida


def cabecalho(disciplina):
    return f"{disciplina.get('nome') or ''} {disciplina.get('restricao') or ''}"


def reconferir(disciplina):
    """Refaz a conferência por regra sobre os assuntos já gravados (regra nova, mesma resposta da IA)."""
    for a in disciplina["assuntos"]:
        a["avisos"] = []
        a["erros"] = conferir_assunto(a, disciplina["texto"], cabecalho(disciplina), disciplina.get("referencias") or [],
                                      a["avisos"])
    disciplina["trechos_sem_assunto"] = trechos_sem_assunto(disciplina["texto"], [a["texto"] for a in disciplina["assuntos"]],
                                                            cabecalho=cabecalho(disciplina))
    return disciplina


def quebrar_disciplina(sge, disciplina):
    """Quebra, confere e refaz uma vez com os erros. Devolve a disciplina com assuntos, erros e trechos."""
    from ia_comum import completar_json
    pedido = QUEBRAR.format(disciplina=disciplina["nome"], texto=disciplina["texto"])
    resposta, tentativas = None, 0
    for tentativas in (1, 2):
        texto = pedido
        if resposta is not None:
            problemas = [f"- assunto {a['texto'][:80]!r}: {e}" for a in resposta.get("assuntos", [])
                         for e in conferir_assunto(a, disciplina["texto"], cabecalho(disciplina))]
            sobras = trechos_sem_assunto(disciplina["texto"], [a["texto"] for a in resposta.get("assuntos", [])],
                                         cabecalho=cabecalho(disciplina))
            texto += "\n\nSua resposta anterior falhou na conferência. Corrija:\n" + "\n".join(problemas[:30]) + \
                ("\n- trechos do edital sem assunto: " + " | ".join(sobras[:10]) if sobras else "")
        resposta = completar_json(sge, SISTEMA, texto)
        assuntos = [a for a in (resposta.get("assuntos") or []) if isinstance(a, dict) and a.get("texto")]
        resposta["assuntos"] = assuntos
        refs = resposta.get("referencias") or []
        for a in assuntos:
            a["avisos"] = []
        erros = {i: conferir_assunto(a, disciplina["texto"], cabecalho(disciplina), refs, a["avisos"])
                 for i, a in enumerate(assuntos)}
        sobras = trechos_sem_assunto(disciplina["texto"], [a["texto"] for a in assuntos], cabecalho=cabecalho(disciplina))
        if not any(erros.values()) and not sobras:
            break
    for i, a in enumerate(resposta["assuntos"]):
        a["erros"] = erros.get(i, [])
    return dict(disciplina, assuntos=resposta["assuntos"], trechos_sem_assunto=sobras,
                referencias=resposta.get("referencias") or [], restricoes=resposta.get("restricoes") or [],
                tentativas=tentativas)


def relatorio(edital, cargo, disciplinas):
    assuntos = [a for d in disciplinas for a in d["assuntos"]]
    partes = [p for a in assuntos for p in a.get("partes") or []]
    recusados = [a for a in assuntos if a["erros"]]
    sobras = [s for d in disciplinas for s in d["trechos_sem_assunto"]]
    saida = [f"# {edital} — {cargo}", "",
             f"{len(disciplinas)} disciplinas · {len(assuntos)} assuntos · {len(partes)} partes · "
             f"{len(recusados)} assuntos recusados pela conferência · {len(sobras)} trechos do edital sem assunto · "
             f"{sum(d['tentativas'] == 2 for d in disciplinas)} disciplinas refeitas", ""]
    for d in disciplinas:
        saida += [f"## {d['nome']} (p. {', '.join(map(str, d['paginas']))})"
                  + (f" — restrição: {d['restricao']}" if d.get("restricao") else ""), ""]
        for a in d["assuntos"]:
            marca = "✗" if a["erros"] else "✓"
            saida.append(f"- {marca} {a['texto']}")
            for p in a.get("partes") or []:
                extra = "".join([f" · contexto: {p['contexto']}" if p.get("contexto") else "",
                                 f" · herdado: {p['herdado']}" if p.get("herdado") else ""])
                saida.append(f"    - {p['texto']}{extra}")
            for e in a["erros"]:
                saida.append(f"    - **conferência:** {e}")
            for al in (a.get("alertas") or []) + (a.get("avisos") or []):
                saida.append(f"    - alerta: {al}")
        for s in d["trechos_sem_assunto"]:
            saida.append(f"- **trecho sem assunto:** {s}")
        for r in d["referencias"]:
            saida.append(f"- referência: {r}")
        saida.append("")
    return "\n".join(saida)


def main():
    ap = argparse.ArgumentParser(description="Protótipo: edital em assuntos e partes, com conferência por regra.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extrair")
    e.add_argument("pdf")
    e.add_argument("--saida", required=True)
    q = sub.add_parser("quebrar")
    q.add_argument("extraido")
    q.add_argument("--cargo", required=True)
    q.add_argument("--saida", required=True)
    r = sub.add_parser("reconferir", help="refaz a conferência por regra sobre um <nome>-partes.json, sem IA")
    r.add_argument("partes")
    r.add_argument("--cargo", required=True)
    args = ap.parse_args()
    if args.cmd == "reconferir":
        arquivo = Path(args.partes)
        feitas = [reconferir(d) for d in json.loads(arquivo.read_text(encoding="utf-8"))]
        arquivo.write_text(json.dumps(feitas, ensure_ascii=False, indent=1), encoding="utf-8")
        nome = arquivo.name.replace("-partes.json", "")
        arquivo.with_name(f"{nome}-partes.md").write_text(relatorio(nome, args.cargo, feitas), encoding="utf-8")
        print(relatorio(nome, args.cargo, feitas).splitlines()[2])
        return
    if args.cmd == "extrair":
        try:
            dados = extrair(args.pdf)
        except ProgramaNaoEncontrado as erro:
            print(f"{args.pdf}: {erro}")
            sys.exit(2)
        Path(args.saida).write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{args.saida}: {len(dados['linhas'])} linhas do conteúdo programático")
        return
    from sge_api import SgeApi
    sge = SgeApi(os.environ.get("SGE_URL", "http://app:8080"), os.environ["INTERNAL_TOKEN"])
    extraido = json.loads(Path(args.extraido).read_text(encoding="utf-8"))
    disciplinas = organizar(sge, extraido, args.cargo)
    print(f"{len(disciplinas)} disciplinas para {args.cargo}", flush=True)
    feitas = []
    for d in disciplinas:
        feitas.append(quebrar_disciplina(sge, d))
        print(f"  {d['nome']}: {len(feitas[-1]['assuntos'])} assuntos, tentativas {feitas[-1]['tentativas']}", flush=True)
    nome = Path(args.extraido).stem
    saida = Path(args.saida)
    (saida / f"{nome}-partes.json").write_text(json.dumps(feitas, ensure_ascii=False, indent=1), encoding="utf-8")
    (saida / f"{nome}-partes.md").write_text(relatorio(extraido["pdf"], args.cargo, feitas), encoding="utf-8")


if __name__ == "__main__":
    main()
