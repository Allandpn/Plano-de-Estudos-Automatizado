# Proposta: catálogo de aulas, modos completo e compacto, apostila própria

**Versão** 0.2.0 · **Data** 2026-10-19 · **Natureza:** proposta em discussão com o usuário. Não é decisão
fechada nem especificação. Nada aqui vira código antes de aprovado; o que tocar o SGE nasce lá, pelo
documento (`01_DOMINIO.md`, ADR), na regra deles.

## 1. Por que

A auditoria da cadeia do material (SGE `docs/AUDITORIA-CADEIA-MATERIAL.md`, com a errata de 2026-10-18) e
os ensaios no Pi mostraram que o material sai incompleto porque a cadeia **parte do assunto e procura
páginas**: o nome do assunto vira uma busca, a busca acha o que as palavras do nome acham, e a IA recorta.
Medições que sustentam a mudança:

- o acervo tem quase tudo o que faltou (no máximo 4 de 33 conceitos não existem nele);
- o mesmo conteúdo aparece em vários cursos (pontos de função: 178, 172, 171 e 169 páginas em quatro
  cursos — a mesma aula reaproveitada);
- a melhor fonte de um tema está espalhada (Ciência de Dados: `Área Fiscal\22 - Curso Completo de TI`,
  `Área Fiscal\50 - Especialidade TI - Ciência de Dados`, `TSE\02 - Banco de Dados`,
  `Curso Regular\03 - Business Intelligence`); não existe "a pasta do cargo" (`04 - SEFAZ-SC` é do Auditor
  Fiscal, não do Auditor de Finanças Públicas – Ciências da Computação).

## 2. Decisões já tomadas pelo usuário (2026-10-18 e 2026-10-19)

1. **Melhor pecar por excesso do que por falta.** O material pago é extenso para acertar todas as
   questões; a preparação é longa e há tempo para cobrir tudo. A aula que é do tema entra inteira.
2. **Triagem por apostila (aula), não por pasta.** Cursos reaproveitam aulas em vários editais sem
   recortar; o sistema faz essa triagem.
3. **Dois modos por assunto: completo e compacto.** Completo = as aulas que ensinam o assunto, inteiras.
   Compacto = recorte do completo que cabe numa **janela de capacidade parametrizável**.
4. **O aluno escolhe o modo de cada assunto ao mapear o edital** (e pode mudar depois).
5. **Catálogo de aulas por IA, uma vez para o acervo**, mas **só depois de as regras estarem definidas e
   testadas** em tipos diferentes de curso, sabendo como as apostilas são estruturadas e se é preciso ler
   o conteúdo (passo 0, §4).
6. **O sistema aponta o que o acervo não cobre**, e o aluno pode **incluir a própria apostila** (feita por
   ele com IA e outras fontes, em PDF), que é indexada e passa a servir para este e para os próximos
   editais.

## 3. Desenho proposto

### 3.1 Catálogo de aulas (uma vez para o acervo; incremental depois)

Para cada PDF do acervo, uma ficha:

| Campo | De onde vem |
|---|---|
| curso, aula, páginas | índice |
| temas que a aula ensina (lista curta, com a faixa de páginas de cada um quando a aula tem mais de um) | IA, a partir do título, sumário/marcadores e, se o passo 0 mostrar necessário, do começo das seções |
| seções: teoria, questões comentadas, lista, gabarito, resumo (faixas) | regra, se o passo 0 mostrar que os títulos de seção são padronizados; senão, IA |
| banca das questões (contagem por banca) | regra (contagem no texto) |
| gêmeas: outras cópias da mesma aula em outros cursos | regra (miolo igual, já implementado em `acervo.py`) |

Catálogo incremental: aula nova ou alterada (o `indexador.py` já sabe quais) ganha ficha; o resto não é
refeito.

### 3.2 Mapeamento de um edital

1. Cada assunto (com o **texto integral do item do edital**, não só o nome curto — pendente no SGE) é
   casado com as fichas cujos temas o ensinam, de qualquer curso.
2. Entre gêmeas, fica **uma** versão: a com mais questões comentadas da banca do concurso; empate, a mais
   recente.
3. Aula quase toda do assunto → inteira. Aula com um pedaço do assunto → a faixa daquele tema (da ficha).
4. Aula do curso escolhido que trata de algo que o edital não pede → **não entra** (é a triagem por
   apostila do item 2 das decisões).
5. Parte do assunto sem nenhuma aula → **lacuna por parte**, com motivo (hoje o SGE só registra lacuna
   do assunto inteiro; ver §3.5).

### 3.3 Modo completo

Os segmentos de ~60 min das aulas/faixas do §3.2, na ordem pedagógica (a ordem das aulas no curso), com
teoria, questões comentadas, lista e resumo.

### 3.4 Modo compacto

Recorte **de dentro do completo, mais o material de revisão do mesmo tema** (nunca traz teoria que o
completo não tem), que cabe na janela:

- **Janela parametrizável**: um percentual do completo, ou as horas disponíveis até a prova distribuídas
  por peso — o parâmetro escolhe a regra.
