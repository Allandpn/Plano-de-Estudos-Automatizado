#!/usr/bin/env python3
"""
prova_worker.py — O ciclo das provas do worker (Sprint 24 do SGE-Concursos, ADR-046).

O usuário envia a prova (e o gabarito) pelo SGE. Este ciclo, a cada volta do worker:

    GET /internal/provas/pendentes
      LENDO     → lê o PDF (OCR se for imagem), separa as questões, lê o gabarito, atribui o assunto
                  e entrega ao SGE, que leva a prova à conferência do usuário (J-6 passo 3)
                  — ou, numa prova já lida que só esperava o gabarito, lê só o gabarito
      JULGANDO  → julga as questões que pedem julgamento (D-79) e entrega os vereditos em lotes
                  pequenos: o que já foi julgado sobrevive a um reinício do worker

O estado todo fica no SGE. Três tipos de problema, tratados de jeito diferente de propósito:

  IA indisponível  (assinatura parou, limite da janela) → o ciclo PARA, nada é gravado, tenta no
                    ciclo seguinte. Nunca vira veredito nem gabarito (D-75).
  Prova ilegível   (PDF inválido, imagem sem OCR, nenhuma questão) → `falha` da etapa, com o motivo
                    que o usuário lê. Não adianta tentar de novo sem mudar nada.
  Gabarito que não serve (outro cargo, total diferente) → a prova ESPERA com o motivo ao lado
                    (`avisoGabarito`); a prova em si não falha.
"""

import logging
from collections import Counter
from pathlib import Path

import prova_atribuicao
import prova_gabarito
import prova_julgamento
import prova_pdf
import prova_questoes
from ia_comum import IaIndisponivel
from prova_pdf import ProvaIlegivel
from sge_api import ErroSge

log = logging.getLogger("prova_worker")

# Quantas questões o segmentador pode ter deixado de achar no fim da prova, e o gabarito ainda assim
# valer (a numeração se estende com questões "sem texto"). Mais que isso é gabarito de outra prova.
MAX_QUESTOES_NAO_ACHADAS = 5
JULGADAS_POR_CICLO = 20
LOTE_DE_VEREDITOS = 5
TENTATIVAS_ATE_DESISTIR = 3
ERROS_DE_GABARITO_DO_SGE = ("GABARITO_NAO_CASA", "LETRA_INVALIDA", "SITUACAO_OBRIGATORIA")


