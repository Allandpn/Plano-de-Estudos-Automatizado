# Triagem do Bloco: Engenharia e Arquitetura de Software + Integração e Sistemas da Administração Pública (Trilha 2)
### SEFAZ SC 2026 — resultado da triagem de PDFs, complementa mapa-assuntos-edital-sefaz-sc.md e cronograma-detalhado-sessoes-sefaz-sc.md
*Gerado em 12/09/2026, com o índice completo (2639 PDFs). Fecha a Trilha 2 inteira.*

Todos os caminhos abaixo são relativos a `apostilas/`.

## Acervo identificado

1. **`00-Curso Regular\06-Engenharia de Software`** (19 aulas, prof. Diego Carvalho e equipe)
   — **fonte principal** de quase todo o sub-bloco Engenharia e Arquitetura de Software.
   Formato uniforme e muito eficiente: cada aula tem Teoria → **Resumo condensado real**
   (texto denso, não imagem) → Questões Comentadas por banca → Lista de Questões. Cobre:
   Metodologias de Desenvolvimento (Aulas 00-01), Engenharia de Requisitos (Aula 07), APOO
   (Aula 09), Qualidade de Software (Aula 11), Testes de Software (Aula 12), Arquitetura de
   Software (Aula 13, inclui camadas/MVC/distribuída), SOA (Aula 14), WS e REST (Aula 15), APF
   (Aula 17).
2. **`00-Curso Regular\05-Desenvolvimento de Software para Concursos`** (mesma família já usada
   nos blocos Programação/Anomalias) — C# (Aula 03, pág. 3-35), .NET Framework (mesma aula,
   pág. 103-160), CSS (Aula 13, 107 pág. de Teoria — usar só a primeira metade, ver decisão
   abaixo), JavaScript/TypeScript (Aula 14, bem mais enxuta).
3. **`05-TCE-SC 2026 - Pos Edital\02-Desenvolvimento de software`, Aula 05** — DevOps dedicado
   (Git, CI/CD, DevSecOps).
4. **`05-TCE-SC 2026 - Pos Edital\01-Banco de Dados`, Aula 14** — seção "Integração e
   Interoperabilidade dos Dados" do DAMA-DMBOK (pág. 38-40) — mesma aula do DAMA Wheel já usada
   na triagem de Governança de Dados, mas essa seção específica tinha ficado de fora de
   propósito (era deste bloco, não daquele).

## Decisão da Etapa 0 — descartes

- **Curso Engenharia de Software, Aulas 02 (RUP), 08 (Análise Estruturada), 10 (UML), 16
  (Padrões de Projeto), 18 (Usabilidade)**: não são assuntos finos deste edital — fora de
  escopo, mantidas como contexto opcional.
- **Curso Desenvolvimento de Software, Aula 03**: NHibernate/VBScript/Visual Basic/ASP clássico
  (pág. 252-283) são tecnologias antigas não citadas no edital — não ler. Só C# e .NET
  Framework.
- **Curso Desenvolvimento de Software, Aula 13 (CSS)**: 107 pág. de Teoria é volume alto pra um
  único sub-item de uma linha do edital que combina 6 tecnologias — **usar só a primeira
  metade (pág. 3-50)**, cobrindo fundamentos/seletores/box model; Bootstrap (pág. 156+) fica de
  fora, não é citado no edital.
- **Curso Desenvolvimento de Software, Aula 21**: Android/Kotlin/Swift/React Native —
  desenvolvimento mobile, não citado no edital — descartada (a menção de TypeScript ali é só
  no contexto de React Native, já coberta pela Aula 14 de forma mais direta).

## Gap confirmado

Nenhum ❌. Um 🟡 real (Pontos de Caso de Uso) e um 🟡 no sub-bloco de Integração (ângulo
específico da administração pública brasileira):

