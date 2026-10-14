#!/usr/bin/env python3
"""
montar_bloco.py — Fatia o material de um assunto em pedaços de leitura de tempo
aproximadamente igual ("bloco de conteúdo" no vocabulário do SGE), sem data de calendário.
Ver docs/requisitos-alinhamento-fatiamento-pdf-bloco.md pro motivo dessa divisão.

Uso:
    python montar_bloco.py manifesto_assunto.json --saida-dir dias/
    python montar_bloco.py manifesto_assunto.json --saida-dir dias/ --validar   (só confere)
    python montar_bloco.py manifesto_assunto.json --saida-dir dias/ --refatiar  (ver "Refatiar")

Formato do manifesto (JSON):
{
    "assunto_uuid": "2f6e...",
    "edital": "EDITAL-2027",
    "titulo": "Entidades, chaves, integridade, normalização",
    "minutos_por_pagina": 4,          (opcional, padrão 4)
    "minutos_por_bloco": 60,          (opcional, padrão 60 — valor combinado com o SGE)
    "subitens": ["Entidades", "chaves", "integridade", "normalização", "valores nulos"],
    "lacunas": [
        {"subitem": "valores nulos", "motivo": "não achado no acervo (triagem bd-sql, gap confirmado)"}
    ],
    "fontes": [
        {"arquivo": "../apostilas/.../aula-04.pdf", "paginas": "3-33",
         "rotulo": "Aula 04 — modelo relacional", "cobre": ["Entidades", "chaves", "integridade"]},
        {"arquivo": "../apostilas/.../aula-04.pdf", "paginas": "70-88",
         "rotulo": "Aula 04 — questões comentadas", "cobre": ["Entidades", "chaves"],
         "tipo": "fixacao", "minutos_por_pagina": 3}
    ],
    "descartes": [
        {"arquivo": "../apostilas/.../aula-04.pdf", "paginas": "34-69",
         "motivo": "repete a aula 02 (triagem bd-sql, decisões de descarte)"}
    ]
}

Regras do manifesto:
- "paginas" é a POSIÇÃO da página no PDF (o contador do leitor de PDF, a mesma numeração
  de indice/buscar_indice.py), nunca o número impresso na apostila. Formato "3-33",
  "5", "3-10,15,20-22".
- "subitens" é obrigatório: as partes do assunto fino, como estão no mapa de assuntos.
  Todo subitem precisa ser coberto por alguma fonte ("cobre") ou declarado em "lacunas"
  com motivo. Esse é o controle contra perder conteúdo na triagem.
- "tipo": "teoria" (padrão) ou "fixacao" (questões comentadas, resumo, lista de exercícios).
  Fixação nunca é misturada com teoria no mesmo bloco: fica num bloco próprio, na posição
  em que aparece no manifesto (a convenção é logo depois da teoria correspondente).
- "minutos_por_pagina" por fonte sobrepõe o do manifesto (lei seca, código e questões
  não levam o mesmo tempo que teoria corrida).
- "descartes" é opcional e informativo: o que a triagem decidiu deixar de fora, com motivo.
  Aparece no relatório de cobertura.

Validação (tudo é conferido ANTES de gerar qualquer arquivo; qualquer erro → nada é
gerado, sai com código 1 e a lista completa de erros):
arquivo inexistente, faixa inválida ou invertida, página fora do PDF, página repetida
(dentro de uma fonte, entre fontes ou entre fonte e descarte), subitem sem cobertura e sem
lacuna, "cobre" citando subitem que não está em "subitens", lacuna sem motivo.

Como corta (determinístico):
- Fronteiras naturais: troca de fonte e início de seção (marcadores/bookmarks do PDF).
  Troca de tipo (teoria ↔ fixação) é corte obrigatório.
- Para cada trecho entre cortes obrigatórios, o número de blocos é o maior entre
  ceil(tempo / máximo) e round(tempo / alvo), e o tempo é dividido por igual entre eles.
  Cada corte cai na fronteira natural mais perto do alvo, dentro de ±25% dele (e nunca
  acima de 1,25 × minutos_por_bloco). Sem fronteira natural na faixa, corta no alvo e o
  relatório marca "corte no meio de seção".

Saída, em <saida-dir>:
    blocos/<assunto-slug>/segmento-01.pdf, ...  — capa de rastreabilidade em cada um
    <assunto-slug>_pedacos.json — lista ordenada dos segmentos (ordem, arquivo local,
        faixas reais por arquivo, tempo estimado, tipo, subitens cobertos,
        chave_externa_segmento) pra `integracao/canonizar_assuntos.py --adicionar-pedacos`.
        pagina_inicial/pagina_final só são preenchidos quando o segmento é UMA faixa
        contínua de UM arquivo — senão ficam nulos, pra nunca sugerir que um intervalo
        inteiro foi incluído quando não foi. As faixas reais ficam em "faixas" e na capa.
    <assunto-slug>_cobertura.md — relatório pra conferir ANTES de subir pro Drive:
        subitem → páginas (ou lacuna), fontes com o começo do texto da primeira página
        (pega erro de numeração), descartes, segmentos e alertas.

Identidade de segmento (docs/requisitos-alinhamento-fatiamento-pdf-bloco.md §8):
cada segmento ganha uma `chave_externa_segmento` (UUID) na primeira vez. Reexecução que
produz o mesmo conjunto de páginas reaproveita a chave.

Refatiar: se já existe registro desse assunto (mesmo assunto_uuid) e o corte mudou
(segmentos diferentes, ou título/slug diferente), o script recusa sem --refatiar. Motivo:
se o assunto já foi exportado, o SGE nunca apaga segmento — os antigos continuariam na
lista ao lado dos novos. Com --refatiar, os PDFs antigos que sobrarem na pasta do assunto
são removidos.
"""

