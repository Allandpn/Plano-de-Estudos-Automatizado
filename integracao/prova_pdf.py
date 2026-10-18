#!/usr/bin/env python3
"""
prova_pdf.py — Do PDF da prova às linhas de texto, com OCR quando o PDF é imagem
(Sprint 24 do SGE-Concursos, ADR-046; docs/SPRINT-24-PROVA-GABARITO.md §8 de lá).

Duas origens, e as bancas entregam as duas:
  - PDF com texto (FGV, CEBRASPE): o texto da página, na ordem de leitura.
  - PDF só de imagem (IDECAN, FCC): OCR com o Tesseract. A prova da FCC chega como UMA página
    de 595 x 8772 pt com 12 imagens empilhadas, e as imagens são fatias da tira — cortam
    questões no meio. Por isso o OCR não é por imagem: renderiza a página por **bandas com
    sobreposição** e, de cada banda, guarda só as linhas que "pertencem" a ela (a posição do
    centro da linha decide). Uma linha partida pela emenda de uma banda é inteira na vizinha,
    então nada some e nada se repete (ponto L da especificação).

Cada linha lida por OCR leva a confiança média das palavras: é o que o segmentador usa para
dizer "isto é duvidoso" quando o OCR leu mal código ou algarismos romanos (D-85 do SGE).
As imagens das páginas vão para `<pasta_paginas>/NN.jpg`, para o usuário conferir (D-85).
"""

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

DPI = 200
BANDA_PX = 2048
SOBREPOSICAO_PX = 256
# Abaixo disso a página não tem texto de verdade (capa escaneada com um carimbo, por exemplo).
MIN_CARACTERES_PAGINA = 80
# O documento só é "de imagem" se menos que isto das páginas tiver texto.
MIN_FRACAO_COM_TEXTO = 0.5
# Uma imagem só conta como "página escaneada" se for grande; logotipos ficam de fora.
MIN_ALTURA_IMAGEM_PT = 150
MIN_LARGURA_RELATIVA = 0.5


class ProvaIlegivel(Exception):
    """A prova não pode ser lida (PDF inválido, imagem sem OCR, nenhuma questão). Vira falha da
    etapa no SGE, com o motivo — ao contrário de IaIndisponivel, que só espera."""


@dataclass
class Linha:
    texto: str
    pagina: int            # página do PDF
    imagem: int | None     # índice (1-based) da imagem salva em paginas/NN.jpg; None se é texto nativo
    confianca: float | None  # média das palavras no OCR (0 a 100); None no texto nativo

    @property
    def ocr(self):
        return self.confianca is not None


@dataclass
class LeituraPdf:
    linhas: list
    usou_ocr: bool
    imagens: list          # nomes dos arquivos salvos em pasta_paginas, na ordem (01.jpg, 02.jpg...)


# ---------------------------------------------------------------- Tesseract

class Tesseract:
    """O Tesseract de linha de comando. `rodar` existe para os testes trocarem o subprocesso."""

    def __init__(self, idioma="por", psm=3, executavel="tesseract", rodar=subprocess.run):
        self.idioma = idioma
        self.psm = psm
        self.executavel = executavel
        self._rodar = rodar

    def disponivel(self):
        return shutil.which(self.executavel) is not None

    def tsv(self, png):
        """O TSV (uma linha por palavra, com caixa e confiança) do OCR de uma imagem PNG."""
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "banda.png"
            arquivo.write_bytes(png)
            try:
                r = self._rodar([self.executavel, str(arquivo), "stdout", "-l", self.idioma, "--psm", str(self.psm), "tsv"],
                                capture_output=True, text=True, encoding="utf-8", timeout=300)
            except FileNotFoundError:
                raise ProvaIlegivel("O OCR (Tesseract) não está instalado neste servidor.") from None
            except subprocess.TimeoutExpired:
                raise ProvaIlegivel("O OCR demorou demais numa página.") from None
        if r.returncode != 0:
            raise ProvaIlegivel(f"O OCR falhou: {(r.stderr or '').strip()[:300]}")
        return r.stdout


