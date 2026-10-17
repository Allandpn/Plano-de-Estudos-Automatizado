#!/usr/bin/env python3
"""
worker.py — Prepara sozinho o material de leitura do concurso-alvo do SGE-Concursos.

Roda no Pi, ao lado do SGE, como um contêiner do mesmo compose (ADR-044 do SGE;
docs/arquitetura-integracao-planejamento-sge.md §9). O usuário sobe o edital e escolhe o
cargo no SGE; daqui em diante nada pede intervenção:

    a cada INTERVALO_SEG segundos:
        concurso-alvo do SGE → assuntos do edital
        para cada assunto sem segmento e sem lacuna (um por vez):
            busca no índice do acervo → arquivos e páginas candidatos
            IA (pelo proxy do SGE, com a chave e o modelo de Ajustes) escolhe as páginas
            dias/montar_bloco.py valida a escolha e fatia em segmentos
              recusada: uma nova tentativa, com os erros; recusada de novo: lacuna
            importa o segmentos.csv no SGE (arquivo = /material/blocos/...)
        o que o acervo não ensina vira lacuna com motivo (D-65) — nunca material inventado

O estado fica todo no SGE (quantos segmentos cada assunto tem, se tem lacuna): reiniciar o
worker no meio retoma de onde parou. Uso:

    python worker.py                 # laço contínuo (contêiner)
    python worker.py --uma-vez       # um ciclo e sai (manual / teste)

Configuração (variáveis de ambiente):
    SGE_URL          http://app:8080          (rede interna do compose)
    INTERNAL_TOKEN   o mesmo do SGE
    ACERVO_DIR       raiz das apostilas       (somente leitura)
    INDICE_DB        indice.db gerado no PC   (somente leitura)
    MATERIAL_DIR     onde os PDFs fatiados ficam (o SGE serve em /material/)
    TRABALHO_DIR     manifestos gerados       (padrão: MATERIAL_DIR/.manifestos)
    INTERVALO_SEG    300
    MAX_POR_CICLO    10
"""

import argparse
import csv
import io
import json
import logging
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dias"))
import montar_bloco as mb  # noqa: E402
import triagem_ia  # noqa: E402
from acervo import Acervo, termos_de_busca  # noqa: E402
from sge_api import ErroSge, SgeApi  # noqa: E402

log = logging.getLogger("worker")

CAMPOS_SEGMENTOS = ["chaveExternaSegmento", "chaveExternaAssunto", "ordem", "arquivo",
                    "paginaInicial", "paginaFinal", "tempoEstimadoMin"]
TENTATIVAS_IA = 2


class IaIndisponivel(Exception):
    """A IA não respondeu (sem chave, sem crédito, fora do ar). Não é lacuna do assunto:
    o ciclo para e tenta de novo depois."""


