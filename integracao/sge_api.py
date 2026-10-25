#!/usr/bin/env python3
"""
sge_api.py — O que o worker do material (integracao/worker.py) usa do SGE-Concursos, pela
rede interna do compose (ADR-044 do SGE; docs/SPRINT-19-MATERIAL-AUTOMATICO.md de lá).

Só biblioteca padrão: o contêiner do worker fica pequeno e sem dependência de rede extra.

Rotas:
    GET  /api/concursos/ativo                    o concurso-alvo (204 = nenhum)
    GET  /api/concursos/{id}/planejamento        assuntos do edital, com segmentos e lacuna
    POST /api/segmentos/importacoes/confirmar    o segmentos.csv de sempre (multipart)
    POST /internal/ia/completar                  IA com a chave e o modelo de Ajustes (token)
    POST /internal/material/lacunas              D-65: o acervo não ensina o assunto (token)
    GET  /internal/provas/pendentes              provas que pedem trabalho (token)
    GET  /internal/provas/{id}/leitura           o que ler: arquivos, assuntos do alvo (token)
    POST /internal/provas/{id}/leitura           entrega as questões lidas (e o gabarito) (token)
    POST /internal/provas/{id}/gabarito          entrega só o gabarito (token)
    GET  /internal/provas/{id}/julgamento        as questões a julgar, com os segmentos (token)
    POST /internal/provas/{id}/vereditos         entrega vereditos (token)
    POST /internal/provas/{id}/falha             a leitura ou o julgamento falhou (token)
    GET  /internal/editais/pendentes             editais com o cargo escolhido, esperando a leitura (token)
    GET  /internal/editais/{id}/dados            PDF, cargo, árvore vigente e as decisões da pessoa (token)
    POST /internal/editais/{id}/revisao          entrega a leitura "edital-revisao/1" (token)
    POST /internal/editais/{id}/falha            a leitura falhou, com a etapa (token)
    GET  /internal/editais/material/pendentes    assuntos de uma conferência concluída que esperam material (token)
    POST /internal/editais/{id}/material         entrega o material por casamento de cada assunto (token)
    POST /internal/arvores                       carrega uma versão da árvore do QConcursos (token)
"""

import json
import urllib.error
import urllib.request
import uuid


class ErroSge(Exception):
    def __init__(self, status, codigo, mensagem):
        super().__init__(f"{status} {codigo or ''}: {mensagem}".strip())
        self.status = status
        self.codigo = codigo


