# Triagem do Bloco: Estatística, Ciência de Dados e Machine Learning (Trilha 1)
### SEFAZ SC 2026 — resultado da triagem de PDFs, complementa mapa-assuntos-edital-sefaz-sc.md e cronograma-detalhado-sessoes-sefaz-sc.md
*Gerado em 12/09/2026, com o índice completo (2639 PDFs).*

Todos os caminhos abaixo são relativos a `apostilas/`.

## Acervo identificado

Duas famílias de curso, papéis bem diferentes:

1. **`10-Área Fiscal\50-Especialidade TI - Ciência de Dados`** (16 aulas, prof. Thiago
   Rodrigues Cavalcanti, `curso-263551-aula-NN-...pdf`) — **fonte principal**, curso dedicado e
   focado em TI (não em Matemática/RLM pesada). Cobre com boa profundidade e no nível certo
   pro edital: Aula 02 (Mineração de Dados + Pré-Processamento), Aula 04 (Estatística + Análise
   Exploratória + Visualização), Aula 05 (Aprendizado Supervisionado, 191 pág.), Aula 06
   (Aprendizado Não Supervisionado, 47 pág.).
2. **`10-Área Fiscal\15-Curso Básico de Estatística`** (18 aulas, `curso-220877-aula-NN-...pdf`)
   — curso genérico e **muito mais profundo do que este bloco precisa** (798 páginas só pra
   "medidas de posição/dispersão", divididas em 4 aulas inteiras: Aula 01 Média, Aula 02
   Mediana, Aula 03 Moda, Aula 04 Dispersão). **Usado só pontualmente**, pras duas partes que a
   Aula 04 da Ciência de Dados não cobre em profundidade: Probabilidade e distribuições (Aula
   09: discretas — Bernoulli/Binomial/Geométrica/Hipergeométrica/Poisson; Aula 11: contínuas —
   Uniforme/Exponencial/Normal/Qui-Quadrado/T-Student) e Inferência mais formal (Aula 15:
   Testes de Hipóteses).

## Decisão da Etapa 0 — descartes

- **`10-Área Fiscal\15-Curso Básico de Estatística`:** só usamos Aula 09 (Distribuições
  Discretas), Aula 11 (Distribuições Contínuas) e o início da Aula 15 (Testes de Hipóteses,
  conceitos fundamentais). **Aulas 01-04 (Medidas de Posição/Dispersão, 798 pág.) ficam de
  fora** — a Aula 04 da Ciência de Dados já cobre média/mediana/moda/variância/desvio padrão
  de forma direta e suficiente pro nível do edital (item é uma única linha, não uma prova
  inteira de Estatística/RLM). Aulas 05-08 (Assimetria/Curtose/Correlação/Regressão — ainda não
  conferidas) e 12-17 ficam como reforço opcional futuro, não lidas agora.
- **`10-Área Fiscal\22-Curso Completo de TI`, Aulas 23-31:** já checadas durante a triagem
  anterior (Programação/Automação) e nesta — são Linguagem R, Processos de Negócio/BPMN,
  COBIT/ITIL/MPS.BR (Governança de TI) — nenhuma é deste bloco.
- **Ciência de Dados, Aula 00, 01, 03, 07-15:** fora de escopo fino deste bloco (respectivamente
  Banco de Dados/apresentação, ETL, Big Data/NoSQL/Hadoop — já vistos no bloco Data Warehouse
  —, Visão Computacional/Deep Learning/PLN/Séries Temporais/Ingestão — pertencem ao bloco IA/PLN/
  GenAI ou ficam de fora do mapa-assuntos atual). Não ler aqui.

## Gap confirmado

Nenhum ❌. Um 🟡 real (correlação/regressão dentro de Inferência) e um ponto de atenção
(volume de Probabilidade):

