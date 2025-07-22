import os
from coleta_dados import realizar_login, navegar_e_exportar, aguardar_download, mover_para_dados, carregar_config, configurar_chrome
from analise_dados import analisar_medidores, gerar_graficos_alerta_por_ceo
from envio_alerta import enviar_email
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def main():
    os.makedirs("dados", exist_ok=True)
    os.makedirs("relatorios", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    config = carregar_config()
    download_dir = os.path.abspath("dados")
    chrome_options = configurar_chrome(download_dir)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        realizar_login(driver, config)
        navegar_e_exportar(driver)

        if aguardar_download(download_dir):
            caminho_arquivo = mover_para_dados(download_dir, "dados")

            if caminho_arquivo:
                df = analisar_medidores(caminho_arquivo)
                caminhos_graficos = gerar_graficos_alerta_por_ceo(df)
                caminho_relatorio = max(
                    [os.path.join("relatorios", f) for f in os.listdir("relatorios") if f.endswith(".xlsx")],
                    key=os.path.getmtime
                )
                enviar_email(caminho_relatorio, caminhos_graficos)
        else:
            print("⚠️ Download falhou ou demorou demais.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
