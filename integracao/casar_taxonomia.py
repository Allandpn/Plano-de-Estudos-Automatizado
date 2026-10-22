#!/usr/bin/env python3
"""
casar_taxonomia.py — Liga assuntos do edital e temas das fichas aos nós da árvore do QConcursos e casa um
com o outro pelos nós (`docs/proposta-catalogo-aulas-e-modos.md` §3.2 e §3.7).

1. Regra: para cada item (assunto do edital ou tema de ficha), os nós candidatos da árvore, por palavras em
   comum com o nome e os termos (palavra rara pesa mais; o caminho do nó dá contexto).
2. IA em lote: escolhe, só entre os candidatos, até 3 nós por item (ou nenhum) — só nomes, sem apostila.
3. Casamento: assunto e tema casam quando caem no mesmo nó ou um dentro do outro (assunto ↔ subassunto);
   nunca só pela disciplina.

Ensaio (este script): os assuntos do concurso-alvo no SGE e os temas das fichas de algumas aulas; todos vão
para a IA, para comparar com a escolha da regra e calibrar quando a regra decide sozinha.

    docker compose run --rm --no-deps -T -v ~/casamento:/saida planejamento \\
        python integracao/casar_taxonomia.py --concurso 1 --db /dados/material/catalogo.db --saida /saida
"""

import argparse
import json
import math
import os
import re
import sqlite3
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ia_comum import IaIndisponivel, completar_json  # noqa: E402

PASTA_TAXONOMIA = Path(__file__).resolve().parent / "taxonomia"
VAZIAS = set("de da do das dos e em a o as os para com por no na nos nas ao aos um uma sua seu suas seus ou "
             "outros outras demais assuntos questoes variadas mescladas topicos aspectos gerais nocoes conceitos "
             "basicos basicas introducao principais geral".split())
CANDIDATOS = 8
LOTE = 25
LOTE_ARVORE = 20
# Ensaio de 2026-10-20: a busca por palavras deixa o nó certo de fora quando o nome muda ('Coordenação e
# subordinação' x 'orações coordenadas'); as árvores das disciplinas são pequenas (mediana 32 nós), então a IA
# vê a árvore inteira das disciplinas ligadas. Só as maiores (legislação municipal e estadual) ficam na busca.
MAX_NOS_ARVORE = 1200
# Disciplina enorme (Legislação Estadual: 969 nós, todos os estados): entram só os ramos cujo nome tem palavra
# da disciplina do item ('Conhecimentos Regionais de Santa Catarina' -> 'Legislação do Estado de Santa Catarina').
MAX_NOS_DISCIPLINA = 300
CANDIDATOS_SEGUNDA = 15


def palavras(texto):
    """Palavras sem acento, minúsculas, sem as vazias; plural simples tirado ('protocolos' -> 'protocolo')."""
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().lower()
    saida = []
    for token in re.findall(r"[a-z0-9]+", t):
        # sigla colada na versão ('ITILv4', 'ISO27001', 'IPv6') vale a sigla e o número, como em 'ITIL 4'
        colada = re.fullmatch(r"([a-z]{3,}?)v?(\d+)", token)
        for w in (colada.groups() if colada else (token,)):
            if w in VAZIAS or len(w) < 2:
                continue
            saida.append(w[:-1] if len(w) > 4 and w.endswith("s") else w)
    return saida


def carregar_arvore(pasta=PASTA_TAXONOMIA, fonte="qconcursos"):
    arquivo = sorted(pasta.glob(f"{fonte}-*.json"))[-1]
    return json.loads(arquivo.read_text(encoding="utf-8"))["disciplinas"], arquivo.name


