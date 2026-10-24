# Proposta: o material do plano vem do casamento parte ↔ ficha, não de busca por palavras

**Versão** 0.4.0 · **Data** 2026-10-24 (0.4.0: §8, o que a implementação e a prática mostraram) · **Data original** 2026-10-23 · **Natureza:** proposta discutida e decidida com o usuário nos pontos D1 a D7 (§3). O
que toca o SGE nasce lá, pelo documento e pela regra deles; esta proposta é o pedido e o desenho de origem.

**Escopo (decisão do usuário, 2026-10-23): o sistema está sendo construído do zero.** Não há compatibilidade com concursos
criados pela análise antiga do SGE e nenhum remendo de transição. Quando a cadeia nova estiver pronta, os editais são subidos
por ela e estudados a partir daí. O caminho antigo do worker (busca por palavras + triagem por IA) deixa de ser o fluxo e
sobra só como segunda chance de uma parte sem candidato (D4).

## 1. Por que

Hoje o worker (`integracao/worker.py`) prepara o material assunto por assunto: separa o assunto em "partes" por vírgula e
ponto e vírgula, busca as palavras de cada parte no índice (FTS) e pede a uma IA que escolha aulas inteiras ou faixas de
páginas (`triagem_ia.py`). Três problemas, medidos:

1. **A busca por palavras perde material que existe** (auditoria de 2026-10-17: 8 de 12 "lacunas" do SEFAZ SC tinham
   apostila) e **traz material que não ensina** (60% dos candidatos por nó eram outro assunto; por palavras é pior).
2. **A IA recebe aulas inteiras** "com teoria, questões comentadas, lista e resumo" (prompt atual), o que contradiz a
   decisão 7 (questões fora da apostila de teoria).
3. **As partes são cortes de vírgula**, não assuntos de estudo ("Windows Server 2019 e 2022" vira duas partes soltas).

Já temos as peças para trocar isso: partes revisadas do edital (`partes_edital.py`, 65/66 certas), ficha de cada aula com
as páginas de cada tema, sem questões (`catalogo_aulas.py`), ligação de partes e fichas pelos nós do QConcursos
(`mapear_partes.py`, `ligar_fichas.py`, `casar_partes_fichas.py`) e a confirmação por IA entre os candidatos
(`confirmar_material.py`: 92% de acordo, medido às cegas com outra IA em 60 partes).

## 2. Fluxo proposto

```
edital revisado (partes com chave)  ─┐
fichas ligadas aos nós               ├─▶ casamento (regra) ─▶ candidatos por parte ─▶ confirmação (IA, uma vez por edital)
árvore do QConcursos                ─┘                                                   │
                                                                                          ▼
         decisões do usuário (trocar material/nó) ───────────────────▶  seleção por política (REGRA, sem IA)
                                                                                          │
                                           manifesto por assunto ◀── páginas dos temas + fixação da aula
                                                                                          │
                                      montar_bloco.py (validação estrita, cortes de ~60 min) ─▶ segmentos ─▶ SGE
```

A IA entra **uma vez por edital**, na confirmação. A escolha final de páginas e o fatiamento são regra e validador (os
mesmos de hoje), então reprocessar não muda o material por acaso.

## 3. Decisões a discutir

**D1. Unidade do plano.** O SGE trabalha por *assunto*. Proposta: o assunto do SGE é o assunto do edital revisado
(texto exato), e o material dele é a união do material das suas partes, na ordem do edital, cada fonte marcada com as
partes que cobre. A `chave` do assunto entra no contrato (hoje só a parte tem).

**D2. Quanto material por parte (decidido pelo usuário).** Dois modos: **completo como padrão** e **compacto como opção** por
concurso nos Ajustes do SGE. Medido em ALESC e SEFAZ-SP TIC, mediana por assunto, a 4 min/página:

| Política | ALESC | SEFAZ-SP |
|---|---:|---:|
| **Completo:** tudo que ensina ou ensina em parte, de todos os cursos | 4,3 h | 5,9 h |
| Só o que ensina (todos os cursos) | 2,1 h | 2,4 h |
| **Compacto:** uma fonte por parte (a mais curta que ensina; "parcial" só se nada ensina) | 1,1 h | 2,2 h |

Em ambos a mesma aula não entra duas vezes e a cobertura de cada parte é provada no manifesto. No completo, a ordem vai do
que mais ensina ao que ensina em parte, e cada fonte mostra o seu tempo estimado, para o aluno decidir o que ler.

