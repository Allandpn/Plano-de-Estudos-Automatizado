# Planejamento de estudos para concursos — Instruções do Projeto

Contexto: preparação para **qualquer edital** de concurso público (foco em TI), a partir
de um acervo de ~2600 apostilas do Estratégia Concursos indexadas em `indice/indice.db`.
O planejamento lê o edital, mapeia os assuntos, tria o acervo, fatia o material e
exporta tudo pro SGE-Concursos, que decide o dia a dia (escada de revisão, turno).
**Caminho principal desde 2026-10-17:** o material é preparado sozinho por
`integracao/worker.py`, no Pi, ao lado do SGE (`docs/arquitetura-integracao-planejamento-sge.md`
§9; ADR-044 do SGE). Os fluxos em chat abaixo viram **modo manual** — para revisar uma
lacuna, refazer a triagem de um assunto com cuidado ou trabalhar o legado.

O primeiro concurso trabalhado foi o SEFAZ SC 2026 — o material dele fica arquivado em
`docs/concursos/sefaz-sc-2026/` e serve de **referência de convenção** (formato do mapa
de assuntos, das triagens, das fichas).

Cada concurso tem a própria pasta, `docs/concursos/<slug>/` (o mesmo slug da pasta de
importação do SGE, `SGE-Importacao/<slug>/`). Leia sempre, antes de qualquer tarefa
sobre um concurso: o mapa de assuntos (`mapa-assuntos-edital-<slug>.md`) e o plano/
cronograma dele, se existirem. O **método** (recuperação, espaçamento, regras de
flashcard) está em `docs/concursos/sefaz-sc-2026/plano-estudos-sefaz-sc-2026.md` e vale
para todos os concursos até ganhar documento próprio.

## Estrutura de pastas

```
docs/            → integração com o SGE e documentos gerais
docs/concursos/<slug>/ → por concurso: edital, mapa-assuntos, triagens, sessoes (legado
                   SEFAZ), inventário
apostilas/       → os PDFs originais (não editar/mover)
indice/          → indice.db (SQLite+FTS5) e os scripts de indexação/busca
dias/            → PDFs mesclados por dia (SEFAZ SC) ou por bloco de assunto (editais
                   novos) + manifestos JSON
anki/            → rascunhos de deck (JSON) e CSVs gerados
integracao/      → canonico.db (registro canônico de assuntos) e os scripts de
                   canonicalização/orçamento/exportação pro SGE-Concursos
```

## Fluxo de leitura de um edital novo

Quando pedirem "leia o edital X" (estágio 1 de
`docs/arquitetura-integracao-planejamento-sge.md`): a única entrada é o PDF do edital, a
saída é um mapa de assuntos novo pronto pra triagem.

1. Ler o edital completo (conteúdo programático) e extrair os assuntos finos, um por
   linha, na ordem em que aparecem — mesmo formato/granularidade de
   `docs/concursos/sefaz-sc-2026/mapa-assuntos-edital-sefaz-sc.md` (referência de convenção,
   inclusive o agrupamento por ponto-e-vírgula quando fizer sentido).
2. Procurar o quadro de distribuição de questões do edital (normalmente um anexo com
   número de questões por disciplina). Se existir e for granular por disciplina, esse
   número vira o `peso` (ALTO/MEDIO/BAIXO, por tercis ou corte que fizer sentido pro
   total de questões daquele edital) aplicado a todos os assuntos daquela disciplina.
   **Se o edital não granular peso por disciplina, marcar `peso` como "não determinado"
   e seguir — nunca estimar peso a partir de menções soltas em apostilas.**
3. **Reaproveitar antes de triar:** pra cada assunto, buscar o canônico existente
   (`integracao/canonizar_assuntos.py --buscar`, ver "Fluxo de canonicalização"). Assunto
   que já existe de um edital anterior já tem triagem e material — só os realmente novos
   precisam de triagem completa. É isso que deixa um edital novo pronto em pouco tempo.
