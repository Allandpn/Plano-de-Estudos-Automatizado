#!/usr/bin/env python3
"""
prova_questoes.py — Das linhas da prova às questões (Sprint 24 do SGE-Concursos, ADR-046).

A separação das questões é **determinística**, com validação — a IA não entra aqui. Uma prova
de 70 questões em texto são ~25 mil tokens que a IA teria de devolver reescritos, a cada prova,
para um resultado que regras simples dão de graça e que os testes conseguem provar. A IA fica
onde só ela serve: ler o gabarito, atribuir o assunto e julgar (D-67 do SGE).

Como as bancas numeram (amostra real de CEBRASPE, FGV, IDECAN e FCC):
  FGV        "6" sozinho na linha, depois o enunciado, depois "(A) ...(E)"
  IDECAN     "38. Assinale..." e "A) ...", em imagem
  FCC        "24. Considere..." e "(A) ...", em imagem, com rodapé e código de barras no meio
  CEBRASPE   "13 No trecho..." — itens certo/errado, sem alternativas, ligados a um texto-base

Quem guia é a **sequência**: procura a questão 1, depois a 2, e assim por diante. Isso derruba o
ruído que também começa com número (rodapé, numeração de linha do texto-base, itens de lista).
Em múltipla escolha uma largada só vale se a questão anterior já tem as alternativas (uma lista
numerada dentro do enunciado vem antes delas) e se há "A)" e "B)" logo adiante.

O que o OCR leu mal vira dúvida declarada, nunca texto julgado como se estivesse certo (D-85):
linhas de baixa confiança, e itens em algarismos romanos lidos como "1.", "11.", "TI.".
"""

import re
from dataclasses import dataclass, field

# Linhas de OCR abaixo desta confiança são ruído (código de barras, borda): saem antes de tudo.
CONFIANCA_RUIDO = 40.0
# Uma questão lida por OCR com muita linha de baixa confiança é duvidosa.
CONFIANCA_DUVIDOSA = 65.0
FRACAO_DUVIDOSA = 0.25
JANELA_ALTERNATIVAS = 80
MAX_PULO_DE_NUMERO = 3
MIN_ALTERNATIVAS = 4
MIN_ALTERNATIVAS_PARA_FECHAR = 2

R_ALT = re.compile(r"^\s*\(?([A-E])\)\s*(.*)$")
R_NUM_SOZINHO = re.compile(r"^\s*(\d{1,3})\s*$")
R_NUM_PONTO = re.compile(r"^\s*(\d{1,3})\s*[.)\-–]\s+(\S.*)$")
R_NUM_TEXTO = re.compile(r"^\s*(\d{1,3})\s+(\S.*)$")
R_TITULO_TEXTO = re.compile(r"^\s*Texto\s+(CB\d+A\d+(?:-[IVX]+)?)\s*$", re.IGNORECASE)
R_CODIGO_TEXTO = re.compile(r"\bCB\d+A\d+(?:-[IVX]+)?\b", re.IGNORECASE)
R_PREAMBULO_CE = re.compile(r"^\s*(Julgue|Com base|Considerando|Acerca|A respeito|Em rela[cç][aã]o)\b", re.IGNORECASE)
R_ROMANO_CERTO = re.compile(r"^(I{1,3}|IV|V|VI{0,3}|IX|X)$")
R_ITEM_DE_LISTA = re.compile(r"^\s*([IVXlLTi1|]{1,4})\s*[.)]\s+\S")
FIM_DE_FRASE = (".", "?", "!", ";", ":", ",")


@dataclass
class QuestaoBruta:
    numero: int
    enunciado: str | None
    alternativas: list          # [(letra, texto)]
    texto_base: str | None = None
    cabecalho: str | None = None
    lida_por_ocr: bool = False
    pagina_origem: int | None = None
    motivo: str | None = None   # None | "SEM_TEXTO" | "OCR_DUVIDOSO"


@dataclass
class Segmentacao:
    formato: str                # "MULTIPLA_ESCOLHA" | "CERTO_ERRADO"
    questoes: list
    capa: str
    avisos: list = field(default_factory=list)
    capa_ampla: str = ""        # as primeiras 400 linhas: banca e ano (o nome da banca está no cabeçalho das páginas)


# ---------------------------------------------------------------- limpeza

def _unidade(linha):
    return linha.imagem if linha.imagem is not None else linha.pagina


