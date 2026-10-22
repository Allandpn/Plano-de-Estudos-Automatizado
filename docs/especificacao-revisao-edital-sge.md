# Especificação: revisão do edital no SGE (assuntos, partes e ligação à árvore do QConcursos)

**Versão** 0.1.0 · **Data** 2026-10-22 · **Natureza:** especificação aprovada pelo usuário nos pontos da §9. O que
toca o SGE nasce lá, pelo documento e pela regra deles (`01_DOMINIO.md`, ADR); este texto é o pedido e o desenho
de origem. O protótipo do lado do planejamento está em `integracao/partes_edital.py`,
`integracao/mapear_partes.py` e `integracao/casar_taxonomia.py`; os casos reais de teste, em
`integracao/casos-de-teste/`. Contexto das decisões: `docs/proposta-catalogo-aulas-e-modos.md` §3.7.

## 1. Princípio

A IA propõe, as regras conferem, **a pessoa resolve**. Trocar de modelo ou de prompt muda as respostas da IA; por isso a
qualidade do sistema não pode depender de acertar a IA, e sim de **deixar a pessoa resolver cada divergência com pouco
esforço e de guardar o que ela decidiu**. Nada que uma pessoa decidiu é desfeito por um novo processamento.

## 2. Fluxo

1. Subir o PDF do edital e escolher o cargo.
2. Extração do texto (regra) → organização em disciplinas (IA) → assuntos e partes (IA, com conferência por regra) →
   ligação das partes a nós da árvore do QConcursos (IA + segunda checagem).
3. **Tela de conferência do edital** (esta especificação).
4. Com a revisão concluída, o edital segue para o material e o plano.

## 3. Tela de conferência

**Cabeçalho com as contagens:** disciplinas · assuntos · partes · ligadas por natureza (exato, mais amplo, parcial) ·
sem nó · **pendências abertas** · decididas por pessoa · aplicadas de decisão anterior.

**Duas visões:** por disciplina (como o edital) e **fila de revisão** (só o que pede decisão, na ordem de gravidade).

### 3.1 O que entra na fila de revisão (tipos de divergência)

| Tipo | Origem | O que a pessoa decide |
|---|---|---|
| Linhas fora de qualquer disciplina | organização | confirmar que são outro cargo/observação, ou incluir como disciplina |
| Trecho do edital sem assunto | conferência por regra | criar o assunto, ou descartar com motivo |
| Assunto recusado pela conferência | regra (texto reescrito, parte sem cobertura) | corrigir o texto ou aceitar assim mesmo |
| Alerta de parte | regra (contexto de outro assunto, repetição) | aceitar, editar ou separar |
| Parte mal dividida | revisão humana | **dividir, juntar, editar texto, prefixo herdado ou contexto**; a conferência por regra reroda na hora |
| Parte sem nó | ligação | escolher um nó, ou "a árvore não tem" |
| Vínculo "mais amplo" ou "parcial" | ligação | aceitar, escolher nó mais específico ou acrescentar nós |
| Nó trocado pela segunda checagem | ligação | aceitar a troca ou voltar ao anterior |
| Duas execuções (ou dois modelos) discordam | reprocessamento | escolher uma, ou outro nó |
| Disciplina do edital ligada à disciplina errada | mapa de disciplinas | **editar o mapa**; afeta todas as partes da disciplina |
| Nó da decisão sumiu ou mudou na árvore | atualização da árvore | reconfirmar |

### 3.2 Ações em cada item

- **Aceitar** (um clique; também "aceitar todos os exatos da disciplina").
- **Trocar o nó:** busca por texto na árvore, navegação por ramos, e as sugestões do sistema ao lado. Aceita mais de um
  nó. Mostra o caminho completo e o número de nós filhos (para perceber se está largo demais).
- **"A árvore não tem":** a parte fica sem filtro de questões e aparece como lacuna (não bloqueia o estudo).
- **Dividir / juntar / editar parte.**
- **Descartar** com motivo (fora do cargo, observação, repetição).
- **Comentário** livre.

**Depois de concluída a revisão, tudo isso continua disponível:** a pessoa pode vincular uma parte sem nó, trocar o nó de
uma parte já vinculada, ou acrescentar nós, a qualquer momento (ver §6.1). Cada item mostra: a parte, o contexto, o trecho do edital de onde saiu, o nó proposto, a natureza do vínculo e o que
a IA e a regra disseram.

## 4. Decisões aprovadas

Toda ação humana vira uma **decisão** com: parte (normalizada), contexto, nós, natureza, data, edital de origem, versão
da árvore. O sistema é de uma pessoa só (preparo individual): não há autor nem revisores concorrentes. Regras:

1. **Valem antes da IA e do refino**, em qualquer edital: a chave é parte + contexto, sem a disciplina.
2. O reprocessamento nunca sobrescreve uma decisão. Se a IA nova discorda, isso aparece como informação, não como
   pendência obrigatória.
