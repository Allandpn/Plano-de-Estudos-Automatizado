# Triagem do Bloco: Programação e Automação para Dados (Trilha 1)
### SEFAZ SC 2026 — resultado da triagem de PDFs, complementa mapa-assuntos-edital-sefaz-sc.md e cronograma-detalhado-sessoes-sefaz-sc.md
*Gerado em 12/09/2026, com o índice completo (2639 PDFs).*

Todos os caminhos abaixo são relativos a `apostilas/`.

## Acervo identificado

Quatro fontes cruzadas, nenhuma sozinha cobre o bloco inteiro:

1. **`10-Área Fiscal\22-Curso Completo de Tecnologia da Informação`, Aula 21** (prof. Diego
   Carvalho e Renato da Costa, `curso-247678-aula-21-...pdf`, 147 pág.) — **fonte principal**
   de Lógica de Programação e Python básico. Estrutura própria dessa aula: Teoria intercalada
   com Mapa Mental (imagem) e Questões Comentadas — **não tem "Resumo" condensado separado**
   como as aulas de BD/SQL tinham; a leitura precisa passar pela Teoria completa.
2. **`10-Área Fiscal\22-Curso Completo de Tecnologia da Informação`, Aula 22** (prof. Diego
   Carvalho e Raphael Lacerda, `curso-247678-aula-22-...pdf`, 114 pág., título "Bibliotecas de
   Python") — cobre Pandas e NumPy com bom detalhe (a aula segue até Matplotlib/Scikit-
   learn/TensorFlow, que são do bloco de ML — não ler aqui, fica pra lá). Mesmo padrão de Teoria
   com Questões Comentadas intercaladas por biblioteca, sem Resumo separado.
3. **`06-TRT-SC\05-Desenvolvimento de Software`, Aula 05** (profs. Paolla Ramos e Raphael
   Lacerda, `aula 05.pdf`, 194 pág.) — **achado novo, fora da família "22-Curso Completo"
   usada nos blocos anteriores**. Primeira metade (pág. 3-75) é um curso de Python mais
   completo que a Aula 21 (inclui RegEx, Lambda, Iteradores, Escopo, Módulos, Datas,
   Matemática — nenhum desses está na Aula 21). A partir da pág. 91 tem uma seção
   **"Automação de Scripts"** dedicada, cobrindo exatamente PyAutoGUI, Selenium Python,
   Splinter, **Scrapy** (web scraping) e **Tagui** (biblioteca de RPA em Python) — os dois
   assuntos mais difíceis de achar no acervo (Consumo de APIs/web scraping e Automação de
   rotinas/RPA).
4. **`07-TSE Unificado\02-Banco de Dados`, Aula 15** (profs. Felipe Mathias e Emannuelle
   Gouveia, `aula 15.pdf`) — dentro de uma seção "IA na Robótica" (fora de escopo deste bloco
   na maior parte), tem uma definição sólida e uma questão real de banca sobre **RPA**
   (pág. 55-58 e 98, incluindo uma questão FGV/SEFAZ AM/2022 — mesma banca do nosso edital
   em outro estado).

## Decisão da Etapa 0 — descartes

- **Aula 21 (Área Fiscal 22):** pág. 78-93 é Mapa Mental em imagem (sem texto extraível) — não
  é leitura, só revisão visual rápida opcional. O "Desafio" da pág. 78 (programar a letra de
  uma música dos Beatles) é um exercício de fixação avulso, não teoria — pular, é opcional.
- **Aula 22 (Área Fiscal 22):** pág. 62-114 (Matplotlib, Scikit-learn, TensorFlow) pertence ao
  bloco Estatística/Ciência de Dados/ML, ainda não triado — não ler aqui.
- **Aula 05 (TRT-SC):** pág. 98-194 é o banco de "Questões Comentadas" de todo o Python básico
  (mesmo conteúdo já coberto na Aula 21) — usar só como banco de reserva adicional, não como
  leitura principal. Seções fora deste bloco: nenhuma outra identificada (o resto do arquivo é
  só Python + automação, ambos deste bloco).
- **Aula 15 (TSE Unificado, Banco de Dados):** o restante da aula (IA/ML/PLN em geral) pertence
  ao bloco Estatística/Ciência de Dados/ML e ao bloco IA/PLN/GenAI, ainda não triados — só a
  seção de RPA (pág. 55-58, 98) é deste bloco.

## Gap confirmado

Nenhum ❌ — os 6 assuntos finos têm alguma cobertura real. Dois ficam 🟡 (parcial):

