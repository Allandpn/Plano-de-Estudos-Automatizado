#!/usr/bin/env python3
"""
diagnostico_prova.py — Onde se perdeu o conteúdo que uma prova cobrou e o material não entregou?

A auditoria da cadeia do material (SGE `docs/AUDITORIA-CADEIA-MATERIAL.md`, 2026-10-18)
procurou cada conceito que faltou só no ÍNDICE do acervo. Faltava separar o que estava no
material e o julgador não viu do que nunca chegou ao material. Este script faz isso, sem IA:
para cada questão NAO_RESPONDIVEL ou PARCIAL da prova, procura cada conceito

    1. nos PDFs dos segmentos do assunto ATRIBUÍDO à questão;
    2. nos PDFs dos segmentos de TODOS os assuntos do concurso-alvo;
    3. no índice do acervo inteiro (se INDICE_DB estiver configurado);

e classifica:

    JULGADOR   está no segmento do assunto atribuído — o material tinha; as 6 páginas que o
               julgamento escolheu não o trouxeram (ou o julgador foi rigoroso)
    ATRIBUICAO está no material de outro assunto do concurso — a questão foi para o assunto errado
               (ou o tema se divide entre dois assuntos)
    CADEIA     só no acervo — a busca ou a triagem não o trouxe ao material
    ACERVO     em lugar nenhum — o acervo não tem
    SEM_TERMO  a questão não tem conceito listado (texto-base, gráfico, artigo de lei)

Os conceitos vêm de um JSON {"<número>": ["conceito", ["sinônimo", "sinônimo"], ...]} (--conceitos; o da
prova 2 está em integracao/diagnostico/conceitos-prova-2.json). Sem o arquivo, saem do
campo `falta` do veredito, o que é ruidoso: prefira listar. Casamento por frase, sem acento,
sem diferenciar maiúsculas; sigla curta ("NTP") pode casar por acaso — confira a página.

Roda no contêiner do worker (tem o material, o índice e a rede do SGE):

    docker compose exec planejamento python integracao/diagnostico_prova.py --prova 2 \\
        --conceitos integracao/diagnostico/conceitos-prova-2.json > diagnostico-prova-2.md

Variáveis: SGE_URL (http://app:8080), MATERIAL_DIR, INDICE_DB (opcional), INTERNAL_TOKEN (não usado
nas rotas públicas, aceito por simetria com o worker).
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acervo import termos_de_busca  # noqa: E402
from sge_api import SgeApi  # noqa: E402

VEREDITOS_FALHA = ("NAO_RESPONDIVEL", "PARCIAL")


def frase_fts(conceito):
    """'TLS 1.3' -> '"tls 1 3"': frase FTS5 com as palavras do conceito, sem pontuação."""
    palavras = re.findall(r"\w+", conceito.lower())
    return '"' + " ".join(palavras) + '"' if palavras else None


class MaterialDoConcurso:
    """O texto de todas as páginas dos segmentos do concurso, com o assunto de cada uma, em FTS5."""

    def __init__(self, segmentos_por_assunto, material_dir, abrir_pdf=None):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("CREATE VIRTUAL TABLE p USING fts5(texto, assunto UNINDEXED, seg UNINDEXED, "
                        "pag UNINDEXED, tokenize='unicode61 remove_diacritics 2')")
        self.ilegiveis = []
        abrir_pdf = abrir_pdf or _paginas_do_pdf
        for assunto_id, segmentos in segmentos_por_assunto.items():
            for s in segmentos:
                caminho = Path(material_dir) / s["arquivo"].removeprefix("/material/")
                try:
                    for numero, texto in enumerate(abrir_pdf(caminho), 1):
                        if texto.strip():
                            self.db.execute("INSERT INTO p VALUES (?, ?, ?, ?)", (texto, assunto_id, s["id"], numero))
                except Exception as e:  # arquivo ausente ou corrompido: conta e segue
                    self.ilegiveis.append(f"{caminho}: {e}")

    def buscar(self, conceito, assunto_id=None, limite=3):
        frase = frase_fts(conceito)
        if not frase:
            return []
        filtro, args = ("AND assunto = ?", (frase, assunto_id, limite)) if assunto_id is not None else ("", (frase, limite))
        return self.db.execute(
            f"SELECT assunto, seg, pag, snippet(p, 0, '[', ']', '…', 10) FROM p WHERE p MATCH ? {filtro} "
            "ORDER BY bm25(p) LIMIT ?", args).fetchall()


def _paginas_do_pdf(caminho):
    import fitz  # PyMuPDF, já na imagem do worker
    with fitz.open(str(caminho)) as doc:
        return [pagina.get_text() for pagina in doc]


def no_acervo(indice_db, conceito):
    """(páginas que casam, [os 3 cursos com mais páginas]) no índice inteiro."""
    frase = frase_fts(conceito)
    if not indice_db or not frase:
        return None
    with closing(sqlite3.connect(f"file:{indice_db}?mode=ro", uri=True)) as conn:
        linhas = conn.execute(
            """SELECT a.curso, a.nome_arquivo, COUNT(*) n FROM paginas_fts
               JOIN paginas p ON p.id = paginas_fts.rowid JOIN arquivos a ON a.id = p.arquivo_id
               WHERE paginas_fts MATCH ? GROUP BY a.id ORDER BY n DESC""", (frase,)).fetchall()
    return sum(n for _, _, n in linhas), [f"{c}/{a} ({n})" for c, a, n in linhas[:3]]


ORDEM_CAUSAS = ["ACERVO", "CADEIA", "CADEIA?", "ATRIBUICAO", "JULGADOR"]


def onde_esta(conceito, questao, material, indice_db, nomes):
    """(causa, evidências) de um termo: o lugar mais perto da questão onde ele aparece."""
    no_assunto = material.buscar(conceito, questao["assuntoId"]) if questao.get("assuntoId") else []
    if no_assunto:
        return "JULGADOR", [f"S{s}-p{p}: {t}" for _, s, p, t in no_assunto]
    no_concurso = material.buscar(conceito)
    if no_concurso:
        return "ATRIBUICAO", [f"{nomes.get(a, a)[:50]} · S{s}-p{p}: {t}" for a, s, p, t in no_concurso]
    acervo = no_acervo(indice_db, conceito)
    if acervo is None:
        return "CADEIA?", ["índice do acervo não configurado (INDICE_DB)"]
    if acervo[0]:
        return "CADEIA", [f"{acervo[0]} pág. no acervo; " + "; ".join(acervo[1])]
    return "ACERVO", ["nenhuma página no acervo"]


def classificar(questao, conceitos, material, indice_db, nomes):
    """Uma linha do diagnóstico para a questão: causa e as evidências de cada conceito.

    Cada item de `conceitos` é um conceito: um texto, ou uma lista de sinônimos
    (["hiperconvergente", "hiperconvergência"]) — basta um sinônimo aparecer, e vale o mais perto
    da questão. Entre conceitos diferentes, a questão fica com o mais LONGE do material: se um
    deles nem chegou, é ali o furo."""
    if not conceitos:
        return "SEM_TERMO", []
    evidencias, causas = [], []
    for item in conceitos:
        sinonimos = item if isinstance(item, list) else [item]
        achados = [(termo, *onde_esta(termo, questao, material, indice_db, nomes)) for termo in sinonimos]
        termo, causa, onde = max(achados, key=lambda a: ORDEM_CAUSAS.index(a[1]))
        causas.append(causa)
        evidencias.append((" / ".join(sinonimos) if len(sinonimos) > 1 else termo, causa, onde))
    return min(causas, key=ORDEM_CAUSAS.index), evidencias


def conceitos_da_falta(falta):
    """Sem lista: as palavras do campo `falta`, sem as que não dizem conteúdo."""
    genericas = {"material", "nao", "pagina", "paginas", "questao", "alternativa", "gabarito", "ensina",
                 "trata", "explica", "traz", "sobre", "como", "seria", "preciso", "necessario", "qual"}
    return [t for t in termos_de_busca(falta or "") if t not in genericas][:6]


def relatorio_md(prova, linhas, ilegiveis):
    saida = [f"# Diagnóstico da prova {prova['provaId']} — {prova.get('nome') or ''}", "",
             "Causa por questão NAO_RESPONDIVEL ou PARCIAL (ver a docstring de `integracao/diagnostico_prova.py`).", ""]
    contagem = {}
    for _, causa, _ in linhas:
        contagem[causa] = contagem.get(causa, 0) + 1
    saida += ["| Causa | Questões |", "|---|---|"]
    saida += [f"| {c} | {n} |" for c, n in sorted(contagem.items(), key=lambda kv: -kv[1])]
    saida += ["", "| Q | Veredito | Assunto | Causa | Conceito → onde |", "|---|---|---|---|---|"]
    for q, causa, evidencias in linhas:
        detalhe = "<br>".join(f"**{c}** ({k}): " + " / ".join(o)[:300].replace("|", "/") for c, k, o in evidencias) or "—"
        saida.append(f"| {q['numero']} | {q['veredito']} | {(q.get('assunto') or '—')[:60]} | {causa} | {detalhe} |")
    if ilegiveis:
        saida += ["", "Segmentos ilegíveis:", *[f"- {i}" for i in ilegiveis]]
    return "\n".join(saida)


def main():
    ap = argparse.ArgumentParser(description="Onde se perdeu o conteúdo que a prova cobrou (sem IA).")
    ap.add_argument("--prova", type=int, required=True)
    ap.add_argument("--concurso", type=int, help="padrão: o concurso-alvo")
    ap.add_argument("--conceitos", help='JSON {"<número>": ["conceito", ...]}')
    args = ap.parse_args()

    env = os.environ
    sge = SgeApi(env.get("SGE_URL", "http://app:8080"), env.get("INTERNAL_TOKEN", ""))
    prova = sge._pedir("GET", f"/api/provas/{args.prova}/relatorio")[1]
    concurso_id = args.concurso or sge.concurso_ativo()["id"]
    material_por_assunto = sge._pedir("GET", f"/api/concursos/{concurso_id}/material")[1]
    nomes = {m["assuntoId"]: m["assunto"] for m in material_por_assunto}
    segmentos = {m["assuntoId"]: sge._pedir("GET", f"/api/assuntos/{m['assuntoId']}/segmentos")[1]
                 for m in material_por_assunto if m["segmentos"]}
    material = MaterialDoConcurso(segmentos, env["MATERIAL_DIR"])
    lista = json.loads(Path(args.conceitos).read_text(encoding="utf-8")) if args.conceitos else None

    linhas = []
    for q in prova["questoes"]:
        if q.get("veredito") not in VEREDITOS_FALHA:
            continue
        conceitos = lista.get(str(q["numero"]), []) if lista is not None else conceitos_da_falta(q.get("falta"))
        causa, evidencias = classificar(q, conceitos, material, env.get("INDICE_DB"), nomes)
        linhas.append((q, causa, evidencias))
    print(relatorio_md(prova, linhas, material.ilegiveis))


if __name__ == "__main__":
    main()
