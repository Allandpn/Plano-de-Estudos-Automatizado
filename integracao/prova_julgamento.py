#!/usr/bin/env python3
"""
prova_julgamento.py — O material do assunto sustenta a alternativa do gabarito? (Sprint 24 do
SGE-Concursos, ADR-046; D-68, D-69 e D-75 do SGE.)

Para cada questão, o worker junta o texto das páginas dos segmentos ATIVOS do assunto (os PDFs que
ele mesmo gerou, em MATERIAL_DIR), escolhe as poucas páginas mais próximas da questão e da
alternativa do gabarito por busca (índice FTS5 em memória, por assunto) e pergunta à IA o veredito.
Mandar o texto inteiro de segmentos de 200 páginas estouraria o contexto e a cota.

O critério é a **alternativa do gabarito**: as erradas podem usar fatos que nenhum PDF traz, e isso
não é furo (D-68). Quem aceita o veredito é o sistema: `RESPONDIVEL` só vale com uma página que
foi das oferecidas à IA — senão rebaixa para `NAO_RESPONDIVEL`. Na dúvida, o pior (D-69).
Sem segmento, ou sem página que cite os termos, o veredito é `NAO_RESPONDIVEL` sem gastar IA.
"""

import logging
import sqlite3
from pathlib import Path

import fitz  # PyMuPDF

from acervo import termos_de_busca
from ia_comum import completar_json

log = logging.getLogger("prova_julgamento")

PAGINAS_POR_QUESTAO = 6
MAX_TERMOS = 14
MAX_CARACTERES_PAGINA = 2500
TENTATIVAS_IA = 2
VEREDITOS = ("RESPONDIVEL", "PARCIAL", "NAO_RESPONDIVEL")

SISTEMA = """Você julga se o material de estudo de um assunto permite justificar a alternativa CORRETA (o gabarito)
de uma questão de prova de concurso. Recebe a questão, a alternativa do gabarito e algumas páginas do
material do assunto.

Regras:
- O que importa é a alternativa do GABARITO. As alternativas erradas podem usar fatos que nenhum material
  traz, e isso NÃO é falta do material.
- "Marque a incorreta" (ou "errada"): a alternativa do gabarito é a FALSA; basta o material permitir
  reconhecê-la como falsa.
- Certo/errado: o gabarito é C (certo) ou E (errado); o material sustenta se permite decidir o item nesse sentido.
- Questão de cálculo: o material precisa ensinar o MÉTODO, não só o conceito.
- "RESPONDIVEL" só se uma das PÁGINAS LISTADAS ensina o necessário para justificar a alternativa do gabarito;
  cite essa página pelo id exato (ex.: "S12-p3"). Não cite página que não foi listada.
- "PARCIAL": o material ensina parte; diga em "falta" o que não está nas páginas.
- "NAO_RESPONDIVEL": as páginas não trazem o necessário; diga em "falta" o que seria preciso.
- Na dúvida, escolha o PIOR dos dois vereditos.

Responda só JSON:
{"veredito": "RESPONDIVEL", "pagina": "S12-p3", "falta": null}"""


# ---------------------------------------------------------------- as páginas do assunto

class PaginasDoAssunto:
    """O texto das páginas dos segmentos ativos de um assunto, com busca por FTS5 em memória."""

    def __init__(self, segmentos, material_dir):
        self._db = sqlite3.connect(":memory:")
        self._db.execute("CREATE VIRTUAL TABLE p USING fts5(texto, seg UNINDEXED, pag UNINDEXED, "
                         "tokenize='unicode61 remove_diacritics 2')")
        self.total = 0
        self.ilegiveis = []
        for s in segmentos:
            caminho = Path(material_dir) / s["arquivo"].removeprefix("/material/")
            try:
                with fitz.open(str(caminho)) as doc:
                    for numero, pagina in enumerate(doc, 1):
                        texto = pagina.get_text().strip()
                        if texto:
                            self._db.execute("INSERT INTO p (texto, seg, pag) VALUES (?, ?, ?)", (texto, s["id"], numero))
                            self.total += 1
            except Exception as e:  # PyMuPDF lança vários tipos para arquivo ausente ou corrompido
                self.ilegiveis.append(str(caminho))
                log.warning("segmento %s ilegível (%s): %s", s["id"], caminho, e)

    def buscar(self, termos, k=PAGINAS_POR_QUESTAO):
        """As `k` páginas que mais combinam com os termos: [(segmento_id, pagina_no_segmento, texto)]."""
        termos = sorted(set(termos), key=len, reverse=True)[:MAX_TERMOS]
        if not termos:
            return []
        consulta = " OR ".join(f'"{t}"*' for t in termos)
        linhas = self._db.execute("SELECT seg, pag, texto FROM p WHERE p MATCH ? ORDER BY bm25(p) LIMIT ?", (consulta, k))
        return list(linhas)


# ---------------------------------------------------------------- o pedido e a resposta

def _alternativa_do_gabarito(q, formato):
    letra = q.get("respostaGabarito")
    if formato == "CERTO_ERRADO":
        return letra, "Certo" if letra == "C" else "Errado"
    texto = next((a["texto"] for a in q.get("alternativas") or [] if a["letra"] == letra), "")
    return letra, texto


def termos_da_questao(q, formato):
    """O que procurar: o enunciado e a alternativa do gabarito (é ela que o material tem de sustentar)."""
    _, texto = _alternativa_do_gabarito(q, formato)
    base = " ".join(filter(None, [q.get("enunciado"), texto if formato != "CERTO_ERRADO" else ""]))
    return termos_de_busca(base)


