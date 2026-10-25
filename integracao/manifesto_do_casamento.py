#!/usr/bin/env python3
"""Do casamento parte ↔ ficha aos manifestos de fatiamento, um por assunto do edital, validados por `dias/montar_bloco.py`.

Entradas (de `mapear_partes.py`, `casar_partes_fichas.py` e `confirmar_material.py`): `<edital>-partes.json` (disciplinas,
assuntos, partes), `<edital>-material.json` (liga cada parte a um item) e `<edital>-confirmado.json` (os candidatos de cada
item, com o veredito da IA). A escolha das fontes é regra (`selecao_material.py`); o validador estrito do fatiador diz se
cada manifesto passa: arquivo existe, página existe, nenhuma página repetida, toda parte coberta ou declarada lacuna.

    python integracao/manifesto_do_casamento.py EDITAL-partes.json --material M.json --confirmado C.json \\
        --db catalogo.db --acervo /acervo/apostilas --saida DIR [--modo completo|compacto]

Grava `<saida>/manifestos/<chave>.json` e `<saida>/questoes/<chave>.json` (as faixas de "Questões deste assunto") e um
relatório `<saida>/relatorio.md`. Com `--sem-validar` não chama o fatiador.
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path, PureWindowsPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dias"))
from entrega_revisao import chave_do_assunto  # noqa: E402
from selecao_material import selecionar  # noqa: E402


def caminho_no_acervo(raiz, relativo):
    """O catálogo guarda o caminho com barra invertida (Windows): vira POSIX sob a raiz do acervo."""
    return Path(raiz).joinpath(*[p for p in PureWindowsPath(relativo).parts if p not in ("", ".")])


def nome_da_parte(p):
    return " ".join(x for x in (p.get("herdado"), p.get("texto")) if x).strip()


def partes_do_assunto(disciplina, indice_assunto, assunto, por_posicao, confirmados):
    """As partes do assunto na ordem do edital, cada uma com os candidatos confirmados do seu item."""
    saida = []
    for ip, p in enumerate(assunto.get("partes") or []):
        item = por_posicao.get((disciplina, indice_assunto, ip))
        c = confirmados.get(item) or {}
        saida.append({"nome": nome_da_parte(p), "candidatos": [m for m in c.get("material", []) if m.get("veredito")]})
    return saida


def manifesto(slug, disciplina, assunto, chave, escolha, raiz):
    return {"assunto_uuid": chave, "edital": slug, "titulo": f"{disciplina} — {assunto['texto'][:90]}",
            "subitens": escolha["subitens"], "lacunas": escolha["lacunas"], "descartes": [],
            "fontes": [{"arquivo": str(caminho_no_acervo(raiz, f["arquivo"])), "paginas": f["paginas"], "rotulo": f["rotulo"][:120],
                        "cobre": f["cobre"], "tipo": f["tipo"],
                        **({"minutos_por_pagina": 3} if f["tipo"] == "fixacao" else {})} for f in escolha["fontes"]]}


def processar(slug, disciplinas, material, confirmado, ficha_de, raiz, modo="completo", validar=None, saida=None, so=None):
    """Um manifesto por assunto. `validar(caminho_do_manifesto)` devolve a lista de erros (vazia = passou)."""
    por_posicao = {(p["disciplina"], p["assunto"], p["parte"]): p["item"] for p in material["partes"]}
    confirmados = {c["indice"]: c for c in confirmado}
    resultado = []
    for d in disciplinas:
        if so and not any(t.lower() in d["nome"].lower() for t in so):
            continue
        vistos = {}
        for ia, a in enumerate(d["assuntos"]):
            # A chave pode vir pronta (o SGE a guarda desde a conferência; sem ela, repetir assuntos mudaria a contagem).
            chave = chave_do_assunto(d["nome"], a["texto"], vistos) if not a.get("chave") else a["chave"]
            partes = partes_do_assunto(d["nome"], ia, a, por_posicao, confirmados)
            escolha = selecionar(partes, ficha_de, modo)
            linha = {"chave": chave, "disciplina": d["nome"], "assunto": a["texto"], "partes": len(partes),
                     "fontes": len(escolha["fontes"]), "lacunas": len(escolha["lacunas"]), "minutos": escolha["estimativa_min"],
                     "tem_questoes": bool(escolha["questoes"]), "erros": [], "avisos": escolha["avisos"]}
            if saida and not escolha["fontes"]:  # sobra de rodada anterior: assunto sem material não pode ficar com manifesto
                for pasta in ("manifestos", "questoes"):
                    (saida / pasta / f"{chave}.json").unlink(missing_ok=True)
            if escolha["fontes"]:
                m = manifesto(slug, d["nome"], a, chave, escolha, raiz)
                if saida:
                    (saida / "manifestos").mkdir(parents=True, exist_ok=True)
                    (saida / "manifestos" / f"{chave}.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
                    (saida / "questoes" / f"{chave}.json").unlink(missing_ok=True)
                    if escolha["questoes"]:
                        (saida / "questoes").mkdir(parents=True, exist_ok=True)
                        (saida / "questoes" / f"{chave}.json").write_text(json.dumps(
                            [dict(q, arquivo=str(caminho_no_acervo(raiz, q["arquivo"]))) for q in escolha["questoes"]],
                            ensure_ascii=False, indent=1), encoding="utf-8")
                if validar and saida:
                    linha["erros"] = validar(saida / "manifestos" / f"{chave}.json")
            linha["situacao"] = "sem material" if not escolha["fontes"] else "recusado" if linha["erros"] else \
                "parcial" if escolha["lacunas"] else "completo"
            resultado.append(linha)
    return resultado


def relatorio(slug, modo, linhas):
    n = len(linhas)
    cont = {}
    for l in linhas:
        cont[l["situacao"]] = cont.get(l["situacao"], 0) + 1
    horas = sorted(l["minutos"] / 60 for l in linhas if l["fontes"])
    mediana = horas[len(horas) // 2] if horas else 0
    saida = [f"# {slug} — manifestos do casamento (modo {modo})", "",
             f"{n} assuntos · " + " · ".join(f"{k}: {v}" for k, v in sorted(cont.items())) +
             f" · mediana {mediana:.1f} h por assunto com material · {sum(1 for l in linhas if l['tem_questoes'])} com questões à parte", ""]
    recusados = [l for l in linhas if l["situacao"] == "recusado"]
    if recusados:
        saida += ["## Recusados pelo fatiador", ""]
        for l in recusados:
            saida.append(f"- **{l['assunto'][:90]}** _({l['disciplina']})_")
            saida += [f"    - {e}" for e in l["erros"][:4]]
        saida.append("")
    avisos = {(a["arquivo"], a["tema"]): a for l in linhas for a in l.get("avisos", [])}
    if avisos:
        saida += [f"## Temas do catálogo com página fora do PDF, não usados ({len(avisos)})", ""]
        saida += [f"- {a['arquivo'].replace(chr(92), '/').split('/')[-1]}: {a['tema'][:70]} — {a['motivo']}" for a in avisos.values()]
        saida.append("")
    sem = [l for l in linhas if l["situacao"] == "sem material"]
    saida += [f"## Assuntos sem nenhum material ({len(sem)})", ""] + [f"- {l['assunto'][:100]} _({l['disciplina']})_" for l in sem]
    return "\n".join(saida)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("partes")
    ap.add_argument("--material", required=True)
    ap.add_argument("--confirmado", required=True)
    ap.add_argument("--db", required=True, help="catalogo.db")
    ap.add_argument("--acervo", required=True, help="raiz das apostilas")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--slug")
    ap.add_argument("--modo", default="completo", choices=("completo", "compacto"))
    ap.add_argument("--sem-validar", action="store_true")
    ap.add_argument("--disciplinas", nargs="*", help="só as disciplinas cujo nome contém algum destes textos")
    args = ap.parse_args()
    db = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    cache = {}

    def ficha_de(caminho):
        if caminho not in cache:
            linha = db.execute("SELECT ficha FROM fichas WHERE caminho = ? AND situacao = 'ok'", (caminho,)).fetchone()
            cache[caminho] = json.loads(linha[0]) if linha else None
        return cache[caminho]

    validar = None
    if not args.sem_validar:
        import montar_bloco as mb
        import tempfile

        def validar(caminho):
            try:
                with tempfile.TemporaryDirectory() as t:
                    mb.montar_bloco(caminho, t, refatiar=True, so_validar=True)
                return []
            except mb.ManifestoInvalido as e:
                return e.erros
    nome = Path(args.partes).name.replace("-partes.json", "")
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    linhas = processar(args.slug or nome, json.loads(Path(args.partes).read_text(encoding="utf-8")),
                       json.loads(Path(args.material).read_text(encoding="utf-8")),
                       json.loads(Path(args.confirmado).read_text(encoding="utf-8")), ficha_de, args.acervo, args.modo,
                       validar, saida, args.disciplinas)
    (saida / "assuntos.json").write_text(json.dumps(linhas, ensure_ascii=False, indent=1), encoding="utf-8")
    texto = relatorio(args.slug or nome, args.modo, linhas)
    (saida / "relatorio.md").write_text(texto, encoding="utf-8")
    print(texto.splitlines()[2])


if __name__ == "__main__":
    main()
