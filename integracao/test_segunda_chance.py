"""Testes de integracao/segunda_chance.py: a busca antiga só nas partes sem cobertura, sem repetir página, sem questões."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import segunda_chance as sc  # noqa: E402
from entrega_revisao import chave_do_assunto  # noqa: E402


class AcervoFalso:
    def __init__(self, candidatos):
        self.candidatos = candidatos
        self.pedidos = []

    def candidatos_por_partes(self, partes, disciplina=None):
        self.pedidos.append(list(partes))
        return self.candidatos

    def caminho(self, relativo):
        return Path("/acervo") / relativo


class SgeFalso:
    def __init__(self, *respostas):
        self.respostas = list(respostas)
        self.sistemas = []

    def completar(self, sistema, usuario):
        self.sistemas.append((sistema, usuario))
        return self.respostas.pop(0)


CAND = [{"arquivo": "c/aula.pdf", "n_paginas": 50, "partes": ["Docker"], "paginas": [{"pagina": 3, "trecho": "docker"}]}]
RESP = json.dumps({"fontes": [{"arquivo": "A1", "paginas": "10-20", "rotulo": "aula", "cobre": ["Docker"], "tipo": "teoria"}],
                   "lacunas": []})
MANIFESTO = {"assunto_uuid": "k", "edital": "e", "titulo": "t", "subitens": ["Redes", "Docker"], "descartes": [],
             "lacunas": [{"subitem": "Docker", "motivo": "nenhum tema"}],
             "fontes": [{"arquivo": "/acervo/c/aula.pdf", "paginas": "1-12", "rotulo": "r", "cobre": ["Redes"], "tipo": "teoria"}]}


class TentarTest(unittest.TestCase):
    def test_busca_so_a_parte_sem_cobertura_e_junta(self):
        sge, acervo = SgeFalso(RESP), AcervoFalso(CAND)
        novo, msg = sc.tentar(sge, acervo, "D", "Redes, Docker", ["Redes", "Docker"], dict(MANIFESTO), lambda m: [])
        self.assertEqual([["Docker"]], acervo.pedidos)
        self.assertEqual([], novo["lacunas"])
        extra = novo["fontes"][-1]
        self.assertEqual("segunda_chance", extra["origem"])
        self.assertEqual("/acervo/c/aula.pdf", extra["arquivo"])
        self.assertEqual("13-20", extra["paginas"], "tira 10-12, que o casamento já usa")
        self.assertIn("sem questões", sge.sistemas[0][0].lower().replace("não inclua questões", "sem questões"))

    def test_sem_candidato_ou_sem_material_mantem(self):
        self.assertIsNone(sc.tentar(SgeFalso(), AcervoFalso([]), "D", "x", ["Docker"], dict(MANIFESTO), lambda m: [])[0])
        sem = json.dumps({"sem_material": True, "motivo": "só cita"})
        novo, msg = sc.tentar(SgeFalso(sem), AcervoFalso(CAND), "D", "x", ["Redes", "Docker"], dict(MANIFESTO), lambda m: [])
        self.assertIsNone(novo)
        self.assertEqual("só cita", msg)

    def test_recusado_pelo_validador_tenta_de_novo_e_desiste(self):
        sge = SgeFalso(RESP, RESP)
        novo, msg = sc.tentar(sge, AcervoFalso(CAND), "D", "x", ["Redes", "Docker"], dict(MANIFESTO), lambda m: ["página fora"])
        self.assertIsNone(novo)
        self.assertIn("página fora", msg)
        self.assertIn("página fora", sge.sistemas[1][1], "os erros voltam no segundo pedido")

    def test_so_paginas_ja_usadas_nao_vira_fonte(self):
        resp = json.dumps({"fontes": [{"arquivo": "A1", "paginas": "2-5", "rotulo": "a", "cobre": ["Docker"]}], "lacunas": []})
        novo, msg = sc.tentar(SgeFalso(resp), AcervoFalso(CAND), "D", "x", ["Redes", "Docker"], dict(MANIFESTO), lambda m: [])
        self.assertIsNone(novo)
        self.assertIn("já usa", msg)


class ProcessarTest(unittest.TestCase):
    def test_assunto_sem_material_ganha_manifesto_e_linha_atualizada(self):
        pasta = Path(tempfile.mkdtemp())
        disciplinas = [{"nome": "D", "assuntos": [{"texto": "Docker", "partes": [{"texto": "Docker"}]}]}]
        chave = chave_do_assunto("D", "Docker", {})
        linhas = [{"chave": chave, "situacao": "sem material", "fontes": 0, "lacunas": 1, "minutos": 0},
                  {"chave": "outra", "situacao": "completo", "fontes": 1, "lacunas": 0, "minutos": 5}]
        tentados = sc.processar("e", disciplinas, linhas, pasta, SgeFalso(RESP), AcervoFalso(CAND), lambda m: [], lambda *_: None)
        self.assertEqual(["achou"], [t["resultado"] for t in tentados])
        self.assertEqual(("completo", 1, 0, 11 * sc.MINUTOS_TEORIA), (linhas[0]["situacao"], linhas[0]["fontes"], linhas[0]["lacunas"], linhas[0]["minutos"]))
        m = json.loads((pasta / "manifestos" / f"{chave}.json").read_text(encoding="utf-8"))
        self.assertEqual(["Docker"], m["subitens"])
        self.assertEqual("e", m["edital"])
        self.assertEqual(5, linhas[1]["minutos"], "o assunto completo não é tocado")


if __name__ == "__main__":
    unittest.main()