| Assunto (mapa-assuntos) | Status | Observação |
|---|---|---|
| Estatística descritiva (medidas de posição/dispersão) | ✅ | Condensado mas completo — média, mediana, moda, variância, desvio padrão |
| Probabilidade e distribuições | ✅ | Completo (9 distribuições nomeadas no edital, todas encontradas) — **mas é MUITO volume** (~140 pág. de Teoria densa), maior dia do bloco de longe |
| Inferência: amostragem, IC, testes de hipótese, correlação, regressão | 🟡 | Amostragem ✅ (tipos probabilísticos/não-probabilísticos); IC e testes de hipótese ✅ (conceitos fundamentais + tipos de erro); **correlação e regressão como técnicas de inferência não confirmadas nesta fonte** — resolver com IA no dia, ou complementar depois se sobrar tempo (aulas 05-08 do Curso Básico de Estatística, ainda não conferidas, podem tê-las) |
| Análise exploratória de dados | ✅ | Completo — inclui outliers e escalas de mensuração (nominal/ordinal/intervalar/proporção) |
| Ciclo de vida de projetos de Ciência de Dados; preparação/engenharia/seleção de atributos | ✅ | Completo — Mineração de Dados (inclui CRISP-DM) + Técnicas de Pré-Processamento |
| Aprendizado supervisionado/não supervisionado: classificação, regressão, clustering | ✅ | Completo |
| Árvores de decisão, ensemble, algoritmos baseados em distância | ✅ | Completo (mesma fonte do item anterior — Aula 05 mistura os conceitos por algoritmo, não dá pra separar por dia limpo) |
| Treinamento, validação, overfitting/underfitting, métricas de avaliação, scikit-learn | ✅ | Completo (idem — interleaved na Aula 05) |

## Etapa 1 — cronograma

**Correção: Probabilidade e distribuições precisa de dia próprio.** A fusão de Estatística
Descritiva + Probabilidade no Dom 27/09 (decidida na triagem anterior, do bloco Programação)
partiu da suposição de que ambas seriam rápidas — descritiva é mesmo rápida (aula curta, 7
pág.), **mas Probabilidade não é**: são 9 distribuições nomeadas explicitamente no edital, cada
uma com definição+fórmula+exemplo, só encontradas na fonte funda (~140 pág. de Teoria).

| Fonte | Conteúdo | Páginas |
|---|---|---|
| CD Aula 04 — Estatística (condensado) | Definições, amostragem, parâmetro/estimador, média/mediana/moda/variância/desvio padrão | 3-9 |
| CD Aula 04 — Análise Exploratória de Dados | AED, outliers, escalas de mensuração | 10-19 |
| CD Aula 02 — Mineração de Dados + Pré-Processamento | CRISP-DM, técnicas de pré-processamento (limpeza, seleção de atributos) | 3-42 |
| Estatística Básica Aula 09 — Distribuições Discretas | Uniforme, Bernoulli, Binomial, Geométrica, Hipergeométrica, Poisson | 5-67 |
| Estatística Básica Aula 11 — Distribuições Contínuas | Uniforme, Exponencial, Normal, Soma de Variáveis/TCL, Qui-Quadrado, T-Student, F-Snedecor | 5-79 |
| Estatística Básica Aula 15 — Testes de Hipóteses (só o início) | Introdução, conceitos fundamentais, tipos de erro | 4-24 |
| CD Aula 05 — Aprendizado Supervisionado | Regressão, classificação, árvores, KNN, distância, ensemble, overfitting, métricas, scikit-learn (tudo interleaved) | 3-167 |
| CD Aula 06 — Aprendizado Não Supervisionado | Clustering | 3-39 |

**Reorganização proposta (contida na Semana 5, sem tocar Semana 6 em diante):** desmembrar
Descritiva de Probabilidade (volta a ser 1 dia cada, não mais fundidos), empurrando o resto da
semana em 1 dia e consumindo o dia de "questões mistas" (Sáb 03/10) como dia de conteúdo —
Qua 30/09 (Matemática Financeira, já fixado por dois ajustes anteriores) **não muda de data**:

| Dia | Antes (pós-ajuste do bloco Python) | Depois (este ajuste) |
|---|---|---|
| Dom 27/09 | Estatística descritiva + Probabilidade | Estatística descritiva (sozinha) |
| Seg 28/09 | Inferência | **Probabilidade e distribuições** |
| Ter 29/09 | Ciência de Dados (AED/ciclo de vida) | **Inferência** |
| Qua 30/09 | Matemática Financeira | Matemática Financeira (inalterado) |
| Qui 01/10 | ML: supervisionado/não supervisionado | **Ciência de Dados (AED/ciclo de vida)** |
| Sex 02/10 | ML: árvores/ensemble/overfitting (fechamento) | **ML: supervisionado/não supervisionado** |
| Sáb 03/10 | Questões mistas: Estatística + ML | **ML: árvores/ensemble/overfitting (fechamento)** — consome o buffer |
| Dom 04/10 | Detecção de Anomalias | Detecção de Anomalias (inalterado) |

