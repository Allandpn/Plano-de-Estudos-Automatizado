#!/usr/bin/env python3
"""Pipeline único: do PDF do edital aos manifestos de material, às questões por assunto e à entrega da revisão ao SGE.

    python integracao/preparar_edital.py EDITAL.pdf --slug alesc-2024 --cargo "Analista de Sistemas" --saida DIR \\
        --db catalogo.db --fichas fichas-nos.jsonl --acervo /acervo/apostilas [--modo completo|compacto] [--esperar]

Etapas, cada uma gravando um arquivo em `<saida>/<slug>/` (rodar de novo pula as que já têm saída; `--refazer ETAPA` refaz
aquela e todas as seguintes; `--ate ETAPA` para depois dela):

  extrair     regra   texto do conteúdo programático                         → extraido.json
  quebrar     IA      disciplinas, assuntos e partes, conferidos por regra    → partes.json, fora.json
  ligar       IA      partes → nós do QConcursos (decisões aprovadas primeiro) → nos.json, disciplinas.json
  casar       regra   partes ↔ temas das fichas, pelos nós                   → material.json
  confirmar   IA      quais candidatos ensinam a parte                       → confirmado.json
  manifestos  regra   um manifesto por assunto, validado pelo fatiador       → manifestos/, questoes/, assuntos.json, relatorio.md
  entrega     regra   o JSON "edital-revisao/1" para o SGE                   → entrega.json

As etapas com IA usam o proxy do SGE (SGE_URL e INTERNAL_TOKEN). `--esperar` dorme até o horário que a assinatura indicar
quando o limite de uso acaba, e continua de onde parou na etapa.
"""
import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dias"))

ETAPAS = ["extrair", "quebrar", "ligar", "casar", "confirmar", "manifestos", "entrega"]
SAIDA_DA_ETAPA = {"extrair": "extraido.json", "quebrar": "partes.json", "ligar": "nos.json", "casar": "material.json",
                  "confirmar": "confirmado.json", "manifestos": "relatorio.md", "entrega": "entrega.json"}


class ErroDeEtapa(Exception):
    """A etapa não pode continuar (por exemplo, o PDF não traz o conteúdo programático)."""


class Contexto:
    def __init__(self, pdf, slug, cargo, pasta, db=None, fichas=None, acervo=None, modo="completo", decisoes=None,
                 sge=None, esperar=False, log=print):
        self.pdf, self.slug, self.cargo, self.pasta = pdf, slug, cargo, Path(pasta)
        self.db, self.fichas, self.acervo, self.modo = db, fichas, acervo, modo
        self.decisoes, self.sge, self.esperar, self.log = decisoes, sge, esperar, log

    def arquivo(self, nome):
        return self.pasta / nome

    def ler(self, nome):
        return json.loads(self.arquivo(nome).read_text(encoding="utf-8"))

    def gravar(self, nome, dados):
        self.pasta.mkdir(parents=True, exist_ok=True)
        self.arquivo(nome).write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")


def com_espera(ctx, funcao):
    """Roda `funcao()`; se a IA parar por limite de uso e `--esperar`, dorme até liberar e tenta de novo (a função precisa
    continuar de onde parou)."""
    from catalogo_aulas import segundos_ate_liberar
    from ia_comum import IaIndisponivel
    while True:
        try:
            return funcao()
        except IaIndisponivel as e:
            if not ctx.esperar:
                raise
            espera = segundos_ate_liberar(str(e))
            ctx.log(f"A IA parou ({e}); espero {espera // 60} min")
            time.sleep(espera)


# ------------------------------------------------------------------------------------------------------ etapas

def etapa_extrair(ctx):
    import partes_edital as pe
    try:
        dados = pe.extrair(ctx.pdf)
    except pe.ProgramaNaoEncontrado as e:
        raise ErroDeEtapa(str(e)) from None
    ctx.gravar("extraido.json", dados)
    return f"{len(dados['linhas'])} linhas do conteúdo programático"


