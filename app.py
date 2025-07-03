import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime
from bcb import sgs
import json
import requests
import io

# As importações abaixo não estão sendo usadas e podem ser removidas para um código mais limpo:
# from bcb import currency
# from bcb import Expectativas
# from bcb import TaxaJuros
# import google.generativeai as genai # A menos que seja usada em outra parte não mostrada


# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Minha Aplicação Web",
    page_icon="🏦",
    layout="wide"
)

# --- CARREGAR INDICADORES DO ARQUIVO JSON ---
@st.cache_data(ttl=3600) # Cache para evitar recarregar o JSON a cada interação
def load_indicadores_data():
    """Carrega os dados dos indicadores do arquivo JSON."""
    try:
        with open(".streamlit/indicadores.json", "r", encoding="utf-8") as f:
            indicadores_completos = json.load(f)
    except FileNotFoundError:
        st.error("Erro: O arquivo 'indicadores.json' não foi encontrado na pasta '.streamlit/'.")
        st.stop() # Interrompe a execução se o arquivo não for encontrado
    except json.JSONDecodeError:
        st.error("Erro: O arquivo 'indicadores.json' está mal formatado. Verifique a sintaxe JSON.")
        st.stop()

    indicadores_bcb_dict = {item["nome"]: item["codigo_sgs"] for item in indicadores_completos if item["codigo_sgs"] is not None}
    nomes_indicadores = [item["nome"] for item in indicadores_completos]
    indicador_detalhes = {item["nome"]: item for item in indicadores_completos}
    return indicadores_bcb_dict, nomes_indicadores, indicador_detalhes