4. Propor o novo `docs/concursos/<slug>/mapa-assuntos-edital-<slug>.md` **como diff,
   pedindo aprovação antes de gravar** — mesma regra de sempre pra `docs/*.md`.
   **Nome do assunto fiel à redação do edital:** o SGE adota por nome (sem acento/caixa) o
   assunto criado lá pela análise por IA; nome diferente duplica. Todo `concurso.json`
   exportado precisa de `slug` e `nome` (o SGE passou a lê-lo; ver §14 dos requisitos de lá).
   **Entrada alternativa:** se o edital já foi subido no SGE (análise por IA, que guarda a
   chave do OpenRouter — o planejamento não tem chave), os assuntos confirmados lá são a
   entrada no lugar do passo 1: manter os nomes exatamente como vieram e seguir da triagem
   em diante (decisão de 2026-10-15, `docs/arquitetura-integracao-planejamento-sge.md`).
5. Depois de aprovado, os assuntos novos entram no fluxo normal de triagem (próxima seção).

## Fluxo de uma triagem de bloco

Quando pedirem "triagem do bloco X":

1. Ler os assuntos finos do bloco no mapa de assuntos do concurso.
2. Pra cada assunto, buscar no índice: `python indice/buscar_indice.py "termo"`.
   - A busca usa OR entre palavras (prioriza recall) — **sempre ler o trecho
     retornado antes de considerar o assunto coberto**, não confiar só no
     fato de ter retornado resultado.
3. **Orçamento de busca por assunto** (não pular etapas, não repetir em loop):
   1. Query direta com os termos do mapa-assuntos.
   2. Se não achar (ou o trecho não bate de verdade): reformular com até 2
      sinônimos/termos relacionados (ex: "window function" → "OVER" →
      "PARTITION BY").
   3. Se ainda não achar: abrir no máximo 2 PDFs candidatos, no máximo ~20
      páginas cada, via leitura direta do arquivo.
   4. Se mesmo assim não achar: marcar ❌ no `mapa-assuntos-edital.md`,
      registrar no "Gap confirmado" da triagem, e seguir em frente — não
      repetir o ciclo pro mesmo assunto.
   A triagem registra a cobertura **por subitem** do assunto (quais páginas ensinam cada
   parte, ou ❌ com motivo) e as páginas descartadas com motivo — é disso que sai o
   manifesto do fatiamento, que recusa subitem sem página e sem lacuna declarada.
4. Escrever `docs/concursos/<slug>/triagens/triagem-bloco-<nome>.md` no mesmo formato de
   `docs/concursos/sefaz-sc-2026/triagens/triagem-bloco-bd-sql-sefaz-sc.md` (acervo identificado, decisões de
   descarte, gap confirmado, roteiro por dia com leitura/pretest/fixação/
   banco de reserva/observações). **Toda citação de aula/PDF no roteiro leva
   o caminho da pasta (relativo a `apostilas/`) escrito por extenso ao lado**
   (ex: `00-Curso Regular\02, aula 07.pdf`) — mesmo repetindo o caminho
   várias vezes ao longo do documento. Nada de código/legenda que exija
   voltar ao topo do arquivo pra decodificar — o objetivo é achar o PDF no
   Explorer sem sair do trecho que está lendo.
5. Propor as edições no mapa de assuntos do concurso **como diff, pedindo
   aprovação antes de gravar** — é a espinha dorsal do plano, erro silencioso ali é
   caro. (Em edital novo não há cronograma por dia: quem decide o dia é o SGE. O
   `cronograma-detalhado` existe só no legado SEFAZ.)

## Fluxo de canonicalização de assuntos

Depois que um bloco (ou o mapa-assuntos inteiro de um edital) está triado e aprovado, e
antes de rodar o orçamento/exportação pro SGE (estágios 3-6 de
`docs/arquitetura-integracao-planejamento-sge.md`): decidir se cada assunto já triado é
"o mesmo" de um assunto canônico que já existe (de um edital anterior), ou se é novo.

1. Pra cada assunto do bloco, buscar candidatos parecidos:
   `python integracao/canonizar_assuntos.py --buscar "termo" --db integracao/canonico.db`
   (termo sem acento se possível — ver docstring do script sobre codificação no Windows).
2. Comparar semanticamente — o mesmo conceito pode estar escrito com palavras diferentes
   entre editais (ex: "Normalização de banco de dados" vs. "Formas normais e dependência
   funcional"). Se achar candidato claramente igual, reaproveitar o UUID dele (campo
   `uuid_existente`). Se for ambíguo, **perguntar antes de decidir** — nunca mesclar nem
   duplicar por conta própria.
