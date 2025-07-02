import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Minha Aplicação Web",
    page_icon="🏦",
    layout="wide"
)

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
        .st-emotion-cache-nahz7x {
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

        /* Imagens nas colunas */
        .st-emotion-cache-z5fcl4 .stImage {
            height: 250px;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .st-emotion-cache-z5fcl4 .stImage img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- SIDEBAR ---
with st.sidebar:
    st.image("Logo_UERJ.svg", width=300, output_format="svg")
    st.title("Menu")

    abas = [
        "🌐 Página inicial",
        "📈 Dashboard",
        "🗃️ Dados",
        "📝 Análises e Tendências",
        "⚠️ Alertas e Cenários"
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
        st.image("Operarios.jpg", caption="O lucro cresce sobre rostos que não sorriem.", use_container_width=True)
    with col3:
        st.image("wall.jpg", caption="Um só caminho, e não é para todos.", use_container_width=True)

elif pagina == "📈 Dashboard":
    exibe_header("📈 Dashboard", "Visualize gráficos e indicadores.")

    df = pd.DataFrame({
        "Categoria": ["A", "B", "C", "D"],
        "Valores": np.random.randint(10, 100, size=4)
    })

    fig = px.bar(df, x="Categoria", y="Valores", title="Gráfico de Barras", color="Categoria", height=400)
    st.plotly_chart(fig, use_container_width=True)

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

# --- FOOTER ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: grey;'>Developed by Núcleo de Estudos em Economia Empírica · 2025</p>",
    unsafe_allow_html=True
)
