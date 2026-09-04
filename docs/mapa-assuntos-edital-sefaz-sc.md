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
| Assunto | Aula/PDF | Status |
|---|---|---|
| Governança: papéis, catálogo, glossário, metadados, dicionário, linhagem | | |
| Ciclo de vida, dados mestres/referência | | |
| Qualidade de dados (completude, consistência, validade, precisão, unicidade, integridade, atualidade) | | |
| Data profiling, limpeza, tratamento de inconsistências/duplicidades/outliers | | |
 
### Programação e Automação para Dados
| Assunto | Aula/PDF | Status |
|---|---|---|
| Lógica de programação, algoritmos, estruturas de dados, funções, exceções | | |
| Python 3.14.x — sintaxe | | |
| NumPy 2.5.x, pandas 3.0.x | | |
| CSV, JSON, XML — manipulação/transformação/integração | | |
| Consumo de APIs, web scraping | | |
| Automação de rotinas, RPA | | |
 
### Estatística, Ciência de Dados e Machine Learning
| Assunto | Aula/PDF | Status |
|---|---|---|
| Estatística descritiva (medidas de posição/dispersão) | | |
| Probabilidade e distribuições | | |
| Inferência: amostragem, IC, testes de hipótese, correlação, regressão | | |
| Análise exploratória de dados | | |
| Ciclo de vida de projetos de Ciência de Dados; preparação/engenharia/seleção de atributos | | |
| Aprendizado supervisionado/não supervisionado: classificação, regressão, clustering | | |
| Árvores de decisão, ensemble, algoritmos baseados em distância | | |
| Treinamento, validação, overfitting/underfitting, métricas de avaliação, scikit-learn | | |
 
### Detecção de Anomalias e Padrões Suspeitos
| Assunto | Aula/PDF | Status |
|---|---|---|
| Técnicas estatísticas/regras/ML pra anomalias; aplicação a transações financeiras/orçamentárias/compras/contratos/licitações; falsos positivos/negativos, indicadores de risco | | |
 
### Business Intelligence, Analytics e Visualização
| Assunto | Aula/PDF | Status |
|---|---|---|
| Arquitetura de BI, indicadores, análise descritiva/diagnóstica/preditiva/prescritiva, self-service BI | Aula 15 nova (BI e KDD, pág 3-10) — a confirmar em triagem dedicada | 🟡 |
| Power BI: Power Query, linguagem M, modelagem de dados | | ❌ |
| Power BI: DAX, medidas, relacionamentos, filtros, dashboards | | ❌ |
 
### Inteligência Artificial, PLN e IA Generativa
| Assunto | Aula/PDF | Status |
|---|---|---|
| Conceitos de IA, Deep Learning, redes neurais | | |
| PLN: classificação, extração, entidades, similaridade, busca semântica, sumarização | | |
| LLMs, transformers, tokens, embeddings, prompt engineering, RAG, bancos vetoriais, agentes de IA, PyTorch/TensorFlow | | |
| Alucinações, vieses, segurança, privacidade, explicabilidade, uso responsável | | |
 
---
 
## Trilha 2 — Governança, Projetos e Engenharia
 
### Governança, Gestão de TI e Projetos
| Assunto | Aula/PDF | Status |
|---|---|---|
| Governança de TI: alinhamento estratégico, serviços, processos, riscos, controles, indicadores; COBIT 2019 e ITIL v5 | | |
| Contratos de TI: planejamento/contratação/fiscalização, gestão de fornecedores, SLA, critérios de aceite, entregáveis | | |
| Gestão de riscos contratuais, controles, monitoramento, conformidade | | |
| Gerenciamento de projetos: PMBOK Guide 8ª edição | | |
| Métodos ágeis: Scrum Guide 2020, Kanban; abordagens preditivas/adaptativas/híbridas | | |
 
### Engenharia e Arquitetura de Software
| Assunto | Aula/PDF | Status |
|---|---|---|
| Ciclo de vida e processos de desenvolvimento; engenharia de requisitos (funcionais/não funcionais) | | |
| Arquitetura de software, sistemas distribuídos, microsserviços, integração de aplicações | | |
| Qualidade e testes de software | | |
| Métricas de software: APF, Pontos de Caso de Uso, produtividade/esforço/prazo/custo/qualidade, estimativas, uso em contratação/fiscalização | | |
| Git 2.x; CI/CD, DevOps, DevSecOps | | |
| APIs REST, HTTP/HTTPS, JSON, XML, autenticação, autorização, mensageria, interoperabilidade | | |
| C#, .NET, ASP.NET, HTML5, CSS3, JavaScript, TypeScript | | |
| POO, arquitetura em camadas, cliente-servidor; leitura/análise de código-fonte | | |
 
### Integração e Sistemas da Administração Pública
| Assunto | Aula/PDF | Status |
|---|---|---|
| Integração com sistemas estruturantes (planejamento, orçamento, finanças, contabilidade, compras, licitações, contratos, patrimônio); APIs, barramentos, mensageria | | |
| Análise de integrações: interfaces, fluxos de dados, regras de negócio, controles, segurança, rastreabilidade | | |
 
---
 
## Trilha 3 — Infraestrutura e Segurança
 
### Infraestrutura, Redes e Computação em Nuvem
| Assunto | Aula/PDF | Status |
|---|---|---|
| Servidores, SOs, virtualização, armazenamento, contêineres, alta disponibilidade, balanceamento | | |
| Redes: OSI/TCP-IP, IPv4/IPv6, TCP/UDP, DNS/DHCP, HTTP/HTTPS, LAN/WAN/WLAN/VLAN, NAT, VPN, roteamento, switching | | |
| Cloud: IaaS/PaaS/SaaS, pública/privada/híbrida, elasticidade, serverless, responsabilidade compartilhada; AWS/Azure/GCP | | |
| Docker e Kubernetes | | |
 
