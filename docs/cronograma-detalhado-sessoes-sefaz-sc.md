# Cronograma Detalhado — Sessão a Sessão
### SEFAZ SC 2026 — complementa o plano-estudos-sefaz-sc-2026.md e o mapa-assuntos-edital-sefaz-sc.md
*v3 — bloco Bancos de Dados e SQL triado e expandido de 2 para 3 dias (14-16/09); Semana 3 reorganizada para absorver a expansão sem empurrar a Fase 3*

Este arquivo divide o conteúdo oficial do edital em sessões diárias. Marque as caixas conforme for concluindo.

**Como usar:**
- Cada sessão termina com criação de cards no Anki do que foi visto.
- Domingo costuma levar o assunto mais abstrato/pesado da semana — método apostila + IA nesses dias.
- **É um orçamento, não uma sentença.** As sessões de "questões mistas" e os buffers absorvem atrasos.
- A estrutura dia a dia já usa a granularidade real do `mapa-assuntos-edital-sefaz-sc.md` — o que ainda pode mudar é o *tempo exato* de cada assunto, conforme a triagem real dos PDFs (páginas, questões disponíveis) for feita bloco por bloco.
- Semana 1 é curta (começa quarta) — carga menor de propósito.
- A Fase 3 (semanas 7–9) continua a mais apertada — 30 assuntos finos pra 15 sessões (~2/sessão). Um único dia (Dom 01/11) mistura dois blocos de propósito, pra fechar a fase; é a única exceção.
- **Bloco Bancos de Dados e SQL (Trilha 1) já foi triado com PDFs reais em 02/09/2026** — ver `claude/triagem-bloco-bd-sql-sefaz-sc.md` para o roteiro completo por página (leitura, pretest, fixação, banco de reserva, observações de banca/imagens). O detalhe fino não é repetido aqui, só o resumo do assunto do dia.

## Log de ajustes de triagem (provisório até rebalanceamento final)

Conforme cada bloco for triado, registre aqui se o orçamento de dias bateu com a realidade. **Não recalcule o cronograma inteiro a cada achado individual** — isso vai acontecer em várias interações ao longo dos próximos dias (limite de contexto por conversa). Só faça o rebalanceamento completo quando fizer sentido acumulado — pelo menos ao fechar a Trilha 1 inteira (antes de 14/09, se possível).

| Bloco | Orçamento original | Real (triagem) | Diferença | Status |
|---|---|---|---|---|
| Bancos de Dados e SQL | 2 dias | 3 dias | +1 dia | Absorvido nos 3 dias de Matemática Financeira (provisório — pode mudar no rebalanceamento final) |

---

## FASE 1 — Diagnóstico

### Semana 1 (02–06/09) — semana curta
- [ ] **Qua 02/09** — Inventário: cruzar apostilas (Estratégia + SEFAZ CE) com os 16+7 blocos oficiais; montar estrutura dos decks no Anki
- [ ] **Qui 03/09** — Diagnóstico com questões: Trilha 1 (SQL, DW, Governança de Dados, Python) — testar nível real
- [ ] **Sex 04/09** — Diagnóstico com questões: Trilha 1 restante (Estatística/ML, Anomalias, BI, IA) + Trilha 2/3 (Governança TI, Engenharia, Infra, Segurança) — panorama
- [ ] **Sáb 05/09** — Diagnóstico: Direito Constitucional/Administrativo + Finanças Públicas + nível atual de Português/RLM
- [ ] **Dom 06/09** — Reativar Português: ortografia, crase, concordância, regência + questões

### Semana 2 (07–13/09)
- [ ] **Seg 07/09** — RLM: estruturas lógicas, raciocínio verbal/matemático + questões
- [ ] **Ter 08/09** — Português: compreensão e interpretação de textos (o mais cobrado em FCC), relação do texto com contexto histórico, morfossintaxe, concordância, regência
- [ ] **Qua 09/09** — Português: vozes verbais, correlação verbal, coordenação/subordinação, conectivos, figuras de linguagem, discurso direto/indireto, pontuação, pronomes, sinonímia/antonímia, redação oficial e redação (confronto de frases)
- [ ] **Qui 10/09** — RLM: raciocínio sequencial, orientação espacial/temporal, formação de conceitos
- [ ] **Sex 11/09** — Fechar inventário; ajustar tags 🟢🟡🔴 com base no que o diagnóstico revelou
- [ ] **Sáb 12/09** — Questões mistas: Português + RLM
- [ ] **Dom 13/09** — Cards Anki de tudo visto até aqui; revisar resultado geral do diagnóstico