def montar_pedido(q, formato, candidatas, erros_anteriores=None):
    letra, texto = _alternativa_do_gabarito(q, formato)
    linhas = [f"Assunto: {q['assunto']['nome']} ({q['assunto']['disciplina']})", ""]
    if q.get("textoBase"):
        linhas += ["TEXTO-BASE DO ITEM:", q["textoBase"].strip(), ""]
    linhas += ["QUESTÃO:", (q.get("enunciado") or "").strip()]
    for a in q.get("alternativas") or []:
        linhas.append(f"({a['letra']}) {a['texto']}")
    linhas += ["", f"ALTERNATIVA DO GABARITO: {letra}" + (f" — {texto}" if texto else ""), "", "PÁGINAS DO MATERIAL:"]
    for seg, pag, conteudo in candidatas:
        linhas.append(f"\n[S{seg}-p{pag}]\n{conteudo.strip()[:MAX_CARACTERES_PAGINA]}")
    if erros_anteriores:
        linhas.append("\nSua resposta anterior foi recusada. Corrija:")
        linhas += [f"- {e}" for e in erros_anteriores]
    return "\n".join(linhas)


def interpretar(dados, oferecidas):
    """A resposta da IA -> (veredito, (segmento, pagina) ou None, falta ou None). `oferecidas` são os
    (segmento, pagina) que foram mostrados à IA: RESPONDIVEL com página fora delas rebaixa para
    NAO_RESPONDIVEL (D-68, D-69). Lança ValueError se o formato não serve."""
    if not isinstance(dados, dict):
        raise ValueError("a resposta não é um objeto JSON")
    veredito = str(dados.get("veredito", "")).strip().upper()
    if veredito not in VEREDITOS:
        raise ValueError(f"veredito inválido: {dados.get('veredito')!r} (esperado {', '.join(VEREDITOS)})")
    falta = dados.get("falta")
    falta = falta.strip() if isinstance(falta, str) and falta.strip() else None
    citada = _pagina_citada(dados.get("pagina"))
    if citada is not None and citada not in oferecidas:
        if veredito == "RESPONDIVEL":
            return "NAO_RESPONDIVEL", None, "A IA citou uma página que não estava entre as oferecidas; sem sustentação válida."
        citada = None
    if veredito == "RESPONDIVEL" and citada is None:
        return "NAO_RESPONDIVEL", None, "A IA disse que o material sustenta a resposta, mas não citou a página."
    if veredito == "NAO_RESPONDIVEL":
        citada = None
    return veredito, citada, falta


def _pagina_citada(texto):
    """"S12-p3" -> (12, 3); qualquer outra coisa -> None."""
    if not isinstance(texto, str):
        return None
    t = texto.strip().strip("[]").upper()
    if not t.startswith("S") or "-P" not in t:
        return None
    seg, _, pag = t[1:].partition("-P")
    return (int(seg), int(pag)) if seg.isdigit() and pag.isdigit() else None


class JulgamentoFalhou(Exception):
    """A IA respondeu, mas duas vezes sem um veredito legível. Não é veredito (D-75): quem chama
    decide quando desistir da questão."""


def _item(q, veredito, citada, falta):
    return {"numero": q["numero"], "veredito": veredito,
            "segmentoId": citada[0] if citada else None, "paginaSegmento": citada[1] if citada else None,
            "falta": falta}


class Julgador:
    """Julga questões de uma prova contra o material dos assuntos. Guarda o índice de páginas de cada
    assunto enquanto durar (os PDFs dos segmentos não mudam no meio de um ciclo)."""

    def __init__(self, sge, material_dir):
        self.sge = sge
        self.material_dir = material_dir
        self._por_assunto = {}

    def _paginas(self, assunto):
        chave = (assunto["id"], tuple(s["id"] for s in assunto["segmentos"]))
        if chave not in self._por_assunto:
            self._por_assunto[chave] = PaginasDoAssunto(assunto["segmentos"], self.material_dir)
        return self._por_assunto[chave]

    def julgar(self, q, formato):
        """O veredito de uma questão: {numero, veredito, segmentoId, paginaSegmento, falta}.
        IaIndisponivel sobe (D-75); JulgamentoFalhou também, sem veredito."""
        assunto = q["assunto"]
        if not assunto["segmentos"]:
            return _item(q, "NAO_RESPONDIVEL", None, "O assunto não tem material (sem segmentos ativos).")
        paginas = self._paginas(assunto)
        if paginas.total == 0:
            return _item(q, "NAO_RESPONDIVEL", None, "O material do assunto não pôde ser lido (PDF sem texto ou ausente).")
        candidatas = paginas.buscar(termos_da_questao(q, formato))
        if not candidatas:
            return _item(q, "NAO_RESPONDIVEL", None, "Nenhuma página do material cita os termos da questão.")
        oferecidas = {(seg, pag) for seg, pag, _ in candidatas}
        erros = None
        for _ in range(TENTATIVAS_IA):
            try:
                resposta = completar_json(self.sge, SISTEMA, montar_pedido(q, formato, candidatas, erros))
                return _item(q, *interpretar(resposta, oferecidas))
            except ValueError as e:
                erros = [str(e)]
        raise JulgamentoFalhou(f"a IA não devolveu um veredito legível para a questão {q['numero']}: {erros[0]}")