- **Toda parte do assunto tem pelo menos um trecho no compacto** (nenhuma parte zera).
- **Prioridade dentro da janela**: (1) resumo da aula; (2) teoria dos subtemas de maior incidência — a
  tabela de incidência da própria apostila (Passo, Bizu) quando existir, senão a contagem de questões
  comentadas da banca; (3) questões comentadas da banca; (4) o resto da teoria.
- **Passo Estratégico e Bizu** do tema não entram no completo (o completo são as aulas) e entram no
  compacto como material de revisão, pela mesma régua: foram feitos para a reta final (decisão do
  usuário, 2026-10-19, opção "b").
- Cada segmento diz de onde veio (aula/faixa), para o aluno saber o que está relendo.

### 3.5 No SGE (proposta a levar para lá — documento primeiro, decisão deles com o usuário)

- Segmento com **modo** (COMPLETO, COMPACTO); assunto com o **modo escolhido**, definido no mapeamento do
  edital e alterável depois; o plano do turno e "Abrir material" seguem o modo. Escada e fase não mudam.
- Parâmetro da **janela do compacto**.
- **Lacuna por parte do assunto** e a tela "o que o acervo não cobre".
- **Apostila própria**: envio de PDF pelo aluno, que vai para o acervo (pasta própria, p.ex.
  `99 - Minhas apostilas`), é indexado e catalogado, e entra no mapeamento dos editais.
- **Texto integral do item do edital** guardado em cada assunto (a análise por IA hoje resume e perde
  conteúdo).

### 3.6 Apostila própria (retroalimentação)

1. O SGE lista as lacunas (por parte do assunto) do concurso-alvo.
2. O aluno produz o material (IA e outras fontes) e envia o PDF, dizendo para qual assunto/parte é.
3. O worker indexa só esse arquivo (o `indexador.py` é incremental; um PDF cabe no Pi), gera a ficha do
   catálogo e refaz o material das partes que ele cobre.
4. A apostila fica no acervo: o próximo edital que cobrar o mesmo tema já a encontra.

Risco: material feito com IA pode ter erro. A ficha marca a origem ("apostila do aluno") e o segmento
mostra isso; o aluno decide se confia.

## 4. Passo 0 — medir a estrutura das apostilas, sem IA

`integracao/estrutura_apostilas.py` lê só o índice e, para uma amostra de cursos de tipos diferentes
(curso regular, pós-edital, especialidade, passo estratégico, bizu, lei), mostra por aula: marcadores do PDF,
abertura, sumário, onde começam as seções típicas, banca das questões e páginas sem texto.

As respostas que o passo 0 tem de dar antes de escrever as regras do catálogo:

1. O título + sumário/marcadores bastam para saber os temas da aula, ou é preciso ler o começo das seções?
2. Os títulos de seção (questões comentadas, lista, gabarito, resumo) são padronizados a ponto de uma regra
   achá-los? Em que tipo de curso não são?
3. Que fração das aulas trata de mais de um tema (e precisa de faixa por tema)?
4. A contagem de banca nas questões é confiável para escolher entre gêmeas?

Depois do passo 0: um ensaio do catálogo com IA em ~30 aulas de cursos diferentes, conferido pelo aluno,
antes de rodar no acervo inteiro (~90 chamadas).

### 4.1 O que o passo 0 mostrou (amostra de 12 cursos; texto cru de 4 aulas)

Nenhuma aula tem marcadores. O sumário fica na p. 2 (e na p. 3, nas aulas longas), em quatro formatos:

| Formato | Exemplo | Entrada | Página |
|---|---|---|---|
| A: regular e pós-edital | `00 - Curso Regular\09 - Redes de Computadores\aula 06.pdf` | `N) Tema - Tipo [- Banca]` + pontilhada + página grudada (`Cesgranrio17`) | posição no PDF |
| B: aulas mais antigas | `04 - SEFAZ-SC\09 - Legislação Tributária de Santa Catarina - Parte 01` | `SUMÁRIO PÁGINA` / `N. Título 02` | impressa, +1 |
| C: Passo Estratégico | `39 - Passo Estratégico Básico de Português`, aula 06 | `Título ..... N`, sem número de entrada | impressa, +1; **a numeração recomeça** no questionário anexado (Perguntas 3 → p. 36, +33) |
| D: Bizu | `SEFAZ-CE 2026\22 - Bizu Estratégico`, aula 11 | sem sumário com página; tabela "assunto → bizus 1 a 4 → link do caderno" | o assunto abre a página, seguido do primeiro bizu da faixa (`5. Classificações…` na p. 9) |

- Formato A: tirados os pontos, a página fica grudada na última palavra ("Teoria4", "Cesgranrio17") e é a
  posição no PDF (9 de 9 conferidas em `00 - Curso Regular\09 - Redes de Computadores\aula 06.pdf`). A
  banca vem escrita "Cebraspe", "Cesgranrio", "FCC", "FGV"; no corpo, "CESPE".