Custo: a sessão de "questões mistas" de fechamento do bloco desaparece (absorvida como dia de
conteúdo) — mesmo tipo de troca já aceito nos ajustes anteriores (Matemática Financeira
perdendo dias duas vezes). Ver diff proposto em `cronograma-detalhado-sessoes-sefaz-sc.md`.

## Etapa 2 — roteiro por dia

### Dom 27/09 — Estatística descritiva (medidas de posição/dispersão)
- **Leitura:** `10-Área Fiscal\50-Especialidade TI - Ciência de Dados`,
  `curso-263551-aula-04-010d-completo.pdf`: Introdução (Estatística, Probabilidade, Inferência
  — conceitos gerais) pág. 3-4; Amostragem (tipos) pág. 5,7; Moda/Mediana/Média/Variância/
  Desvio Padrão pág. 8-9.
- **Pretest:** 2-3 questões antes da leitura — Questões Comentadas pág. 28+ (Visualização e AED
  — Multibancas, as primeiras cobrem conceitos gerais de Estatística).
- **Fixação:** 3-5 questões ao final.
- **Banco de reserva:** mesma fonte, seguir na Lista de Questões se houver após pág. 32 — volta
  no dia de revisão geral da Trilha 1 (Sáb 10/10, "Questões mistas: BI + revisão geral").
- **Observações:** conteúdo condensado (só 7 pág.) — se sobrar tempo, complementar com
  Assimetria/Curtose via `10-Área Fiscal\15`, Aula 05 (não lida nesta triagem, reforço opcional).

### Seg 28/09 — Probabilidade e distribuições (dia mais denso do bloco)
- **Leitura:** `10-Área Fiscal\15-Curso Básico de Estatística`:
  - `curso-220877-aula-09-425b-completo.pdf` (Distribuições Discretas): Uniforme pág. 5-8,
    Bernoulli pág. 9-12, Binomial pág. 13-28, Geométrica pág. 29-38, Hipergeométrica pág. 39-48,
    Poisson pág. 49-67 (Teoria completa da aula, Questões Comentadas começam pág. 68).
  - `curso-220877-aula-11-17f8-completo.pdf` (Distribuições Contínuas): Uniforme pág. 5-13,
    Exponencial pág. 14-32, Normal pág. 33-51, Soma de Variáveis/Teorema Central do Limite
    pág. 52-63, Qui-Quadrado pág. 64-68, T de Student pág. 69-73, **F-Snedecor pág. 74-79**
    (confirmado — Teoria completa da aula, Questões Comentadas começam pág. 80).
- **Priorização se o tempo apertar:** Binomial, Normal e Poisson são as mais cobradas
  historicamente — se não der tempo de tudo, garantir essas três e revisar as demais
  (Geométrica, Hipergeométrica, Qui-Quadrado, T-Student, F-Snedecor) via Anki/IA depois.
- **Pretest:** 2-3 questões antes de cada distribuição, mesmo chutando — Questões Comentadas
  de cada aula (posição exata a confirmar na leitura, ficam depois da Teoria de cada aula).
- **Fixação:** 5-8 questões ao final, priorizando Binomial/Normal/Poisson.
- **Banco de reserva:** Lista de Questões de ambas as aulas — volta Sáb 10/10.
- **Observações:** dia mais pesado do bloco — se necessário, usar IA pra resumir/gerar exemplos
  extras das distribuições menos cobradas em vez de ler tudo no detalhe.

### Ter 29/09 — Inferência: amostragem, IC, testes de hipótese, correlação, regressão
- **Leitura:**
  - `10-Área Fiscal\50`, `curso-263551-aula-04-...pdf` — revisão rápida de Amostragem
    (já vista Dom 27/09, só relembrar): pág. 5,7.
  - `10-Área Fiscal\15`, `curso-220877-aula-15-5daf-completo.pdf` — Introdução a Testes de
    Hipóteses, Conceitos Fundamentais, Tipos de Erros: pág. 4-24.
- **Complemento via IA (gap 🟡):** Correlação e Regressão como técnicas de inferência
  (coeficiente de Pearson, regressão linear simples) — sem fonte dedicada confirmada nesta
  triagem. Resolver com IA/documentação no próprio dia.
- **Pretest:** 2-3 questões antes da leitura — Questões Comentadas da Aula 15 (posição a
  confirmar, ficam depois da seção lida).
- **Fixação:** 3-5 questões ao final.
- **Banco de reserva:** mesma fonte — volta Sáb 10/10.
- **Observações:** gap de correlação/regressão registrado acima — se ao ler a Aula 15 completa
  (pág. 25+) aparecerem esses tópicos mais à frente, atualizar este roteiro e o mapa-assuntos.