def _sem_ruido_e_repetidas(linhas):
    """Tira linha de OCR de baixa confiança e cabeçalho/rodapé que se repete por página. Número
    sozinho nunca sai: é o que numera as questões (a FGV tem 70 deles, todos iguais depois de
    trocar dígito por #)."""
    linhas = [l for l in linhas if l.confianca is None or l.confianca >= CONFIANCA_RUIDO]
    unidades = {_unidade(l) for l in linhas}
    if len(unidades) < 3:
        return linhas
    vistas = {}
    for l in linhas:
        chave = re.sub(r"\d+", "#", l.texto.strip().lower())
        vistas.setdefault(chave, set()).add(_unidade(l))
    # Cabeçalho e rodapé estão em quase toda página; um 70% poupa o enunciado que se repete de
    # verdade ("Está correto o que se afirma APENAS em" aparece em muitas questões da FCC).
    limite = max(4, int(len(unidades) * 0.7))
    repetidas = {k for k, u in vistas.items() if len(u) >= limite and len(k) <= 120}
    return [l for l in linhas
            if R_NUM_SOZINHO.match(l.texto)
            or R_ALT.match(l.texto)
            or re.sub(r"\d+", "#", l.texto.strip().lower()) not in repetidas]


def _formato(linhas):
    """Múltipla escolha se existe a sequência A, B, C em linhas próximas; certo/errado não tem
    alternativas. Não por contagem: uma prova de poucas questões também é de múltipla escolha."""
    for i, l in enumerate(linhas):
        m = R_ALT.match(l.texto)
        if m and m.group(1) == "A":
            seguintes = {mm.group(1) for x in linhas[i + 1:i + 16] if (mm := R_ALT.match(x.texto))}
            if {"B", "C"} <= seguintes:
                return "MULTIPLA_ESCOLHA"
    return "CERTO_ERRADO"


# ---------------------------------------------------------------- largadas

def _inicio(texto, numero, formato=None):
    """(True, resto da linha) se `texto` abre a questão `numero`. Vale para as duas formas: o
    número sozinho (FGV; CEBRASPE nos itens de 1 a 9) e o número seguido do texto."""
    for regra in (R_NUM_SOZINHO, R_NUM_PONTO, R_NUM_TEXTO):
        m = regra.match(texto)
        if m and int(m.group(1)) == numero:
            return True, (m.group(2).strip() if regra is not R_NUM_SOZINHO else "")
    return False, ""


def _alternativas_adiante(linhas, i, proximo, formato):
    """Há "A)" e "B)" logo adiante? Não para na linha que lembra a questão seguinte: uma lista
    numerada dentro do enunciado ("2. segundo item") tem o mesmo número e vem antes das alternativas.
    Para só depois do "E", quando as alternativas acabaram."""
    letras = set()
    for l in linhas[i + 1:i + 1 + JANELA_ALTERNATIVAS]:
        m = R_ALT.match(l.texto)
        if m:
            letras.add(m.group(1))
            if m.group(1) == "E":
                break
    return {"A", "B"} <= letras


def _alternativas_desde(linhas, desde, ate):
    return sum(1 for l in linhas[desde:ate] if R_ALT.match(l.texto))


def _largadas(linhas, formato):
    """[(indice_da_linha, numero, resto)] — as largadas confirmadas, em ordem. Número que não
    aparece é pulado (até MAX_PULO_DE_NUMERO) só em múltipla escolha, onde a confirmação por
    alternativas segura os falsos positivos."""
    largadas = []
    proximo = 1
    for i, l in enumerate(linhas):
        # A primeira questão nunca é pulada: a capa tem linhas como "2 (duas) horas após o início",
        # e um pulo logo de saída consumiria a numeração (achado na prova real da FGV).
        pulos = MAX_PULO_DE_NUMERO + 1 if formato == "MULTIPLA_ESCOLHA" and largadas else 1
        for pulo in range(0, pulos):
            candidato = proximo + pulo
            achou, resto = _inicio(l.texto, candidato, formato)
            if not achou:
                continue
            if formato == "MULTIPLA_ESCOLHA":
                # A anterior só "fecha" depois de chegar às alternativas (uma lista numerada no enunciado
                # vem antes delas); se vieram poucas, a validação a declara incompleta — ela não engole a seguinte.
                anterior_completa = not largadas or _alternativas_desde(linhas, largadas[-1][0], i) >= MIN_ALTERNATIVAS_PARA_FECHAR
                if not (anterior_completa and _alternativas_adiante(linhas, i, candidato, formato)):
                    continue
            largadas.append((i, candidato, resto))
            proximo = candidato + 1
            break
    return largadas


# ---------------------------------------------------------------- blocos

def _juntar(linhas):
    """Junta linhas de um mesmo texto: palavra hifenizada no fim da linha volta inteira."""
    texto = ""
    for linha in (l.strip() for l in linhas if l.strip()):
        if texto.endswith("-") and linha[:1].islower() and len(texto) > 1 and texto[-2].isalpha():
            texto = texto[:-1] + linha
        else:
            texto = f"{texto} {linha}" if texto else linha
    return texto.strip()


