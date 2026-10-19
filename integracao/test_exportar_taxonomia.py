#!/usr/bin/env python3
"""Testes de integracao/exportar_taxonomia.py, com respostas no formato real do QConcursos e do TEC, sem rede."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exportar_taxonomia as et  # noqa: E402

DISCIPLINAS = [{"id": 213, "nome": "Administração de Recursos Materiais"}, {"id": 96, "nome": "Banco de Dados"}]
ASSUNTOS = {213: {"213": [
    {"id": 21289, "name": "Conceitos Básicos na Administração de Recursos Materiais", "sort": 1,
     "nested_subjects": [{"id": 21290, "name": "Objetivos da Área de Materiais", "sort": 1}]},
    {"id": 8745, "name": "Classificação de Materiais", "sort": 2, "nested_subjects": [
        {"id": 21294, "name": "Classificação por Tipo de Demanda", "sort": 2},
        {"id": 17478, "name": "Atributos Para Classificação de Materiais", "sort": 1}]}]},
    96: {"96": [{"id": 1001, "name": "SQL", "sort": 1, "nested_subjects": []}]}}
TEC = {"dominios": [
    {"codigo_dominio_taxonomico": "CONCURSO_PUBLICO", "conteudos": [
        {"id_no_taxonomico": 1, "nome_no_taxonomico": "TI - Redes de Computadores", "ordem_exibicao": 1, "filhos": [
            {"id_no_taxonomico": 2, "nome_no_taxonomico": "NAT", "ordem_exibicao": 1, "filhos": []}]}]},
    {"codigo_dominio_taxonomico": "ENEM", "conteudos": [
        {"id_no_taxonomico": 9, "nome_no_taxonomico": "Física", "ordem_exibicao": 1, "filhos": []}]}]}


class TaxonomiaTest(unittest.TestCase):
    def test_qconcursos_normalizado_na_ordem_do_site(self):
        arvore = et.normalizar_qconcursos(DISCIPLINAS, ASSUNTOS)
        self.assertEqual(["Conceitos Básicos na Administração de Recursos Materiais", "Classificação de Materiais"],
                         [a["nome"] for a in arvore[0]["filhos"]])
        self.assertEqual([17478, 21294], [s["id"] for s in arvore[0]["filhos"][1]["filhos"]], "pela ordem do site")
        self.assertEqual(8, len(et.nos(arvore)))
        self.assertEqual(("Objetivos da Área de Materiais", 21289,
                          ("Administração de Recursos Materiais", "Conceitos Básicos na Administração de Recursos Materiais",
                           "Objetivos da Área de Materiais")), et.nos(arvore)[21290])

    def test_tec_so_concursos(self):
        arvore = et.normalizar_tec(TEC)
        self.assertEqual([{"id": 1, "nome": "TI - Redes de Computadores", "ordem": 1,
                           "filhos": [{"id": 2, "nome": "NAT", "ordem": 1, "filhos": []}]}], arvore)

    def test_grava_e_compara_com_a_exportacao_anterior(self):
        with tempfile.TemporaryDirectory() as tmp:
            antiga = et.normalizar_qconcursos(DISCIPLINAS, ASSUNTOS)
            caminho, dif = et.gravar("qconcursos", antiga, Path(tmp), hoje="2026-10-01")
            self.assertIsNone(dif)
            self.assertEqual(8, json.loads(caminho.read_text(encoding="utf-8"))["quantidade_nos"])
            nova = json.loads(json.dumps(antiga))
            nova[0]["filhos"][1]["nome"] = "Classificação dos Materiais"
            nova[0]["filhos"][0]["filhos"].append(nova[0]["filhos"][1]["filhos"].pop(0))
            nova[1]["filhos"] = [{"id": 1002, "nome": "NoSQL", "ordem": 1, "filhos": []}]
            _, dif = et.gravar("qconcursos", nova, Path(tmp), hoje="2026-11-01")
            self.assertEqual(["Banco de Dados > NoSQL"], dif["novos"])
            self.assertEqual(["Banco de Dados > SQL"], dif["removidos"])
            self.assertEqual(["Classificação de Materiais → Classificação dos Materiais (Administração de Recursos Materiais)"],
                             dif["renomeados"])
            self.assertEqual(1, len(dif["movidos"]))
            self.assertIn("Atributos Para Classificação de Materiais:", dif["movidos"][0])


if __name__ == "__main__":
    unittest.main()