def etapa_quebrar(ctx):
    import partes_edital as pe
    extraido = ctx.ler("extraido.json")
    parcial = ctx.arquivo("partes.parcial.json")
    if ctx.arquivo("organizacao.json").exists():
        disciplinas = ctx.ler("organizacao.json")
    else:
        disciplinas = com_espera(ctx, lambda: pe.organizar(ctx.sge, extraido, ctx.cargo))
        ctx.gravar("organizacao.json", disciplinas)
    feitas = json.loads(parcial.read_text(encoding="utf-8")) if parcial.exists() else []
    prontas = {d["nome"] for d in feitas}
    for d in disciplinas:
        if d["nome"] in prontas:
            continue
        feitas.append(com_espera(ctx, lambda d=d: pe.quebrar_disciplina(ctx.sge, d)))
        parcial.write_text(json.dumps(feitas, ensure_ascii=False, indent=1), encoding="utf-8")  # retoma daqui
        ctx.log(f"  {d['nome']}: {len(feitas[-1]['assuntos'])} assuntos")
    fora = pe.linhas_fora(extraido, disciplinas)
    ctx.gravar("fora.json", fora)
    ctx.arquivo("partes.md").write_text(pe.relatorio(Path(ctx.pdf).name, ctx.cargo, feitas, fora), encoding="utf-8")
    ctx.gravar("partes.json", feitas)
    partes = sum(len(a.get("partes") or []) for d in feitas for a in d["assuntos"])
    return (f"{len(feitas)} disciplinas · {sum(len(d['assuntos']) for d in feitas)} assuntos · {partes} partes · "
            f"{sum(1 for d in feitas for a in d['assuntos'] if a['erros'])} recusados · {len(fora)} blocos fora")


def decisoes_padrao(arvore_nome):
    """As decisões aprovadas da árvore em uso (integracao/decisoes/<árvore>.json), se existirem."""
    f = Path(__file__).resolve().parent / "decisoes" / f"{arvore_nome}.json"
    if not f.exists():
        return []
    lido = json.loads(f.read_text(encoding="utf-8"))
    return lido["decisoes"] if isinstance(lido, dict) else lido


def descricao_da_disciplina(cargo, disciplina, quantos=12):
    """O que o nome da disciplina não diz: o cargo e os primeiros assuntos dela, para a IA achar a área no QConcursos."""
    amostra = "; ".join(a["texto"].strip(" .")[:70] for a in disciplina["assuntos"][:quantos])
    return f"cargo: {cargo}; assuntos: {amostra}"


def etapa_ligar(ctx):
    import mapear_partes as mp
    from casar_taxonomia import Arvore, carregar_arvore, ligar_com_ia, mapear_disciplinas, refinar
    disciplinas = ctx.ler("partes.json")
    disc, nome_arvore = carregar_arvore()
    arvore = Arvore(disc)
    mapa = json.loads(ctx.arquivo("disciplinas.json").read_text(encoding="utf-8")) if ctx.arquivo("disciplinas.json").exists() else {}
    faltam = [d["nome"] for d in disciplinas if not mapa.get(d["nome"])]  # mapa vazio vale como não mapeado: pergunta de novo
    if faltam:
        descricoes = {d["nome"]: descricao_da_disciplina(ctx.cargo, d) for d in disciplinas}
        mapa.update(com_espera(ctx, lambda: mapear_disciplinas(ctx.sge, faltam, arvore, descricoes)))
        ctx.gravar("disciplinas.json", mapa)
    itens, partes = mp.itens_das_partes(disciplinas, arvore, mapa)
    decisoes = decisoes_padrao(nome_arvore.replace(".json", ""))
    if ctx.decisoes:
        lido = json.loads(Path(ctx.decisoes).read_text(encoding="utf-8"))
        decisoes += lido["decisoes"] if isinstance(lido, dict) else lido
    aplicadas = mp.aplicar_decisoes(itens, decisoes)
    # sem nó (inclusive o que ficou assim por uma interrupção antes da segunda passada) entra de novo; o que já tem nó, não
    com_espera(ctx, lambda: ligar_com_ia(ctx.sge, [it for it in itens if not it.get("ia") and not it.get("decisao")], arvore,
                                         log=lambda *_: None))
    com_espera(ctx, lambda: refinar(ctx.sge, itens, arvore, log=lambda *_: None))
    ctx.gravar("nos.json", {"itens": itens, "partes": partes, "arvore": nome_arvore})
    ctx.arquivo("nos.md").write_text(mp.relatorio(ctx.slug, itens, partes, arvore, mapa), encoding="utf-8")
    sem = sum(1 for it in itens if not it.get("ia"))
    return f"{len(partes)} partes · {len(itens)} ligações · {aplicadas} por decisão aprovada · {sem} sem nó"


