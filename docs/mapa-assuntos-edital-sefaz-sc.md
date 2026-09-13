# Mapa de Assuntos — Edital SEFAZ SC 2026
### Derivado direto do texto oficial, organizado por trilha — base pra triagem dos PDFs
 
Este mapa substitui minhas suposições anteriores de "quanto tempo cada assunto leva". Cada linha é um assunto fino, na ordem em que aparece no edital. Use-o em cada chat de triagem: para cada assunto, identifique qual aula/PDF do Estratégia (ou SEFAZ CE) cobre, e marque. O cronograma-detalhado (dia a dia) é preenchido **a partir** deste mapa, bloco por bloco — não o contrário.
 
**Como preencher:** coluna "Aula/PDF" recebe o nome do arquivo quando você identificar; coluna "Status" usa ✅ (identificado e ok) / 🟡 (parcial) / ❌ (sem material, buscar fora).
 
---
 
## Trilha 1 — Dados & Analytics
 
### Bancos de Dados e SQL
*(triado em 02/09/2026, refeito em 04/09/2026 com o índice completo — ver
`docs/triagens/triagem-bloco-bd-sql-sefaz-sc.md` para o detalhe completo por página)*
 
| Assunto | Aula/PDF | Status |
|---|---|---|
| Modelagem conceitual, lógica e física; MER; modelo relacional | `10-Área Fiscal\22`, aulas 03-04 (Modelagem Conceitual/Relacional) | ✅ |
| Entidades, chaves, integridade, normalização, tratamento de valores nulos | `10-Área Fiscal\22`, aulas 04-05 (Modelagem Relacional/Normalização) | ✅ |
| Transações, concorrência, backup/recovery | `10-Área Fiscal\49`, Aula 04 (dedicada, 152 pág, pág 3-50) | ✅ |
| Índices, particionamento | `00-Curso Regular\02`, Aula 04 nova (pág 3-40, B-tree/Hash) | ✅ |
| Views | `00-Curso Regular\02`, Aula 05 nova (pág 40-54, incl. materializadas) | ✅ |
| Bancos relacionais x NoSQL | `00-Curso Regular\02`, Aula 18 nova (pág 3-48) | ✅ |
| PostgreSQL 18 | `00-Curso Regular\02`, Aula 08 nova (pág 3-24) — versão "18" não confirmada explicitamente no texto lido | 🟡 |
| MySQL 8.4 LTS | `00-Curso Regular\02`, Aula 07 nova (pág 3-29) — confirma versão 8.4 | ✅ |
| SQL Server 2025 | `00-Curso Regular\02`, Aula 09 nova (pág 3-28) + `TCE-SC\01`, Aula 22 (T-SQL, bônus) | ✅ |
| MongoDB 8.0 | `00-Curso Regular\02`, Aula 18 nova (pág 20-42) — versão "8.0" não confirmada explicitamente no texto lido | 🟡 |
| SQL: DDL, DML, DCL, TCL | `10-Área Fiscal\22`, Aula 06 (pág 20-121) | ✅ |
| SQL: consultas, filtros, joins, subconsultas (IN/EXISTS/ALL/ANY), CASE, COLLATE, operações de conjunto | `10-Área Fiscal\22`, Aula 06 (pág 70-99, 146) | ✅ |
| SQL avançado: CTE, window functions, planos de execução, otimização | `10-Área Fiscal\22`, Aula 06 (CTE pág 149-150; window functions pág 152-173) + `00-Curso Regular\02`, Aula 04 nova (otimização pág 3-33) | ✅ |
 
### Data Warehouse e Engenharia de Dados
*(triado em 04/09/2026 — ver `docs/triagens/triagem-bloco-data-warehouse-sefaz-sc.md`)*

| Assunto | Aula/PDF | Status |
|---|---|---|
| DW, Data Mart, Data Lake, Lakehouse; OLTP x OLAP | `10-Área Fiscal\22`, Aula 07 (BI e DW), Resumo pág 60-76 | ✅ |
| Modelagem dimensional (fato/dimensão, estrela/floco de neve) | `10-Área Fiscal\22`, Aula 08 (Modelagem Multidimensional), Resumo pág 76-92 | ✅ |
| ETL/ELT — coleta, ingestão, limpeza, transformação, integração, armazenamento | `10-Área Fiscal\22`, Aula 07, pág 47-48 (Teoria) | ✅ |
| Pipelines batch/streaming; processamento distribuído; Big Data; arquiteturas escaláveis | `10-Área Fiscal\22`, Aula 11 (Big Data), Resumo pág 41-47 + Aula 12 (Hadoop), Resumo pág 42-55 | ✅ |
| Apache Spark 4.x, DataFrame, Spark SQL | `10-Área Fiscal\22`, Aula 12, seção Apache Spark, Teoria pág 78-96 + Resumo pág 97-103 | ✅ |
 