---

## FASE 2 — Trilha 1 (Dados & Analytics) — 37 assuntos finos em 20 sessões

### Semana 3 (14–20/09) — SQL (3 dias, triado) + Data Warehouse (início)
- [ ] **Seg 14/09** — SQL: fundamentos (Dados/BD/SGBDs), modelagem conceitual/lógica, MER, modelo relacional, normalização, tratamento de valores nulos *(roteiro detalhado: triagem-bloco-bd-sql-sefaz-sc.md)*
- [ ] **Ter 15/09** — SQL: DDL/DML/DCL/TCL; cláusulas (WHERE, subconsultas, IN/EXISTS/ALL/ANY, CASE, COLLATE), junções *(gap: CTE e window functions ausentes do acervo — resolver via IA/doc oficial neste dia)*
- [ ] **Qua 16/09** — SQL: transações/concorrência/backup-recovery/otimização e planos de execução; PostgreSQL, MySQL, SQL Server; relacional x NoSQL/MongoDB *(fecha o bloco SQL — 3º dia, adicionado após triagem real dos PDFs)*
- [ ] **Qui 17/09** — Data Warehouse: DW/Data Mart/Lake/Lakehouse, OLTP/OLAP, modelagem dimensional
- [ ] **Sex 18/09** — Data Warehouse: ETL/ELT, pipelines batch/streaming, Big Data, processamento distribuído
- [ ] **Sáb 19/09** — Questões mistas: SQL + DW *(inclui banco de reserva de questões do bloco SQL — ver triagem)*
- [ ] **Dom 20/09** — Data Warehouse: Apache Spark 4.x, DataFrame, Spark SQL (fechamento)

### Semana 4 (21–27/09) — Governança de Dados + Python + Estatística (início)
- [ ] **Seg 21/09** — Governança e Qualidade de Dados (bloco completo): catálogo/metadados/linhagem, ciclo de vida/dados mestres, qualidade de dados, data profiling
- [ ] **Ter 22/09** — Python: lógica de programação, sintaxe, NumPy, pandas
- [ ] **Qua 23/09** — Gerais: Matemática Financeira (juros simples/compostos, taxa real/efetiva, capitais equivalentes)
- [ ] **Qui 24/09** — Python: CSV/JSON/XML, consumo de APIs, web scraping, automação/RPA (fechamento)
- [ ] **Sex 25/09** — Estatística: descritiva (medidas de posição/dispersão)
- [ ] **Sáb 26/09** — Questões mistas: Governança de Dados + Python
- [ ] **Dom 27/09** — 🔴 Estatística: probabilidade e distribuições (Bernoulli, binomial, geométrica, uniforme, normal, Poisson, qui-quadrado, t-Student, F-Snedecor) — use apostila + IA

### Semana 5 (28/09–04/10) — Estatística e ML
- [ ] **Seg 28/09** — 🔴 Estatística: inferência — amostragem, intervalos de confiança, testes de hipótese, correlação, regressão
- [ ] **Ter 29/09** — Ciência de Dados: análise exploratória, ciclo de vida de projetos de CD, preparação/engenharia/seleção de atributos
- [ ] **Qua 30/09** — Gerais: Matemática Financeira (descontos simples/composto, amortizações SAC/francês/misto)
- [ ] **Qui 01/10** — ML: aprendizado supervisionado/não supervisionado, classificação, regressão, clustering
- [ ] **Sex 02/10** — ML: árvores de decisão, ensemble, algoritmos por distância, overfitting/underfitting, métricas, scikit-learn (fechamento Estatística/ML)
- [ ] **Sáb 03/10** — Questões mistas: Estatística + ML (fixação pesada — bloco mais denso da trilha)
- [ ] **Dom 04/10** — Detecção de Anomalias: técnicas estatísticas/ML, análise de transações, falsos positivos/negativos, indicadores de risco

