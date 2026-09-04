# Triagem do Bloco: Bancos de Dados e SQL (Trilha 1)
### SEFAZ SC 2026 — resultado da triagem de PDFs, complementa mapa-assuntos-edital-sefaz-sc.md e cronograma-detalhado-sessoes-sefaz-sc.md
*Refeita em 04/09/2026 com o índice completo (2639 PDFs) — substitui a versão de 02/09/2026, feita só contra uma amostra de 19 PDFs.*

Todos os caminhos abaixo são relativos a `apostilas/`.

## Acervo identificado

Duas famílias de curso foram cruzadas neste bloco:

1. **`10-Área Fiscal\22-Curso Completo de Tecnologia da Informação`** (55 aulas, prof.
   Diego Carvalho e equipe; arquivos `curso-247678-aula-NN-...pdf`) — curso avulso, não
   específico de um concurso, muito mais denso que qualquer fonte usada na triagem
   anterior. **Nova fonte principal deste bloco**: aulas 02-06 cobrem Banco de Dados,
   Modelagem Conceitual, Modelagem Relacional, Normalização e SQL completo (315 páginas só
   de SQL). Cada aula segue o padrão Teoria → Mapa Mental → Resumo → Questões Comentadas
   MULTIBANCA → Lista de Questões.
2. **`00-Curso Regular\02-Banco de Dados para Concursos`** (arquivos `aula NN.pdf`; e
   cópias-irmãs idênticas em `SEFAZ-CE 2026\26`, `05-TCE-SC 2026 - Pos Edital\01`,
   `07-TSE Unificado\02`, `06-TRT-SC\04`) — mesma fonte usada na triagem anterior. Continua
   sendo a **melhor fonte para índices, views e os SGBDs específicos** (MySQL, PostgreSQL,
   SQL Server, MongoDB), que o Curso Completo de TI não cobre com o mesmo detalhe.
3. **`10-Área Fiscal\49-Especialidade TI - Banco de Dados`** (arquivos
   `curso-220905-aula-NN-....pdf`, 10 aulas, "apostila antiga" da triagem original) —
   **quase se perdeu na refeitura**: uma busca minha por "curso220905" (sem hífen) não
   achou nada, mas o nome real do arquivo tem hífen (`curso-220905-...`). Continua sendo a
   **melhor fonte para Transações/Concorrência/Recuperação** — Aula 04 (152 pág.) é
   inteiramente dedicada a isso.
4. **Achado extra**: `05-TCE-SC 2026 - Pos Edital\01-Banco de Dados` (arquivos
   `Aula NN.pdf`) tem 23 arquivos contra 19 de `00-Curso Regular\02` — 4 aulas a mais
   (19-22). Só a **Aula 22 (T-SQL)** é relevante a este bloco (reforço de SQL Server +
   window functions); aulas 19-21 são de Estatística/ML/Auditoria e ficam pra outros
   blocos.

## Decisão da Etapa 0 — descartes

- **`10-Área Fiscal\22`:** aulas 00-01, 07-21, 23-53 pertencem a outros blocos do edital
  (Teoria da Informação, Governança de Dados, DW/BI/Big Data, IA/ML/PLN, Python/R,
  Governança de TI, Segurança, Cloud) ou são flashcards de revisão — fora do escopo fino
  deste bloco, mas já mapeadas pra quando triarmos esses blocos.
- **`00-Curso Regular\02` (e irmãs):** mesmos descartes da triagem anterior — Aula 06
  (PL/SQL Oracle-specific), Aula 10 (H2), Aula 11 (SQLite), Aula 12 (DB2), Aula 13 (BD em
  memória), Aula 14 (BD orientado a objetos), Aulas 15-17 (redirecionadas pro bloco Data
  Warehouse). Aula 05 nova (Oracle) mantida só como contexto de Views Materializadas
  (Oracle não é citado no edital, mas o conceito de view materializada é transferível).
- **`05-TCE-SC 2026 - Pos Edital\01`, Aulas 19-21:** fora deste bloco (métricas de ML, AED,
  auditoria de fraudes) — relevantes pros blocos de Estatística/CD/ML e Detecção de
  Anomalias.
- **`10-Área Fiscal\49-Especialidade TI - Banco de Dados`:** só a Aula 04 (Transações) é
  usada aqui. Aulas 00-03 e 05-09 são conteúdo genérico/acadêmico de BD (modelagem,
  Álgebra Relacional etc.) que o Curso Completo de TI já cobre melhor e mais atualizado —
  mantidas como material de contexto opcional, não como leitura obrigatória.