### Governança e Qualidade de Dados
*(triado em 04/09/2026 — ver `docs/triagens/triagem-bloco-governanca-dados-sefaz-sc.md`)*

| Assunto | Aula/PDF | Status |
|---|---|---|
| Governança: papéis, catálogo, glossário, metadados, dicionário, linhagem | `10-Área Fiscal\22`, Aula 01 (Governança de Dados), pág. 6-23 e 51-53 | ✅ |
| Ciclo de vida, dados mestres/referência | `10-Área Fiscal\22`, Aula 00, pág. 123-128 (ciclo de vida) + Aula 01, pág. 44-47 (dados mestres/referência) | ✅ |
| Qualidade de dados (completude, consistência, validade, precisão, unicidade, integridade, atualidade) | `10-Área Fiscal\22`, Aula 01, pág. 54-55 | ✅ |
| Data profiling, limpeza, tratamento de inconsistências/duplicidades/outliers | `10-Área Fiscal\22`, Aula 01, pág. 56-57 + Aula 00, pág. 124 | ✅ |
 
### Programação e Automação para Dados
*(triado em 12/09/2026 — ver `docs/triagens/triagem-bloco-programacao-automacao-dados-sefaz-sc.md`)*

| Assunto | Aula/PDF | Status |
|---|---|---|
| Lógica de programação, algoritmos, estruturas de dados, funções, exceções | `10-Área Fiscal\22`, Aula 21, pág. 4-58 | ✅ |
| Python 3.14.x — sintaxe | `10-Área Fiscal\22`, Aula 21, pág. 14-77 + `06-TRT-SC\05`, Aula 05, pág. 68-75 (RegEx) | ✅ |
| NumPy 2.5.x, pandas 3.0.x | `10-Área Fiscal\22`, Aula 22, pág. 6-61 | ✅ |
| CSV, JSON, XML — manipulação/transformação/integração | `10-Área Fiscal\22`, Aula 22, pág. 7, 30-34 | 🟡 (JSON em Python sem fonte dedicada — complemento via IA no dia) |
| Consumo de APIs, web scraping | `10-Área Fiscal\22`, Aula 21, pág. 111-141 (API) + `06-TRT-SC\05`, Aula 05, pág. 91-96 (Scrapy) | 🟡 (biblioteca `requests` sem fonte dedicada — complemento via IA no dia) |
| Automação de rotinas, RPA | `06-TRT-SC\05`, Aula 05, pág. 91-96 (Tagui/PyAutoGUI/Selenium) + `07-TSE Unificado\02`, Aula 15, pág. 55-58/98 | ✅ |
 
### Estatística, Ciência de Dados e Machine Learning
*(triado em 12/09/2026 — ver `docs/triagens/triagem-bloco-estatistica-cd-ml-sefaz-sc.md`)*

| Assunto | Aula/PDF | Status |
|---|---|---|
| Estatística descritiva (medidas de posição/dispersão) | `10-Área Fiscal\50`, Aula 04, pág. 3-4,8-9 | ✅ |
| Probabilidade e distribuições | `10-Área Fiscal\15`, Aula 09 (discretas) + Aula 11 (contínuas) | ✅ |
| Inferência: amostragem, IC, testes de hipótese, correlação, regressão | `10-Área Fiscal\50`, Aula 04, pág. 5,7 (amostragem) + `10-Área Fiscal\15`, Aula 15, pág. 4-24 (IC/testes) | 🟡 (correlação/regressão sem fonte confirmada — complemento via IA) |
| Análise exploratória de dados | `10-Área Fiscal\50`, Aula 04, pág. 10-19 | ✅ |
| Ciclo de vida de projetos de Ciência de Dados; preparação/engenharia/seleção de atributos | `10-Área Fiscal\50`, Aula 02, pág. 3-42 | ✅ |
| Aprendizado supervisionado/não supervisionado: classificação, regressão, clustering | `10-Área Fiscal\50`, Aula 05, pág. 3-90 + Aula 06, pág. 3-39 | ✅ |
| Árvores de decisão, ensemble, algoritmos baseados em distância | `10-Área Fiscal\50`, Aula 05, pág. 91-167 | ✅ |
| Treinamento, validação, overfitting/underfitting, métricas de avaliação, scikit-learn | `10-Área Fiscal\50`, Aula 05, pág. 91-167 | ✅ |
 
