# Worker do material e das provas (integracao/worker.py) — roda no Pi como serviço do docker compose
# do SGE-Concursos (ADR-044 e ADR-046 de lá; docs/arquitetura-integracao-planejamento-sge.md §9).
# Imagem pequena: o fatiador, o worker do material e o worker das provas, sem pdfplumber (a indexação é feita no PC).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONUTF8=1

# OCR das provas em imagem (Sprint 24 do SGE; ADR-046): Tesseract com o idioma português.
# Medido no Pi: +150 MB de imagem, pico de ~85 MB de RAM, ~8 s por página.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-por \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements-worker.txt .
RUN pip install --no-cache-dir -r requirements-worker.txt

COPY dias/montar_bloco.py dias/montar_dia.py dias/
COPY integracao/acervo.py integracao/sge_api.py integracao/triagem_ia.py integracao/worker.py integracao/
COPY integracao/ia_comum.py integracao/prova_pdf.py integracao/prova_questoes.py integracao/prova_gabarito.py \
     integracao/prova_atribuicao.py integracao/prova_julgamento.py integracao/prova_worker.py integracao/
# Diagnóstico de prova, sem IA: onde se perdeu o conteúdo que a prova cobrou (rodado à mão).
COPY integracao/diagnostico_prova.py integracao/estrutura_apostilas.py integracao/
COPY integracao/diagnostico/ integracao/diagnostico/

# Sem root: os volumes do material e das provas são os únicos lugares onde escreve.
RUN useradd --uid 1000 --create-home worker
USER worker

# Prioridade baixa: no Pi 4 de 4 GB, o app e o banco vêm primeiro.
CMD ["nice", "-n", "15", "python", "integracao/worker.py"]
