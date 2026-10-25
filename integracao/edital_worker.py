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


# ====================================================================================================================
# O material por casamento (Sprint 26 do SGE; docs/SPRINT-26-REPROCESSAR-E-MATERIAL.md §6 e §7)

import csv  # noqa: E402
import io  # noqa: E402
import shutil  # noqa: E402

CAMPOS_SEGMENTOS = ["chaveExternaSegmento", "chaveExternaAssunto", "ordem", "arquivo", "paginaInicial", "paginaFinal", "tempoEstimadoMin"]
ETAPAS_DO_MATERIAL = ["casar", "confirmar", "manifestos", "segunda", "consulta"]
SITUACAO_DO_SGE = {"completo": "COMPLETO", "parcial": "PARCIAL", "sem material": "SEM_MATERIAL", "recusado": "RECUSADO"}
MOTIVO_SEM_TEMA = "nenhum tema do acervo ensina esta parte"


def csv_dos_segmentos(chave_externa, segmentos):
    """O segmentos.csv de sempre, com a chave externa do assunto no SGE (o UUID dado na conclusão, D-64)."""
    saida = io.StringIO()
    escritor = csv.DictWriter(saida, fieldnames=CAMPOS_SEGMENTOS, lineterminator="\n")
    escritor.writeheader()
    for sg in segmentos:
        escritor.writerow({"chaveExternaSegmento": sg["chave_externa_segmento"], "chaveExternaAssunto": chave_externa,
                           "ordem": sg["ordem"], "arquivo": "/material/" + sg["arquivo"],
                           "paginaInicial": "" if sg["pagina_inicial"] is None else sg["pagina_inicial"],
                           "paginaFinal": "" if sg["pagina_final"] is None else sg["pagina_final"],
                           "tempoEstimadoMin": sg["tempo_estimado_min"]})
    return saida.getvalue()


def entradas_do_material(pendente, nos_validos=None):
    """`partes.json` e `nos.json` do pipeline a partir do que a PESSOA conferiu no SGE (não do que a IA propôs). Uma ligação por
    parte distinta (disciplina, nome, contexto), como `mapear_partes.itens_das_partes`; a chave do assunto vem pronta."""
    disciplinas, itens, partes, por_chave = [], [], [], {}
    por_disciplina = {}
    for a in pendente["assuntos"]:
        if a["disciplina"] not in por_disciplina:
            por_disciplina[a["disciplina"]] = {"nome": a["disciplina"], "assuntos": []}
            disciplinas.append(por_disciplina[a["disciplina"]])
        d = por_disciplina[a["disciplina"]]
        d["assuntos"].append({"chave": a["chave"], "texto": a["texto"], "erros": [], "alertas": [],
                              "partes": [{"texto": p["texto"], "contexto": p.get("contexto"), "herdado": p.get("herdado")} for p in a["partes"]]})
        for ip, p in enumerate(a["partes"]):
            nome = " ".join(x for x in (p.get("herdado"), p["texto"]) if x).strip()
            contexto = p.get("contexto") or ""
            chave = (a["disciplina"], nome.lower(), contexto.lower())
            if chave not in por_chave:
                nos = [n for n in p.get("nos") or [] if nos_validos is None or n in nos_validos]
                por_chave[chave] = len(itens)
                itens.append({"tipo": "parte", "nome": nome, "disciplina": a["disciplina"], "termos": [contexto] if contexto else [a["texto"][:100]],
                              "raizes": [], "candidatos": [], "ia": nos, "natureza": (p.get("natureza") or "").lower() or None,
                              "decisao": "conferida pela pessoa"})
            partes.append({"disciplina": a["disciplina"], "assunto": len(d["assuntos"]) - 1, "parte": ip, "item": por_chave[chave]})
    return disciplinas, {"itens": itens, "partes": partes}


