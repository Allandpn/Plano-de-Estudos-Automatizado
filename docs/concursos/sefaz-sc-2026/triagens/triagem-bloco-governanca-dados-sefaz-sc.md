# Triagem do Bloco: Governança e Qualidade de Dados (Trilha 1)
### SEFAZ SC 2026 — resultado da triagem de PDFs, complementa mapa-assuntos-edital-sefaz-sc.md e cronograma-detalhado-sessoes-sefaz-sc.md
*Gerado em 04/09/2026, já com o índice completo (2639 PDFs).*

Todos os caminhos abaixo são relativos a `apostilas/`.

## Acervo identificado

**`10-Área Fiscal\22-Curso Completo de Tecnologia da Informação`** (mesma fonte principal
usada nas triagens de Bancos de Dados/SQL e Data Warehouse) cobre o bloco inteiro, com boa
profundidade — na verdade é uma aula inteira baseada no framework DAMA-DMBOK (a "roda"/DAMA
Wheel de áreas de conhecimento de gestão de dados):

- `curso-247678-aula-01-prof-diego-carvalho-e-renato-da-costa-.pdf` (111 pág., dedicada a
  Governança de Dados) — cobre **Governança de Dados** (Conceitos, Estrutura/Papéis, Data
  Stewardship, Modelos), **Dados Mestres e de Referência**, **Metadados** (Tipos,
  Repositório, Linhagem, Glossário de Negócios, Padrões) e **Qualidade de Dados**
  (Dimensões, Perfilagem/Data Profiling, Enriquecimento, Ciclo de Melhoria, Causa Raiz,
  Regras de Negócio de DQ) — os 4 assuntos finos do bloco praticamente inteiros num único
  arquivo.
- `curso-247678-aula-00-prof-diego-carvalho-e-renato-da-costa-3347-completo.pdf` (154 pág.,
  aula de conceitos básicos gerais) — seção dedicada **Ciclo de Vida de Dados** (Coleta,
  Tratamento, Armazenamento, Integração, Recuperação, Descarte), que complementa o assunto
  "ciclo de vida" não coberto na aula-01 (lá só existe "Ciclo de Vida de Registros", sobre
  gestão documental, um conceito vizinho mas diferente).

Reforço opcional (não necessário como leitura principal, mas cruza os mesmos termos):
`10-Área Fiscal\22`, `curso-247678-aula-53-prof-diego-carvalho-e-emannuelle-gouve.pdf`
(dimensões de qualidade + Data Profiling outra vez, com foco em ISO 8000 — útil só se sobrar
tempo ou se o pretest mostrar fraqueza específica em Qualidade de Dados).

## Decisão da Etapa 0 — descartes

A `aula-01` é a aula inteira do DAMA Wheel — cobre muito mais do que os 4 assuntos finos
deste bloco. Fora de escopo aqui (pertencem a outros blocos do mapa-assuntos, tratar lá):

- **Arquitetura de Dados, Modelagem e Design, Armazenamento e Operações** (pág. 23-30): se
  sobrepõe com o bloco Bancos de Dados e SQL, já triado.
- **Segurança de Dados** (pág. 32-33): pertence ao bloco Segurança da Informação e Proteção
  de Dados (Trilha 3), ainda não triado — não repetir aqui.
- **Integração e Interoperabilidade** (pág. 35-36): pertence ao bloco Integração e Sistemas
  da Administração Pública (Trilha 2) — mesmo raciocínio.
- **Gestão de Conteúdo e Documento** (pág. 38-40, inclui "Ciclo de Vida de Registros"): não
  consta como assunto fino no mapa-assuntos deste bloco nem de nenhum outro — é sobre gestão
  documental/ECM, fora do escopo do edital. Fica de fora.
- **Business Intelligence e Data Warehouse** (pág. 48-50, dentro da própria aula-01,
  "INCIDÊNCIA EM PROVA: BAIXÍSSIMA"): já coberto com muito mais profundidade na triagem do
  bloco Data Warehouse e Engenharia de Dados — não repetir.

## Gap confirmado