def _parece_cabecalho(linha, anterior):
    return (len(linha) <= 80 and linha[:1].isupper() and not linha.rstrip().endswith(FIM_DE_FRASE)
            and anterior.rstrip().endswith((".", "?", "!", ";")))


def _dividir(textos):
    """(enunciado, [(letra, texto)], cabecalho_da_proxima). As alternativas só valem em ordem
    A, B, C...: um "(A)" citado no meio do enunciado não conta."""
    enunciado, alternativas = [], []
    esperada = "A"
    for t in textos:
        m = R_ALT.match(t)
        if m and m.group(1) == esperada:
            alternativas.append([m.group(1), [m.group(2)]])
            esperada = chr(ord(esperada) + 1)
        elif alternativas:
            alternativas[-1][1].append(t)
        else:
            enunciado.append(t)
    cabecalho = None
    if alternativas and len(alternativas[-1][1]) >= 2:
        ultima = alternativas[-1][1]
        if _parece_cabecalho(ultima[-1].strip(), ultima[-2]):
            cabecalho = ultima.pop().strip()
    return _juntar(enunciado), [(letra, _juntar(ls)) for letra, ls in alternativas], cabecalho


def _romano_mal_lido(textos):
    """Itens de lista em algarismos romanos que o OCR leu como "1.", "11.", "TI.": a resposta
    depende de qual item é qual, e não dá para saber (D-85)."""
    fichas = []
    for t in textos:
        m = R_ITEM_DE_LISTA.match(t)
        if m:
            fichas.append(m.group(1))
    return len(fichas) >= 2 and any(not R_ROMANO_CERTO.match(f) for f in fichas)


def _confianca_baixa(linhas_da_questao):
    com_ocr = [l for l in linhas_da_questao if l.confianca is not None]
    if not com_ocr:
        return False
    baixas = sum(1 for l in com_ocr if l.confianca < CONFIANCA_DUVIDOSA)
    return baixas / len(com_ocr) >= FRACAO_DUVIDOSA


# ---------------------------------------------------------------- a segmentação

def segmentar(linhas, total_esperado=None):
    """As linhas da prova -> Segmentacao. Número que não foi achado vira questão sem texto, para o
    gabarito casar com a prova (D-82); `total_esperado` (o nº de respostas do gabarito) estende a
    numeração até o fim. Lança ValueError se não achou questão nenhuma."""
    originais = list(linhas)
    linhas = _sem_ruido_e_repetidas(linhas)
    formato = _formato(linhas)
    largadas = _largadas(linhas, formato)
    if not largadas:
        raise ValueError("não achei nenhuma questão no texto da prova")
    capa = capa_da_prova(originais)
    avisos = []
    if formato == "CERTO_ERRADO":
        avisos.append("Prova certo/errado: o texto-base de cada item é o do último comando 'Julgue...'.")

    achadas = {}
    nomeados = _textos_nomeados(linhas) if formato == "CERTO_ERRADO" else {}
    base_atual = _preambulo_antes(linhas, largadas[0][0], nomeados) if formato == "CERTO_ERRADO" else None
    cabecalho_pendente = None
    for k, (inicio, numero, resto) in enumerate(largadas):
        fim = largadas[k + 1][0] if k + 1 < len(largadas) else len(linhas)
        corpo = linhas[inicio + 1:fim]
        textos = ([resto] if resto else []) + [l.texto for l in corpo]
        base_do_item = base_atual
        if formato == "CERTO_ERRADO":
            textos, base_atual = _cortar_preambulo(textos, base_atual, nomeados)
        enunciado, alternativas, cabecalho_seguinte = _dividir(textos)
        todas = [linhas[inicio]] + corpo
        ocr = any(l.ocr for l in todas)
        imagem = linhas[inicio].imagem
        q = QuestaoBruta(numero, enunciado or None, alternativas, base_do_item, cabecalho_pendente, ocr, imagem)
        q.motivo = _validar(q, formato, todas, textos)
        achadas[numero] = q
        cabecalho_pendente = cabecalho_seguinte

    ultimo = max(max(achadas), total_esperado or 0)
    questoes = []
    for numero in range(1, ultimo + 1):
        questoes.append(achadas.get(numero) or QuestaoBruta(numero, None, [], motivo="SEM_TEXTO"))
    faltando = [n for n in range(1, ultimo + 1) if n not in achadas]
    if faltando:
        avisos.append(f"Questões não achadas no texto: {', '.join(map(str, faltando[:20]))}.")
    return Segmentacao(formato, questoes, capa, avisos, capa_da_prova(originais, 12000, 400))