| Assunto (mapa-assuntos) | Status | Observação |
|---|---|---|
| Ciclo de vida e processos de desenvolvimento; engenharia de requisitos (funcionais/não funcionais) | ✅ | Completo |
| Arquitetura de software, sistemas distribuídos, microsserviços, integração de aplicações | ✅ | Completo (Arquitetura Distribuída dentro da própria Aula 13) |
| Qualidade e testes de software | ✅ | Completo |
| Métricas de software: APF, Pontos de Caso de Uso, produtividade/esforço/prazo/custo/qualidade, estimativas, uso em contratação/fiscalização | 🟡 | APF ✅ completo (aula dedicada); **Pontos de Caso de Uso só aparece como distrator de questão** (comparando com Story Points), sem teoria dedicada — complementar com IA no dia |
| Git 2.x; CI/CD, DevOps, DevSecOps | ✅ | Completo |
| APIs REST, HTTP/HTTPS, JSON, XML, autenticação, autorização, mensageria, interoperabilidade | ✅ | REST/WS + SOA (mensageria) |
| C#, .NET, ASP.NET, HTML5, CSS3, JavaScript, TypeScript | ✅ | Completo, mas volume muito alto pra um único dia — ver Etapa 1 |
| POO, arquitetura em camadas, cliente-servidor; leitura/análise de código-fonte | ✅ | Completo |
| Integração com sistemas estruturantes (planejamento, orçamento, finanças, contabilidade, compras, licitações, contratos, patrimônio); APIs, barramentos, mensageria | 🟡 | Conceitos gerais de integração/interoperabilidade ✅ (DAMA); **a lista específica de sistemas estruturantes da administração pública brasileira (tipo SIAFI/ComprasNet) não tem fonte dedicada no acervo** — complementar com IA |
| Análise de integrações: interfaces, fluxos de dados, regras de negócio, controles, segurança, rastreabilidade | 🟡 | Mesma fonte/mesmo gap do item anterior |

## Etapa 1 — cronograma

**Correção: "C#/.NET/HTML/CSS/JS/TS + POO/camadas" precisa de 2 dias, não 1.** Essa única
linha do edital combina 6 tecnologias — só C#+.NET já somam 91 pág., mais HTML/CSS/JS/TS
(~66 pág. mesmo cortando Bootstrap) e POO (6 pág. de Resumo) — total ~163 pág., inviável num
dia só.

