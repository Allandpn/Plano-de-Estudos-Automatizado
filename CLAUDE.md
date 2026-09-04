# SEFAZ SC 2026 — Instruções do Projeto

Contexto: preparação pro concurso SEFAZ SC 2026 (Auditor Estadual de Finanças
Públicas, área Ciências da Computação), prova em 22/11/2026. Acervo de ~2600
apostilas do Estratégia Concursos indexadas em `indice/indice.db`.

Leia sempre, antes de qualquer tarefa: `docs/plano-estudos-sefaz-sc-2026.md`
(método completo), `docs/mapa-assuntos-edital-sefaz-sc.md` (lista oficial de
assuntos finos) e `docs/cronograma-detalhado-sessoes-sefaz-sc.md` (orçamento
de dias por bloco).

## Estrutura de pastas

```
docs/            → plano, cronograma, mapa-assuntos, inventário, triagens
apostilas/       → os PDFs originais (não editar/mover)
indice/          → indice.db (SQLite+FTS5) e os scripts de indexação/busca
dias/            → PDFs mesclados por dia de estudo + manifestos JSON
anki/            → rascunhos de deck (JSON) e CSVs gerados
integracao/      → canonico.db (registro canônico de assuntos) e os scripts de
                   canonicalização/orçamento/exportação pro SGE-Concursos
```

## Fluxo de leitura de um edital novo

Quando pedirem "leia o edital X" (estágio 1 de
`docs/arquitetura-integracao-planejamento-sge.md`): a única entrada é o PDF do edital, a
saída é um mapa de assuntos novo pronto pra triagem.

1. Ler o edital completo (conteúdo programático) e extrair os assuntos finos, um por
   linha, na ordem em que aparecem — mesmo formato/granularidade de
   `mapa-assuntos-edital-sefaz-sc.md` (usar esse arquivo como referência de convenção,
   inclusive o agrupamento por ponto-e-vírgula quando fizer sentido).
2. Procurar o quadro de distribuição de questões do edital (normalmente um anexo com
   número de questões por disciplina). Se existir e for granular por disciplina, esse
   número vira o `peso` (ALTO/MEDIO/BAIXO, por tercis ou corte que fizer sentido pro
   total de questões daquele edital) aplicado a todos os assuntos daquela disciplina.
   **Se o edital não granular peso por disciplina, marcar `peso` como "não determinado"
   e seguir — nunca estimar peso a partir de menções soltas em apostilas.**
3. Propor o novo `docs/mapa-assuntos-edital-<concurso>.md` **como diff, pedindo aprovação
   antes de gravar** — mesma regra de sempre pra `docs/*.md`.
4. Depois de aprovado, o assunto entra no fluxo normal de triagem (próxima seção).

## Fluxo de uma triagem de bloco

Quando pedirem "triagem do bloco X":

1. Ler os assuntos finos do bloco em `mapa-assuntos-edital-sefaz-sc.md`.
2. Pra cada assunto, buscar no índice: `python indice/buscar_indice.py "termo"`.
   - A busca usa OR entre palavras (prioriza recall) — **sempre ler o trecho
     retornado antes de considerar o assunto coberto**, não confiar só no
     fato de ter retornado resultado.
3. **Orçamento de busca por assunto** (não pular etapas, não repetir em loop):
   1. Query direta com os termos do mapa-assuntos.
   2. Se não achar (ou o trecho não bate de verdade): reformular com até 2
      sinônimos/termos relacionados (ex: "window function" → "OVER" →
      "PARTITION BY").
   3. Se ainda não achar: abrir no máximo 2 PDFs candidatos, no máximo ~20
      páginas cada, via leitura direta do arquivo.
   4. Se mesmo assim não achar: marcar ❌ no `mapa-assuntos-edital.md`,
      registrar no "Gap confirmado" da triagem, e seguir em frente — não
      repetir o ciclo pro mesmo assunto.
4. Escrever `docs/triagens/triagem-bloco-<nome>.md` no mesmo formato de
   `triagem-bloco-bd-sql-sefaz-sc.md` (acervo identificado, decisões de
   descarte, gap confirmado, roteiro por dia com leitura/pretest/fixação/
   banco de reserva/observações). **Toda citação de aula/PDF no roteiro leva
   o caminho da pasta (relativo a `apostilas/`) escrito por extenso ao lado**
   (ex: `00-Curso Regular\02, aula 07.pdf`) — mesmo repetindo o caminho
   várias vezes ao longo do documento. Nada de código/legenda que exija
   voltar ao topo do arquivo pra decodificar — o objetivo é achar o PDF no
   Explorer sem sair do trecho que está lendo.
5. Propor as edições em `mapa-assuntos-edital.md` e `cronograma-detalhado.md`
   **como diff, pedindo aprovação antes de gravar** — esses dois arquivos são
   a espinha dorsal do plano de 11 semanas, erro silencioso ali é caro.

## Fluxo de canonicalização de assuntos

Depois que um bloco (ou o mapa-assuntos inteiro de um edital) está triado e aprovado, e
antes de rodar o orçamento/exportação pro SGE (estágios 3-5 de
`docs/arquitetura-integracao-planejamento-sge.md`): decidir se cada assunto já triado é
"o mesmo" de um assunto canônico que já existe (de um edital anterior), ou se é novo.

