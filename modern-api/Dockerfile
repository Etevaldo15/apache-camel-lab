FROM python:3.11-slim

WORKDIR /app

# Instala dependências primeiro (cache do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código
COPY main.py .

# Expõe a porta
EXPOSE 9005

# Healthcheck nativo do Docker
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9005/health')"

# Executa com Uvicorn (4 workers para produção)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9005", "--workers", "4"]