### Semana 6 (05–11/10) — BI + IA/GenAI (fechamento da Trilha 1)
- [ ] **Seg 05/10** — 🔴 BI: arquitetura, indicadores, análise descritiva/diagnóstica/preditiva/prescritiva, self-service BI
- [ ] **Ter 06/10** — BI: Power BI — Power Query, linguagem M, modelagem de dados
- [ ] **Qua 07/10** — Gerais: Combinatória e Probabilidade (RLM) — complementa Estatística + Matemática Financeira: fluxo de caixa, valor atual, TIR (fechamento)
- [ ] **Qui 08/10** — BI: Power BI — DAX, medidas, relacionamentos, filtros, dashboards (fechamento)
- [ ] **Sex 09/10** — IA/GenAI: conceitos de IA/Deep Learning, redes neurais, PLN
- [ ] **Sáb 10/10** — Questões mistas: BI + revisão geral de toda a Trilha 1
- [ ] **Dom 11/10** — IA/GenAI: LLMs, transformers, embeddings, RAG, PyTorch/TensorFlow, uso responsável — **fecha a Trilha 1** + Gerais: Governo Digital e LGPD como lei (complemento)

---

## FASE 3 — Direito, Finanças Públicas, Trilhas 2 e 3 — 30 assuntos finos em 15 sessões *(a mais apertada)*

### Semana 7 (12–18/10) — Finanças Públicas + Governança de TI + início Direito
- [ ] **Seg 12/10** — 🔴 Finanças Públicas: Lei 4.320/1964, LRF, PPA/LDO/LOA e princípios orçamentários
- [ ] **Ter 13/10** — 🔴 Finanças Públicas: receita/despesa orçamentária, classificações, estágios; créditos adicionais, restos a pagar, despesas de exercícios anteriores, fontes/destinações de recursos (fechamento)
- [ ] **Qua 14/10** — Direito Constitucional: princípios fundamentais, direitos e garantias fundamentais; organização político-administrativa do Estado, administração pública/servidores públicos
- [ ] **Qui 15/10** — 🔴 Governança de TI: governança e gestão de TI, alinhamento estratégico, COBIT 2019, ITIL v5
- [ ] **Sex 16/10** — 🔴 Governança de TI: contratos de TI, gestão de fornecedores, SLA, critérios de aceite; gestão de riscos contratuais e conformidade
- [ ] **Sáb 17/10** — Questões mistas: Finanças Públicas (fixação — é novo e denso)
- [ ] **Dom 18/10** — 🔴 Governança de TI: PMBOK Guide 8ª edição, Scrum Guide 2020, Kanban, abordagens preditivas/adaptativas/híbridas (fechamento)

### Semana 8 (19–25/10) — Engenharia de Software + Integração + Direito
- [ ] **Seg 19/10** — 🟢 Engenharia de Software: ciclo de vida/processos de desenvolvimento, engenharia de requisitos; arquitetura de software, sistemas distribuídos, microsserviços (revisão rápida, já forte)
- [ ] **Ter 20/10** — Engenharia de Software: qualidade e testes de software; 🔴 Métricas de Software (APF, Pontos de Caso de Uso, produtividade, estimativas, uso em contratação/fiscalização)
- [ ] **Qua 21/10** — Direito Constitucional: Poder Executivo/Legislativo, finanças públicas na CF; ordem econômica/social, Constituição do Estado de SC (fechamento)
- [ ] **Qui 22/10** — Engenharia de Software: Git 2.x, CI/CD, DevOps, DevSecOps; APIs REST, HTTP/HTTPS, JSON, XML, autenticação/autorização
- [ ] **Sex 23/10** — 🔴 Engenharia de Software: C#, .NET, ASP.NET, HTML5/CSS3/JavaScript/TypeScript; POO, arquitetura em camadas, leitura de código-fonte (fechamento)
- [ ] **Sáb 24/10** — Questões mistas: Governança de TI + Engenharia de Software
- [ ] **Dom 25/10** — Integração e Sistemas da Administração Pública: integração com sistemas estruturantes/APIs/barramentos; análise de integrações (interfaces, fluxos, regras de negócio)

