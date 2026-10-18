#!/usr/bin/env python3
"""
prova_atribuicao.py — A que assunto do edital pertence cada questão (Sprint 24 do SGE-Concursos,
ADR-046; D-74 e D-77 do SGE).

A IA escolhe, entre os assuntos do concurso-alvo, o de cada questão — ou "nenhum", quando a prova
cobra o que o edital não lista (a legislação do órgão que fez a prova, o bloco de outro cargo).
Quem decide se vale é o sistema: chave que não está na lista da cobertura vira "fora do edital",
nunca um assunto inventado. "Nenhum" é resposta válida e **não é furo do material** (D-74).

A atribuição de baixa confiança vai para o usuário revisar na conferência (J-6 passo 4): é a única
etapa de IA antes do ponto em que o usuário confere, e o erro aqui custaria o julgamento inteiro.
"""

from ia_comum import completar_json

LOTE = 10
TENTATIVAS_IA = 2
MAX_ENUNCIADO = 600
MAX_ALTERNATIVA = 90

SISTEMA = """Você atribui cada questão de uma prova de concurso ao assunto do edital a que ela pertence.
Recebe a lista de assuntos do edital (chave, disciplina e nome) e um lote de questões.

Regras:
- Escolha SÓ entre os assuntos listados, pela chave exata. Nunca invente uma chave.
- Se a questão cobra algo que nenhum assunto lista (por exemplo, a legislação do órgão que aplicou a
  prova, ou matéria de outro cargo), responda "assunto": null.
- "confianca" é "ALTA" quando um assunto claramente cabe, e "BAIXA" quando mais de um cabe ou você está em
  dúvida. Na dúvida, "BAIXA": o usuário vai conferir.
- O cabeçalho de disciplina da prova, quando existe, é uma pista, não uma regra.
- Responda sobre TODAS as questões do lote.

Responda só JSON:
{"atribuicoes": [{"numero": 1, "assunto": "<chave>", "confianca": "ALTA"}, {"numero": 2, "assunto": null, "confianca": "ALTA"}]}"""


def _resumo(q):
    texto = (q.enunciado or "").strip().replace("\n", " ")
    if len(texto) > MAX_ENUNCIADO:
        texto = texto[:MAX_ENUNCIADO] + "…"
    linhas = [f"Q{q.numero}" + (f" [cabeçalho da prova: {q.cabecalho}]" if q.cabecalho else "") + f": {texto}"]
    for letra, alternativa in q.alternativas:
        linhas.append(f"  ({letra}) {alternativa[:MAX_ALTERNATIVA]}")
    return "\n".join(linhas)


def montar_pedido(lote, assuntos, erros_anteriores=None):
    linhas = ["ASSUNTOS DO EDITAL (chave | disciplina | assunto):"]
    linhas += [f"{a['chaveExterna']} | {a['disciplina']} | {a['nome']}" for a in assuntos]
    linhas.append("\nQUESTÕES:")
    linhas += [_resumo(q) for q in lote]
    if erros_anteriores:
        linhas.append("\nSua resposta anterior foi recusada. Corrija:")
        linhas += [f"- {e}" for e in erros_anteriores]
    return "\n".join(linhas)


def interpretar(dados, numeros, chaves):
    """A resposta da IA -> {numero: (chave ou None, baixa_confianca)}. Só para os números pedidos.
    Chave fora da cobertura vira None (fora do edital, D-74). Lança ValueError se o formato não serve."""
    lista = dados.get("atribuicoes") if isinstance(dados, dict) else None
    if not isinstance(lista, list):
        raise ValueError('a resposta não traz a lista "atribuicoes"')
    resultado = {}
    for item in lista:
        if not isinstance(item, dict) or not isinstance(item.get("numero"), int):
            raise ValueError("uma atribuição veio sem número inteiro")
        numero = item["numero"]
        if numero not in numeros:
            continue
        chave = item.get("assunto")
        chave = chave.strip() if isinstance(chave, str) and chave.strip() else None
        if chave not in chaves:
            chave = None
        resultado[numero] = (chave, str(item.get("confianca", "")).strip().upper() != "ALTA")
    return resultado


def atribuir(sge, questoes, assuntos):
    """Atribui as questões com texto aos assuntos, em lotes. -> {numero: (chave|None, baixa_confianca)}.
    Questão sem texto não é atribuída (não há o que classificar). Questão que a IA deixou sem resposta,
    mesmo depois de tentar de novo, volta como (None, True): fora do edital e para revisar — nunca um
    assunto chutado. IaIndisponivel sobe: o ciclo espera, nada é gravado."""
    chaves = {a["chaveExterna"] for a in assuntos}
    com_texto = [q for q in questoes if q.enunciado]
    atribuicoes = {}
    for inicio in range(0, len(com_texto), LOTE):
        lote = com_texto[inicio:inicio + LOTE]
        pendentes = list(lote)
        erros = None
        for _ in range(TENTATIVAS_IA):
            try:
                achadas = interpretar(completar_json(sge, SISTEMA, montar_pedido(pendentes, assuntos, erros)),
                                      {q.numero for q in pendentes}, chaves)
            except ValueError as e:
                erros = [str(e)]
                continue
            atribuicoes.update(achadas)
            pendentes = [q for q in pendentes if q.numero not in achadas]
            if not pendentes:
                break
            erros = [f"faltou responder as questões {', '.join(str(q.numero) for q in pendentes)}"]
        for q in pendentes:
            atribuicoes[q.numero] = (None, True)
    return atribuicoes
