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
| 2 | Triagem contra o acervo | Mapa de assuntos do estágio 1 | Busca no índice, decide cobertura/gap por assunto — fluxo já existente (ver `CLAUDE.md`, "Fluxo de uma triagem de bloco") | `mapa-assuntos-edital-<concurso>.md` + `docs/triagens/*` | Humano aprova diff (regra já existente) |
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
