# Arquitetura de Integração — Sistema de Planejamento × SGE-Concursos

Fonte da verdade pra como este sistema (o "planejamento") vai gerar planos de estudo por
edital e alimentar o SGE-Concursos. Qualquer mudança de comportamento nessa integração
**atualiza este documento primeiro**, e só depois vira código — mesma disciplina que o SGE já
usa com `especificacao/`.

Ver também `docs/requisitos-sge-integracao.md` — a mesma integração, traduzida pro
vocabulário e pro repositório do SGE, pra levar pra lá.

---

## 1. Contexto e objetivo

Hoje o cronograma de estudo (`cronograma-detalhado-sessoes-sefaz-sc.md`) é montado e mantido
manualmente. A visão de longo prazo: informar um concurso, subir o edital, definir o tempo de
estudo disponível, e o sistema cuidar do resto — leitura do edital, triagem contra o acervo,
geração do plano, e entrega desse plano pro SGE-Concursos gerenciar dia a dia (sessões,
revisão espaçada, "o que fazer hoje").

## 2. Divisão de responsabilidades

| Responsabilidade | Dono |
|---|---|
| Definir o escopo do concurso (nome, data da prova, disciplinas, assuntos, segmentos) | **Planejamento** |
| Ler o edital, extrair conteúdo programático e peso | **Planejamento** |
| Triar o acervo, decidir cobertura/gap por assunto | **Planejamento** |
| Canonicalizar assuntos entre editais diferentes | **Planejamento** |
| Calcular ordem de estudo e orçamento de tempo por assunto | **Planejamento** |
| Sessão de estudo, revisão espaçada (escada), "o que fazer hoje" | **SGE** |
| Estado de aprendizado (nível, histórico, dificuldade percebida) | **SGE** |
| Priorização entre editais concorrentes ativos ao mesmo tempo | **SGE** (futuro) |

## 3. Topologia / infraestrutura

- **Planejamento roda no PC pessoal**, como processo sob demanda (pipeline em lote) — não é
  um serviço 24/7. Roda uma vez por edital novo, ou por bloco/correção pontual.
- **SGE roda no Raspberry Pi**, junto do Pi-hole, como serviço sempre disponível.
- **Sem chamada de rede direta entre os dois sistemas.** Decisão do lado do SGE (ADR-037,
  ver `docs/requisitos-alinhamento-fatiamento-pdf-bloco.md` §5): os artefatos da exportação
  (estágio 6) chegam via **Google Drive**, não via Tailscale/endpoint direto — planejamento e
  SGE têm ritmos de disponibilidade diferentes (sob demanda vs. 24/7), e exigir os dois online
  ao mesmo tempo seria fricção desnecessária.
  - O **CSV** (assuntos + segmentos de material) é colocado numa pasta do Drive; o SGE
    sincroniza essa pasta via `rclone`, no próprio ritmo dele — o planejamento não precisa
    saber que o Pi existe nem se está acessível.
  - Os **PDFs dos segmentos não vão pro Pi** — ficam no Drive, compartilhados com link; esse
    link é o valor que entra em `referência_material` (seção 8), não um caminho local.
  - Estrutura de pasta combinada: `SGE-Importacao/<slug-do-concurso>/assuntos.csv` +
    `concurso.json` (nome + data da prova, ver seção 5/8) + `blocos/<assunto-slug>/segmento-NN.pdf`.
    `dias/montar_bloco.py` já gera o layout de `blocos/` localmente
    (`<saida-dir>/blocos/<assunto-slug>/segmento-NN.pdf`); upload pro Drive e geração do
    link compartilhável ainda são passos manuais (sem automação `rclone`/Drive API do lado
    do planejamento por enquanto).
- **O planejamento é autocontido durante a análise**: não depende de conectividade com o SGE
  pra decidir nomes canônicos, pesos ou UUIDs — o registro histórico de assuntos canonizados
  vive só no lado do planejamento (ver seção 5). Nem a análise nem a exportação (estágio 6)
  dependem do SGE estar online — só de uma pasta do Drive estar acessível.
- Formato exato do CSV de exportação: ver seção 8.

## 4. Pipeline