### Detecção de Anomalias e Padrões Suspeitos
*(triado em 12/09/2026 — ver `docs/triagens/triagem-bloco-deteccao-anomalias-sefaz-sc.md`)*

| Assunto | Aula/PDF | Status |
|---|---|---|
| Técnicas estatísticas/regras/ML pra anomalias; aplicação a transações financeiras/orçamentárias/compras/contratos/licitações; falsos positivos/negativos, indicadores de risco | `05-TCE-SC 2026 - Pos Edital\01`, Aula 21 (Auditoria Contínua e Análise de Fraudes), pág. 7-40 + Aula 19 (Métricas de Classificação), pág. 4-31 | ✅ |
 
### Business Intelligence, Analytics e Visualização
*(triado em 12/09/2026 — ver `docs/triagens/triagem-bloco-bi-analytics-visualizacao-sefaz-sc.md`)*

| Assunto | Aula/PDF | Status |
|---|---|---|
| Arquitetura de BI, indicadores, análise descritiva/diagnóstica/preditiva/prescritiva, self-service BI | `10-Área Fiscal\22`, Aula 07 (BI e DW), pág. 3-30 (só a parte de BI) | ✅ |
| Power BI: Power Query, linguagem M, modelagem de dados | `10-Área Fiscal\22`, Aula 14 (PowerBI), pág. 3-25 | ✅ |
| Power BI: DAX, medidas, relacionamentos, filtros, dashboards | `10-Área Fiscal\22`, Aula 14 (PowerBI), pág. 26-47 | ✅ |
 
### Inteligência Artificial, PLN e IA Generativa
*(triado em 12/09/2026 — ver `docs/triagens/triagem-bloco-ia-pln-genai-sefaz-sc.md` — fecha a Trilha 1)*

| Assunto | Aula/PDF | Status |
|---|---|---|
| Conceitos de IA, Deep Learning, redes neurais | `10-Área Fiscal\22`, Aula 15 (Resumo pág. 93-100) + `10-Área Fiscal\50`, Aula 07, pág. 3-96 | ✅ |
| PLN: classificação, extração, entidades, similaridade, busca semântica, sumarização | `10-Área Fiscal\50`, Aula 08, pág. 3-101 | ✅ |
| LLMs, transformers, tokens, embeddings, prompt engineering, RAG, bancos vetoriais, agentes de IA, PyTorch/TensorFlow | `10-Área Fiscal\22`, Aula 15 (Resumo pág. 101-112) + `10-Área Fiscal\50`, Aula 07, pág. 43-53 (PyTorch/TensorFlow) + `07-TSE Unificado\02`, Aula 15, pág. 37-38 (RAG) + `00-Curso Regular\02`, Aula 15, pág. 48-50 (Vector Storages) | ✅ |
| Alucinações, vieses, segurança, privacidade, explicabilidade, uso responsável | `10-Área Fiscal\22`, Aula 15 (Resumo pág. 21-26) | ✅ |
 
---
 
## Trilha 2 — Governança, Projetos e Engenharia
 
### Governança, Gestão de TI e Projetos
*(triado em 12/09/2026 — ver `docs/triagens/triagem-bloco-governanca-gestao-ti-projetos-sefaz-sc.md`)*

| Assunto | Aula/PDF | Status |
|---|---|---|
| Governança de TI: alinhamento estratégico, serviços, processos, riscos, controles, indicadores; COBIT 2019 e ITIL v5 | `SEFAZ-CE 2026\15`, Aula 01 (COBIT 2019, Resumo pág. 48-66) + Aula 02 (ITIL 4, Resumo pág. 61-69) + Aula 06 (Estratégia de TI, pág. 3-28) | 🟡 (só ITIL 4 encontrado, edital pede v5) |
| Contratos de TI: planejamento/contratação/fiscalização, gestão de fornecedores, SLA, critérios de aceite, entregáveis | `SEFAZ-CE 2026\15`, Aula 09 (Contratos de TI e IN 94/2022), pág. 3-49 | ✅ |
| Gestão de riscos contratuais, controles, monitoramento, conformidade | `SEFAZ-CE 2026\15`, Aula 08 (ISO 31000), pág. 3-33 | ✅ |
| Gerenciamento de projetos: PMBOK Guide 8ª edição | `SEFAZ-CE 2026\15`, Aula 03 (PMBOK 7), pág. 100-104,119-146 | 🟡 (só PMBOK 7 encontrado, edital pede 8ª edição) |
| Métodos ágeis: Scrum Guide 2020, Kanban; abordagens preditivas/adaptativas/híbridas | `00-Curso Regular\06`, Aula 04 (Scrum), pág. 5-30 + Aula 06 (Kanban), pág. 5-19 + PMBOK 7 Tailoring | ✅ |
 