import argparse
import hashlib
import json
import math
import re
import sys
import unicodedata
import uuid
from pathlib import Path

from pypdf import PdfReader, PdfWriter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from montar_dia import gerar_capa  # noqa: E402

MINUTOS_POR_PAGINA_PADRAO = 4
MINUTOS_POR_BLOCO_PADRAO = 60
TOLERANCIA = 0.25
TIPOS = {"teoria", "fixacao"}


class ManifestoInvalido(Exception):
    def __init__(self, erros):
        super().__init__("\n".join(erros))
        self.erros = erros


def slugificar(texto):
    """'Governança e Qualidade de Dados' -> 'governanca-e-qualidade-de-dados'."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", sem_acento).strip("-").lower()
    return slug or "assunto"


def normalizar(texto):
    sem_acento = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", sem_acento).strip().lower()


def parse_paginas_estrito(spec):
    """'3-10,15' -> [3..10, 15]. Lança ValueError em qualquer coisa ambígua — nunca
    devolve lista vazia em silêncio (o parse antigo transformava '30-20' em nada)."""
    if not isinstance(spec, str) or not spec.strip():
        raise ValueError("faixa de páginas vazia")
    paginas = []
    for parte in spec.split(","):
        parte = parte.strip()
        m = re.fullmatch(r"(\d+)(?:\s*-\s*(\d+))?", parte)
        if not m:
            raise ValueError(f"faixa inválida: {parte!r}")
        ini = int(m.group(1))
        fim = int(m.group(2)) if m.group(2) else ini
        if ini < 1:
            raise ValueError(f"página tem que ser ≥ 1: {parte!r}")
        if fim < ini:
            raise ValueError(f"faixa invertida: {parte!r} (o fim vem antes do começo)")
        paginas.extend(range(ini, fim + 1))
    return paginas


def compactar_faixas(numeros):
    """[1,2,3,7,9,10] -> '1-3,7,9-10' (na ordem dada; quebra quando não é consecutivo)."""
    partes, ini, ant = [], None, None
    for n in numeros:
        if ini is None:
            ini = ant = n
        elif n == ant + 1:
            ant = n
        else:
            partes.append(f"{ini}-{ant}" if ant != ini else f"{ini}")
            ini = ant = n
    if ini is not None:
        partes.append(f"{ini}-{ant}" if ant != ini else f"{ini}")
    return ",".join(partes)


def resolver_arquivo(arquivo, manifesto_dir):
    caminho = Path(arquivo)
    return caminho if caminho.is_absolute() else (manifesto_dir / caminho).resolve()


def inicios_de_secao(reader):
    """Páginas (1-indexadas) onde começa alguma seção, pelos marcadores do PDF."""
    inicios = set()

    def percorrer(itens):
        for item in itens:
            if isinstance(item, list):
                percorrer(item)
            else:
                try:
                    inicios.add(reader.get_destination_page_number(item) + 1)
                except Exception:
                    pass
    try:
        percorrer(reader.outline)
    except Exception:
        pass
    return inicios


def primeira_linha(reader, pagina):
    try:
        texto = reader.pages[pagina - 1].extract_text() or ""
    except Exception:
        return ""
    for linha in texto.splitlines():
        linha = linha.strip()
        if linha:
            return linha[:90]
    return ""


# ----------------------------------------------------------------------------
# Validação
# ----------------------------------------------------------------------------

def validar_manifesto(manifesto, manifesto_dir):
    """Confere tudo e devolve (fontes_resolvidas, descartes_resolvidos, subitens, lacunas).
    Junta todos os erros antes de lançar, pra uma rodada de correção resolver tudo."""
    erros = []
    leitores = {}

    def leitor(caminho):
        if caminho not in leitores:
            leitores[caminho] = PdfReader(str(caminho))
        return leitores[caminho]

    if not str(manifesto.get("titulo", "")).strip():
        erros.append("manifesto sem 'titulo'")

    subitens = manifesto.get("subitens")
    if not isinstance(subitens, list) or not subitens or not all(str(s).strip() for s in subitens):
        erros.append("'subitens' é obrigatório: liste as partes do assunto, como estão no mapa de assuntos")
        subitens = []
    chave_subitem = {}
    for s in subitens:
        k = normalizar(s)
        if k in chave_subitem:
            erros.append(f"subitem repetido: {s!r}")
        chave_subitem[k] = s

    mpp_padrao = manifesto.get("minutos_por_pagina", MINUTOS_POR_PAGINA_PADRAO)
    if not isinstance(mpp_padrao, (int, float)) or mpp_padrao <= 0:
        erros.append("'minutos_por_pagina' tem que ser número > 0")
        mpp_padrao = MINUTOS_POR_PAGINA_PADRAO
    mpb = manifesto.get("minutos_por_bloco", MINUTOS_POR_BLOCO_PADRAO)
    if not isinstance(mpb, (int, float)) or mpb <= 0:
        erros.append("'minutos_por_bloco' tem que ser número > 0")

    usadas = {}  # (caminho, pagina) -> descrição de onde foi usada
    fontes_ok = []
    cobertos = {}  # chave subitem -> [descrição de fonte]

    def registrar_paginas(caminho, paginas, onde):
        for p in paginas:
            anterior = usadas.get((caminho, p))
            if anterior:
                erros.append(f"página {p} de {caminho.name} aparece duas vezes: {anterior} e {onde}")
            else:
                usadas[(caminho, p)] = onde

    def conferir_faixa(item, onde):
        caminho = resolver_arquivo(item.get("arquivo", ""), manifesto_dir)
        if not item.get("arquivo") or not caminho.exists():
            erros.append(f"{onde}: arquivo não encontrado: {item.get('arquivo')!r}")
            return None, None
        try:
            paginas = parse_paginas_estrito(item.get("paginas"))
        except ValueError as e:
            erros.append(f"{onde}: {e}")
            return caminho, None
        total = len(leitor(caminho).pages)
        fora = [p for p in paginas if p > total]
        if fora:
            erros.append(f"{onde}: página(s) {compactar_faixas(fora)} não existem em {caminho.name} ({total} páginas)")
            return caminho, None
        return caminho, paginas

    fontes = manifesto.get("fontes")
    if not isinstance(fontes, list):
        erros.append("'fontes' tem que ser uma lista (pode ser vazia se o assunto inteiro for lacuna)")
        fontes = []
    for i, fonte in enumerate(fontes, 1):
        onde = f"fonte {i} ({fonte.get('rotulo') or fonte.get('arquivo')})"
        tipo = fonte.get("tipo", "teoria")
        if tipo not in TIPOS:
            erros.append(f"{onde}: tipo {tipo!r} inválido (use 'teoria' ou 'fixacao')")
        mpp = fonte.get("minutos_por_pagina", mpp_padrao)
        if not isinstance(mpp, (int, float)) or mpp <= 0:
            erros.append(f"{onde}: 'minutos_por_pagina' tem que ser número > 0")
            mpp = mpp_padrao
        cobre = fonte.get("cobre")
        if not isinstance(cobre, list) or not cobre:
            erros.append(f"{onde}: 'cobre' é obrigatório (quais subitens esta fonte ensina)")
            cobre = []
        for s in cobre:
            k = normalizar(s)
            if k not in chave_subitem:
                erros.append(f"{onde}: cobre {s!r}, que não está em 'subitens'")
            else:
                cobertos.setdefault(k, []).append(onde)
        caminho, paginas = conferir_faixa(fonte, onde)
        if paginas is None:
            continue
        registrar_paginas(caminho, paginas, onde)
        fontes_ok.append({
            "caminho": caminho, "paginas": paginas, "rotulo": fonte.get("rotulo", ""),
            "tipo": tipo, "minutos_por_pagina": mpp,
            "cobre": [chave_subitem.get(normalizar(s), s) for s in cobre],
        })

    descartes_ok = []
    for i, desc in enumerate(manifesto.get("descartes", []) or [], 1):
        onde = f"descarte {i} ({desc.get('arquivo')})"
        if not str(desc.get("motivo", "")).strip():
            erros.append(f"{onde}: descarte sem 'motivo'")
        caminho, paginas = conferir_faixa(desc, onde)
        if paginas is None:
            continue
        registrar_paginas(caminho, paginas, onde)
        descartes_ok.append({"caminho": caminho, "paginas": paginas, "motivo": desc.get("motivo", "")})

    lacunas_ok = []
    for lac in manifesto.get("lacunas", []) or []:
        s = lac.get("subitem") if isinstance(lac, dict) else None
        k = normalizar(s or "")
        if k not in chave_subitem:
            erros.append(f"lacuna {s!r} não está em 'subitens'")
            continue
        if not str(lac.get("motivo", "")).strip():
            erros.append(f"lacuna {s!r} sem 'motivo'")
        if k in cobertos:
            erros.append(f"subitem {chave_subitem[k]!r} está como lacuna mas é coberto por {', '.join(cobertos[k])}")
        lacunas_ok.append({"subitem": chave_subitem[k], "motivo": lac.get("motivo", "")})

    lacunas_chaves = {normalizar(l["subitem"]) for l in lacunas_ok}
    for k, s in chave_subitem.items():
        if k not in cobertos and k not in lacunas_chaves:
            erros.append(f"subitem {s!r} sem nenhuma página e sem lacuna declarada — "
                         f"ache o material ou declare a lacuna com motivo")

    if erros:
        raise ManifestoInvalido(erros)
    return fontes_ok, descartes_ok, subitens, lacunas_ok, leitores


# ----------------------------------------------------------------------------
# Corte
# ----------------------------------------------------------------------------

def achatar(fontes, leitores):
    """Lista única de páginas na ordem de leitura, cada uma com tempo, tipo e se começa
    uma fronteira natural (troca de fonte ou início de seção do PDF)."""
    paginas = []
    secoes = {}
    for idx, fonte in enumerate(fontes):
        caminho = fonte["caminho"]
        if caminho not in secoes:
            secoes[caminho] = inicios_de_secao(leitores[caminho])
        for j, p in enumerate(fonte["paginas"]):
            paginas.append({
                "arquivo": caminho, "pagina_original": p, "rotulo": fonte["rotulo"],
                "tipo": fonte["tipo"], "minutos": fonte["minutos_por_pagina"], "fonte": idx,
                "fronteira": j == 0 or p in secoes[caminho],
            })
    return paginas


def dividir_em_blocos(paginas, minutos_por_bloco):
    """Devolve lista de (inicio, fim_exclusivo, corte_fora_de_fronteira)."""
    maximo = minutos_por_bloco * (1 + TOLERANCIA)
    blocos = []
    # trechos entre cortes obrigatórios (troca de tipo)
    trechos, ini = [], 0
    for i in range(1, len(paginas) + 1):
        if i == len(paginas) or paginas[i]["tipo"] != paginas[i - 1]["tipo"]:
            trechos.append((ini, i))
            ini = i

    for t_ini, t_fim in trechos:
        tempos = [p["minutos"] for p in paginas[t_ini:t_fim]]
        total = sum(tempos)
        n = max(1, math.ceil(total / maximo - 1e-9), round(total / minutos_por_bloco))
        n = min(n, t_fim - t_ini)  # nunca mais blocos que páginas
        inicio = t_ini
        for restantes in range(n, 0, -1):
            if restantes == 1 or inicio >= t_fim:
                if inicio < t_fim:
                    blocos.append((inicio, t_fim, False))
                break
            tempo_restante = sum(p["minutos"] for p in paginas[inicio:t_fim])
            alvo = tempo_restante / restantes
            lo, hi = alvo * (1 - TOLERANCIA), min(alvo * (1 + TOLERANCIA), maximo)
            # Sem fronteira natural na faixa, corta onde o acumulado chega ao alvo (ou ao
            # máximo, se o alvo passar dele depois de blocos anteriores curtos).
            limite_fallback = min(alvo, hi)
            acumulado, melhor, primeiro_no_alvo = 0, None, None
            for e in range(inicio + 1, t_fim):
                acumulado += paginas[e - 1]["minutos"]
                if primeiro_no_alvo is None and acumulado >= limite_fallback:
                    primeiro_no_alvo = e
                if acumulado > hi:
                    break
                if acumulado >= lo and paginas[e]["fronteira"]:
                    dist = abs(acumulado - alvo)
                    if melhor is None or dist < melhor[0]:
                        melhor = (dist, e)
            if melhor is not None:
                fim, fora = melhor[1], False
            else:
                fim, fora = (primeiro_no_alvo or t_fim - 1), True
            fim = max(fim, inicio + 1)
            blocos.append((inicio, fim, fora))
            inicio = fim
    return blocos


def faixas_do_bloco(bloco):
    """Agrupa as páginas do bloco por arquivo, na ordem, em faixas compactas."""
    faixas = []
    for item in bloco:
        nome = item["arquivo"].name
        if faixas and faixas[-1]["_arquivo"] == item["arquivo"]:
            faixas[-1]["_paginas"].append(item["pagina_original"])
        else:
            faixas.append({"_arquivo": item["arquivo"], "arquivo": nome, "_paginas": [item["pagina_original"]]})
    for f in faixas:
        f["paginas"] = compactar_faixas(f.pop("_paginas"))
        f.pop("_arquivo")
    return faixas


def fingerprint_bloco(bloco):
    """Identidade de conteúdo: hash do conjunto ordenado (arquivo, página) do segmento."""
    chave = "|".join(f"{item['arquivo'].name}:{item['pagina_original']}" for item in bloco)
    return hashlib.sha1(chave.encode("utf-8")).hexdigest()


def montar_pedaco(paginas_bloco, titulo_bloco, saida_pdf, leitores):
    writer = PdfWriter()
    mapa_rastreio = []
    for n, item in enumerate(paginas_bloco, start=2):  # capa ocupa a página 1
        writer.add_page(leitores[item["arquivo"]].pages[item["pagina_original"] - 1])
        mapa_rastreio.append({
            "pagina_mesclada": n, "arquivo": item["arquivo"].name,
            "pagina_original": item["pagina_original"], "rotulo": item["rotulo"],
        })
    saida_pdf.parent.mkdir(parents=True, exist_ok=True)
    capa_tmp = saida_pdf.with_suffix(".capa.tmp.pdf")
    gerar_capa(capa_tmp, titulo_bloco, mapa_rastreio)
    final = PdfWriter()
    for pg in PdfReader(str(capa_tmp)).pages:
        final.add_page(pg)
    for pg in writer.pages:
        final.add_page(pg)
    with open(saida_pdf, "wb") as f:
        final.write(f)
    capa_tmp.unlink(missing_ok=True)


# ----------------------------------------------------------------------------
# Registro anterior e refatiar
# ----------------------------------------------------------------------------

def achar_registro_anterior(saida_dir, assunto_uuid, slug):
    """Registro anterior do mesmo assunto: pelo assunto_uuid (sobrevive a troca de título),
    senão pelo slug."""
    candidatos = sorted(Path(saida_dir).glob("*_pedacos.json"))
    for caminho in candidatos:
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if assunto_uuid and dados.get("assunto_uuid") == assunto_uuid:
            return caminho, dados
    caminho = Path(saida_dir) / f"{slug}_pedacos.json"
    if caminho.exists():
        return caminho, json.loads(caminho.read_text(encoding="utf-8"))
    return None, None


# ----------------------------------------------------------------------------
# Relatório
# ----------------------------------------------------------------------------

def escrever_relatorio(caminho, titulo, subitens, lacunas, fontes, descartes, segmentos, leitores):
    lin = [f"# Cobertura — {titulo}", "",
           "Conferir antes de subir os blocos pro Drive. Gerado por `dias/montar_bloco.py`.", ""]

    lin += ["## Subitens", "", "| Subitem | Onde está |", "|---|---|"]
    lacuna_de = {normalizar(l["subitem"]): l["motivo"] for l in lacunas}
    for s in subitens:
        k = normalizar(s)
        if k in lacuna_de:
            lin.append(f"| {s} | ❌ lacuna — {lacuna_de[k]} |")
        else:
            onde = [f"{f['caminho'].name} p. {compactar_faixas(f['paginas'])}"
                    for f in fontes if k in {normalizar(c) for c in f["cobre"]}]
            segs = [str(sg["ordem"]) for sg in segmentos if s in sg["subitens"]]
            lin.append(f"| {s} | {'; '.join(onde)} (segmento {', '.join(segs)}) |")

    lin += ["", "## Fontes", "",
            "A coluna \"começa com\" é a primeira linha de texto da primeira página da faixa — "
            "se não for o que a triagem esperava, a numeração de páginas está deslocada.", "",
            "| Arquivo | Páginas | Do PDF | Tipo | Min/pág | Começa com |", "|---|---|---|---|---|---|"]
    for f in fontes:
        total = len(leitores[f["caminho"]].pages)
        pct = round(100 * len(f["paginas"]) / total)
        inicio = primeira_linha(leitores[f["caminho"]], f["paginas"][0]).replace("|", "/")
        lin.append(f"| {f['caminho'].name} | {compactar_faixas(f['paginas'])} | {len(f['paginas'])} de {total} ({pct}%) "
                   f"| {f['tipo']} | {f['minutos_por_pagina']} | {inicio or '(sem texto extraível)'} |")

    if descartes:
        lin += ["", "## Descartado pela triagem", "", "| Arquivo | Páginas | Motivo |", "|---|---|---|"]
        for d in descartes:
            lin.append(f"| {d['caminho'].name} | {compactar_faixas(d['paginas'])} | {d['motivo']} |")

    lin += ["", "## Segmentos", "", "| # | Tipo | Tempo | Faixas | Subitens | Alerta |", "|---|---|---|---|---|---|"]
    for sg in segmentos:
        faixas = "; ".join(f"{fx['arquivo']} p. {fx['paginas']}" for fx in sg["faixas"])
        lin.append(f"| {sg['ordem']} | {sg['tipo']} | ~{sg['tempo_estimado_min']} min | {faixas} "
                   f"| {', '.join(sg['subitens'])} | {'; '.join(sg['alertas']) or '—'} |")
    if not segmentos:
        lin.append("| — | — | — | nenhum segmento: todos os subitens são lacuna | — | — |")

    caminho.write_text("\n".join(lin) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------
# Principal
# ----------------------------------------------------------------------------

def montar_bloco(manifesto_path, saida_dir, refatiar=False, so_validar=False):
    manifesto_path = Path(manifesto_path)
    manifesto = json.loads(manifesto_path.read_text(encoding="utf-8"))
    manifesto_dir = manifesto_path.resolve().parent

    fontes, descartes, subitens, lacunas, leitores = validar_manifesto(manifesto, manifesto_dir)

    titulo = manifesto["titulo"]
    minutos_por_bloco = manifesto.get("minutos_por_bloco", MINUTOS_POR_BLOCO_PADRAO)
    paginas = achatar(fontes, leitores)
    cortes = dividir_em_blocos(paginas, minutos_por_bloco)

    slug = slugificar(titulo)
    saida_dir = Path(saida_dir)
    assunto_dir_rel = Path("blocos") / slug

    # Monta a descrição dos segmentos antes de gravar qualquer coisa.
    segmentos = []
    for ordem, (ini, fim, fora) in enumerate(cortes, 1):
        bloco = paginas[ini:fim]
        tempo = round(sum(p["minutos"] for p in bloco))
        faixas = faixas_do_bloco(bloco)
        continua = len(faixas) == 1 and "," not in faixas[0]["paginas"]
        cobertos = []
        for idx in sorted({p["fonte"] for p in bloco}):
            for s in fontes[idx]["cobre"]:
                if s not in cobertos:
                    cobertos.append(s)
        alertas = []
        if fora:
            alertas.append("corte no meio de seção")
        if tempo < minutos_por_bloco * 0.25:
            # Assunto pequeno ou trecho de fixação curto: não é erro, só avisa que cabe
            # junto com outra coisa no turno.
            alertas.append("bloco muito curto")
        segmentos.append({
            "ordem": ordem, "_bloco": bloco, "tipo": bloco[0]["tipo"],
            "arquivo": str((assunto_dir_rel / f"segmento-{ordem:02d}.pdf").as_posix()),
            "pagina_inicial": bloco[0]["pagina_original"] if continua else None,
            "pagina_final": bloco[-1]["pagina_original"] if continua else None,
            "faixas": faixas, "tempo_estimado_min": tempo, "subitens": cobertos,
            "alertas": alertas, "fingerprint": fingerprint_bloco(bloco),
        })

    registro_anterior_path, anterior = achar_registro_anterior(saida_dir, manifesto.get("assunto_uuid"), slug)
    chaves_anteriores = {}
    if anterior:
        chaves_anteriores = {p["fingerprint"]: p["chave_externa_segmento"]
                             for p in anterior.get("pedacos", [])
                             if p.get("fingerprint") and p.get("chave_externa_segmento")}
        mudou_corte = set(chaves_anteriores) != {s["fingerprint"] for s in segmentos}
        mudou_slug = registro_anterior_path.name != f"{slug}_pedacos.json"
        if (mudou_corte or mudou_slug) and not refatiar:
            motivos = []
            if mudou_corte:
                motivos.append(f"o corte mudou ({len(chaves_anteriores)} segmento(s) antes, {len(segmentos)} agora)")
            if mudou_slug:
                motivos.append(f"o título mudou (registro anterior: {registro_anterior_path.name})")
            raise ManifestoInvalido([
                "este assunto já foi fatiado antes e " + " e ".join(motivos) + ".",
                "Se ele já foi exportado pro SGE, os segmentos antigos continuam lá (o SGE nunca apaga) "
                "ao lado dos novos. Rode de novo com --refatiar se é isso mesmo que você quer.",
            ])

    if so_validar:
        return None, segmentos

    reaproveitadas = novas = 0
    for sg in segmentos:
        chave = chaves_anteriores.get(sg["fingerprint"])
        if chave:
            reaproveitadas += 1
        else:
            chave, novas = str(uuid.uuid4()), novas + 1
        sg["chave_externa_segmento"] = chave
        titulo_bloco = f"{titulo} — segmento {sg['ordem']}/{len(segmentos)}"
        if sg["tipo"] == "fixacao":
            titulo_bloco += " (fixação)"
        montar_pedaco(sg["_bloco"], titulo_bloco, saida_dir / sg["arquivo"], leitores)
        print(f"Gerado: {saida_dir / sg['arquivo']}  (~{sg['tempo_estimado_min']} min, {sg['tipo']}"
              f"{', ' + '; '.join(sg['alertas']) if sg['alertas'] else ''})")

    # Refatiar: remove PDFs antigos que sobraram e o registro com slug antigo.
    if refatiar and anterior:
        validos = {saida_dir / sg["arquivo"] for sg in segmentos}
        pasta = saida_dir / assunto_dir_rel
        for velho in pasta.glob("segmento-*.pdf"):
            if velho not in validos:
                velho.unlink()
        if registro_anterior_path.name != f"{slug}_pedacos.json":
            registro_anterior_path.unlink(missing_ok=True)
            pasta_antiga = saida_dir / "blocos" / registro_anterior_path.name.removesuffix("_pedacos.json")
            for velho in pasta_antiga.glob("segmento-*.pdf"):
                velho.unlink()

    saida_dir.mkdir(parents=True, exist_ok=True)
    registro_path = saida_dir / f"{slug}_pedacos.json"
    pedacos = [{k: v for k, v in sg.items() if k != "_bloco"} for sg in segmentos]
    registro_path.write_text(json.dumps({
        "assunto_uuid": manifesto.get("assunto_uuid"), "edital": manifesto.get("edital"),
        "titulo": titulo, "subitens": subitens, "lacunas": lacunas, "pedacos": pedacos,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    relatorio_path = saida_dir / f"{slug}_cobertura.md"
    escrever_relatorio(relatorio_path, titulo, subitens, lacunas, fontes, descartes, segmentos, leitores)

    if anterior:
        print(f"Identidade de segmentos: {reaproveitadas} reaproveitada(s), {novas} nova(s).")
    print(f"\n{len(segmentos)} segmento(s). Registro: {registro_path}")
    print(f"Relatório de cobertura (conferir antes de subir pro Drive): {relatorio_path}")
    if lacunas:
        print(f"Lacunas declaradas: {', '.join(l['subitem'] for l in lacunas)}")
    return registro_path, segmentos


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Fatia o material de um assunto em blocos de leitura, sem perder página.")
    ap.add_argument("manifesto", help="Caminho do manifesto JSON do assunto")
    ap.add_argument("--saida-dir", default="dias", help="Diretório de saída dos PDFs/registro (padrão: dias)")
    ap.add_argument("--refatiar", action="store_true",
                    help="Aceita mudar o corte de um assunto já fatiado (ver docstring)")
    ap.add_argument("--validar", action="store_true", help="Só confere o manifesto e mostra o corte, sem gerar nada")
    args = ap.parse_args()
    try:
        _, segmentos = montar_bloco(args.manifesto, args.saida_dir, args.refatiar, args.validar)
    except ManifestoInvalido as e:
        print("Nada foi gerado. Corrija o manifesto:", file=sys.stderr)
        for erro in e.erros:
            print(f"  - {erro}", file=sys.stderr)
        sys.exit(1)
    if args.validar:
        print("Manifesto válido. Corte previsto:")
        for sg in segmentos:
            faixas = "; ".join(f"{fx['arquivo']} p. {fx['paginas']}" for fx in sg["faixas"])
            print(f"  {sg['ordem']:>2}. ~{sg['tempo_estimado_min']} min {sg['tipo']}: {faixas}"
                  f"{'  [' + '; '.join(sg['alertas']) + ']' if sg['alertas'] else ''}")


if __name__ == "__main__":
    main()
