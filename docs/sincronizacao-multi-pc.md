# Sincronização entre PCs (trabalho ↔ casa)
### Como reaproveitar este projeto em outra máquina

O repositório git só carrega o que é leve (docs, scripts, manifestos JSON, cards de Anki).
Duas coisas ficam de fora do git (`.gitignore`) e precisam ser resolvidas à parte em cada
máquina:

1. **`apostilas/`** — junction local pros PDFs originais (~10GB). Cada máquina aponta pra
   sua própria cópia.
2. **`indice/indice.db`** — banco SQLite com o índice full-text (~820MB, gerado a partir
   das apostilas).

## 1. Clonar o repositório

```bash
git clone https://github.com/Allandpn/Plano-de-Estudos-Automatizado.git
cd Plano-de-Estudos-Automatizado
```

Opcional — usar um e-mail diferente do trabalho nos commits feitos nessa máquina:
```bash
git config user.email "seu-email-pessoal"
```

## 2. Recriar a junction `apostilas`

No PC de casa as apostilas já estão on-premise (HD local). Aponte a junction pra lá:

```powershell
New-Item -ItemType Junction -Path "apostilas" -Target "CAMINHO\LOCAL\PRA\Estrategia Concursos"
```

Troque `CAMINHO\LOCAL\PRA\Estrategia Concursos` pelo caminho real no PC de casa (não
precisa ser o mesmo caminho do PC do trabalho — a junction é local a cada máquina).

## 3. Trazer o `indice/indice.db`

**Fluxo escolhido:** subir o `indice.db` gerado aqui no trabalho pro Google Drive, e baixar
ele no PC de casa — evita ter que reindexar os ~2639 PDFs de novo (levou horas na primeira
vez).

No PC do trabalho, depois de rodar o indexador (já feito — `indice/indice.db`, 820MB):
1. Subir `indice/indice.db` pro Google Drive (upload manual, ou uma pasta sincronizada).

No PC de casa:
1. Baixar o arquivo do Google Drive.
2. Colocar em `indice/indice.db` (mesmo caminho relativo, dentro da pasta do projeto
   clonado).
3. Testar: `python indice/buscar_indice.py --listar-cursos --db indice/indice.db` — se
   listar os cursos, o índice está valendo.

**Alternativa (se o `indice.db` ficar desatualizado ou corrompido):** reindexar do zero.
Só precisa fazer isso se optar por não usar o Google Drive, ou se as apostilas mudarem:
```bash
pip install pdfplumber pypdf reportlab
python indice/indexador.py "apostilas" --db indice/indice.db
```
Roda em background, sem travar o resto do trabalho — mas demora (rodou várias horas aqui).
Se der erro de caminho longo no Windows (`WinError 3`), habilitar Long Paths:
```powershell
# PowerShell como Administrador
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWord -Force
```
(depois reiniciar o Windows)

## 4. Dependências Python por script

| Script | Precisa de |
|---|---|
| `indice/buscar_indice.py` | nada (só biblioteca padrão) |
| `indice/indexador.py` | `pdfplumber`, `pypdf` |
| `dias/montar_dia.py` | `pypdf`, `reportlab` |
| `anki/anki_gerar.py` | nada (só biblioteca padrão) |

```bash
pip install pdfplumber pypdf reportlab
```

## 5. Mantendo os dois PCs em dia

Depois de cada sessão de trabalho no projeto (triagem nova, fichas geradas etc.), commitar
e dar push de uma máquina, e puxar (`git pull`) na outra antes de começar a trabalhar nela.
O `indice.db` **não** viaja pelo git — se ele mudar (reindexação nova), repetir o passo 3
(subir/baixar do Google Drive) manualmente.