1. Pra cada assunto do bloco, buscar candidatos parecidos:
   `python integracao/canonizar_assuntos.py --buscar "termo" --db integracao/canonico.db`
   (termo sem acento se possível — ver docstring do script sobre codificação no Windows).
2. Comparar semanticamente — o mesmo conceito pode estar escrito com palavras diferentes
   entre editais (ex: "Normalização de banco de dados" vs. "Formas normais e dependência
   funcional"). Se achar candidato claramente igual, reaproveitar o UUID dele (campo
   `uuid_existente`). Se for ambíguo, **perguntar antes de decidir** — nunca mesclar nem
   duplicar por conta própria.
3. Registrar a decisão de todo o bloco de uma vez: montar um JSON (`disciplina`, `assunto`,
   `edital`, `redacao`, `peso`, `paginas`, `referencia`, `uuid_existente` opcional — ver
   docstring de `canonizar_assuntos.py`) e rodar
   `python integracao/canonizar_assuntos.py --adicionar-lote arquivo.json --db integracao/canonico.db`.
   Texto com acento entra sempre pelo JSON, nunca por flag de linha de comando.
4. **O nome canônico só é corrigido pelo lado do planejamento.** Se um nome canônico
   existente estava errado, corrigir com `--uuid-existente` apontando pro UUID certo
   (nunca criar um UUID novo só porque o nome mudou — isso quebraria o upsert no SGE).

## Ficha de sessão diária

Assim que a triagem de um bloco for aprovada, gerar de uma vez **todas as
fichas dos dias daquele bloco** (não dia a dia sob demanda) em
`docs/sessoes/AAAA-MM-DD.md`: versão compacta só do necessário pra cada dia
(leitura com arquivo+página exatos, pretest, fixação, banco de reserva,
observações de gap) — extraída da triagem completa, sem exigir abrir o
documento inteiro na hora de estudar. Gerar o bloco inteiro de uma vez evita
depender de um chat toda noite antes de cada sessão.

## Divergência entre sessão real e mapa de assuntos

A triagem confirma cobertura por amostragem (busca + leitura de trecho), mas
o estudo real pode revelar que o status não bate — ex: um ❌ que na verdade
está coberto em outro PDF, ou um ✅/🟡 que só menciona o termo de passagem
sem ensinar de verdade. Ao notar isso durante uma sessão:

1. Registrar no campo "observações de gap" da ficha do dia
   (`docs/sessoes/AAAA-MM-DD.md`).
2. Propor a correção pontual em `mapa-assuntos-edital.md` como diff, pedindo
   aprovação — não é preciso reabrir a triagem inteira do bloco por um único
   assunto divergente.
3. Não recalcular o mapa inteiro a cada achado isolado — um recheck
   consolidado faz mais sentido em cadência semanal.

## PDF mesclado do dia

Junto de cada ficha de sessão, gerar o manifesto JSON e rodar
`dias/montar_dia.py` pra produzir um único PDF por dia, com as páginas na
ordem de leitura sugerida (não necessariamente a ordem do PDF original) e
capa de rastreabilidade. Ver `dias/montar_dia.py` (docstring) pro formato do
manifesto. Gerar os manifestos/PDFs de todos os dias do bloco junto com as
fichas, na mesma leva — não esperar o dia chegar pra montar.

## Rascunho de Anki

Ao final de uma triagem (ou sessão), gerar `anki/cards_bloco_<nome>.json`
com os pontos-chave identificados, seguindo as regras do método
(`plano-estudos-sefaz-sc-2026.md`, seção "Sistema de flashcards"):

- **cloze** → leis, classificações, decoreba
- **basic** → "quando usar X em vez de Y" (não "defina X")
- **basic_reversed** → sigla ↔ significado
- Cards atômicos: um fato por card
- Deck: `SEFAZ SC::<Trilha>::<Bloco>` (ver estrutura em `inventario-materiais-sefaz-sc.md`)

Rodar `anki/anki_gerar.py` pra converter em CSV importável. **O rascunho é
pra revisão humana antes de importar** — não é pra importar direto sem olhar.

## Regras gerais

- **Sempre que uma nova descoberta contradisser ou enriquecer o que já está documentado**
  (ex: uma fonte melhor achada depois, um gap que na verdade não existe, um status
  desatualizado), **atualizar a documentação existente relevante no mesmo momento**
  (`mapa-assuntos-edital.md`, `inventario-materiais-sefaz-sc.md`, triagens já escritas)
  — não deixar a descoberta só registrada na conversa. Continua valendo mostrar o diff
  antes de gravar `docs/*.md`.
- Nunca sobrescrever `docs/*.md` sem mostrar o diff antes.
- Nunca reindexar o acervo inteiro sem necessidade — `indexador.py` já é
  incremental (só processa arquivo novo/alterado).
- Ao encontrar um gap real (assunto não coberto no acervo), documentar
  explicitamente — não inventar conteúdo pra "preencher" a lacuna.
