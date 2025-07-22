import os
import time
import json
import logging
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configura logging
logging.basicConfig(
    filename='logs/coleta_dados.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def carregar_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def configurar_chrome(download_dir):
    chrome_options = Options()
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.90 Safari/537.36")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--disable-software-rasterizer")
    prefs = {
        "download.default_directory": os.path.abspath(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    return chrome_options


def aguardar_download(diretorio, timeout=60):
    logging.info("Aguardando término do download...")
    segundos = 0
    while segundos < timeout:
        arquivos = os.listdir(diretorio)
        if any(arquivo.endswith('.crdownload') for arquivo in arquivos):
            time.sleep(1)
            segundos += 1
        else:
            # Espera extra para garantir finalização de escrita no disco
            time.sleep(3)
            logging.info("✅ Download concluído!")
            return True
    logging.warning("⏱️ Timeout: download não finalizado após 60s.")
    return False


def mover_para_dados(origem_dir, destino_dir):
    for arquivo in os.listdir(origem_dir):
        if arquivo.endswith(".xlsx"):
            origem = os.path.join(origem_dir, arquivo)
            destino = os.path.join(destino_dir, arquivo)
            if os.path.abspath(origem) != os.path.abspath(destino):
                shutil.move(origem, destino)
                logging.info(f"📁 Arquivo movido para: {destino}")
            else:
                logging.info(f"📁 Arquivo já está na pasta correta: {destino}")
            print(f"📁 Arquivo pronto: {destino}")
            return destino
    logging.error("❌ Nenhum arquivo .xlsx encontrado para mover.")
    return None


def realizar_login(driver, config):
    url = config["url_sistema"]
    usuario = config["login"]
    senha = config["senha"]

    driver.get(url)
    time.sleep(3)

    campo_email = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
    campo_senha = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
    botao_login = driver.find_element(
        By.CSS_SELECTOR,
        "#app > div > div.AuthenticationScreen-style__Container-sc-c7756277-0.jNpYyo > div.Authentication-style__Container-sc-7c39c71f-0.bfIWWE > div > form > div.ContentBox-style__Content-sc-9240c14d-1.icBjh.content-box-content > button"
    )

    campo_email.send_keys(usuario)
    campo_senha.send_keys(senha)
    time.sleep(1)
    botao_login.click()
    logging.info("✅ Login realizado com sucesso!")

def navegar_e_exportar(driver):
    wait = WebDriverWait(driver, 20)

    wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR, "#sidebar-scrollbar > div:nth-child(2) > div:nth-child(4)"
    ))).click()
    logging.info("🔹 Clicou em NORTE SABESP")

    wait.until(EC.element_to_be_clickable((
        By.XPATH, '//*[@id="sidebar-scrollbar"]/div[2]/a[1]'
    ))).click()
    logging.info("🔹 Clicou em Norte Nível - Mapa e Resumo")
    time.sleep(2)

    wait.until(EC.element_to_be_clickable((
        By.XPATH, '//*[@id="app"]/div/div[2]/div[5]/div/div/div/div/nav/button[2]'
    ))).click()
    logging.info("🔹 Clicou em Resumo de dados")
    time.sleep(2)

    wait.until(EC.element_to_be_clickable((
        By.XPATH, '//*[@id="app"]/div/div[2]/div[5]/div/div/div/div/div/div/div[1]/div/div/div/div[1]/div/button[2]'
    ))).click()
    logging.info("🔹 Clicou nos três pontos (...)")

    wait.until(EC.element_to_be_clickable((
        By.XPATH, '/html/body/div[2]/div[3]'
    ))).click()
    logging.info("🔹 Clicou em Export to")

    wait.until(EC.element_to_be_clickable((
        By.XPATH, '/html/body/div[3]/div[1]'
    ))).click()
    logging.info("✅ Exportação XLSX iniciada")

def main():
    os.makedirs("dados", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    config = carregar_config()
    download_dir = os.path.abspath("dados")
    chrome_options = configurar_chrome(download_dir)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        realizar_login(driver, config)
        navegar_e_exportar(driver)
        if aguardar_download(download_dir):
            mover_para_dados(download_dir, "dados")
        else:
            logging.warning("⚠️ Nenhum arquivo movido, download pode ter falhado.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
