FROM python:3.11-slim

WORKDIR /app

# Instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código
COPY sender.py .
COPY legacy-private.pem .

# Executa o simulador
CMD ["python", "sender.py"]