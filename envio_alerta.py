
import smtplib
import os
import json
import mimetypes
import pandas as pd
from email.message import EmailMessage
from datetime import datetime
from analise_dados import extrair_numero, gerar_graficos_alerta_por_ceo
from jinja2 import Template

def carregar_config():
    with open("config.json", "r") as f:
        return json.load(f)

def encontrar_ultimo_relatorio():
    pasta = "relatorios"
    arquivos = [f for f in os.listdir(pasta) if f.startswith("relatorio_medidor_") and f.endswith(".xlsx")]
    if not arquivos:
        print("❌ Nenhum relatório encontrado.")
        return None
    ultimo = max(arquivos, key=lambda f: os.path.getmtime(os.path.join(pasta, f)))
    return os.path.join(pasta, ultimo)

def anexar_arquivo(msg, caminho_arquivo):
    if not os.path.exists(caminho_arquivo):
        print(f"⚠️ Arquivo não encontrado: {caminho_arquivo}")
        return
    tipo, _ = mimetypes.guess_type(caminho_arquivo)
    tipo = tipo or "application/octet-stream"
    maintype, subtype = tipo.split("/", 1)
    with open(caminho_arquivo, "rb") as f:
        msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(caminho_arquivo))

def gerar_html_carteira(df):
    resumo = (
        df.groupby("CEO")["STATUS"]
        .value_counts()
        .unstack(fill_value=0)
        .reset_index()
    )

    # Garante que todas as colunas esperadas estejam presentes
    for status in ["NORMAL", "CRÍTICO", "ALERTA"]:
        if status not in resumo.columns:
            resumo[status] = 0

    # Força conversão para int antes de somar
    resumo[["NORMAL", "CRÍTICO", "ALERTA"]] = resumo[["NORMAL", "CRÍTICO", "ALERTA"]].astype(int)
    resumo["TOTAL"] = resumo[["NORMAL", "CRÍTICO", "ALERTA"]].sum(axis=1)

    template = Template("""
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; color: #333; background: #fff; }
            h2 { color: #005eb8; }
            table {
                width: 100%; border-collapse: collapse;
                background: white; margin-top: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            th { background-color: #005eb8; color: white; padding: 10px; }
            td { text-align: center; padding: 10px; border-bottom: 1px solid #ddd; }
            tr:hover { background-color: #f1f1f1; }
            .alerta { color: red; font-weight: bold; }
        </style>
    </head>
    <body>
        <div style="margin-bottom: 20px;">
            <h3 style="color: #005eb8;">🔎 Resumo Geral</h3>
            <p><strong>Total de Pontos:</strong> {{ resumo.total }}</p>
            <p><strong>Status:</strong>
               Normal: {{ resumo.normal }} |
               Crítico: {{ resumo.critico }} |
               <span style="color:red;">Alerta: {{ resumo.alerta }}</span>
            </p>
        </div>

        <h2>📊 Carteira de Monitoramento - Resumo por CEO</h2>
        <table>
            <thead>
                <tr>
                    <th>CEO</th>
                    <th>Total</th>
                    <th>Normal</th>
                    <th>Crítico</th>
                    <th>Alerta</th>
                </tr>
            </thead>
            <tbody>
            {% for linha in dados %}
                <tr>
                    <td>{{ linha.CEO }}</td>
                    <td>{{ linha.TOTAL }}</td>
                    <td>{{ linha.NORMAL }}</td>
                    <td>{{ linha["CRÍTICO"] }}</td>
                    <td class="alerta">{{ linha.ALERTA }}</td>
                </tr>
            {% endfor %}
            </tbody>
        </table>
        <div style="margin-top: 40px;">
            <h3 style="color: red;">🚨 Medidores em Alerta</h3>
            {% if alertas %}
                <ul>
                {% for item in alertas %}
                    <li><strong>[{{ item.CEO }}]</strong> — {{ item.Endereco_Limpo }} → <span style="color:red">{{ item.Preenchimento_pct }}%</span></li>
                {% endfor %}
                </ul>
            {% else %}
                <p style="color: green;">Nenhum medidor em alerta no momento.</p>
            {% endif %}
        </div>

    </body>
    </html>
    """)
    resumo_dict = dict(
    total=len(df),
    normal=(df['STATUS'] == 'NORMAL').sum(),
    critico=(df['STATUS'] == 'CRÍTICO').sum(),
    alerta=(df['STATUS'] == 'ALERTA').sum()
)
    
    alertas = df[df["STATUS"] == "ALERTA"].copy()
    alertas["Preenchimento_pct"] = alertas["Preenchimento"].apply(lambda x: float(str(x).replace('%', '').replace(',', '.').strip()) if isinstance(x, str) else x)
    lista_alertas = alertas[["CEO", "Endereco_Limpo", "Preenchimento_pct"]].sort_values(by="CEO").to_dict(orient="records")

    return template.render(dados=resumo.to_dict(orient="records"), resumo=resumo_dict, alertas=lista_alertas)

def enviar_email(caminho_relatorio, caminhos_graficos=None):
    config = carregar_config()
    email_cfg = config["email_alerta"]

    df = pd.read_excel(caminho_relatorio)
    html_corpo = gerar_html_carteira(df)

    msg = EmailMessage()
    msg["Subject"] = "📡 Relatório de Medidores de Nível"
    msg["From"] = email_cfg["remetente"]
    msg["To"] = ", ".join(email_cfg["destinatarios"])
    msg.set_content("Segue resumo da carteira de monitoramento em HTML. Se não visualizar, verifique o anexo.")
    msg.add_alternative(html_corpo, subtype='html')

    anexar_arquivo(msg, caminho_relatorio)
    if caminhos_graficos:
        for caminho in caminhos_graficos:
            anexar_arquivo(msg, caminho)

    try:
        with smtplib.SMTP("smtp.office365.com", 587) as smtp:
            smtp.starttls()
            smtp.login(email_cfg["remetente"], email_cfg["senha_app"])
            smtp.send_message(msg)
            print("✅ E-mail enviado com sucesso!")
    except Exception as e:
        print(f"❌ Falha ao enviar e-mail: {e}")

def main():
    caminho_relatorio = encontrar_ultimo_relatorio()
    if not caminho_relatorio:
        return
    df = pd.read_excel(caminho_relatorio)
    caminhos_graficos = gerar_graficos_alerta_por_ceo(df)
    enviar_email(caminho_relatorio, caminhos_graficos)

if __name__ == "__main__":
    main()
