# Passagem de sessão — revisão da cadeia do material (2026-10-18 e 19)

**Para quem é:** a próxima sessão do Claude, rodando **no Pi** (`claude remote-control` em
`/opt/Plano-de-Estudos-Automatizado`), que continua exatamente do ponto em que a sessão em nuvem parou.
**Leia inteiro antes de agir.** Depois leia `CLAUDE.md` deste repositório e
`docs/proposta-catalogo-aulas-e-modos.md`.

**Modo de trabalho pedido pelo usuário:** esta etapa é de **especificação** e é a mais importante do
projeto agora. Qualidade antes de velocidade. Nenhuma chamada de IA (cota) antes de as regras estarem
escritas e testadas sem IA. Discutir com o usuário antes de decidir; ele está decidindo o desenho junto.

---

## 1. O que disparou tudo

O usuário subiu um edital, o sistema montou o material sozinho (worker da Sprint 19 do SGE), e ele
testou com uma prova + gabarito (Sprint 24): **6 respondíveis, 5 parciais, 28 não respondíveis de 39
avaliáveis**. Ele quer revisar o sistema inteiro para ter o melhor conteúdo de estudo possível.

Documentos do lado do SGE (repositório `Allandpn/SGE-Concursos`, `main`):
- `docs/RELATORIO-SEGUNDA-OPINIAO.md` — apresentação do sistema e da cadeia para uma segunda IA;
- `docs/AUDITORIA-CADEIA-MATERIAL.md` 1.0.1 — causa de cada questão;
- **Errata (commit `685ef3f`):** o concurso-alvo é o **SEFAZ SC 2026, Auditor Estadual de Finanças
  Públicas – Ciências da Computação (FCC)**; a prova do ensaio (prova id 2) é do **TJ-CE, Analista
  Judiciário – Infraestrutura de TI**. A prova não é régua justa; ~12 das 33 falhas são contra o que o
  edital-alvo nomeia.

## 2. Diagnóstico consolidado (o que sabemos com medição)

1. **O acervo tem quase tudo.** Ausência real só em ~4 conceitos (PgBouncer, Dynamic ARP Inspection,
   NTP Kiss-o'-Death, MOBIKE). Nenhuma perda por OCR (1,8% das páginas vazias).
2. **A análise do edital por IA resume demais o conteúdo programático.** O prompt
   (`edital/PromptsEdital.java` do SGE) pede "nome curto, até 250 caracteres". Exemplo medido com o
   Anexo III do SEFAZ SC: o item de infraestrutura diz "servidores, sistemas operacionais,
   virtualização, armazenamento, contêineres, alta disponibilidade e balanceamento de carga; OSI e
   TCP/IP, IPv4 e IPv6, TCP, UDP, DNS, DHCP, HTTP/HTTPS, LAN, WAN, WLAN, VLAN, NAT, VPN, roteamento e
   switching" e o assunto 91 ficou "Infraestrutura e redes: servidores, virtualização, contêineres,
   modelos OSI e TCP/IP, protocolos, VLAN, NAT, VPN". O mesmo em Nuvem (perdeu nuvem
   pública/privada/híbrida, backup…), Segurança (perdeu backup e continuidade, hashes, hardening…),
   Bancos de Dados (perdeu concorrência, particionamento, os SGBDs nomeados). **O que não está no nome
   do assunto, a busca nunca procura.**
3. **A busca antiga** (nome inteiro do assunto → ~12 termos em OU, 6 arquivos × 12 páginas, recorte de
   curso por radical do nome da pasta) casava 24% do acervo e deixava partes inteiras de fora.
4. **Diagnóstico sem IA da prova 2** (`integracao/diagnostico_prova.py`, rodado no Pi): a maior parte
   das falhas é **CADEIA** (o acervo tem, nos cursos certos — `SEFAZ-CE 2026\28 - Redes e Segurança`,
   `TSE\06 - Redes e Segurança`, `58 - Especialidade TI - Redes` — e o material não trouxe). Onde o termo
   aparecia no segmento, era menção de passagem (alternativa de questão, link, capa): o julgador acertou.
5. **Palavras de categoria** ("Morfossintaxe", "Flexão nominal e flexão verbal", "protocolos") quase não
   aparecem literalmente nas apostilas, que usam "termos da oração", "classes de palavras" etc.