3. Registrar a decisão de todo o bloco de uma vez: montar um JSON (`disciplina`, `assunto`,
   `edital`, `redacao`, `peso`, `paginas`, `referencia`, `uuid_existente` opcional — ver
   docstring de `canonizar_assuntos.py`) e rodar
   `python integracao/canonizar_assuntos.py --adicionar-lote arquivo.json --db integracao/canonico.db`.
   Texto com acento entra sempre pelo JSON, nunca por flag de linha de comando.
4. **O nome canônico só é corrigido pelo lado do planejamento.** Se um nome canônico
   existente estava errado, corrigir com `--uuid-existente` apontando pro UUID certo
   (nunca criar um UUID novo só porque o nome mudou — isso quebraria o upsert no SGE).

## Ficha de sessão diária (legado SEFAZ SC — não usar em edital novo)

Assim que a triagem de um bloco for aprovada, gerar de uma vez **todas as
fichas dos dias daquele bloco** (não dia a dia sob demanda) em
`docs/concursos/sefaz-sc-2026/sessoes/AAAA-MM-DD.md`: versão compacta só do necessário pra cada dia
(leitura com arquivo+página exatos, pretest, fixação, banco de reserva,
observações de gap) — extraída da triagem completa, sem exigir abrir o
documento inteiro na hora de estudar. Gerar o bloco inteiro de uma vez evita
depender de um chat toda noite antes de cada sessão.

## Divergência entre sessão real e mapa de assuntos

A triagem confirma cobertura por amostragem (busca + leitura de trecho), mas
o estudo real pode revelar que o status não bate — ex: um ❌ que na verdade
está coberto em outro PDF, ou um ✅/🟡 que só menciona o termo de passagem
sem ensinar de verdade. Ao notar isso durante uma sessão:

1. Registrar no campo "observações de gap" da ficha do dia
   (`docs/concursos/sefaz-sc-2026/sessoes/AAAA-MM-DD.md`).
2. Propor a correção pontual em `mapa-assuntos-edital.md` como diff, pedindo
   aprovação — não é preciso reabrir a triagem inteira do bloco por um único
   assunto divergente.
3. Não recalcular o mapa inteiro a cada achado isolado — um recheck
   consolidado faz mais sentido em cadência semanal.

## PDF mesclado do dia (legado SEFAZ SC)

Usado só no SEFAZ SC, registrado aqui pra entender o material arquivado — fluxo por dia de calendário:
junto de cada ficha de sessão, gerar o manifesto JSON e rodar
`dias/montar_dia.py` pra produzir um único PDF por dia, com as páginas na
ordem de leitura sugerida (não necessariamente a ordem do PDF original) e
capa de rastreabilidade. Ver `dias/montar_dia.py` (docstring) pro formato do
manifesto. Gerar os manifestos/PDFs de todos os dias do bloco junto com as
fichas, na mesma leva — não esperar o dia chegar pra montar.

**Este fluxo por dia não é usado em editais novos** — ver
`docs/requisitos-alinhamento-fatiamento-pdf-bloco.md` pro motivo. Editais novos usam o fluxo
por bloco de assunto abaixo.

## PDF fatiado por bloco de assunto (editais novos)

Depois da triagem de um bloco aprovada, pra cada assunto (não por dia): montar o manifesto por
assunto e rodar `dias/montar_bloco.py` pra cortar o material em pedaços de leitura de tempo
aproximadamente igual (`minutos_por_bloco`, default 60 — valor fixo combinado com o SGE, não
mudar sem avisar), sem data de calendário — quem decide qual pedaço estudar em qual dia é a
escada do SGE. Ver `dias/montar_bloco.py` (docstring) pro formato do manifesto e
`docs/arquitetura-integracao-planejamento-sge.md` §4/§5 pro desenho completo.

**O manifesto é onde se prova que nada ficou de fora** (formato completo na docstring de
`dias/montar_bloco.py`). Ao montar cada um a partir da triagem:

- `subitens`: as partes do assunto fino exatamente como estão no mapa (o que vem separado
  por vírgula/ponto-e-vírgula). Toda fonte diz em `cobre` quais subitens ensina. Subitem
  sem página **só passa declarado em `lacunas`, com motivo** — o mesmo ❌ do mapa.
- `descartes`: o que a triagem decidiu deixar de fora (as "decisões de descarte"), com motivo.
- `paginas` é a **posição no PDF** (contador do leitor, a mesma de `buscar_indice.py`),
  nunca o número impresso na apostila.
