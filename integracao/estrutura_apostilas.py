#!/usr/bin/env python3
"""
estrutura_apostilas.py — Como as apostilas do acervo são montadas? Medição SEM IA, antes de definir as
regras do catálogo de aulas (decisão de 2026-10-19: nenhuma chamada de IA antes de as regras estarem
definidas e testadas em tipos diferentes de curso).

Para uma amostra de aulas de cursos de tipos diferentes (curso regular, pós-edital, especialidade,
passo estratégico, bizu, lei), lê só o índice (indice.db) e mostra, por aula:

- páginas, marcadores do PDF (bookmarks) e quantos de nível 1/2;
- a abertura (páginas 1 e 2) — o que diz o título da aula;
- se há página de sumário nas 6 primeiras e as linhas dela;
- onde aparecem as seções típicas (questões comentadas, lista de questões, gabarito, resumo, ...);
- de que banca são as questões (contagem de FCC, CEBRASPE, FGV, ...);
- páginas sem texto.

E, no fim, o resumo por curso. É isso que diz se o catálogo pode sair do título + sumário (barato) ou
se precisa ler o conteúdo, e se as seções de teoria/questões/resumo podem ser achadas por regra.

Uso (no contêiner do worker, que tem o índice):

    docker compose exec -T planejamento python integracao/estrutura_apostilas.py > ~/estrutura.md
    docker compose exec -T planejamento python integracao/estrutura_apostilas.py --curso "Ciência de Dados" --aulas 5
"""

import argparse
import os
import re
import sqlite3
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

SECOES = {
    "sumario": r"sum[áa]rio|[íi]ndice",
    "questoes_comentadas": r"quest[õo]es\s+comentadas|exerc[íi]cios\s+comentados",
    "lista_questoes": r"lista\s+de\s+(quest[õo]es|exerc[íi]cios)",
    "gabarito": r"^\s*gabarito",
    "resumo": r"^\s*(resumo|mapa\s+mental|esquema)",
    "consideracoes_finais": r"considera[çc][õo]es\s+finais",
    "apresentacao": r"apresenta[çc][ãa]o\s+(da\s+aula|do\s+curso)",
}
ENTRADA_SUMARIO = re.compile(r"\.{3,}|…|\s\d{1,3}\s*$")
BANCAS = {"FCC": r"\bFCC\b", "CEBRASPE": r"\bCEBRASPE\b|\bCESPE\b", "FGV": r"\bFGV\b",
          "VUNESP": r"\bVUNESP\b", "CESGRANRIO": r"\bCESGRANRIO\b", "IDECAN": r"\bIDECAN\b"}


def linhas_uteis(texto, n=25):
    return [l.strip() for l in (texto or "").splitlines() if len(l.strip()) > 3][:n]


def analisar_aula(conn, arquivo_id):
    paginas = conn.execute("SELECT pagina, texto FROM paginas WHERE arquivo_id = ? ORDER BY pagina",
                           (arquivo_id,)).fetchall()
    marcadores = conn.execute("SELECT nivel, titulo, pagina FROM bookmarks WHERE arquivo_id = ? ORDER BY pagina",
                              (arquivo_id,)).fetchall()
    secoes = {}
    for nome, padrao in SECOES.items():
        regex = re.compile(padrao, re.IGNORECASE | re.MULTILINE)
        # Linha que É o título da seção (curta), não a menção no meio de um parágrafo nem a entrada
        # do sumário ("Questões Comentadas ........ 6").
        achadas = [p for p, t in paginas
                   if any(regex.search(l) and len(l.strip()) < 60 and not ENTRADA_SUMARIO.search(l)
                          for l in (t or "").splitlines())]
        if achadas:
            secoes[nome] = achadas
    inicio_questoes = min(secoes.get("questoes_comentadas", []) + secoes.get("lista_questoes", []), default=None)
    trecho = [t for p, t in paginas if inicio_questoes and p >= inicio_questoes] or [t for _, t in paginas]
    bancas = {b: sum(len(re.findall(r, t or "")) for t in trecho) for b, r in BANCAS.items()}
    sumario = next(((p, t) for p, t in paginas[:6] if re.search(SECOES["sumario"], t or "", re.IGNORECASE)), None)
    return {
        "n": len(paginas),
        "vazias": sum(1 for _, t in paginas if len((t or "").strip()) < 20),
        "marcadores": marcadores,
        "abertura": " | ".join(" ".join(linhas_uteis(t, 4)) for _, t in paginas[:2])[:300],
        "sumario": (sumario[0], linhas_uteis(sumario[1])) if sumario else None,
        "secoes": secoes,
        "inicio_questoes": inicio_questoes,
        "bancas": {b: n for b, n in bancas.items() if n},
    }