## Gap confirmado — ATUALIZAÇÃO IMPORTANTE

A triagem anterior (02/09) registrou **CTE e window functions como ausentes de todo o
acervo**. Isso **não é real** — era um artefato de ter testado só 19 PDFs de uma pasta.
Com o índice completo, CTE e window functions **estão bem cobertos**:

- `10-Área Fiscal\22`, `curso-247678-aula-06-...pdf` (SQL): CTE nas pág. 149-150 (Teoria) e
  213 (reforço em Resumo/Questões); window functions (`OVER`, `PARTITION BY`, `RANK()`) nas
  pág. 152-173 (dentro da Teoria) com exemplos de código.
- `05-TCE-SC 2026 - Pos Edital\01`, `Aula 22.pdf` (T-SQL, exclusiva dessa pasta): reforço
  extra de window functions com `PARTITION BY`, `ORDER BY`, `LAST_VALUE` (pág. 29-34).

**Gap real remanescente (menor):** as versões específicas "PostgreSQL 18" e "MongoDB 8.0"
citadas no edital não aparecem confirmadas explicitamente pelo número da versão no texto
lido (mesma observação da triagem anterior — o conteúdo é atual/2025-2026, mas o número
exato da versão não bate uma citação literal). Não é ausência de conteúdo, é uma checagem
rápida a fazer durante a leitura (comparar com changelog oficial se sobrar tempo).

## Etapa 1 — cronograma

**Sem mudança no orçamento de dias**: continuam sendo 3 dias (Seg 14, Ter 15, Qua 16/09),
como a triagem anterior já havia ajustado. O que muda é a fonte principal (mais densa e
melhor) e a resolução do gap de CTE/window functions — não há necessidade de diff no
`cronograma-detalhado-sessoes-sefaz-sc.md` desta vez.

## Etapa 2 — roteiro por dia

### Seg 14/09 — Fundamentos, Modelagem Conceitual/Relacional, Normalização
- **Leitura** (todas em `10-Área Fiscal\22`, arquivos `curso-247678-aula-0N-...pdf`), na
  ordem:
  - `curso-247678-aula-02-...pdf` (Banco de Dados): Mapa Mental pág. 55-58 → Resumo pág. 59-63
  - `curso-247678-aula-03-...pdf` (Modelagem Conceitual — MER): Mapa Mental pág. 41-43 → Resumo pág. 44-52
  - `curso-247678-aula-04-...pdf` (Modelagem Relacional — chaves, integridade): Mapa Mental pág. 58-60 → Resumo pág. 61-66
  - `curso-247678-aula-05-...pdf` (Normalização): Resumo pág. 24-26 → Mapa Mental pág. 27
  - Aprofundar na Teoria completa (aula 02 pág. 3-54, aula 03 pág. 3-40, aula 04 pág. 3-57,
    aula 05 pág. 3-23) só onde o pretest mostrar fraqueza — não ler tudo de cara.
- **Pretest:** 2-3 questões de cada aula (Questões Comentadas, em `10-Área Fiscal\22`:
  aula02 pág. 64+, aula03 pág. 53+, aula04 pág. 67+, aula05 pág. 28+), antes da respectiva
  teoria.
- **Fixação:** 3-5 questões de cada, depois do resumo.
- **Banco de reserva:** Lista de Questões de cada aula (`10-Área Fiscal\22`: aula02
  pág. 85+, aula03 pág. 102+, aula04 pág. 127+, aula05 pág. 76+) — volta Sáb 19/09.
- **Observações:** confirmar durante a leitura se "tratamento de valores nulos" (item do
  mapa-assuntos) aparece explicitamente na aula 04 (Modelagem Relacional) ou 02 — não
  localizado ainda por busca pontual.

### Ter 15/09 — SQL completo (DDL/DML/DCL/TCL, cláusulas, junções, CTE, window functions)
- **Leitura:** `10-Área Fiscal\22`, `curso-247678-aula-06-...pdf` (SQL — 315 pág. no
  total):
  - Mapa Mental pág. 174-183 (survey rápido) → Resumo pág. 184-202 (leitura principal,
    cobre tudo de forma condensada)
  - Aprofundar na Teoria (pág. 3-173) dirigido por subtópico, só onde precisar: DDL
    pág. 20-32, DML/DQL pág. 51-119, DCL (GRANT/REVOKE) pág. 119-121, TCL
    (COMMIT/ROLLBACK) pág. 113-116, subconsultas (EXISTS/IN/ALL/ANY/UNION) pág. 97-99,
    junções (INNER/LEFT/RIGHT/FULL OUTER) pág. 70-73 e 146, **CTE pág. 149-150**,
    **window functions (OVER/PARTITION BY/RANK) pág. 152-173**.
  - Reforço opcional (se sobrar tempo ou pretest mostrar fraqueza em window functions):
    `05-TCE-SC 2026 - Pos Edital\01`, `Aula 22.pdf` (T-SQL) pág. 29-34.
