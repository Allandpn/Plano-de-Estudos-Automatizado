#!/usr/bin/env python3
"""PDF anexado a uma lacuna do material (D-97, ADR-049 do SGE; docs/SPRINT-28-PDF-ANEXADO-A-LACUNA.md).

A pessoa anexa, no SGE, o PDF de uma parte que o acervo não ensina (a lei do órgão, por exemplo). O SGE o guarda no volume
`editais`; este ciclo o corta em segmentos de ~60 min com `dias/montar_bloco.py`, importa pelo caminho de sempre (CSV de segmentos
ligado ao assunto pela chave externa) e devolve o resultado. Nada que o assunto já tem é apagado: os segmentos novos entram depois,
com a `ordem` continuando a numeração (`proximaOrdem`).
"""
import logging
import tempfile
from pathlib import Path

from edital_worker import csv_dos_segmentos
from sge_api import ErroSge

log = logging.getLogger("anexo_worker")

MINUTOS_POR_PAGINA = 3   # texto de lei é leitura corrida, não teoria densa


def manifesto_do_anexo(pendente, arquivo):
    """Um manifesto de uma fonte só, com todas as páginas. O `assunto_uuid` e o título levam o id do anexo: cada anexo tem o seu
    próprio destino (`blocos/<título>`) e nunca se confunde com os segmentos que o assunto já tem."""
    parte = pendente["parte"]
    return {
        "assunto_uuid": f"anexo-{pendente['id']}",
        "edital": "anexo",
        "titulo": f"{pendente['assunto'][:80]} — anexo {pendente['id']}",
        "minutos_por_pagina": MINUTOS_POR_PAGINA,
        "subitens": [parte],
        "lacunas": [],
        "descartes": [],
        "fontes": [{"arquivo": str(arquivo), "paginas": f"1-{pendente['paginas']}", "rotulo": pendente.get("nome") or "PDF anexado",
                    "cobre": [parte], "tipo": "teoria"}],
    }


class AnexosDeLacuna:
    def __init__(self, sge, editais_dir, material_dir, fatiador=None):
        self.sge = sge
        self.editais = Path(editais_dir)
        self.material = Path(material_dir)
        self.fatiador = fatiador  # só os testes trocam o fatiador de PDF

    def ciclo(self):
        """Prepara os anexos pendentes, um a um; falha de um não para os outros. Devolve quantos ficaram prontos."""
        prontos = 0
        for pendente in self.sge.anexos_pendentes():
            try:
                self.processar(pendente)
                prontos += 1
            except ErroSge:
                raise  # o SGE fora do ar não é culpa do PDF: tenta de novo no próximo ciclo
            except Exception as e:  # noqa: BLE001 — o motivo vai para a pessoa, que pode anexar de novo
                log.warning("Anexo %s falhou: %s", pendente.get("id"), e)
                self.sge.anexo_falha(pendente["id"], str(e)[:400] or e.__class__.__name__)
        return prontos

    def processar(self, pendente):
        arquivo = (self.editais / pendente["arquivo"]).resolve()
        if not str(arquivo).startswith(str(self.editais.resolve())) or not arquivo.is_file():
            raise FileNotFoundError("o PDF anexado não está no volume do servidor")
        fatiar = self.fatiador
        if fatiar is None:
            import montar_bloco as mb
            fatiar = lambda manifesto, destino: mb.montar_bloco(manifesto, destino, refatiar=True)[1]  # noqa: E731
        import json
        with tempfile.TemporaryDirectory() as pasta:
            manifesto = Path(pasta) / "manifesto.json"
            manifesto.write_text(json.dumps(manifesto_do_anexo(pendente, arquivo), ensure_ascii=False), encoding="utf-8")
            segmentos = fatiar(manifesto, self.material)
        for deslocamento, sg in enumerate(segmentos):
            sg["ordem"] = pendente["proximaOrdem"] + deslocamento
        self.sge.importar_segmentos(csv_dos_segmentos(pendente["chaveExterna"], segmentos))
        minutos = sum(sg["tempo_estimado_min"] for sg in segmentos)
        self.sge.anexo_pronto(pendente["id"], len(segmentos), minutos)
        log.info("Anexo %s virou %d segmento(s), %d min.", pendente["id"], len(segmentos), minutos)