def faixa(paginas):
    return f"p. {paginas[0]}" + (f" (+{len(paginas) - 1})" if len(paginas) > 1 else "")


def relatorio(conn, cursos, aulas_por_curso):
    saida, resumo = ["# Estrutura das apostilas (amostra, sem IA)", ""], []
    for padrao in cursos:
        arquivos = conn.execute("SELECT id, curso, nome_arquivo, n_paginas FROM arquivos WHERE curso LIKE ? "
                                "ORDER BY nome_arquivo", (f"%{padrao}%",)).fetchall()
        if not arquivos:
            saida += [f"## {padrao}", "", "_nenhum arquivo casou_", ""]
            continue
        # Primeira, do meio e última (ou espalhadas, se pedirem mais).
        passo = max(1, (len(arquivos) - 1) // max(1, aulas_por_curso - 1))
        amostra = sorted({min(i, len(arquivos) - 1) for i in range(0, len(arquivos), passo)})[:aulas_por_curso]
        saida += [f"## {arquivos[0][1]}  ({len(arquivos)} arquivos)", ""]
        com_marcador = com_sumario = com_questoes = com_resumo = 0
        for i in amostra:
            arquivo_id, _, nome, _ = arquivos[i]
            a = analisar_aula(conn, arquivo_id)
            com_marcador += bool(a["marcadores"])
            com_sumario += bool(a["sumario"])
            com_questoes += a["inicio_questoes"] is not None
            com_resumo += "resumo" in a["secoes"]
            niveis = {}
            for nivel, _, _ in a["marcadores"]:
                niveis[nivel] = niveis.get(nivel, 0) + 1
            saida += [f"### {nome} — {a['n']} págs, {a['vazias']} sem texto",
                      f"- abertura: {a['abertura']}",
                      f"- marcadores: {len(a['marcadores'])} " + (str(niveis) if niveis else "")]
            for nivel, titulo, pagina in a["marcadores"][:15]:
                saida.append(f"    - {'  ' * (nivel - 1)}{titulo[:70]} (p. {pagina})")
            if a["sumario"]:
                saida.append(f"- sumário na p. {a['sumario'][0]}:")
                saida += [f"    - {l[:90]}" for l in a["sumario"][1]]
            else:
                saida.append("- sumário: não achado nas 6 primeiras páginas")
            saida.append("- seções: " + ("; ".join(f"{n} {faixa(p)}" for n, p in a["secoes"].items() if n != "sumario")
                                         or "nenhuma achada"))
            pct = f" ({100 * a['inicio_questoes'] // max(1, a['n'])}% da aula)" if a["inicio_questoes"] else ""
            saida.append(f"- questões começam: {a['inicio_questoes'] or '—'}{pct}; bancas: {a['bancas'] or '—'}")
            saida.append("")
        n = len(amostra)
        resumo.append(f"| {arquivos[0][1][-60:]} | {n} | {com_marcador} | {com_sumario} | {com_questoes} | {com_resumo} |")
    saida += ["## Resumo por curso", "",
              "| Curso | Aulas lidas | Com marcadores | Com sumário | Com seção de questões | Com resumo |",
              "|---|---|---|---|---|---|", *resumo]
    return "\n".join(saida)


def main():
    ap = argparse.ArgumentParser(description="Estrutura das apostilas (amostra, sem IA).")
    ap.add_argument("--curso", action="append", help="trecho do nome da pasta (repetível); padrão: a amostra")
    ap.add_argument("--aulas", type=int, default=3, help="aulas por curso (padrão 3: primeira, meio, última)")
    ap.add_argument("--indice", default=os.environ.get("INDICE_DB"))
    args = ap.parse_args()
    with closing(sqlite3.connect(f"file:{args.indice}?mode=ro", uri=True)) as conn:
        print(relatorio(conn, args.curso or AMOSTRA, args.aulas))


if __name__ == "__main__":
    main()