6. **Aulas repetidas entre cursos são a regra:** a mesma aula do mesmo professor está em TSE, TCE-SC,
   SEFAZ-CE e Curso Regular (pontos de função: 178/172/171/169 páginas em quatro cursos).
7. **Não existe "pasta do cargo":** `04 - SEFAZ-SC` é do Auditor **Fiscal** (Tributário, Contabilidade…),
   sem TI. TI do alvo está em `SEFAZ-CE 2026` (Banco de Dados, Desenvolvimento, Redes e Segurança, SO, IA,
   Governança/Contratações de TIC, Engenharia de Software, Inglês Técnico) e `TCE-SC 2026 - Pos Edital`.
8. **Ciência de Dados está espalhada:** `Área Fiscal\22 - Curso Completo de TI` (fonte principal),
   `Área Fiscal\50 - Especialidade TI - Ciência de Dados`, `TSE\02 - Banco de Dados` (Power BI),
   `Curso Regular\03 - Business Intelligence`. Prováveis buracos: web scraping (4 páginas no melhor
   curso), pandas/NumPy (33), DAX (19); e já confirmados: Conhecimentos Regionais de SC, LC 741/2019.

## 3. O que foi feito nesta branch (`claude/relaxed-bell-02ejxe`, a partir de `main` `35f7fe2`)

| Commit | O quê |
|---|---|
| `e8d544e` | `acervo.candidatos_por_partes`: uma busca por parte do assunto (E entre os termos da parte, OU se o E não acha; título antes dos dois-pontos fora), cursos afins e acervo inteiro na mesma rodada, orçamento proporcional (6 a 12 arquivos), mapa por região. Worker com uma rodada só; partes sem página vão para `TRABALHO_DIR/lacunas-parciais.jsonl`. `--ensaiar` com `--busca antiga\|nova` e `--sem-ia`. `diagnostico_prova.py` + `integracao/diagnostico/conceitos-prova-2.json` |
| `1050578` | Plural do edital casa o singular (`radical_de_busca`); julgamento ignora a capa de rastreabilidade do segmento; diagnóstico trata sinônimos como grupo |
| `660cbfe` | **Aula inteira como unidade** (`"inteira": true` → páginas 1-N); "na dúvida, inclua"; abertura da aula (p. 1-2) no pedido à IA; aula gêmea entre cursos entra uma vez |
| `02d3860` | Toda parte leva pelo menos um candidato (seleção "cobertura primeiro"); gêmeas detectadas pelo miolo (p. 3-14); IA mais tolerante (aula inteira sem faixa; lacuna de parte coberta descartada) |
| `29ae66b` | `docs/proposta-catalogo-aulas-e-modos.md` 0.1.0; `integracao/estrutura_apostilas.py` (passo 0, sem IA) |
| `42e0c17`, `9ea2afd` | `estrutura_apostilas.py` lê o sumário (tema, tipo, banca, página), confere a página no PDF, marca arquivo que não é aula; `--bruto TRECHO` mostra o texto cru de uma aula |

Testes: `python -m unittest discover -s integracao -p "test_*.py"` (194 verdes) e
`python -m unittest dias/test_montar_bloco.py`. **Nada disto foi mesclado em `main`**, e **nenhum
"Refazer o material" foi feito no SGE**: o material no SGE ainda é o da busca antiga.

Ensaio da busca nova com IA (assunto 91, Infraestrutura e redes): de 5 segmentos/~256 min para
13 segmentos/~512 min, cobrindo virtualização (Hyper-V, Failover Cluster, hypervisor), Docker e
Kubernetes, VLAN com questões FCC, NAT, VPN. Depois da mudança para aula inteira, as duas rodadas
seguintes falharam na validação por formato da resposta da IA — corrigido em `02d3860`, **ainda não
reensaiado**.

## 4. Decisões do usuário (não reabrir sem ele)

1. **Melhor pecar por excesso do que por falta.** O material da Estratégia é extenso para acertar todas
   as questões; a preparação é longa (provas a partir de 24 meses); não estrangular o que foi pago.
2. **Triagem por apostila (aula), não por pasta.** Cursos reaproveitam aulas sem recortar para o edital;
   o sistema faz essa triagem. Aula de curso que trata de algo que o edital não pede não entra.