def _textos_nomeados(linhas):
    """Os textos-base com título próprio ("Texto CB1A1"): código -> texto. Os itens do CEBRASPE os
    citam pelo código ("...acerca das ideias veiculadas no texto CB1A1"), sem repeti-los."""
    textos, atual, corpo = {}, None, []
    for l in linhas:
        titulo = R_TITULO_TEXTO.match(l.texto)
        if titulo or R_PREAMBULO_CE.match(l.texto):
            if atual:
                textos[atual] = _juntar(corpo)
            atual, corpo = (titulo.group(1).upper() if titulo else None), []
        elif atual:
            corpo.append(l.texto)
    if atual:
        textos[atual] = _juntar(corpo)
    return textos


def _base_do_comando(comando, nomeados):
    """O comando 'Julgue...' e os textos que ele cita pelo código."""
    codigos = []
    for c in R_CODIGO_TEXTO.findall(comando):
        if c.upper() not in codigos:
            codigos.append(c.upper())
    citados = [f"Texto {c}\n{nomeados[c]}" for c in codigos if nomeados.get(c)]
    return "\n\n".join([comando] + citados)


def _preambulo_antes(linhas, indice, nomeados):
    """O último comando 'Julgue...' antes da primeira questão, com o texto que ele cita."""
    for j in range(indice - 1, max(-1, indice - 400), -1):
        if R_PREAMBULO_CE.match(linhas[j].texto):
            comando = _juntar([l.texto for l in linhas[j:indice]])
            return _base_do_comando(comando, nomeados) if comando else None
    return None


def _cortar_preambulo(textos, base_atual, nomeados):
    """Num item certo/errado, as linhas a partir de um comando 'Julgue...' são o preâmbulo dos
    itens seguintes, não do item: viram o texto-base novo. -> (textos do item, texto-base)."""
    for j, t in enumerate(textos[1:], 1):
        if R_PREAMBULO_CE.match(t):
            comando = _juntar(textos[j:])
            return textos[:j], _base_do_comando(comando, nomeados) if comando else base_atual
    return textos, base_atual


def _validar(q, formato, linhas_da_questao, textos):
    """None se a questão está inteira; senão o motivo de sair do denominador (D-70, D-85)."""
    if not q.enunciado:
        return "SEM_TEXTO"
    if formato == "MULTIPLA_ESCOLHA":
        letras = [letra for letra, _ in q.alternativas]
        if len(letras) < MIN_ALTERNATIVAS or any(not texto for _, texto in q.alternativas):
            return "OCR_DUVIDOSO" if q.lida_por_ocr else "SEM_TEXTO"
    if q.lida_por_ocr and (_confianca_baixa(linhas_da_questao) or _romano_mal_lido(textos)):
        return "OCR_DUVIDOSO"
    return None


# ---------------------------------------------------------------- capa

def capa_da_prova(linhas, maximo=1500, n=60):
    """As primeiras linhas da prova, ANTES do filtro de repetidas: o cabeçalho que se repete em
    toda página ("FGV CONHECIMENTO", "TIPO 1 – PÁGINA 4") é justamente o que diz banca e tipo."""
    return "\n".join(l.texto for l in linhas[:n])[:maximo]


BANCAS = ("CEBRASPE", "CESPE", "FGV", "FCC", "IDECAN", "VUNESP", "CESGRANRIO", "IBFC", "QUADRIX", "AOCP", "FUNDATEC", "FUNCAB")


def metadados_da_capa(capa, capa_ampla=None):
    """Banca, ano, tipo e cargo, quando a capa os mostra. Só uma pista: a IA do gabarito é quem
    casa o cargo e o tipo de verdade. A banca e o tipo se procuram na janela ampla (o nome da banca
    está no cabeçalho das páginas); o ano só na capa curta, porque datas de lei pelo texto afora
    dariam o ano errado."""
    texto = capa or ""
    ampla = capa_ampla if capa_ampla is not None else texto
    maiusculo = ampla.upper()
    banca = next((b for b in BANCAS if re.search(rf"\b{b}\b", maiusculo)), None)
    if banca == "CESPE":
        banca = "CEBRASPE"
    ano = re.search(r"\b(20[12]\d)\b", texto)
    tipo = re.search(r"\bTIPO\s*[:\-]?\s*([A-D]|\d{1,3})\b", maiusculo)
    cargo = re.search(r"CARGO\s*[:\-]?\s*(.{3,120})", texto, re.IGNORECASE)
    return {
        "banca": banca,
        "ano": int(ano.group(1)) if ano else None,
        "tipo": (tipo.group(1).lstrip("0") or "0") if tipo and tipo.group(1).isdigit() else (tipo.group(1) if tipo else None),
        "cargoProva": cargo.group(1).strip() if cargo else None,
    }
