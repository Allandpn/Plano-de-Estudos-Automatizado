#!/usr/bin/env python3
"""Escolhe, por regra, o material de um assunto a partir dos candidatos confirmados de cada parte (sem IA).

Faz parte do fluxo "material por casamento" (docs/proposta-material-por-casamento.md): `confirmar_material.py` diz, por
parte, quais temas de ficha ensinam; aqui se decide **o que entra no plano** segundo a política, e se monta a saída que o
fatiador (`dias/montar_bloco.py`) valida:

  * `fontes`   — teoria (as páginas do tema, sem questões) e fixação (resumo e mapa mental do mesmo tema), no formato do
                 manifesto, com "cobre" dizendo quais partes cada fonte ensina;
  * `questoes` — questões comentadas, lista, questionário e gabarito das aulas escolhidas, agrupados à parte (decisão 7:
                 não são segmentos; viram a consulta "Questões deste assunto");
  * `lacunas`  — partes sem nenhum tema que sirva.

Políticas (decisão do usuário, 2026-10-23): "completo" (padrão) leva todo candidato que ensina ou ensina em parte; "compacto"
leva, por parte, o conjunto mais curto que a cobre (cobertura gulosa por custo em páginas), preferindo quem ensina.
Nenhuma página aparece duas vezes (o validador do fatiador recusa).
"""
import re

MINUTOS_TEORIA = 4
MINUTOS_FIXACAO = 3
SERVEM = ("ensina", "parcial")
TIPOS_FIXACAO = ("resumo", "mapa_mental")
TIPOS_QUESTOES = ("questoes_comentadas", "lista_questoes", "questionario")
GABARITO = "gabarito"


def paginas_de(faixas):
    """[[3, 9], [12, 12]] -> {3..9, 12}."""
    saida = set()
    for f in faixas or []:
        a, b = (f[0], f[-1]) if isinstance(f, (list, tuple)) else (f, f)
        saida |= set(range(int(a), int(b) + 1))
    return saida


def texto_das_paginas(paginas):
    """{3,4,5,9} -> "3-5,9" (o formato do manifesto)."""
    ordem, saida = sorted(paginas), []
    i = 0
    while i < len(ordem):
        j = i
        while j + 1 < len(ordem) and ordem[j + 1] == ordem[j] + 1:
            j += 1
        saida.append(str(ordem[i]) if i == j else f"{ordem[i]}-{ordem[j]}")
        i = j + 1
    return ",".join(saida)


def rotulos_unicos(nomes):
    """O manifesto exige subitens com nome único: a repetição ganha ' (2)', ' (3)'."""
    vistos, saida = {}, []
    for n in nomes:
        vistos[n] = vistos.get(n, 0) + 1
        saida.append(n if vistos[n] == 1 else f"{n} ({vistos[n]})")
    return saida


def aula_curta(caminho):
    partes = caminho.replace("\\", "/").split("/")
    return " / ".join(p[:40] for p in partes[-2:]) if len(partes) > 1 else caminho


def tema_da_ficha(ficha, nome):
    return next((t for t in (ficha or {}).get("temas", []) if t.get("tema") == nome), None)


def faixa_da_secao(s):
    """As páginas de uma seção da ficha; seção sem posição conhecida (não confirmada) não tem página para usar."""
    if s.get("inicio") is None or s.get("fim") is None:
        return set()
    return set(range(int(s["inicio"]), int(s["fim"]) + 1))


def cabe_no_pdf(ficha, paginas):
    """Falso se a ficha diz quantas páginas o PDF tem e alguma página passa disso (leitura errada do catálogo)."""
    total = (ficha or {}).get("paginas")
    return not total or not paginas or max(paginas) <= total


def secoes_do_tema(ficha, nome, tipos):
    saida = set()
    for s in (ficha or {}).get("secoes", []):
        if s.get("tema") == nome and s.get("tipo") in tipos:
            faixa = faixa_da_secao(s)
            if cabe_no_pdf(ficha, faixa):
                saida |= faixa
    return saida


def candidatas(partes, ficha_de, avisos=None):
    """{(caminho, tema): {"paginas": {...}, "partes": {indices}, "ensina": {indices}}} só dos que servem e têm página.
    Tema com página além do fim do PDF não é usado e vira aviso (o catálogo leu errado: não se adivinha o recorte)."""
    fontes = {}
    for i, p in enumerate(partes):
        for c in p.get("candidatos") or []:
            if c.get("veredito") not in SERVEM:
                continue
            ficha = ficha_de(c["caminho"])
            tema = tema_da_ficha(ficha, c["tema"])
            paginas = paginas_de((tema or {}).get("paginas"))
            if not paginas:
                continue
            if not cabe_no_pdf(ficha, paginas):
                if avisos is not None and (c["caminho"], c["tema"]) not in [(a["arquivo"], a["tema"]) for a in avisos]:
                    avisos.append({"arquivo": c["caminho"], "tema": c["tema"], "motivo": f"páginas {min(paginas)}-{max(paginas)}, "
                                   f"mas o PDF tem {(ficha or {}).get('paginas')}"})
                continue
            f = fontes.setdefault((c["caminho"], c["tema"]), {"paginas": paginas, "partes": set(), "ensina": set()})
            f["partes"].add(i)
            if c["veredito"] == "ensina":
                f["ensina"].add(i)
    return fontes