3. **Dois modos por assunto: completo e compacto.** Completo = as aulas que ensinam o assunto, inteiras.
   Compacto = recorte **de dentro do completo** numa **janela de capacidade parametrizável** (percentual
   do completo ou horas até a prova), na linha do que o sistema fazia antes, mas com toda parte do
   assunto tendo pelo menos um trecho.
4. **O aluno escolhe o modo de cada assunto ao mapear o edital** (e pode mudar depois).
5. **Catálogo de aulas por IA, uma vez para o acervo (~90 chamadas)** — **só depois** de as regras
   estarem bem definidas e testadas em tipos diferentes de curso, sabendo como as apostilas são
   estruturadas e se é preciso ler o conteúdo.
6. **O sistema identifica o que as apostilas não cobrem** e o aluno pode **incluir a própria apostila**
   (feita por ele com IA e outras fontes, em PDF), que é indexada e serve para este e para os próximos
   editais (retroalimentação).

## 5. Onde paramos: passo 0, estrutura das apostilas

Duas rodadas de `estrutura_apostilas.py` no Pi (amostra de 3 aulas de 12 cursos):

- **Nenhuma aula tem marcadores (bookmarks)** no índice.
- **Cursos regulares e pós-edital** (Curso Regular, Curso Completo de TI, SEFAZ-CE, TCE-SC, TSE) têm na
  p. 2 um "Índice" de formato fixo **`N) Tema - Tipo [- Banca] ...... página`**, que a extração devolve
  com os pontos da linha pontilhada intercalados nas letras (`.N..A...T.. .e.. .P..A...T..` = `NAT e
  PAT`). Decodificado (tirando os pontos): **85–100% das entradas com tipo** (teoria, resumo, mapa
  mental, questões comentadas, lista de questões, apresentação, flashcards).
- **Banca saiu 0%** e **quase nenhuma entrada trouxe o número da página** → deslocamento não
  conferível. Hipóteses: o número cai em outra linha ou some junto com a pontilhada; a banca pode vir
  com outra caixa ("Cebraspe") ou como "Multibancas" (`9ea2afd` já trata caixa e guarda o rótulo cru).
- **Os títulos de seção no corpo saem mutilados:** "QUESTÕES COMENTADAS" vira "Q C - UESTÕES OMENTADAS"
  (letra inicial grande separada). Ideia para achar as seções sem depender do número do sumário:
  percorrer as páginas na ordem do sumário procurando o tema, e casar o tipo por pedaços das palavras
  sem a primeira letra ("UESTOES", "OMENTADAS", "ISTA", "EORIA", "ESUMO", "ABARITO").
- **Passo Estratégico (Português e TI), Bizu Estratégico e lei seca (Legislação Tributária de SC) não
  têm sumário nesse formato.** São as fontes candidatas do **compacto**. Precisa de outra regra ou de IA
  lendo o começo das páginas.
- Estatística Descritiva e Curso Básico de Português: sumário parcial (47–60% com tipo) — outros nomes
  de seção.
- Arquivos que não são aula (aviso de 3 páginas, orientação de estudos de 4) → regra "curto e sem
  sumário fica fora" já implementada.

**Próximo passo imediato (os arquivos já foram gerados no Pi, a sessão em nuvem não chegou a lê-los):**

```bash
cat ~/bruto-regular.md   # 09 - Redes de Computadores/aula 06
cat ~/bruto-passo.md     # 39 - Passo Estratégico Básico de Português/aula 06
cat ~/bruto-bizu.md      # SEFAZ-CE 2026/22 - Bizu Estratégico/aula 11
cat ~/bruto-lei.md       # 04 - SEFAZ-SC/09 - Legislação Tributária de SC
```

Com eles, responder e **escrever na proposta** (`docs/proposta-catalogo-aulas-e-modos.md`, mostrando o
diff ao usuário antes de gravar, regra do `CLAUDE.md`):

1. Onde fica o número da página na entrada do sumário; a página do sumário é a posição no PDF?
2. Como a banca aparece no sumário.
3. Regra para achar o começo de cada seção no corpo (pela ordem do sumário + tema + pedaços do tipo).
4. Que estrutura (se alguma) Passo Estratégico, Bizu e lei seca têm; se o compacto pode sair por regra
   ou precisa de IA lendo o começo das páginas.
