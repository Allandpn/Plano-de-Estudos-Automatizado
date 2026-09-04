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
- Comunicação entre os dois via Tailscale (mesma rede já usada hoje pra sync do
  `indice.db`/Drive entre PCs — mas este fluxo é PC→Pi, separado daquele).
- **O planejamento é autocontido durante a análise**: não depende de conectividade com o SGE
  pra decidir nomes canônicos, pesos ou UUIDs — o registro histórico de assuntos canonizados
  vive só no lado do planejamento (ver seção 5). O único ponto de contato de rede necessário é
  a exportação final (estágio 5 do pipeline).
- Formato da exportação (CSV vs. chamada direta a um endpoint de import) é detalhe de
  implementação em aberto — decidir quando o SGE tiver o endpoint pronto para receber o novo
  formato (ver `docs/requisitos-sge-integracao.md`, seção 4).

## 4. Pipeline

| # | Estágio | Entrada | O que faz | Saída | Gate de validação |
|---|---|---|---|---|---|
| 1 | Leitura do edital | PDF do edital | IA extrai conteúdo programático (assuntos finos) e o quadro de distribuição de questões (peso por disciplina, quando o edital granular isso) | Rascunho de mapa de assuntos + pesos candidatos | Humano revisa/corrige antes de seguir |
| 2 | Triagem contra o acervo | Mapa de assuntos do estágio 1 | Busca no índice, decide cobertura/gap por assunto — fluxo já existente (ver `CLAUDE.md`, "Fluxo de uma triagem de bloco") | `mapa-assuntos-edital-<concurso>.md` + `docs/triagens/*` | Humano aprova diff (regra já existente) |
| 3 | Canonicalização de assuntos | Assuntos triados + registro histórico de canônicos (seção 5) | IA compara semanticamente cada assunto novo contra os já canonizados de editais anteriores; propõe match existente ou novo | Nome canônico + UUID (reaproveitado ou recém-mintado) por assunto | Humano confirma quando o match é ambíguo |
| 4 | Orçamento de tempo / ordem | Assuntos canonizados + peso + volume (páginas identificadas na triagem) + dias até a prova + tempo/dia disponível | Fórmula determinística: tempo proporcional a peso × volume, dentro do tempo disponível. Quando o total estoura o prazo, IA propõe compressão/corte com justificativa explícita | Ordem de estudo + tempo estimado por assunto, específicos daquele edital | Validação leve quando houve compressão/corte |
| 5 | Exportação | Tudo acima | Gera o payload pro SGE (ver seção 8) | Import no SGE (Edital + relação Edital↔Assunto) | — |

## 5. Modelo de dados mantido pelo planejamento

Isso é uma camada nova, agregando por cima do que já existe (mapa-assuntos por edital,
triagens por bloco) — não substitui esses artefatos, que continuam fiéis à redação de cada
edital individualmente.

**Registro canônico de assuntos** (novo, persistente, atravessa múltiplos editais):
- `uuid` — identidade estável, mintada na primeira vez que o assunto é canonizado
- `nome_canonico`, `disciplina`
- lista de origens: `(edital, redação original naquele edital)` — pra rastreabilidade, permite
  responder "de onde veio esse assunto" mesmo depois de canonizado

**Por par (edital, assunto canônico)**:
- `peso`, `ordem`
- `referência_material` (apostila + página, quando identificado na triagem)
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

## 7. Fora do escopo do planejamento

- Calendário dia a dia (isso é do SGE).
- Estado de aprendizado / histórico de revisões (isso é do SGE).
- Priorização entre editais concorrentes ativos simultaneamente (isso é do SGE, quando
  existir mais de um edital ativo — ver `docs/requisitos-sge-integracao.md`, seção 6).

## 8. Formato de exportação

Payload por linha (assunto dentro de um edital):

| Campo | Observação |
|---|---|
| `uuid` | sempre preenchido — identidade do assunto canônico (seção 5) |
| `disciplina` | |
| `assunto` | nome canônico, não a redação literal do edital |
| `edital` | referência ao Edital sendo importado |
| `peso` | do quadro de distribuição de questões, ou "não determinado" |
| `ordem` | do estágio 4 |
| `referência_material` | opcional |

Semântica de import: **sempre upsert por `uuid`** — nunca "criar quando vazio". O SGE nunca
gera `id` de Assunto por conta própria nesse fluxo.