class Worker:
    def __init__(self, sge, acervo, material_dir, trabalho_dir, max_por_ciclo=10):
        self.sge = sge
        self.acervo = acervo
        self.material_dir = Path(material_dir)
        self.trabalho_dir = Path(trabalho_dir)
        self.max_por_ciclo = max_por_ciclo

    def ciclo(self):
        """Um passo do laço. Devolve quantos assuntos foram resolvidos (material ou lacuna)."""
        ativo = self.sge.concurso_ativo()
        if not ativo:
            log.info("Nenhum concurso-alvo no SGE.")
            return 0
        entrega = self.sge.planejamento(ativo["id"])
        pendentes = [a for a in entrega["assuntos"]
                     if a.get("chaveExterna") and not a.get("segmentos") and not a.get("lacuna")]
        if not pendentes:
            return 0
        log.info("%s: %d assunto(s) a preparar.", entrega["nome"], len(pendentes))
        feitos = 0
        for assunto in pendentes[:self.max_por_ciclo]:
            try:
                self.preparar(assunto, entrega["slug"])
                feitos += 1
            except IaIndisponivel as e:
                log.warning("IA indisponível, tento no próximo ciclo: %s", e)
                break
        return feitos

    def preparar(self, assunto, edital):
        nome, disciplina, chave = assunto["assunto"], assunto["disciplina"], assunto["chaveExterna"]
        candidatos = self.acervo.candidatos(termos_de_busca(nome))
        if not candidatos:
            return self._lacuna(chave, nome, "nenhuma página do acervo cita os termos do assunto")

        partes = triagem_ia.partes_do_assunto(nome)
        erros = None
        for tentativa in range(1, TENTATIVAS_IA + 1):
            pedido = triagem_ia.montar_pedido(nome, disciplina, partes, candidatos, erros)
            try:
                resposta = self.sge.completar(triagem_ia.SISTEMA, pedido)
            except ErroSge as e:
                raise IaIndisponivel(str(e)) from None
            try:
                tipo, valor = triagem_ia.interpretar(resposta, candidatos)
            except ValueError as e:
                erros = [f"resposta ilegível: {e}"]
                continue
            if tipo == "sem_material":
                return self._lacuna(chave, nome, valor)
            try:
                segmentos = self._fatiar(chave, edital, disciplina, nome, partes, valor)
            except mb.ManifestoInvalido as e:
                erros = e.erros
                log.info("%s: tentativa %d recusada pela validação (%d erro(s)).", nome, tentativa, len(erros))
                continue
            self.sge.importar_segmentos(self._csv(chave, segmentos))
            log.info("%s: %d segmento(s) prontos.", nome, len(segmentos))
            return True
        motivo = "a seleção de páginas da IA não passou na validação: " + "; ".join((erros or [])[:3])
        return self._lacuna(chave, nome, motivo[:900])

    def _fatiar(self, chave, edital, disciplina, nome, partes, escolha):
        manifesto = {
            "assunto_uuid": chave,
            "edital": edital,
            # Disciplina no título: dois assuntos de mesmo nome em disciplinas diferentes não
            # podem cair na mesma pasta blocos/<slug>/.
            "titulo": f"{disciplina} — {nome}",
            "subitens": partes,
            "lacunas": escolha["lacunas"],
            "fontes": [dict(f, arquivo=str(self.acervo.caminho(f["arquivo"]))) for f in escolha["fontes"]],
            "descartes": [],
        }
        self.trabalho_dir.mkdir(parents=True, exist_ok=True)
        caminho = self.trabalho_dir / f"{chave}.json"
        caminho.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
        # refatiar=True: só chegam aqui assuntos sem segmento no SGE, então um corte anterior
        # (de uma tentativa que não chegou a ser importada) nunca foi visto pelo usuário.
        _, segmentos = mb.montar_bloco(caminho, self.material_dir, refatiar=True)
        return segmentos

    @staticmethod
    def _csv(chave, segmentos):
        saida = io.StringIO()
        escritor = csv.DictWriter(saida, fieldnames=CAMPOS_SEGMENTOS, lineterminator="\n")
        escritor.writeheader()
        for sg in segmentos:
            escritor.writerow({
                "chaveExternaSegmento": sg["chave_externa_segmento"],
                "chaveExternaAssunto": chave,
                "ordem": sg["ordem"],
                "arquivo": "/material/" + sg["arquivo"],
                "paginaInicial": "" if sg["pagina_inicial"] is None else sg["pagina_inicial"],
                "paginaFinal": "" if sg["pagina_final"] is None else sg["pagina_final"],
                "tempoEstimadoMin": sg["tempo_estimado_min"],
            })
        return saida.getvalue()

    def _lacuna(self, chave, nome, motivo):
        self.sge.registrar_lacuna(chave, motivo)
        log.info("%s: sem material no acervo (%s).", nome, motivo)
        return False


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="Prepara sozinho o material do concurso-alvo do SGE.")
    ap.add_argument("--uma-vez", action="store_true", help="Um ciclo e sai")
    args = ap.parse_args()

    env = os.environ
    faltando = [v for v in ("INTERNAL_TOKEN", "ACERVO_DIR", "INDICE_DB", "MATERIAL_DIR") if not env.get(v)]
    if faltando:
        log.error("Configure: %s", ", ".join(faltando))
        sys.exit(1)
    material = env["MATERIAL_DIR"]
    worker = Worker(
        SgeApi(env.get("SGE_URL", "http://app:8080"), env["INTERNAL_TOKEN"]),
        Acervo(env["INDICE_DB"], env["ACERVO_DIR"]),
        material,
        env.get("TRABALHO_DIR", str(Path(material) / ".manifestos")),
        int(env.get("MAX_POR_CICLO", "10")),
    )
    intervalo = int(env.get("INTERVALO_SEG", "300"))
    while True:
        try:
            worker.ciclo()
        except ErroSge as e:
            log.warning("SGE indisponível: %s", e)
        if args.uma_vez:
            break
        time.sleep(intervalo)


if __name__ == "__main__":
    main()