5. Ajustar `estrutura_apostilas.py` e rodar de novo (sem cota) até a tabela-resumo mostrar tipo e
   página confiáveis nos cursos regulares.

Depois do passo 0: **ensaio do catálogo com IA em ~30 aulas de cursos diferentes, conferido pelo
usuário**, e só então o acervo inteiro.

## 6. Pendências e propostas em aberto (ainda sem decisão)

No **SGE** (repositório deles; especificação primeiro — `01_DOMINIO.md`, ADR, documento da sprint — e
decisão com o usuário antes de código):
- **Texto integral do item do edital** guardado em cada assunto (a correção de maior efeito, item 2 do
  §2). Proposta "B".
- Segmento com **modo** (COMPLETO/COMPACTO); assunto com o **modo escolhido**; parâmetro da **janela**.
- **Lacuna por parte do assunto** (hoje só do assunto inteiro, D-65) e a tela "o que o acervo não cobre".
- **Apostila própria**: envio de PDF, pasta própria no acervo (ex.: `99 - Minhas apostilas`), indexação
  incremental no Pi, catálogo, e marca de origem "apostila do aluno" no segmento.
- **Calibrar minutos por página** pelo ritmo real registrado (hoje 4 min fixos) e mostrar material ×
  horas até a prova. O completo de TI sozinho passa de ~770 h a 4 min/página.
- Compacto também no **reestudo** depois de FALHA e na reta final (Sprint 21) — ideia.
- Aulas do curso que o edital não pede: decisão do usuário é **não incluir** (triagem por apostila).

No **planejamento**:
- Expansão de termos por IA para palavras de categoria (proposta "A") — perde importância se o catálogo
  por aula vier; reavaliar depois do passo 0.
- O filtro de "curso afim" por radical do nome da pasta atrapalha em TI ("Ciências da Computação" casa
  "Arquitetura de Computadores", nunca "Redes e Segurança"); com o catálogo, ele deixa de existir.
- Régua: o ensaio válido precisa de uma prova **do mesmo cargo** (FCC, Auditor/Analista de TI voltado a
  dados), não a do TJ-CE.

## 7. Ambiente no Pi (descoberto nesta sessão)

- SGE: `/opt/estudos` (projeto compose `estudos`: serviços `app`, `postgres`, `planejamento`).
- Planejamento: `/opt/Plano-de-Estudos-Automatizado` (`PLANEJAMENTO_DIR` no `.env` do SGE aponta para
  ele); a branch `claude/relaxed-bell-02ejxe` está em checkout lá.
- O `git fetch` falhou uma vez com "insufficient permission ... .git/objects" (objetos gravados por root);
  foi resolvido com `sudo git -C ...`. Sugerido ao usuário: `sudo chown -R allan:allan
  /opt/Plano-de-Estudos-Automatizado`.
- Reconstruir o worker depois de mudar código: `cd /opt/estudos && docker compose build planejamento &&
  docker compose up -d planejamento`.
- Rodar scripts no contêiner: `docker compose exec -T planejamento python integracao/<script>.py ...`
  (o contêiner tem `INDICE_DB`, `ACERVO_DIR`, `MATERIAL_DIR`, `SGE_URL`). O índice: 2.639 PDFs, 264.013
  páginas, 160 cursos.
- O Pi é de 4 GB e compartilhado (há outros projetos compose: `deploy`, `imagineer`). Não pare nem mexa
  em serviços que não são do `estudos`.
- Concurso-alvo no SGE: id 1 (SEFAZ SC 2026), 97 assuntos; prova do ensaio: id 2.

## 8. Regras que continuam valendo

- Desenvolver e empurrar só na branch `claude/relaxed-bell-02ejxe` (nos dois repositórios); sem pull
  request sem pedido explícito.
- Neste repositório: nunca sobrescrever `docs/*.md` sem mostrar o diff antes; gap real é documentado,
  nunca preenchido com conteúdo inventado.
- No SGE: especificação é a fonte da verdade; documento primeiro, depois código; cada IA escreve no
  próprio repositório salvo exceção registrada pelo usuário.
- Mensagens de commit terminam com as linhas de atribuição que a sessão indicar.
- Nenhuma chamada de IA (cota da assinatura do usuário) para o catálogo antes das regras testadas.