Nenhum. Os 4 assuntos finos do bloco foram identificados com boa profundidade:

| Assunto (mapa-assuntos) | Status |
|---|---|
| Governança: papéis, catálogo, glossário, metadados, dicionário, linhagem | ✅ |
| Ciclo de vida, dados mestres/referência | ✅ |
| Qualidade de dados (completude, consistência, validade, precisão, unicidade, integridade, atualidade) | ✅ |
| Data profiling, limpeza, tratamento de inconsistências/duplicidades/outliers | ✅ |

Nota sobre "catálogo" e "dicionário": não existe um heading dedicado "Catálogo de Dados" ou
"Dicionário de Dados" na aula-01 — o DMBOK trata isso dentro de "Repositório de Metadados"
(pág. 52) e "Glossário de Negócios" (pág. 53), e a aula-00 reforça os dois termos
explicitamente dentro da etapa de Tratamento do ciclo de vida (pág. 124: "glossários de
dados, catálogos corporativos e dicionários de metadados") e da etapa de Integração (pág.
126: "dicionários corporativos e glossários de negócio"). Cobertura real, só não está sob um
título isolado — não é um gap, é a forma como o DMBOK organiza esses três conceitos como uma
coisa só (gestão de metadados).

## Etapa 1 — cronograma

**Correção pós-triagem: 1 dia → 2 dias.** A leitura inicial desta triagem tratou o "Resumo"
da aula-01 (pág. 59-71) como recapitulação em texto dos 4 assuntos, igual funcionou nos
blocos SQL/DW. Não é bem assim: conferindo página a página, pág. 63-65 é uma tabela-resumo
da DAMA Wheel inteira (incluindo áreas fora deste bloco), pág. 65-69 são **mapas mentais em
imagem** por área — inclusive o de Metadados (pág. 69), sem nenhum texto extraível — e
pág. 68/70-71 (Dados Mestres/Qualidade) só **repetem** a tabela da Teoria, sem conteúdo novo.
Ou seja, o Resumo não é uma leitura condensada confiável pra Metadados (nem adiciona nada além
da Teoria pra Dados Mestres/Qualidade). A leitura real precisa se apoiar na Teoria:

| Fonte | Páginas | Volume |
|---|---|---|
| aula-01 — Governança (Conceitos/Papéis/Stewardship/Modelos) | 6-23 | 18 pág. |
| aula-01 — Dados Mestres e de Referência | 44-47 | 4 pág. |
| aula-01 — Metadados | 51-53 | 3 pág. |
| aula-01 — Qualidade de Dados + Data Profiling | 54-57 | 4 pág. |
| aula-00 — Ciclo de Vida de Dados | 123-128 | 6 pág. |
| **Total** | | **35 pág.** de Teoria densa (definição/classificação) |

35 páginas de Teoria (não de Resumo condensado) não cabem com pretest+fixação+Anki num único
dia de semana (~2:15h) — o dia 1 do bloco DW sozinho já usava ~40 páginas, mas de Resumo, que
rende mais rápido por página que Teoria. **Correção: o bloco passa de 1 para 2 dias.**

Absorção no cronograma (sem empurrar a Fase 3, mesmo princípio já usado quando o bloco SQL
cresceu de 2 para 3 dias): a Governança ganha Ter 22/09, e a sessão de Matemática Financeira
que estava em Qua 23/09 é removida dessa semana — o conteúdo dela (juros simples/compostos,
taxa real/efetiva, capitais equivalentes) passa pra dentro da sessão de Qua 30/09
(que já tinha descontos/amortizações), sem reduzir o tempo de Específicos. Ver diff proposto em
`cronograma-detalhado-sessoes-sefaz-sc.md`.

## Etapa 2 — roteiro por dia

