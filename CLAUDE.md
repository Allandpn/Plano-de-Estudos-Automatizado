@AGENTS.md

# Específico do Claude Code

O que vale para qualquer agente está em `AGENTS.md` (importado acima). Aqui fica só o que depende do Claude Code:

- **Memória do Claude** (`~/.claude/projects/.../memory/`): é conveniência, **não fonte de verdade**. Tudo o que outro agente precisaria
  saber (regras, comandos, estado, armadilhas) está em `AGENTS.md` e nos documentos do repositório. Ao descobrir algo assim, grave
  no repositório, não só na memória.
- **Skills e hooks** do Claude Code, se existirem, ficam em `.claude/` e nunca carregam regra de negócio.
- **Commits**: terminar a mensagem com o trailer `Co-Authored-By` que a sessão indicar.
