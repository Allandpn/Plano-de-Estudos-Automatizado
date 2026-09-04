# Resumo pra continuar no repositório do SGE-Concursos
### Contexto trazido da conversa no projeto "PlanoEstudosSefazSC" (triagem/indexação de apostilas)

## O que é o outro projeto (PlanoEstudosSefazSC)

Sistema de apoio ao estudo pro concurso SEFAZ SC 2026 (prova 22/11/2026). Indexa ~2639
PDFs de apostilas (Estratégia Concursos) num SQLite full-text, e faz "triagem" por bloco do
edital: cruza a lista oficial de assuntos finos (`mapa-assuntos-edital-sefaz-sc.md`) contra
o acervo, decide o que está coberto/gap, e gera material de estudo (fichas diárias, PDFs
mesclados por dia, rascunho de cards Anki).

Repositório: `github.com/Allandpn/Plano-de-Estudos-Automatizado` (privado).

## O que foi discutido: integrar os dois sistemas

Ideia do usuário: usar o SGE-Concursos (gestão de sessões/revisão espaçada) como o "motor
de processo" pro que a triagem do outro projeto descobre — em vez de gerenciar cronograma
manualmente como hoje. Visão final: informar um concurso, postar o edital, definir tempo de
estudo, e o sistema combinado cuida do resto.

## O que encontrei ao ler o repositório do SGE-Concursos (clone local, só leitura)

- Stack: Java 21, Spring Boot 4.1, PostgreSQL 17, Docker no Raspberry Pi via Tailscale.
- Metodologia rígida: `especificacao/` é fonte única de verdade — nada de código sem doc
  primeiro (regra central do `CLAUDE.md` de lá).
- Estado: Sprints 1-8 com documento técnico e código escritos ("feito"), mas ainda sem
  verificação real no Pi; Sprint 9 (frontend) não começou.
- **Domínio central:** `Disciplina` → `Assunto` → `Sessao`/`Revisao`/`Erro`. A `Revisao`
  usa uma "escada" de 6 níveis com roteamento por resultado (SUCESSO sobe, PARCIAL repete,
  FALHA regride — regra D-07).
- **Já existe importação em lote de Disciplina/Assunto** (Jornada J-1, Sprint 2, "feito"),
  via CSV:
  ```csv
  disciplina,assunto,peso,ordem
  Banco de Dados,Modelagem Conceitual de Dados (MER e DER),ALTO,1
  ```
  Colunas: `id` (vazio=cria, preenchido=atualiza), `disciplina` (obrigatória),
  `assunto` (obrigatória, única por disciplina), `peso` (ALTO/MEDIO/BAIXO, default MEDIO),
  `ordem` (int, default = ordem de aparição), `dificuldadePercebida` (1-5, default 3).
- **O SGE deliberadamente não tem noção de "onde estudar"** — `Assunto` lá é só
  nome/peso/ordem/dificuldade, sem referência a material/página. E **não tem tela de
  calendário** — "o sistema diz o que fazer hoje; planejar a semana é decisão que ele não
  toma" (`02_JORNADAS.md`).

## Minha avaliação (compartilhada com o usuário)

Os dois sistemas encaixam de forma limpa e complementar, sem sobreposição de
responsabilidade:

| | Dono |
|---|---|
| Ler o edital, achar/triar material, decidir cobertura/gap | **PlanoEstudosSefazSC** |
| Sessão de estudo, revisão espaçada (escada), métricas, "o que fazer hoje" | **SGE-Concursos** |

**Ponto de integração natural:** exportar `mapa-assuntos-edital-sefaz-sc.md` (já triado) num
CSV no formato exato do J-1 — isso não exigiria **nenhuma mudança no SGE**, só um script novo
do lado do PlanoEstudosSefazSC.

**O que eu deliberadamente não fiz:** escrever ou sugerir código no repositório do SGE. A
regra deles é clara (doc antes de código), e a decisão de como formalizar essa integração
(por exemplo, uma nota em `01_DOMINIO.md` sobre populações externas do Assunto, ou um ADR
novo) é uma decisão de vocês dois nesse projeto, não algo pra eu introduzir de fora.

## Em aberto, pra decidir aqui no SGE

1. Vale registrar em algum documento conceitual (`01_DOMINIO.md`? um ADR novo?) que
   `Assunto` pode ser populado por uma fonte externa de triagem, além do cadastro manual/CSV
   direto do usuário?
2. O campo `peso` (ALTO/MEDIO/BAIXO) do SGE representa importância na prova — o
   PlanoEstudosSefazSC não calcula isso hoje (os PDFs às vezes trazem "incidência em prova"
   como texto livre, não estruturado). Mapear isso automaticamente é factível ou fica
   manual por enquanto?
3. `dificuldadePercebida` (1-5) tem uma correspondência conceitual com os marcadores
   🟢🟡🔴 do plano de estudos original (nível de domínio do candidato) — vale essa ponte, ou
   são conceitos distintos o suficiente pra não misturar?
4. Cadência: a exportação CSV seria gerada uma vez por bloco triado (import incremental,
   reaproveitando a coluna `id` pra não duplicar), ou reimportação completa a cada mudança?