class Arvore:
    """Os nós da árvore com caminho, pai e um índice invertido de palavras para achar candidatos."""

    def __init__(self, disciplinas):
        self.nos = {}
        def andar(n, pai, caminho):
            c = caminho + [n["nome"]]
            self.nos[n["id"]] = {"id": n["id"], "nome": n["nome"], "pai": pai, "caminho": c, "nivel": len(c),
                                 "palavras": set(palavras(n["nome"])), "contexto": set(palavras(" ".join(c)))}
            for f in n["filhos"]:
                andar(f, n["id"], c)
        for d in disciplinas:
            andar(d, None, [])
        freq = Counter(w for n in self.nos.values() for w in n["contexto"])
        self.idf = {w: math.log(len(self.nos) / f) for w, f in freq.items()}
        self.indice = {}
        for i, n in self.nos.items():
            for w in n["contexto"]:
                self.indice.setdefault(w, set()).add(i)

    def subarvore(self, raizes, disciplina=""):
        """Os ids dos nós abaixo das disciplinas 'raizes' (sem as próprias disciplinas), na ordem da árvore. De
        disciplina com mais de MAX_NOS_DISCIPLINA nós, só os ramos cujo nome tem palavra de 'disciplina'."""
        raizes, chave = set(raizes), set(palavras(disciplina))
        por_raiz = {}
        for i in self.nos:
            if self.nos[i]["nivel"] > 1:
                anc = self.ancestrais(i)
                if anc[-1] in raizes:
                    por_raiz.setdefault(anc[-1], []).append((i, anc))
        saida = []
        for r, membros in por_raiz.items():
            if len(membros) > MAX_NOS_DISCIPLINA:
                ramos = {a[-2] for _, a in membros if len(a) >= 2 and self.nos[a[-2]]["palavras"] & chave - self.nos[r]["palavras"]}
                membros = [(i, a) for i, a in membros if len(a) >= 2 and a[-2] in ramos]
            saida += [i for i, _ in membros]
        return saida

    def ancestrais(self, i):
        saida = []
        while i is not None:
            saida.append(i)
            i = self.nos[i]["pai"]
        return saida

    def candidatos(self, nome, extras=(), disciplina="", n=CANDIDATOS, raizes=None):
        """Os n nós mais parecidos: quanto das palavras do nó o item cobre (o nó inteiro achado vale mais) e
        quanto do item o caminho do nó cobre; a disciplina só desempata. 'raizes': só nós destas disciplinas
        do QConcursos (as ligadas à disciplina do item); sem elas, a árvore toda. Devolve [(nota, id)]."""
        q = set(palavras(nome)) | set(w for e in extras for w in palavras(e))
        qd = set(palavras(disciplina))
        if not q:
            return []
        peso = lambda ws: sum(self.idf.get(w, 0) for w in ws) or 1e-9  # noqa: E731
        possiveis = set().union(*(self.indice.get(w, set()) for w in q))
        notas = []
        for i in possiveis:
            no = self.nos[i]
            if no["nivel"] == 1 or not no["palavras"]:
                continue
            if raizes and self.ancestrais(i)[-1] not in raizes:
                continue
            cobre_no = peso(no["palavras"] & q) / peso(no["palavras"])
            cobre_item = peso(no["contexto"] & q) / peso(q)
            raiz = self.nos[self.ancestrais(i)[-1]]
            bonus = 0.05 if qd and qd & raiz["palavras"] else 0
            notas.append((round(0.6 * cobre_no + 0.4 * cobre_item + bonus, 3), i))
        return sorted(notas, reverse=True)[:n]


SISTEMA_DISCIPLINAS = """Você liga disciplinas de editais e de apostilas de concurso às disciplinas do QConcursos.
Responda só com JSON, sem texto fora dele."""


def mapear_disciplinas(sge, nomes, arvore):
    """{disciplina do edital ou da ficha: [ids das disciplinas do QConcursos]}, numa chamada só: uma disciplina
    larga ('Conhecimentos Específicos - Ciências da Computação') liga a várias."""
    raizes = sorted((n["nome"], i) for i, n in arvore.nos.items() if n["nivel"] == 1)
    pedido = ("Disciplinas do QConcursos (id: nome):\n" + "\n".join(f"{i}: {nome}" for nome, i in raizes)
              + "\n\nDisciplinas a ligar:\n" + "\n".join(f"- {n}" for n in nomes)
              + "\n\nPara cada uma, os ids das disciplinas do QConcursos que cobrem o mesmo conteúdo. Disciplina que é uma "
                "área inteira (ex.: Ciências da Computação, Ciência de Dados, Inteligência Artificial, Tecnologia da "
                "Informação) liga a TODAS as disciplinas do QConcursos que a área abrange (ex.: Banco de Dados, "
                "Programação, Engenharia de Software, Redes, Segurança da Informação, Estatística...). Lista vazia só "
                "se nada do QConcursos tratar do conteúdo.\nResponda: {\"disciplinas\": {\"nome exatamente como veio\": [ids]}}")
    resposta = completar_json(sge, SISTEMA_DISCIPLINAS, pedido)
    validos = {i for _, i in raizes}
    return {n: [i for i in (resposta.get("disciplinas") or {}).get(n, []) if i in validos] for n in nomes}