- **Fixação entra sempre:** questões comentadas, lista de exercícios e resumo de cada aula
  vão como fonte `"tipo": "fixacao"`, logo depois da teoria correspondente. O script nunca
  mistura fixação com teoria no mesmo bloco. Use `minutos_por_pagina` por fonte quando o
  ritmo for diferente (lei seca, código, questões).
- Rodar primeiro com `--validar` (confere tudo e mostra o corte, sem gerar nada). Qualquer
  erro — arquivo inexistente, faixa invertida, página fora do PDF, página repetida, subitem
  sem cobertura — faz o script parar sem gerar nada.
- O corte cai em troca de fonte ou início de seção do PDF (marcadores), entre 75% e 125% do
  alvo. Sem fronteira natural, corta no alvo e marca "corte no meio de seção".
- **Ler `<assunto>_cobertura.md` antes de subir pro Drive:** subitem → páginas, a primeira
  linha de cada faixa (se não bate com o esperado, a numeração está deslocada), descartes e
  alertas por segmento.
- Assunto já fatiado (e talvez já exportado) não é refatiado sem `--refatiar`: o SGE nunca
  apaga segmento, então refatiar deixa os antigos lá ao lado dos novos.
- Testes do fatiador: `python -m unittest dias/test_montar_bloco.py`. Testes do caminho
  canonizar → orçamento → publicar → exportar, incluindo o contrato de colunas com o SGE, e
  do worker do material: `python -m unittest discover -s integracao -p "test_*.py"`.

O script já gera os PDFs no layout combinado com o SGE:
`blocos/<assunto-slug>/segmento-NN.pdf` dentro do `--saida-dir`. Depois de gerar:
1. Rodar `integracao/canonizar_assuntos.py --adicionar-pedacos` pra registrar a lista em
   `canonico.db` (campo `arquivo` ainda com o caminho local).
2. Publicar no Drive: `python integracao/publicar_drive.py --db integracao/canonico.db
   --edital <EDITAL> --saida-dir <o mesmo de montar_bloco> --remoto <remoto rclone>`
   (use `--simular` antes). Sobe cada PDF com `rclone`, pega o link compartilhável e grava
   no lugar do caminho local — é esse link, não o caminho, que vai no `segmentos.csv` e
   que o botão "Abrir material" do SGE abre. Pedaço que já tem link é pulado, então
   rodar de novo depois de uma falha continua de onde parou. Registrar pedaços de novo
   (passo 1) volta os caminhos locais: publique outra vez.
3. Exportar a pasta do concurso, já no formato do SGE
   (`docs/arquitetura-integracao-planejamento-sge.md` §8.1):
   `python integracao/exportar_sge.py --db integracao/canonico.db --edital <EDITAL>
   --nome "<nome>" --data-prova AAAA-MM-DD --saida-dir <Drive>/SGE-Importacao/<slug>`
   — gera `assuntos.csv`, `segmentos.csv` e `concurso.json`. No SGE, o concurso só é
   importado quando `CONCURSO_ATIVO=<slug>` (ADR-039 deles).

Pro orçamento (estágio 4), `integracao/calcular_orcamento.py --blocos-por-dia N` aceita
ritmo direto em "blocos por dia" em vez de minutos — conversão interna via
`minutos_por_bloco`, nunca exportado ao SGE. A `ordem` que ele grava é peso, depois a
**ordem do mapa de assuntos** (a do lote registrado) — no SGE ela decide qual assunto da
disciplina entra primeiro na frente, então é ordem pedagógica. Registre o lote na ordem
do mapa.

## Rascunho de Anki

Ao final de uma triagem (ou sessão), gerar `anki/cards_bloco_<nome>.json`
com os pontos-chave identificados, seguindo as regras do método
(`docs/concursos/sefaz-sc-2026/plano-estudos-sefaz-sc-2026.md`, seção "Sistema de flashcards"):

- **cloze** → leis, classificações, decoreba
- **basic** → "quando usar X em vez de Y" (não "defina X")
- **basic_reversed** → sigla ↔ significado
- Cards atômicos: um fato por card
- Deck: `<Concurso>::<Trilha>::<Bloco>` (estrutura de referência em
  `docs/concursos/sefaz-sc-2026/inventario-materiais-sefaz-sc.md`). Card de assunto canônico
  comum a vários editais não se duplica por concurso