- **Pretest:** 2-3 questões antes de começar (Questões Comentadas, `10-Área Fiscal\22`
  aula06 pág. 203+).
- **Fixação:** 5-8 questões depois (é o assunto mais denso e mais cobrado do bloco).
- **Banco de reserva:** Lista de Questões, `10-Área Fiscal\22` aula06 pág. 275+ — volta
  Sáb 19/09.
- **Observações — GAP RESOLVIDO:** CTE e window functions confirmados nesta aula (ver seção
  "Gap confirmado" acima) — não é mais necessário buscar via IA/documentação externa.

### Qua 16/09 — Transações/Concorrência/Otimização, Índices, Views, os 4 SGBDs, NoSQL/MongoDB
- **Leitura:**
  - `10-Área Fiscal\49-Especialidade TI - Banco de Dados`,
    `curso-220905-aula-04-2326-completo.pdf` (Transações/Concorrência/Recuperação —
    dedicada, 152 pág.): Processamento de Transações pág. 3, Ponto de Efetivação pág. 15,
    Controle de Concorrência pág. 26, Recuperação Após Falha pág. 39
  - `00-Curso Regular\02`, `aula 04.pdf` (Otimização/planos de execução + Índices
    B-tree/Hash, pág. 3-40) — mesmo conteúdo em `SEFAZ-CE 2026\26`/
    `05-TCE-SC 2026 - Pos Edital\01`/`07-TSE Unificado\02`/`06-TRT-SC\04`
  - `00-Curso Regular\02`, `aula 05.pdf` (Views, incl. Views Materializadas — contexto
    Oracle, pág. 40-54)
  - `00-Curso Regular\02`, `aula 07.pdf` (MySQL 8.4) pág. 3-29
  - `00-Curso Regular\02`, `aula 08.pdf` (PostgreSQL) pág. 3-24 — versão "18" não confirmada explicitamente
  - `00-Curso Regular\02`, `aula 09.pdf` (SQL Server) pág. 3-28
  - `00-Curso Regular\02`, `aula 18.pdf` (NoSQL x Relacional + MongoDB) pág. 3-48 — versão "8.0" não confirmada
  - Bônus/reforço: `05-TCE-SC 2026 - Pos Edital\01`, `Aula 22.pdf` (T-SQL — dialeto SQL
    Server) pág. 29-34
- **Pretest:** 2-3 questões de transações (`10-Área Fiscal\49`,
  `curso-220905-aula-04-2326-completo.pdf`, Questões Comentadas pág. 51) + 2-3 por SGBD
  (`00-Curso Regular\02`: MySQL pág. 30, PostgreSQL pág. 25, SQL Server pág. 29, NoSQL
  pág. 43 — mesmas referências da triagem anterior, confirmadas).
- **Fixação:** 3-5 questões de transações (mesma fonte, pág. 51+) + 3-5 por SGBD,
  priorizando MySQL/PostgreSQL/SQL Server/MongoDB sobre otimização se o tempo apertar.
- **Banco de reserva:** `10-Área Fiscal\49`, `curso-220905-aula-04-2326-completo.pdf`,
  Lista de Questões pág. 115+; e listas de questões de cada aula em `00-Curso Regular\02`:
  MySQL pág. 42, PostgreSQL pág. 42, SQL Server pág. 45, NoSQL pág. 52 — volta Sáb 19/09.
- **Observações:** questão de exemplo FGV/SEF-MG/2023 (não é FCC, conceito transferível).
  Diagrama de arquitetura do PostgreSQL pode ter perdido nuance na extração — abrir o PDF
  original nessa página se precisar. Oracle não é citado no edital SEFAZ SC — Aula 05 é
  material de contexto (views materializadas) apenas.

## Impacto no cronograma master

Nenhum — o orçamento de 3 dias (Seg-Qua 14-16/09) já estava correto desde a triagem
anterior. A mudança é só de fonte (mais rica) e a resolução do gap de CTE/window functions.
