# Requisitos de Integração com o Sistema de Planejamento

Documento pra levar ao repositório do SGE-Concursos (uso com a IA de lá), descrevendo o que o
SGE precisa suportar pra receber dados gerados pelo sistema de planejamento
(`PlanoEstudosSefazSC`, projeto separado). Cobre só a integração — outros ajustes do SGE ficam
fora desta rodada (ver seção 7).

Espelha `docs/arquitetura-integracao-planejamento-sge.md` do lado do planejamento — mesma
integração, dois vocabulários.

---

## 1. Contexto

O sistema de planejamento é um projeto separado que lê editais de concurso, triagem um acervo
de apostilas contra o conteúdo programático, e monta um plano de estudo por edital. Hoje o SGE
só recebe `Disciplina`/`Assunto` via import manual direto (Jornada J-1). A proposta é que essa
mesma via passe a ser alimentada também por essa fonte externa automatizada, com o formato de
import levemente estendido.

## 2. Nova entidade: `Edital`

Campos: `nome`, `data da prova`, `tempo de estudo disponível` (opcional), `status`
(ativo/concluído).

Motivo: o candidato estuda pra mais de um concurso ao longo do tempo (o acervo já referencia
material de SEFAZ CE / TCE-SC, por exemplo). Sem essa entidade não dá pra ter peso/ordem por
contexto de prova, nem uma futura priorização entre provas concorrentes ativas ao mesmo tempo.

**Decisão (2026-09-06):** `nome` e `data da prova` não são digitados manualmente no SGE —
vêm de um manifesto enviado pelo planejamento, `concurso.json`, na mesma pasta do Drive do
CSV de assuntos (`SGE-Importacao/<slug>/concurso.json`). O SGE só armazena e exibe esses
dois campos, nunca decide nada a partir deles — mesmo princípio do `chaveExterna` (§3). Ver
`docs/arquitetura-integracao-planejamento-sge.md` §5/§8 do lado do planejamento pro formato
exato.

## 3. `Assunto`: peso e ordem deixam de ser fixos, viram atributos da relação `Edital`↔`Assunto`

Motivo: o mesmo assunto pode ter peso ALTO num edital e BAIXO (ou nem aparecer) em outro. Se
peso/ordem ficam presos ao `Assunto`, ele não pode ser reaproveitado entre editais sem se
contradizer.

Proposta: tabela de junção N:N (`EditalAssunto` ou nome equivalente) carregando `peso` e
`ordem` — específicos daquele par edital+assunto.

**O que continua pertencendo ao `Assunto`** (compartilhado entre editais, porque é sobre o
candidato, não sobre a prova):
- nome canônico + disciplina
- estado da escada: nível, histórico de sessões/erros, próxima revisão
- `dificuldadePercebida`

**Campo novo, opcional, no `Assunto`:** referência de material (ex: apostila + página) —
estático, vem do planejamento. O SGE só armazena e exibe, não interpreta nem decide a partir
dele.

Formato: string JSON com uma lista ordenada de pedaços de leitura (`ordem`, `arquivo`,
`página_inicial`, `página_final`, `tempo_estimado_min`) — um por bloco de ~45–75min gerado pelo
fatiamento do lado do planejamento (ver `docs/arquitetura-integracao-planejamento-sge.md`
§4/§5). Continua sendo só um ponteiro: o SGE não abre nem interpreta o conteúdo, só guarda e
exibe pro candidato saber onde parou.

## 4. Import: `id` passa a ser UUID gerado externamente, sempre upsert

Contrato atual (Jornada J-1): `id` vazio = cria, preenchido = atualiza — SGE decide o `id` na
criação.

Contrato proposto: o `id` do `Assunto` (e possivelmente do `EditalAssunto`) é sempre um UUID já
definido pelo sistema de planejamento antes do envio. **O SGE nunca mais gera `id` de
`Assunto` sozinho nesse fluxo** — sempre recebe preenchido e faz upsert por ele.

Motivo: o planejamento precisa reconhecer "este assunto já existe" de forma estável entre
editais diferentes, mesmo quando o mesmo conceito foi escrito com palavras diferentes em cada
edital. Ele resolve isso do próprio lado (registro histórico + comparação semântica) e só
informa ao SGE qual identidade usar — o SGE não precisa (nem deve) tentar essa reconciliação.

