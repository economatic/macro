import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Minha Aplicação Web",
    page_icon="✨",
    layout="wide"
)

# --- ESTILO CUSTOMIZADO ---
st.markdown(
    """
    <style>
        .main {
            background: linear-gradient(135deg, #f0f2f6 0%, #d9e4f5 100%);
        }
        header.css-18ni7ap.e8zbici2 {
            background-color: #0E1117;
        }
        .st-emotion-cache-10trblm.e1nzilvr1 {
            color: #0E1117;
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }
        /* Estilo para o rodapé do sidebar */
        .st-emotion-cache-vk33gh { /* Este é o seletor para o conteúdo do sidebar */
            display: flex;
            flex-direction: column;
            min-height: 100vh; /* Garante que o sidebar ocupe toda a altura da viewport */
        }
        .sidebar-footer {
            margin-top: auto; /* Empurra o footer para o final */
            text-align: center;
            color: #A9A9A9; /* Cinza claro */
            font-size: 0.8em;
            font-weight: 300; /* Fina */
            padding-bottom: 1rem; /* Espaço para não colar na borda */
        }
        /* Ajuste para o texto principal da página */
        .st-emotion-cache-nahz7x { /* Seletor para o markdown de parágrafo */
            font-size: 1.1em;
            line-height: 1.6;
            color: #4F4F4F;
            text-align: justify;
        }

        /* --- NOVO ESTILO PARA AS IMAGENS NAS COLUNAS --- */
        /* O seletor para o contêiner das imagens dentro das colunas */
        /* O seletor exato pode variar, o .stImage é mais genérico para imagens */
        .st-emotion-cache-z5fcl4 .stImage { /* Para as colunas especificas, este pode ser o seletor certo */
            height: 250px; /* Define uma altura fixa para todas as imagens */
            overflow: hidden; /* Oculta partes da imagem que excedam a altura */
            display: flex; /* Para centralizar o conteúdo da imagem */
            align-items: center; /* Centraliza verticalmente */
            justify-content: center; /* Centraliza horizontalmente */
        }

        .st-emotion-cache-z5fcl4 .stImage img {
            width: 100%; /* Garante que a imagem preencha a largura da coluna */
            height: 100%; /* Preenche a altura definida no pai (.stImage) */
            object-fit: cover; /* Recorta a imagem para preencher o contêiner sem distorcer */
            display: block; /* Remove espaços extras */
        }

    </style>
    """,
    unsafe_allow_html=True
)

# --- SIDEBAR ---
with st.sidebar:
    st.image(
        "Logo_UERJ.svg",
        width=300,
        output_format="svg"
    )

    st.title("Menu")

    # Definição das abas
    abas = [
        "🌐 Página inicial",
        "📈 Dashboard",
        "🗃️ Dados",
        "📝 Análises e Tendências",
        "⚠️ Alertas e Cenários"
    ]

    # Seleção da aba
    pagina = st.radio("Ir para:", abas)

    # --- FOOTER DO SIDEBAR ---
    st.markdown(
        """
        <div class="sidebar-footer">
            Developed by - Marcio V.
        </div>
        """,
        unsafe_allow_html=True
    )


# --- HEADER ---
def exibe_header(titulo, descricao=None):
    st.markdown(f"<h1 style='color:#0E1117'>{titulo}</h1>", unsafe_allow_html=True)
    if descricao:
        st.markdown(f"<p style='color:#333333'>{descricao}</p>", unsafe_allow_html=True)
    st.markdown("---")

# --- CONTEÚDOS DAS ABAS ---
if pagina == "🌐 Página inicial":
    exibe_header("Bem vindo ao monitor econômico")

    # Texto de sua autoria
    st.markdown(
        """
        <p>
        Este monitor econômico foi desenvolvido para fornecer uma visão abrangente e detalhada dos
        principais indicadores econômicos. Nosso objetivo é transformar dados complexos em informações
        claras e acessíveis, permitindo que você tome decisões mais informadas. Explore os dashboards
        interativos, acesse dados brutos e acompanhe análises e tendências para compreender o cenário
        econômico atual e futuro.
        </p>
        """,
        unsafe_allow_html=True
    )
    st.markdown("---") # Adiciona uma linha divisória para separar o texto da imagem

    # --- COLUNAS PARA AS IMAGENS ---
    # Criamos 3 colunas de tamanhos iguais (1, 1, 1)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.image(
            "agro.jpeg", # Sua imagem do Agro (nova)
            caption="Força de tudo aquilo que move o agronegócio.",
            use_container_width=True
        )
    with col2:
        st.image(
            "Operarios.jpeg", # Sua imagem dos Operários
            caption="O motor da indústria e do trabalho.",
            use_container_width=True
        )
    with col3:
        st.image(
            "wall.jpeg", # Sua imagem de Wall Street
            caption="Centro financeiro global.",
            use_container_width=True
        )

elif pagina == "📈 Dashboard":
    exibe_header("📈 Dashboard", "Visualize gráficos e indicadores.")

    # Exemplo de gráfico
    df = pd.DataFrame({
        "Categoria": ["A", "B", "C", "D"],
        "Valores": np.random.randint(10, 100, size=4)
    })

    fig = px.bar(
        df,
        x="Categoria", # <-- Corrigido: x é 'Categoria'
        y="Valores",   # <-- Corrigido: y é 'Valores'
        title="Gráfico de Barras",
        color="Categoria",
        height=400
    )
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
    st.download_button(
        label="📥 Baixar dados em CSV",
        data=csv,
        file_name='dados.csv',
        mime='text/csv'
    )

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

# --- FOOTER (Opcional - da página principal) ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: grey;'>"
    "Develpode by Marcio V · 2025"
    "</p>",
    unsafe_allow_html=True
)