
import pandas as pd
import os
import re
from datetime import datetime
import matplotlib.pyplot as plt
from mapeamento_ceo import ENDERECO_PARA_CEO


# Extrai número de strings como "77 %" ou "123 mm"
def extrair_numero(texto):
    if isinstance(texto, str):
        numero = re.findall(r'\d+(?:[\.,]\d+)?', texto)
        return float(numero[0].replace(",", ".")) if numero else None
    return texto

# Extrai apenas o endereço do campo "P001 - endereço"
def extrair_endereco_completo(texto):
    if isinstance(texto, str) and " - " in texto:
        return texto.split(" - ", 1)[1].strip()
    return texto.strip() if isinstance(texto, str) else texto

# Classificação baseada na % de preenchimento
def classificar(pct):
    if pct <= 50:
        return "NORMAL"
    elif pct <= 75:
        return "CRÍTICO"
    else:
        return "ALERTA"

# Analisa o preenchimento dos medidores e salva o relatório com STATUS e CEO
def analisar_medidores(caminho_arquivo):
    df = pd.read_excel(caminho_arquivo)
    df.columns = [col.strip() for col in df.columns]

    if "Preenchimento" not in df.columns:
        raise KeyError("Coluna 'Preenchimento' não encontrada na planilha.")

    df["Endereco_Limpo"] = df["Endereço"].apply(extrair_endereco_completo)
    df["Preenchimento_pct"] = df["Preenchimento"].apply(extrair_numero)
    df["STATUS"] = df["Preenchimento_pct"].apply(classificar)
    df["CEO"] = df["Endereco_Limpo"].map(ENDERECO_PARA_CEO).fillna("DESCONHECIDO")

    os.makedirs("relatorios", exist_ok=True)
    timestamp = datetime.now().strftime("%y%m%d%H%M")
    nome_saida = f"relatorio_medidor_{timestamp}.xlsx"
    caminho_saida = os.path.join("relatorios", nome_saida)

    df.drop(columns=["Preenchimento_pct"], inplace=True)
    df.to_excel(caminho_saida, index=False)

    print(f"✅ Relatório salvo em: {caminho_saida}")
    return df

# Gera gráficos por CEO com base em medidores em ALERTA
def gerar_graficos_alerta_por_ceo(df):
    df_alerta = df[df["STATUS"] == "ALERTA"]
    if df_alerta.empty:
        print("ℹ️ Nenhum medidor em ALERTA para gerar gráficos por CEO.")
        return []

    os.makedirs("relatorios", exist_ok=True)
    caminhos = []
    data_str = datetime.now().strftime("%y%m%d")

    for ceo, grupo in df_alerta.groupby("CEO"):
        grupo = grupo.copy()
        grupo["Preenchimento_pct"] = grupo["Preenchimento"].apply(extrair_numero)
        grupo.sort_values("Preenchimento_pct", ascending=True, inplace=True)

        plt.figure(figsize=(10, 6))
        bars = plt.barh(grupo["Endereco_Limpo"], grupo["Preenchimento_pct"], color="orange")
        plt.xlabel("Preenchimento (%)")
        plt.title(f"Medidores em ALERTA (>75%) - {ceo}")
        plt.xlim(0, 100)

        for bar, valor in zip(bars, grupo["Preenchimento_pct"]):
            plt.text(valor + 1, bar.get_y() + bar.get_height()/2, f"{valor:.1f}%", va="center")

        nome_imagem = f"grafico_alerta_{ceo.replace(' ', '_')}_{data_str}.png"
        caminho = os.path.join("relatorios", nome_imagem)
        plt.tight_layout()
        plt.savefig(caminho)
        plt.close()

        caminhos.append(caminho)
        print(f"📊 Gráfico de alerta para {ceo} salvo em: {caminho}")

    return caminhos

# Teste local
if __name__ == "__main__":
    caminho = os.path.join("dados", "Resumo - Leituras Nível-1752771591557.xlsx")
    df = analisar_medidores(caminho)
    gerar_graficos_alerta_por_ceo(df)