### Engenharia e Arquitetura de Software
*(triado em 12/09/2026 — ver `docs/triagens/triagem-bloco-engenharia-arquitetura-software-sefaz-sc.md`)*

| Assunto | Aula/PDF | Status |
|---|---|---|
| Ciclo de vida e processos de desenvolvimento; engenharia de requisitos (funcionais/não funcionais) | `00-Curso Regular\06`, Aulas 00-01 (Resumo) + Aula 07 (Resumo) | ✅ |
| Arquitetura de software, sistemas distribuídos, microsserviços, integração de aplicações | `00-Curso Regular\06`, Aula 13, pág. 10-30 | ✅ |
| Qualidade e testes de software | `00-Curso Regular\06`, Aula 11 (Resumo) + Aula 12 (Resumo) | ✅ |
| Métricas de software: APF, Pontos de Caso de Uso, produtividade/esforço/prazo/custo/qualidade, estimativas, uso em contratação/fiscalização | `00-Curso Regular\06`, Aula 17, pág. 3-53 | 🟡 (Pontos de Caso de Uso sem fonte dedicada — complemento via IA) |
| Git 2.x; CI/CD, DevOps, DevSecOps | `05-TCE-SC 2026 - Pos Edital\02`, Aula 05, pág. 3-24 | ✅ |
| APIs REST, HTTP/HTTPS, JSON, XML, autenticação, autorização, mensageria, interoperabilidade | `00-Curso Regular\06`, Aula 15 (Resumo) + Aula 14, pág. 5-38 | ✅ |
| C#, .NET, ASP.NET, HTML5, CSS3, JavaScript, TypeScript | `00-Curso Regular\05`, Aula 03, pág. 3-35,103-160 (C#/.NET) + Aula 13, pág. 3-50 (CSS) + Aula 14, pág. 3-13,54-57,68-70 (JS/TS) | ✅ |
| POO, arquitetura em camadas, cliente-servidor; leitura/análise de código-fonte | `00-Curso Regular\06`, Aula 09 (Resumo) + Aula 13, pág. 10-14 (camadas) | ✅ |

### Integração e Sistemas da Administração Pública
*(triado em 12/09/2026 — ver `docs/triagens/triagem-bloco-engenharia-arquitetura-software-sefaz-sc.md`)*

| Assunto | Aula/PDF | Status |
|---|---|---|
| Integração com sistemas estruturantes (planejamento, orçamento, finanças, contabilidade, compras, licitações, contratos, patrimônio); APIs, barramentos, mensageria | `05-TCE-SC 2026 - Pos Edital\01`, Aula 14 (DAMA-DMBOK), pág. 38-40 | 🟡 (lista de sistemas estruturantes específicos da administração pública brasileira sem fonte — complemento via IA) |
| Análise de integrações: interfaces, fluxos de dados, regras de negócio, controles, segurança, rastreabilidade | `05-TCE-SC 2026 - Pos Edital\01`, Aula 14 (DAMA-DMBOK), pág. 38-40 | 🟡 (mesmo gap do item anterior) |
 
---
 
## Trilha 3 — Infraestrutura e Segurança
 
### Infraestrutura, Redes e Computação em Nuvem
*(triado em 12/09/2026 — ver `docs/triagens/triagem-bloco-infraestrutura-seguranca-sefaz-sc.md`)*