class WorkerProvas:
    def __init__(self, sge, provas_dir, material_dir, tesseract=None, julgadas_por_ciclo=JULGADAS_POR_CICLO,
                 lote_de_vereditos=LOTE_DE_VEREDITOS):
        self.sge = sge
        self.provas = Path(provas_dir)
        self.tesseract = tesseract if tesseract is not None else prova_pdf.Tesseract()
        self.julgador = prova_julgamento.Julgador(sge, material_dir)
        self.julgadas_por_ciclo = julgadas_por_ciclo
        self.lote_de_vereditos = lote_de_vereditos
        self._tentativas = Counter()

    # ------------------------------------------------------------ o ciclo

    def ciclo(self):
        """Um passo. Devolve quantas provas avançaram. Não propaga IaIndisponivel: para e espera."""
        feitas = 0
        for p in self.sge.provas_pendentes():
            etapa = "JULGANDO" if p["status"] == "JULGANDO" else "LENDO"
            try:
                self.julgar(p) if etapa == "JULGANDO" else self.ler(p)
                feitas += 1
            except IaIndisponivel as e:
                log.warning("IA indisponível, tento no próximo ciclo: %s", e)
                break
            except ProvaIlegivel as e:
                log.warning("Prova %s ilegível: %s", p["id"], e)
                self._falhar(p, etapa, str(e))
            except ErroSge as e:
                if e.status is None:
                    raise  # SGE fora do ar: quem chama espera e tenta de novo
                log.warning("Prova %s: o SGE recusou (%s).", p["id"], e)
            except Exception as e:  # um bug numa prova não pode travar as outras nem repetir para sempre
                log.exception("Erro inesperado na prova %s", p["id"])
                self._falhar(p, etapa, f"Erro inesperado ao processar a prova: {type(e).__name__}: {e}")
        return feitas

    def _falhar(self, p, etapa, motivo):
        try:
            self.sge.prova_falha(p["id"], etapa, motivo[:1900])
        except ErroSge as e:
            log.warning("Não consegui registrar a falha da prova %s: %s", p["id"], e)

    # ------------------------------------------------------------ ler (J-6 passos 2-3)

    def ler(self, p):
        dados = self.sge.prova_dados_leitura(p["id"])
        if dados["jaLida"]:
            return self._ler_so_o_gabarito(p, dados)
        entrada = self.provas / "entrada" / str(p["id"])
        pasta_paginas = self.provas / "paginas" / str(p["id"])
        leitura = prova_pdf.ler_prova(entrada / "prova.pdf", pasta_paginas, self.tesseract)
        try:
            seg = prova_questoes.segmentar(leitura.linhas)
        except ValueError as e:
            raise ProvaIlegivel(f"Não consegui separar as questões da prova ({e}).") from None
        pasta_paginas.mkdir(parents=True, exist_ok=True)
        (pasta_paginas / "capa.txt").write_text(seg.capa, encoding="utf-8")  # o gabarito-só lê daqui
        meta = prova_questoes.metadados_da_capa(seg.capa, seg.capa_ampla)

        gabarito, aviso = self._ler_gabarito(dados, entrada, seg.capa, seg.formato)
        if gabarito:
            gabarito, aviso, seg = self._conciliar(gabarito, seg, leitura.linhas)
        atribuicoes = prova_atribuicao.atribuir(self.sge, seg.questoes, dados["assuntos"])

        corpo = {
            "banca": meta["banca"], "ano": meta["ano"], "tipo": dados.get("tipo") or meta["tipo"],
            "cargoProva": meta["cargoProva"], "formato": seg.formato, "modelo": None,
            "questoes": [self._questao(q, atribuicoes) for q in seg.questoes],
            "gabarito": gabarito, "avisoGabarito": aviso,
        }
        try:
            self.sge.prova_entregar_leitura(p["id"], corpo)
        except ErroSge as e:
            if not (gabarito and e.codigo in ERROS_DE_GABARITO_DO_SGE):
                raise
            # O SGE conferiu o gabarito de novo (D-82) e não aceitou: entrega a prova sem ele, com o motivo.
            corpo["gabarito"], corpo["avisoGabarito"] = None, f"O gabarito enviado não pôde ser usado: {e}"
            self.sge.prova_entregar_leitura(p["id"], corpo)
        log.info("Prova %s lida: %d questões (%s)%s.", p["id"], len(seg.questoes), seg.formato,
                 ", gabarito lido" if corpo["gabarito"] else ", sem gabarito")

    @staticmethod
    def _questao(q, atribuicoes):
        chave, baixa = atribuicoes.get(q.numero, (None, False))
        return {
            "numero": q.numero, "enunciado": q.enunciado, "textoBase": q.texto_base, "cabecalhoDisciplina": q.cabecalho,
            "alternativas": [{"letra": letra, "texto": texto} for letra, texto in q.alternativas],
            "assuntoChaveExterna": chave, "baixaConfianca": baixa, "lidaPorOcr": q.lida_por_ocr,
            "paginaOrigem": q.pagina_origem, "motivoNaoAvaliavel": q.motivo,
        }

    def _ler_gabarito(self, dados, entrada, capa, formato, total_esperado=None):
        """-> (gabarito, aviso). Sem arquivo, os dois são None (a prova espera sem alarde)."""
        nome = dados.get("gabaritoArquivo")
        if not nome:
            return None, None
        arquivo = entrada / nome
        try:
            paginas = prova_pdf.texto_do_arquivo(arquivo)
        except FileNotFoundError:
            return None, f"O arquivo do gabarito ({nome}) não está no servidor."
        except ProvaIlegivel as e:
            return None, f"O gabarito enviado não pôde ser usado: {e}"
        return prova_gabarito.ler_gabarito(self.sge, paginas, capa, formato, total_esperado,
                                           tipo=dados.get("tipo"), cargo=dados.get("cargoProva"))

    def _conciliar(self, gabarito, seg, linhas):
        """Confere o total de respostas com o de questões (D-82). Se o gabarito traz poucas a mais, são
        questões que o segmentador não achou: a numeração se estende (sem texto). Senão, é outro gabarito."""
        n_gabarito, n_questoes = len(gabarito["respostas"]), len(seg.questoes)
        if n_gabarito == n_questoes:
            return gabarito, None, seg
        if 0 < n_gabarito - n_questoes <= MAX_QUESTOES_NAO_ACHADAS:
            return gabarito, None, prova_questoes.segmentar(linhas, total_esperado=n_gabarito)
        return None, f"O gabarito enviado não pôde ser usado: ele traz {n_gabarito} respostas e a prova tem {n_questoes} questões.", seg

    def _ler_so_o_gabarito(self, p, dados):
        """A prova já foi lida e esperava pelo gabarito (que o usuário acabou de enviar)."""
        entrada = self.provas / "entrada" / str(p["id"])
        capa_arquivo = self.provas / "paginas" / str(p["id"]) / "capa.txt"
        capa = capa_arquivo.read_text(encoding="utf-8") if capa_arquivo.is_file() \
            else f"{dados.get('cargoProva') or ''}\n{dados.get('nome') or ''}"
        gabarito, aviso = self._ler_gabarito(dados, entrada, capa, dados["formato"])
        if gabarito is None and aviso is None:
            aviso = "Nenhum gabarito foi enviado."
        if gabarito and len(gabarito["respostas"]) != len(dados["numerosDasQuestoes"]):
            gabarito, aviso = None, (f"O gabarito enviado não pôde ser usado: ele traz {len(gabarito['respostas'])} respostas "
                                     f"e a prova tem {len(dados['numerosDasQuestoes'])} questões.")
        self.sge.prova_entregar_gabarito(p["id"], {"modelo": None, "gabarito": gabarito, "avisoGabarito": aviso})
        log.info("Prova %s: %s.", p["id"], "gabarito lido" if gabarito else "gabarito recusado (" + aviso + ")")

    # ------------------------------------------------------------ julgar (J-6 passo 5, D-79)

    def julgar(self, p):
        dados = self.sge.prova_para_julgar(p["id"])
        formato, lote, julgadas = dados["formato"], [], 0
        try:
            for q in dados["questoes"]:
                if julgadas >= self.julgadas_por_ciclo:
                    break
                chave = (p["id"], q["numero"])
                try:
                    item = self.julgador.julgar(q, formato)
                except prova_julgamento.JulgamentoFalhou as e:
                    # Resposta ilegível da IA não é veredito (D-75). Pula; só depois de várias voltas é que
                    # a questão fica "não respondível", com o motivo, para a prova não ficar presa nela.
                    self._tentativas[chave] += 1
                    log.warning("%s (tentativa %d).", e, self._tentativas[chave])
                    if self._tentativas[chave] < TENTATIVAS_ATE_DESISTIR:
                        continue
                    item = {"numero": q["numero"], "veredito": "NAO_RESPONDIVEL", "segmentoId": None,
                            "paginaSegmento": None, "falta": "Não foi possível julgar: a IA não devolveu um veredito legível."}
                lote.append(item)
                julgadas += 1
                if len(lote) >= self.lote_de_vereditos:
                    self._entregar(p, lote)
                    lote = []
        finally:
            # IA indisponível no meio: o que já foi julgado é entregue, e o resto espera o próximo ciclo.
            if lote:
                self._entregar(p, lote)
        log.info("Prova %s: %d questões julgadas neste ciclo.", p["id"], julgadas)

    def _entregar(self, p, itens):
        resposta = self.sge.prova_vereditos(p["id"], {"modelo": None, "itens": itens})
        for r in (resposta.get("rebaixados") or []) + (resposta.get("recusados") or []):
            log.info("Prova %s, questão %s: %s", p["id"], r.get("numero"), r.get("motivo"))