def etapa_casar(ctx):
    from casar_partes_fichas import montar_material
    from casar_taxonomia import Arvore, carregar_arvore
    arvore = Arvore(carregar_arvore()[0])
    temas = [json.loads(l) for l in Path(ctx.fichas).read_text(encoding="utf-8").splitlines() if l.strip()]
    material, por_nome = montar_material(arvore, ctx.ler("nos.json"), temas)
    ctx.gravar("material.json", material)
    com = sum(1 for it in material["itens"] if it["material"])
    return f"{com} de {len(material['itens'])} ligações com candidatos ({por_nome} só por nome)"


def etapa_confirmar(ctx):
    import confirmar_material as cm
    material = ctx.ler("material.json")
    itens = material["itens"]
    nos = ctx.ler("nos.json")["itens"]
    for it, base in zip(itens, nos):
        it["contexto"] = (base.get("termos") or [""])[0]
    cm.anexar_trechos(itens, material["partes"], ctx.ler("partes.json"))
    db = sqlite3.connect(f"file:{ctx.db}?mode=ro", uri=True)
    escolha = [i for i, it in enumerate(itens) if it["material"]]

    def rodar():
        pendentes = [(ctx.slug, itens[i]) for i in escolha if "confirmado" not in itens[i]]
        if pendentes and not cm.confirmar(ctx.sge, db, pendentes, log=lambda m: ctx.log("  " + m)):
            from ia_comum import IaIndisponivel
            raise IaIndisponivel("a assinatura parou durante a confirmação")
    com_espera(ctx, rodar)
    feitos = [dict(itens[i], indice=i) for i in escolha]
    ctx.gravar("confirmado.json", feitos)
    return cm.resumo(feitos)


def etapa_manifestos(ctx):
    import manifesto_do_casamento as mc
    db = sqlite3.connect(f"file:{ctx.db}?mode=ro", uri=True)
    cache = {}

    def ficha_de(caminho):
        if caminho not in cache:
            linha = db.execute("SELECT ficha FROM fichas WHERE caminho = ? AND situacao = 'ok'", (caminho,)).fetchone()
            cache[caminho] = json.loads(linha[0]) if linha else None
        return cache[caminho]
    import montar_bloco as mb
    import tempfile

    def validar(caminho):
        try:
            with tempfile.TemporaryDirectory() as t:
                mb.montar_bloco(caminho, t, refatiar=True, so_validar=True)
            return []
        except mb.ManifestoInvalido as e:
            return e.erros
    linhas = mc.processar(ctx.slug, ctx.ler("partes.json"), ctx.ler("material.json"), ctx.ler("confirmado.json"), ficha_de,
                          ctx.acervo, ctx.modo, validar, ctx.pasta)
    ctx.gravar("assuntos.json", linhas)
    texto = mc.relatorio(ctx.slug, ctx.modo, linhas)
    ctx.arquivo("relatorio.md").write_text(texto, encoding="utf-8")
    return texto.splitlines()[2]


