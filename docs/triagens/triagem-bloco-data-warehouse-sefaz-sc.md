# Triagem do Bloco: Data Warehouse e Engenharia de Dados (Trilha 1)
### SEFAZ SC 2026 — resultado da triagem de PDFs, complementa mapa-assuntos-edital-sefaz-sc.md e cronograma-detalhado-sessoes-sefaz-sc.md
*Gerado em 04/09/2026, já com o índice completo (2639 PDFs).*

Todos os caminhos abaixo são relativos a `apostilas/`.

## Acervo identificado

**`10-Área Fiscal\22-Curso Completo de Tecnologia da Informação`** (mesma fonte principal
usada na triagem de Bancos de Dados e SQL) cobre o bloco inteiro sozinho, com boa
profundidade:

- `curso-247678-aula-07-...pdf` (BI e DW) — DW/Data Mart/Data Lake/Lakehouse, OLTP x OLAP,
  **ETL/ELT** (pág. 47-48)
- `curso-247678-aula-08-...pdf` (Modelagem Multidimensional) — fato/dimensão, esquema
  estrela/floco de neve
- `curso-247678-aula-11-...pdf` (Big Data) — pipelines batch/streaming, processamento
  distribuído, arquiteturas escaláveis
- `curso-247678-aula-12-...pdf` (152 pág.!) — **duas seções completas em um arquivo só**:
  Hadoop (pág. 3-77) e **Apache Spark** (pág. 78-115, Teoria+Resumo+Questões dedicados) +
  bônus "Big Data e Outras Soluções/Ciência de Dados/Cloud Computing" (pág. 116+)

`00-Curso Regular\02-Banco de Dados para Concursos` (aulas 15-17, a fonte que a triagem de
BD/SQL tinha redirecionado pra cá) cobre o mesmo território de forma mais enxuta — vira
**reforço opcional**, não leitura principal.

## Decisão da Etapa 0 — descartes

- **`10-Área Fiscal\22`, aulas 09-10 (Mineração de Dados, Algoritmos de Data Mining):**
  conferido contra `mapa-assuntos-edital-sefaz-sc.md` — **não constam na lista fina oficial
  deste bloco**. Ficam de fora como leitura obrigatória; relevantes como contexto pro bloco
  Estatística/Ciência de Dados/ML mais adiante, não repetir aqui.
- **`10-Área Fiscal\22`, aula 12, itens 9-11 (Big Data e Outras Soluções/Ciência de
  Dados/Cloud Computing, pág. 116+):** bônus, fora do escopo fino do edital pra este bloco.

## Gap confirmado — ATUALIZAÇÃO

O `mapa-assuntos-edital-sefaz-sc.md` tinha **Apache Spark marcado como ❌** (sem fonte). Não
é real: `10-Área Fiscal\22`, `curso-247678-aula-12-...pdf` tem uma seção inteira e dedicada
sobre Apache Spark (Teoria pág. 78-96, Resumo pág. 97-103, Questões Comentadas
pág. 104-110, Lista pág. 111-115) — inclui DataFrame, Spark SQL, RDD e o modelo de
streaming em micro-lote.

Nenhum gap remanescente identificado neste bloco.

## Etapa 1 — cronograma

**Sem mudança no orçamento de dias.** O `cronograma-detalhado-sessoes-sefaz-sc.md` já
reserva 3 dias pro bloco (Qui 17/09, Sex 18/09, Dom 20/09 — com Sáb 19/09 de questões
mistas SQL+DW no meio). A distribuição de conteúdo por dia abaixo encaixa exatamente nesses
3 dias sem precisar de diff.

## Etapa 2 — roteiro por dia

### Qui 17/09 — DW, Data Mart/Lake/Lakehouse, OLTP x OLAP, Modelagem Dimensional
- **Leitura:**
  - `10-Área Fiscal\22`, `curso-247678-aula-07-...pdf` (BI e DW): Resumo pág. 60-76
    (cobre DW/Data Mart/Lake/Lakehouse/OLTP-OLAP/ETL-ELT de forma condensada; aprofundar na
    Teoria pág. 3-59 só onde o pretest mostrar fraqueza — ETL/ELT especificamente nas
    pág. 47-48)
  - `10-Área Fiscal\22`, `curso-247678-aula-08-...pdf` (Modelagem Multidimensional): Mapa
    Mental pág. 70-75 → Resumo pág. 76-92 (aprofundar Teoria pág. 3-69 só se precisar)
- **Pretest:** 2-3 questões de cada (aula07 Questões Comentadas pág. 77+; aula08 pág. 93+).
- **Fixação:** 3-5 questões de cada, depois do resumo.
- **Banco de reserva:** Lista de Questões (aula07 pág. 111+; aula08 pág. 175+) — volta
  Sáb 19/09.
- **Observações:** nenhum gap conhecido neste dia.

### Sex 18/09 — Big Data, Pipelines Batch/Streaming, Processamento Distribuído, Hadoop
- **Leitura:**
  - `10-Área Fiscal\22`, `curso-247678-aula-11-...pdf` (Big Data): Mapa Mental pág. 40 →
    Resumo pág. 41-47 (aprofundar Teoria pág. 3-39 só se precisar — pipelines
    batch/streaming nas pág. 25, arquiteturas escaláveis pág. 66)
  - `10-Área Fiscal\22`, `curso-247678-aula-12-...pdf`, seção Hadoop: Resumo pág. 42-55
    (aprofundar Teoria pág. 3-41 só se precisar)
- **Pretest:** 2-3 questões de cada (aula11 pág. 48+; aula12-Hadoop pág. 56+).
- **Fixação:** 3-5 questões de cada.
- **Banco de reserva:** Lista de Questões (aula11 pág. 70+; aula12-Hadoop pág. 71-77) —
  volta Sáb 19/09.
- **Observações:** nenhum gap conhecido neste dia.

### Dom 20/09 — Apache Spark, DataFrame, Spark SQL (fechamento do bloco)
- **Leitura:** `10-Área Fiscal\22`, `curso-247678-aula-12-...pdf`, seção Apache Spark:
  - Resumo pág. 97-103 (leitura principal)
  - Teoria pág. 78-96 (dirigida — este é o assunto que antes era gap confirmado, então vale
    ler com mais atenção que o normal, não só o resumo)
  - Reforço opcional: `SEFAZ-CE 2026\27-Desenvolvimento de Software`,
    `curso-383837-aula-12-...pdf` pág. 152-160 (RDD/DataFrame/Spark SQL, outra explicação)
    ou `07-TSE Unificado\02-Banco de Dados`, `aula 12.pdf` pág. 28 (Spark Core/SQL/Streaming
    — visão geral rápida)
- **Pretest:** 2-3 questões (Questões Comentadas pág. 104+).
- **Fixação:** 5-8 questões (assunto que era gap — reforçar bem).
- **Banco de reserva:** Lista de Questões pág. 111-115 — volta pra revisão geral depois.
- **Observações — GAP RESOLVIDO:** Apache Spark confirmado nesta aula (ver seção "Gap
  confirmado" acima).

## Impacto no cronograma master

Nenhum — os 3 dias já reservados (Qui 17, Sex 18, Dom 20/09) recebem exatamente o conteúdo
do bloco, incluindo o Apache Spark que antes seria buscado via IA/documentação externa.
