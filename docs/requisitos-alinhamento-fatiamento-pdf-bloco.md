# Requisitos de Alinhamento: Fatiamento de PDF por Bloco, não por Dia

Documento pra levar ao repositório do planejamento (`Plano-de-Estudos-Automatizado`,
uso com a IA de lá), sobre um atrito identificado entre os dois sistemas. Espelha
o padrão que `docs/requisitos-sge-integracao.md` **de lá** já usa: mesma integração,
escrita do lado de quem está pedindo a mudança.

Este documento **não é sobre o payload de import de `Edital`/`Assunto`**
(isso já está coberto pelo par de documentos existente,
`docs/requisitos-sge-integracao.md` / `docs/arquitetura-integracao-planejamento-sge.md`).
É sobre uma camada anterior: **como o material de estudo (PDF) é fatiado antes de
chegar ao candidato.**

---

## 1. O atrito

O planejamento monta hoje, por concurso, PDFs consolidados **por dia**
(`dias/manifesto_AAAA-MM-DD.json`, `dias/montar_dia.py`): cada PDF tem o tamanho
que cabe na janela de estudo daquele dia, calculado a partir do prazo até a prova.

Isso funcionou bem para este concurso específico (SEFAZ SC, prova em novembro,
prazo curto) — mas **contradiz um princípio que a própria arquitetura de
integração já registra**:

> `docs/arquitetura-integracao-planejamento-sge.md §6`:
> *"O planejamento nunca decide 'quando' estudar dia a dia — só a ordem de
> entrada dos assuntos e o orçamento de tempo agregado por assunto. O dia a dia
> real (o que muda com SUCESSO/PARCIAL/FALHA) é território exclusivo da escada
> do SGE."*

Fatiar por **dia de calendário** é decidir "quando" — exatamente o que essa
regra já reserva para o SGE. O problema não aparece com prazo curto porque, na
prática, o ritmo calculado à mão coincidiu com o que o SGE pediria de qualquer
forma. Ele aparia no próximo concurso, com prazo mais longo: o PDF do "dia N" e
o que a escada do SGE realmente pede naquele dia deixam de coincidir, porque
nenhum dos dois sistemas sabe do plano do outro.

## 2. Como o SGE decide "quando" e "quanto por dia" hoje

Pra desenhar a fatia certa, o planejamento precisa saber o que já existe do
lado de cá — não precisa reimplementar nada disso, só **não competir com isso**:

| Mecanismo | O que faz | Onde |
|---|---|---|
| **Bloco de conteúdo** | Unidade de leitura/teoria: 45–75 min. Recuperação é outra unidade, ~8 min | `01_DOMINIO.md §7.1`, D-26 |
| **Duração do bloco é parâmetro**, não constante fixa — o sistema mede a duração real ao longo do tempo | O "45–75 min" é ponto de partida, ajustável, nunca hardcoded | D-29 |
| **Plano de turno** | Quantos blocos cabem hoje é derivado da janela do turno (1h30 em dia de semana → 1 bloco; 3h no fim de semana → 2 blocos) | `01_DOMINIO.md §7.3`, D-27 |
| **Frente de estudo** | Teto global e por disciplina limitam quantos assuntos estão "abertos" ao mesmo tempo — isso já governa o ritmo entre assuntos concorrentes | D-19, D-20, D-23 (nível-alvo por peso) |
| **Escada por resultado** | `SUCESSO` avança, `PARCIAL` repete, `FALHA` regride **e volta pra fila de estudo** — o número de vezes que um assunto é revisitado não é previsível de antemão | D-07 |
| **O sistema nunca exibe o material** | O candidato estuda no tablet, registra no computador; abrir o PDF é decisão do candidato, sempre | `02_JORNADAS.md §1.1` |

A consequência prática: **quantos blocos por dia, e em qual assunto, já é
100% calculado pelo SGE, dinamicamente, considerando desempenho real.** Um
segundo sistema tentando prever isso de antemão (por dia de calendário) vai
divergir assim que o desempenho real do candidato não bater com a suposição.

## 3. A proposta: fatiar por bloco de assunto, não por dia

Trocar a unidade de fatiamento do PDF de **dia** para **bloco de conteúdo
dentro do assunto**:

- Cada assunto (já com `volume_estimado`, que a arquitetura de integração já
  calcula — `docs/arquitetura-integracao-planejamento-sge.md §5`) é dividido em
  **N segmentos de ~45–75 min de leitura cada**, na ordem em que aparece no
  material de origem.
- O PDF de cada segmento é gerado exatamente como hoje (consolidado, com
  mapeamento de página rastreável) — só muda o **critério de corte**: page
  count/tempo de leitura por bloco, não "o que cabe no dia X".