| # | Estágio | Entrada | O que faz | Saída | Gate de validação |
|---|---|---|---|---|---|
| 1 | Leitura do edital | PDF do edital | IA extrai conteúdo programático (assuntos finos) e o quadro de distribuição de questões (peso por disciplina, quando o edital granular isso) | Rascunho de mapa de assuntos + pesos candidatos | Humano revisa/corrige antes de seguir |
| 2 | Triagem contra o acervo | Mapa de assuntos do estágio 1 | Busca no índice, decide cobertura/gap por assunto — fluxo já existente (ver `CLAUDE.md`, "Fluxo de uma triagem de bloco") | `mapa-assuntos-edital-<concurso>.md` + `docs/concursos/sefaz-sc-2026/triagens/*` | Humano aprova diff (regra já existente) |
| 3 | Canonicalização de assuntos | Assuntos triados + registro histórico de canônicos (seção 5) | IA compara semanticamente cada assunto novo contra os já canonizados de editais anteriores; propõe match existente ou novo | Nome canônico + UUID (reaproveitado ou recém-mintado) por assunto | Humano confirma quando o match é ambíguo |
| 4 | Orçamento de tempo / ordem | Assuntos canonizados + peso + volume (páginas identificadas na triagem) + dias até a prova + tempo/dia disponível | Fórmula determinística: tempo proporcional a peso × volume, dentro do tempo disponível. Quando o total estoura o prazo, IA propõe compressão/corte com justificativa explícita | Ordem de estudo + tempo estimado por assunto, específicos daquele edital | Validação leve quando houve compressão/corte |
| 5 | Fatiamento do material por bloco | Páginas identificadas na triagem + `minutos_por_bloco` (parâmetro local, ver seção 6) | Corta o material de cada assunto em pedaços de leitura de tempo aproximadamente igual — mesmo critério de página que a triagem já usa, só muda o ponto de parada (`dias/montar_bloco.py`) | Sequência ordenada de pedaços por assunto (PDF + metadados de rastreio: arquivo, página inicial/final, tempo estimado) | — (determinístico) |
| 6 | Exportação | Tudo acima | Gera o payload pro SGE (ver seção 8) | Import no SGE (Edital + relação Edital↔Assunto) | — |

## 5. Modelo de dados mantido pelo planejamento

Isso é uma camada nova, agregando por cima do que já existe (mapa-assuntos por edital,
triagens por bloco) — não substitui esses artefatos, que continuam fiéis à redação de cada
edital individualmente.

**Concurso** (decisão de 2026-09-06, ver `docs/requisitos-alinhamento-fatiamento-pdf-bloco.md`
§9 — todo o escopo do concurso é responsabilidade do planejamento, nunca digitado manualmente
no SGE):
- `slug` — mesmo identificador usado na pasta do Drive (`SGE-Importacao/<slug>/`)
- `nome` — nome de exibição (ex.: "SEFAZ SC 2026")
- `data_prova`
- Disciplinas não têm entidade própria — continuam sendo só o atributo `disciplina` de
  cada assunto canônico (abaixo); a lista de disciplinas do concurso é derivável agrupando
  os assuntos por esse campo.

**Registro canônico de assuntos** (novo, persistente, atravessa múltiplos editais):
- `uuid` — identidade estável, mintada na primeira vez que o assunto é canonizado
- `nome_canonico`, `disciplina`
- lista de origens: `(edital, redação original naquele edital)` — pra rastreabilidade, permite
  responder "de onde veio esse assunto" mesmo depois de canonizado

**Por par (edital, assunto canônico)**:
- `peso`, `ordem`
- `referência_material` — lista ordenada de pedaços de leitura: `(ordem, arquivo,
  página_inicial, página_final, tempo_estimado_min)`, produzida pelo fatiamento (estágio 5)
- `volume_estimado` (páginas / tempo de leitura estimado)

## 6. Regras e princípios

Reaproveitados do método já em uso neste projeto (`CLAUDE.md`):
- Nunca inventar conteúdo pra preencher gap.
- Diff antes de gravar qualquer `docs/*.md`.
- Orçamento de busca por assunto (query direta → até 2 sinônimos → até 2 PDFs/~20 páginas →
  senão marcar gap e seguir).

