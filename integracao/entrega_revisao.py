#!/usr/bin/env python3
"""Monta o JSON que o planejamento entrega ao SGE para a tela de revisão do edital (contrato "edital-revisao/1").

O contrato está descrito em docs/especificacao-revisao-edital-sge.md §11. Aqui só se junta o que os passos do protótipo
já gravam: o texto extraído (`partes_edital.py extrair`), as disciplinas com assuntos e partes (`<edital>-partes.json`), a
ligação das partes aos nós (`<edital>-nos.json`, de `mapear_partes.py`), o mapa de disciplinas e as linhas fora de
disciplina (`<edital>-fora.json`).

    python integracao/entrega_revisao.py EDITAL-partes.json --slug alesc-2024 --cargo "Analista de Sistemas" --saida DIR

Cada parte ganha uma **chave estável** (hash do texto normalizado e da posição entre as repetições), para que reprocessar
o mesmo edital mantenha a identidade da parte e as decisões do usuário continuem presas a ela.
"""
import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from partes_edital import normalizar  # noqa: E402

CONTRATO = "edital-revisao/1"


def chave_da_parte(disciplina, assunto, parte, vistas):
    """Hash curto e estável: disciplina, assunto, prefixo herdado, texto e contexto, mais o número da ocorrência quando o
    edital repete a mesma parte no mesmo assunto."""
    base = "|".join(normalizar(x or "") for x in (disciplina, assunto, parte.get("herdado"), parte.get("texto"),
                                                   parte.get("contexto")))
    vistas[base] = vistas.get(base, 0) + 1
    return hashlib.sha1(f"{base}|{vistas[base]}".encode("utf-8")).hexdigest()[:16]


def chave_do_assunto(disciplina, texto, vistos):
    """Hash estável do assunto: disciplina e texto normalizados, mais o número da ocorrência se o edital o repete."""
    base = "|".join(normalizar(x or "") for x in (disciplina, texto))
    vistos[base] = vistos.get(base, 0) + 1
    return hashlib.sha1(f"assunto|{base}|{vistos[base]}".encode("utf-8")).hexdigest()[:16]


def _ligacao(item, arvore_id):
    """A ligação de um item de `mapear_partes`: nós, natureza e de onde veio."""
    if item is None:
        return None
    origem = "decisao" if item.get("decisao") else "refino" if item.get("refinado") else "ia"
    ligacao = {"nos": list(item.get("ia") or []), "natureza": item.get("natureza"), "origem": origem}
    if item.get("decisao"):
        ligacao["decisao"] = item["decisao"]
    if item.get("refinado"):
        ligacao["antes"] = list(item.get("ia_antes") or [])
    if item.get("segunda_passada"):
        ligacao["segunda_passada"] = True
    return ligacao


def montar_entrega(slug, cargo, pdf, disciplinas, nos=None, mapa_disciplinas=None, fora=None, execucao=None,
                   arvore="qconcursos"):
    """`disciplinas`: lista de `<edital>-partes.json`. `nos`: o `<edital>-nos.json` ({itens, partes}). Devolve o dict."""
    por_parte = {(p["disciplina"], p["assunto"], p["parte"]): p["item"] for p in (nos or {}).get("partes", [])}
    itens = (nos or {}).get("itens", [])
    saida_disciplinas = []
    for d in disciplinas:
        assuntos, vistas, vistos = [], {}, {}
        for ia, a in enumerate(d["assuntos"]):
            partes = []
            for ip, p in enumerate(a.get("partes") or []):
                i = por_parte.get((d["nome"], ia, ip))
                partes.append({"chave": chave_da_parte(d["nome"], a["texto"], p, vistas), "ordem": ip + 1,
                               "texto": p["texto"], "contexto": p.get("contexto"), "herdado": p.get("herdado"),
                               "ligacao": _ligacao(itens[i], arvore) if i is not None else None})
            assuntos.append({"chave": a.get("chave") or chave_do_assunto(d["nome"], a["texto"], vistos), "ordem": ia + 1, "texto": a["texto"],
                             "partes": partes,
                             "erros": a.get("erros") or [], "alertas": (a.get("alertas") or []) + (a.get("avisos") or [])})
        saida_disciplinas.append({"nome": d["nome"], "restricao": d.get("restricao"), "comum": d.get("comum"),
                                  "paginas": d.get("paginas"), "linhas": [d.get("linha_inicio"), d.get("linha_fim")],
                                  "qconcursos": (mapa_disciplinas or {}).get(d["nome"], []),
                                  "tentativas": d.get("tentativas"), "assuntos": assuntos,
                                  "trechos_sem_assunto": d.get("trechos_sem_assunto") or [],
                                  "referencias": d.get("referencias") or [],
                                  # O texto da disciplina, para o SGE refazer a conferência por regra quando a pessoa
                                  # edita uma parte (a regra de `partes_edital.conferir_assunto` precisa dele).
                                  "texto": d.get("texto")})
    todas = [p for d in saida_disciplinas for a in d["assuntos"] for p in a["partes"]]
    return {"contrato": CONTRATO, "concurso": {"slug": slug, "cargo": cargo}, "pdf": pdf,
            "execucao": dict({"data": date.today().isoformat(), "arvore": arvore}, **(execucao or {})),
            "disciplinas": saida_disciplinas, "linhas_fora": fora or [],
            "resumo": {"disciplinas": len(saida_disciplinas), "assuntos": sum(len(d["assuntos"]) for d in saida_disciplinas),
                       "partes": len(todas), "sem_no": sum(1 for p in todas if p["ligacao"] and not p["ligacao"]["nos"]),
                       "assuntos_recusados": sum(1 for d in saida_disciplinas for a in d["assuntos"] if a["erros"]),
                       "trechos_sem_assunto": sum(len(d["trechos_sem_assunto"]) for d in saida_disciplinas),
                       "blocos_fora": len(fora or [])}}


def main():
    ap = argparse.ArgumentParser(description="Monta o JSON de entrega 'edital-revisao/1' para o SGE.")
    ap.add_argument("partes", help="<edital>-partes.json")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--cargo", required=True)
    ap.add_argument("--saida", required=True, help="pasta de saída")
    ap.add_argument("--modelo", help="modelo de IA usado (para o histórico da execução)")
    ap.add_argument("--arvore", default="qconcursos-2026-10-19", help="nome da árvore usada (arquivo em taxonomia/)")
    args = ap.parse_args()
    arquivo = Path(args.partes)
    nome = arquivo.name.replace("-partes.json", "")
    pasta = arquivo.parent

    def ler(sufixo, padrao=None):
        f = pasta / f"{nome}{sufixo}"
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else padrao

    entrega = montar_entrega(args.slug, args.cargo, nome, json.loads(arquivo.read_text(encoding="utf-8")),
                             ler("-nos-refinado.json") or ler("-nos.json"), ler("-disciplinas.json"), ler("-fora.json"),
                             {"modelo": args.modelo} if args.modelo else None, args.arvore)
    destino = Path(args.saida)
    destino.mkdir(parents=True, exist_ok=True)
    (destino / f"{args.slug}-edital-revisao.json").write_text(json.dumps(entrega, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(entrega["resumo"], ensure_ascii=False))


if __name__ == "__main__":
    main()