| Assunto (mapa-assuntos) | Status | Observação |
|---|---|---|
| Lógica de programação, algoritmos, estruturas de dados, funções, exceções | ✅ | Completo |
| Python 3.14.x — sintaxe | ✅ | Completo (versão 3.14 não citada literalmente no texto, mesmo padrão de observação já usado no bloco SQL para versões de SGBD) |
| NumPy 2.5.x, pandas 3.0.x | ✅ | Completo (idem, número de versão não citado literalmente) |
| CSV, JSON, XML — manipulação/transformação/integração | 🟡 | CSV e XML bem cobertos (Pandas `read_csv`/`to_csv`, bibliotecas `xml.etree.ElementTree`/`lxml`/`BeautifulSoup`); **JSON como formato de dado em Python (`json.loads`/`json.dumps`) não tem teoria dedicada no acervo** — só aparece como formato citado ao lado de CSV/XML em contexto de API/dados estruturados. Resolver com um complemento rápido via IA/documentação oficial no próprio dia — não é ausência de acervo pro assunto todo, só desse sub-ponto |
| Consumo de APIs, web scraping | 🟡 | Conceito de API REST (HTTP GET/POST/PUT/DELETE, formatos JSON/XML/CSV) bem coberto na Aula 21; **web scraping tem teoria real via Scrapy** (Aula 05, TRT-SC); **falta a biblioteca `requests` (consumo prático de API em Python)** — não encontrada em nenhuma fonte do acervo. Mesmo tratamento: complemento rápido via IA/documentação oficial no dia, sem precisar abrir mais PDFs |
| Automação de rotinas, RPA | ✅ | Completo — Tagui (RPA em Python) + PyAutoGUI + Selenium/Splinter (Aula 05, TRT-SC) + conceito de RPA com questão real de banca SEFAZ (Aula 15, TSE Unificado) |

## Etapa 1 — cronograma

**Correção: 2 dias → 3 dias**, mesmo padrão já visto nos blocos SQL (2→3) e Governança
(1→2). Motivo: a Aula 21 e a Aula 22 não têm Resumo condensado separado da Teoria (diferente
das aulas de BD/SQL) — a leitura precisa passar pela Teoria completa, que soma um volume alto:

| Fonte | Conteúdo | Páginas |
|---|---|---|
| Aula 21 — Lógica de Programação | Conceitos, representações de algoritmo, pseudocódigo, fluxograma | 4-13 |
| Aula 21 — Python básico | Conceitos, operadores, funções, exceções, tipos/variáveis, estruturas de dados, controle de fluxo, arquivos, f-string, OOP | 14-77 |
| Aula 22 — Pandas | Conceitos, Series, DataFrame, leitura/escrita CSV/Excel/XML | 6-34 |
| Aula 22 — NumPy | Conceitos e operações | 36-61 |
| Aula 05 (TRT-SC) — RegEx | Complementa a Aula 21 (que não cobre RegEx) | 68-75 |
| Aula 05 (TRT-SC) — Automação de Scripts | PyAutoGUI, Selenium, Splinter, Scrapy, OpenPyXL/XlsxWriter, Tagui (RPA) | 91-96 |
| Aula 15 (TSE) — RPA conceitual | IA na robótica, tipos de robôs, definição RPA, RPA×IA | 55-58, 98 |
| **Total teoria** | | **~140 pág.** |

140 páginas de Teoria densa (a maior parte com trechos de código, mais rápida de ler que prosa
pura, mas ainda assim mais que o dobro do volume que já exigiu +1 dia no bloco Governança) não
cabem em 2 dias de semana (~2h15 cada) com pretest+fixação+Anki. **Correção: o bloco passa de
2 para 3 dias.**

Absorção no cronograma (contida na própria Semana 4, sem empurrar Semana 5 em diante — mesmo
princípio já usado nos ajustes anteriores): a sessão de Sex 25/09, que era só "Estatística:
descritiva", passa a ser o 3º dia de Python; **Estatística descritiva é fundida com
Probabilidade e distribuições no Dom 27/09** (mesmo recurso de "misturar dois blocos num dia"
já usado na Fase 3, Dom 01/11, pra fechar orçamento sem empurrar prazo). Estatística/CD/ML da
Semana 5 em diante não mudam de data. Ver diff proposto em `cronograma-detalhado-sessoes-sefaz-sc.md`.

## Etapa 2 — roteiro por dia

### Qua 23/09 — Python (dia 1 de 3): Lógica de Programação + sintaxe básica
- **Leitura:** `10-Área Fiscal\22`, `curso-247678-aula-21-prof-diego-carvalho-e-renato-da-costa-.pdf`:
  - Lógica de Programação — Conceitos Básicos, Representações de Algoritmo (Linguagem
    Natural/Máquina/Programação), Pseudocódigo, Fluxograma: pág. 4-13
  - Python — Conceitos Básicos, Tipos de Operadores: pág. 14-20
  - Python — Funções (inclui exceções `try/except`): pág. 21-27
  - Python — Tipos e Variáveis, Identificadores, Tipos de Dados: pág. 28-34
- **Pretest:** 2-3 questões antes da leitura, mesmo chutando — Questões Comentadas da própria
  Aula 21, pág. 94+ (procurar as que citam `print()`, tipos/variáveis — vêm intercaladas, não
  em bloco separado por subtópico).