INDICADORES_BCB_DICT, NOMES_INDICADORES, INDICADOR_DETALHES = load_indicadores_data()


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
        .st-emotion-cache-vk33gh { /* Pode precisar de ajuste futuro */
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

    # Mapeamento nome -> código
    nome_para_codigo = {nome: codigos_sgs[nome] for nome in nomes_indicadores if nome in codigos_sgs}
    if not nome_para_codigo:
        st.warning("Nenhum código válido encontrado para os indicadores fornecidos.")
        return pd.DataFrame()

    df_list = []
    for nome, codigo in nome_para_codigo.items():
        try:
            serie = sgs.get(codigo, start=data_inicial_str, end=data_final_str)
            if not serie.empty:
                serie.columns = [nome] # Força o nome do indicador como nome da coluna
                df_list.append(serie)
            else:
                st.info(f"Dados vazios para o indicador '{nome}' no período selecionado.")
        except Exception as e:
            st.error(f"Erro ao buscar dados do BCB para '{nome}' (código {codigo}): {e}")

    if df_list:
        # Usar join no índice de data para combinar, depois resetar
        df_combinado = pd.concat(df_list, axis=1, join='outer').reset_index()
        df_combinado = df_combinado.rename(columns={df_combinado.columns[0]: 'Data'})

        # Garantir tipo datetime e ordenar antes de formatar
        df_combinado['Data'] = pd.to_datetime(df_combinado['Data'])
        df_combinado = df_combinado.sort_values('Data').reset_index(drop=True)

        # Substituir "None" (strings) por np.nan e preencher valores ausentes
        df_combinado = df_combinado.replace("None", np.nan)
        # Atenção: ffill e bfill podem não ser a melhor estratégia para todas as séries
        df_combinado = df_combinado.fillna(method='ffill').fillna(method='bfill')

        # Formatar a coluna de Data para string no final, se necessário para exibição
        df_combinado['Data'] = df_combinado['Data'].dt.strftime('%d/%m/%Y')
        
        return df_combinado
    else:
        st.warning("Não foram encontrados dados para o período especificado para nenhum dos indicadores.")
        return pd.DataFrame()


# --- CONTEÚDOS DAS ABAS ---
if pagina == "🌐 Página inicial":
    exibe_header("Bem-vindo ao Monitor Econômico - NE3")

    st.markdown(
        """
        <p>
        Este monitor econômico foi concebido com o objetivo central de simplificar a busca, compilação e extração dos principais dados econômicos disponíveis em fontes oficiais, como o Banco Central do Brasil, o IBGE e o IPEA. A plataforma foi desenvolvida a partir de uma arquitetura orientada à automação e à integridade das informações, garantindo eficiência na coleta e atualização dos dados.

O sistema integra diretamente a API do Banco Central, utilizando o Sistema Gerenciador de Séries Temporais (SGS), e está preparado para incorporar outras bases públicas de dados econômicos, consolidando múltiplas fontes em um único ambiente analítico.

A solução apresenta painéis interativos, acesso a dados brutos e visualizações dinâmicas, permitindo uma compreensão rápida e aprofundada do cenário macroeconômico. Seu desenvolvimento envolveu uma abordagem estratégica e técnica voltada à democratização da informação econômica e à melhoria do processo decisório em ambientes institucionais, corporativos e acadêmicos.

O projeto é resultado de uma iniciativa independente, idealizada e estruturada por seu criador com foco em usabilidade, confiabilidade e escalabilidade na análise de séries temporais econômicas.
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
    exibe_header("📌 Painel Econômico", "Os indicadores mais importantes em uma única busca e em um só lugar.")

    # --- CAMPO PARA SELEÇÃO DE MÚLTIPLOS INDICADORES E DATAS ---
    indicadores_selecionados_nomes = st.multiselect(
        "Selecione os Indicadores para visualizar:",
        NOMES_INDICADORES,
        default=[NOMES_INDICADORES[0]] if NOMES_INDICADORES else [],
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
        # --- BUSCA DE DADOS E PLOTAGEM ---
        with st.spinner("Buscando dados do Banco Central..."):
            df_dashboard = buscar_dados_bcb(INDICADORES_BCB_DICT, indicadores_selecionados_nomes, data_inicial, data_final)

        if not df_dashboard.empty:
            st.subheader("Dados Combinados:")
            st.dataframe(df_dashboard, use_container_width=True)

            # --- GERAR GRÁFICOS EM COLUNAS (2 por linha) ---
            for i in range(0, len(indicadores_selecionados_nomes), 2):
                cols = st.columns(2)

                for j in range(2):
                    if i + j < len(indicadores_selecionados_nomes):
                        indicador = indicadores_selecionados_nomes[i + j]

                        if indicador in df_dashboard.columns:
                            # Plotly Express tenta inferir tipos, mas é bom garantir que a coluna é numérica
                            df_dashboard[indicador] = pd.to_numeric(df_dashboard[indicador], errors='coerce')
                            
                            fig = px.line(
                                df_dashboard,
                                x="Data",
                                y=indicador,
                                title=f"{indicador} ao longo do tempo",
                                labels={"Data": "Data", indicador: "Valor"},
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

                            with cols[j]:
                                st.plotly_chart(fig, use_container_width=True)
                        else:
                            with cols[j]:
                                st.warning(f"Dados para '{indicador}' não encontrados no DataFrame retornado.")
        else:
            st.warning("Não foi possível carregar dados para os indicadores e período selecionados.")

elif pagina == "🗃️ Dados":
    exibe_header("🗃️ Dados", "Tenha todos os indicadores que quiser com apenas um só clique.")

    st.markdown("### Selecione Indicadores para ver os dados brutos:")

    indicadores_para_dados = st.multiselect(
        "Escolha um ou mais indicadores:",
        NOMES_INDICADORES,
        default=[NOMES_INDICADORES[0]] if NOMES_INDICADORES else [],
        key="indicadores_dados_multiselect"
    )

    col_data_inicio_dados, col_data_fim_dados = st.columns(2)
    with col_data_inicio_dados:
        data_inicial_dados = st.date_input(
            "Data Inicial:",
            value=datetime.date(2020, 1, 1),
            key="data_inicial_dados"
        )
    with col_data_fim_dados:
        data_final_dados = st.date_input(
            "Data Final:",
            value=datetime.date.today(),
            key="data_final_dados"
        )

    if not indicadores_para_dados:
        st.warning("Selecione pelo menos um indicador para visualizar os dados.")
    else:
        st.markdown("### Descrição dos Indicadores Selecionados:")
        for ind_nome in indicadores_para_dados:
            desc = INDICADOR_DETALHES.get(ind_nome, {}).get("descricao", "Descrição não disponível.")
            st.markdown(f"**{ind_nome}**: *{desc}*")
        st.markdown("---")

        with st.spinner("Buscando dados do Banco Central..."):
            df_dados_brutos = buscar_dados_bcb(
                INDICADORES_BCB_DICT,
                indicadores_para_dados,
                data_inicial_dados,
                data_final_dados
            )

        if not df_dados_brutos.empty:
            # A coluna 'Data' já vem como datetime e ordenada de buscar_dados_bcb,
            # mas vamos garantir a consistência do formato para evitar erros em pd.to_datetime
            # e a ordenação final após qualquer processamento
            df_dados_brutos['Data_DT'] = pd.to_datetime(df_dados_brutos['Data'], format='%d/%m/%Y')
            df_dados_brutos = df_dados_brutos.sort_values('Data_DT').reset_index(drop=True)
            
            ipca_nome = "IPCA - Índice Nacional de Preços ao Consumidor Amplo"
            if ipca_nome in indicadores_para_dados and ipca_nome in df_dados_brutos.columns:
                # Garante que os valores do IPCA sejam numéricos para o cálculo
                ipca_valores_original = pd.to_numeric(df_dados_brutos[ipca_nome], errors='coerce')
                
                # Remove NaN's para o cálculo do IPCA acumulado, pois NaN's interromperiam o .cumprod()
                # Considera-se que `fillna` já foi feito na `buscar_dados_bcb`, mas é uma precaução extra.
                ipca_valores_sem_nan = ipca_valores_original.dropna()

                if not ipca_valores_sem_nan.empty:
                    # Transforma para proporção (ex: 0.5% -> 0.005)
                    ipca_proporcao = ipca_valores_sem_nan / 100 
                    
                    # Calcula o "fator de crescimento" para cada mês (1 + taxa/100)
                    fatores_crescimento = 1 + ipca_proporcao
                    
                    # Calcula o produtório acumulado desses fatores
                    produtorio_acumulado = fatores_crescimento.cumprod()
                    
                    # Ajusta a série acumulada para começar com o valor do primeiro IPCA original
                    # e compor os crescimentos subsequentes.
                    # Cria uma nova série Pandas com o mesmo índice para atribuição.
                    ipca_acumulado_calculado = (produtorio_acumulado / fatores_crescimento.iloc[0]) * ipca_valores_sem_nan.iloc[0]
                    
                    # Atribui os valores calculados de volta ao DataFrame original
                    # Usamos `.loc` para garantir que a atribuição seja feita nos locais corretos
                    df_dados_brutos["IPCA_Acumulado"] = np.nan # Inicializa a coluna
                    df_dados_brutos.loc[ipca_valores_sem_nan.index, "IPCA_Acumulado"] = ipca_acumulado_calculado
                else:
                    st.warning("Não há dados válidos de IPCA para calcular o IPCA Acumulado.")
                    df_dados_brutos["IPCA_Acumulado"] = np.nan # Garante que a coluna existe, mesmo vazia

                # IPCA 12m (%) - este cálculo está correto
                # Aplica o cálculo apenas se houver dados suficientes
                if len(ipca_proporcao) >= 12:
                    df_dados_brutos["IPCA_12m (%)"] = (
                        (1 + ipca_proporcao).rolling(window=12).apply(np.prod, raw=True) - 1
                    ) * 100
                else:
                    df_dados_brutos["IPCA_12m (%)"] = np.nan # Preenche com NaN se não houver 12 meses

            # Remove a coluna auxiliar de data se ela não for mais necessária
            df_dados_brutos = df_dados_brutos.drop(columns=['Data_DT'])
            
            # Exibir
            st.dataframe(df_dados_brutos, use_container_width=True)

            # Botão de download
            # Criação do Excel em memória
            col1, col2 = st.columns([0.5, 5.9])

            # Excel
            with col1:
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                    df_dados_brutos.to_excel(writer, index=False, sheet_name='Indicadores')
                output_excel.seek(0)
                st.download_button(
                    label="📥 Baixar Excel",
                    data=output_excel,
                    file_name="dados_indicadores_combinados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            # CSV
            with col2:
                csv = df_dados_brutos.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Baixar CSV",
                    data=csv,
                    file_name="dados_indicadores_combinados.csv",
                    mime="text/csv"
                )
        else:
            st.warning("Nenhum dado retornado para os indicadores e período selecionados.")

elif pagina == "📝 Análises e Tendências":
    exibe_header("📝 Relatórios", "Gere e visualize relatórios.")

    st.info("Em breve, relatórios automáticos estarão disponíveis.")
    st.text_area("Digite anotações ou um rascunho de relatório:")
    # st.button("Gerar Relatório") # Adicione um botão para "Gerar Relatório" aqui no futuro

elif pagina == "⚠️ Alertas e Cenários":
    exibe_header("⚙️ Configurações", "Personalize sua experiência.")

    # Tema não é controlável diretamente via Streamlit CSS para o tema global.
    # Mas você pode simular a alteração de tema ajustando cores de gráficos etc.
    # st.selectbox("Escolha um tema:", ["Claro", "Escuro"], index=1 if st.get_option("theme.base") == "dark" else 0)
    
    st.subheader("Configurações de Notificações")
    notificacoes = st.checkbox("Receber notificações por email?", value=False)
    
    if notificacoes:
        email = st.text_input("Email para notificações:", placeholder="seu.email@exemplo.com")
        if st.button("Salvar Configurações de Notificação"):
            if "@" in email and "." in email: # Validação básica de email
                st.success(f"Configurações de notificação salvas para {email}!")
                # Aqui você pode salvar o email em um banco de dados ou variável de sessão
            else:
                st.error("Por favor, insira um email válido.")
    else:
        st.info("As notificações por email estão desativadas.")


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
                    # Define um timeout para a requisição para evitar travamentos
                    response = requests.post(backend_api_url, json=feedback_data, timeout=15) 

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