SISTEMA = """Você liga assuntos de concurso público aos nós da árvore de assuntos do QConcursos.
Responda só com JSON, sem texto fora dele."""

INSTRUCOES = """Para cada item, escolha entre os candidatos dele os nós que correspondem ao MESMO assunto (até 3:
use mais de um só quando o item junta assuntos que a árvore separa). Prefira o nó mais específico que cobre
o item inteiro. Se não houver nó específico para o assunto, escolha o nó mais próximo que o CONTÉM (o ramo onde
as questões desse assunto estariam) e marque confiança "baixa". Lista vazia só se nada da árvore trata do
assunto. Não invente id fora dos candidatos.

Diga também a NATUREZA do vínculo: "exato" (o nó é o mesmo assunto do item), "mais_amplo" (não há nó específico;
o nó escolhido contém o assunto) ou "parcial" (os nós escolhidos cobrem só uma parte do item).

Responda: {"ligacoes": [{"item": número do item, "nos": [ids], "natureza": "exato" | "mais_amplo" | "parcial",
  "confianca": "alta" | "media" | "baixa"}]}"""


def pedido_com_arvore(itens, arvore, ids):
    """O lote de itens de uma mesma disciplina com a árvore inteira dela (só nomes)."""
    linhas = ["Árvore de assuntos do QConcursos (id: caminho):"]
    linhas += [f"{i}: {' > '.join(arvore.nos[i]['caminho'])}" for i in ids]
    linhas.append("\nItens:")
    for k, it in enumerate(itens, 1):
        extra = f" (termos: {', '.join(it['termos'][:6])})" if it.get("termos") else ""
        linhas.append(f"{k}. [{it['disciplina'] or '?'}] {it['nome']}{extra}")
    return "\n".join(linhas) + "\n\n" + INSTRUCOES.replace("entre os candidatos dele", "na árvore acima")


def pedido_do_lote(itens, arvore):
    linhas = []
    for k, it in enumerate(itens, 1):
        extra = f" (termos: {', '.join(it['termos'][:6])})" if it.get("termos") else ""
        linhas.append(f"{k}. [{it['disciplina'] or '?'}] {it['nome']}{extra}")
        for _, i in it["candidatos"]:
            linhas.append(f"   - {i}: {' > '.join(arvore.nos[i]['caminho'])}")
    return "\n".join(linhas) + "\n\n" + INSTRUCOES


def _inteiro(x):
    """A IA às vezes devolve número como texto ('12345', ' 3'): aceita os dois."""
    try:
        return int(str(x).strip())
    except (TypeError, ValueError):
        return None


