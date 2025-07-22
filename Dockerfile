FROM python:3.11-slim

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg2 ca-certificates fonts-liberation \
    libnss3 libatk-bridge2.0-0 libxss1 libasound2 libgtk-3-0 libgbm1 libu2f-udev libxshmfence1 libdrm2 \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Instala o Google Chrome estável
RUN curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-linux.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Define variável de ambiente
ENV CHROME_BIN="/usr/bin/google-chrome"

# Define diretório de trabalho
WORKDIR /app

# Copia os arquivos
COPY . .

# Instala dependências Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Comando padrão
CMD ["python", "main.py"]