def escolher_compacto(partes, fontes):
    """Cobertura gulosa: a cada passo, a fonte que cobre mais partes ainda sem cobertura por página (quem ensina primeiro);
    a parte que nenhuma fonte cobre fica de fora (lacuna)."""
    faltam = {i for i in range(len(partes)) if any(i in f["partes"] for f in fontes.values())}
    escolhidas = []
    for fase in ("ensina", "partes"):  # primeiro só com quem ensina; o que sobrar, também com quem ensina em parte
        while True:
            melhor, nota = None, 0
            for k, f in fontes.items():
                novas = len(faltam & f[fase])
                if novas and novas / len(f["paginas"]) > nota:
                    melhor, nota = k, novas / len(f["paginas"])
            if melhor is None:
                break
            escolhidas.append(melhor)
            faltam -= fontes[melhor]["partes"]
    return escolhidas


def selecionar(partes, ficha_de, modo="completo"):
    """`partes`: [{"nome", "candidatos": [{"caminho", "tema", "veredito"}]}] na ordem do edital. `ficha_de(caminho)`: a ficha.
    Devolve {"subitens", "fontes", "questoes", "lacunas", "estimativa_min", "avisos"}."""
    if modo not in ("completo", "compacto"):
        raise ValueError(f"modo desconhecido: {modo!r}")
    subitens = rotulos_unicos([p["nome"] for p in partes])
    avisos = []
    fontes = candidatas(partes, ficha_de, avisos)
    chaves = escolher_compacto(partes, fontes) if modo == "compacto" else list(fontes)
    # ordem: a primeira parte que a fonte cobre, quem ensina antes de quem ensina em parte, depois o caminho
    chaves.sort(key=lambda k: (min(fontes[k]["partes"]), 0 if fontes[k]["ensina"] else 1, k))
    usadas = {}      # arquivo -> páginas já tomadas por alguma fonte (teoria ou fixação)
    donos = {}       # (arquivo, página) -> posição da fonte em `saida` que a tomou
    saida = []
    for k in chaves:
        caminho, tema = k
        livres = fontes[k]["paginas"] - usadas.setdefault(caminho, set())
        cobre = {subitens[i] for i in fontes[k]["partes"]}
        for pg in fontes[k]["paginas"] & usadas[caminho]:  # página já de outra fonte: aquela fonte passa a cobrir estas partes também
            saida[donos[(caminho, pg)]]["cobre"] |= cobre
        if livres:
            usadas[caminho] |= livres
            saida.append({"arquivo": caminho, "tema": tema, "paginas": livres, "cobre": set(cobre), "tipo": "teoria",
                          "rotulo": f"{aula_curta(caminho)}: {tema}"})
            for pg in livres:
                donos[(caminho, pg)] = len(saida) - 1
            ficha = ficha_de(caminho)
            fix = secoes_do_tema(ficha, tema, TIPOS_FIXACAO) - usadas[caminho]
            if fix:
                usadas[caminho] |= fix
                saida.append({"arquivo": caminho, "tema": tema, "paginas": fix, "cobre": set(cobre), "tipo": "fixacao",
                              "rotulo": f"{aula_curta(caminho)}: resumo de {tema}"})
                for pg in fix:
                    donos[(caminho, pg)] = len(saida) - 1
    # questões: das mesmas aulas e temas escolhidos; o gabarito da aula vai junto se houver questões nela
    questoes, tomadas = [], {}
    for k in chaves:
        caminho, tema = k
        ficha = ficha_de(caminho)
        q = secoes_do_tema(ficha, tema, TIPOS_QUESTOES) - tomadas.setdefault(caminho, set())
        if q:
            tomadas[caminho] |= q
            questoes.append({"arquivo": caminho, "paginas": q, "rotulo": f"{aula_curta(caminho)}: questões de {tema}"})
    for caminho in list(tomadas):
        gab = set()
        for s in (ficha_de(caminho) or {}).get("secoes", []):
            if s.get("tipo") == GABARITO and cabe_no_pdf(ficha_de(caminho), faixa_da_secao(s)):
                gab |= faixa_da_secao(s)
        gab -= tomadas[caminho]
        if gab and any(q["arquivo"] == caminho for q in questoes):
            questoes.append({"arquivo": caminho, "paginas": gab, "rotulo": f"{aula_curta(caminho)}: gabarito"})
    cobertas = {s for f in saida for s in f["cobre"]}
    lacunas = [{"subitem": s, "motivo": "nenhum tema do acervo ensina esta parte"} for s in subitens if s not in cobertas]
    for f in saida:
        f["cobre"] = [s for s in subitens if s in f["cobre"]]
        f["paginas_lista"] = sorted(f["paginas"])
        f["paginas"] = texto_das_paginas(f["paginas"])
    for q in questoes:
        q["paginas"] = texto_das_paginas(q["paginas"])
    minutos = sum(len(f["paginas_lista"]) * (MINUTOS_FIXACAO if f["tipo"] == "fixacao" else MINUTOS_TEORIA) for f in saida)
    for f in saida:
        del f["paginas_lista"]
    return {"subitens": subitens, "fontes": saida, "questoes": questoes, "lacunas": lacunas, "estimativa_min": minutos,
            "avisos": avisos}