Novos, específicos desta integração:
- **Nome canônico só muda pelo lado do planejamento.** O SGE nunca edita identidade de
  assunto — se precisar mudar, o ajuste entra pelo planejamento e é reexportado.
- **Renomear um canônico existente é migração explícita**, não uma reescrita solta: reaproveita
  o UUID já existente, nunca minta um novo só porque o nome mudou.
- **Peso vem do quadro de distribuição de questões do próprio edital.** Se o edital não
  granular peso por disciplina, marcar "peso não determinado" e pedir input manual — nunca
  estimar a partir de menções soltas em apostilas.
- **`dificuldadePercebida` nunca é preenchida pelo planejamento.** É território do SGE/escada,
  que mede isso a partir do desempenho real do candidato.
- **O planejamento nunca decide "quando" estudar dia a dia** — só a ordem de entrada dos
  assuntos e o orçamento de tempo agregado por assunto. O dia a dia real (o que muda com
  SUCESSO/PARCIAL/FALHA) é território exclusivo da escada do SGE.
- **O fatiamento do material nunca data um pedaço a um dia de calendário** — produz uma
  sequência ordenada de pedaços por assunto (estágio 5); é a escada do SGE quem decide, turno a
  turno, qual pedaço consumir (ver `docs/requisitos-alinhamento-fatiamento-pdf-bloco.md`).
- **O tamanho do bloco de leitura (`minutos_por_bloco`) é um valor fixo único, combinado entre
  os dois lados (60min) e documentado nos dois repositórios** — nunca uma consulta em tempo
  real ao SGE (mantém a autocontenção da seção 3). Se o SGE recalibrar esse parâmetro
  (evento raro, registrado em changelog), o número é espelhado manualmente aqui — não é
  esperado divergir em silêncio.
- **Quantos blocos por dia (`blocos_por_dia`) é parâmetro só do estágio 4 (orçamento)**,
  usado apenas pra checar se o volume total cabe até a prova — nunca é exportado nem
  comunicado ao SGE de nenhuma forma. `integracao/calcular_orcamento.py --blocos-por-dia`
  aceita esse número diretamente (convertido internamente via `minutos_por_bloco`).
- **Reteach em `FALHA` nunca aciona nova geração de pedaço** — o SGE reaproveita o ponteiro já
  entregue; o planejamento não precisa saber quantas vezes um assunto foi revisitado.

## 7. Fora do escopo do planejamento

- Calendário dia a dia (isso é do SGE).
- Estado de aprendizado / histórico de revisões (isso é do SGE).
- Priorização entre editais concorrentes ativos simultaneamente (isso é do SGE, quando
  existir mais de um edital ativo — ver `docs/requisitos-sge-integracao.md`, seção 6).

## 8. Formato de exportação

**`concurso.json`** — um por concurso, em `SGE-Importacao/<slug>/concurso.json`, ao lado
do CSV de assuntos (ver seção 3 e `docs/requisitos-alinhamento-fatiamento-pdf-bloco.md`
§9):

| Campo | Observação |
|---|---|
| `slug` | mesmo valor usado no nome da pasta |
| `nome` | nome de exibição do concurso |
| `data_prova` | formato ISO `AAAA-MM-DD` |

O SGE só armazena e exibe esses campos, nunca decide nada a partir deles (mesmo princípio
do `chave_externa_segmento`, seção 5 / `docs/requisitos-alinhamento-fatiamento-pdf-bloco.md`
§8).

**CSV de assuntos** — payload por linha (assunto dentro de um edital):

| Campo | Observação |
|---|---|
| `uuid` | sempre preenchido — identidade do assunto canônico (seção 5) |
| `disciplina` | |
| `assunto` | nome canônico, não a redação literal do edital |
| `edital` | referência ao Edital sendo importado |
| `peso` | do quadro de distribuição de questões, ou "não determinado" |
| `ordem` | do estágio 4 |
| `referência_material` | opcional — string JSON com a lista ordenada de pedaços (`ordem`, `arquivo`, `página_inicial`, `página_final`, `tempo_estimado_min`, `chave_externa_segmento`); `arquivo` é o **link compartilhável do Google Drive** do PDF daquele segmento (não um caminho local — ver seção 3), preenchido manualmente após o upload; o SGE só armazena e exibe, não interpreta (ver `docs/requisitos-sge-integracao.md` §3) |