3. A pessoa escolhe o **escopo**: só este edital (padrão), ou todos os editais ("sempre que aparecer 'Kanban' em Gestão de
   Projetos, use este nó"). **"Todos os editais" pede confirmação extra**, mostrando quantas partes de outros editais
   mudariam.
4. Decisões podem ser vistas, editadas e revogadas numa lista própria.
5. Conflito (duas decisões para a mesma chave com nós diferentes) abre pendência para a pessoa resolver.
6. A árvore do QConcursos muda: a decisão guarda o id, o caminho e a versão. Quando a árvore é atualizada
   (`exportar_taxonomia.py` já gera novos, removidos, renomeados e movidos), os nós afetados voltam à fila.

## 5. Independência do modelo de IA

- Cada execução guarda o modelo, a versão do prompt e a data. A fila mostra qual execução gerou a proposta.
- Trocar o modelo reprocessa só o que **não tem decisão humana**.
- Uma medida de qualidade vem do uso: taxa de aceitação por modelo e por tipo de divergência, sem depender de
  gabarito externo. Serve para escolher entre modelos.
- Os 12 casos reais de `integracao/casos-de-teste/` (6 em aberto, 6 resolvidos) viram o teste do fluxo.

## 6. Quando o edital está "pronto"

- **Bloqueia a conclusão** (o conteúdo do edital está incerto): linhas fora de disciplina não confirmadas, trechos sem
  assunto, assuntos recusados pela conferência e partes com alerta de divisão.
- **Não bloqueia, mas avisa:** partes sem nó do QConcursos ou com vínculo "mais amplo". O painel mostra, por exemplo,
  "12 partes sem filtro de questões", e o mesmo aviso fica **visível no plano**, junto ao assunto afetado, até a pessoa
  resolver. O estudo e o material seguem normalmente.
- A pessoa pode concluir com pendências que não bloqueiam; elas ficam registradas.

### 6.1 Vincular ou trocar o nó depois da conclusão

Vale a qualquer momento, a partir do aviso no plano, do painel ou da lista de partes. **O que depende do nó:**

| Depende do nó | Efeito de vincular ou trocar |
|---|---|
| Atalho para as questões do assunto (QConcursos) | muda na hora; é o uso principal |
| Casamento com o material (temas das apostilas ligados ao mesmo nó) | pode mudar quais trechos de material o assunto sugere |
| Plano, escada de revisão e histórico de estudo | **não dependem do nó**: ficam presos ao assunto, não ao nó |

**Regras para a troca não quebrar o que já existe:**

1. Trocar o nó atualiza o atalho de questões imediatamente.
2. Se a troca muda o material sugerido, o sistema **mostra o que mudaria** antes de aplicar (trechos que entram e que
   saem do assunto).
3. Material já fatiado ou já estudado **nunca é removido** (o SGE não apaga segmento): trechos novos entram como sugestão
   adicional; o que já existe fica onde está, marcado como "ligado ao nó anterior".
4. A troca é uma decisão como as outras (§4): vai para o histórico, tem escopo (este edital ou todos) e pode ser
   desfeita.
5. Antes de aplicar, o sistema checa se o nó novo ainda existe na versão atual da árvore.

## 7. Dados (resumo)

`edital_versao`, `disciplina_edital`, `assunto_edital` (texto exato), `parte` (texto, contexto, herdado),
`ligacao_proposta` (nós, natureza, execução), `decisao` (chave, nós, escopo, data, versão da árvore),
`execucao_ia` (modelo, prompt, data), `evento_de_revisao` (histórico de cada ação).

## 8. Fora do escopo desta versão

Leitura de PDF em imagem (OCR), ligação à árvore do TEC, e o uso das ligações para filtrar questões dentro do SGE.

## 9. Decididas pelo usuário (2026-10-22)

1. Concluir bloqueia só quando o conteúdo do edital está incerto; parte sem nó avisa no painel e no plano e pode ser
   resolvida depois (inclusive trocando um nó já vinculado).
2. "Valer para todos os editais" pede confirmação extra.
3. Um único usuário; sem revisores concorrentes.

## 10. Verificado no código do SGE (2026-10-22)

- O SGE **não tem hoje** nenhum campo, tabela ou tela com nó do QConcursos/TEC (só usa o site como referência visual de
  estilo). O vínculo com o nó é um **dado novo**, guardado na parte (ou no assunto), sem nada existente que dependa dele.
- No SGE, o assunto é identificado por `chaveExterna` e o segmento de material é preso ao assunto (migração
  `V9__segmento.sql`). Plano, escada de revisão e histórico de estudo seguem o assunto, não o nó. Trocar um nó **não pode**
  quebrar nada do que existe no SGE.
- O único uso do nó para o material é no lado do planejamento (`integracao/`): o casamento entre assuntos do edital e temas
  das apostilas pela árvore. Trocar o nó muda só as **sugestões** de material, como descrito no §6.1.
