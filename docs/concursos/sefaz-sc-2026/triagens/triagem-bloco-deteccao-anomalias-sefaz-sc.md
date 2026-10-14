# Triagem do Bloco: Detecção de Anomalias e Padrões Suspeitos (Trilha 1)
### SEFAZ SC 2026 — resultado da triagem de PDFs, complementa mapa-assuntos-edital-sefaz-sc.md e cronograma-detalhado-sessoes-sefaz-sc.md
*Gerado em 12/09/2026, com o índice completo (2639 PDFs).*

Todos os caminhos abaixo são relativos a `apostilas/`.

## Acervo identificado

Achado forte, fora da família de cursos usada nos blocos anteriores:

1. **`05-TCE-SC 2026 - Pos Edital\01-Banco de Dados`, Aula 21** (prof. Rodrigo Rennó, 53 pág.,
   "Auditoria Contínua e Análise de Fraudes") — **fonte principal**, encaixe quase perfeito com
   o assunto fino do edital: mapeamento de riscos, trilhas de auditoria, monitoramento em tempo
   real, falso positivo definido no contexto exato de controle externo, com exemplos concretos
   de licitação/cartel e Data Mining aplicado a compras públicas. Vem de um curso pra TCE-SC —
   o "primo" fiscalizador do SEFAZ SC, mesmo estado, ângulo de auditoria de dados idêntico ao
   que o edital pede. **Sem banco de questões próprio** (a aula termina em Resumo, só imagem).
2. **`05-TCE-SC 2026 - Pos Edital\01-Banco de Dados`, Aula 19** (prof. Lucas Ianni, 84 pág.,
   "Métricas de Avaliação de Modelos de Classificação/Regressão") — complementa com a teoria
   formal de falsos positivos/negativos e matriz de confusão (que a Aula 21 usa mas não
   formaliza), **e fornece o banco de questões que a Aula 21 não tem**.

## Decisão da Etapa 0 — descartes

- **Aula 21:** pág. 41-53 é "Resumo" só em imagem (mapa mental), sem texto extraível — não é
  leitura, só revisão visual opcional.
- **Aula 19:** só a seção "7.0 Métricas de Avaliação de Modelos de Classificação" (Teoria
  pág. 4-31, Questões pág. 32-56) é deste bloco. A seção "7.1 Métricas de Regressão" (Teoria
  pág. 57-62, Questões pág. 63+) pertence ao bloco Estatística/CD/ML (métricas/scikit-learn),
  já triado — não reler aqui.
- **`10-Área Fiscal\22-Curso Completo de TI`, Aula 16** ("Machine Learning – Básico" — o termo
  "detecção de anomalias" aparece lá só como exemplo dentro de Tipos de Aprendizado, não é o
  tema da aula): já é redundante com o que a Estatística/CD/ML já cobriu, e não tem o ângulo de
  auditoria/setor público que este assunto pede — descartada como fonte principal.

## Gap confirmado

Nenhum. Assunto fino coberto com boa profundidade e no ângulo certo (auditoria de dados no
setor público, não só ML genérico):

| Assunto (mapa-assuntos) | Status |
|---|---|
| Técnicas estatísticas/regras/ML pra anomalias; aplicação a transações financeiras/orçamentárias/compras/contratos/licitações; falsos positivos/negativos, indicadores de risco | ✅ |

## Etapa 1 — cronograma

**Sem mudança**: o orçamento de 1 dia (Dom 04/10) já é suficiente — Aula 21 (34 pág. de teoria
real) + Aula 19 (28 pág. de teoria + questões) somam um volume compatível com o já usado em
dias de 1 assunto só nos blocos anteriores.

## Etapa 2 — roteiro do dia

### Dom 04/10 — Detecção de Anomalias: técnicas estatísticas/ML, análise de transações, falsos positivos/negativos, indicadores de risco
- **Leitura:**
  - `05-TCE-SC 2026 - Pos Edital\01-Banco de Dados`, `Aula 21.pdf` (Auditoria Contínua e
    Análise de Fraudes): pág. 7-40 — cobre o paradigma de Auditoria Contínua (substitui
    amostragem manual por monitoramento automatizado), Mapeamento de Riscos e Trilhas de
    Auditoria (roteiro: entendimento do negócio → análise de regras → tipologias), exemplo de
    Data Mining detectando cartel em licitação, Falso Positivo no contexto de controle externo,
    Monitoramento em Tempo Real (red flags/indicadores).
  - `05-TCE-SC 2026 - Pos Edital\01-Banco de Dados`, `Aula 19.pdf` — Métricas de Avaliação de
    Modelos de Classificação (formaliza falsos positivos/negativos, matriz de confusão): pág. 4-31.
- **Pretest:** 2-3 questões antes da leitura, mesmo chutando — `Aula 19.pdf`, Questões
  pág. 32+ (só a parte de Classificação, não ler as de Regressão a partir da pág. 63).
- **Fixação:** 5-8 questões ao final — assunto único do dia, aproveitar pra reforçar bem.
- **Banco de reserva:** mesma fonte (`Aula 19.pdf`), questões restantes de Classificação
  (pág. 32-56) que não tiverem sido usadas no pretest/fixação — volta Sáb 10/10 (revisão geral
  da Trilha 1).
- **Observações:** nenhum gap conhecido. A Aula 21 não tem banco de questões próprio — o
  reforço de questões vem inteiramente da Aula 19, que é sobre métricas (mais genérica), não
  sobre o cenário de auditoria/fraude em si — ok pra fixação de falsos positivos/negativos, mas
  não testa o conteúdo de auditoria contínua/trilhas de auditoria diretamente. Se sobrar tempo,
  vale simular 2-3 questões próprias (via IA) sobre os exemplos concretos da Aula 21
  (cartel em licitação, red flags).

## Impacto no cronograma master

Nenhum — orçamento de 1 dia confirmado suficiente.