Semântica de import: **sempre upsert por `uuid`** — nunca "criar quando vazio". O SGE nunca
gera `id` de Assunto por conta própria nesse fluxo.

O CSV e o `concurso.json` viajam pela mesma pasta do Google Drive sincronizada via `rclone`
do lado do SGE, não por chamada direta a um endpoint — ver seção 3.

### 8.1 Formato vigente (2026-10-14) — substitui o CSV único acima

O CSV único desta seção (`uuid,...,referencia_material` com segmentos em JSON) **nunca
bateu com o que o SGE lê** — achado numa análise dos dois repositórios. Importado como
estava, o assunto entraria sem `chaveExterna` e os segmentos seriam recusados. O contrato
é do lado que consome: `especificacao/02_JORNADAS.md` J-1 do SGE-Concursos (v1.6.0). O
texto acima fica como registro; vale este.

Pasta do concurso, `SGE-Importacao/<slug>/` (o slug é o nome da pasta, e o mesmo de
`docs/concursos/<slug>/` aqui):

| Arquivo | Colunas / campos |
|---|---|
| `assuntos.csv` | `disciplina,assunto,peso,ordem,chaveExterna` — `chaveExterna` = `uuid` canônico; peso `ALTO`/`MEDIO`/`BAIXO`, ou vazio quando "não determinado" (o SGE assume `MEDIO`); sem `id` |
| `segmentos.csv` | `chaveExternaSegmento,chaveExternaAssunto,ordem,arquivo,paginaInicial,paginaFinal,tempoEstimadoMin` — só quando há pedaços; `arquivo` = link do Drive |
| `concurso.json` | `{"slug", "nome", "dataProva"}` |

Gerado por `integracao/exportar_sge.py --saida-dir`. Do lado do SGE (Sprint 16, já feito):

- linha sem `id` com `chaveExterna` conhecida **atualiza** o assunto — o "upsert por uuid"
  que esta seção sempre pediu passa a existir de fato;
- só o **concurso-alvo ativo** (`CONCURSO_ATIVO=<slug>`, ADR-039 deles) é importado.
  Assunto canônico comum a dois editais mantém escada e histórico no SGE ao trocar de
  concurso; peso e ordem passam a ser os do concurso ativo. A entidade `Edital` com peso
  por edital (pedida em `docs/requisitos-sge-integracao.md` §2-§3) **não** foi adotada —
  ver §8 daquele documento.

### 8.2 Ordem pedagógica, publicação no Drive e o uso do tempo estimado (2026-10-14)

**Ordem (estágio 4) — correção.** `calcular_orcamento.py` desempatava assuntos de mesmo
peso **pelo nome**. No SGE, `ordem` decide qual assunto da disciplina entra primeiro na
frente de estudo (D-41 de lá), então a exportação mandava estudar "Bancos relacionais x
NoSQL" antes de "Modelagem conceitual" e "SQL avançado" antes de "SQL: DDL". Passa a ser
peso, depois a **ordem do mapa de assuntos** (a ordem em que o lote foi registrado). A
§4 fala em "tempo proporcional a peso × volume"; o código nunca fez isso — o tempo é só
volume × minutos por página, e peso só ordena e indica candidato a corte. Vale o código.

**Publicação (entre os estágios 5 e 6) — novo.** `integracao/publicar_drive.py` sobe os
PDFs de `blocos/` com `rclone` (o mesmo remoto que o SGE usa, ADR-037 de lá), pega o link
compartilhável de cada um e grava em `material_pedacos.arquivo`. Era o único passo
manual do caminho até o SGE, e nenhum comando fazia a parte de gravar o link. O caminho no
Drive repete o local (`blocos/<assunto-slug>/segmento-NN.pdf`): o material é do assunto
canônico, então dois editais que compartilham o assunto apontam pro mesmo PDF.

**Respostas aos pedidos do SGE de 2026-10-14**
(`docs/requisitos-planejamento-blocos-de-conteudo.md` de lá):

- §11 (formato dos arquivos): atendido por `exportar_sge.py` (§8.1 acima).
- §12 (segmento é leitura obrigatória): a `ordem` do segmento é a ordem de leitura do
  manifesto; descartes nunca viram segmento; fixação (questões comentadas, resumo) vira
  segmento próprio, como pedido.
