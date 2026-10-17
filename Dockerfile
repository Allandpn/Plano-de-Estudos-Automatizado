# Worker do material (integracao/worker.py) — roda no Pi como serviço do docker compose do
# SGE-Concursos (ADR-044 de lá; docs/arquitetura-integracao-planejamento-sge.md §9).
# Imagem pequena: só o fatiador e o worker, sem pdfplumber (a indexação é feita no PC).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONUTF8=1

WORKDIR /app
COPY requirements-worker.txt .
RUN pip install --no-cache-dir -r requirements-worker.txt

COPY dias/montar_bloco.py dias/montar_dia.py dias/
COPY integracao/acervo.py integracao/sge_api.py integracao/triagem_ia.py integracao/worker.py integracao/

# Sem root: o volume do material é o único lugar onde escreve.
RUN useradd --uid 1000 --create-home worker
USER worker

# Prioridade baixa: no Pi 4 de 4 GB, o app e o banco vêm primeiro.
CMD ["nice", "-n", "15", "python", "integracao/worker.py"]