### Qua 30/09 — Gerais: Matemática Financeira
*(bloco diferente, já coberto pelo ajuste do bloco Governança — sem mudança aqui.)*

### Qui 01/10 — Ciência de Dados: análise exploratória, ciclo de vida, preparação/engenharia/seleção de atributos
- **Leitura:** `10-Área Fiscal\50-Especialidade TI - Ciência de Dados`:
  - `curso-263551-aula-04-010d-completo.pdf` — Análise Exploratória de Dados (inclui outliers,
    escalas de mensuração nominal/ordinal/intervalar/proporção): pág. 10-19.
  - `curso-263551-aula-02-df85-completo.pdf` — Mineração de Dados (inclui ciclo de vida
    CRISP-DM): pág. 3-27; Técnicas de Pré-Processamento (limpeza, transformação, seleção de
    atributos): pág. 28-42.
- **Pretest:** 2-3 questões antes da leitura — Aula 04 Questões Comentadas pág. 28+ (AED) e
  Aula 02 Questões Comentadas pág. 65+ (Mineração de Dados).
- **Fixação:** 3-5 questões de cada fonte ao final.
- **Banco de reserva:** Lista de Questões de ambas as aulas (Aula 02 pág. 117+) — volta
  Sáb 10/10.
- **Observações:** nenhum gap conhecido.

### Sex 02/10 — ML: aprendizado supervisionado/não supervisionado, classificação, regressão, clustering
- **Leitura:**
  - `10-Área Fiscal\50`, `curso-263551-aula-05-e3e2-completo.pdf` (Aprendizado Supervisionado):
    pág. 3-90 (introdução, regressão linear/logística, classificação, árvores de decisão, KNN —
    ler dirigido pelo pretest, é uma teoria contínua sem seções bem demarcadas).
  - `10-Área Fiscal\50`, `curso-263551-aula-06-4df9-completo.pdf` (Aprendizado Não
    Supervisionado — clustering): pág. 3-39.
- **Pretest:** 2-3 questões antes de cada fonte — Aula 05 Questões Comentadas pág. 168+ (usar
  as que citam classificação/regressão/KNN) e Aula 06 Questões Comentadas pág. 40+.
- **Fixação:** 5-8 questões ao final — dia denso, mistura muitos algoritmos.
- **Banco de reserva:** Lista de Questões de ambas — volta Sáb 10/10.
- **Observações:** a Aula 05 não separa os subtemas por seção clara (conceitos aparecem
  misturados por algoritmo) — se o pretest mostrar lacuna específica, buscar o termo direto no
  índice (`python indice/buscar_indice.py`) dentro dessa aula pra achar a página exata.

### Sáb 03/10 — ML: árvores de decisão, ensemble, algoritmos por distância, overfitting/underfitting, métricas, scikit-learn (fechamento)
- **Leitura:** `10-Área Fiscal\50`, `curso-263551-aula-05-e3e2-completo.pdf`, continuação:
  pág. 91-167 (Random Forest/ensemble, distância euclidiana aprofundada, overfitting/
  underfitting aprofundado, métricas — matriz de confusão/acurácia/precisão —, scikit-learn).
- **Pretest:** 2-3 questões — Aula 05 Questões Comentadas pág. 168+ (usar as que citam
  ensemble/overfitting/métricas/sklearn, complementando o dia anterior).
- **Fixação:** 5-8 questões ao final — fecha o bloco, reforçar bem.
- **Banco de reserva:** Lista de Questões pág. 178+ (Cesgranrio) e pág. 188+ (FGV) — revisão
  geral posterior no Sáb 10/10 (fechamento da Trilha 1).
- **Observações:** este dia consome o que era o buffer de "questões mistas" do bloco — sem
  sessão de revisão dedicada só pra Estatística+ML antes do fechamento geral da Trilha 1
  (Sáb 10/10). Se o tempo permitir, revisar Anki do bloco inteiro ao final do dia.

## Impacto no cronograma master

**Reorganização interna da Semana 5** (Estatística Descritiva volta a ser separada de
Probabilidade; todo o resto da semana empurra 1 dia; o buffer de "questões mistas" de Sáb 03/10
vira dia de conteúdo). Matemática Financeira (Qua 30/09) e tudo de Semana 6 em diante
(BI/IA/GenAI) não mudam de data. Ver diff proposto em `cronograma-detalhado-sessoes-sefaz-sc.md`.