| Assunto | Aula/PDF | Status |
|---|---|---|
| Servidores, SOs, virtualização, armazenamento, contêineres, alta disponibilidade, balanceamento | `05-TCE-SC 2026 - Pos Edital\07`, Aula 04 (Virtualização/Hypervisor), pág. 4-18,88-90 | ✅ |
| Redes: OSI/TCP-IP, IPv4/IPv6, TCP/UDP, DNS/DHCP, HTTP/HTTPS, LAN/WAN/WLAN/VLAN, NAT, VPN, roteamento, switching | `05-TCE-SC 2026 - Pos Edital\06`, Aulas 01 (Equip/OSI/TCPIP), 04 (IPv4), 05 (NAT/IPv6), 07 (HTTP), 08 (DNS) | 🟡 (DHCP/VLAN/roteamento sem fonte dedicada — complemento via IA) |
| Cloud: IaaS/PaaS/SaaS, pública/privada/híbrida, elasticidade, serverless, responsabilidade compartilhada; AWS/Azure/GCP | `05-TCE-SC 2026 - Pos Edital\07`, Aula 05 (Cloud + Azure AD), pág. 3-12 | ✅ |
| Docker e Kubernetes | `00-Curso Regular\05`, Aula 09, pág. 84-110,156-180 | ✅ |

### Segurança da Informação e Proteção de Dados
*(triado em 12/09/2026 — ver `docs/triagens/triagem-bloco-infraestrutura-seguranca-sefaz-sc.md`)*

| Assunto | Aula/PDF | Status |
|---|---|---|
| CIA, autenticidade, não repúdio; ameaças, vulnerabilidades, riscos, controles | `05-TCE-SC 2026 - Pos Edital\06`, Aula 09, pág. 3-11 + Aula 14 (ISO 27001/27002), pág. 3-25 + Aula 15 (ISO 27005), pág. 3-25 | ✅ |
| IAM, MFA, RBAC; segurança de redes/sistemas/BD/APIs/apps/endpoints/pipelines/cloud | `05-TCE-SC 2026 - Pos Edital\06`, Aula 09, pág. 58-69,93-115 | ✅ |
| Firewalls, IDS/IPS, WAF; hardening, gestão de vulnerabilidades/patches | `05-TCE-SC 2026 - Pos Edital\06`, Aula 10, pág. 3-33 | ✅ |
| Logs, monitoramento, incidentes, backup, continuidade | `05-TCE-SC 2026 - Pos Edital\06`, Aula 16, pág. 3-30 + `07`, Aula 03, pág. 95-109 | 🟡 (logs/monitoramento genérico só encontrado em contexto Linux — complemento via IA) |
| Criptografia simétrica/assimétrica, hashes, certificados, assinaturas, PKI, TLS, gestão de chaves | `05-TCE-SC 2026 - Pos Edital\06`, Aula 11 (SSL/TLS) + Aula 12 (Criptografia) + Aula 13 (Assinatura Digital) | ✅ |
| LGPD aplicada a sistemas/analytics/IA; Privacy by Design, anonimização/pseudonimização/mascaramento | `05-TCE-SC 2026 - Pos Edital\06`, Aula 14, pág. 75-90 (técnico) + `05-TCE-SC 2026 - Pos Edital\10`, Aula 20 (jurídico — LGPD como lei, ver bloco Gerais/CD) | ✅ (gap resolvido — ver `docs/triagens/triagem-bloco-gerais-matfin-etica-regionais-sefaz-sc.md`) |
 
---
 
## Trilha 4 — Síntese
 
### Auditoria e Controle com Uso de Tecnologia
| Assunto | Aula/PDF | Status |
|---|---|---|
| Aplicação de BD/SQL/BI/Ciência de Dados/automação/IA à auditoria/fiscalização; extração/cruzamento/análise de bases; indicadores de risco | `05-TCE-SC 2026 - Pos Edital\01`, Aula 21 (Auditoria Contínua e Análise de Fraudes), pág. 7-40 (reaproveitada do bloco Detecção de Anomalias) | ✅ |
| Auditoria de contratos de TI e serviços (dev/manutenção/sustentação/infra/suporte); conformidade contratual, SLA, métricas de software | `SEFAZ-CE 2026\15`, Aula 09 (Contratos de TI e IN 94/2022), pág. 3-42,44-49 + `00-Curso Regular\06`, Aula 17 (Métricas de Software), pág. 3-53 (reaproveitadas do bloco Governança) | ✅ |
| Auditoria de sistemas/aplicações: requisitos, arquitetura, código-fonte, integrações, controles, trilhas de auditoria | `10-Área Fiscal\22`, Aula 35 (ISO 27002, Resumo pág. 120-133, revisão) | ❌ (auditoria de SDLC/código-fonte/arquitetura sem fonte dedicada no acervo — complemento via IA) |
 