- §13 (`tempoEstimadoMin` passa a preencher o tempo do registro): o tempo sai sempre de
  `minutos_por_pagina` (padrão 4). Como agora o usuário vê esse número toda vez que
  registra, vale declarar `minutos_por_pagina` por fonte sempre que o ritmo for outro
  (lei seca, questões comentadas, código) — um padrão errado vira correção manual em
  todo registro.

Testes: `integracao/test_integracao.py` (contrato de colunas com o SGE, ordem, publicação).

**Respostas ao pedido do SGE de 2026-10-15** (§14 de lá, Sprint 18, ADR-042/043 — ainda na
branch `claude/relaxed-bell-02ejxe` do SGE, não mesclada em `main` na data desta checagem):

- `concurso.json` agora é **lido** pelo SGE (cria/reativa pelo `slug`; `slug` e `nome`
  obrigatórios, `dataProva` opcional; arquivo inválido recusa a importação inteira).
  `exportar_sge.py` já grava os três campos (`slug` = nome da pasta, `nome` = `--nome`).
- **Adoção por nome:** se o usuário subir um edital pelo SGE (análise por IA), os assuntos
  nascem lá sem `chaveExterna`; ao exportarmos o mesmo nome (sem acento/caixa) na mesma
  disciplina, o SGE grava a chave no assunto existente em vez de duplicar. Consequência
  pra nós: **o nome do assunto no mapa segue a redação do edital**; nome diferente cria
  assunto novo.
- **Estágio 1 — caminho principal é o do planejamento** (decisão de 2026-10-15): o estágio 1
  daqui reaproveita o canônico e a triagem contra o acervo, coisa que a IA do SGE não faz.
  A análise por IA do SGE é um caminho de conveniência (ver o edital no app); se o usuário a
  usar antes, a exportação posterior só adota os assuntos por nome. O peso segue a mesma
  regra dos dois lados: por contagem de questões do edital (SGE: tercis, D-61); sem
  contagem, "não determinado" — nunca estimado.
- Ordem ocupada por assunto de outro edital deixou de recusar o arquivo (o assunto antigo
  vai pro fim da disciplina): nenhuma ação nossa.

**Revisão da decisão do estágio 1 (2026-10-15, mesmo dia, a pedido do usuário)** — substitui
o parágrafo "Estágio 1 — caminho principal é o do planejamento" acima (mantido por ser
documento que só cresce):

- **O SGE (com o eAgora) é o sistema principal** na experiência do usuário: é onde o edital
  é subido, onde a IA (OpenRouter, ADR-043 deles) separa os assuntos pelo cargo escolhido e
  traz banca, data da prova e peso por questões, e onde o usuário revisa e confirma. **A
  chave `OPENROUTER_API_KEY` vive só no SGE** (`.env` do Pi). O planejamento não chama IA
  nenhuma e não guarda chave.
- **O planejamento vira a retaguarda de material**, rodando sob demanda no PC: parte dos
  assuntos já confirmados no SGE e faz a triagem contra o acervo, a canonicalização, o
  fatiamento e a exportação dos segmentos pelo Drive (estágios 2–6). O estágio 1 daqui
  (leitura de edital por sessão do Claude Code) fica como alternativa, para quem não usa a
  análise do SGE.
- **Convergência por nome:** os assuntos nascem no SGE sem `chaveExterna`; o planejamento
  mantém o nome exatamente como veio do SGE, atribui o UUID canônico e exporta — o SGE adota
  por nome (§14 dos requisitos de lá) e ganha os segmentos.
- **Lacuna de entrada:** o `GET /api/assuntos/exportacao` do SGE devolve `id,disciplina,
  assunto,peso,ordem,dificuldadePercebida` de todos os assuntos ativos, sem `chaveExterna`,
  sem separar por concurso e sem os dados do concurso. Pedido de ajuste registrado em
  `docs/requisitos-sge-integracao.md` §10.

## 9. Material preparado sozinho, no Pi (2026-10-17)