### Seg 21/09 — Governança de Dados (dia 1 de 2): Conceitos, Papéis, Modelos, Metadados
- **Leitura:** `10-Área Fiscal\22`, `curso-247678-aula-01-...pdf`:
  - Mapa Mental pág. 58 (visão geral rápida, 3-5min)
  - Teoria — Conceitos Básicos de Governança: pág. 6-11
  - Teoria — Papéis Clássicos e Data Stewardship: pág. 14-16 (Data Owner, Technical Data
    Steward, Data Producers, Data Consumers, Organização de Governança/DGC/DGO)
  - Teoria — Modelos de Governança / Dama Wheel (visão geral das áreas): pág. 17-23
  - Teoria — Metadados (Tipos, Repositório, Linhagem de Dados, Glossário de Negócios,
    Padrões ISO/IEC 11179): pág. 51-53 (leitura principal — o Resumo pág. 69 é só imagem,
    não serve de atalho aqui)
- **Pretest:** 2-3 questões antes da leitura, mesmo chutando — aula-01 Questões Comentadas
  pág. 72+ (as primeiras cobrem Governança/Papéis, na ordem da Teoria).
- **Fixação:** 3-5 questões ao final — incidência ALTÍSSIMA em Governança, reforçar bem.
- **Banco de reserva:** aula-01 Lista de Questões pág. 98-109 (Gabarito pág. 110) — volta
  Sáb 26/09.
- **Observações:** nenhum gap conhecido.

### Ter 22/09 — Governança de Dados (dia 2 de 2, fechamento): Dados Mestres, Ciclo de Vida, Qualidade
- **Leitura:**
  - `10-Área Fiscal\22`, `curso-247678-aula-01-...pdf`, Teoria — Dados Mestres e de
    Referência (Dados Mestres, Dados de Referência, Dados Transacionais, Resolução de
    Entidades, Sistema de Registro x Sistema de Referência, Gestão de Hierarquias,
    Stewardship em MDM): pág. 44-47
  - `10-Área Fiscal\22`, `curso-247678-aula-00-...pdf`, Teoria — Ciclo de Vida de Dados
    (Coleta, Tratamento — inclui limpeza/duplicidades/outliers, Armazenamento, Integração,
    Recuperação, Descarte): pág. 123-128 → Resumo em tabela pág. 131 (baixa incidência, não
    aprofundar demais)
  - `10-Área Fiscal\22`, `curso-247678-aula-01-...pdf`, Teoria — Qualidade de Dados —
    Dimensões (acurácia, completude, consistência, atualidade, integridade, razoabilidade,
    tempo adequado, unicidade, validade, acessibilidade, privacidade): pág. 54-55
  - Teoria — Perfilagem/Data Profiling, Enriquecimento, Ciclo de Melhoria (Shewhart/Deming),
    Causa Raiz, Regras de Negócio de DQ: pág. 56-57
- **Pretest:** 2-3 questões de cada fonte, mesmo chutando — aula-01 Questões Comentadas
  (parte final, Dados Mestres/Qualidade, dentro de pág. 72-97); aula-00 Questões Comentadas
  pág. 134+ (atenção: nessa aula as questões de Ciclo de Vida vêm misturadas com ETL, já
  visto no bloco DW — pular as que forem puramente sobre ETL).
- **Fixação:** 5-8 questões ao final (3 assuntos com bastante decoreba: MDM, 10 dimensões de
  qualidade, 6 etapas do ciclo de vida — reforçar mais que o normal, incidência ALTA em
  Qualidade).
- **Banco de reserva:** aula-01 Lista de Questões pág. 98-109 (Gabarito pág. 110) — volta
  Sáb 26/09.
- **Observações:** nenhum gap conhecido. Se o pretest mostrar fraqueza específica em
  Qualidade de Dados/Data Profiling, reforço opcional: `curso-247678-aula-53-...pdf` (mesma
  pasta, ângulo ISO 8000).

## Impacto no cronograma master

**+1 dia** (Ter 22/09) pro bloco, absorvido removendo a sessão de Matemática Financeira de
Qua 23/09 dessa semana (conteúdo dela passa pra dentro de Qua 30/09) — Python, Estatística e
os dias de fim de semana da Semana 4 não mudam de data. Fase 3 continua começando 13/10, sem
alteração. Ver diff proposto em `cronograma-detalhado-sessoes-sefaz-sc.md`.
