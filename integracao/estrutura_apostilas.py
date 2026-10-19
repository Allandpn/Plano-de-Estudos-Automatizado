#!/usr/bin/env python3
"""
estrutura_apostilas.py — Como as apostilas do acervo são montadas? Medição SEM IA, antes de definir as
regras do catálogo de aulas (decisão de 2026-10-19: nenhuma chamada de IA antes de as regras estarem
definidas e testadas em tipos diferentes de curso).

Para uma amostra de aulas de cursos de tipos diferentes (curso regular, pós-edital, especialidade,
passo estratégico, bizu, lei), lê só o índice (indice.db) e mostra, por aula:

- páginas, páginas sem texto, marcadores do PDF (a primeira rodada, 2026-10-19: nenhuma aula tem);
- o SUMÁRIO decodificado. As apostilas têm na p. 2 um "Índice" no formato fixo
  "N) Tema - Tipo [- Banca] ...... página", que a extração devolve com os pontos da linha pontilhada
  intercalados nas letras (".N..A...T.. .e.. .P..A...T.."); tirados os pontos, cada entrada diz o tema,
  o tipo (teoria, resumo, mapa mental, questões comentadas, lista, gabarito) e a banca;
- se a página do sumário é a posição no PDF (procura o tema escrito naquela página, de -3 a +3);
- se o arquivo é aula (curto e sem sumário — aviso, orientação de estudos — fica fora);
- de que banca são as questões, pela contagem no texto.

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
          "VUNESP": r"\bVUNESP\b", "CESGRANRIO": r"\bCESGRANRIO\b", "IDECAN": r"\bIDECAN\b"}

# O sumário ("Índice") das apostilas segue um formato fixo: "N) Tema - Tipo [- Banca] ...... página".
TIPOS = [("teoria", r"teoria"), ("resumo", r"resumo"), ("mapa_mental", r"mapa\s+mental"),
         ("questoes_comentadas", r"quest[õo]es(\s+comentadas)?|exerc[íi]cios\s+comentados"),
         ("lista_questoes", r"lista\s+de\s+(quest|exerc)"), ("gabarito", r"gabarito"),
         ("apresentacao", r"apresenta[çc][ãa]o"), ("flashcards", r"flash\s*cards?")]
ENTRADA = re.compile(r"^(\d{1,3})\s*\)\s*(.+?)(?:\s+(\d{1,4}))?$")
MIN_PAGINAS_AULA = 10


def sem_acento(texto):
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")


def decodificar(linha):
    """'.1..). .N..A...T.. .e.. .P..A...T.. .-. .T..e..o..r.i.a...... 3' -> '1) NAT e PAT - Teoria 3': a linha
    pontilhada do sumário sai intercalada com as letras na extração; tirar os pontos devolve o texto."""
    l = (linha or "").strip().replace("…", "")
    if l.count(".") > len(l) / 4:
        l = l.replace(".", "")
    return re.sub(r"\s+", " ", l).strip()


def entrada_do_sumario(linha):
    """'1) NAT e PAT - Questões Comentadas - CEBRASPE 12' -> {n, tema, tipo, banca, pagina}; None se não é entrada."""
    m = ENTRADA.match(decodificar(linha))
    if not m:
        return None
    partes = [p.strip() for p in re.split(r"\s+-\s+|\s-|-\s", m.group(2)) if p.strip()]
    tipo, i_tipo = None, None
    for i, parte in enumerate(partes):
        tipo = next((nome for nome, r in TIPOS if re.match(r, parte, re.IGNORECASE)), None)
        if tipo:
            i_tipo = i
            break
    tema = " - ".join(partes[:i_tipo]) if i_tipo else (partes[0] if partes else "")
    resto = " ".join(partes[i_tipo + 1:]) if i_tipo is not None else ""
    banca = next((b for b, r in BANCAS.items() if re.search(r, resto)), None) if resto else None
    return {"n": int(m.group(1)), "tema": tema, "tipo": tipo, "banca": banca,
            "pagina": int(m.group(3)) if m.group(3) else None}


def sumario(paginas, primeiras=8):
    """As entradas do sumário: páginas 2 a 8 com pelo menos duas linhas que são entrada; para na
    primeira página sem entrada depois de achar alguma (o sumário ocupa mais de uma página nas aulas longas)."""
    entradas, achou = [], False
    for _, texto in paginas[1:primeiras]:
        desta = [e for e in map(entrada_do_sumario, (texto or "").splitlines()) if e]
        if len(desta) >= 2:
            entradas += desta
            achou = True
        elif achou:
            break
    return entradas


def chave(texto, n=10):
    return re.sub(r"[^A-Z]", "", sem_acento(texto or "").upper())[:n]


def deslocamento(paginas, entradas, alcance=3):
    """A página do sumário é a posição no PDF? Para cada deslocamento de -3 a +3, quantas entradas
    têm o tema escrito naquela página do PDF. Devolve (melhor deslocamento, confirmadas, testadas)."""
    texto = {p: chave(t, 10 ** 6) for p, t in paginas}
    testaveis = [e for e in entradas if e["pagina"] and len(chave(e["tema"])) >= 5]
    if not testaveis:
        return None, 0, 0
    placar = {d: sum(1 for e in testaveis if chave(e["tema"]) in texto.get(e["pagina"] + d, "")) for d in
              range(-alcance, alcance + 1)}
    melhor = max(placar, key=lambda d: (placar[d], -abs(d)))
    return melhor, placar[melhor], len(testaveis)


def analisar_aula(conn, arquivo_id):
    paginas = conn.execute("SELECT pagina, texto FROM paginas WHERE arquivo_id = ? ORDER BY pagina",
                           (arquivo_id,)).fetchall()
    marcadores = conn.execute("SELECT nivel, titulo, pagina FROM bookmarks WHERE arquivo_id = ? ORDER BY pagina",
                              (arquivo_id,)).fetchall()
    entradas = sumario(paginas)
    d, confirmadas, testadas = deslocamento(paginas, entradas)
    bancas = {b: sum(len(re.findall(r, t or "")) for _, t in paginas) for b, r in BANCAS.items()}
    return {
        "n": len(paginas),
        "vazias": sum(1 for _, t in paginas if len((t or "").strip()) < 20),
        "marcadores": marcadores,
        "abertura": " | ".join(" ".join(linhas_uteis(t, 3)) for _, t in paginas[:1])[:200],
        "entradas": entradas,
        "deslocamento": (d, confirmadas, testadas),
        "fora": len(paginas) < MIN_PAGINAS_AULA and not entradas,
        "bancas_texto": {b: n for b, n in bancas.items() if n},
    }


def linhas_uteis(texto, n=25):
    return [l.strip() for l in (texto or "").splitlines() if len(l.strip()) > 3][:n]


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
        c = {"com_sumario": 0, "entradas": 0, "com_tipo": 0, "com_banca": 0, "fora": 0, "conf": 0, "test": 0}
        desloc, tipos_vistos, bancas_vistas = {}, set(), set()
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
            if test:
                desloc[d] = desloc.get(d, 0) + 1
            tipos_vistos |= {x["tipo"] for x in e if x["tipo"]}
            bancas_vistas |= {x["banca"] for x in e if x["banca"]}
            saida += [f"### {nome} — {a['n']} págs, {a['vazias']} sem texto, {len(a['marcadores'])} marcadores"
                      + (" — FORA (curto e sem sumário)" if a["fora"] else ""),
                      f"- abertura: {a['abertura']}",
                      f"- sumário: {len(e)} entradas; página do sumário = página do PDF {d:+d} "
                      f"({conf} de {test} conferidas)" if test else f"- sumário: {len(e)} entradas, nenhuma conferível"]
            for x in e[:40]:
                saida.append(f"    - {x['n']}) {x['tema'][:60]} | {x['tipo'] or '?'} | {x['banca'] or ''} | p. {x['pagina'] or '?'}")
            if len(e) > 40:
                saida.append(f"    - … mais {len(e) - 40}")
            saida.append(f"- bancas no texto: {a['bancas_texto'] or '—'}")
            saida.append("")
        n = len(amostra)
        moda = max(desloc, key=desloc.get) if desloc else None
        resumo.append(f"| {arquivos[0][1][-55:]} | {n} | {c['fora']} | {c['com_sumario']} | {c['entradas']} | "
                      f"{100 * c['com_tipo'] // max(1, c['entradas'])}% | {100 * c['com_banca'] // max(1, c['entradas'])}% | "
                      f"{'—' if moda is None else f'{moda:+d}'} ({c['conf']}/{c['test']}) | "
                      f"{', '.join(sorted(tipos_vistos)) or '—'} | {', '.join(sorted(bancas_vistas)) or '—'} |")
    saida += ["## Resumo por curso", "",
              "| Curso | Aulas | Fora | Com sumário | Entradas | Com tipo | Com banca | Deslocamento (conferidas) | Tipos | Bancas |",
              "|---|---|---|---|---|---|---|---|---|---|", *resumo]
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