class SgeApi:
    def __init__(self, base, token, tempo_maximo=330):
        self.base = base.rstrip("/")
        self.token = token
        # Um pouco acima dos 5 min que o SGE espera o OpenRouter.
        self.tempo_maximo = tempo_maximo

    # ------------------------------------------------------------ leitura

    def concurso_ativo(self):
        status, corpo = self._pedir("GET", "/api/concursos/ativo")
        return None if status == 204 else corpo

    def planejamento(self, concurso_id):
        return self._pedir("GET", f"/api/concursos/{concurso_id}/planejamento")[1]

    # ------------------------------------------------------------ escrita

    def importar_segmentos(self, csv_texto):
        fronteira = uuid.uuid4().hex
        corpo = (
            f"--{fronteira}\r\n"
            'Content-Disposition: form-data; name="arquivo"; filename="segmentos.csv"\r\n'
            "Content-Type: text/csv; charset=utf-8\r\n\r\n"
            f"{csv_texto}\r\n--{fronteira}--\r\n"
        ).encode("utf-8")
        return self._pedir("POST", "/api/segmentos/importacoes/confirmar", corpo,
                           f"multipart/form-data; boundary={fronteira}")[1]

    def completar(self, sistema, usuario):
        corpo = json.dumps({"sistema": sistema, "usuario": usuario}).encode("utf-8")
        return self._pedir("POST", "/internal/ia/completar", corpo, "application/json", interno=True)[1]["conteudo"]

    def registrar_lacuna(self, chave_externa, motivo):
        corpo = json.dumps({"chaveExterna": chave_externa, "motivo": motivo}).encode("utf-8")
        self._pedir("POST", "/internal/material/lacunas", corpo, "application/json", interno=True)

    # ------------------------------------------------------------ prova (Sprint 24 do SGE, ADR-046)

    def provas_pendentes(self):
        return self._pedir("GET", "/internal/provas/pendentes", interno=True)[1]

    def prova_dados_leitura(self, prova_id):
        return self._pedir("GET", f"/internal/provas/{prova_id}/leitura", interno=True)[1]

    def prova_entregar_leitura(self, prova_id, corpo):
        return self._json("POST", f"/internal/provas/{prova_id}/leitura", corpo)

    def prova_entregar_gabarito(self, prova_id, corpo):
        return self._json("POST", f"/internal/provas/{prova_id}/gabarito", corpo)

    def prova_para_julgar(self, prova_id):
        return self._pedir("GET", f"/internal/provas/{prova_id}/julgamento", interno=True)[1]

    def prova_vereditos(self, prova_id, corpo):
        return self._json("POST", f"/internal/provas/{prova_id}/vereditos", corpo)

    def prova_falha(self, prova_id, etapa, erro):
        return self._json("POST", f"/internal/provas/{prova_id}/falha", {"etapa": etapa, "erro": erro})

    # ------------------------------------------------------------ edital (Sprint 25 do SGE, ADR-047)

    def editais_pendentes(self):
        return self._pedir("GET", "/internal/editais/pendentes", interno=True)[1]

    def edital_dados(self, analise_id):
        return self._pedir("GET", f"/internal/editais/{analise_id}/dados", interno=True)[1]

    def edital_entregar(self, analise_id, texto_json):
        """`texto_json`: o JSON da entrega, como texto — o SGE tira o hash do corpo para a entrega ser idempotente."""
        return self._pedir("POST", f"/internal/editais/{analise_id}/revisao", texto_json.encode("utf-8"),
                           "application/json", interno=True)[1]

    def edital_falha(self, analise_id, etapa, mensagem, disciplina=None):
        return self._json("POST", f"/internal/editais/{analise_id}/falha",
                          {"etapa": etapa, "disciplina": disciplina, "mensagem": mensagem})

    def edital_material_pendentes(self):
        return self._pedir("GET", "/internal/editais/material/pendentes", interno=True)[1]

    def edital_material_entregar(self, analise_id, assuntos):
        return self._json("POST", f"/internal/editais/{analise_id}/material", {"assuntos": assuntos})

    def arvore_carregar(self, bytes_do_arquivo):
        return self._pedir("POST", "/internal/arvores", bytes_do_arquivo, "application/json", interno=True)[1]

    def _json(self, metodo, caminho, corpo):
        dados = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        return self._pedir(metodo, caminho, dados, "application/json", interno=True)[1]

    # ------------------------------------------------------------ transporte

    def _pedir(self, metodo, caminho, corpo=None, tipo=None, interno=False):
        pedido = urllib.request.Request(self.base + caminho, data=corpo, method=metodo)
        pedido.add_header("Accept", "application/json")
        if tipo:
            pedido.add_header("Content-Type", tipo)
        if interno:
            pedido.add_header("X-Internal-Token", self.token)
        try:
            with urllib.request.urlopen(pedido, timeout=self.tempo_maximo) as resposta:
                bruto = resposta.read()
                return resposta.status, (json.loads(bruto) if bruto else None)
        except urllib.error.HTTPError as e:
            codigo, mensagem = None, e.reason
            try:
                problema = json.loads(e.read())
                codigo, mensagem = problema.get("codigo"), problema.get("detail") or mensagem
            except (ValueError, AttributeError):
                pass
            raise ErroSge(e.code, codigo, mensagem) from None
        except urllib.error.URLError as e:
            raise ErroSge(None, "SEM_CONEXAO", str(e.reason)) from None