def ligar_com_ia(sge, itens, arvore, log=print, respostas=None):
    """Grava em cada item 'ia': [ids] e 'confianca'. Itens com disciplinas ligadas de árvore pequena vão em
    lotes por disciplina, com a árvore inteira; os outros, com os candidatos da busca por palavras. Id que a
    IA não recebeu é descartado."""
    grupos = {}
    for it in itens:
        ids = arvore.subarvore(it.get("raizes") or [], it.get("disciplina") or "")
        chave = (tuple(sorted(it.get("raizes") or [])), it.get("disciplina") or "") if ids and len(ids) <= MAX_NOS_ARVORE else None
        grupos.setdefault(chave, []).append(it)
    feitos = 0
    for chave, membros in grupos.items():
        ids = arvore.subarvore(*chave) if chave else None
        passo = LOTE_ARVORE if chave else LOTE
        for ini in range(0, len(membros), passo):
            lote = membros[ini:ini + passo]
            pedido = pedido_com_arvore(lote, arvore, ids) if chave else pedido_do_lote(lote, arvore)
            resposta = completar_json(sge, SISTEMA, pedido)
            if respostas is not None:
                respostas.append(resposta)
            por_item = {_inteiro(r.get("item")): r for r in (resposta.get("ligacoes") or []) if isinstance(r, dict)}
            for k, it in enumerate(lote, 1):
                r = por_item.get(k) or {}
                validos = set(ids) if chave else {i for _, i in it["candidatos"]}
                it["ia"] = [i for i in map(_inteiro, r.get("nos") or []) if i in validos][:3]
                it["confianca"] = r.get("confianca")
                it["natureza"] = r.get("natureza")
            feitos += len(lote)
            log(f"... {feitos} de {len(itens)} itens")
    # Segunda passada: item sem nó (lei que mora em 'Legislação Federal', assunto fora das disciplinas ligadas)
    # ganha candidatos por palavras na árvore inteira.
    sem = [it for it in itens if not it.get("ia")]
    for it in sem:
        it["candidatos"] = arvore.candidatos(it["nome"], it.get("termos") or [], it.get("disciplina") or "",
                                             n=CANDIDATOS_SEGUNDA)
    sem = [it for it in sem if it["candidatos"]]
    for ini in range(0, len(sem), LOTE):
        lote = sem[ini:ini + LOTE]
        resposta = completar_json(sge, SISTEMA, pedido_do_lote(lote, arvore))
        if respostas is not None:
            respostas.append(resposta)
        por_item = {_inteiro(r.get("item")): r for r in (resposta.get("ligacoes") or []) if isinstance(r, dict)}
        for k, it in enumerate(lote, 1):
            r = por_item.get(k) or {}
            validos = {i for _, i in it["candidatos"]}
            it["ia"] = [i for i in map(_inteiro, r.get("nos") or []) if i in validos][:3]
            it["confianca"] = r.get("confianca")
            it["natureza"] = r.get("natureza")
            it["segunda_passada"] = True
        log(f"... segunda passada: {min(ini + LOTE, len(sem))} de {len(sem)} itens sem nó")


SISTEMA_REFINO = """Você confere ligações de assuntos de concurso público a nós da árvore de assuntos do QConcursos.
Responda só com JSON, sem texto fora dele."""

INSTRUCOES_REFINO = """Cada item já tem uma ligação (nó ATUAL, que pode estar vazio) feita só dentro das disciplinas ligadas
ao edital. Abaixo dela há CANDIDATOS achados na árvore inteira pelas palavras do item. Escolha, entre o atual e os
candidatos, o nó mais específico que corresponde ao MESMO assunto do item (até 3 se o item junta assuntos que a
árvore separa). Troque o atual só quando um candidato for claramente mais adequado: mesmo assunto, ou ramo certo e
mais específico. Se o atual for o melhor, devolva-o. Se nenhum serve, lista vazia. Não invente id fora da lista.

Responda: {"ligacoes": [{"item": número do item, "nos": [ids], "natureza": "exato" | "mais_amplo" | "parcial"}]}"""

REFINAR_NATUREZAS = ("mais_amplo", "parcial", None, "")


def refinar(sge, itens, arvore, log=print, respostas=None, candidatos=CANDIDATOS_SEGUNDA):
    """Segunda checagem dos itens 'mais_amplo', 'parcial' ou sem nó: candidatos da árvore inteira, por palavras, e a
    IA fica com o nó atual ou troca. Guarda 'ia_antes' quando troca e marca 'refinado'. Id fora da lista é descartado."""
    alvo = [it for it in itens if it.get("natureza") in REFINAR_NATUREZAS]
    for it in alvo:
        achados = arvore.candidatos(it["nome"], it.get("termos") or [], it.get("disciplina") or "", n=candidatos)
        it["candidatos_refino"] = [i for _, i in achados if i not in (it.get("ia") or [])]
    alvo = [it for it in alvo if it["candidatos_refino"]]
    nome = lambda i: " > ".join(arvore.nos[i]["caminho"])  # noqa: E731
    for ini in range(0, len(alvo), LOTE):
        lote = alvo[ini:ini + LOTE]
        linhas = []
        for k, it in enumerate(lote, 1):
            extra = f" (termos: {', '.join(it['termos'][:6])})" if it.get("termos") else ""
            linhas.append(f"{k}. [{it['disciplina'] or '?'}] {it['nome']}{extra}")
            linhas.append("   ATUAL: " + ("; ".join(f"{i}: {nome(i)}" for i in it.get("ia") or []) or "nenhum"))
            linhas += [f"   - {i}: {nome(i)}" for i in it["candidatos_refino"]]
        resposta = completar_json(sge, SISTEMA_REFINO, "\n".join(linhas) + "\n\n" + INSTRUCOES_REFINO)
        if respostas is not None:
            respostas.append(resposta)
        por_item = {_inteiro(r.get("item")): r for r in (resposta.get("ligacoes") or []) if isinstance(r, dict)}
        for k, it in enumerate(lote, 1):
            r = por_item.get(k)
            if not r:
                continue
            validos = set(it["candidatos_refino"]) | set(it.get("ia") or [])
            novos = [i for i in map(_inteiro, r.get("nos") or []) if i in validos][:3]
            if novos != (it.get("ia") or []):
                it["ia_antes"] = it.get("ia") or []
                it["ia"] = novos
                it["natureza"] = r.get("natureza") if novos else None
                it["refinado"] = True
        log(f"... refino: {min(ini + LOTE, len(alvo))} de {len(alvo)} itens")


