#!/usr/bin/env python3
"""
publicar_drive.py — Sobe os PDFs dos segmentos pro Google Drive e grava o link de cada um
em canonico.db, no lugar do caminho local.

Uso:
    python publicar_drive.py --edital SEFAZ-SC-2026 --saida-dir ../dias --remoto gdrive:Estudos/Material
    python publicar_drive.py --edital SEFAZ-SC-2026 --saida-dir ../dias --remoto gdrive:Estudos/Material --simular

Por que existe: o SGE só guarda e mostra o `arquivo` de cada segmento — se for caminho
local, o link "Abrir material" do celular não abre nada. Até aqui o passo era manual
(subir a pasta blocos/ no Drive, compartilhar cada PDF, colar o link no banco), e nenhum
comando fazia a última parte. Este script fecha o caminho fatiar → publicar → exportar.

O que faz, para cada pedaço do edital cujo `arquivo` ainda não é link (http/https):
    1. `rclone copyto <saida-dir>/<arquivo> <remoto>/<arquivo>` — o caminho relativo
       gerado por dias/montar_bloco.py (blocos/<assunto-slug>/segmento-NN.pdf) é mantido
       igual no Drive. O material é do assunto canônico, não do edital: dois editais que
       compartilham o assunto apontam pro mesmo PDF.
    2. `rclone link <remoto>/<arquivo>` — cria (ou devolve) o link compartilhável.
    3. Grava o link em material_pedacos.arquivo.

Pedaço que já tem link é pulado, então rodar de novo depois de uma falha no meio continua
de onde parou. Qualquer falha do rclone para tudo, sem gravar o link daquele pedaço.

Pré-requisito: rclone instalado e configurado com o remoto do Drive (`rclone config`) —
o mesmo remoto que o SGE usa pra baixar a pasta SGE-Importacao (ADR-037 de lá).

Atenção: canonizar_assuntos.py --adicionar-pedacos substitui os pedaços do assunto pelos
do registro local (caminhos locais de novo). Depois de refatiar e registrar, publique de
novo.
"""

import argparse
import re
import sqlite3
import subprocess
import sys
from pathlib import Path


class FalhaRclone(Exception):
    pass


def eh_link(arquivo):
    return bool(re.match(r"^https?://", arquivo or ""))


def rclone_real(executavel):
    def rodar(*args):
        proc = subprocess.run([executavel, *args], capture_output=True, text=True, encoding="utf-8")
        if proc.returncode != 0:
            raise FalhaRclone(f"rclone {' '.join(args)} falhou ({proc.returncode}): {proc.stderr.strip()}")
        return proc.stdout.strip()
    return rodar


def pendentes(conn, edital):
    sql = """
        SELECT mp.id, mp.arquivo, mp.ordem, ac.nome_canonico AS assunto
        FROM material_pedacos mp
        JOIN edital_assunto ea ON ea.id = mp.edital_assunto_id
        JOIN assuntos_canonicos ac ON ac.uuid = ea.assunto_uuid
        WHERE ea.edital = ?
        ORDER BY ea.ordem IS NULL, ea.ordem, mp.ordem
    """
    return [p for p in conn.execute(sql, (edital,)).fetchall() if not eh_link(p["arquivo"])]


def caminho_remoto(remoto, arquivo):
    return f"{remoto.rstrip('/')}/{Path(arquivo).as_posix()}"


def publicar(conn, edital, saida_dir, remoto, rclone, simular=False, saida=print):
    """Devolve quantos pedaços foram publicados. `rclone(*args) -> stdout` é injetado
    pra teste; em simulação, nada é chamado nem gravado."""
    lista = pendentes(conn, edital)
    if not lista:
        saida("Nada a publicar: todos os pedaços desse edital já têm link.")
        return 0

    faltando = [p["arquivo"] for p in lista if not (Path(saida_dir) / p["arquivo"]).is_file()]
    if faltando:
        raise FileNotFoundError(
            "PDF não encontrado em --saida-dir (gere com dias/montar_bloco.py):\n  "
            + "\n  ".join(faltando))

    for p in lista:
        local = Path(saida_dir) / p["arquivo"]
        destino = caminho_remoto(remoto, p["arquivo"])
        if simular:
            saida(f"[simulação] {local} -> {destino}")
            continue
        rclone("copyto", str(local), destino)
        link = rclone("link", destino).splitlines()[-1].strip()
        if not eh_link(link):
            raise FalhaRclone(f"rclone link devolveu algo que não é link para {destino}: {link!r}")
        conn.execute("UPDATE material_pedacos SET arquivo = ? WHERE id = ?", (link, p["id"]))
        conn.commit()  # um por um: falha no meio não perde o que já subiu
        saida(f"{p['assunto']} · segmento {p['ordem']}: {link}")
    return len(lista)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Sobe os segmentos pro Drive e grava os links em canonico.db.")
    ap.add_argument("--db", default="canonico.db", help="Caminho do banco SQLite (padrão: canonico.db)")
    ap.add_argument("--edital", required=True, help="Edital cujos pedaços publicar")
    ap.add_argument("--saida-dir", required=True,
                    help="O --saida-dir usado em dias/montar_bloco.py (onde está a pasta blocos/)")
    ap.add_argument("--remoto", required=True, help="Destino no rclone, ex.: gdrive:Estudos/Material")
    ap.add_argument("--rclone", default="rclone", help="Executável do rclone (padrão: rclone no PATH)")
    ap.add_argument("--simular", action="store_true", help="Só mostra o que faria")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        n = publicar(conn, args.edital, args.saida_dir, args.remoto, rclone_real(args.rclone), args.simular)
    except (FileNotFoundError, FalhaRclone) as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
    if n and not args.simular:
        print(f"\n{n} pedaço(s) publicado(s). Agora rode exportar_sge.py.")


if __name__ == "__main__":
    main()
