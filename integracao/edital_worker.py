#!/usr/bin/env python3
"""
edital_worker.py — O ciclo dos editais do worker (Sprint 25 do SGE-Concursos, ADR-047).

O usuário sobe o PDF do edital e escolhe o cargo no SGE. Este ciclo, a cada volta do worker:

    GET /internal/editais/pendentes
      → GET .../dados                  o PDF (volume `editais`, só leitura), o cargo e as decisões da pessoa
      → carrega a árvore do QConcursos no SGE, se ainda não foi (POST /internal/arvores; idempotente)
      → extrair → quebrar → ligar      (preparar_edital.py; as decisões valem antes da IA)
      → POST .../revisao               a leitura "edital-revisao/1", que o SGE leva à conferência da pessoa

A pasta de trabalho de cada edital é `TRABALHO_DIR/editais/<análise>/`: cada etapa grava o que fez, então reiniciar o worker
ou "tentar de novo" no SGE continua de onde parou. Os três tipos de problema, tratados de jeito diferente de propósito:

  IA indisponível   (assinatura parou, limite da janela) → o ciclo PARA, nada é reportado, tenta no ciclo seguinte.
  Edital ilegível   (sem conteúdo programático, PDF ausente, resposta que a regra não aceita) → `falha` com a etapa
                    (EXTRACAO, ORGANIZACAO, QUEBRA, LIGACAO) e o motivo; a análise volta a "pendente" quando a pessoa pede.
  SGE recusa a entrega por estado (já em conferência, etapa inválida) → só registra no log: o SGE já seguiu em frente.

O material por casamento (casar, confirmar, manifestos, segunda, consulta) não roda aqui: é da Sprint 26, depois da conclusão.
"""

import json
import logging
import tempfile
from pathlib import Path

import preparar_edital as pe
from casar_taxonomia import PASTA_TAXONOMIA
from ia_comum import IaIndisponivel
from sge_api import ErroSge

log = logging.getLogger("edital_worker")

ETAPAS_DA_LEITURA = ["extrair", "quebrar", "ligar"]
# Estados em que o SGE recusa a entrega porque a análise já não espera o planejamento: não é falha do edital.
RECUSAS_DE_ESTADO = ("ETAPA_INVALIDA", "REPROCESSAR_NA_26")


class WorkerEditais:
    def __init__(self, sge, editais_dir, trabalho_dir, funcoes=None, taxonomia_dir=None, log_etapa=None):
        self.sge = sge
        self.editais = Path(editais_dir)
        self.trabalho = Path(trabalho_dir) / "editais"
        self.funcoes = funcoes  # só os testes trocam as etapas
        self.taxonomia = Path(taxonomia_dir) if taxonomia_dir else PASTA_TAXONOMIA
        self.log_etapa = log_etapa or (lambda m: log.info(m))

    # ------------------------------------------------------------ o ciclo

    def ciclo(self):
        """Um edital por volta (a leitura demora minutos). Devolve quantos foram entregues."""
        pendentes = self.sge.editais_pendentes()
        if not pendentes:
            return 0
        pendente = pendentes[0]
        try:
            return 1 if self.processar(pendente) else 0
        except IaIndisponivel as e:
            log.warning("IA indisponível, tento no próximo ciclo: %s", e)
            return 0

    def processar(self, pendente):
        analise_id = pendente["id"]
        dados = self.sge.edital_dados(analise_id)
        pasta = self.trabalho / str(analise_id)
        pasta.mkdir(parents=True, exist_ok=True)
        pdf = self.editais / (dados.get("pdf") or "")
        if not dados.get("pdf") or not pdf.is_file():
            return self._falha(analise_id, "EXTRACAO", f"O PDF do edital não está no volume ({dados.get('pdf')}).")
        nome_arvore = self._garantir_arvore(pasta)
        decisoes = pasta / "decisoes-do-sge.json"
        decisoes.write_text(json.dumps({"arvore": nome_arvore, "decisoes": dados.get("decisoes") or []}, ensure_ascii=False),
                            encoding="utf-8")
        ctx = pe.Contexto(str(pdf), pendente["slug"], pendente["cargo"], pasta, decisoes=str(decisoes), sge=self.sge,
                          log=self.log_etapa)
        for etapa in ETAPAS_DA_LEITURA:
            try:
                pe.executar(ctx, ate=etapa, funcoes=self.funcoes)
            except IaIndisponivel:
                raise
            except pe.ErroDeEtapa as e:
                return self._falha(analise_id, self._etapa_do_sge(etapa, ctx), str(e))
            except Exception as e:  # noqa: BLE001 — uma falha inesperada não pode deixar a análise esperando para sempre
                log.exception("Falha inesperada em %s do edital %s", etapa, analise_id)
                return self._falha(analise_id, self._etapa_do_sge(etapa, ctx),
                                   f"Falha inesperada na leitura ({type(e).__name__}): {e}"[:900])
        return self._entregar(analise_id, ctx)

    # ------------------------------------------------------------ pedaços

    def _entregar(self, analise_id, ctx):
        funcao = (self.funcoes or pe.FUNCOES)["entrega"]
        funcao(ctx)
        corpo = ctx.arquivo("entrega.json").read_text(encoding="utf-8")
        try:
            resumo = self.sge.edital_entregar(analise_id, corpo)
        except ErroSge as e:
            if e.codigo in RECUSAS_DE_ESTADO:
                log.info("Edital %s: o SGE não espera mais a leitura (%s).", analise_id, e)
                return False
            if e.status is not None and 400 <= e.status < 500:
                return self._falha(analise_id, "LIGACAO", f"O SGE recusou a leitura: {e}"[:900])
            raise
        log.info("Edital %s entregue: %s", analise_id, resumo)
        return True

    def _garantir_arvore(self, pasta):
        """Carrega no SGE a árvore que a ligação vai usar. Idempotente pelo rótulo; o arquivo só sobe uma vez."""
        arquivo = sorted(self.taxonomia.glob("qconcursos-*.json"))[-1]
        enviadas = self.trabalho / "arvores-enviadas.json"
        ja = json.loads(enviadas.read_text(encoding="utf-8")) if enviadas.exists() else []
        if arquivo.stem not in ja:
            self.sge.arvore_carregar(arquivo.read_bytes())
            enviadas.parent.mkdir(parents=True, exist_ok=True)
            enviadas.write_text(json.dumps(ja + [arquivo.stem]), encoding="utf-8")
        return arquivo.stem

    @staticmethod
    def _etapa_do_sge(etapa, ctx):
        """As etapas do contrato (EXTRACAO, ORGANIZACAO, QUEBRA, LIGACAO) a partir das do pipeline."""
        if etapa == "quebrar":
            return "QUEBRA" if ctx.arquivo("organizacao.json").exists() else "ORGANIZACAO"
        return {"extrair": "EXTRACAO", "ligar": "LIGACAO"}[etapa]

    def _falha(self, analise_id, etapa, mensagem):
        log.warning("Edital %s falhou em %s: %s", analise_id, etapa, mensagem)
        self.sge.edital_falha(analise_id, etapa, mensagem)
        return False
