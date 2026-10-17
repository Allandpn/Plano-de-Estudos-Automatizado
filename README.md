# Toolkit de planejamento de estudos para concursos (qualquer edital)

Testado nesta sessão contra um PDF real de apostila (Estratégia Concursos,
coluna única, cabeçalho/rodapé repetido) — ver detalhes no chat. Antes de
apontar pros ~2600 PDFs de produção, rode contra uma pasta pequena (10-20
arquivos variados: aula curta, aula longa, aula com diagrama) pra calibrar.

## Instalação

```bash
pip install pdfplumber pypdf reportlab --break-system-packages
```

## 1. Indexar uma pasta de apostilas

```bash
python indice/indexador.py /caminho/para/apostilas --db indice/indice.db
```

Roda de novo a qualquer momento — só reprocessa arquivo novo/alterado
(compara por hash+data de modificação). Use `--forcar` pra reindexar tudo.

## 2. Buscar no índice

```bash
python indice/buscar_indice.py "window function" --db indice/indice.db
python indice/buscar_indice.py --listar-cursos --db indice/indice.db
```

**Atenção:** a busca usa OR entre as palavras (prioriza não perder nada) —
sempre confira o trecho retornado antes de considerar o assunto "coberto".

## 3. Montar o PDF de um dia de estudo

Crie um manifesto JSON (ver `dias/montar_dia.py` pro formato) listando os
trechos de cada apostila na ordem de leitura, depois:

```bash
python dias/montar_dia.py meu_manifesto.json --saida dias/2026-09-16.pdf
```

Gera um único PDF com capa de rastreabilidade (mapeia cada página de volta
ao arquivo/página original).

## 3A. Fatiar o material de um assunto em blocos de leitura

```bash
python dias/montar_bloco.py manifesto_assunto.json --saida-dir dias/ --validar   # confere, não gera
python dias/montar_bloco.py manifesto_assunto.json --saida-dir dias/
python -m unittest dias/test_montar_bloco.py                                     # testes do fatiador
python -m unittest discover -s integracao -p "test_*.py"                        # contrato com o SGE
```

O manifesto declara os subitens do assunto, quais páginas cobrem cada um e as lacunas.
Qualquer página perdida, repetida ou fora do PDF faz o script parar sem gerar nada. Leia o
`<assunto>_cobertura.md` gerado antes de subir os blocos pro Drive.

## 4. Gerar rascunho de deck Anki

Crie um JSON de cards (ver `anki/anki_gerar.py` pro formato), depois:

```bash
python anki/anki_gerar.py cards.json --saida deck.csv --deck "Concurso::Trilha 1 - Dados::Bloco"
```

Gera um CSV por tipo de note (Basic / Basic-reversed / Cloze), pronto pra
`File > Import` no Anki. **Revise antes de importar.**

## 4A. Worker do material (caminho principal, no Pi)

`integracao/worker.py` roda como contêiner ao lado do SGE e prepara sozinho o material do
concurso-alvo: busca no índice, IA pelo proxy do SGE, fatiamento, importação dos segmentos.
Configuração por variável de ambiente (docstring do script); a imagem vem do `Dockerfile`
da raiz. Para rodar um ciclo à mão:

```bash
SGE_URL=http://127.0.0.1:8080 INTERNAL_TOKEN=... ACERVO_DIR=apostilas INDICE_DB=indice/indice.db \
    MATERIAL_DIR=/tmp/material python integracao/worker.py --uma-vez
```

## 5. Publicar os segmentos no Google Drive (legado)

Depois de registrar os pedaços (`canonizar_assuntos.py --adicionar-pedacos`), com o
`rclone` configurado para o Drive:

```bash
python integracao/publicar_drive.py --db integracao/canonico.db --edital MEU-EDITAL-2027 \
    --saida-dir dias/ --remoto gdrive:Estudos/Material --simular   # mostra o que faria
python integracao/publicar_drive.py --db integracao/canonico.db --edital MEU-EDITAL-2027 \
    --saida-dir dias/ --remoto gdrive:Estudos/Material
```

Sobe cada PDF e troca o caminho local pelo link compartilhável no banco — é o link que o
SGE abre no botão "Abrir material".

## 6. Exportar um concurso pro SGE-Concursos

Depois de canonicalizar os assuntos (`integracao/canonizar_assuntos.py`), calcular a
ordem (`integracao/calcular_orcamento.py`, que segue a ordem do mapa de assuntos) e
publicar os segmentos (§5):

```bash
python integracao/exportar_sge.py --db integracao/canonico.db --edital MEU-EDITAL-2027 \
    --nome "Meu Edital 2027" --data-prova 2027-05-10 \
    --saida-dir "<Google Drive>/SGE-Importacao/meu-edital-2027"
```

Gera `assuntos.csv`, `segmentos.csv` (se houver material fatiado) e `concurso.json` no
formato que o SGE lê (`docs/arquitetura-integracao-planejamento-sge.md` §8.1). No SGE,
o concurso entra quando `CONCURSO_ATIVO=meu-edital-2027`.

## Próximos passos

1. Testar numa pasta pequena (10-20 PDFs variados).
2. Conferir a qualidade da extração (sobrou algum boilerplate? coluna
   detectada errado em algum PDF de layout diferente?).
3. Ajustar os limiares em `indexador.py` se necessário
   (`limiar_frequencia` do boilerplate, `limiar_fracao` da detecção de
   coluna) — comentados no código.
4. Só então rodar contra os 2600 PDFs de produção.
5. Configurar o Claude Code apontando pra essa pasta, com `CLAUDE.md` já
   pronto — ele passa a poder rodar `buscar_indice.py`, ler apostilas
   específicas, montar PDFs de dia e rascunhos de Anki sozinho, seguindo o
   fluxo documentado em `CLAUDE.md`.