def regra_decide(it, minimo=0.75, margem=0.15):
    """A regra decide sozinha quando o primeiro candidato é forte e o segundo bem atrás (ou é o mesmo ramo)."""
    c = it["candidatos"]
    if not c or c[0][0] < minimo:
        return None
    return c[0][1] if len(c) == 1 or c[0][0] - c[1][0] >= margem else None


def casam(arvore, a, b):
    """a e b (ids) casam se um é o outro ou está dentro dele, abaixo do nível de disciplina."""
    return a == b or (a in arvore.ancestrais(b) and arvore.nos[a]["nivel"] > 1) or \
        (b in arvore.ancestrais(a) and arvore.nos[b]["nivel"] > 1)


def itens_do_edital(planejamento, arvore, disciplinas=None):
    itens = []
    for a in planejamento["assuntos"]:
        raizes = set((disciplinas or {}).get(a["disciplina"]) or [])
        itens.append({"tipo": "edital", "nome": a["assunto"], "disciplina": a["disciplina"], "termos": [],
                      "chave": a["chaveExterna"], "raizes": sorted(raizes),
                      "candidatos": arvore.candidatos(a["assunto"], (), a["disciplina"], raizes=raizes)})
    return itens


def itens_das_fichas(db, caminhos, arvore, disciplinas=None):
    itens = []
    for caminho in caminhos:
        linha = db.execute("SELECT ficha FROM fichas WHERE caminho = ? AND situacao = 'ok'", (caminho,)).fetchone()
        if not linha:
            continue
        for t in json.loads(linha[0])["temas"]:
            extras = list(t.get("termos") or []) + [s["nome"] for s in t.get("subtemas", [])][:4]
            raizes = sorted((disciplinas or {}).get(t.get("disciplina")) or [])
            itens.append({"tipo": "ficha", "nome": t["tema"], "disciplina": t.get("disciplina"), "termos": t.get("termos") or [],
                          "caminho": caminho, "paginas": t.get("paginas"), "raizes": raizes,
                          "candidatos": arvore.candidatos(t["tema"], extras, t.get("disciplina") or "",
                                                          raizes=set((disciplinas or {}).get(t.get("disciplina")) or []))})
    return itens


