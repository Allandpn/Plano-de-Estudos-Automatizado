# Triagem do Bloco: Auditoria e Controle com Uso de Tecnologia (Trilha 4 — Síntese)
### SEFAZ SC 2026 — resultado da triagem de PDFs, complementa mapa-assuntos-edital-sefaz-sc.md e cronograma-detalhado-sessoes-sefaz-sc.md
*Gerado em 12/09/2026, com o índice completo (2639 PDFs).*

Todos os caminhos abaixo são relativos a `apostilas/`.

## Natureza deste bloco

Trilha 4 é "Síntese": os 3 assuntos finos aqui não pedem teoria nova, pedem a aplicação do
que já foi triado em blocos anteriores (BD/SQL/BI/CD/ML, Detecção de Anomalias, Governança de
TI) sob a ótica específica de auditoria/fiscalização. Por isso a busca priorizou primeiro
reaproveitar fontes já mapeadas, e só then buscar fontes novas pro que sobrar sem cobertura.

## Acervo identificado

1. **`05-TCE-SC 2026 - Pos Edital\01-Banco de Dados`, Aula 21** (prof. Rodrigo Rennó, 53 pág.,
   "Auditoria Contínua e Análise de Fraudes") — **reaproveitada** do bloco Detecção de
   Anomalias (`docs/triagens/triagem-bloco-deteccao-anomalias-sefaz-sc.md`). Cobre
   exatamente o assunto 1 (extração/cruzamento de bases, Data Mining aplicado a
   compras/licitações, indicadores de risco/red flags, trilhas de auditoria, monitoramento em
   tempo real) — mesmo texto, agora lido com o foco em "aplicação de tecnologia à auditoria"
   em vez de "técnica de detecção de anomalias" em si.
2. **`SEFAZ-CE 2026\15-Governança, Gestão e Contratações de TIC`, Aula 09**
   (`curso-383844-aula-09-prof-paolla-ramos-e-fernando-pedrosa-somente-em-pdf-67b0-completo.pdf`,
   "Contratos de TI e IN 94/2022") — **reaproveitada** do bloco Governança/Gestão de TI
   (`docs/triagens/triagem-bloco-governanca-gestao-ti-projetos-sefaz-sc.md`). Cobre o núcleo do
   assunto 2 (planejamento/contratação/fiscalização, gestão de fornecedores, SLA, critérios de
   aceite, entregáveis).
3. **`00-Curso Regular\06-Engenharia de Software`, Aula 17** (Métricas de Software: APF, Pontos
   de Caso de Uso, produtividade/esforço/prazo/custo/qualidade) — **reaproveitada** do mesmo
   bloco Governança, completa o assunto 2 com a parte de métricas usadas em
   contratação/fiscalização de serviços de TI.

## Decisão da Etapa 0 — descartes e busca do assunto 3