- **Fixação:** 3-5 questões ao final, mesma fonte.
- **Banco de reserva:** `06-TRT-SC\05-Desenvolvimento de Software`, `aula 05.pdf`, Questões
  Comentadas pág. 98+ (mesmo conteúdo de Python básico, banca cruzada) — volta Sáb 26/09.
- **Observações:** nenhum gap conhecido para este dia.

### Qui 24/09 — Python (dia 2 de 3): Estruturas de dados avançadas, OOP, NumPy, pandas
- **Leitura:**
  - `10-Área Fiscal\22`, `curso-247678-aula-21-...pdf` — Estruturas de Dados (listas, tuplas,
    dicionários, conjuntos): pág. 35-47
  - Mesma aula — Controle de Fluxo (If-Elif-Else, While, For): pág. 48-58
  - Mesma aula — Arquivos, f-string, Orientação a Objetos (Classes, Herança, Polimorfismo,
    Objetos Iteráveis): pág. 59-77
  - `10-Área Fiscal\22`, `curso-247678-aula-22-prof-diego-carvalho-e-raphael-lacerda-.pdf` —
    Pandas (conceitos, Series, DataFrame, seleção/filtragem com máscaras): pág. 6-30
  - Mesma aula — NumPy: pág. 36-61
- **Pretest:** 2-3 questões antes de cada bloco de leitura, mesmo chutando — Aula 21 pág. 94+
  (parte de estruturas/OOP) e Aula 22 pág. 30-34/59-61 (Pandas/NumPy, questões já intercaladas
  na própria teoria).
- **Fixação:** 5-8 questões ao final — é o dia mais denso do bloco (estruturas de dados +
  OOP + duas bibliotecas novas), reforçar bem.
- **Banco de reserva:** `06-TRT-SC\05`, `aula 05.pdf`, Questões Comentadas pág. 98+
  (continuação do banco do dia 1) — volta Sáb 26/09.
- **Observações:** nenhum gap conhecido para este dia.

### Sex 25/09 — Python (dia 3 de 3, fechamento): CSV/JSON/XML, consumo de APIs, web scraping, automação/RPA
- **Leitura:**
  - `10-Área Fiscal\22`, `curso-247678-aula-22-...pdf` — leitura/escrita de arquivos CSV/Excel/XML
    com Pandas (inclui menção às bibliotecas `csv`, `openpyxl`, `xlrd`, `xml.etree.ElementTree`,
    `lxml`, `BeautifulSoup`): pág. 7, 30-34
  - `10-Área Fiscal\22`, `curso-247678-aula-21-...pdf` — conceito de API REST (métodos HTTP
    GET/POST/PUT/DELETE, formatos JSON/XML/CSV): pág. 111-141 (questões intercaladas, ler
    dirigido pelos trechos que citam "API"/"REST"/"webhook")
  - `06-TRT-SC\05`, `aula 05.pdf` — RegEx (complementa a Aula 21, que não cobre): pág. 68-75
  - Mesma aula — Automação de Scripts (PyAutoGUI, Selenium Python, Splinter, **Scrapy** —
    web scraping —, OpenPyXL/XlsxWriter/PyXLL, ReportLab/Borb, **Tagui** — RPA): pág. 91-96
  - `07-TSE Unificado\02-Banco de Dados`, `aula 15.pdf` — RPA conceitual (IA na robótica, tipos
    de robôs, definição RPA, RPA×IA): pág. 55-58
- **Complemento rápido via IA/documentação oficial (gap 🟡, ver seção acima):** biblioteca
  `json` (`json.loads`/`json.dumps`) e biblioteca `requests` (consumo prático de API) — sem
  fonte dedicada no acervo, resolver direto no dia (mesmo tratamento dado ao gap de
  CTE/window functions no bloco SQL antes de ele ser localizado — aqui é gap real e pequeno).
- **Pretest:** 2-3 questões antes da leitura — `07-TSE Unificado\02`, `aula 15.pdf`, pág. 98
  (questão FGV/SEFAZ AM/2022 sobre RPA — usar como primeira questão do dia, é de uma SEFAZ).
- **Fixação:** 5-8 questões ao final, priorizando RPA e API REST (são os dois pontos mais
  prováveis de cair, dado o padrão de bancas de área fiscal).
- **Banco de reserva:** `06-TRT-SC\05`, `aula 05.pdf`, Questões Comentadas pág. 98+ (fecha o
  banco de reserva do bloco inteiro) — volta Sáb 26/09.
- **Observações:** gap 🟡 duplo (JSON em Python, biblioteca `requests`) — registrado acima,
  resolver com IA no próprio dia, não abrir mais PDFs por causa disso.

## Impacto no cronograma master

**+1 dia** (Sex 25/09 passa a ser Python, não Estatística), absorvido fundindo Estatística
descritiva com Probabilidade e distribuições no Dom 27/09 — mesmo recurso de "um dia com dois
blocos" já usado na Fase 3 (Dom 01/11). Semana 5 em diante não muda de data. Ver diff proposto
em `cronograma-detalhado-sessoes-sefaz-sc.md`.