def linhas_do_tsv(tsv):
    """O TSV do Tesseract -> [(texto, topo_px, base_px, confianca_media)] na ordem de leitura que
    ele emitiu (bloco, parágrafo, linha) — que respeita colunas. Palavras vazias ou sem confiança
    (conf < 0, ruído) ficam de fora."""
    linhas = {}
    ordem = []
    for bruta in tsv.splitlines()[1:]:
        c = bruta.split("\t")
        if len(c) < 12 or c[0] != "5":
            continue
        texto = c[11].strip()
        confianca = float(c[10])
        if not texto or confianca < 0:
            continue
        chave = (int(c[2]), int(c[3]), int(c[4]))
        topo, base = int(c[7]), int(c[7]) + int(c[9])
        if chave not in linhas:
            linhas[chave] = {"palavras": [], "topo": topo, "base": base, "conf": []}
            ordem.append(chave)
        linha = linhas[chave]
        linha["palavras"].append((int(c[5]), texto))
        linha["topo"], linha["base"] = min(linha["topo"], topo), max(linha["base"], base)
        linha["conf"].append(confianca)
    resultado = []
    for chave in ordem:
        linha = linhas[chave]
        palavras = " ".join(t for _, t in sorted(linha["palavras"]))
        resultado.append((palavras, linha["topo"], linha["base"], sum(linha["conf"]) / len(linha["conf"])))
    return resultado


def bandas(altura_px, banda=BANDA_PX, sobreposicao=SOBREPOSICAO_PX):
    """As faixas [(y0, y1)] em que uma página de `altura_px` é renderizada. Página que cabe numa
    banda e meia vai inteira; as demais, em faixas que se sobrepõem em `sobreposicao` px."""
    if altura_px <= banda * 1.25:
        return [(0, altura_px)]
    passo = banda - sobreposicao
    faixas, y = [], 0
    while True:
        fim = min(y + banda, altura_px)
        faixas.append((y, fim))
        if fim >= altura_px:
            return faixas
        y += passo


def unir_bandas(faixas, linhas_por_banda, sobreposicao=SOBREPOSICAO_PX):
    """Junta o OCR das bandas sem repetir nem perder linha: a banda k é dona da faixa que vai de
    (y0 de k + meia sobreposição) até (y0 de k+1 + meia sobreposição); só as linhas cujo centro cai
    nela entram. A linha que a emenda partiu (centro perto da borda da banda) cai na dona vizinha,
    onde está inteira. A ordem de leitura do Tesseract dentro de cada banda é preservada.
    -> [(texto, y_centro_px_na_pagina, confianca)]"""
    meia = sobreposicao / 2
    saida = []
    for k, (y0, _) in enumerate(faixas):
        inicio = float("-inf") if k == 0 else y0 + meia
        fim = float("inf") if k == len(faixas) - 1 else faixas[k + 1][0] + meia
        for texto, topo, base, confianca in linhas_por_banda[k]:
            centro = y0 + (topo + base) / 2
            if inicio <= centro < fim:
                saida.append((texto, centro, confianca))
    return saida


def ocr_pagina(pagina, tesseract, dpi=DPI):
    """OCR de uma página do PyMuPDF, por bandas: [(texto, y_centro_em_pontos, confianca)]."""
    escala = dpi / 72
    altura_px = int(pagina.rect.height * escala)
    faixas = bandas(altura_px)
    por_banda = []
    for y0, y1 in faixas:
        clip = fitz.Rect(0, y0 / escala, pagina.rect.width, y1 / escala)
        png = pagina.get_pixmap(dpi=dpi, clip=clip).tobytes("png")
        por_banda.append(linhas_do_tsv(tesseract.tsv(png)))
    return [(t, y / escala, c) for t, y, c in unir_bandas(faixas, por_banda)]


# ---------------------------------------------------------------- imagens das páginas (D-85)

def _imagens_da_pagina(pagina):
    """As imagens grandes da página, de cima para baixo: [(xref, y0_pt, y1_pt)]."""
    achadas = []
    for info in pagina.get_image_info(xrefs=True):
        x0, y0, x1, y1 = info["bbox"]
        if (y1 - y0) >= MIN_ALTURA_IMAGEM_PT and (x1 - x0) >= pagina.rect.width * MIN_LARGURA_RELATIVA and info.get("xref"):
            achadas.append((info["xref"], y0, y1))
    return sorted(achadas, key=lambda i: i[1])