---
 
## Fora das trilhas
 
### Finanças Públicas
*(triado em 12/09/2026 — ver `docs/triagens/triagem-bloco-financas-publicas-sefaz-sc.md`)*

| Assunto | Aula/PDF | Status |
|---|---|---|
| Lei nº 4.320/1964 | `05-TCE-SC 2026 - Pos Edital\12`, Aula 00, pág. 5-30 | ✅ |
| Lei de Responsabilidade Fiscal | `05-TCE-SC 2026 - Pos Edital\12`, Aula 12, pág. 3-66 + Aula 13, pág. 3-40 | ✅ |
| PPA, LDO, LOA; princípios orçamentários | `05-TCE-SC 2026 - Pos Edital\12`, Aula 01, pág. 3-38 + Aula 02, pág. 3-35 | ✅ |
| Receita e despesa orçamentária; classificações; estágios | `05-TCE-SC 2026 - Pos Edital\12`, Aula 10, pág. 3-44 | ✅ |
| Créditos adicionais; restos a pagar; despesas de exercícios anteriores; fontes/destinações de recursos | `05-TCE-SC 2026 - Pos Edital\12`, Aula 03, pág. 3-45 + Aula 11, pág. 3-33 | ✅ |
 
### Inglês Técnico
Sem sessão dedicada — incorporar lendo documentação/artigos técnicos ao longo das outras trilhas.
 
---
 
## Gerais *(usando o documento correto — Ciências da Computação, não o de Direito)*
 
### Língua Portuguesa
*(triado em 12/09/2026, nível de reconhecimento — ver `docs/triagens/triagem-bloco-portugues-rlm-sefaz-sc.md`)*

| Assunto | Aula/PDF | Status |
|---|---|---|
| Redação oficial; ortografia/acentuação; crase | `10-Área Fiscal\39`, Aula 00 | 🟡 (redação oficial não confirmada — complemento via IA) |
| Compreensão e interpretação de textos (o mais cobrado em FCC); relação do texto com seu contexto histórico | `10-Área Fiscal\39`, Aula 08 | 🟡 (contexto histórico não confirmado — complemento via IA) |
| Morfossintaxe; concordância nominal/verbal; regência; flexão | `10-Área Fiscal\39`, Aulas 01,02,03,04 | ✅ |
| Vozes verbais; correlação verbal; coordenação/subordinação; conectivos | `10-Área Fiscal\39`, Aulas 03,07,09 | ✅ |
| Figuras de linguagem; discurso direto/indireto; pontuação; pronomes; sinonímia/antonímia; intertextualidade | `10-Área Fiscal\39`, Aulas 05,07 | 🟡 (figuras de linguagem/discurso/sinonímia-antonímia/intertextualidade não confirmados — complemento via IA) |
| Redação: confronto/reconhecimento de frases corretas/incorretas | `10-Área Fiscal\39`, Aula 08 | ✅ |
 
### Matemática Financeira/Estatística/RLM
*(Matemática Financeira e Combinatória triadas em 12/09/2026 — ver
`docs/triagens/triagem-bloco-gerais-matfin-etica-regionais-sefaz-sc.md`. Raciocínio Lógico com
fonte identificada mas ficha/PDF pendente de decisão sobre datas — ver aviso na mesma triagem)*

| Assunto | Aula/PDF | Status |
|---|---|---|
| Juros simples e compostos (montante, taxa real/efetiva, equivalentes, capitalização contínua) | `SEFAZ-CE 2026\12`, Aulas 01-02 | ✅ |
| Descontos (simples/composto/racional/comercial); amortizações (SAC/francês/misto) | `SEFAZ-CE 2026\12`, Aulas 03,06 | ✅ |
| Fluxo de caixa, valor atual, TIR | `SEFAZ-CE 2026\12`, Aulas 04-05 | ✅ |
| Estatística descritiva; combinatória | Descritiva já coberta na Trilha 1 + `10-Área Fiscal\36`, Aula 05 (combinatória) | ✅ |
| Probabilidade/distribuições *(já coberto na Trilha 1)* | — | ✅ |
| Inferência estatística *(já coberto na Trilha 1)* | — | ✅ |
| Raciocínio Lógico (verbal, matemático, sequencial, espacial/temporal) | `10-Área Fiscal\57`, Aulas 01,02,04,07,10 — ver `docs/triagens/triagem-bloco-portugues-rlm-sefaz-sc.md` | 🟡 ("orientação temporal" especificamente não confirmada — complemento via IA) |
 