**Absorção: consumindo o buffer de Sáb 24/10** ("Questões mistas: Governança de TI +
Engenharia de Software", mesmo recurso já usado nos blocos Estatística/CD/ML e IA/PLN/GenAI):

| Dia | Antes | Depois |
|---|---|---|
| Sex 23/10 | C#/.NET/HTML/JS/TS + POO/camadas (fechamento) | **C#, .NET, ASP.NET (dia 1 de 2)** |
| Sáb 24/10 | Questões mistas: Governança de TI + Eng. Software | **HTML5/CSS3/JS/TypeScript + POO/camadas/cliente-servidor/leitura de código (dia 2 de 2, fechamento)** |

Os demais dias já orçados (Seg 19/10, Ter 20/10, Qui 22/10) se confirmaram **generosos**
graças aos Resumos condensados — Seg 19/10 em particular fica bem leve (~22 pág.), compatível
com o próprio rótulo 🟢 "revisão rápida, já forte" do cronograma.

## Etapa 2 — roteiro por dia

### Seg 19/10 — 🟢 Engenharia de Software: ciclo de vida/processos, requisitos, arquitetura, sistemas distribuídos, microsserviços (revisão rápida)
- **Leitura:** `00-Curso Regular\06-Engenharia de Software`:
  - `aula 00.pdf`, Resumo: pág. 39-46 (Metodologias de Desenvolvimento — Parte 1).
  - `aula 01.pdf`, Resumo: pág. 27-30 (Metodologias de Desenvolvimento — Parte 2).
  - `aula 07.pdf`, Resumo: pág. 50-55 (Engenharia de Requisitos).
  - `aula 13.pdf`, Teoria (Arquitetura em Camadas, MVC, Arquitetura Distribuída): pág. 10-26 +
    Resumo: pág. 27-30.
- **Pretest:** 2-3 questões de cada fonte, mesmo chutando (posições variam por aula, ver
  Questões Comentadas logo após cada Resumo).
- **Fixação:** 3-5 questões ao final — dia leve, já é revisão.
- **Banco de reserva:** Lista de Questões de cada aula — volta antes do simulado #1.
- **Observações:** nenhum gap conhecido. Dia intencionalmente leve (🟢), aproveitar o tempo
  sobrando pra Anki de blocos anteriores se quiser adiantar.

### Ter 20/10 — Engenharia de Software: qualidade e testes de software; Métricas de Software (APF, PCU, produtividade/estimativas)
- **Leitura:**
  - `00-Curso Regular\06`, `aula 11.pdf`, Resumo: pág. 36-42 (Qualidade de Software).
  - Mesma família, `aula 12.pdf`, Resumo: pág. 74-78 (Testes de Software).
  - Mesma família, `aula 17.pdf`, Teoria completa: pág. 3-53 (APF — Contexto Histórico, Ponto
    de Função, Componentes Fundamentais, Etapas de Contagem, NESMA) — Teoria completa aqui, não
    só Resumo, porque Métricas é um dos pontos mais difíceis/exigidos em contratação/fiscalização.
- **Complemento via IA (gap 🟡):** Pontos de Caso de Uso (Use Case Points) como técnica
  alternativa de estimativa — sem fonte dedicada no acervo.
- **Pretest:** 2-3 questões de cada — Qualidade pág. 43+, Testes pág. 79+, APF pág. 61+.
- **Fixação:** 5-8 questões ao final, priorizando APF (mais provável de cair com detalhe).
- **Banco de reserva:** Lista de Questões de cada aula — volta antes do simulado #1.
- **Observações:** gap 🟡 de Pontos de Caso de Uso registrado acima.

### Qui 22/10 — Engenharia de Software: Git 2.x, CI/CD, DevOps, DevSecOps; APIs REST, HTTP/HTTPS, JSON, XML, mensageria
- **Leitura:**
  - `05-TCE-SC 2026 - Pos Edital\02-Desenvolvimento de software`, `aula 05.pdf`, Teoria:
    pág. 3-24 (DevOps — Git, CI/CD, DevSecOps).
  - `00-Curso Regular\06-Engenharia de Software`, `aula 15.pdf`, Resumo: pág. 37-43 (WS e
    REST — arquitetura, métodos HTTP, formatos).
  - Mesma família, `aula 14.pdf`, Teoria: pág. 5-38 (SOA — inclui Mensageria/CORBA pág. 34,
    Composição de Serviço, Governança de Serviços).
- **Pretest:** 2-3 questões de cada — DevOps pág. 25+, WS/REST pág. 44+, SOA pág. 39+.
- **Fixação:** 5-8 questões ao final.
- **Banco de reserva:** Lista de Questões de cada fonte — volta antes do simulado #1.
- **Observações:** se o pretest mostrar fraqueza específica em JSON/XML como formato de dado
  (não só como conceito de API), complementar com IA — o foco das fontes aqui é mais
  arquitetura de API do que sintaxe dos formatos em si.

### Sex 23/10 — Engenharia de Software (dia 1 de 2): C#, .NET, ASP.NET
- **Leitura:** `00-Curso Regular\05-Desenvolvimento de Software para Concursos`,
  `aula 03.pdf`:
  - Desenvolvimento Back-End - C#, Teoria: pág. 3-35.
  - Plataforma .Net - .Net Framework, Teoria: pág. 103-160.
- **Pretest:** 2-3 questões — C# Questões Comentadas pág. 36+ (FGV) ou pág. 53+ (Multibancas);
  .NET Questões Comentadas pág. 161+.
- **Fixação:** 5-8 questões ao final — dia denso (91 pág.), reforçar bem.
- **Banco de reserva:** C# Lista de Questões pág. 74+/87+; .NET Lista de Questões pág. 227+ —
  volta antes do simulado #1.
- **Observações:** ASP clássico (pág. 265+) fica de fora — tecnologia datada, não citada
  explicitamente no edital (que pede ASP.NET, coberto dentro do .NET Framework).

### Sáb 24/10 — Engenharia de Software (dia 2 de 2, fechamento): HTML5/CSS3/JavaScript/TypeScript + POO/arquitetura em camadas/cliente-servidor/leitura de código-fonte
*(Este dia substitui o antigo buffer de "questões mistas: Governança de TI + Eng. Software".)*
- **Leitura:**
  - `00-Curso Regular\05`, `aula 13.pdf`, Teoria (primeira metade — fundamentos, seletores,
    box model; não ler Bootstrap): pág. 3-50.
  - Mesma família, `aula 14.pdf`, Teoria: pág. 3-13 (JavaScript DEV), pág. 54-57 (JavaScript
    Moderno/ECMA 2021), pág. 68-70 (TypeScript).
  - `00-Curso Regular\06-Engenharia de Software`, `aula 09.pdf`, Resumo: pág. 34-39 (APOO —
    POO, herança, polimorfismo; cliente-servidor e leitura de código já vêm sendo praticados
    desde o bloco Python).
- **Pretest:** 2-3 questões de cada — CSS Questões Comentadas pág. 110+; JS/TS Questões
  Comentadas pág. 14+/58+/71+; APOO pág. 40+.
- **Fixação:** 5-8 questões ao final — fecha a Engenharia de Software (e a Trilha 2 quase
  inteira, só falta Integração no dia seguinte).
- **Banco de reserva:** Lista de Questões de cada fonte — volta antes do simulado #1.
- **Observações:** CSS Teoria completa tem mais 57 pág. não lidas aqui (pág. 51-107, cobrem
  detalhes avançados de seletores/animações) — se o pretest mostrar fraqueza grande em CSS,
  voltar nelas; senão, seguir em frente.

### Dom 25/10 — Integração e Sistemas da Administração Pública: sistemas estruturantes, APIs/barramentos/mensageria, análise de integrações
- **Leitura:** `05-TCE-SC 2026 - Pos Edital\01-Banco de Dados`, `Aula 14.pdf`, Teoria: pág. 38-40
  ("Integração e Interoperabilidade dos Dados", dentro do DAMA-DMBOK — conceitos gerais de
  integração de dados, interoperabilidade, Data as a Service).
- **Complemento via IA (gap 🟡 duplo):** (1) lista de sistemas estruturantes da administração
  pública brasileira relevantes a SEFAZ (ex: SIAFI, e-Fisco, sistemas de compras/licitações
  estaduais de SC) — sem fonte dedicada no acervo; (2) análise de integrações (interfaces,
  fluxos de dados, regras de negócio, controles, segurança, rastreabilidade) num contexto
  específico de administração pública — o acervo só tem o ângulo genérico de TI (REST/SOA já
  vistos nos dias anteriores), não o ângulo de "sistemas estruturantes governamentais"
  especificamente.
- **Pretest:** 2-3 questões — DAMA (mesma aula) Questões Comentadas pág. 70+ (usar as que
  citam integração/interoperabilidade, não as de outras áreas do DAMA Wheel).
- **Fixação:** 3-5 questões ao final, complementando com questões geradas via IA sobre sistemas
  estruturantes (dado o gap).
- **Banco de reserva:** DAMA Lista de Questões pág. 88+ (filtrar por integração) — volta antes
  do simulado #1.
- **Observações:** gap 🟡 duplo registrado acima — este é o assunto mais fraco de cobertura de
  toda a Trilha 2, por ser muito específico do contexto de administração pública brasileira
  (o acervo do Estratégia Concursos é majoritariamente genérico de TI/CS). Considerar reforço
  com a apostila de Direito Administrativo/Finanças Públicas quando estudada (pode ter menção
  a sistemas estruturantes do lado orçamentário).

## Impacto no cronograma master

**Fecha a Trilha 2 inteira.** +0 dias líquidos no cômputo total da semana (Sex 23/10 vira 2
dias, mas consome o buffer de Sáb 24/10 que já existia) — Dom 25/10 (Integração) e Semana 9
(Fase 3 continua) não mudam de data. Ver diff proposto em `cronograma-detalhado-sessoes-sefaz-sc.md`.