Rodar `anki/anki_gerar.py` pra converter em CSV importável. **O rascunho é
pra revisão humana antes de importar** — não é pra importar direto sem olhar.

## Canal com o SGE (SGE-Concursos)

Dois sistemas separados, cada IA só escreve no próprio repositório — nunca
acesso de escrita cruzado.

**Exceção registrada (2026-10-14), pedida pelo usuário:** uma sessão do SGE trabalhou
neste repositório, numa branch própria (`integracao-sge`) e seguindo este `CLAUDE.md`,
para alinhar a exportação ao formato do SGE e fechar o caminho até o Drive. A regra acima
continua valendo para o dia a dia; uma nova exceção precisa de novo pedido explícito.

**Segunda exceção (2026-10-15), pedida pelo usuário:** esta sessão escreveu no SGE-Concursos,
na branch `exportacao-planejamento` (endpoint `GET /api/concursos/{id}/planejamento`) e mesclou a
Sprint 18 em `main` de lá. Também vale só para aquele pedido.

**Terceira exceção (2026-10-17), pedida pelo usuário:** uma sessão do SGE escreveu aqui, na
branch `material-automatico`, o worker do material (`integracao/worker.py`, `acervo.py`,
`sge_api.py`, `triagem_ia.py`, `Dockerfile`), para a Sprint 19 de lá. Vale só para aquele
pedido.

**Antes de começar qualquer trabalho que toque a integração com o SGE**
(fatiamento de blocos, segmentos, chaveExterna, ADR-037, ou qualquer
novidade do lado deles), confira o repositório público
`github.com/Allandpn/SGE-Concursos` (leitura pública, nunca escrita) nestes
arquivos, nesta ordem, comparando com o que você já sabe/implementou:

1. `docs/requisitos-planejamento-blocos-de-conteudo.md` — nosso canal
   principal de pedidos vindos do SGE. Preste atenção a qualquer seção
   nova ou alterada, especialmente as marcadas "Requisito novo" ou
   "Requisito especulativo" (olhe a data).
2. `docs/00A_ADR.md`, ADR-037 — decisão de infraestrutura entre os dois
   sistemas (Google Drive + rclone). Confira se a versão mudou desde a
   última checagem.
3. `especificacao/02_JORNADAS.md`, seção "Segunda importação: segmentos de
   material" (dentro de J-1) — formato exato do CSV de segmentos que o SGE
   espera. Qualquer coluna nova ou obrigatoriedade mudada aqui nos afeta.
4. `especificacao/01_DOMINIO.md`, §10 (tabela de regras D-xx), de D-50 em
   diante — regras que nasceram da integração conosco.
5. `PROGRESSO.md`, seção "Sprint 10 · Integração externa — planejamento" —
   estado real de implementação do lado do SGE: o que já está em produção
   e testado vs. o que ainda é só decisão de documento.

**Depois de ler, resuma pra mim — sem implementar nada sozinho:**
- O que mudou desde a última vez (se nada, diga "nada novo").
- O que, dentre as mudanças, exige alguma ação ou decisão nossa (ex.: campo
  novo a exportar, formato de CSV mudado).
- O que é só informativo, sem ação necessária.

**Nosso canal de saída, pro SGE:** `docs/requisitos-sge-integracao.md` e
`docs/arquitetura-integracao-planejamento-sge.md` — só cresce, nunca
reescrito por cima.

**Nada lido do lado deles vira código ou muda nossa arquitetura sozinho.**
É sugestão a avaliar comigo, nunca aplicada automaticamente.

## Regras gerais

- **Sempre que uma nova descoberta contradisser ou enriquecer o que já está documentado**
  (ex: uma fonte melhor achada depois, um gap que na verdade não existe, um status
  desatualizado), **atualizar a documentação existente relevante no mesmo momento**
  (`mapa-assuntos-edital.md`, `inventario-materiais-sefaz-sc.md`, triagens já escritas)
  — não deixar a descoberta só registrada na conversa. Continua valendo mostrar o diff
  antes de gravar `docs/*.md`.
- Nunca sobrescrever `docs/*.md` sem mostrar o diff antes.
- Nunca reindexar o acervo inteiro sem necessidade — `indexador.py` já é
  incremental (só processa arquivo novo/alterado).
- Ao encontrar um gap real (assunto não coberto no acervo), documentar
  explicitamente — não inventar conteúdo pra "preencher" a lacuna.