**Pedido do usuário:** "subir um edital, escolher um cargo, e todo o resto será feito pelo
sistema". Do lado do SGE: ADR-044 (substitui ADR-037), `01_DOMINIO` v1.24.0 (§3.10, D-64,
D-65) e `docs/SPRINT-19-MATERIAL-AUTOMATICO.md`, todos no repositório de lá.

**O que muda aqui.** O caminho principal deixa de ser uma sessão em chat no PC e passa a
ser `integracao/worker.py`, um contêiner no mesmo `docker compose` do SGE, no Pi:

| Antes (§3–§8) | Agora |
|---|---|
| Alguém pede ao Claude Code no PC "leia o edital", "triagem do bloco X" | O usuário confirma o edital no SGE; o worker percebe sozinho |
| Triagem, canonicalização e manifesto julgados no chat, com aprovação | A IA (OpenRouter, pelo proxy do SGE) escolhe as páginas; o validador estrito do `montar_bloco` decide se vale |
| `canonico.db` dá o UUID; o SGE casava por nome | O SGE dá a `chaveExterna` na confirmação (D-64); o worker só a usa |
| `publicar_drive.py` + Drive + cron com `CONCURSO_ATIVO` | PDF gravado em `MATERIAL_DIR`, servido pelo SGE em `/material/`; segmentos importados por HTTP interno |
| Gap da triagem anotado no mapa de assuntos | Lacuna registrada no SGE com motivo (D-65), visível na tela |

**Como o worker decide** (docstrings de `worker.py` e `triagem_ia.py`):

1. Assunto do concurso-alvo **sem segmento e sem lacuna** — o estado mora no SGE;
   reiniciar o worker retoma de onde parou.
2. Busca no `indice.db` com os termos do nome do assunto (sem conectivos) → até 6 arquivos,
   cada um com as páginas que citam e o sumário.
3. A IA recebe o assunto dividido em partes (vírgula e ponto e vírgula, como o mapa faz) e
   devolve as fontes no formato do manifesto. Nada inventado: o que não acha vira lacuna.
4. `montar_bloco` valida. Recusou: **uma** nova tentativa, com os erros no pedido. Recusou
   de novo: lacuna "não passou na validação", com os erros.
5. Aceito: fatia, importa o `segmentos.csv` (arquivo `/material/blocos/...`) no SGE.
6. IA fora do ar (sem chave, sem crédito) **não** é lacuna: o ciclo para e tenta depois.

**O índice do PC funciona no Pi sem conversão:** o caminho é reconstruído como
`ACERVO_DIR/<curso>/<nome_arquivo>`, não pelo caminho absoluto gravado na indexação.
A indexação continua no PC (pesada demais para o Pi 4); o `indice.db` e as apostilas são
copiados para o SSD do Pi.

**O que continua valendo:** o fluxo em chat do `CLAUDE.md` vira modo manual — útil para
revisar uma lacuna, refazer a triagem de um assunto com cuidado, ou trabalhar o legado
SEFAZ. Exportação por arquivo (`exportar_sge.py`, `publicar_drive.py`) segue funcionando
como legado.

Testes: `integracao/test_worker.py` (SGE e IA falsos, PDFs sintéticos, índice com caminho
de outra máquina), `integracao/test_sge_api.py` (HTTP real local).

### 9.1 Mapa de início das páginas (2026-10-17)

**Achado na primeira preparação real** (SEFAZ SC 2026, Ciências da Computação, no Pi):
a IA via só o trecho das páginas onde o termo aparecia e o sumário do PDF, e não onde
um tema termina e o vizinho começa. Em apostilas-resumo e listas de questões, as faixas
transbordavam — acentuação dentro de "crase", voz passiva dentro de "ortografia".

**Correção:** cada arquivo candidato leva também o **início de cada página** da região
das ocorrências (todas elas, com 3 páginas de margem, até 45 páginas), sem o número de
rodapé; o prompt manda começar e terminar a faixa nas mudanças de tema e deixar de fora
a página em dúvida. O validador continua o mesmo.

**Para avaliar sem gravar nada:** `python integracao/worker.py --ensaiar "<assunto>"
--disciplina "<disciplina>"` mostra a escolha, com o início da primeira e da última
página de cada faixa, e se passaria na validação.

Do lado do SGE, o material já preparado pode ser refeito (D-66 de lá): os segmentos são
arquivados e o assunto volta a "a preparar".