## 5. O que o SGE não precisa resolver

- Não decide se um assunto de um import novo é "o mesmo" de um já existente — isso já vem
  resolvido no `uuid` enviado.
- Não interpreta "onde estudar" — só guarda a referência de material que vier, sem lógica em
  cima dela.
- Não decide peso/prioridade sozinho — recebe pronto do import.

## 6. Consequência a avaliar depois (não bloqueante agora)

Com múltiplos `Edital` podendo estar ativos ao mesmo tempo (datas de prova diferentes), a
lógica de "o que fazer hoje" da escada eventualmente vai precisar equilibrar urgência entre
eles. Não precisa ser resolvido nesta rodada — é um efeito direto do modelo N:N que vale um ADR
próprio quando chegar a hora.

## 7. Fora de escopo desta doc

Outros ajustes/sprints do SGE não relacionados a esta integração (ex: frontend do Sprint 9)
ficam de fora — tratar separadamente, no fluxo normal de `especificacao/` do próprio SGE.

## 8. Resposta do SGE às §2-§4 (registrada em 2026-10-14)

- **§2/§3 (entidade `Edital`, peso por edital):** não adotada por ora. O SGE decidiu por
  **um concurso-alvo ativo por vez** (ADR-039 deles): peso e ordem vêm do edital ativo,
  e a escada/histórico de um assunto canônico sobrevive à troca de concurso porque a
  identidade é a `chaveExterna` (= nosso `uuid`). `Edital` volta à mesa se um dia for
  preciso estudar para dois concursos com pesos diferentes ao mesmo tempo.
- **§4 (upsert por UUID):** adotado — linha sem `id` com `chaveExterna` conhecida
  atualiza o assunto (`02_JORNADAS` J-1 v1.6.0 deles).
- Formato de arquivo vigente: `docs/arquitetura-integracao-planejamento-sge.md` §8.1.

## 9. Checagem do canal de leitura em 2026-10-15

Lido o SGE-Concursos (`main` + branch `claude/relaxed-bell-02ejxe`, Sprint 18) e o eAgora
(app Android do SGE, só consome a API deles). Novidade: requisitos §14 (SGE lê
`concurso.json`, adota assunto sem chave por nome, ordem ocupada não recusa). Nenhuma
mudança de formato de arquivo. Resposta em
`docs/arquitetura-integracao-planejamento-sge.md` (final do documento).

## 10. Pedido ao SGE (2026-10-15): entregar ao planejamento os assuntos de um concurso

Contexto: decidido que o SGE é o sistema principal (leitura do edital por IA, ADR-043 deles)
e o planejamento faz a triagem e o fatiamento a partir dos assuntos confirmados lá
(`docs/arquitetura-integracao-planejamento-sge.md`, "Revisão da decisão do estágio 1").

Hoje `GET /api/assuntos/exportacao` serve a outro propósito (round-trip do cadastro) e não
basta. **Pedido:** uma saída por concurso, na pasta `SGE-Importacao/<slug>/` do Drive ou por
endpoint, com:

1. `concurso.json` (`slug`, `nome`, `dataProva`, e banca/cargo se o SGE os guarda);
2. lista dos assuntos da cobertura daquele concurso, na ordem do edital: `disciplina,
   assunto, peso, ordem, chaveExterna` (vazia se o assunto nasceu na análise por IA),
   mais o número de questões da disciplina quando existir;
3. indicação de assunto com **correspondência** a um assunto já existente (D-63), para o
   planejamento reaproveitar o canônico.

Nada disso é implementado por nós: a decisão de formato e de onde expor é do SGE. Até lá, o
caminho manual funciona (copiar o CSV de exportação atual para o planejamento).

**Atendido em 2026-10-15** (por pedido do usuário, escrito direto no SGE e já em `main` de lá): `GET /api/concursos/{id}/planejamento`
devolve `slug, nome, cargo, banca, dataProva` e os assuntos na ordem do edital
(`disciplina, assunto, peso, ordem, chaveExterna`). Ficaram de fora, por não serem guardados
depois da confirmação: número de questões por disciplina e correspondência com assunto
existente. Suíte do SGE 170/170 verde.

