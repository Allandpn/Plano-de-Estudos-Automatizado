#!/usr/bin/env python3
"""Vetores compartilhados com o SGE: a mesma entrada, a mesma saída, nos dois lados.

O SGE refaz em Java, quando a pessoa edita, divide ou junta uma parte, o que o planejamento calcula aqui: o texto
normalizado, as palavras de um texto, a chave estável de parte e de assunto e a conferência por regra de um assunto
(`partes_edital.conferir_assunto`). Para as duas implementações não divergirem, este módulo gera um arquivo de casos
(`casos-de-teste/vetores-conferencia.json`) que os dois testam: o teste daqui exige que o arquivo seja o que o código
atual gera; o do SGE (`src/test/resources/conferencia/vetores.json`, cópia) exige que o código Java dê as mesmas respostas.
Mudou a regra de um lado, o outro lado quebra. Regerar: `python integracao/vetores_conferencia.py`.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrega_revisao import chave_da_parte, chave_do_assunto  # noqa: E402
from partes_edital import conferir_assunto, normalizar, palavras  # noqa: E402

ARQUIVO = Path(__file__).resolve().parent / "casos-de-teste" / "vetores-conferencia.json"

TEXTOS = [
    "Normalização de banco de dados",
    "  Álgebra  Relacional ",
    "Lei nº 8.112/1990 — art. 5º",
    "Coesão e coerên-\ncia textual",
    "SQL: DDL, DML, DCL",
    "Windows Server 2019 e 2022",
    "Ação, Opção e Eleição (Cônsul)",
    "ÇÃO ÀÉÎÕÜ ção",
    "PMBOK 6ª edição",
    "",
    "Redes: TCP/IP; UDP",
    "Kanban – Scrum – XP",
]

PALAVRAS = [
    "Concordância verbal e nominal",
    "Os princípios da Administração Pública",
    "Redes de computadores e protocolos",
    "Funções de janela (window functions) em SQL",
    "A, o, as e os",
    "4.1 Coesão referencial",
    "Estruturas de dados",
]

SEQUENCIAS_DE_PARTES = [
    {"disciplina": "Banco de Dados", "assunto": "SQL: DDL, DML, DCL", "partes": [
        {"texto": "DDL", "contexto": "SQL", "herdado": None},
        {"texto": "DML", "contexto": "SQL", "herdado": None},
        {"texto": "DDL", "contexto": "SQL", "herdado": None}]},
    {"disciplina": "Língua Portuguesa", "assunto": "Concordância verbal e nominal", "partes": [
        {"texto": "Concordância verbal", "contexto": None, "herdado": None},
        {"texto": "nominal", "contexto": None, "herdado": "Concordância"}]},
]

SEQUENCIAS_DE_ASSUNTOS = [
    {"disciplina": "Banco de Dados", "textos": ["Modelagem", "SQL", "Modelagem", "Modelagem"]},
    {"disciplina": "Redes", "textos": ["TCP/IP", "tcp/ip"]},
]

TEXTO_BD = ("Banco de Dados Apenas para o cargo Analista. "
            "1 Modelagem: conceitual, lógica e física. 2 SQL: DDL, DML e DCL. 3 Normalização. "
            "4 Coesão: 4.1 referencial 4.2 sequencial. Todo o conteúdo das disciplinas de Redes.")


def _parte(texto, contexto=None, herdado=None):
    return {"texto": texto, "contexto": contexto, "herdado": herdado}


CONFERENCIAS = [
    {"nome": "assunto bem quebrado", "cabecalho": "Banco de Dados Analista", "referencias": [], "texto_disciplina": TEXTO_BD,
     "assunto": {"texto": "2 SQL: DDL, DML e DCL", "partes": [_parte("DDL", "SQL"), _parte("DML", "SQL"), _parte("DCL", "SQL")]}},
    {"nome": "assunto reescrito", "cabecalho": "Banco de Dados Analista", "referencias": [], "texto_disciplina": TEXTO_BD,
     "assunto": {"texto": "2 SQL: linguagens DDL, DML e DCL", "partes": [_parte("DDL", "SQL"), _parte("DML", "SQL"), _parte("DCL", "SQL")]}},
    {"nome": "assunto sem partes", "cabecalho": "Banco de Dados", "referencias": [], "texto_disciplina": TEXTO_BD,
     "assunto": {"texto": "3 Normalização", "partes": []}},
    {"nome": "parte com palavra alheia", "cabecalho": "Banco de Dados", "referencias": [], "texto_disciplina": TEXTO_BD,
     "assunto": {"texto": "3 Normalização", "partes": [_parte("Normalização de tabelas")]}},
    {"nome": "herdado fora do assunto", "cabecalho": "Banco de Dados", "referencias": [], "texto_disciplina": TEXTO_BD,
     "assunto": {"texto": "3 Normalização", "partes": [_parte("Normalização", None, "Projeto")]}},
    {"nome": "contexto vindo de assunto anterior vira alerta", "cabecalho": "Banco de Dados", "referencias": [],
     "texto_disciplina": TEXTO_BD,
     "assunto": {"texto": "DML e DCL", "partes": [_parte("DML", "Modelagem"), _parte("DCL", "Modelagem")]}},
    {"nome": "contexto que não está em lugar nenhum", "cabecalho": "Banco de Dados", "referencias": [],
     "texto_disciplina": TEXTO_BD,
     "assunto": {"texto": "3 Normalização", "partes": [_parte("Normalização", "Kubernetes")]}},
    {"nome": "palavras do assunto sem parte", "cabecalho": "Banco de Dados", "referencias": [], "texto_disciplina": TEXTO_BD,
     "assunto": {"texto": "2 SQL: DDL, DML e DCL", "partes": [_parte("DDL", "SQL")]}},
    {"nome": "assunto é só uma referência", "cabecalho": "Banco de Dados", "referencias": ["Todo o conteúdo das disciplinas de Redes"],
     "texto_disciplina": TEXTO_BD,
     "assunto": {"texto": "Todo o conteúdo das disciplinas de Redes", "partes": []}},
    {"nome": "números de item não exigem parte", "cabecalho": "Banco de Dados", "referencias": [], "texto_disciplina": TEXTO_BD,
     "assunto": {"texto": "4 Coesão: 4.1 referencial 4.2 sequencial", "partes": [_parte("referencial", "Coesão"), _parte("sequencial", "Coesão")]}},
    {"nome": "texto da parte com aspas", "cabecalho": "Banco de Dados", "referencias": [], "texto_disciplina": TEXTO_BD,
     "assunto": {"texto": "3 Normalização", "partes": [_parte("Normalização d'água")]}},
]


def gerar():
    saida = {"normalizar": [{"entrada": t, "saida": normalizar(t)} for t in TEXTOS],
             "palavras": [{"entrada": t, "saida": sorted(palavras(t))} for t in PALAVRAS],
             "chaves_de_parte": [], "chaves_de_assunto": [], "conferencias": []}
    for seq in SEQUENCIAS_DE_PARTES:
        vistas = {}
        saida["chaves_de_parte"].append(dict(seq, chaves=[chave_da_parte(seq["disciplina"], seq["assunto"], p, vistas)
                                                         for p in seq["partes"]]))
    for seq in SEQUENCIAS_DE_ASSUNTOS:
        vistos = {}
        saida["chaves_de_assunto"].append(dict(seq, chaves=[chave_do_assunto(seq["disciplina"], t, vistos) for t in seq["textos"]]))
    for c in CONFERENCIAS:
        alertas = []
        erros = conferir_assunto(c["assunto"], c["texto_disciplina"], c["cabecalho"], c["referencias"], alertas)
        saida["conferencias"].append(dict(c, erros=erros, alertas=alertas))
    return saida


def main():
    ARQUIVO.write_text(json.dumps(gerar(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"gravado {ARQUIVO}")


if __name__ == "__main__":
    main()