- **Nenhum segmento é datado.** O planejamento entrega uma sequência ordenada de
  segmentos por assunto; o SGE decide, turno a turno, qual segmento é "o próximo"
  daquele assunto — do mesmo jeito que já decide qual assunto entra no bloco de
  conteúdo de hoje.
- Prazo curto deixa de ser "PDF menor por dia" e passa a ser "mais blocos por
  dia" (o candidato consome 2–3 segmentos num turno de 3h, se a escada permitir);
  prazo longo é "menos blocos por dia, mais dias" — sem o planejamento saber
  nem precisar saber qual dos dois é o caso.

## 4. O que muda no contrato de dados

`docs/arquitetura-integracao-planejamento-sge.md §5/§8` já previa
`referência_material` (apostila + página) como campo opcional, estático, que
"o SGE só armazena e exibe, não interpreta nem decide a partir dele". Isso
continua valendo — só passa a apontar pra uma sequência, não pra um ponto
único:

| Campo (por assunto) | Antes | Proposto |
|---|---|---|
| `referência_material` | Um valor (apostila + página) | Lista ordenada de segmentos: `(ordem, arquivo/identificador, página inicial, página final, tempo estimado de leitura)` |

**Continua sendo ponteiro, nunca conteúdo nem link que o SGE precise abrir** —
coerente com `02_JORNADAS.md §1.1`. O SGE só grava "candidato está no segmento 2
de 5 do assunto X" como parte do registro de uma sessão `ESTUDO`; quem abre o
PDF é o candidato, no tablet, como já acontece hoje.

## 5. Topologia: como os artefatos chegam ao SGE (substitui a premissa do §3 de vocês)

Ponto novo, fora da discussão de fatiamento, mas que nasce da mesma conversa:
`arquitetura-integracao-planejamento-sge.md §3` supõe contato direto
PC→Pi via Tailscale no momento da exportação (estágio 5). Isso presume os
dois sistemas online ao mesmo tempo — mas **o planejamento roda só sob
demanda** (quando surge um edital novo, num PC pessoal), enquanto o **SGE é
24/7** no Raspberry Pi. São ritmos de disponibilidade diferentes, e exigir
coincidência entre eles é fricção desnecessária.

**Decisão já tomada do lado do SGE** (`docs/00A_ADR.md`, ADR-037): os
artefatos chegam via **Google Drive**, sem chamada de rede direta entre os
dois sistemas:

- O **CSV** (assuntos + segmentos de material) é sincronizado pro Pi por
  `rclone` (mesma ferramenta já usada pro backup do SGE) — o planejamento só
  precisa **subir o arquivo numa pasta do Drive**, sem saber que o Pi existe
  ou está acessível.
- Os **PDFs dos blocos não precisam ir pro Pi**. Ficam no Drive; o candidato
  abre o link direto de lá, em qualquer aparelho. Por isso, cada PDF de bloco
  precisa ser **compartilhado com link** (não só "arquivo na pasta") — é esse
  link que entra na coluna `referência_material` do CSV, não um caminho local.

**Proposta de estrutura de pasta** (pra confirmar/ajustar com vocês):

```
SGE-Importacao/
  <slug-do-concurso>/
    assuntos.csv              ← ou o CSV de segmentos de material, formato do §4
    blocos/
      <assunto-slug>/
        segmento-01.pdf         ← compartilhado com link, o link vai no CSV
        segmento-02.pdf
        ...
```

O SGE só sincroniza (`rclone`) a raiz de `assuntos.csv`/CSVs — nunca a pasta
`blocos/`, que existe só pra vocês organizarem os PDFs antes de gerar os
links.

## 6. O que **não** muda

A divisão de responsabilidades de `docs/arquitetura-integracao-planejamento-sge.md §2`
continua igual — esta proposta não move nenhuma linha daquela tabela:

- Planejamento continua sem decidir "quando" — só passa a fatiar por unidade
  de leitura em vez de por data.
- SGE continua sendo o único lado que decide dia a dia, com base em desempenho
  real (escada, frente, teto).

## 7. Questões — respondidas pelo planejamento em 2026-09-04

Pra cada uma, três alternativas foram avaliadas do lado de cá; a coluna
"proposta" é a que o SGE recomendou. **As quatro vieram confirmadas sem
contestação**, registradas em `docs/requisitos-alinhamento-fatiamento-pdf-bloco.md`
e `docs/arquitetura-integracao-planejamento-sge.md §3/§6/§8` do lado do
planejamento.

### 7.1 Origem do tamanho do bloco — e separação de dois parâmetros diferentes

Revisão de 2026-09-04: a pergunta original misturava dois números que têm
donos diferentes. Separando:

