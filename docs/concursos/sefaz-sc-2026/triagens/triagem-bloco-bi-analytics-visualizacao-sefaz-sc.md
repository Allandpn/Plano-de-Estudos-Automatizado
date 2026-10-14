# Triagem do Bloco: Business Intelligence, Analytics e Visualização (Trilha 1)
### SEFAZ SC 2026 — resultado da triagem de PDFs, complementa mapa-assuntos-edital-sefaz-sc.md e cronograma-detalhado-sessoes-sefaz-sc.md
*Gerado em 12/09/2026, com o índice completo (2639 PDFs) — resolve os dois ❌ (Power BI)
registrados provisoriamente no mapa-assuntos.*

Todos os caminhos abaixo são relativos a `apostilas/`.

## Acervo identificado

Mesma família de curso já usada em quase todos os blocos da Trilha 1:

1. **`10-Área Fiscal\22-Curso Completo de Tecnologia da Informação`, Aula 07** ("BI e DW",
   128 pág., prof. Diego Carvalho e Renato da Costa) — cobre BI e DW juntos na mesma aula;
   **só a parte de BI** (conceitos básicos, self-service BI, tipos de análise, arquitetura de
   BI, indicadores/KPI) é deste bloco — a parte de DW (Modelagem Dimensional em diante) já foi
   coberta na triagem do bloco Data Warehouse, não reler aqui.
2. **`10-Área Fiscal\22-Curso Completo de Tecnologia da Informação`, Aula 14** ("PowerBI",
   142 pág., prof. Diego Carvalho e Emannuelle Gouveia) — **resolve os dois ❌** do
   mapa-assuntos: cobre Power Query, linguagem M, modelagem de dados, DAX, medidas,
   relacionamentos, filtros e dashboards, tudo dentro da mesma Teoria (pág. 3-42) — os dois
   conceitos aparecem interligados ao longo do texto, sem uma fronteira limpa entre eles
   (mesmo padrão de interleaving já visto na Aula 05 de ML). Tem Resumo condensado (pág. 43-47).

## Decisão da Etapa 0 — descartes

- **Aula 07:** pág. 31-59 (Modelagem Dimensional, Data Warehouse aprofundado) — já coberto na
  triagem do bloco Data Warehouse. Resumo (pág. 60-76) e Questões (pág. 77+) da aula inteira
  misturam BI+DW — usar só as questões que claramente são de BI.
- **Aula 14:** pág. 84-142 (Oracle BIEE, QlikView, Oracle Data Visualization) — ferramentas de
  BI concorrentes ao Power BI, **não citadas no mapa-assuntos do edital** (que só menciona
  "Power BI" explicitamente) — fora de escopo, não ler.

## Gap confirmado

Nenhum. Os dois ❌ do mapa-assuntos (que nunca tinham sido buscados de fato) tinham fonte real
o tempo todo — só não tinha sido encontrada ainda:

| Assunto (mapa-assuntos) | Status antes | Status agora |
|---|---|---|
| Arquitetura de BI, indicadores, análise descritiva/diagnóstica/preditiva/prescritiva, self-service BI | 🟡 (nota antiga incompleta) | ✅ |
| Power BI: Power Query, linguagem M, modelagem de dados | ❌ | ✅ |
| Power BI: DAX, medidas, relacionamentos, filtros, dashboards | ❌ | ✅ |

## Etapa 1 — cronograma

**Sem mudança.** O orçamento já previa 2 dias pra Power BI (Ter 06/10 e Qui 08/10, com Qua
07/10 de Gerais no meio) — como o conteúdo de Power Query/DAX está interligado na Aula 14 (sem
seção própria pra cada um), a divisão feita aqui é só por **quantidade de página** (metade
Teoria+Resumo cada), não por conceito isolado — mesmo recurso já usado na Aula 05 de ML.

## Etapa 2 — roteiro por dia

### Seg 05/10 — BI: arquitetura, indicadores, análise descritiva/diagnóstica/preditiva/prescritiva, self-service BI
- **Leitura:** `10-Área Fiscal\22`, `curso-247678-aula-07-prof-prof-diego-carvalho-e-renato-da-c.pdf`
  — Teoria (só a parte de BI, não ler Modelagem Dimensional em diante): pág. 3-30. Cobre
  histórico (STP→SSD→SIE→DW→OLAP→BI), self-service BI (pág. 6), tipos de análise
  descritiva/diagnóstica/preditiva/prescritiva (pág. 7-10), arquitetura de BI/indicadores/KPI
  (pág. 15-21).
- **Pretest:** 2-3 questões antes da leitura — Questões Comentadas pág. 77+ (usar só as que
  citam BI/análise/self-service, pular as de DW/modelagem dimensional).
- **Fixação:** 3-5 questões ao final, mesmo critério de filtro.
- **Banco de reserva:** Lista de Questões pág. 111+ (mesmo filtro BI x DW) — volta Sáb 10/10.
- **Observações:** aula mista BI+DW — ao ler questões, pular as que forem puramente sobre
  modelagem dimensional/star schema (já vistas no bloco Data Warehouse).

### Ter 06/10 — Power BI: Power Query, linguagem M, modelagem de dados
- **Leitura:** `10-Área Fiscal\22`, `curso-247678-aula-14-prof-diego-carvalho-e-emannuelle-gouve.pdf`
  — Teoria, primeira metade: pág. 3-25 (conceitos básicos do Power BI, Power Query, linguagem
  M — DAX/medidas aparecem misturados aqui também, é normal, não pular).
- **Pretest:** 2-3 questões antes da leitura — Questões Comentadas pág. 48+ (usar as que citam
  Power Query/linguagem M/importação de dados).
- **Fixação:** 3-5 questões ao final.
- **Banco de reserva:** Lista de Questões pág. 71-83 — volta Sáb 10/10.
- **Observações:** conteúdo interligado com DAX (dia seguinte) — não se preocupar em separar
  100%, o pretest/fixação de cada dia naturalmente reforça o que já foi lido.

### Qua 07/10 — Gerais: Combinatória e Probabilidade
*(bloco diferente, sem mudança aqui.)*

### Qui 08/10 — Power BI: DAX, medidas, relacionamentos, filtros, dashboards (fechamento)
- **Leitura:** `10-Área Fiscal\22`, `curso-247678-aula-14-...pdf` — Teoria, segunda metade:
  pág. 26-42 (DAX, medidas, relacionamentos, filtros, dashboards — aprofundamento) + Resumo:
  pág. 43-47 (revisão condensada de tudo, Power Query e DAX juntos).
- **Pretest:** 2-3 questões — Questões Comentadas pág. 48+ (continuação, usar as que citam
  DAX/medidas/relacionamentos/dashboards).
- **Fixação:** 5-8 questões ao final — fecha o bloco (e a Trilha 1 inteira), reforçar bem.
- **Banco de reserva:** Lista de Questões pág. 71-83 (restante) — volta Sáb 10/10.
- **Observações:** nenhum gap conhecido. Este é o último dia de conteúdo novo da Trilha 1 antes
  do fechamento com IA/GenAI (Sex 09/10 e Dom 11/10).

## Impacto no cronograma master

Nenhum — os 2 dias já orçados pra Power BI (Ter 06/10, Qui 08/10) e 1 dia pra BI geral (Seg
05/10) se confirmaram suficientes.