- Formatos B e C: página impressa, deslocamento +1; o C pode ter mais de uma sequência de numeração.
- Títulos de seção no corpo saem mutilados (letra inicial grande numa linha, o resto na seguinte:
  "Q C – NAT E PAT - CESGRANRIO / UESTÕES OMENTADAS"); a conferência usa pedaços das palavras sem a
  primeira letra.
- O Passo e o Bizu trazem tabela de incidência por subassunto, com banca e período ("Tipologia textual
  45,5%… FGV, FCC e Cebraspe, 2023 a 2026"; "Despesa Pública 13,20%… banca FCC").
- Páginas de imagem com OCR ilegível existem (Bizu de Direito Financeiro, SEFAZ-CE: 8 de 47 ilegíveis,
  outras com OCR falho mas legível; uma com texto invertido) e não aparecem como "vazias".
- A "lei" da amostra (`04 - SEFAZ-SC\09 - Legislação Tributária de Santa Catarina - Parte 01`) é aula
  comum (formato B: teoria comentada, bateria de questões, lista, gabarito), não lei seca. O número da aula
  sai do conteúdo ("AULA 14" no arquivo `aula-00`).

Regras:

- **R1 (formato A):** se a linha crua tinha pontilhada, os dígitos do fim são a página, com ou sem espaço;
  a banca é o que sobra depois do tipo, sem o número.
- **R2 (formatos B e C):** `N. Título NN` e `Título ..... NN`. Página do sumário que diminui começa uma
  nova sequência, com deslocamento medido à parte. Um sumário A seguido de um detalhado (B, C) são duas
  listas da mesma aula, conferidas e fechadas à parte.
- **R3 (formato D):** lê a tabela "assunto → faixa de bizus" e acha no corpo a página que começa com o
  primeiro número da faixa (`N.`).
- **R4 (conferir no corpo):** o deslocamento de cada aula (ou sequência) é o que mais se repete entre as
  entradas. A página é "confirmada" quando traz o tema como linha própria, ou as três primeiras linhas
  trazem o tema ou os pedaços das palavras do tema sem a primeira letra (`ROTOCOLO`, `ABARITO`).
  No formato A, o texto do tipo também confirma ("L Q / ISTA DE UESTÕES"). Entrada sem página no
  sumário é procurada no corpo, em ordem, só como título (linha própria ou começo de linha).
- **R5 (fim da seção):** a página antes da próxima entrada; o que não está no sumário (gabarito,
  referências) fica dentro da seção em que cai.
- **R6 (tipos):** `Bateria de Questões` e `Questões estratégicas` → questões comentadas; `Roteiro de
  Revisão` e `Aposta Estratégica` → resumo; novo `incidencia` ("O que é mais cobrado", "Análise
  estatística"); novo `questionario` ("Perguntas e respostas"); `bibliografia`. Entrada sem tipo herda o
  da anterior nos formatos B e C (a primeira é teoria); no A, é título de teoria.
- **R7 (incidência):** linhas `Subassunto NN,N%`, com a banca e o período citados na mesma página.
- **R8 (banca da aula):** a do sumário; senão a da incidência; senão a contagem no texto (CESPE =
  Cebraspe).
- **R9 (página ilegível):** marcada quando a maior parte das palavras é longa e colada ou cheia de
  símbolos.
- **R10 (número da aula):** do conteúdo ("AULA 14"); o nome do arquivo só na falta.

Respostas às perguntas do §4: (1) o título e o sumário dão o tema nos formatos A–C; no B o nome da lei só
aparece na abertura (p. 3) → o catálogo lê o sumário e a abertura; (2) sim, nos formatos A–D, com a
conferência por pedaços; (3) sai da próxima rodada — aulas com mais de um tema no sumário (Redes aula 06
tem 7); (4) a banca vem do sumário no A; a contagem no texto fica como reserva. O compacto sai por regra
na estrutura (seções, faixas e incidência do Passo e do Bizu); casar os subtemas deles com os assuntos do
edital continua sendo trabalho do catálogo, igual aos cursos regulares.

## 5. Riscos conhecidos

- O casamento assunto ↔ aula ainda depende do texto do assunto; nome resumido pelo edital por IA continua
  perdendo conteúdo até o texto integral existir no SGE.
- Volume: o completo de TI pode passar de 700 h de leitura a 4 min/página; calibrar minutos por página pelo
  ritmo real registrado no SGE e mostrar material × horas até a prova.
- Qualidade do compacto só se mede com a régua da prova (uma prova do mesmo cargo).
- Buracos prováveis medidos no acervo: web scraping (4 páginas no melhor curso), pandas/NumPy (33), DAX (19),
  Conhecimentos Regionais de SC e LC 741/2019 (sem material).

## Histórico

| Versão | Data | Mudança |
|---|---|---|
| 0.1.0 | 2026-10-19 | Primeira versão, a partir da conversa com o usuário e dos ensaios no Pi |
| 0.2.0 | 2026-10-19 | Resultado do passo 0: formatos de sumário, regras R1–R10, incidência, OCR ilegível; compacto = recorte do completo + Passo/Bizu do tema (opção "b") |