### Segurança da Informação e Proteção de Dados
| Assunto | Aula/PDF | Status |
|---|---|---|
| CIA, autenticidade, não repúdio; ameaças, vulnerabilidades, riscos, controles | | |
| IAM, MFA, RBAC; segurança de redes/sistemas/BD/APIs/apps/endpoints/pipelines/cloud | | |
| Firewalls, IDS/IPS, WAF; hardening, gestão de vulnerabilidades/patches | | |
| Logs, monitoramento, incidentes, backup, continuidade | | |
| Criptografia simétrica/assimétrica, hashes, certificados, assinaturas, PKI, TLS, gestão de chaves | | |
| LGPD aplicada a sistemas/analytics/IA; Privacy by Design, anonimização/pseudonimização/mascaramento | | |
 
---
 
## Trilha 4 — Síntese
 
### Auditoria e Controle com Uso de Tecnologia
| Assunto | Aula/PDF | Status |
|---|---|---|
| Aplicação de BD/SQL/BI/Ciência de Dados/automação/IA à auditoria/fiscalização; extração/cruzamento/análise de bases; indicadores de risco | | |
| Auditoria de contratos de TI e serviços (dev/manutenção/sustentação/infra/suporte); conformidade contratual, SLA, métricas de software | | |
| Auditoria de sistemas/aplicações: requisitos, arquitetura, código-fonte, integrações, controles, trilhas de auditoria | | |
 
---
 
## Fora das trilhas
 
### Finanças Públicas
| Assunto | Aula/PDF | Status |
|---|---|---|
| Lei nº 4.320/1964 | | |
| Lei de Responsabilidade Fiscal | | |
| PPA, LDO, LOA; princípios orçamentários | | |
| Receita e despesa orçamentária; classificações; estágios | | |
| Créditos adicionais; restos a pagar; despesas de exercícios anteriores; fontes/destinações de recursos | | |
 
### Inglês Técnico
Sem sessão dedicada — incorporar lendo documentação/artigos técnicos ao longo das outras trilhas.
 
---
 
## Gerais *(usando o documento correto — Ciências da Computação, não o de Direito)*
 
### Língua Portuguesa
| Assunto | Aula/PDF | Status |
|---|---|---|
| Redação oficial; ortografia/acentuação; crase | | |
| Compreensão e interpretação de textos (o mais cobrado em FCC); relação do texto com seu contexto histórico | | |
| Morfossintaxe; concordância nominal/verbal; regência; flexão | | |
| Vozes verbais; correlação verbal; coordenação/subordinação; conectivos | | |
| Figuras de linguagem; discurso direto/indireto; pontuação; pronomes; sinonímia/antonímia; intertextualidade | | |
| Redação: confronto/reconhecimento de frases corretas/incorretas | | |
 
### Matemática Financeira/Estatística/RLM
| Assunto | Aula/PDF | Status |
|---|---|---|
| Juros simples e compostos (montante, taxa real/efetiva, equivalentes, capitalização contínua) | | |
| Descontos (simples/composto/racional/comercial); amortizações (SAC/francês/misto) | | |
| Fluxo de caixa, valor atual, TIR | | |
| Estatística descritiva; combinatória | | |
| Probabilidade/distribuições *(já coberto na Trilha 1)* | — | ✅ |
| Inferência estatística *(já coberto na Trilha 1)* | — | ✅ |
| Raciocínio Lógico (verbal, matemático, sequencial, espacial/temporal) | | |
 
### Direito Constitucional
| Assunto | Aula/PDF | Status |
|---|---|---|
| Princípios fundamentais; direitos e garantias fundamentais (individuais/coletivos, sociais, nacionalidade, políticos) | | |
| Organização político-administrativa do Estado; administração pública/servidores públicos | | |
| Poder Executivo; Poder Legislativo (fiscalização contábil/financeira/orçamentária); Finanças Públicas | | |
| Ordem econômica e financeira; Ordem social (seguridade social, mínimos constitucionais) | | |
| Constituição do Estado de Santa Catarina | | |
 
### Direito Administrativo
| Assunto | Aula/PDF | Status |
|---|---|---|
| Poderes da Administração; Responsabilidade Civil do Estado; Controle da Administração | | |
| LC nº 741/2019; Lei nº 6.745/1985 | | |
| Lei nº 12.527/2011 (LAI) | | |
| Lei nº 8.429/1992 (Improbidade) | | |
| Lei nº 14.133/2021 (Licitações) | | |
 
### Ciência e Análise de Dados
| Assunto | Aula/PDF | Status |
|---|---|---|
| Conceitos aplicados à Administração Pública *(já coberto na Trilha 1)* | — | ✅ |
| Governo Digital (transformação digital, serviços públicos digitais, interoperabilidade) | | |
| LGPD como lei: princípios, bases legais, direitos dos titulares, agentes de tratamento | | |
 
### Ética, Integridade e Prevenção ao Assédio
| Assunto | Aula/PDF | Status |
|---|---|---|
| Ética no setor público; programas de integridade/compliance; prevenção a assédio/discriminação; Lei 12.846/2013 | | |
 
### Conhecimentos Regionais de SC
| Assunto | Aula/PDF | Status |
|---|---|---|
| História, Geografia, Cultura, Política, Economia de SC | | |
 
---
*Este mapa é a referência pra cada chat de triagem por bloco. O cronograma-detalhado-sessoes-sefaz-sc.md continua valendo como orçamento de semanas por trilha — o dia-a-dia dentro de cada bloco ainda não triado deve ser tratado como provisório até passar por aqui.*