class MaterialDoEdital:
    """O ciclo do material por casamento: casa as partes conferidas com as aulas, corta os segmentos, importa e entrega a situação."""

    def __init__(self, sge, trabalho_dir, material_dir, catalogo, fichas, acervo, indice, modo="completo", funcoes=None, log_etapa=None,
                 fatiador=None):
        self.sge = sge
        self.trabalho = Path(trabalho_dir) / "editais"
        self.material = Path(material_dir)
        self.catalogo, self.fichas, self.acervo, self.indice, self.modo = catalogo, fichas, acervo, indice, modo
        self.funcoes = funcoes
        self.fatiador = fatiador  # só os testes trocam o fatiador de PDF
        self.log_etapa = log_etapa or (lambda m: log.info(m))

    def disponivel(self):
        return all(x and Path(x).exists() for x in (self.catalogo, self.fichas))

    def ciclo(self):
        """Um edital por volta. Devolve quantos assuntos tiveram o material entregue."""
        if not self.disponivel():
            return 0
        pendentes = self.sge.edital_material_pendentes()
        if not pendentes:
            return 0
        try:
            return self.processar(pendentes[0])
        except IaIndisponivel as e:
            log.warning("IA indisponível, o material segue no próximo ciclo: %s", e)
            return 0

    def processar(self, pendente):
        from casar_taxonomia import Arvore, carregar_arvore
        analise_id = pendente["analiseId"]
        pasta = self.trabalho / str(analise_id) / "material"
        pasta.mkdir(parents=True, exist_ok=True)
        # A pasta é do lote que o SGE pediu: se o lote mudou (assunto a mais ou a menos), o trabalho antigo não vale.
        lote = sorted(a["chave"] for a in pendente["assuntos"])
        marca = pasta / "lote.json"
        if marca.exists() and json.loads(marca.read_text(encoding="utf-8")) != lote:
            for f in pasta.iterdir():
                shutil.rmtree(f) if f.is_dir() else f.unlink()
        marca.write_text(json.dumps(lote), encoding="utf-8")
        ctx = pe.Contexto(None, pendente.get("slug") or f"analise-{analise_id}", pendente.get("cargo") or "", pasta, self.catalogo, self.fichas,
                          self.acervo, self.modo, None, self.sge, True, log=self.log_etapa, indice=self.indice)
        if not ctx.arquivo("nos.json").exists():
            arvore = Arvore(carregar_arvore()[0])
            disciplinas, nos = entradas_do_material(pendente, set(arvore.nos))
            nos["arvore"] = carregar_arvore()[1]
            ctx.gravar("partes.json", disciplinas)
            ctx.gravar("nos.json", nos)
        pe.executar(ctx, ate="consulta", funcoes=self.funcoes, etapas=ETAPAS_DO_MATERIAL)
        return self._entregar(analise_id, pendente, ctx)

    def _entregar(self, analise_id, pendente, ctx):
        fatiar = self.fatiador
        if fatiar is None:
            import montar_bloco as mb
            fatiar = lambda manifesto, destino: mb.montar_bloco(manifesto, destino, refatiar=True)[1]  # noqa: E731
        linhas = {l["chave"]: l for l in ctx.ler("assuntos.json")}
        consulta = {c["chave"]: c for c in ctx.ler("consulta/consulta.json")} if ctx.arquivo("consulta/consulta.json").exists() else {}
        saida = []
        for a in pendente["assuntos"]:
            linha = linhas.get(a["chave"])
            if linha is None:
                continue
            situacao = SITUACAO_DO_SGE[linha["situacao"]]
            manifesto = ctx.arquivo(f"manifestos/{a['chave']}.json")
            lacunas = []
            if situacao == "RECUSADO":
                lacunas = [{"parte": "(fatiador)", "motivo": e[:300]} for e in (linha.get("erros") or [])[:3]]
            elif situacao == "SEM_MATERIAL":
                lacunas = [{"parte": p["texto"], "motivo": MOTIVO_SEM_TEMA} for p in a["partes"]]
            elif manifesto.exists():
                lacunas = [{"parte": l["subitem"], "motivo": l["motivo"]} for l in json.loads(manifesto.read_text(encoding="utf-8")).get("lacunas", [])]
            if situacao in ("COMPLETO", "PARCIAL") and not a.get("temSegmentos") and a.get("chaveExterna"):
                # O SGE nunca apaga segmento: assunto que já tem não recebe os novos (a pessoa usa "Refazer o material", D-66).
                segmentos = fatiar(manifesto, self.material)
                self.sge.importar_segmentos(csv_dos_segmentos(a["chaveExterna"], segmentos))
            elif situacao == "SEM_MATERIAL" and a.get("chaveExterna") and not a.get("temSegmentos"):
                self.sge.registrar_lacuna(a["chaveExterna"], "nenhum tema do acervo ensina as partes deste assunto (casamento por partes)")
            entrada = {"chave": a["chave"], "situacao": situacao, "minutos": linha["minutos"], "fontes": linha["fontes"], "lacunas": lacunas}
            c = consulta.get(a["chave"])
            if c and c.get("arquivo"):
                destino = self.material / "consulta"
                destino.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ctx.arquivo(f"consulta/{c['arquivo']}"), destino / f"{a['chave']}.pdf")
                entrada["consulta"] = {"arquivo": f"consulta/{a['chave']}.pdf", "paginas": c["paginas"]}
            saida.append(entrada)
        self.sge.edital_material_entregar(analise_id, saida)
        log.info("Material do edital %s entregue: %d assunto(s).", analise_id, len(saida))
        return len(saida)
