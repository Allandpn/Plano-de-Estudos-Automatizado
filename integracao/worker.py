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
    EDITAIS_DIR      volume `editais` do SGE (Sprint 25, só leitura): o PDF do edital em conferência; sem ele, o
                     worker não lê editais (integracao/edital_worker.py)
    PROVAS_DIR       volume `provas` do SGE (Sprint 24): entrada/ (o SGE grava) e paginas/ (o worker grava);
                     sem ele, o worker só prepara o material e não lê provas
    OCR_IDIOMA       por                      (Tesseract, para prova em imagem)
    OCR_PSM          3                        (segmentação de página do Tesseract; 3 = automática)
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
from ia_comum import IaIndisponivel  # noqa: E402,F401  (também usada pelos testes)
from sge_api import ErroSge, SgeApi  # noqa: E402

log = logging.getLogger("worker")

CAMPOS_SEGMENTOS = ["chaveExternaSegmento", "chaveExternaAssunto", "ordem", "arquivo",
                    "paginaInicial", "paginaFinal", "tempoEstimadoMin"]
TENTATIVAS_IA = 2


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
        partes = triagem_ia.partes_do_assunto(nome)
        # Uma busca por parte, nos cursos afins e no acervo inteiro ao mesmo tempo
        # (Acervo.candidatos_por_partes): uma rodada só, com tudo o que cada parte achou.
        candidatos = self.acervo.candidatos_por_partes(partes, disciplina=disciplina)
        if not candidatos:
            return self._lacuna(chave, nome, "nenhuma página do acervo cita os termos do assunto")
        resultado = self._rodada(chave, nome, disciplina, edital, partes, candidatos)
        if resultado is True:
            return True
        return self._lacuna(chave, nome, resultado)

    def _rodada(self, chave, nome, disciplina, edital, partes, candidatos):
        """Uma rodada de triagem: True se importou os segmentos; senão, o motivo da lacuna."""
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
                return valor
            try:
                segmentos = self._fatiar(chave, edital, disciplina, nome, partes, valor)
            except mb.ManifestoInvalido as e:
                erros = e.erros
                log.info("%s: tentativa %d recusada pela validação (%d erro(s)).", nome, tentativa, len(erros))
                continue
            self.sge.importar_segmentos(self._csv(chave, segmentos))
            self._lacunas_parciais(chave, nome, disciplina, valor["lacunas"])
            log.info("%s: %d segmento(s) prontos.", nome, len(segmentos))
            return True
        return ("a seleção de páginas da IA não passou na validação: " + "; ".join((erros or [])[:3]))[:900]

    def _lacunas_parciais(self, chave, nome, disciplina, lacunas):
        """Parte do assunto que a IA declarou sem página, num assunto que ganhou material. O SGE
        só registra lacuna do assunto inteiro (D-65): sem isto, o assunto aparecia PRONTO e a
        parte que faltou não deixava rastro fora do _cobertura.md. Uma linha JSON por parte em
        TRABALHO_DIR/lacunas-parciais.jsonl — a lista do que o acervo não ensina."""
        if not lacunas:
            return
        self.trabalho_dir.mkdir(parents=True, exist_ok=True)
        with open(self.trabalho_dir / "lacunas-parciais.jsonl", "a", encoding="utf-8") as f:
            for l in lacunas:
                f.write(json.dumps({"quando": time.strftime("%Y-%m-%dT%H:%M:%S"), "chaveExterna": chave,
                                    "disciplina": disciplina, "assunto": nome, "parte": l["subitem"],
                                    "motivo": l["motivo"]}, ensure_ascii=False) + "\n")
        log.info("%s: %d parte(s) sem material (lacunas-parciais.jsonl).", nome, len(lacunas))

    def ensaiar(self, nome, disciplina, saida=print, busca="nova", sem_ia=False):
        """Mostra os candidatos e a escolha da IA para um assunto, sem fatiar de verdade nem
        importar — para avaliar a qualidade da triagem (python worker.py --ensaiar).
        `busca="antiga"` usa a busca de antes (nome inteiro, um recorte), para comparar;
        `sem_ia` só lista os candidatos, sem gastar cota."""
        import re
        partes = triagem_ia.partes_do_assunto(nome)
        if busca == "antiga":
            candidatos = self.acervo.candidatos(termos_de_busca(nome), disciplina=disciplina)
        else:
            candidatos = self.acervo.candidatos_por_partes(partes, disciplina=disciplina)
        saida(f"== {disciplina} — {nome}: {len(candidatos)} arquivo(s) candidato(s) (busca {busca})")
        for i, c in enumerate(candidatos, 1):
            paginas = [p["pagina"] for p in c["paginas"]]
            faixa = f"p. {min(paginas)}–{max(paginas)}" if paginas else "-"
            saida(f"   [A{i}] {c['arquivo'][-90:]}  ({len(paginas)} págs. citadas, {faixa})")
            if c.get("partes"):
                saida(f"        achado para: {'; '.join(c['partes'])[:150]}")
        if busca != "antiga":
            sem = [p for p in partes if not any(p in c.get("partes", []) for c in candidatos)]
            saida(f"   partes sem nenhum candidato: {'; '.join(sem) if sem else 'nenhuma'}")
        if not candidatos or sem_ia:
            return
        tipo, valor = triagem_ia.interpretar(
            self.sge.completar(triagem_ia.SISTEMA, triagem_ia.montar_pedido(nome, disciplina, partes, candidatos)),
            candidatos)
        if tipo == "sem_material":
            saida(f"   sem material: {valor}")
            return
        for f in valor["fontes"]:
            numeros = [int(n) for n in re.findall(r"\d+", f["paginas"])] or [0]
            saida(f"   {f['tipo']:<8} {f['paginas']:<10} {f['arquivo'][-70:]}")
            saida(f"      cobre:  {'; '.join(f['cobre'])[:120]}")
            saida(f"      início: {self.acervo.inicio(f['arquivo'], numeros[0])[:80]}")
            saida(f"      fim:    {self.acervo.inicio(f['arquivo'], numeros[-1])[:80]}")
        for l in valor["lacunas"]:
            saida(f"   lacuna: {l['subitem']} — {l['motivo']}")
        try:
            manifesto = self._manifesto("ensaio", "ensaio", disciplina, nome, partes, valor)
            caminho = self.trabalho_dir / "ensaio.json"
            caminho.parent.mkdir(parents=True, exist_ok=True)
            caminho.write_text(json.dumps(manifesto, ensure_ascii=False), encoding="utf-8")
            _, segmentos = mb.montar_bloco(caminho, self.trabalho_dir / "ensaio", refatiar=True, so_validar=True)
            saida(f"   validação: ok, {len(segmentos)} segmento(s), "
                  f"~{sum(s['tempo_estimado_min'] for s in segmentos)} min")
        except mb.ManifestoInvalido as e:
            saida("   validação: recusada — " + "; ".join(e.erros[:3]))

    def _manifesto(self, chave, edital, disciplina, nome, partes, escolha):
        return {
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

    def _fatiar(self, chave, edital, disciplina, nome, partes, escolha):
        manifesto = self._manifesto(chave, edital, disciplina, nome, partes, escolha)
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
    ap.add_argument("--ensaiar", metavar="ASSUNTO",
                    help="Mostra a escolha da IA para um assunto, sem fatiar nem importar")
    ap.add_argument("--disciplina", default="", help="Disciplina do assunto de --ensaiar")
    ap.add_argument("--busca", choices=("nova", "antiga"), default="nova",
                    help="--ensaiar com a busca por parte (nova) ou a de antes (antiga), para comparar")
    ap.add_argument("--sem-ia", action="store_true", help="--ensaiar só lista os candidatos, sem chamar a IA")
    args = ap.parse_args()

    env = os.environ
    faltando = [v for v in ("INTERNAL_TOKEN", "ACERVO_DIR", "INDICE_DB", "MATERIAL_DIR") if not env.get(v)]
    if faltando:
        log.error("Configure: %s", ", ".join(faltando))
        sys.exit(1)
    material = env["MATERIAL_DIR"]
    sge = SgeApi(env.get("SGE_URL", "http://app:8080"), env["INTERNAL_TOKEN"])
    worker = Worker(
        sge,
        Acervo(env["INDICE_DB"], env["ACERVO_DIR"]),
        material,
        env.get("TRABALHO_DIR", str(Path(material) / ".manifestos")),
        int(env.get("MAX_POR_CICLO", "10")),
    )
    if args.ensaiar:
        worker.ensaiar(args.ensaiar, args.disciplina, busca=args.busca, sem_ia=args.sem_ia)
        return
    # Sprint 24 do SGE: provas e gabaritos. Só liga se PROVAS_DIR existir (o volume `provas`).
    provas = None
    if env.get("PROVAS_DIR"):
        from prova_pdf import Tesseract
        from prova_worker import WorkerProvas
        provas = WorkerProvas(sge, env["PROVAS_DIR"], material,
                              Tesseract(env.get("OCR_IDIOMA", "por"), int(env.get("OCR_PSM", "3"))))
    # Sprint 25 do SGE: leitura do edital (partes e nós). Só liga se EDITAIS_DIR existir (o volume `editais`).
    editais = None
    if env.get("EDITAIS_DIR"):
        from edital_worker import WorkerEditais
        editais = WorkerEditais(sge, env["EDITAIS_DIR"], env.get("TRABALHO_DIR", str(Path(material) / ".manifestos")))
    intervalo = int(env.get("INTERVALO_SEG", "300"))
    while True:
        for ciclo in filter(None, (editais.ciclo if editais else None, worker.ciclo, provas.ciclo if provas else None)):
            try:
                ciclo()
            except ErroSge as e:
                log.warning("SGE indisponível: %s", e)
        if args.uma_vez:
            break
        time.sleep(intervalo)


if __name__ == "__main__":
    main()