**D3. Fixação e questões (decidido pelo usuário).** Resumo e roteiro de revisão da aula entram como `fixacao` logo depois da
teoria. **Questões comentadas, lista de exercícios e gabaritos não entram nos segmentos**, mas também **não se perdem**:
são agrupadas por assunto e ficam numa consulta à parte, "Questões deste assunto" (ou nome parecido), aberta quando o
aluno quiser. Como o SGE trata todo segmento como leitura obrigatória antes da escada (D-xx do §12 do canal), as questões
**não podem ser segmentos**: são um material de consulta, pedido ao SGE como conceito novo. O planejamento gera, por
assunto, um PDF com as faixas de questões e gabarito das aulas escolhidas, e o SGE o oferece na tela do assunto. A ligação
com o QConcursos pelo nó do assunto (questões novas) continua sendo o caminho de resolução.

**D4. Parte sem candidato que sirva.** Uma segunda chance, uma vez: a triagem antiga (busca por palavras + IA) só para
essas partes, porque o catálogo pode não ter ficha de um assunto que a apostila trata de passagem. Se ainda assim nada
serve, vira lacuna (registro por parte, como `lacunas-parciais.jsonl`, e lacuna do assunto quando nenhuma parte tem
material).

**D5. O usuário troca o material.** Na tela de revisão (especificação 0.2.0), além do nó, o usuário pode trocar a fonte de
uma parte (escolher outro candidato ou excluir). É decisão como as outras: presa à `chave`, vale em reprocessamento.

**D6. Material já criado.** O SGE nunca apaga segmento. Quando a revisão muda o material de um assunto que já tem
segmentos: os novos entram como **sugestão** e o usuário aceita; os antigos ficam.

**D7 (decidido pelo usuário): sem limite de leitura.** Assunto não tem teto de horas; tem **tempo estimado**, mostrado por
fonte e por assunto. Em preparação de alto nível, restringir o assunto por tempo seria arriscar a questão do aluno.

## 4. Mudanças

| Onde | O quê |
|---|---|
| `integracao/` (feito) | `selecao_material.py` e `manifesto_do_casamento.py` (política D2, manifesto por assunto), `pdf_questoes.py` (PDF de questões por assunto, D3) e `preparar_edital.py` (pipeline único) |
| `worker.py` | `preparar` passa a usar o casamento; a busca por palavras sobra só como segunda chance (D4) |
| `entrega_revisao.py` / contrato | `chave` do assunto; material por parte (fontes, páginas, veredito) como saída opcional do planejamento |
| SGE | o que já está pedido (tela de revisão, decisões) e **um conceito novo**: material de consulta "Questões deste assunto", fora da escada (D3) |
| `Dockerfile` | módulos novos na imagem |

## 5. Etapas de implementação

1. **Seleção por política**, pura regra, com testes (entrada: partes confirmadas; saída: fontes por assunto). Sem IA.
2. **Manifesto** por assunto e validação com `montar_bloco --validar` em ALESC e SEFAZ-SP TIC: provar que passam sem erro.
3. **Ensaio no Pi** com um assunto real, comparando o resultado com o que a triagem antiga produz para o mesmo assunto.
4. **Worker**: caminho novo + segunda chance + lacunas; testes.
5. **Contrato**: chave do assunto e material por parte; atualizar a especificação.
6. Ligar ao laço do worker quando o SGE tiver as operações do contrato; então subir os editais pela cadeia nova.

Situação em 2026-10-24: **1, 2, 3 e 5 feitos** (o ensaio do passo 3 foi o MPPR inteiro, §8) e a **segunda chance D4 feita** como
etapa `segunda` do pipeline (`segunda_chance.py`); do passo 4 falta só o worker chamar o pipeline, e o passo 6 aguarda o SGE
adotar o contrato.

## 6. Riscos

- A confirmação por IA varia entre modelos: por isso a escolha final é regra, e a decisão do usuário prevalece.
- Cobertura do acervo: 14% a 19% dos assuntos não têm nenhum material; é lacuna real, não defeito do método. A tela de
  revisão mostra desde o início.
- O SGE precisa adotar o contrato (especificação 0.2.0 §11) para os assuntos serem os do edital revisado; até lá o fluxo novo
  não tem onde ligar, e isso é esperado num sistema novo.