**(a) Duração de um bloco.** 45–75 min é o ponto de partida do SGE, mas é
**parâmetro ajustável** (D-29 — "o sistema mede a duração real ao longo do
tempo"), não constante fixa.

| Alternativa | Risco |
|---|---|
| Valor fixo, hardcoded nos dois lados | Desalinha em silêncio se o SGE recalibrar o parâmetro e o planejamento não souber |
| Planejamento consulta o SGE em tempo real antes de fatiar | Quebra a autocontenção que `arquitetura-integracao-planejamento-sge.md §3` já promete do lado de vocês — fatiar é análise, não exportação |
| **Proposta: valor único fixo (sugestão: 60 min), documentado nos dois lados** — sem chamada em tempo real; quando o SGE recalibrar (evento raro, registrado em changelog), o número espelha manualmente do outro lado | Baixo — muda em meses, não em dias |

**Confirmado: 60 min fixo, documentado nos dois lados.**

**(b) Quantos blocos por dia.** Isso é diferente de (a) e **não precisa
cruzar pra o SGE em nenhuma hipótese** — é usado só internamente pelo
planejamento, no estágio 4 do pipeline (`arquitetura-integracao-planejamento-sge.md §4`,
"orçamento de tempo/ordem"), pra responder **"com N blocos por dia, o volume
todo cabe até a data da prova?"** e decidir se sugere compressão/corte. Não
determina quantos blocos o candidato vai fazer de fato em cada dia — isso
continua 100% dinâmico, decidido pelo SGE dia a dia (turno + escada). Se o
ritmo real divergir do estimado no planejamento, nada quebra dos dois lados:
o candidato só termina o núcleo mais rápido ou mais devagar do que a
estimativa inicial previu, exatamente como já acontece hoje sem essa
integração.

Sugestão pra vocês, se ainda não é assim: perguntar ao usuário, na hora de
cadastrar o edital, "quantos blocos de estudo por dia, em média" (um número
só, não por dia da semana) — é a mesma simplificação que o SGE já faz internamente
no dimensionamento de `01_DOMINIO §7.3`.

**Confirmado: uso interno do orçamento, nunca exportado.** Implementado como
`calcular_orcamento.py --blocos-por-dia N`, alternativa a `--minutos-dia`.

### 7.2 Manifestos de dia já gerados (concurso atual, SEFAZ SC)

| Alternativa | Risco |
|---|---|
| Reprocessar agora, migrando pro novo formato | Risco desnecessário perto da prova de novembro, sem ganho real pro candidato |
| **Proposta: deixar como estão** — só assunto/concurso novo usa o fatiamento por bloco | Nenhum — dois formatos coexistem por um tempo, sem conflito |

**Confirmado: manifestos do SEFAZ SC ficam intocados.**

### 7.3 Reteach em `FALHA` (D-07: assunto regride e volta pra fila de estudo)

| Alternativa | Risco |
|---|---|
| SGE pede ao planejamento um "segmento de reforço" direcionado à causa do erro | Reabre o atrito original — planejamento decidindo "o que estudar" reativamente a um evento do SGE; exige comunicação em tempo real |
| **Proposta: planejamento não é avisado** — SGE só registra uma sessão `ESTUDO` nova no mesmo assunto; o candidato reabre, por conta própria, o(s) PDF(s) que já tem salvos (reforçado pelo próprio registro de `Erro`, com causa e confiança, que já orienta o candidato) | Nenhum |

**Confirmado: planejamento não é avisado.**

### 7.4 Estrutura de pastas/arquivo no Google Drive (§5)

| Alternativa | Risco |
|---|---|
| Cada PDF de bloco vira um link avulso, sem convenção de pasta | Funciona, mas espalha os artefatos sem rastro — difícil auditar "o que já foi exportado pra qual concurso" |
| **Proposta: convenção de pasta do §5** (`SGE-Importacao/<concurso>/assuntos.csv` + `blocos/<assunto>/segmento-NN.pdf`, cada PDF compartilhado com link) | Baixo — é só convenção de nomenclatura, ajustável sem impacto em código de nenhum dos dois lados |

**Confirmado.** `montar_bloco.py` já gera `blocos/<assunto-slug>/segmento-NN.pdf`
localmente. **Ressalva do planejamento:** o upload pro Drive e a geração do
link compartilhável de cada PDF ainda são passos **manuais** — o campo
`arquivo` fica com o caminho local até alguém trocar pelo link antes de
exportar. **Sem impacto no SGE**: `referência_material` já era desenhado
como ponteiro opaco (`§4`) — não importa se o link foi colocado ali manual
ou automaticamente. Não é gargalo deste lado; automatizar o lado deles é
opcional, prioridade só se virar toil real pra eles.

## 8. Requisito novo (2026-09-06): identificador estável por segmento

Ponto que nasceu já na escrita do documento técnico do lado do SGE
(`docs/SPRINT-10-SEGMENTO.md`), depois das quatro questões de §7 já terem
sido confirmadas — o SGE é quem fecha a especificação primeiro (decisão do
usuário), então este pedido vira requisito do lado de vocês, não sugestão.

**O problema:** o CSV de segmentos (§4) hoje identifica cada linha por
`chaveExternaAssunto` + `ordem`. `ordem` é **posição**, não identidade. Se
vocês reordenarem o material de um assunto depois de já exportado — por
exemplo, inserir um segmento novo entre o que hoje é "02" e "03", empurrando
os seguintes —, o SGE não teria como distinguir "o segmento 3 de antes" do
"segmento 3 de agora": um candidato que já tinha estudado o antigo teria seu
registro histórico silenciosamente associado ao conteúdo novo que passou a
ocupar aquela posição.

**O que muda do lado de vocês:** o CSV de segmentos ganha uma coluna nova,
**`chaveExternaSegmento`** — um identificador **por segmento** (não por
assunto), gerado e mantido por vocês, estável entre reexportações do mesmo
pedaço de material. Mesma natureza que `chaveExterna` já tem do lado do
assunto (§4 original) — o SGE guarda, nunca interpreta.

Hoje `montar_bloco.py` nomeia arquivos só por posição
(`segmento-NN.pdf`, §7.4) — não existe, no pipeline de vocês, um conceito de
identidade de segmento independente da posição no arquivo. Pra gerar essa
chave, algo como um UUID mintado na primeira vez que um segmento é criado, e
persistido num manifesto local (mesmo padrão que `dias/manifesto_AAAA-MM-DD.json`
já usa do lado de vocês) resolveria — a chave nasce junto com o segmento e
viaja com ele nas reexportações seguintes, mesmo que a posição mude.

**Sem isso**, a reimportação do lado do SGE continua funcionando para o caso
comum (corrigir o link de um PDF resubido, mesma posição) — só fica exposta
ao risco de reordenação descrito acima. Registrado como requisito, não
bloqueio: se reordenar segmentos já importados não é algo que aconteça na
prática, o risco pode ficar documentado e aceito em vez de resolvido agora.

## 9. Decisão (2026-09-06): o planejamento é a fonte da verdade do escopo do concurso

Revisão do que era um requisito especulativo em versão anterior deste documento: ficou
decidido, do lado do planejamento, que **todo o escopo do concurso** — nome, data da
prova, disciplinas, assuntos e segmentos — é responsabilidade do planejamento entregar,
nunca digitado manualmente no SGE. Isso fecha a lacuna apontada abaixo.

**O problema que motivou a decisão:** o SGE identifica um concurso só pelo **slug da
pasta** em `SGE-Importacao/<slug>/` (ADR-037) — não existia, em `assuntos.csv` nem em
nenhum outro arquivo do contrato, um nome de exibição (ex.: "SEFAZ SC") nem a data da
prova. E o SGE **nunca cria** concurso, só importa o que o planejamento já preparou —
então esses dois dados têm que vir de aqui.

**Motivo prático:** um indicador de "progresso vs. data da prova" (sem virar tela de
calendário, `00_PRODUTO.md §8.5`) depende de uma data que hoje não existe em lugar
nenhum do contrato. O percentual de cobertura do edital já é calculável só com o que o
SGE tem hoje (backlog/frente/consolidado); os dias restantes até a prova, não.

**Formato decidido:** um manifesto pequeno por concurso, `SGE-Importacao/<slug>/concurso.json`,
na mesma pasta do Drive do CSV de assuntos — não colunas extras no CSV existente, pra não
repetir o mesmo dado em toda linha. Campos: `slug`, `nome`, `data_prova`. Mesmo princípio de
`chave_externa_segmento`/`chaveExterna` (§8): o SGE guarda o valor, nunca decide nada a
partir dele.

**Disciplinas não ganham manifesto/entidade própria** — continuam sendo só o atributo
`disciplina` de cada assunto (já exportado no CSV hoje). A lista de disciplinas do
concurso é derivável agrupando os assuntos por esse campo; não há necessidade de uma
estrutura nova só pra isso.

Ver `docs/arquitetura-integracao-planejamento-sge.md` §5/§8 pro modelo de dados e formato
de exportação atualizados com essa decisão.

## 10. Rastreabilidade

Regras do SGE citadas: `01_DOMINIO.md` D-07, D-19, D-20, D-23, D-26, D-27,
D-29, D-50, D-51, D-53 (§8); `02_JORNADAS.md §1.1`, `§7.3`;
`00_PRODUTO.md §8.5` (sem tela de calendário, §9). Decisão de
infraestrutura: `docs/00A_ADR.md` ADR-037 (artefatos via Google Drive +
`rclone`).