Pro assunto 3 ("Auditoria de sistemas/aplicações: requisitos, arquitetura, código-fonte,
integrações, controles, trilhas de auditoria"), orçamento de busca completo, sem sucesso:

- Query direta "auditoria de sistemas de informação" / "auditoria de aplicações" / "auditoria
  de desenvolvimento de sistemas": só retornou (a) `10-Área Fiscal\22-Curso Completo de
  Tecnologia da Informação`, Aulas 34/35 — na verdade é a NBR ISO 27002-2022 completa
  (controles gerais de segurança, já ✅ no bloco Infraestrutura/Segurança), o trecho que
  aparece é só o controle 8.34 ("Proteção de sistemas de informação durante testes de
  auditoria" — sobre não expor dados de produção durante o teste, não é sobre auditar o
  sistema em si); (b) `48-Especialidade TI - Auditoria` e `SEFAZ-CE 2026\02-Auditoria` — curso
  genérico de auditoria contábil/financeira (normas NBC TA: evidência, amostragem, controle
  interno, continuidade), sem seção dedicada a auditoria de SDLC/código-fonte/arquitetura de
  sistemas.
- 2 sinônimos testados ("ISACA auditoria de TI", "ciclo de vida de sistemas auditoria"): só
  retornaram menções de passagem (link pro site da ISACA num rodapé de referência; norma de
  ciclo de vida de sistemas em Engenharia de Software sem ângulo de auditoria).
- 2 PDFs candidatos abertos (~20 pág. cada, verificação direta): `10-Área Fiscal\22`, Aula 35
  (índice completo: só ISO 27002 — Teoria/Resumo/Questões, nenhuma seção de auditoria de
  sistemas propriamente); `07-TSE Unificado\05-Gestão e Governança de TI`, Aula 12, pág. 26
  (menção a "auditoria de SGSI" no contexto de ISO 27001, já ✅ coberto, não desenvolve
  requisitos/arquitetura/código-fonte).

## Gap confirmado

| Assunto (mapa-assuntos) | Status |
|---|---|
| Aplicação de BD/SQL/BI/Ciência de Dados/automação/IA à auditoria/fiscalização; extração/cruzamento/análise de bases; indicadores de risco | ✅ |
| Auditoria de contratos de TI e serviços (dev/manutenção/sustentação/infra/suporte); conformidade contratual, SLA, métricas de software | ✅ |
| Auditoria de sistemas/aplicações: requisitos, arquitetura, código-fonte, integrações, controles, trilhas de auditoria | ❌ (sem fonte dedicada no acervo — complemento via IA) |

O acervo (~2600 apostilas do Estratégia Concursos) não tem um curso de "Auditoria de Sistemas
de TI" no sentido ISACA/CISA (auditoria de SDLC, revisão de requisitos e arquitetura, auditoria
de código-fonte, auditoria de integrações). O que existe é (a) auditoria contábil/financeira
genérica (NBC TA) e (b) controles de segurança da informação (ISO 27001/27002) — ambos já
mapeados em blocos anteriores mas nenhum cobre o assunto no ângulo específico que o edital
pede. Tratamento: nível de reconhecimento com o material mais próximo (ISO 27002 — controles,
já ✅ em Infraestrutura/Segurança — revisitado en passant) + complemento via IA cobrindo
especificamente: papel do auditor de TI na revisão de requisitos e arquitetura, técnicas de
auditoria de código-fonte (revisão estática, trilha de rastreabilidade requisito→código),
auditoria de integrações (contratos de API, pontos de falha), e o conceito de "trilha de
auditoria" (log de auditoria) já coberto tecnicamente em Segurança (`05-TCE-SC 2026 - Pos
Edital\06`, Aula 16) mas sem a lente de "isso é o que o auditor de sistemas verifica".

## Etapa 1 — cronograma

**Sem mudança**: os 3 dias já reservados na Semana 10 (Seg 02/11, Ter 03/11, Qui 05/11) batem
com os 3 assuntos, 1 por dia — orçamento confirmado suficiente, nível de reconhecimento por
ser bloco de síntese/aplicação (conteúdo técnico de base já foi estudado a fundo nos blocos de
origem).

## Etapa 2 — roteiro por dia

### Seg 02/11 — Auditoria com Tecnologia: aplicação de BD/SQL/BI/CD/IA à auditoria/fiscalização
- **Leitura:**
  - `05-TCE-SC 2026 - Pos Edital\01-Banco de Dados`, `Aula 21.pdf` (Auditoria Contínua e
    Análise de Fraudes): pág. 7-40 — releitura focada em "quais tecnologias/técnicas de
    dados o auditor usa e como" (Data Mining em compras públicas, Análise de Redes
    cruzando QSA da Receita Federal, sistemas ALICE/ADELE de IA sobre editais, Monitoramento
    em Tempo Real com regras preventivas/reativas).
- **Pretest:** 2-3 questões antes, mesmo chutando — banco de questões já usado no bloco
  Detecção de Anomalias (`Aula 19.pdf`, pág. 32+), não repetir se já feitas naquele dia;
  senão, revisar de memória os casos hipotéticos da própria Aula 21.
- **Fixação:** 5-8 questões ao final — foco em "qual tecnologia resolve qual problema de
  auditoria" (não repetir o drill de falsos positivos/negativos, isso já foi fixado no bloco
  de origem).
- **Banco de reserva:** nenhum adicional — mesma fonte do bloco de origem, já esgotada lá.
- **Observações de gap:** nenhum — release intencional do mesmo material, ótica de síntese.

### Ter 03/11 — Auditoria com Tecnologia: auditoria de contratos de TI, SLA, métricas de software
- **Leitura:**
  - `SEFAZ-CE 2026\15-Governança, Gestão e Contratações de TIC`,
    `curso-383844-aula-09-prof-paolla-ramos-e-fernando-pedrosa-somente-em-pdf-67b0-completo.pdf`,
    Teoria: pág. 3-42 (Contratos de TI e IN 94/2022 — planejamento/contratação/fiscalização,
    gestão de fornecedores, SLA, critérios de aceite, entregáveis) + Resumo pág. 44-49.
  - `00-Curso Regular\06-Engenharia de Software`, `aula 17.pdf`, Teoria: pág. 3-53 (Métricas de
    Software — APF, Pontos de Caso de Uso, produtividade/esforço/prazo/custo/qualidade,
    estimativas, uso em contratação/fiscalização).
- **Pretest:** 2-3 questões de cada — Contratos Questões Comentadas pág. 50+; Métricas de
  Software Questões (mesma aula 17, verificar sumário local).
- **Fixação:** 5-8 questões ao final, foco no cruzamento "SLA/critério de aceite ↔ métrica
  usada pra medir isso" (é a ponte de síntese que o assunto pede).
- **Banco de reserva:** Contratos Lista de Questões pág. 80+ (mesma do bloco Governança).
- **Observações de gap:** herdado do mapa — 🟡 em Pontos de Caso de Uso (sem fonte dedicada,
  complemento via IA), já registrado no bloco Governança.

### Qui 05/11 — Auditoria com Tecnologia: auditoria de sistemas/aplicações (fechamento)
- **Leitura:**
  - `10-Área Fiscal\22-Curso Completo de Tecnologia da Informação`,
    `curso-247678-aula-35-prof-diego-carvalho-e-andre-castro-1d7.pdf`, Resumo: pág. 120-133
    (ISO 27002 — controles de auditoria/proteção de sistemas em teste, revisão rápida, nível
    de reconhecimento — não reler a Teoria completa, já ✅ em Infraestrutura/Segurança).
  - **Complemento via IA (gap ❌):** requisitos e arquitetura como objeto de auditoria
    (rastreabilidade requisito→implementação), técnicas de auditoria de código-fonte (revisão
    estática, SAST, code review como controle), auditoria de integrações (contratos de API,
    pontos únicos de falha), e trilha de auditoria (log) pela ótica do auditor de sistemas —
    gerar um resumo de 3-5 páginas via IA cobrindo esses pontos antes da sessão.
- **Pretest:** 2-3 questões sobre ISO 27002 (Multibancas, pág. 134+, se ainda não usadas no
  bloco Segurança).
- **Fixação:** 5-8 questões — combinar as de ISO 27002 com questões geradas via IA sobre o
  complemento de auditoria de sistemas.
- **Banco de reserva:** nenhum — fechamento do mapa de assuntos (105/105).
- **Observações de gap:** ❌ confirmado — auditoria de sistemas/aplicações (SDLC,
  código-fonte, arquitetura, integrações) sem fonte dedicada no acervo. Resolvido só via
  complemento por IA.

## Impacto no cronograma master

Nenhum — orçamento de 3 dias (Seg02/11, Ter03/11, Qui05/11) confirmado suficiente, sem
necessidade de consumir buffer adicional.

## Fechamento do mapa-assuntos

Com este bloco, os 105/105 assuntos finos do edital SEFAZ SC 2026 estão triados.
