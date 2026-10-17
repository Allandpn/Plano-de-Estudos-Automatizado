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
