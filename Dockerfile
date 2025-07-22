FROM python:3.11-slim

# Instalações necessárias
RUN apt-get update && apt-get install -y \
    wget unzip gnupg curl xvfb \
    fonts-liberation libnss3 libatk-bridge2.0-0 libxss1 libasound2 libgtk-3-0 libgbm1 libu2f-udev libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Instalar o Google Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

# Define o path
ENV CHROME_BIN="/usr/bin/google-chrome"

# Instalar dependências Python
WORKDIR /app
COPY . .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Executar
CMD ["python", "main.py"]
