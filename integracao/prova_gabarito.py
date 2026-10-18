#!/usr/bin/env python3
"""
prova_gabarito.py — Ler o gabarito de uma prova (Sprint 24 do SGE-Concursos, ADR-046).

Os gabaritos das bancas não se parecem: FGV entrega UM arquivo para todos os cargos (22 a 41
páginas, uma por cargo e por tipo; Dataprev em duas linhas — números, depois letras —, MPES em
pares "n letra"), IDECAN junta seis cargos numa grade "Q01..Q10", FCC traz uma tabela
"Questão | Resposta | Situação", CEBRASPE uma grade fora de ordem. Regra fixa quebra no edital
seguinte; por isso **a IA lê o gabarito e o sistema valida** (D-67 do SGE).

O que a IA nunca decide: se o que ela devolveu serve. O sistema confere que a numeração é
contígua, que só há letras válidas para o formato e que o total bate com o de questões da prova
(D-82); o recorte é o do cargo e tipo da capa (D-83). Quando não serve, o resultado é um
**aviso com o motivo** — a prova espera o gabarito certo, nunca fica com um silêncio.
"""

import re
import unicodedata

from ia_comum import IaIndisponivel, completar_json  # noqa: F401  (IaIndisponivel sobe para quem chama)

LIMITE_CARACTERES = 24000
TENTATIVAS_IA = 2
MAX_PAGINAS_ESCOLHIDAS = 2

SISTEMA = """Você lê o gabarito oficial de uma prova de concurso público.
Recebe a CAPA da prova (cargo, tipo do caderno, turno) e o texto de um arquivo de gabarito, que pode
trazer vários cargos e vários tipos. Ache a seção que corresponde ao cargo e ao tipo da capa e devolva
as respostas dela, da questão 1 até a última.

Regras:
- O layout varia: pares "número letra"; uma linha de números seguida da linha de letras (a n-ésima
  letra é do n-ésimo número); uma grade "Q01 Q02 ..." seguida das letras; ou uma tabela
  "Questão | Resposta | Situação".
- Questão ANULADA ("*", "X" ou "Anulada" na situação): "resposta": null e "anulada": true.
- Prova certo/errado: a resposta é "C" ou "E".
- "situacao" é "PRELIMINAR" ou "DEFINITIVO", como o título do arquivo diz; se não disser, "PRELIMINAR".
- "recorte": cargo, tipo e turno da seção que você usou, como estão escritos no arquivo.
- Se o cargo ou o tipo da capa não está no arquivo, responda {"encontrado": false, "motivo": "..."}. Não
  adivinhe e não use a seção de outro cargo ou de outro tipo.
- Só o que está no texto: nada de inventar resposta.

Responda só JSON:
{"encontrado": true, "situacao": "PRELIMINAR", "recorte": "<cargo, tipo, turno>",
 "respostas": [{"numero": 1, "resposta": "A"}, {"numero": 2, "resposta": null, "anulada": true}]}"""


class GabaritoNaoEncontrado(ValueError):
    """A IA diz que o cargo ou o tipo da capa não está no arquivo. Não adianta tentar de novo."""


def _normalizar(texto):
    sem = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode("ascii")
    return sem.upper()


def _palavras(texto):
    return {p for p in re.findall(r"[A-Z0-9]{4,}", _normalizar(texto)) if p not in {"TIPO", "PROVA", "CONCURSO", "PUBLICO", "NIVEL", "SUPERIOR"}}


def _tipo(texto):
    m = re.search(r"\bTIPO\s*[:\-]?\s*([A-D]|\d{1,3})\b", _normalizar(texto))
    if not m:
        return None
    return (m.group(1).lstrip("0") or "0") if m.group(1).isdigit() else m.group(1)


def escolher_paginas(paginas, capa, limite=LIMITE_CARACTERES):
    """As páginas do gabarito que valem a pena mandar à IA: [(numero_da_pagina, texto)].
    Gabarito curto vai inteiro. Gabarito comprido (FGV: uma página por cargo e tipo) é pontuado
    pelo cabeçalho de cada página contra a capa da prova: palavras do cargo em comum, e o **tipo**
    pesa muito, porque duas páginas de tipos diferentes têm o mesmo cargo e respostas diferentes.
    Lança ValueError se nenhuma página lembra a capa."""
    todas = [(i, t) for i, t in enumerate(paginas, 1) if t.strip()]
    if sum(len(t) for _, t in todas) <= limite:
        return todas
    palavras_da_capa = _palavras(capa)
    tipo_da_capa = _tipo(capa)
    pontuadas = []
    for i, texto in todas:
        cabecalho = texto[:400]
        pontos = len(palavras_da_capa & _palavras(cabecalho))
        if pontos == 0:
            continue  # o tipo só desempata páginas do mesmo cargo; sozinho, não qualifica uma página
        tipo_da_pagina = _tipo(cabecalho)
        if tipo_da_capa and tipo_da_pagina:
            pontos += 4 if tipo_da_capa == tipo_da_pagina else -6
        pontuadas.append((pontos, i, texto))
    if not pontuadas or max(p for p, _, _ in pontuadas) <= 0:
        raise GabaritoNaoEncontrado("nenhuma página do gabarito lembra o cargo e o tipo da capa da prova")
    melhor = max(p for p, _, _ in pontuadas)
    escolhidas = sorted((p for p in pontuadas if p[0] == melhor), key=lambda p: p[1])[:MAX_PAGINAS_ESCOLHIDAS]
    return [(i, t) for _, i, t in escolhidas]


