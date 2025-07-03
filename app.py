import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime
from bcb import sgs
# from bcb import currency # Não está sendo usada
# from bcb import Expectativas # Não está sendo usada
# from bcb import TaxaJuros # Não está sendo usada
import google.generativeai as genai
import requests
import json # Importar para ler o arquivo JSON

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Minha Aplicação Web",
    page_icon="🏦",
    layout="wide"
)

# --- CARREGAR INDICADORES DO ARQUIVO JSON ---
# O arquivo indicadores.json está na pasta .streamlit, então o caminho é relativo.
try:
    with open(".streamlit/indicadores.json", "r", encoding="utf-8") as f:
        INDICADORES_COMPLETOS = json.load(f)
except FileNotFoundError:
    st.error("Erro: O arquivo 'indicadores.json' não foi encontrado na pasta '.streamlit/'.")
    st.stop() # Interrompe a execução se o arquivo não for encontrado

# Criar o dicionário INDICADORES_BCB e a lista de nomes a partir do JSON
INDICADORES_BCB_DICT = {item["nome"]: item["codigo_sgs"] for item in INDICADORES_COMPLETOS if item["codigo_sgs"] is not None}
NOMES_INDICADORES = [item["nome"] for item in INDICADORES_COMPLETOS]

# Criar um dicionário para fácil acesso às descrições e outros atributos por nome
INDICADOR_DETALHES = {item["nome"]: item for item in INDICADORES_COMPLETOS}

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
        /* Este seletor pode mudar dependendo da versão do Streamlit, mas é um bom ponto de partida */
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

        /* Ajuste do sidebar */
        [data-testid="stSidebar"] {
            width: 280px;
            min-width: 280px;
        }

        [data-testid="stSidebarContent"] {
            width: 280px;
        }

    </style>
    """,
    unsafe_allow_html=True
)

# --- SIDEBAR ---
with st.sidebar:
    st.image("NE3.png", width=300, output_format="png")
    st.title("Menu")

    abas = [
        "🌐 Página inicial",
        "📈 Dashboard",
        "🗃️ Dados",
        "📝 Análises e Tendências",
        "⚠️ Alertas e Cenários",
        "💬 Feedback"
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

@st.cache_data(ttl=3600)
def buscar_dados_bcb(codigos_sgs: dict, nomes_indicadores: list, data_inicial, data_final):
    """
    Busca dados de múltiplos indicadores no BCB para um determinado período.
    Retorna um DataFrame com a Data (no formato dd/mm/aaaa) e os valores dos indicadores.
    """

    data_inicial_str = data_inicial.strftime('%Y-%m-%d')
    data_final_str = data_final.strftime('%Y-%m-%d')

    # Mapeamento nome -> código e código -> nome
    nome_para_codigo = {nome: codigos_sgs[nome] for nome in nomes_indicadores if nome in codigos_sgs}
    codigo_para_nome = {v: k for k, v in nome_para_codigo.items()}

    if not codigo_para_nome:
        st.warning("Nenhum código válido encontrado para os indicadores fornecidos.")
        return pd.DataFrame()

    try:
        df_list = []
        for codigo, nome in codigo_para_nome.items():
            serie = sgs.get(codigo, start=data_inicial_str, end=data_final_str)
            if not serie.empty:
                serie.columns = [nome]  # Força o nome do indicador como nome da coluna
                df_list.append(serie)

        if df_list:
            df_combinado = pd.concat(df_list, axis=1).reset_index()

            # Renomear a coluna de data para 'Data'
            df_combinado = df_combinado.rename(columns={df_combinado.columns[0]: 'Data'})

            # Truncar horário e formatar como dd/mm/aaaa
            df_combinado['Data'] = pd.to_datetime(df_combinado['Data']).dt.strftime('%d/%m/%Y')

            # Substituir "None" (strings) por np.nan
            df_combinado = df_combinado.replace("None", np.nan)

            # Preencher valores ausentes com o valor mais próximo (ffill e bfill)
            df_combinado = df_combinado.fillna(method='ffill').fillna(method='bfill')

            return df_combinado
        else:
            st.warning("Não foram encontrados dados para o período especificado.")
            return pd.DataFrame()

    except Exception as e:
        st.error(f"Erro ao buscar dados do Banco Central: {e}")
        return pd.DataFrame()



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

    # --- CAMPO PARA SELEÇÃO DE MÚLTIPLOS INDICADORES E DATAS ---
    indicadores_selecionados_nomes = st.multiselect(
        "Selecione os Indicadores para visualizar:",
        NOMES_INDICADORES,
        default=[NOMES_INDICADORES[0]] if NOMES_INDICADORES else [], # Seleciona o primeiro por padrão
        key="indicadores_dashboard_multi"
    )

    # Exibir descrições dos indicadores selecionados
    if indicadores_selecionados_nomes:
        st.markdown("### Descrição dos Indicadores Selecionados:")
        for ind_nome in indicadores_selecionados_nomes:
            detalhes = INDICADOR_DETALHES.get(ind_nome)
            if detalhes and detalhes.get("descricao"):
                st.markdown(f"**{ind_nome}**: *{detalhes['descricao']}*")
            else:
                st.markdown(f"**{ind_nome}**: *Descrição não disponível.*")
        st.markdown("---")

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
    elif not indicadores_selecionados_nomes:
        st.warning("Por favor, selecione pelo menos um indicador para visualizar.")
    else:
        st.info(f"Carregando dados para: **{', '.join(indicadores_selecionados_nomes)}**")
        st.info(f"Período: de **{data_inicial.strftime('%d/%m/%Y')}** até **{data_final.strftime('%d/%m/%Y')}**")

        # --- BUSCA DE DADOS E PLOTAGEM ---
        with st.spinner("Buscando dados do Banco Central..."):
            df_dashboard = buscar_dados_bcb(INDICADORES_BCB_DICT, indicadores_selecionados_nomes, data_inicial, data_final)

        if not df_dashboard.empty:
            st.subheader("Dados Combinados:")
            st.dataframe(df_dashboard, use_container_width=True)

            # Gerar gráficos para cada indicador selecionado
            for indicador_para_grafico in indicadores_selecionados_nomes:
                if indicador_para_grafico in df_dashboard.columns:
                    fig = px.line(
                        df_dashboard,
                        x="Data",
                        y=indicador_para_grafico,
                        title=f"{indicador_para_grafico} ao longo do tempo",
                        labels={"Data": "Data", indicador_para_grafico: "Valor"},
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
                    st.warning(f"Dados para '{indicador_para_grafico}' não encontrados no DataFrame combinado.")
        else:
            st.warning("Não foi possível carregar dados para os indicadores e período selecionados.")

elif pagina == "🗃️ Dados":
    exibe_header("🗃️ Dados", "Explore dados em tabela.")

    # Nova seção para explorar dados brutos dos indicadores do JSON
    st.markdown("### Selecione um Indicador para ver os dados brutos")
    
    indicador_para_dados = st.selectbox(
        "Escolha um indicador:",
        NOMES_INDICADORES,
        key="indicador_dados_brutos"
    )

    col_data_inicio_dados, col_data_fim_dados = st.columns(2)
    with col_data_inicio_dados:
        data_inicial_dados = st.date_input(
            "Data Inicial para Dados:",
            value=datetime.date(2020, 1, 1),
            key="data_inicial_dados"
        )
    with col_data_fim_dados:
        data_final_dados = st.date_input(
            "Data Final para Dados:",
            value=datetime.date.today(),
            key="data_final_dados"
        )

    if indicador_para_dados:
        st.markdown(f"**Descrição**: *{INDICADOR_DETALHES.get(indicador_para_dados, {}).get('descricao', 'Descrição não disponível.')}*")
        
        codigo_sgs_dados = INDICADORES_BCB_DICT.get(indicador_para_dados)
        if codigo_sgs_dados:
            with st.spinner(f"Buscando dados brutos para {indicador_para_dados}..."):
                df_dados_brutos = buscar_dados_bcb(
                    {indicador_para_dados: codigo_sgs_dados}, # Passa apenas o indicador selecionado
                    [indicador_para_dados],
                    data_inicial_dados,
                    data_final_dados
                )
            if not df_dados_brutos.empty:
                st.dataframe(df_dados_brutos, use_container_width=True)
                csv = df_dados_brutos.to_csv(index=False).encode('utf-8')
                st.download_button(
                    f"📥 Baixar dados de {indicador_para_dados} em CSV",
                    data=csv,
                    file_name=f'{indicador_para_dados.replace(" ", "_").replace("/", "_").lower()}_dados.csv',
                    mime='text/csv'
                )
            else:
                st.warning(f"Não há dados disponíveis para '{indicador_para_dados}' no período selecionado.")
        else:
            st.warning(f"Não há código SGS disponível para '{indicador_para_dados}'. Não foi possível buscar dados do BCB.")

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

elif pagina == "💬 Feedback":
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