def etapa_entrega(ctx):
    import entrega_revisao as er
    nos = ctx.ler("nos.json")
    mapa = ctx.ler("disciplinas.json") if ctx.arquivo("disciplinas.json").exists() else {}
    fora = ctx.ler("fora.json") if ctx.arquivo("fora.json").exists() else []
    entrega = er.montar_entrega(ctx.slug, ctx.cargo, Path(ctx.pdf).name, ctx.ler("partes.json"), nos, mapa, fora,
                                {"modo_de_material": ctx.modo}, nos.get("arvore", "qconcursos").replace(".json", ""))
    por_chave = {l["chave"]: l for l in ctx.ler("assuntos.json")} if ctx.arquivo("assuntos.json").exists() else {}
    for d in entrega["disciplinas"]:
        for a in d["assuntos"]:
            l = por_chave.get(a["chave"])
            if l:
                a["material"] = {"situacao": l["situacao"], "fontes": l["fontes"], "minutos": l["minutos"],
                                 "lacunas": l["lacunas"], "tem_questoes": l["tem_questoes"]}
    ctx.gravar("entrega.json", entrega)
    return json.dumps(entrega["resumo"], ensure_ascii=False)


FUNCOES = {"extrair": etapa_extrair, "quebrar": etapa_quebrar, "ligar": etapa_ligar, "casar": etapa_casar,
           "confirmar": etapa_confirmar, "manifestos": etapa_manifestos, "entrega": etapa_entrega}


def executar(ctx, ate=None, refazer=None, funcoes=None, etapas=None):
    """Roda as etapas em ordem. Pula a que já tem saída, salvo se for `refazer` ou vier depois dela. Devolve
    {etapa: resumo ou 'já feita'}."""
    funcoes, etapas = funcoes or FUNCOES, etapas or ETAPAS
    for nome in (ate, refazer):
        if nome and nome not in etapas:
            raise ValueError(f"etapa desconhecida: {nome!r} (as etapas são {', '.join(etapas)})")
    forcar = False
    resultado = {}
    for nome in etapas:
        if nome == refazer:
            forcar = True
        if not forcar and ctx.arquivo(SAIDA_DA_ETAPA[nome]).exists():
            resultado[nome] = "já feita"
            ctx.log(f"[{nome}] já feita")
        else:
            ctx.log(f"[{nome}] ...")
            resultado[nome] = funcoes[nome](ctx)
            ctx.log(f"[{nome}] {resultado[nome]}")
        if nome == ate:
            break
    return resultado


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pdf")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--cargo", required=True)
    ap.add_argument("--saida", required=True, help="pasta de trabalho; cria <saida>/<slug>/")
    ap.add_argument("--db", required=True, help="catalogo.db")
    ap.add_argument("--fichas", required=True, help="fichas-nos.jsonl (de ligar_fichas.py)")
    ap.add_argument("--acervo", required=True, help="raiz das apostilas")
    ap.add_argument("--modo", default="completo", choices=("completo", "compacto"))
    ap.add_argument("--decisoes", help="JSON de decisões aprovadas além das de integracao/decisoes/")
    ap.add_argument("--ate", choices=ETAPAS)
    ap.add_argument("--refazer", choices=ETAPAS)
    ap.add_argument("--esperar", action="store_true")
    args = ap.parse_args()
    from sge_api import SgeApi
    sge = SgeApi(os.environ.get("SGE_URL", "http://app:8080"), os.environ["INTERNAL_TOKEN"])
    ctx = Contexto(args.pdf, args.slug, args.cargo, Path(args.saida) / args.slug, args.db, args.fichas, args.acervo, args.modo,
                   args.decisoes, sge, args.esperar, log=lambda m: print(m, flush=True))
    try:
        executar(ctx, args.ate, args.refazer)
    except ErroDeEtapa as e:
        print(f"Parou: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