def relatorio(itens, arvore, nome_arvore):
    nomes = lambda ids: "; ".join(" > ".join(arvore.nos[i]["caminho"]) for i in ids) or "**nenhum nó**"  # noqa: E731
    total = len(itens)
    decide = [it for it in itens if regra_decide(it)]
    acerta = [it for it in decide if it.get("ia") and any(casam(arvore, regra_decide(it), i) for i in it["ia"])]
    sem_no = [it for it in itens if "ia" in it and not it["ia"]]
    saida = [f"# Ensaio: edital e fichas na árvore do QConcursos ({nome_arvore})", "",
             f"Itens: {total} ({sum(it['tipo'] == 'edital' for it in itens)} assuntos do edital, "
             f"{sum(it['tipo'] == 'ficha' for it in itens)} temas de fichas).",
             f"A regra decidiria sozinha {len(decide)}; desses, a IA concordou (mesmo nó ou um dentro do outro) em "
             f"{len(acerta)}. A IA não achou nó para {len(sem_no)}.", "",
             "Marque `[x]` se a ligação confere, ou escreva ao lado o nó certo.", ""]
    edital = [it for it in itens if it["tipo"] == "edital"]
    fichas = [it for it in itens if it["tipo"] == "ficha"]
    saida += ["## Assuntos do edital → nós", ""]
    for it in edital:
        regra = regra_decide(it)
        saida.append(f"- [ ] **{it['nome']}** _({it['disciplina']})_ → {nomes(it.get('ia', []))}"
                     + (f" · confiança {it['confianca']}" if it.get("confianca") else "")
                     + (" · regra concorda" if regra and any(casam(arvore, regra, i) for i in it.get("ia", [])) else
                        f" · regra diria: {nomes([regra])}" if regra else ""))
    saida += ["", "## Casamento: assunto do edital → temas das fichas (só as aulas do ensaio)", ""]
    for it in edital:
        achados = [f for f in fichas if any(casam(arvore, a, b) for a in it.get("ia", []) for b in f.get("ia", []))]
        if achados:
            saida.append(f"- **{it['nome']}**: " + "; ".join(f"{f['nome']} — `{f['caminho']}` p. "
                                                           + ", ".join(f"{i}–{j}" for i, j in (f.get('paginas') or []))
                                                           for f in achados))
    saida += ["", "## Temas das fichas → nós", ""]
    for it in fichas:
        saida.append(f"- [ ] {it['nome']} _({it['disciplina']})_ → {nomes(it.get('ia', []))}")
    return "\n".join(saida)


def main():
    ap = argparse.ArgumentParser(description="Ensaio: assuntos do edital e temas das fichas na árvore do QConcursos.")
    ap.add_argument("--concurso", type=int, required=True)
    ap.add_argument("--db", required=True, help="catalogo.db")
    ap.add_argument("--fichas", help="JSON com a lista de caminhos das aulas do ensaio (padrão: as do catalogo-ensaio)")
    ap.add_argument("--saida", required=True)
    args = ap.parse_args()
    from sge_api import SgeApi
    sge = SgeApi(os.environ.get("SGE_URL", "http://app:8080"), os.environ["INTERNAL_TOKEN"])
    disciplinas, nome_arvore = carregar_arvore()
    arvore = Arvore(disciplinas)
    db = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    caminhos = json.loads(Path(args.fichas).read_text(encoding="utf-8")) if args.fichas else []
    planejamento = sge.planejamento(args.concurso)
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    nomes = sorted({a["disciplina"] for a in planejamento["assuntos"]} | {
        t.get("disciplina") for c in caminhos for (f,) in db.execute("SELECT ficha FROM fichas WHERE caminho = ? AND "
                                                                     "situacao = 'ok'", (c,)) for t in json.loads(f)["temas"]} - {None})
    arquivo_disc = saida / "disciplinas.json"
    disciplinas = json.loads(arquivo_disc.read_text(encoding="utf-8")) if arquivo_disc.exists() else {}
    faltam = [n for n in nomes if n not in disciplinas]
    if faltam:
        disciplinas.update(mapear_disciplinas(sge, faltam, arvore))
        arquivo_disc.write_text(json.dumps(disciplinas, ensure_ascii=False, indent=1), encoding="utf-8")
    itens = itens_do_edital(planejamento, arvore, disciplinas) + itens_das_fichas(db, caminhos, arvore, disciplinas)
    respostas = []
    try:
        ligar_com_ia(sge, itens, arvore, respostas=respostas)
    except IaIndisponivel as e:
        print(f"A IA parou: {e}")
    (saida / "respostas-ia.json").write_text(json.dumps(respostas, ensure_ascii=False, indent=1), encoding="utf-8")
    (saida / "disciplinas.md").write_text("# Disciplinas → QConcursos\n\n" + "\n".join(
        f"- [ ] **{n}** → {'; '.join(arvore.nos[i]['nome'] for i in ids) or '**nenhuma**'}" for n, ids in sorted(disciplinas.items())),
        encoding="utf-8")
    (saida / "casamento-ensaio.json").write_text(json.dumps(itens, ensure_ascii=False, indent=1), encoding="utf-8")
    (saida / "casamento-ensaio.md").write_text(relatorio(itens, arvore, nome_arvore), encoding="utf-8")
    print(f"{len(itens)} itens; relatório em {saida / 'casamento-ensaio.md'}")


if __name__ == "__main__":
    main()