def _salvar_imagem(doc, pagina, xref, pasta, numero):
    """Grava a imagem da página como NN.jpg (ou NN.png) e devolve o nome. Prefere a imagem
    original embutida; se o formato não serve ao navegador, renderiza."""
    pasta.mkdir(parents=True, exist_ok=True)
    extraida = doc.extract_image(xref) if xref else None
    if extraida and extraida["ext"] in ("jpg", "jpeg", "png"):
        nome = f"{numero:02d}.{'png' if extraida['ext'] == 'png' else 'jpg'}"
        (pasta / nome).write_bytes(extraida["image"])
        return nome
    nome = f"{numero:02d}.jpg"
    pagina.get_pixmap(dpi=110).save(str(pasta / nome))
    return nome


# ---------------------------------------------------------------- a leitura

def ler_prova(caminho, pasta_paginas, tesseract):
    """O PDF da prova -> linhas de texto na ordem de leitura. Página com texto usa o texto; página
    de imagem usa OCR (e guarda a imagem em pasta_paginas, para o usuário conferir, D-85)."""
    try:
        doc = fitz.open(str(caminho))
    except Exception as e:  # PyMuPDF lança vários tipos para arquivo corrompido
        raise ProvaIlegivel(f"O PDF da prova não pôde ser aberto: {e}") from None
    pasta = Path(pasta_paginas)
    linhas, imagens, usou_ocr = [], [], False
    textos = [p.get_text() for p in doc]
    com_texto = sum(1 for texto in textos if len(texto.strip()) >= MIN_CARACTERES_PAGINA)
    # A decisão é do documento, não da página: uma prova de texto tem páginas em branco e de figura
    # (a FGV tem), e isso não a transforma em imagem. Só quando a maioria das páginas não tem
    # texto é que o OCR entra, e então entra em toda página sem texto.
    documento_de_imagem = com_texto < len(textos) * MIN_FRACAO_COM_TEXTO
    for numero, (pagina, texto) in enumerate(zip(doc, textos), 1):
        if len(texto.strip()) >= MIN_CARACTERES_PAGINA:
            linhas += [Linha(l.rstrip(), numero, None, None) for l in texto.splitlines() if l.strip()]
            continue
        if not documento_de_imagem:
            continue  # página em branco ou só de figura numa prova de texto
        if not tesseract.disponivel():
            raise ProvaIlegivel("A prova é uma imagem e o OCR (Tesseract) não está instalado neste servidor.")
        usou_ocr = True
        grandes = _imagens_da_pagina(pagina)
        indices = []
        if grandes:
            for xref, y0, y1 in grandes:
                imagens.append(_salvar_imagem(doc, pagina, xref, pasta, len(imagens) + 1))
                indices.append((len(imagens), y0, y1))
        else:
            imagens.append(_salvar_imagem(doc, pagina, None, pasta, len(imagens) + 1))
            indices.append((len(imagens), 0, pagina.rect.height))
        for texto_ocr, y_pt, confianca in ocr_pagina(pagina, tesseract):
            if texto_ocr.strip():
                linhas.append(Linha(texto_ocr, numero, _imagem_em(indices, y_pt), confianca))
    doc.close()
    return LeituraPdf(linhas, usou_ocr, imagens)


def _imagem_em(indices, y_pt):
    """O índice da imagem que cobre a posição vertical (a mais próxima, se cair numa emenda)."""
    for indice, y0, y1 in indices:
        if y0 <= y_pt < y1:
            return indice
    return min(indices, key=lambda i: min(abs(y_pt - i[1]), abs(y_pt - i[2])))[0]


def texto_do_arquivo(caminho):
    """O texto de um gabarito (PDF com texto, ou .txt colado pelo usuário), página a página."""
    caminho = Path(caminho)
    if caminho.suffix.lower() == ".txt":
        return [caminho.read_text(encoding="utf-8", errors="replace")]
    try:
        doc = fitz.open(str(caminho))
    except Exception as e:
        raise ProvaIlegivel(f"O PDF do gabarito não pôde ser aberto: {e}") from None
    paginas = [p.get_text() for p in doc]
    doc.close()
    if not any(p.strip() for p in paginas):
        raise ProvaIlegivel("O gabarito não tem texto (é uma imagem). Envie o PDF com texto ou cole o gabarito.")
    return paginas
