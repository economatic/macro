import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime
from bcb import sgs # Importar o módulo sgs da biblioteca bcb
import requests # Importar para fazer requisições HTTP (para enviar feedback)

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Minha Aplicação Web",
    page_icon="🏦",
    layout="wide"
)

# --- LISTA DE INDICADORES (DICIONÁRIO PARA FACILITAR O ACESSO AO CÓDIGO BCB) ---
INDICADORES_BCB = {
    "IPCA - Índice Nacional de Preços ao Consumidor Amplo": 433,
    "SELIC - Taxa Básica de Juros": 432,
    "PIB - Produto Interno Bruto (preços correntes)": 7326,
    "Dólar Comercial - Taxa de câmbio - Compra - PTAX 800": 1,
    "IGP-M - Índice Geral de Preços - Mercado": 189,
    "Taxa de Desemprego (PNAD Contínua - Brasil)": 24369
}
NOMES_INDICADORES = list(INDICADORES_BCB.keys())

# --- ESTILO CUSTOMIZADO ---
st.markdown(
    """
    <style>
        /* Fundo da aplicação */
        .main {
            background: linear-gradient(135deg, #0E1117 0%, #1a1d24 100%);
        }

        /* Cabeçalho - visível em tema escuro */
        h1 {
            color: #f2f2f2;
            text-align: left;
            font-weight: bold;
            margin-bottom: 1rem;
        }

        /* Texto de parágrafo principal */
        p {
            font-size: 1.1em;
            line-height: 1.6;
            color: #d0d0d0;
            text-align: justify;
        }

        /* Container da aplicação */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        /* Footer do sidebar */
        .st-emotion-cache-vk33gh {
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        .sidebar-footer {
            margin-top: auto;
            text-align: center;
            color: #A9A9A9;
            font-size: 0.8em;
            font-weight: 300;
            padding-bottom: 1rem;
        }

        /* Imagens nas colunas - sem corte */
        [data-testid="stImage"] {
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
        }

        [data-testid="stImage"] img {
            width: 100%;
            height: auto;
            object-fit: contain;
            display: block;
        }

        /* CENTRALIZAR LEGENDAS DAS IMAGENS - USANDO data-testid (MAIS ESTÁVEL) */
        [data-testid="stImageCaption"] {
            text-align: center;
            color: #d0d0d0;
            font-size: 0.9em;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- SIDEBAR ---
with st.sidebar:
    st.image("NE3.png", width=300, output_format="png") # Ajustei para .png caso seja o formato da sua logo
    st.title("Menu")

    abas = [
        "🌐 Página inicial",
        "📈 Dashboard",
        "🗃️ Dados",
        "📝 Análises e Tendências",
        "⚠️ Alertas e Cenários",
        "💬 Feedback" # <--- Nova aba adicionada
    ]

    pagina = st.radio("Ir para:", abas)

    st.markdown(
        """
        <div class="sidebar-footer">
            Developed by · Marcio V ·
        </div>
        """,
        unsafe_allow_html=True
    )

# --- HEADER ---
def exibe_header(titulo, descricao=None):
    st.markdown(f"<h1>{titulo}</h1>", unsafe_allow_html=True)
    if descricao:
        st.markdown(f"<p style='color:#CCCCCC'>{descricao}</p>", unsafe_allow_html=True)
    st.markdown("---")

# --- CONTEÚDOS DAS ABAS ---
if pagina == "🌐 Página inicial":
    exibe_header("Bem vindo ao monitor econômico - NE3 ")

    st.markdown(
        """
        <p>
        Este monitor econômico foi desenvolvido para fornecer uma visão abrangente e detalhada dos principais indicadores econômicos. Nosso objetivo é transformar dados complexos em informações claras e acessíveis, permitindo que você tome decisões mais informadas. Para garantir a confiabilidade e atualização contínua, o projeto conta com a integração direta com a API do Banco Central do Brasil, utilizando o Sistema Gerenciador de Séries Temporais (SGS) para a extração dos dados econômicos. Explore os dashboards interativos, acesse dados brutos e acompanhe análises e tendências para compreender o cenário econômico atual e futuro.
        </p>
        """,
        unsafe_allow_html=True
    )
    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.image("agro.jpg", caption="No limite, toda economia volta à terra.", use_container_width=True)
    with col2:
        # Pela imagem, o nome correto seria "Operarios.jpg"
        st.image("Operarios.jpg", caption="O lucro cresce sobre rostos que não sorriem.", use_container_width=True)
    with col3:
        st.image("wall.jpg", caption="Um só caminho, e não é para todos.", use_container_width=True)

elif pagina == "📈 Dashboard":
    exibe_header("📈 Dashboard", "Visualize gráficos e indicadores.")

    # --- CAMPOS PARA SELEÇÃO DE INDICADORES E DATAS ---
    indicador_selecionado_nome = st.selectbox(
        "Selecione o Indicador:",
        NOMES_INDICADORES,
        key="indicador_dashboard"
    )

    indicador_selecionado_codigo = INDICADORES_BCB[indicador_selecionado_nome]

    col_data_inicio, col_data_fim = st.columns(2)

    with col_data_inicio:
        data_inicial = st.date_input(
            "Data Inicial:",
            value=datetime.date(2020, 1, 1),
            key="data_inicial_dashboard"
        )
    with col_data_fim:
        data_final = st.date_input(
            "Data Final:",
            value=datetime.date.today(),
            key="data_final_dashboard"
        )
    # --- FIM DOS CAMPOS DE SELEÇÃO ---

    if data_inicial > data_final:
        st.error("Erro: A Data Inicial não pode ser maior que a Data Final.")
    else:
        st.info(f"Carregando dados para: **{indicador_selecionado_nome}**")
        st.info(f"Período: de **{data_inicial.strftime('%d/%m/%Y')}** até **{data_final.strftime('%d/%m/%Y')}**")

        # --- BUSCA DE DADOS E PLOTAGEM ---
        try:
            data_inicial_str = data_inicial.strftime('%Y-%m-%d')
            data_final_str = data_final.strftime('%Y-%m-%d')

            # --- CORREÇÃO APLICADA AQUI: sgs.G_SGS.get_series ---
            df_bcb = sgs.G_SGS.get_series(
                codes={indicador_selecionado_codigo: indicador_selecionado_nome},
                start=data_inicial_str,
                end=data_final_str
            )

            if not df_bcb.empty:
                df_bcb = df_bcb.reset_index()
                df_bcb = df_bcb.rename(columns={'index': 'Data'})

                fig = px.line(
                    df_bcb,
                    x="Data", # <--- Corrigido para não repetir 'x'
                    y=indicador_selecionado_nome,
                    title=f"{indicador_selecionado_nome} ao longo do tempo",
                    labels={"Data": "Data", indicador_selecionado_nome: "Valor"},
                    template="plotly_dark"
                )
                
                fig.update_xaxes(
                    rangeslider_visible=True,
                    rangeselector=dict(
                        buttons=list([
                            dict(count=1, label="1m", step="month", stepmode="backward"),
                            dict(count=6, label="6m", step="month", stepmode="backward"),
                            dict(count=1, label="1a", step="year", stepmode="backward"),
                            dict(step="all")
                        ])
                    )
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"Não há dados disponíveis para '{indicador_selecionado_nome}' no período selecionado ({data_inicial_str} a {data_final_str}). Tente um período diferente ou verifique o indicador.")

        except Exception as e:
            st.error(f"Ocorreu um erro ao buscar os dados do Banco Central: {e}")
            st.warning("Verifique sua conexão com a internet ou se o código do indicador está correto.")
            st.info("Lembre-se de instalar a biblioteca 'bcb' caso ainda não o tenha feito: `pip install bcb`")

elif pagina == "🗃️ Dados":
    exibe_header("🗃️ Dados", "Explore dados em tabela.")

    data = pd.DataFrame({
        "Nome": ["Alice", "Bob", "Charlie", "Diana"],
        "Idade": [24, 30, 22, 28],
        "Cidade": ["São Paulo", "Rio", "Belo Horizonte", "Curitiba"]
    })

    st.dataframe(data, use_container_width=True)

    csv = data.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar dados em CSV", data=csv, file_name='dados.csv', mime='text/csv')

elif pagina == "📝 Análises e Tendências":
    exibe_header("📝 Relatórios", "Gere e visualize relatórios.")

    st.info("Em breve, relatórios automáticos estarão disponíveis.")
    st.text_area("Digite anotações ou um rascunho de relatório:")

elif pagina == "⚠️ Alertas e Cenários":
    exibe_header("⚙️ Configurações", "Personalize sua experiência.")

    tema = st.selectbox("Escolha um tema:", ["Claro", "Escuro", "Colorido"])
    notificacoes = st.checkbox("Receber notificações?")
    email = st.text_input("Email para notificações:")
    st.button("Salvar Configurações")
    st.success("Configurações atualizadas!")

elif pagina == "💬 Feedback": # <--- Nova aba "Feedback"
    exibe_header("💬 Envie seu Feedback", "Sua opinião é muito importante para nós!")

    st.write("Utilize este formulário para enviar sugestões, reportar bugs ou fazer perguntas. Seu feedback nos ajuda a melhorar!")

    with st.form("feedback_ticket_form"):
        nome = st.text_input("Seu Nome (Opcional):")
        email = st.text_input("Seu Email (Opcional - para contato):")
        assunto = st.text_input("Assunto (Ex: Bug no Dashboard, Sugestão de Novo Indicador):")
        tipo_ticket = st.selectbox(
            "Tipo de Ticket:",
            ["Bug", "Sugestão", "Dúvida", "Outro"]
        )
        prioridade = st.selectbox(
            "Prioridade (para bugs/melhorias):",
            ["Baixa", "Média", "Alta", "Crítica"]
        )
        mensagem = st.text_area("Descreva sua mensagem ou problema detalhadamente:", height=200)

        submitted = st.form_submit_button("Enviar Ticket de Feedback")

        if submitted:
            if not mensagem:
                st.warning("Por favor, preencha o campo de mensagem antes de enviar.")
            else:
                # --- URL DO SEU GOOGLE APPS SCRIPT ---
                # Esta é a URL real do seu App da Web do Google Apps Script
                backend_api_url = "https://script.google.com/macros/s/AKfycbyZ-cd3NC8EuFzMImOu1Ta34B9sMeB6yTsDjI1eOWORtcOdsUQ1EK72zl2s45Y06aXs/exec"

                feedback_data = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "nome": nome if nome else "Não informado",
                    "email": email if email else "Não informado",
                    "assunto": assunto,
                    "tipo": tipo_ticket,
                    "prioridade": prioridade,
                    "mensagem": mensagem
                }

                try:
                    # Envia os dados JSON para o seu App da Web do Google Apps Script
                    response = requests.post(backend_api_url, json=feedback_data, timeout=10)

                    if response.status_code == 200:
                        st.success("✅ Seu feedback foi enviado com sucesso!")
                        st.info("Verifique sua planilha Google para visualizar o feedback.")
                    else:
                        st.error(f"❌ Ocorreu um erro ao enviar seu feedback. Código: {response.status_code} - {response.text}")
                        st.info("Por favor, tente novamente mais tarde ou entre em contato direto.")

                except requests.exceptions.ConnectionError:
                    st.error("❌ Erro de conexão: Não foi possível alcançar o servidor de feedback. Verifique sua conexão com a internet ou tente mais tarde.")
                except requests.exceptions.Timeout:
                    st.error("❌ Tempo limite excedido: O servidor de feedback demorou muito para responder. Tente novamente.")
                except Exception as e:
                    st.error(f"❌ Ocorreu um erro inesperado ao enviar o feedback: {e}")

# --- FOOTER ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: grey;'>Developed by Núcleo de Estudos em Economia Empírica · 2025</p>",
    unsafe_allow_html=True
)