### Semana 9 (26/10–01/11) — Infraestrutura + Segurança + Direito Administrativo
- [ ] **Seg 26/10** — 🔴 Infraestrutura: servidores, virtualização, contêineres, alta disponibilidade; redes — OSI/TCP-IP, IPv4/IPv6, DNS/DHCP, VPN/NAT/VLAN, roteamento
- [ ] **Ter 27/10** — 🔴 Infraestrutura: cloud — IaaS/PaaS/SaaS, AWS/Azure/GCP; Docker e Kubernetes (fechamento)
- [ ] **Qua 28/10** — Direito Administrativo: poderes da Administração, responsabilidade civil, controle; LC 741/2019, Lei 6.745/1985
- [ ] **Qui 29/10** — Segurança da Informação: CIA, ameaças/vulnerabilidades; IAM, MFA, RBAC, segurança de redes/sistemas/APIs
- [ ] **Sex 30/10** — Segurança da Informação: firewalls, IDS/IPS, WAF, hardening, gestão de patches; logs, monitoramento, incidentes, continuidade
- [ ] **Sáb 31/10** — 🃏 **Buffer** — se em dia: revisão geral da Fase 3; se atrasado: absorve pendências
- [ ] **Dom 01/11** — Segurança da Informação: criptografia, PKI, TLS, LGPD aplicada (fechamento) **+** Direito Administrativo: LAI, Lei 8.429/1992 (improbidade), Lei 14.133/2021 (fechamento) — único dia que mistura dois blocos de propósito, pra fechar a fase dentro do orçamento

---

## FASE 4 — Síntese e reta final

### Semana 10 (02–08/11) — Auditoria com Tecnologia + decoreba + 1º simulado
- [ ] **Seg 02/11** — Auditoria com Tecnologia: aplicação de BD/SQL/BI/Ciência de Dados/IA à auditoria/fiscalização, extração/cruzamento/análise de bases, indicadores de risco
- [ ] **Ter 03/11** — Auditoria com Tecnologia: auditoria de contratos de TI e serviços (dev/manutenção/sustentação/infra/suporte), conformidade contratual, SLA, métricas de software
- [ ] **Qua 04/11** — Ética e Integridade: ética no setor público, compliance, Lei 12.846/2013 (anticorrupção)
- [ ] **Qui 05/11** — Auditoria com Tecnologia: auditoria de sistemas/aplicações — requisitos, arquitetura, código-fonte, integrações, controles, trilhas de auditoria (fechamento)
- [ ] **Sex 06/11** — Conhecimentos Regionais de SC: história, geografia, cultura, política, economia
- [ ] **Sáb 07/11** — **SIMULADO COMPLETO #1** — formato real, 2 turnos, 9h no mesmo dia
- [ ] **Dom 08/11** — Correção do simulado + início da revisão dirigida pelos erros

### Semana 11 (09–15/11) — Revisão dirigida + 2º simulado
- [ ] **Seg 09/11** — Revisão dirigida: erros do simulado em Específicos (priorize onde mais errou)
- [ ] **Ter 10/11** — Revisão dirigida: erros do simulado em Gerais
- [ ] **Qua 11/11** — Revisão: Direito Constitucional/Administrativo (reforço — é o que mais decai sem revisão)
- [ ] **Qui 12/11** — Revisão: Finanças Públicas + Governança de TI (reforço dos 🔴 mais apertados da Fase 3)
- [ ] **Sex 13/11** — Revisão: Engenharia de Software/C#.NET + Infraestrutura (reforço)
- [ ] **Sáb 14/11** — Revisão Anki intensiva — dia dedicado só à repetição espaçada, todos os decks
- [ ] **Dom 15/11** — **SIMULADO COMPLETO #2** — última calibragem de fôlego e tempo

### Semana 12 (16–22/11) — Revisão leve, descanso e prova
- [ ] **Seg 16/11** — Revisão dirigida: erros do simulado #2
- [ ] **Ter 17/11** — Revisão leve: pontos fracos remanescentes (última chance de reforço pesado)
- [ ] **Qua 18/11** — Revisão leve: Anki + questões rápidas, sem conteúdo novo
- [ ] **Qui 19/11** — Revisão leve: Anki + Regionais SC/Ética (decoreba final)
- [ ] **Sex 20/11** — Revisão muito leve: só Anki
- [ ] **Sáb 21/11** — Descanso + logística: separar documento, conferir local exato de prova, dormir bem. No máximo uma passada leve no Anki
- [ ] **Dom 22/11** — 🎯 **PROVA — Florianópolis**

---
*Inglês Técnico não tem sessão dedicada — incorpore lendo documentação/artigos técnicos em inglês ao longo das outras trilhas.*