## 7. Dados da ficha usados

Cada tema da ficha tem as páginas da teoria (sem questões, decisão 7). As seções da aula (`secoes`) trazem, por tema, as
faixas de `resumo` e `mapa_mental` (fixação) e de `questoes_comentadas`, `lista_questoes`, `questionario` e `gabarito`
(questões deste assunto). Ficam de fora `incidencia`, `apresentacao` e `bibliografia`.

## 8. O que a implementação e a prática mostraram (2026-10-24)

**Pipeline único.** `integracao/preparar_edital.py` encadeia `extrair → quebrar → ligar → casar → confirmar → manifestos →
consulta → entrega`, cada etapa gravando um arquivo; rodar de novo pula o que já existe, `--refazer ETAPA` refaz aquela e as
seguintes, `--ate` para antes, `--esperar` dorme até o limite de uso da IA liberar. É o que o worker vai chamar.

**Resultado de ponta a ponta, MPPR cargo 402:** 138 assuntos, 300 partes (5 sem nó); material completo em 101 assuntos,
parcial em 16, nenhum em 21; 0 manifestos recusados pelo fatiador; mediana de 4,9 h por assunto (modo completo); 77 assuntos
com PDF de "Questões deste assunto" (5.522 páginas). Os assuntos sem material são lacunas reais: o QConcursos não tem Docker,
Kubernetes, contêineres, CI/CD, IaC nem Direito Empresarial.

**Achados que mudaram o desenho:**

1. **Disciplina genérica.** "Conhecimentos específicos" (MPPR) não casava com nenhuma disciplina do QConcursos. O mapeamento
   de disciplinas passou a receber uma descrição com o **cargo** e uma amostra dos assuntos; sem isso, 39 partes ficavam sem
   nó. Parte sem nó volta a uma segunda passada ao retomar.
2. **Página além do PDF.** 31 temas (28 fichas) do catálogo apontam páginas que o PDF não tem (leitura errada do catálogo).
   Não se adivinha o recorte: o tema não é usado e vira **aviso** no relatório. Refazer a leitura dessas fichas é pendência.
3. **Seção sem posição.** Seção da ficha sem início ou fim não gera página (fixação e questões a ignoram).
4. **A quebra varia entre rodadas.** O mesmo edital deu 199 e 138 assuntos em duas rodadas, com o mesmo total de partes: a IA
   agrupa de outro jeito. É um motivo a mais para a revisão e as decisões presas à `chave` (especificação, §1).
5. **Parte de uma palavra só.** Reserva por nome exige 8 letras ou sigla em maiúsculas; "valor" casava com "P-Valor".
6. **Questões à parte.** O PDF "Questões deste assunto" é gerado pelo planejamento e entregue em `material.consulta`; o SGE
   precisa do conceito novo (canal, §18 de `requisitos-planejamento-blocos-de-conteudo.md`).

**Confirmação por IA:** 84% de veredito igual e 92% de acordo em "serve ou não", às cegas, com outra IA (60 partes).

**Segunda chance (D4) medida no MPPR.** Nos 37 assuntos que o casamento deixou parciais ou sem material, a busca por palavras +
IA, só nas partes sem cobertura, achou material novo em 24 (e em 9 dos 18 que sobraram na segunda volta). Resultado final:
**completos 101 → 127, parciais 16 → 7, sem material 21 → 4**, 0 recusados pelo fatiador. A IA só leva teoria (sem questões e
sem aula inteira), nenhuma página que o casamento já usa entra de novo, e cada fonte nova sai marcada `"origem":
"segunda_chance"` e no fim da lista, para a tela de revisão mostrar que veio da busca e não do catálogo (decisão D5/D6: o
usuário confere e troca). O que sobrou sem material é lacuna real (por exemplo projeto de banco de dados teórico e modelagem
semântica no MPPR).

**Leitura das fichas com página fora do PDF.** Reler as 28 fichas pela IA (2026-10-24) reproduziu o defeito nos mesmos 28 PDFs
(30 temas): são aulas sem sumário em que a IA devolve numeração que o PDF não tem. Não compensa mais cota; ficam como aviso, e
são quase todas de contabilidade, direito civil e tributário (cinco de TI). Se um edital precisar delas, corrige-se pela tela
(trocar a fonte) ou por regra de página, não por nova leitura.
