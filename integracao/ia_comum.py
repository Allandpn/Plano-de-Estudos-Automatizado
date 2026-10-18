#!/usr/bin/env python3
"""
ia_comum.py — O que o worker do material (worker.py) e o worker da prova (prova_worker.py)
dividem da IA: o erro de "a IA não respondeu" e a leitura do JSON que ela devolve.

A IA passa pelo proxy do SGE (POST /internal/ia/completar), que usa a assinatura do Claude
cadastrada em Ajustes (ADR-045 do SGE). Quando a assinatura para (limite da janela, token
expirado), isso NÃO é lacuna do assunto nem veredito da questão: o ciclo para e tenta de novo
depois (D-65 e D-75 do SGE).
"""

import json

from sge_api import ErroSge


class IaIndisponivel(Exception):
    """A IA não respondeu (sem chave, sem crédito, fora do ar). Não é lacuna nem veredito:
    o ciclo para e tenta de novo depois."""


def extrair_json(conteudo):
    """O JSON de uma resposta da IA, mesmo com texto antes ou depois (ou cercado de ```).
    Lança ValueError se não houver JSON legível."""
    try:
        return json.loads(conteudo)
    except (json.JSONDecodeError, TypeError):
        pass
    texto = conteudo if isinstance(conteudo, str) else ""
    for abre, fecha in (("{", "}"), ("[", "]")):
        inicio, fim = texto.find(abre), texto.rfind(fecha)
        if 0 <= inicio < fim:
            try:
                return json.loads(texto[inicio:fim + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError("a IA não devolveu JSON legível")


def completar_json(sge, sistema, usuario):
    """Pergunta à IA e devolve o JSON da resposta. ErroSge do proxy vira IaIndisponivel;
    resposta sem JSON lança ValueError (quem chama decide se tenta de novo)."""
    try:
        resposta = sge.completar(sistema, usuario)
    except ErroSge as e:
        raise IaIndisponivel(str(e)) from None
    return extrair_json(resposta)
