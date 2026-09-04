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

Campos sugeridos: `nome`, `data da prova`, `tempo de estudo disponível` (opcional), `status`
(ativo/concluído).

Motivo: o candidato estuda pra mais de um concurso ao longo do tempo (o acervo já referencia
material de SEFAZ CE / TCE-SC, por exemplo). Sem essa entidade não dá pra ter peso/ordem por
contexto de prova, nem uma futura priorização entre provas concorrentes ativas ao mesmo tempo.

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