### Direito Constitucional
*(triado em 12/09/2026, nível de reconhecimento — ver `docs/triagens/triagem-bloco-direito-constitucional-administrativo-sefaz-sc.md`)*

| Assunto | Aula/PDF | Status |
|---|---|---|
| Princípios fundamentais; direitos e garantias fundamentais (individuais/coletivos, sociais, nacionalidade, políticos) | `05-TCE-SC 2026 - Pos Edital\11`, Aulas 00,01,02,04,05,06 (amostras) | ✅ |
| Organização político-administrativa do Estado; administração pública/servidores públicos | `05-TCE-SC 2026 - Pos Edital\11`, Aulas 08,09 (núcleo) | ✅ |
| Poder Executivo; Poder Legislativo (fiscalização contábil/financeira/orçamentária); Finanças Públicas | `10-Área Fiscal\52`, Aulas 11,12,16 (núcleo) | 🟡 (fiscalização contábil/financeira/orçamentária — art. 70-75 CF — sem fonte dedicada) |
| Ordem econômica e financeira; Ordem social (seguridade social, mínimos constitucionais) | `10-Área Fiscal\52`, Aula 17 + `05-TCE-SC 2026 - Pos Edital\11`, Aula 10 (amostras) | ✅ |
| Constituição do Estado de Santa Catarina | `05-TCE-SC 2026 - Pos Edital\11`, Aulas 11-12 | ✅ |
 
### Direito Administrativo
*(triado em 12/09/2026, nível de reconhecimento — ver `docs/triagens/triagem-bloco-direito-constitucional-administrativo-sefaz-sc.md`)*

| Assunto | Aula/PDF | Status |
|---|---|---|
| Poderes da Administração; Responsabilidade Civil do Estado; Controle da Administração | `05-TCE-SC 2026 - Pos Edital\10`, Aulas 05,13,14 (núcleo) | ✅ |
| LC nº 741/2019; Lei nº 6.745/1985 | `05-TCE-SC 2026 - Pos Edital\10`, Aula 22 (Estatuto do Servidor Público Civil de SC) | ✅ |
| Lei nº 12.527/2011 (LAI) | `05-TCE-SC 2026 - Pos Edital\10`, Aula 19 | ✅ |
| Lei nº 8.429/1992 (Improbidade) | `05-TCE-SC 2026 - Pos Edital\10`, Aula 18 (núcleo) | ✅ |
| Lei nº 14.133/2021 (Licitações) | `05-TCE-SC 2026 - Pos Edital\10`, Aula 09 (introdução) | ✅ |
 
### Ciência e Análise de Dados
| Assunto | Aula/PDF | Status |
|---|---|---|
| Conceitos aplicados à Administração Pública *(já coberto na Trilha 1)* | — | ✅ |
| Governo Digital (transformação digital, serviços públicos digitais, interoperabilidade) | `SEFAZ-CE 2026\01`, Aula 03 | ✅ |
| LGPD como lei: princípios, bases legais, direitos dos titulares, agentes de tratamento | `05-TCE-SC 2026 - Pos Edital\10`, Aula 20 | ✅ |
 
### Ética, Integridade e Prevenção ao Assédio
*(triado em 12/09/2026 — ver `docs/triagens/triagem-bloco-gerais-matfin-etica-regionais-sefaz-sc.md`)*

| Assunto | Aula/PDF | Status |
|---|---|---|
| Ética no setor público; programas de integridade/compliance; prevenção a assédio/discriminação; Lei 12.846/2013 | `10-Área Fiscal\29`, Aula 21 | ✅ |
 
### Conhecimentos Regionais de SC
*(triado em 12/09/2026 — ver `docs/triagens/triagem-bloco-gerais-matfin-etica-regionais-sefaz-sc.md`)*

| Assunto | Aula/PDF | Status |
|---|---|---|
| História, Geografia, Cultura, Política, Economia de SC | | ❌ |
 
---
*Este mapa é a referência pra cada chat de triagem por bloco. O cronograma-detalhado-sessoes-sefaz-sc.md continua valendo como orçamento de semanas por trilha — o dia-a-dia dentro de cada bloco ainda não triado deve ser tratado como provisório até passar por aqui.*