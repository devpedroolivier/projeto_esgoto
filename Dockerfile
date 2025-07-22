FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    chromium-driver \
    chromium \
    curl \
    unzip \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Variáveis de ambiente para o Chrome
ENV CHROME_BIN="/usr/bin/chromium" \
    PATH="/usr/lib/chromium:$PATH"

# Criar diretório
WORKDIR /app

# Copiar arquivos
COPY . .

# Instalar dependências do Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Comando para executar a automação
CMD ["python", "main.py"]