def montar_pedido(capa, formato, paginas, tipo=None, cargo=None, erros_anteriores=None):
    linhas = ["CAPA DA PROVA:", capa.strip()[:1500], f"\nFormato: {'certo/errado' if formato == 'CERTO_ERRADO' else 'múltipla escolha'}"]
    if tipo:
        linhas.append(f"Tipo informado: {tipo}")
    if cargo:
        linhas.append(f"Cargo informado: {cargo}")
    linhas.append("\nTEXTO DO GABARITO:")
    for numero, texto in paginas:
        linhas.append(f"\n[página {numero}]\n{texto.strip()}")
    if erros_anteriores:
        linhas.append("\nSua resposta anterior foi recusada pela validação. Corrija:")
        linhas += [f"- {e}" for e in erros_anteriores]
    return "\n".join(linhas)


def interpretar(dados, formato, total_esperado=None):
    """A resposta da IA -> {"situacao", "recorte", "respostas": [{"numero", "resposta", "anulada"}]}.
    Valida tudo que o sistema sabe conferir. Lança GabaritoNaoEncontrado se a IA não achou o cargo,
    ValueError (com o motivo) se o que ela devolveu não serve."""
    if not isinstance(dados, dict):
        raise ValueError("a resposta da IA não é um objeto JSON")
    if dados.get("encontrado") is False:
        raise GabaritoNaoEncontrado(str(dados.get("motivo") or "o cargo e o tipo da prova não estão no gabarito"))
    brutas = dados.get("respostas")
    if not isinstance(brutas, list) or not brutas:
        raise ValueError("a IA não devolveu nenhuma resposta")
    permitidas = {"C", "E"} if formato == "CERTO_ERRADO" else {"A", "B", "C", "D", "E"}
    respostas, numeros = [], set()
    for item in brutas:
        if not isinstance(item, dict) or not isinstance(item.get("numero"), int):
            raise ValueError("uma resposta veio sem número inteiro")
        numero = item["numero"]
        if numero in numeros:
            raise ValueError(f"a questão {numero} aparece duas vezes no gabarito")
        numeros.add(numero)
        letra = str(item["resposta"]).strip().upper() if item.get("resposta") is not None else None
        anulada = bool(item.get("anulada")) or letra in ("*", "X", "ANULADA")
        if anulada:
            respostas.append({"numero": numero, "resposta": None, "anulada": True})
            continue
        if letra not in permitidas:
            raise ValueError(f"resposta inválida na questão {numero}: {item.get('resposta')!r} (esperado {'/'.join(sorted(permitidas))})")
        respostas.append({"numero": numero, "resposta": letra, "anulada": False})
    if numeros != set(range(1, len(numeros) + 1)):
        raise ValueError("a numeração do gabarito não é contígua a partir de 1")
    if total_esperado is not None and len(numeros) != total_esperado:
        raise ValueError(f"o gabarito traz {len(numeros)} respostas e a prova tem {total_esperado} questões")
    situacao = "DEFINITIVO" if str(dados.get("situacao", "")).strip().upper().startswith("DEFIN") else "PRELIMINAR"
    return {"situacao": situacao, "recorte": str(dados.get("recorte") or "")[:300],
            "respostas": sorted(respostas, key=lambda r: r["numero"])}


def ler_gabarito(sge, paginas, capa, formato, total_esperado=None, tipo=None, cargo=None):
    """Lê o gabarito com a IA e valida. -> (gabarito, aviso): um dos dois é None. O aviso é o motivo,
    em português, de o gabarito não servir — vai ao usuário. IaIndisponivel sobe: não é aviso, é esperar."""
    try:
        escolhidas = escolher_paginas(paginas, capa)
    except GabaritoNaoEncontrado as e:
        return None, f"O gabarito enviado não pôde ser usado: {e}."
    erros = None
    for _ in range(TENTATIVAS_IA):
        pedido = montar_pedido(capa, formato, escolhidas, tipo, cargo, erros)
        try:
            return interpretar(completar_json(sge, SISTEMA, pedido), formato, total_esperado), None
        except GabaritoNaoEncontrado as e:
            return None, f"O gabarito enviado não pôde ser usado: {e}."
        except ValueError as e:
            erros = [str(e)]
    return None, f"O gabarito enviado não pôde ser usado: {erros[0]}."
