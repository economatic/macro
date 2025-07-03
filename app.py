import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime
from bcb import sgs
import json
import requests
import io
import base64

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

        /* --- ESTILOS PARA O RODAPÉ QUE APARECE AO PASSAR O MOUSE --- */
        .footer-content-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #0e1117;
            box-shadow: 0 -2px 5px rgba(0,0,0,0.2);
            z-index: 9999;

            /* Propriedades para o estado "recolhido" */
            height: 10px; /* Altura mínima quando recolhido */
            overflow: hidden; /* Esconde o conteúdo que excede a altura */
            opacity: 0.3; /* Levemente transparente quando recolhido */
            transition: all 0.3s ease-in-out; /* Transição suave para todas as propriedades */
            cursor: pointer; /* Indica que é clicável/interativo */
        }

        /* Estado quando o mouse passa sobre o rodapé */
        .footer-content-wrapper:hover {
            height: 70px; /* Altura expandida quando o mouse está sobre ele (ajuste conforme necessário) */
            opacity: 1; /* Totalmente visível */
            padding: 8px 0; /* Padding ao expandir */
        }
        
        /* Estilos do texto e logo dentro do rodapé */
        .footer-text {
            margin-bottom: 1px; /* Espaço entre texto e logo */
            font-size: 0.9em; /* Tamanho da fonte do texto */
            color: grey; /* Cor do texto */
            text-align: center;
            width: 100%;
            /* Transição para que o texto apareça suavemente */
            transition: opacity 0.3s ease-in-out;
            opacity: 0; /* Invisível por padrão */
        }

        .footer-logo {
            display: block;
            width: 50px; /* Largura da logo */
            height: auto;
            /* Transição para que a logo apareça suavemente */
            transition: opacity 0.3s ease-in-out;
            opacity: 0; /* Invisível por padrão */
        }

        /* Faz o texto e a logo aparecerem quando o rodapé expande */
        .footer-content-wrapper:hover .footer-text,
        .footer-content-wrapper:hover .footer-logo {
            opacity: 1; /* Torna visível ao passar o mouse */
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
        Este monitor econômico foi desenvolvido para otimizar a busca, compilação e extração de dados econômicos de fontes oficiais, como Banco Central do Brasil, IBGE e IPEA. Sua arquitetura, orientada à automação e integridade das informações, assegura eficiência na coleta e atualização dos dados, oferecendo também cálculos e construção de dados automáticos, como janela móvel de 12 meses e taxa de variação composta. A integração direta com a API do Banco Central (SGS) e a capacidade de incorporar outras bases públicas consolidam múltiplas fontes em um ambiente analítico unificado. A solução oferece painéis interativos, acesso a dados brutos e visualizações dinâmicas, promovendo uma compreensão ágil e aprofundada do cenário macroeconômico, visando a acessibilidade da informação e aprimoramento do processo decisório em ambientes institucionais, corporativos e acadêmicos.
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
            col1, col2 = st.columns([0.5, 2])

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

# Esta é a sua string Base64 da logo da UERJ.
# GARANTA QUE ESTA STRING ESTEJA COMPLETA E CORRETA!
logo_uerj_base64_string = "data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rIiB3aWR0aD0iNDYwcHgiIGhlaWdodD0iNTAwcHgiIHZpZXdCb3g9IjAgMCA0NjAgNDk4IiB2ZXJzaW9uPSIxLjEiPgo8ZyBpZD0ic3VyZmFjZTEiPgo8cGF0aCBzdHlsZT0iIHN0cm9rZTpub25lO2ZpbGwtcnVsZTpub256ZXJvO2ZpbGw6cmdiKDk3LjY0NzA1OSUsMjUuODgyMzUzJSwyMi43NDUwOTglKTtmaWxsLW9wYWNpdHk6MTsiIGQ9Ik0gMjk4LjY1NjI1IDEzMS4wNTg1OTQgQyAyOTguNzUgMTMyLjI4OTA2MiAyOTguOTE0MDYyIDE0OS44MzU5MzggMjczLjE5OTIxOSAxNDguMzAwNzgxIEMgMjcyLjE5MTQwNiAxNDguMjQyMTg4IDI3MC45NTcwMzEgMTQ3Ljg0NzY1NiAyNzAuMDMxMjUgMTQ3Ljk1MzEyNSBDIDMxNy4zMTY0MDYgMTE2LjI1MzkwNiAyNjYuNjUyMzQ0IDEwNS45OTIxODggMjYyLjA4OTg0NCA5MS42MzI4MTIgQyAyNjEuNjMyODEyIDk3LjgxNjQwNiAyNjQuMTI4OTA2IDk5Ljc3MzQzOCAyNjYuNDg4MjgxIDEwNS4zNzEwOTQgQyAyNjguNzUzOTA2IDExMC43NjE3MTkgMjY4LjI5Njg3NSAxMTMuMjMwNDY5IDI2OC4yOTY4NzUgMTEzLjIzMDQ2OSBDIDI2OC4yOTY4NzUgMTEzLjIzMDQ2OSAyNDMuMDE1NjI1IDk1LjgxMjUgMjQ3LjEwOTM3NSA3OS40NzI2NTYgQyAyNDcuMzU1NDY5IDc4LjUxMTcxOSAyMzcuNjY3OTY5IDg2LjIxODc1IDIzOS43MTg3NSA5OS45Mzc1IEMgMjQxLjM1OTM3NSAxMTAuODU1NDY5IDI0Mi4xMzY3MTkgMTI4LjQ0OTIxOSAyMTMuNTkzNzUgMTMyLjIxODc1IEMgMTk3Ljk5MjE4OCAxMzQuMjgxMjUgMTU1LjY3OTY4OCAxNDMuNDUzMTI1IDE1OC4yMjY1NjIgMTY1LjY2NDA2MiBDIDE2MC43Njk1MzEgMTg3Ljg1OTM3NSAyMDQuNTYyNSAxODUuMTY0MDYyIDIwNC41NjI1IDE4NS4xNjQwNjIgQyAyMTYuNTk3NjU2IDE4NS4xNjQwNjIgMjExLjQxNDA2MiAxNzUuMDcwMzEyIDIwNC4yOTI5NjkgMTcxLjY0ODQzOCBDIDE5MS45NzI2NTYgMTY2LjAzOTA2MiAxOTEuOTQ5MjE5IDE1Mi40MDIzNDQgMjIyLjg4NjcxOSAxNDYuNDUzMTI1IEMgMjA3LjQ5NjA5NCAxNTYuMDIzNDM4IDIwOS43NTc4MTIgMTYxLjI1NzgxMiAyMjEuMzU5Mzc1IDE2Ny4zOTQ1MzEgQyAyMzQuNSAxNzQuMjI2NTYyIDIyMi42NjQwNjIgMTg1LjA4MjAzMSAyMjguMzYzMjgxIDE4NS4wOTM3NSBDIDIzMi43OTY4NzUgMTg1LjI4MTI1IDI0MC41NjI1IDE4NS4zMTY0MDYgMjQ0LjY3OTY4OCAxODUuMzE2NDA2IEMgMjUxLjc4OTA2MiAxODUuMTk5MjE5IDIxNy45Njg3NSAxNjkuMjQ2MDk0IDI1My4wNTg1OTQgMTQ4LjkzMzU5NCBDIDIzNi40NTcwMzEgMTcyLjY5MTQwNiAyNTcuOTcyNjU2IDE4My40NTcwMzEgMjYxLjMxNjQwNiAxODMuNjA5Mzc1IEMgMjY0LjY2MDE1NiAxODMuNzUgMjUwLjA3ODEyNSAxNjkuODA4NTk0IDI3OC44MTY0MDYgMTYzLjU2NjQwNiBDIDMwOC41MzEyNSAxNTcuMTAxNTYyIDI5OC42NTYyNSAxMzEuMDU4NTk0IDI5OC42NTYyNSAxMzEuMDU4NTk0IFogTSAyMjguNTc0MjE5IDk0LjE3MTg3NSBDIDIzNC40NTMxMjUgMTA4LjY0MDYyNSAyMjQuODkwNjI1IDExOS4zNTkzNzUgMjE1LjE5MTQwNiAxMjIuMjAzMTI1IEMgMjA2LjUzMTI1IDEyNC43NDYwOTQgMTk2LjcwMzEyNSAxMjUuMzY3MTg4IDE5MC4zNTU0NjkgMTI3LjYwNTQ2OSBDIDE4My44MzIwMzEgMTI5LjkxMDE1NiAxNzYuOTAyMzQ0IDEzNi4yMjY1NjIgMTc2LjkwMjM0NCAxMzYuMjI2NTYyIEMgMTc2LjkwMjM0NCAxMzYuMjI2NTYyIDE3Ni4yNjU2MjUgMTI5LjUyNzM0NCAxODQuMTgzNTk0IDEyMS4yNzczNDQgQyAxOTMuNjA1NDY5IDExMi42MjEwOTQgMjAxLjg1MTU2MiAxMTMuNzEwOTM4IDIwOS40NzY1NjIgMTA1LjQ0MTQwNiBDIDIxNi4yMjI2NTYgOTguMTA5Mzc1IDIxMC4zNTU0NjkgOTIuMzM1OTM4IDIxMC45NTMxMjUgODMuODQzNzUgQyAyMTEuMzkwNjI1IDc3LjUzOTA2MiAyMTMuNzEwOTM4IDcyLjY5MTQwNiAyMTguNDg0Mzc1IDY4Ljk3NjU2MiBDIDIxNi41MDM5MDYgNzguMDc4MTI1IDIyMy43NTM5MDYgODIuMzIwMzEyIDIyOC41NzQyMTkgOTQuMTcxODc1IFogTSAxODEuNzM0Mzc1IDc0LjQzNzUgQyAxOTUuNTYyNSA3MS43MzA0NjkgMjEzLjUgOTcuMTk1MzEyIDE5MS44NjcxODggMTA2LjA5NzY1NiBDIDE3MS42Njc5NjkgMTE0LjQwMjM0NCAxNzAuOTY0ODQ0IDEzMi42MDU0NjkgMTcwLjk2NDg0NCAxMzIuNjA1NDY5IEMgMTcwLjk2NDg0NCAxMzIuNjA1NDY5IDE2MC4yODkwNjIgMTEzLjg5ODQzOCAxODUuMDg5ODQ0IDk4LjQ3MjY1NiBDIDE5Ny4yMTg3NSA5MC45Mjk2ODggMTg4LjU2MjUgNzkuMjE0ODQ0IDE4MS43MzQzNzUgNzQuNDM3NSBaIE0gMTgxLjczNDM3NSA3NC40Mzc1ICIvPgo8cGF0aCBzdHlsZT0iIHN0cm9rZTpub25lO2ZpbGwtcnVsZTpub256ZXJvO2ZpbGw6cmdiKDY3Ljg0MzEzNyUsNTEuNzY0NzA2JSwxMi4xNTY4NjMlKTtmaWxsLW9wYWNpdHk6MTsiIGQ9Ik0gMjkwLjk0OTIxOSAyMTIuOTk2MDk0IEMgMjkwLjg0Mzc1IDIwNy43MzgyODEgMjgxLjcwMzEyNSAyMDUuNzM0Mzc1IDI3OS4yMzgyODEgMjA1LjA0Mjk2OSBMIDIyNy42ODM1OTQgMjA1LjA0Mjk2OSBDIDIyNC45OTYwOTQgMjA1LjAzMTI1IDIyOS4wNDI5NjkgMjEyLjk3MjY1NiAyMzAuOTkyMTg4IDIxMi45NzI2NTYgQyAyMzIuOTg0Mzc1IDIxMi45NzI2NTYgMjkwLjk0OTIxOSAyMTIuOTk2MDk0IDI5MC45NDkyMTkgMjEyLjk5NjA5NCBaIE0gMTk3LjI4OTA2MiAyMDIuMzk4NDM4IEwgMjc3LjI4MTI1IDIwMi40MTAxNTYgQyAyNzYuMDUwNzgxIDE5Ny41MTE3MTkgMjcyLjAxNTYyNSAxOTYuODQzNzUgMjcyLjAxNTYyNSAxOTYuODQzNzUgTCAyMjcuMzQzNzUgMTk2LjgzMjAzMSBDIDIyNS4xOTUzMTIgMTk2LjgyMDMxMiAyMjUuMzgyODEyIDE5OC43NDIxODggMjI1LjQ3NjU2MiAyMDAuMTk1MzEyIEwgMTk4LjYwMTU2MiAyMDAuMTk1MzEyIEMgMTk3LjA4OTg0NCAyMDAuMjA3MDMxIDE5Ny4yODkwNjIgMjAyLjM5ODQzOCAxOTcuMjg5MDYyIDIwMi4zOTg0MzggWiBNIDIwNi40MjU3ODEgMTk0LjY4NzUgTCAyNjkuNTc0MjE5IDE5NC42NzU3ODEgQyAyNjguNjEzMjgxIDE5MC4wNTA3ODEgMjY2LjgwNDY4OCAxODkuNTQ2ODc1IDI2Ni44MDQ2ODggMTg5LjU0Njg3NSBMIDIyNi43NTc4MTIgMTg5LjU0Njg3NSBDIDIyNS41ODIwMzEgMTg5LjU0Njg3NSAyMjQuNTUwNzgxIDE5MC4xOTE0MDYgMjI0LjgzMjAzMSAxOTIuNzU3ODEyIEMgMjE3LjMxMjUgMTkyLjc1NzgxMiAyMDkuNjk5MjE5IDE5Mi43NTc4MTIgMjA3LjUzMTI1IDE5Mi43Njk1MzEgQyAyMDYuMzMyMDMxIDE5Mi43Njk1MzEgMjA2LjQyNTc4MSAxOTQuNjg3NSAyMDYuNDI1NzgxIDE5NC42ODc1IFogTSAxOTUuMjQ2MDk0IDE5MC4xNjc5NjkgQyAxOTUuMjQ2MDk0IDE5MC4xNjc5NjkgMTkzLjMxMjUgMTkwLjAxNTYyNSAxOTIuMDIzNDM4IDE5NC41MzUxNTYgQyAxOTAuNDk2MDk0IDE5Ni4yOTI5NjkgMTg3LjAyMzQzOCAxOTIuMjY1NjI1IDE4Mi42NDg0MzggMjAxLjU1NDY4OCBDIDE2OS4zODI4MTIgMjAzLjEwMTU2MiAxNjcuODU1NDY5IDIxMS41OTM3NSAxNjkuODUxNTYyIDIxMi41NzQyMTkgQyAxNzAuNjAxNTYyIDIxMi44NjcxODggMTcwLjUwNzgxMiAyMTIuNjkxNDA2IDE3MC41MDc4MTIgMjEyLjY5MTQwNiBDIDE3MS4xMTcxODggMjA3LjMxNjQwNiAxODEuMTAxNTYyIDIwMy44MzU5MzggMTgzLjk0OTIxOSAyMDMuMTQ0NTMxIEMgMTg3LjUwMzkwNiAxOTMuNTE5NTMxIDE5MS4zMDQ2ODggMTk3LjIwNzAzMSAxOTIuNjc5Njg4IDE5NS4zMjAzMTIgQyAxOTMuNTkzNzUgMTkwLjcwNzAzMSAxOTUuMjQ2MDk0IDE5MC4xNjc5NjkgMTk1LjI0NjA5NCAxOTAuMTY3OTY5IFogTSAxNzQuNzQyMTg4IDIyMC44MTI1IEMgMTc2LjQ3NjU2MiAyMjIuMzQzNzUgMTc2LjA2NjQwNiAyMjEuNzkyOTY5IDE3Ny43MTA5MzggMjIzLjQ4MDQ2OSBDIDE4My4zODY3MTkgMjI5Ljk0OTIxOSAxNzkuNDkyMTg4IDI0Mi43MzgyODEgMjAwLjczODI4MSAyNDkuMzc4OTA2IEMgMjAwLjczODI4MSAyNDkuMzc4OTA2IDIwMS4yNDIxODggMjUyLjkxNzk2OSAyMDMuMDExNzE5IDI1Mi45Mjk2ODggQyAyMDQuNzg1MTU2IDI1Mi45Mjk2ODggMjU1LjAxNTYyNSAyNTIuOTUzMTI1IDI1Ny4xNTIzNDQgMjUyLjkyOTY4OCBDIDI1OS4yODUxNTYgMjUyLjg4MjgxMiAyNTkuODAwNzgxIDI0OS4zNzg5MDYgMjU5LjgwMDc4MSAyNDkuMzc4OTA2IEMgMjgxLjA0Njg3NSAyNDIuNzM4MjgxIDI3Ny4xNjQwNjIgMjI5Ljk0OTIxOSAyODIuODM5ODQ0IDIyMy40ODA0NjkgQyAyODQuNDk2MDk0IDIyMS44MDQ2ODggMjg0LjA3NDIxOSAyMjIuMzQzNzUgMjg1LjgwODU5NCAyMjAuODEyNSBDIDI4OS4xODc1IDIxNy45MTc5NjkgMjkxLjcyMjY1NiAyMTUuMjIyNjU2IDI4OS45Mzc1IDIxNS4yMjI2NTYgQyAyODguMTc5Njg4IDIxNS4yMzQzNzUgMTcxLjEwNTQ2OSAyMTUuMjIyNjU2IDE3MS4xMDU0NjkgMjE1LjIyMjY1NiBDIDE2OC4xNDg0MzggMjE1LjE0MDYyNSAxNzEuMzYzMjgxIDIxNy45MTc5NjkgMTc0Ljc0MjE4OCAyMjAuODEyNSBaIE0gMTgyLjM2NzE4OCAyMTcuMzc4OTA2IEwgMjM0LjY4NzUgMjE3LjU0Mjk2OSBDIDIzNC42ODc1IDIxNy41NDI5NjkgMjQ1Ljk2MDkzOCAyMTkuNDE3OTY5IDI0OS4zNjMyODEgMjI3Ljg1MTU2MiBDIDI1My4xMDU0NjkgMjM5LjE5MTQwNiAyMzguNTM1MTU2IDI0Mi44MjAzMTIgMjI1LjU5Mzc1IDI0NS40ODA0NjkgQyAyMTguNDI1NzgxIDI0Ni45NTcwMzEgMjEyLjE4NzUgMjQ5LjYwMTU2MiAyMDguODIwMzEyIDI0OS42MTMyODEgQyAyMDYuMjczNDM4IDI0OS42MjUgMjA0LjUwMzkwNiAyNDYuMDc4MTI1IDIwNC41MDM5MDYgMjQ2LjA3ODEyNSBDIDE4NS45MTAxNTYgMjQwLjIwNzAzMSAxODUuNSAyMzAuODAwNzgxIDE4My41NjI1IDIyNS4xNDQ1MzEgQyAxODEuNjE3MTg4IDIxOS40NzY1NjIgMTc3LjI4OTA2MiAyMTcuMzc4OTA2IDE4Mi4zNjcxODggMjE3LjM3ODkwNiBaIE0gMjAzLjk1MzEyNSAyNTYuNzYxNzE5IEMgMjAzLjk1MzEyNSAyNTcuNjE3MTg4IDIwNC4zODY3MTkgMjU4LjMwNDY4OCAyMDQuOTE0MDYyIDI1OC4zMDQ2ODggTCAyNTUuMTc5Njg4IDI1OC4zMDQ2ODggQyAyNTUuNzE4NzUgMjU4LjMwNDY4OCAyNTYuMTQwNjI1IDI1Ny42MTcxODggMjU2LjE0MDYyNSAyNTYuNzYxNzE5IEMgMjU2LjE0MDYyNSAyNTUuODk0NTMxIDI1NS43MTg3NSAyNTUuMTkxNDA2IDI1NS4xNzk2ODggMjU1LjE5MTQwNiBMIDIwNC45MTQwNjIgMjU1LjE5MTQwNiBDIDIwNC4zOTg0MzggMjU1LjIwMzEyNSAyMDMuOTUzMTI1IDI1NS44OTQ1MzEgMjAzLjk1MzEyNSAyNTYuNzYxNzE5IFogTSAyMTcuODYzMjgxIDMwOS4wNjI1IEMgMjE1Ljk1MzEyNSAzMDkuMDYyNSAyMTUuNDAyMzQ0IDMwOS4wNzQyMTkgMjEzLjQ4ODI4MSAzMDkuMDc0MjE5IEwgMjE4LjY2NDA2MiAzNTYuMDU4NTk0IEMgMjIwLjExNzE4OCAzNTYuNTYyNSAyMTkuODU5Mzc1IDM1Ni40ODA0NjkgMjIxLjUyMzQzOCAzNTYuOTQ5MjE5IFogTSAyMjEuNSAzMDkuMDYyNSBDIDIyMy4yODUxNTYgMzA5LjA2MjUgMjI1LjY2NDA2MiAzMDkuMDUwNzgxIDIyOC4xNjQwNjIgMzA5LjA1MDc4MSBMIDIyOC43ODUxNTYgMzU4LjAyNzM0NCBDIDIyNi4zMDA3ODEgMzU3LjkyMTg3NSAyMjQuMjQ2MDk0IDM1Ny41ODIwMzEgMjIzLjI1IDM1Ny40MTc5NjkgWiBNIDIyOS45NTcwMzEgNDA2Ljk0MTQwNiBDIDIyNS42MTcxODggNDA2Ljk0MTQwNiAyMjQuMzYzMjgxIDQwNi4wNjI1IDIyNC4zNjMyODEgNDA2LjA2MjUgTCAyMjYuNTkzNzUgNDI2IEMgMjI2LjU5Mzc1IDQyNiAyMjcuMDI3MzQ0IDQyOS4xNTIzNDQgMjMwLjA2NjQwNiA0MjkuMTUyMzQ0IEMgMjMzLjEwMTU2MiA0MjkuMTUyMzQ0IDIzMy42MTcxODggNDI1Ljk4ODI4MSAyMzMuNjE3MTg4IDQyNS45ODgyODEgTCAyMzUuNzUzOTA2IDQwNi4wNjI1IEMgMjM1Ljc0MjE4OCA0MDYuMDYyNSAyMzQuMzEyNSA0MDYuOTQxNDA2IDIyOS45NTcwMzEgNDA2Ljk0MTQwNiBaIE0gMjMxLjI1IDM1OC4wMzkwNjIgQyAyMzMuNjY0MDYyIDM1Ny45Njg3NSAyMzUuODAwNzgxIDM1Ny42NTIzNDQgMjM2Ljc5Njg3NSAzNTcuNSBMIDIzOC41MjM0MzggMzA5LjA2MjUgQyAyMzYuNzM4MjgxIDMwOS4wNTA3ODEgMjM0LjM1OTM3NSAzMDkuMDUwNzgxIDIzMS44NzEwOTQgMzA5LjA1MDc4MSBMIDIzMS4yNjE3MTkgMzU3Ljc0NjA5NCBaIE0gMjQyLjI3NzM0NCAzMDkuMDk3NjU2IEwgMjM4Ljc2OTUzMSAzNTYuOTcyNjU2IEMgMjQwLjIyMjY1NiAzNTYuNjIxMDk0IDI0MC4xOTkyMTkgMzU2LjYyMTA5NCAyNDEuNTI3MzQ0IDM1Ni4xNTIzNDQgTCAyNDYuNjE3MTg4IDMwOS4xNTYyNSBDIDI0NC43MTQ4NDQgMzA5LjEzMjgxMiAyNDQuMTc1NzgxIDMwOS4xMjEwOTQgMjQyLjI3NzM0NCAzMDkuMDk3NjU2IFogTSAyNDIuMjc3MzQ0IDMwOS4wOTc2NTYgIi8+CjxwYXRoIHN0eWxlPSIgc3Ryb2tlOm5vbmU7ZmlsbC1ydWxlOm5vbnplcm87ZmlsbDpyZ2IoMCUsNDQuNzA1ODgyJSw4MC43ODQzMTQlKTtmaWxsLW9wYWNpdHk6MTsiIGQ9Ik0gMzMyLjQxNDA2MiAxMjQuMDY2NDA2IEMgMzI5LjYwMTU2MiAxMjIuMDYyNSAzMjYuODU1NDY5IDEyMy4wMzUxNTYgMzI0LjM2NzE4OCAxMjUuNTQyOTY5IEMgMzIxLjAzNTE1NiAxMjguODk0NTMxIDMyMC44NTkzNzUgMTMyLjM0NzY1NiAzMjMuMzcxMDk0IDEzNC45MjU3ODEgTCAzMzAuMTc1NzgxIDE0MS44OTQ1MzEgTCAzNDkuNzE4NzUgMTIyLjIxNDg0NCBMIDM0Ni4wMzUxNTYgMTE4LjQ0NTMxMiBMIDMzNy45NDE0MDYgMTI2LjU4NTkzOCBMIDMzNi45OTIxODggMTI1LjYxMzI4MSBDIDMzNC4xNTIzNDQgMTIyLjcxODc1IDMzNi4zMjAzMTIgMTIwLjkyNTc4MSAzMzguNjU2MjUgMTE4LjU4NTkzOCBDIDMzOS45MzM1OTQgMTE3LjMwODU5NCAzNDEuMzU1NDY5IDExNi4wNjY0MDYgMzQyLjA1ODU5NCAxMTQuMzc4OTA2IEwgMzM4LjQ0NTMxMiAxMTAuNjc5Njg4IEMgMzM3Ljk3NjU2MiAxMTEuODQ3NjU2IDMzNC4zNjMyODEgMTE1LjYyMTA5NCAzMzMuMTMyODEyIDExNi44NzUgQyAzMjkuNjEzMjgxIDEyMC40MjU3ODEgMzMxLjc4MTI1IDEyMy4wODIwMzEgMzMyLjQ3MjY1NiAxMjQuMDE5NTMxIFogTSAzMzMuMjk2ODc1IDEyNy45NDUzMTIgTCAzMzQuOTI1NzgxIDEyOS42MjEwOTQgTCAzMjkuNDg0Mzc1IDEzNS4xMDE1NjIgTCAzMjcuODUxNTYyIDEzMy40MjU3ODEgQyAzMjYuNjc5Njg4IDEzMi4yMTg3NSAzMjYuNjc5Njg4IDEzMC44MDA3ODEgMzI4LjU0Mjk2OSAxMjguOTA2MjUgQyAzMjkuODAwNzgxIDEyNy42NTIzNDQgMzMxLjgyODEyNSAxMjYuNDQ1MzEyIDMzMy4yOTY4NzUgMTI3Ljk0NTMxMiBaIE0gMzMzLjI5Njg3NSAxMjcuOTQ1MzEyICIvPgo8cGF0aCBzdHlsZT0iIHN0cm9rZTpub25lO2ZpbGwtcnVsZTpub256ZXJvO2ZpbGw6cmdiKDAlLDQ0LjcwNTg4MiUsODAuNzg0MzE0JSk7ZmlsbC1vcGFjaXR5OjE7IiBkPSJNIDEzMS43ODUxNTYgMzIzLjY1NjI1IEwgMTI1LjkwNjI1IDMxNy4wOTc2NTYgTCAxMDUuNjAxNTYyIDMzNS45NDUzMTIgTCAxMTEuMzQ3NjU2IDM0Mi4zMjgxMjUgQyAxMTcuMzkwNjI1IDM0OS4wMzEyNSAxMjQuMTM2NzE5IDM0MS45NjQ4NDQgMTI3LjI0MjE4OCAzMzkuMDYyNSBDIDEzMy41NjY0MDYgMzMzLjE5MTQwNiAxMzYuNDE3OTY5IDMyOC43ODkwNjIgMTMxLjc4NTE1NiAzMjMuNjU2MjUgWiBNIDEyMy41NDY4NzUgMzM1LjE5NTMxMiBDIDExOC40NTcwMzEgMzM5LjkyOTY4OCAxMTYuMTAxNTYyIDM0MS4yNSAxMTMuOTQxNDA2IDMzOC44NzUgTCAxMTIuMjQyMTg4IDMzNi45NzY1NjIgTCAxMjYuMjkyOTY5IDMyMy45MjU3ODEgTCAxMjguMTI1IDMyNS45NTMxMjUgQyAxMzAuNTg1OTM4IDMyOC42NzE4NzUgMTI3LjI4OTA2MiAzMzEuNzI2NTYyIDEyMy41NDY4NzUgMzM1LjE5NTMxMiBaIE0gMTIzLjU0Njg3NSAzMzUuMTk1MzEyICIvPgo8cGF0aCBzdHlsZT0iIHN0cm9rZTpub25lO2ZpbGwtcnVsZTpub256ZXJvO2ZpbGw6cmdiKDAlLDQ0LjcwNTg4MiUsODAuNzg0MzE0JSk7ZmlsbC1vcGFjaXR5OjE7IiBkPSJNIDEwMi40MTAxNTYgMzAwLjczNDM3NSBMIDEwOC4zNTkzNzUgMjk3LjQ1MzEyNSBMIDExMi4zODI4MTIgMzA0Ljk2MDkzOCBMIDExNi4xMDE1NjIgMzAyLjkxNDA2MiBMIDEwOS41ODk4NDQgMjkwLjcxODc1IEwgODUuNDEwMTU2IDMwNC4wNzAzMTIgTCA5Mi4wNTA3ODEgMzE2LjUgTCA5NS43Njk1MzEgMzE0LjQzNzUgTCA5MS42Mjg5MDYgMzA2LjY4MzU5NCBMIDk4LjY3OTY4OCAzMDIuNzg1MTU2IEwgMTAyLjM4NjcxOSAzMDkuNzE4NzUgTCAxMDYuMTA1NDY5IDMwNy42NTYyNSBaIE0gMTAyLjQxMDE1NiAzMDAuNzM0Mzc1ICIvPgo8cGF0aCBzdHlsZT0iIHN0cm9rZTpub25lO2ZpbGwtcnVsZTpub256ZXJvO2ZpbGw6cmdiKDAlLDQ0LjcwNTg4MiUsODAuNzg0MzE0JSk7ZmlsbC1vcGFjaXR5OjE7IiBkPSJNIDE0Ni4xODc1IDMzNi43NjU2MjUgQyAxMzkuNTAzOTA2IDMzMS4yNSAxMzUuMTI4OTA2IDMzNi43MDcwMzEgMTMwLjUyNzM0NCAzNDIuNDQ1MzEyIEMgMTI1Ljk4ODI4MSAzNDguMTE3MTg4IDEyMS41NTQ2ODggMzUzLjY0NDUzMSAxMjguMjUzOTA2IDM1OS4xNjAxNTYgQyAxMzQuOTQ5MjE5IDM2NC42OTE0MDYgMTM5LjM2MzI4MSAzNTkuMTYwMTU2IDE0My45MTQwNjIgMzUzLjUwMzkwNiBDIDE0OC41MTE3MTkgMzQ3Ljc2NTYyNSAxNTIuODg2NzE5IDM0Mi4yOTI5NjkgMTQ2LjE4NzUgMzM2Ljc2NTYyNSBaIE0gMTM5LjgwODU5NCAzNTAuMTA1NDY5IEMgMTM1LjM2MzI4MSAzNTUuNjYwMTU2IDEzMy4xNDQ1MzEgMzU3LjgxNjQwNiAxMzAuODU1NDY5IDM1NS45Mjk2ODggQyAxMjguNTgyMDMxIDM1NC4wNDI5NjkgMTMwLjIxMDkzOCAzNTEuMzk0NTMxIDEzNC42NDQ1MzEgMzQ1Ljg0Mzc1IEMgMTM5LjA5Mzc1IDM0MC4yOTI5NjkgMTQxLjMwODU5NCAzMzguMTM2NzE5IDE0My41OTc2NTYgMzQwLjAyMzQzOCBDIDE0NS44ODI4MTIgMzQxLjg5NDUzMSAxNDQuMjUzOTA2IDM0NC41NTQ2ODggMTM5LjgwODU5NCAzNTAuMTA1NDY5IFogTSAxMzkuODA4NTk0IDM1MC4xMDU0NjkgIi8+CjxwYXRoIHN0eWxlPSIgc3Ryb2tlOm5vbmU7ZmlsbC1ydWxlOm5vbnplcm87ZmlsbDpyZ2IoMCUsNDQuNzA1ODgyJSw4MC43ODQzMTQlKTtmaWxsLW9wYWNpdHk6MTsiIGQ9Ik0gMzEwLjMzOTg0NCAxMjQuMTQ4NDM4IEMgMzE3LjIxMDkzOCAxMjkuNDQ1MzEyIDMyMS40MDIzNDQgMTIzLjgzMjAzMSAzMjUuODAwNzgxIDExNy45Mjk2ODggQyAzMzAuMTUyMzQ0IDExMi4xMDU0NjkgMzM0LjM4NjcxOSAxMDYuNDI1NzgxIDMyNy41MTE3MTkgMTAxLjE0NDUzMSBDIDMyMC42MzY3MTkgOTUuODQ3NjU2IDMxNi40MDIzNDQgMTAxLjUzMTI1IDMxMi4wNTA3ODEgMTA3LjM1MTU2MiBDIDMwNy42NTIzNDQgMTEzLjI0MjE4OCAzMDMuNDY0ODQ0IDExOC44NTU0NjkgMzEwLjMzOTg0NCAxMjQuMTQ4NDM4IFogTSAzMTYuMjczNDM4IDExMC41OTc2NTYgQyAzMjAuNTMxMjUgMTA0Ljg5MDYyNSAzMjIuNjc5Njg4IDEwMi42NjQwNjIgMzI1LjAyMzQzOCAxMDQuNDU3MDMxIEMgMzI3LjM3MTA5NCAxMDYuMjczNDM4IDMyNS44MzU5MzggMTA4Ljk2ODc1IDMyMS41NzgxMjUgMTE0LjY3MTg3NSBDIDMxNy4zMTY0MDYgMTIwLjM5MDYyNSAzMTUuMTcxODc1IDEyMi42MTMyODEgMzEyLjgyNDIxOSAxMjAuODA4NTk0IEMgMzEwLjQ4MDQ2OSAxMTkuMDA3ODEyIDMxMi4wMTU2MjUgMTE2LjMwMDc4MSAzMTYuMjczNDM4IDExMC41OTc2NTYgWiBNIDMxNi4yNzM0MzggMTEwLjU5NzY1NiAiLz4KPHBhdGggc3R5bGU9IiBzdHJva2U6bm9uZTtmaWxsLXJ1bGU6bm9uemVybztmaWxsOnJnYigwJSw0NC43MDU4ODIlLDgwLjc4NDMxNCUpO2ZpbGwtb3BhY2l0eToxOyIgZD0iTSAyMTQuMTc5Njg4IDM2Ni43ODkwNjIgTCAxOTcuNTgyMDMxIDM2My43MDcwMzEgTCAxOTYuNzczNDM4IDM2OC4yNzM0MzggTCAyMDIuNDg0Mzc1IDM2OS4zMzk4NDQgTCAxOTguMzY3MTg4IDM5Mi4yNjU2MjUgTCAyMDMuNTE5NTMxIDM5My4yMjY1NjIgTCAyMDcuNjM2NzE5IDM3MC4yODkwNjIgTCAyMTMuMzU5Mzc1IDM3MS4zNjcxODggWiBNIDIxNC4xNzk2ODggMzY2Ljc4OTA2MiAiLz4KPHBhdGggc3R5bGU9IiBzdHJva2U6bm9uZTtmaWxsLXJ1bGU6bm9uemVybztmaWxsOnJnYigwJSw0NC43MDU4ODIlLDgwLjc4NDMxNCUpO2ZpbGwtb3BhY2l0eToxOyIgZD0iTSA4Ni42Nzk2ODggMTY3LjM4MjgxMiBMIDk0LjA1ODU5NCAxNzAuNjQwNjI1IEwgOTAuOTcyNjU2IDE3Ny44NjcxODggTCA5NC44NDM3NSAxNzkuNTc4MTI1IEwgOTcuOTQxNDA2IDE3Mi4zNTE1NjIgTCAxMDQuMTU2MjUgMTc1LjA5Mzc1IEwgMTAwLjgwNDY4OCAxODIuOTI5Njg4IEwgMTA0LjY4NzUgMTg0LjY0MDYyNSBMIDExMC4xMTcxODggMTcxLjkyOTY4OCBMIDg0Ljg4MjgxMiAxNjAuODAwNzgxIEwgNzkuMzM1OTM4IDE3My43Njk1MzEgTCA4My4yMTg3NSAxNzUuNDgwNDY5IFogTSA4Ni42Nzk2ODggMTY3LjM4MjgxMiAiLz4KPHBhdGggc3R5bGU9IiBzdHJva2U6bm9uZTtmaWxsLXJ1bGU6bm9uemVybztmaWxsOnJnYigwJSw0NC43MDU4ODIlLDgwLjc4NDMxNCUpO2ZpbGwtb3BhY2l0eToxOyIgZD0iTSAxODkuODg2NzE5IDM2MC43NDIxODggQyAxODMuODIwMzEyIDM1OC43NzczNDQgMTgwLjk5NjA5NCAzNjEuNTAzOTA2IDE3OS42Njc5NjkgMzY1LjY2NDA2MiBDIDE3Ny4xNzE4NzUgMzczLjU5Mzc1IDE4Ny4xMDU0NjkgMzc3LjE0NDUzMSAxODUuNjA1NDY5IDM4MS45MzM1OTQgQyAxODUuMDMxMjUgMzgzLjc1IDE4My44MjAzMTIgMzg0LjY4NzUgMTgyLjE0NDUzMSAzODQuMTQ4NDM4IEMgMTc5LjM5ODQzOCAzODMuMjQ2MDk0IDE3OS45NzI2NTYgMzgxLjA3ODEyNSAxODAuNzg1MTU2IDM3OC41MzUxNTYgTCAxNzUuNzk2ODc1IDM3Ni45MjE4NzUgQyAxNzQuMDk3NjU2IDM4MS40NDE0MDYgMTczLjk2ODc1IDM4NS44NzEwOTQgMTgwLjEzNjcxOSAzODcuODcxMDk0IEMgMTgzLjkyNTc4MSAzODkuMTEzMjgxIDE4OC43MDMxMjUgMzg5Ljc2OTUzMSAxOTAuODgyODEyIDM4Mi44NzEwOTQgQyAxOTMuNTIzNDM4IDM3NC41MDc4MTIgMTgzLjM1MTU2MiAzNzEuNjgzNTk0IDE4NC45NDkyMTkgMzY2LjYyNSBDIDE4NS41MjM0MzggMzY0Ljc4NTE1NiAxODYuODAwNzgxIDM2NC4xMDU0NjkgMTg4LjQyMTg3NSAzNjQuNjMyODEyIEMgMTkwLjQzNzUgMzY1LjI4OTA2MiAxOTAuMDg1OTM4IDM2Ny40MjE4NzUgMTg5LjQ2NDg0NCAzNjkuMzk4NDM4IEwgMTk0LjMwODU5NCAzNzAuOTY4NzUgQyAxOTYuMzc1IDM2NS41MzUxNTYgMTk0Ljc0MjE4OCAzNjIuMzEyNSAxODkuODg2NzE5IDM2MC43NDIxODggWiBNIDE4OS44ODY3MTkgMzYwLjc0MjE4OCAiLz4KPHBhdGggc3R5bGU9IiBzdHJva2U6bm9uZTtmaWxsLXJ1bGU6bm9uemVybztmaWxsOnJnYigwJSw0NC43MDU4ODIlLDgwLjc4NDMxNCUpO2ZpbGwtb3BhY2l0eToxOyIgZD0iTSAxMTMuMTY3OTY5IDE2Ni4yMjY1NjIgTCA5OC4yMjI2NTYgMTUyLjAwMzkwNiBMIDk4LjI1NzgxMiAxNTEuOTQ1MzEyIEwgMTE3LjQxNDA2MiAxNTguOTcyNjU2IEwgMTIwLjIxODc1IDE1NC4yMzA0NjkgTCA5My40MjU3ODEgMTQ1LjI4MTI1IEwgOTAuMjgxMjUgMTUwLjYzMjgxMiBMIDExMC41MTU2MjUgMTcwLjczNDM3NSBaIE0gMTEzLjE2Nzk2OSAxNjYuMjI2NTYyICIvPgo8cGF0aCBzdHlsZT0iIHN0cm9rZTpub25lO2ZpbGwtcnVsZTpub256ZXJvO2ZpbGw6cmdiKDAlLDQ0LjcwNTg4MiUsODAuNzg0MzE0JSk7ZmlsbC1vcGFjaXR5OjE7IiBkPSJNIDE3MC40MTQwNjIgMzU4LjAxNTYyNSBMIDE3OC4wMzkwNjIgMzYxLjY0NDUzMSBMIDE3OS44MzIwMzEgMzU3Ljc2OTUzMSBMIDE2Ny40ODA0NjkgMzUxLjg2MzI4MSBMIDE1NS43NzM0MzggMzc3LjE0NDUzMSBMIDE2OC4zNzEwOTQgMzgzLjE2NDA2MiBMIDE3MC4xNzk2ODggMzc5LjI4NTE1NiBMIDE2Mi4zMDg1OTQgMzc1LjUyNzM0NCBMIDE2NS43MjI2NTYgMzY4LjEzNjcxOSBMIDE3Mi43NDYwOTQgMzcxLjQ4NDM3NSBMIDE3NC41NDI5NjkgMzY3LjU5NzY1NiBMIDE2Ny41MjczNDQgMzY0LjIzNDM3NSBaIE0gMTcwLjQxNDA2MiAzNTguMDE1NjI1ICIvPgo8cGF0aCBzdHlsZT0iIHN0cm9rZTpub25lO2ZpbGwtcnVsZTpub256ZXJvO2ZpbGw6cmdiKDAlLDQ0LjcwNTg4MiUsODAuNzg0MzE0JSk7ZmlsbC1vcGFjaXR5OjE7IiBkPSJNIDk1LjQ4ODI4MSAyOTIuOTEwMTU2IEMgMTAzLjUxMTcxOSAyODkuODI4MTI1IDEwNy43NTc4MTIgMjg2Ljc5Mjk2OSAxMDUuMzMyMDMxIDI4MC4yODEyNSBMIDEwMi4yNDYwOTQgMjcxLjk4ODI4MSBMIDc2LjUxOTUzMSAyODEuODc1IEwgNzkuNTM1MTU2IDI4OS45Njg3NSBDIDgyLjY5MTQwNiAyOTguNDg0Mzc1IDkxLjUyMzQzOCAyOTQuNDQ1MzEyIDk1LjQ4ODI4MSAyOTIuOTEwMTU2IFogTSA4My4yMDcwMzEgMjg3Ljc0MjE4OCBMIDgyLjMxNjQwNiAyODUuMzQzNzUgTCAxMDAuMTMyODEyIDI3OC40ODgyODEgTCAxMDEuMDk3NjU2IDI4MS4wNjY0MDYgQyAxMDIuMzg2NzE5IDI4NC41MjM0MzggOTguMjEwOTM4IDI4Ni4xMjUgOTMuNDcyNjU2IDI4Ny45NDE0MDYgQyA4Ny4wMDc4MTIgMjkwLjQxNDA2MiA4NC4zMzIwMzEgMjkwLjc3NzM0NCA4My4yMDcwMzEgMjg3Ljc0MjE4OCBaIE0gODMuMjA3MDMxIDI4Ny43NDIxODggIi8+CjxwYXRoIHN0eWxlPSIgc3Ryb2tlOm5vbmU7ZmlsbC1ydWxlOm5vbnplcm87ZmlsbDpyZ2IoMCUsNDQuNzA1ODgyJSw4MC43ODQzMTQlKTtmaWxsLW9wYWNpdHk6MTsiIGQ9Ik0gMjI3LjQ4NDM3NSAyODYuNDc2NTYyIEwgMjIyLjA3NDIxOSAyODYuNDc2NTYyIEMgMjIxLjk4MDQ2OSAyODguMzM5ODQ0IDIyMS43ODEyNSAyODkuODk4NDM4IDIyMS40ODgyODEgMjkxLjEyODkwNiBDIDIyMS4xODM1OTQgMjkyLjM1OTM3NSAyMjAuNzg1MTU2IDI5My40MDIzNDQgMjIwLjI2OTUzMSAyOTQuMjQ2MDk0IEMgMjE5LjgxMjUgMjk0Ljk1NzAzMSAyMTkuMTQ0NTMxIDI5NS40NzI2NTYgMjE4LjI4NTE1NiAyOTUuNzY1NjI1IEMgMjE3LjQyOTY4OCAyOTYuMDcwMzEyIDIxNS44NzEwOTQgMjk2LjIxMDkzOCAyMTMuNjA1NDY5IDI5Ni4yMTA5MzggTCAyMDcuNzMwNDY5IDI5Ni4yMTA5MzggTCAyMDcuNzMwNDY5IDI4NC45OTIxODggTCAyMDkuMDU0Njg4IDI4NC45OTIxODggQyAyMTAuNTg5ODQ0IDI4NC45OTIxODggMjExLjYzNjcxOSAyODUuMzc4OTA2IDIxMi4xNzU3ODEgMjg2LjEyNSBDIDIxMi43MTQ4NDQgMjg2Ljg3NSAyMTMuMDE5NTMxIDI4OC41MTU2MjUgMjEzLjA4OTg0NCAyOTEuMDQ2ODc1IEwgMjE3LjE5NTMxMiAyOTEuMDQ2ODc1IEwgMjE3LjE5NTMxMiAyNzQuNjAxNTYyIEwgMjEzLjA4OTg0NCAyNzQuNjAxNTYyIEwgMjEzLjA4OTg0NCAyNzQuOTE3OTY5IEMgMjEzLjA4OTg0NCAyNzYuOTE3OTY5IDIxMi43ODUxNTYgMjc4LjMxMjUgMjEyLjE3NTc4MSAyNzkuMDg1OTM4IEMgMjExLjU2NjQwNiAyNzkuODcxMDk0IDIxMC41MDc4MTIgMjgwLjI2OTUzMSAyMDkuMDA3ODEyIDI4MC4yNjk1MzEgTCAyMDcuNzMwNDY5IDI4MC4yNjk1MzEgTCAyMDcuNzMwNDY5IDI3MC4zNzEwOTQgTCAyMTIuOTk2MDk0IDI3MC4zNzEwOTQgQyAyMTQuOTkyMTg4IDI3MC4zNzEwOTQgMjE2LjQ0NTMxMiAyNzAuNTExNzE5IDIxNy4zMzU5MzggMjcwLjgwNDY4OCBDIDIxOC4yMzgyODEgMjcxLjA4NTkzOCAyMTguOTkyMTg4IDI3MS41NzgxMjUgMjE5LjYyNSAyNzIuMjY5NTMxIEMgMjIwLjE2NDA2MiAyNzIuODY3MTg4IDIyMC42MzI4MTIgMjczLjY1MjM0NCAyMjEuMDA3ODEyIDI3NC42MzY3MTkgQyAyMjEuMzgyODEyIDI3NS42MjEwOTQgMjIxLjc0NjA5NCAyNzYuOTg4MjgxIDIyMi4wODU5MzggMjc4LjczNDM3NSBMIDIyNy4zMDg1OTQgMjc4LjczNDM3NSBMIDIyNy4zMDg1OTQgMjY1LjMwMDc4MSBMIDE5Mi42MzI4MTIgMjY1LjMwMDc4MSBMIDE5Mi42MzI4MTIgMjcwLjM1OTM3NSBMIDE5NC4yMzgyODEgMjcwLjM1OTM3NSBDIDE5NS40MjE4NzUgMjcwLjM1OTM3NSAxOTYuMTUyMzQ0IDI3MC41MjM0MzggMTk2LjQ2ODc1IDI3MC44NTE1NjIgQyAxOTYuNzk2ODc1IDI3MS4xNzk2ODggMTk2Ljk2MDkzOCAyNzIuMDQ2ODc1IDE5Ni45NjA5MzggMjczLjQ1MzEyNSBMIDE5Ni45NjA5MzggMjkzLjM3ODkwNiBDIDE5Ni45NjA5MzggMjk0LjcwMzEyNSAxOTYuNzg1MTU2IDI5NS41MDc4MTIgMTk2LjQ0NTMxMiAyOTUuNzg5MDYyIEMgMTk2LjEwNTQ2OSAyOTYuMDcwMzEyIDE5NS4zODY3MTkgMjk2LjE5OTIxOSAxOTQuMjk2ODc1IDI5Ni4xOTkyMTkgTCAxOTIuNjQ0NTMxIDI5Ni4xOTkyMTkgTCAxOTIuNjQ0NTMxIDMwMS4zMjAzMTIgTCAyMjcuNTA3ODEyIDMwMS4zMjAzMTIgTCAyMjcuNTA3ODEyIDI4Ni40NzY1NjIgWiBNIDIyNy40ODQzNzUgMjg2LjQ3NjU2MiAiLz4KPHBhdGggc3R5bGU9IiBzdHJva2U6bm9uZTtmaWxsLXJ1bGU6bm9uemVybztmaWxsOnJnYigwJSw0NC43MDU4ODIlLDgwLjc4NDMxNCUpO2ZpbGwtb3BhY2l0eToxOyIgZD0iTSA4MC45MDYyNSAxOTYuNTYyNSBDIDg1LjY3MTg3NSAxOTcuOTQ1MzEyIDg2LjkwMjM0NCAxOTQuNzIyNjU2IDg3LjM1OTM3NSAxOTMuNjQ4NDM4IEwgODcuNDI5Njg4IDE5My42NzE4NzUgQyA4Ny4wNzgxMjUgMTk3LjE2MDE1NiA4OS4yNTc4MTIgMTk5LjExNzE4OCA5Mi42MjUgMjAwLjEwMTU2MiBDIDk3LjEzMjgxMiAyMDEuNDE0MDYyIDEwMC4xNjc5NjkgMTk5Ljg5MDYyNSAxMDEuMTU2MjUgMTk2LjM5ODQzOCBMIDEwMy44MjgxMjUgMTg2Ljk2ODc1IEwgNzcuMzg2NzE5IDE3OS4yNSBMIDc1Ljk0NTMxMiAxODQuMzQ3NjU2IEwgODYuOTAyMzQ0IDE4Ny41NDI5NjkgTCA4Ni41MjczNDQgMTg4Ljg2NzE4OCBDIDg1LjQxMDE1NiAxOTIuNzkyOTY5IDgyLjgyMDMxMiAxOTEuNzM4MjgxIDc5LjY2NDA2MiAxOTAuODEyNSBDIDc3Ljk1MzEyNSAxOTAuMzIwMzEyIDc2LjE5MTQwNiAxODkuNjUyMzQ0IDc0LjM5ODQzOCAxODkuODYzMjgxIEwgNzIuOTc2NTYyIDE5NC44NjMyODEgQyA3NC4yMTA5MzggMTk0LjcyMjY1NiA3OS4yMTg3NSAxOTYuMDcwMzEyIDgwLjkwNjI1IDE5Ni41NjI1IFogTSA5MC4zMjgxMjUgMTkxIEwgOTAuOTcyNjU2IDE4OC43MzgyODEgTCA5OC4zMjgxMjUgMTkwLjg4MjgxMiBMIDk3LjY4MzU5NCAxOTMuMTQ0NTMxIEMgOTcuMjI2NTYyIDE5NC43NTc4MTIgOTUuOTkyMTg4IDE5NS40NzI2NTYgOTMuNDYwOTM4IDE5NC43MzQzNzUgQyA5MS43ODEyNSAxOTQuMjQyMTg4IDg5Ljc1MzkwNiAxOTMuMDM5MDYyIDkwLjMyODEyNSAxOTEgWiBNIDkwLjMyODEyNSAxOTEgIi8+CjxwYXRoIHN0eWxlPSIgc3Ryb2tlOm5vbmU7ZmlsbC1ydWxlOm5vbnplcm87ZmlsbDpyZ2IoMCUsNDQuNzA1ODgyJSw4MC43ODQzMTQlKTtmaWxsLW9wYWNpdHk6MTsiIGQ9Ik0gNzcgMjE3LjQ2MDkzOCBDIDg1LjU3ODEyNSAyMTguNzAzMTI1IDg2LjYyMTA5NCAyMDguMDU0Njg4IDkxLjc4MTI1IDIwOC44MTY0MDYgQyA5My42NzE4NzUgMjA5LjA4NTkzOCA5NC41MzkwNjIgMjEwLjI0NjA5NCA5NC4zMDQ2ODggMjExLjk1NzAzMSBDIDk0IDIxNC4wODU5MzggOTEuODc1IDIxNC4wOTc2NTYgODkuODQ3NjU2IDIxMy43ODEyNSBMIDg5LjExNzE4OCAyMTguOTAyMzQ0IEMgOTQuNzUgMjIwLjA4NTkzOCA5Ny42MTMyODEgMjE3LjkwNjI1IDk4LjMzOTg0NCAyMTIuNzg1MTU2IEMgOTkuMjQyMTg4IDIwNi4zNzg5MDYgOTYuMTIxMDk0IDIwNCA5MS44NjMyODEgMjAzLjM3ODkwNiBDIDgzLjc1NzgxMiAyMDIuMTg3NSA4MS45NDE0MDYgMjEyLjcyNjU2MiA3Ny4wNDY4NzUgMjEyLjAxNTYyNSBDIDc1LjE5NTMxMiAyMTEuNzQ2MDk0IDc0LjA2NjQwNiAyMTAuNjkxNDA2IDc0LjMyODEyNSAyMDguOTEwMTU2IEMgNzQuNzM4MjgxIDIwNi4wMTU2MjUgNzYuOTI5Njg4IDIwNi4yMzgyODEgNzkuNTM1MTU2IDIwNi42MjUgTCA4MC4yODUxNTYgMjAxLjM2NzE4OCBDIDc1LjYwNTQ2OSAyMDAuNDA2MjUgNzEuMjg5MDYyIDIwMS4wMDM5MDYgNzAuMzYzMjgxIDIwNy41MTU2MjUgQyA2OS43OTY4NzUgMjExLjUyMzQzOCA2OS45NDkyMTkgMjE2LjQxNzk2OSA3NyAyMTcuNDYwOTM4IFogTSA3NyAyMTcuNDYwOTM4ICIvPgo8cGF0aCBzdHlsZT0iIHN0cm9rZTpub25lO2ZpbGwtcnVsZTpub256ZXJvO2ZpbGw6cmdiKDAlLDQ0LjcwNTg4MiUsODAuNzg0MzE0JSk7ZmlsbC1vcGFjaXR5OjE7IiBkPSJNIDEyNC40NzY1NjIgMTQ4Ljg4NjcxOSBMIDEwMi4zOTg0MzggMTMyLjE5NTMxMiBMIDk5LjI3NzM0NCAxMzYuNDcyNjU2IEwgMTIxLjM0Mzc1IDE1My4xNDA2MjUgWiBNIDEyNC40NzY1NjIgMTQ4Ljg4NjcxOSAiLz4KPHBhdGggc3R5bGU9IiBzdHJva2U6bm9uZTtmaWxsLXJ1bGU6bm9uemVybztmaWxsOnJnYigwJSw0NC43MDU4ODIlLDgwLjc4NDMxNCUpO2ZpbGwtb3BhY2l0eToxOyIgZD0iTSA2OS4xMDkzNzUgMjI3LjM3NSBMIDY5LjMzOTg0NCAyMjIuMDU4NTk0IEwgOTYuODM1OTM4IDIyMy4yNTM5MDYgTCA5Ni42MDE1NjIgMjI4LjU2NjQwNiBaIE0gNjkuMTA5Mzc1IDIyNy4zNzUgIi8+CjxwYXRoIHN0eWxlPSIgc3Ryb2tlOm5vbmU7ZmlsbC1ydWxlOm5vbnplcm87ZmlsbDpyZ2IoMCUsNDQuNzA1ODgyJSw4MC43ODQzMTQlKTtmaWxsLW9wYWNpdHk6MTsiIGQ9Ik0gMTQxLjM0Mzc1IDEzMC4yMDMxMjUgTCAxNDUuNDcyNjU2IDEyNi45Mzc1IEwgMTMzLjcwNzAzMSAxMTEuNjI1IEMgMTMxLjgzMjAzMSAxMDkuMTc5Njg4IDEzMS42MzI4MTIgMTA3LjE4NzUgMTMzLjQyNTc4MSAxMDUuNzU3ODEyIEMgMTM0LjkyNTc4MSAxMDQuNTc0MjE5IDEzNi43OTI5NjkgMTA0LjgyMDMxMiAxMzguODgyODEyIDEwNy41MjczNDQgTCAxNTAuNjM2NzE5IDEyMi44NTkzNzUgTCAxNTQuNzY1NjI1IDExOS41OTM3NSBMIDE0Mi43NjU2MjUgMTAzLjk1MzEyNSBDIDEzOS41NzQyMTkgOTkuODA4NTk0IDEzNS4zNzUgOTguOTA2MjUgMTMwLjg0Mzc1IDEwMi41IEMgMTI1LjgxMjUgMTA2LjQ4NDM3NSAxMjYuODIwMzEyIDExMS4yNzczNDQgMTI5LjM1NTQ2OSAxMTQuNTc4MTI1IFogTSAxNDEuMzQzNzUgMTMwLjIwMzEyNSAiLz4KPHBhdGggc3R5bGU9IiBzdHJva2U6bm9uZTtmaWxsLXJ1bGU6bm9uemVybztmaWxsOnJnYigwJSw0NC43MDU4ODIlLDgwLjc4NDMxNCUpO2ZpbGwtb3BhY2l0eToxOyIgZD0iTSA5OC44NTU0NjkgMjU3LjI0MjE4OCBMIDcwLjUwMzkwNiAyNTYuMjM0Mzc1IEwgNzEuNTgyMDMxIDI2MS4zNjMyODEgTCA3Ny44NDM3NSAyNjEuNDY4NzUgTCA3OS4zNDc2NTYgMjY4LjU1NDY4OCBMIDczLjY3OTY4OCAyNzEuMjM4MjgxIEwgNzQuODMyMDMxIDI3Ni42OTUzMTIgTCAxMDAuMjg1MTU2IDI2NC4wODIwMzEgWiBNIDgzLjI0MjE4OCAyNjYuNTU0Njg4IEwgODIuMTk5MjE5IDI2MS41OTc2NTYgTCA5NC4zMjgxMjUgMjYxLjQzMzU5NCBMIDk0LjMzOTg0NCAyNjEuNTAzOTA2IFogTSA4My4yNDIxODggMjY2LjU1NDY4OCAiLz4KPHBhdGggc3R5bGU9IiBzdHJva2U6bm9uZTtmaWxsLXJ1bGU6bm9uemVybztmaWxsOnJnYigwJSw0NC43MDU4ODIlLDgwLjc4NDMxNCUpO2ZpbGwtb3BhY2l0eToxOyIgZD0iTSAxMjkuNjgzNTk0IDE0Mi4zODY3MTkgTCAxMTUuNzkyOTY5IDEyOS4xNDA2MjUgTCAxMTUuODUxNTYyIDEyOS4wOTM3NSBMIDEzNC4yOTI5NjkgMTM3LjQxMDE1NiBMIDEzOS4xMTcxODggMTMyLjE4MzU5NCBMIDExOS4wNzgxMjUgMTEzLjA1NDY4OCBMIDExNS43MjI2NTYgMTE2LjY2NDA2MiBMIDEzMC4zODY3MTkgMTMwLjY2MDE1NiBMIDEzMC4zMzk4NDQgMTMwLjcwNzAzMSBMIDExMS4wMDc4MTIgMTIxLjc2OTUzMSBMIDEwNi4yOTI5NjkgMTI2Ljg3ODkwNiBMIDEyNi4zNTE1NjIgMTQ2LjAwNzgxMiBaIE0gMTI5LjY4MzU5NCAxNDIuMzg2NzE5ICIvPgo8cGF0aCBzdHlsZT0iIHN0cm9rZTpub25lO2ZpbGwtcnVsZTpub256ZXJvO2ZpbGw6cmdiKDAlLDQ0LjcwNTg4MiUsODAuNzg0MzE0JSk7ZmlsbC1vcGFjaXR5OjE7IiBkPSJNIDgzLjgxNjQwNiAyNTAuMjEwOTM4IEMgOTIuMzY3MTg4IDI0OS42NDg0MzggOTcuMzIwMzEyIDI0OC4wMzUxNTYgOTYuODgyODEyIDI0MS4wODU5MzggTCA5Ni4zMjAzMTIgMjMyLjI0MjE4OCBMIDY4Ljg1OTM3NSAyMzQuMDIzNDM4IEwgNjkuMzk4NDM4IDI0Mi42NTYyNSBDIDY5Ljk3MjY1NiAyNTEuNzEwOTM4IDc5LjYwNTQ2OSAyNTAuNDkyMTg4IDgzLjgxNjQwNiAyNTAuMjEwOTM4IFogTSA5Mi40Mzc1IDIzNy44MjAzMTIgTCA5Mi42MDE1NjIgMjQwLjU1ODU5NCBDIDkyLjgzNTkzOCAyNDQuMjM4MjgxIDg4LjM5MDYyNSAyNDQuNTMxMjUgODMuMzM1OTM4IDI0NC44NTkzNzUgQyA3Ni40NDkyMTkgMjQ1LjMwNDY4OCA3My43ODUxNTYgMjQ0Ljg0NzY1NiA3My41ODU5MzggMjQxLjYxMzI4MSBMIDczLjQyMTg3NSAyMzkuMDYyNSBaIE0gOTIuNDM3NSAyMzcuODIwMzEyICIvPgo8cGF0aCBzdHlsZT0iIHN0cm9rZTpub25lO2ZpbGwtcnVsZTpub256ZXJvO2ZpbGw6cmdiKDAlLDQ0LjcwNTg4MiUsODAuNzg0MzE0JSk7ZmlsbC1vcGFjaXR5OjE7IiBkPSJNIDE2Ni42NDg0MzggMzAyLjQxMDE1NiBDIDE3MS41NTA3ODEgMzAyLjQxMDE1NiAxNzUuMjkyOTY5IDMwMS40MTQwNjIgMTc3Ljg1MTU2MiAyOTkuNDEwMTU2IEMgMTgwLjM5NDUzMSAyOTcuNDA2MjUgMTgxLjY2NDA2MiAyOTQuNDkyMTg4IDE4MS42NjQwNjIgMjkwLjYzNjcxOSBMIDE4MS42NjQwNjIgMjczLjI3NzM0NCBDIDE4MS42NjQwNjIgMjcxLjk3NjU2MiAxODEuODI4MTI1IDI3MS4xNjc5NjkgMTgyLjE0NDUzMSAyNzAuODUxNTYyIEMgMTgyLjQ3MjY1NiAyNzAuNTIzNDM4IDE4My4yMTA5MzggMjcwLjM3MTA5NCAxODQuMzcxMDk0IDI3MC4zNzEwOTQgTCAxODUuODg2NzE5IDI3MC4zNzEwOTQgTCAxODUuODg2NzE5IDI2NS4zMTI1IEwgMTcwLjU2NjQwNiAyNjUuMzEyNSBMIDE3MC41NjY0MDYgMjcwLjM3MTA5NCBMIDE3Mi4yNDIxODggMjcwLjM3MTA5NCBDIDE3My40MDYyNSAyNzAuMzcxMDk0IDE3NC4xNDQ1MzEgMjcwLjUzNTE1NiAxNzQuNDYwOTM4IDI3MC44Mzk4NDQgQyAxNzQuNzg5MDYyIDI3MS4xNTYyNSAxNzQuOTQxNDA2IDI3Mi4wMTE3MTkgMTc0Ljk0MTQwNiAyNzMuNDQxNDA2IEwgMTc0Ljk0MTQwNiAyODkuNzU3ODEyIEMgMTc0Ljk0MTQwNiAyOTIuMjY1NjI1IDE3NC40NjA5MzggMjk0LjA3MDMxMiAxNzMuNDg4MjgxIDI5NS4xNjc5NjkgQyAxNzIuNTExNzE5IDI5Ni4yNjk1MzEgMTcwLjkwNjI1IDI5Ni44MjAzMTIgMTY4LjY2NDA2MiAyOTYuODIwMzEyIEMgMTY2Ljc3NzM0NCAyOTYuODIwMzEyIDE2NS40NDE0MDYgMjk2LjI2OTUzMSAxNjQuNjUyMzQ0IDI5NS4xNTYyNSBDIDE2My44NjcxODggMjk0LjAzNTE1NiAxNjMuNDY4NzUgMjkyLjA4OTg0NCAxNjMuNDY4NzUgMjg5LjMxMjUgTCAxNjMuNDY4NzUgMjczLjQ0MTQwNiBDIDE2My40Njg3NSAyNzIuMDgyMDMxIDE2My42MzI4MTIgMjcxLjIyNjU2MiAxNjMuOTYwOTM4IDI3MC44ODY3MTkgQyAxNjQuMjg5MDYyIDI3MC41MzUxNTYgMTY1LjA1MDc4MSAyNzAuMzcxMDk0IDE2Ni4yMzgyODEgMjcwLjM3MTA5NCBMIDE2OC4wNjY0MDYgMjcwLjM3MTA5NCBMIDE2OC4wNjY0MDYgMjY1LjMxMjUgTCAxNDguMTQ4NDM4IDI2NS4zMTI1IEwgMTQ4LjE0ODQzOCAyNzAuMzcxMDk0IEwgMTQ5LjgyNDIxOSAyNzAuMzcxMDk0IEMgMTUxIDI3MC4zNzEwOTQgMTUxLjczODI4MSAyNzAuNTQ2ODc1IDE1Mi4wODk4NDQgMjcwLjg4NjcxOSBDIDE1Mi40MTc5NjkgMjcxLjIxNDg0NCAxNTIuNTkzNzUgMjcyLjA3MDMxMiAxNTIuNTkzNzUgMjczLjQ0MTQwNiBMIDE1Mi41OTM3NSAyOTEuMDkzNzUgQyAxNTIuNTkzNzUgMjk0LjY5MTQwNiAxNTMuODEyNSAyOTcuNDg4MjgxIDE1Ni4yNjU2MjUgMjk5LjQ2ODc1IEMgMTU4LjcxODc1IDMwMS40Mzc1IDE2Mi4xNzk2ODggMzAyLjQxMDE1NiAxNjYuNjQ4NDM4IDMwMi40MTAxNTYgWiBNIDE2Ni42NDg0MzggMzAyLjQxMDE1NiAiLz4KPHBhdGggc3R5bGU9IiBzdHJva2U6bm9uZTtmaWxsLXJ1bGU6bm9uemVybztmaWxsOnJnYigwJSw0NC43MDU4ODIlLDgwLjc4NDMxNCUpO2ZpbGwtb3BhY2l0eToxOyIgZD0iTSAzNDAuNDUzMTI1IDMwOC4xNjAxNTYgTCAzNjMuNDgwNDY5IDMyMy40NTcwMzEgTCAzNjYuMzM5ODQ0IDMxOS4wMDc4MTIgTCAzNDMuMzAwNzgxIDMwMy43MjI2NTYgWiBNIDM0MC40NTMxMjUgMzA4LjE2MDE1NiAiLz4KPHBhdGggc3R5bGU9IiBzdHJva2U6bm9uZTtmaWxsLXJ1bGU6bm9uemVybztmaWxsOnJnYigwJSw0NC43MDU4ODIlLDgwLjc4NDMxNCUpO2ZpbGwtb3BhY2l0eToxOyIgZD0iTSAyMTguNTE5NTMxIDM2Ny4wMTE3MTkgTCAyMDkuOTU3MDMxIDM5NC40OTIxODggTCAyMTUuMTA5Mzc1IDM5NC44MDg1OTQgTCAyMTYuODkwNjI1IDM4OC43MDMxMjUgTCAyMjQuMDExNzE5IDM4OS4xMzY3MTkgTCAyMjUuMDMxMjUgMzk1LjQwNjI1IEwgMjMwLjUyMzQzOCAzOTUuNzQ2MDk0IEwgMjI1LjQwNjI1IDM2Ny40MzM1OTQgWiBNIDIxOC4xNzk2ODggMzg0LjQ3NjU2MiBMIDIyMS4yNzczNDQgMzcyLjU2MjUgTCAyMjEuMzQ3NjU2IDM3Mi41NzQyMTkgTCAyMjMuMTY3OTY5IDM4NC43ODEyNSBaIE0gMjE4LjE3OTY4OCAzODQuNDc2NTYyICIvPgo8cGF0aCBzdHlsZT0iIHN0cm9rZTpub25lO2ZpbGwtcnVsZTpub256ZXJvO2ZpbGw6cmdiKDAlLDQ0LjcwNTg4MiUsODAuNzg0MzE0JSk7ZmlsbC1vcGFjaXR5OjE7IiBkPSJNIDM0Ni45MTQwNjIgMzIzLjM2MzI4MSBMIDM0Ni44NTU0NjkgMzIzLjMxNjQwNiBDIDM0OC41MTE3MTkgMzIwLjI2MTcxOSAzNDcuMjUzOTA2IDMxNy41NzgxMjUgMzQ0LjUyMzQzOCAzMTUuMzUxNTYyIEMgMzQwLjg3NSAzMTIuMzU1NDY5IDMzNy40ODQzNzUgMzEyLjU1NDY4OCAzMzUuMjQyMTg4IDMxNS4zNzUgTCAzMjkuMTY3OTY5IDMyMy4wMTE3MTkgTCAzNTAuNTUwNzgxIDM0MC41ODU5MzggTCAzNTMuODM1OTM4IDMzNi40NjA5MzggTCAzNDQuOTgwNDY5IDMyOS4xNzU3ODEgTCAzNDUuODI0MjE5IDMyOC4xMDkzNzUgQyAzNDguMzQ3NjU2IDMyNC45MzM1OTQgMzUwLjMzOTg0NCAzMjYuOTM3NSAzNTIuODg2NzE5IDMyOS4wMjM0MzggQyAzNTQuMjY5NTMxIDMzMC4xNjAxNTYgMzU1LjY0NDUzMSAzMzEuNDYwOTM4IDM1Ny4zNzg5MDYgMzMxLjk4NDM3NSBMIDM2MC42MDU0NjkgMzI3LjkzMzU5NCBDIDM1OS40MTAxNTYgMzI3LjU5Mzc1IDM1NS4zMTI1IDMyNC4zNTkzNzUgMzUzLjk1MzEyNSAzMjMuMjQ2MDk0IEMgMzUwLjExNzE4OCAzMjAuMDg1OTM4IDM0Ny43NDYwOTQgMzIyLjU2NjQwNiAzNDYuOTE0MDYyIDMyMy4zNjMyODEgWiBNIDM0My4xNjAxNTYgMzI0LjY0MDYyNSBMIDM0MS43MDcwMzEgMzI2LjQ4MDQ2OSBMIDMzNS43NDYwOTQgMzIxLjU4NTkzOCBMIDMzNy4yMTQ4NDQgMzE5Ljc0NjA5NCBDIDMzOC4yNjk1MzEgMzE4LjQzMzU5NCAzMzkuNjY0MDYyIDMxOC4yNjk1MzEgMzQxLjcwNzAzMSAzMTkuOTQ1MzEyIEMgMzQzLjA2NjQwNiAzMjEuMDcwMzEyIDM0NC40NzY1NjIgMzIzIDM0My4xNjAxNTYgMzI0LjY0MDYyNSBaIE0gMzQzLjE2MDE1NiAzMjQuNjQwNjI1ICIvPgo8cGF0aCBzdHlsZT0iIHN0cm9rZTpub25lO2ZpbGwtcnVsZTpub256ZXJvO2ZpbGw6cmdiKDAlLDQ0LjcwNTg4MiUsODAuNzg0MzE0JSk7ZmlsbC1vcGFjaXR5OjE7IiBkPSJNIDMwOS42MzI4MTIgMzQwLjE2NDA2MiBDIDMwMi43MjY1NjIgMzQ1LjQxMDE1NiAzMDYuODc4OTA2IDM1MS4wNDI5NjkgMzExLjI0MjE4OCAzNTYuOTcyNjU2IEMgMzE1LjU1ODU5NCAzNjIuODM5ODQ0IDMxOS43Njk1MzEgMzY4LjU0Mjk2OSAzMjYuNjY3OTY5IDM2My4yODUxNTYgQyAzMzMuNTc4MTI1IDM1OC4wMzkwNjIgMzI5LjM3ODkwNiAzNTIuMzQzNzUgMzI1LjA3NDIxOSAzNDYuNDc2NTYyIEMgMzIwLjY4MzU5NCAzNDAuNTUwNzgxIDMxNi41MzEyNSAzMzQuOTE0MDYyIDMwOS42MzI4MTIgMzQwLjE2NDA2MiBaIE0gMzI0LjIwMzEyNSAzNTkuOTMzNTk0IEMgMzIxLjg0NzY1NiAzNjEuNzI2NTYyIDMxOS43MTA5MzggMzU5LjQ3NjU2MiAzMTUuNDg4MjgxIDM1My43NSBDIDMxMS4yNzczNDQgMzQ4IDMwOS43NSAzNDUuMzA0Njg4IDMxMi4wOTc2NTYgMzQzLjUxMTcxOSBDIDMxNC40NTcwMzEgMzQxLjcxODc1IDMxNi42MDE1NjIgMzQzLjk2ODc1IDMyMC44MTI1IDM0OS42OTkyMTkgQyAzMjUuMDM1MTU2IDM1NS40MjU3ODEgMzI2LjU1MDc4MSAzNTguMTQ0NTMxIDMyNC4yMDMxMjUgMzU5LjkzMzU5NCBaIE0gMzI0LjIwMzEyNSAzNTkuOTMzNTk0ICIvPgo8cGF0aCBzdHlsZT0iIHN0cm9rZTpub25lO2ZpbGwtcnVsZTpub256ZXJvO2ZpbGw6cmdiKDAlLDQ0LjcwNTg4MiUsODAuNzg0MzE0JSk7ZmlsbC1vcGFjaXR5OjE7IiBkPSJNIDM3NS42NTYyNSAyNTQuODk4NDM4IEMgMzY3LjI2OTUzMSAyNTMuMDU4NTk0IDM2Mi4wODIwMzEgMjUzLjI2OTUzMSAzNjAuNjQwNjI1IDI2MC4wODU5MzggTCAzNTguNzk2ODc1IDI2OC43NTM5MDYgTCAzODUuNjk1MzEyIDI3NC42MjUgTCAzODcuNDkyMTg4IDI2Ni4xNTYyNSBDIDM4OS4zNzg5MDYgMjU3LjI4OTA2MiAzNzkuNzg1MTU2IDI1NS44MDA3ODEgMzc1LjY1NjI1IDI1NC44OTg0MzggWiBNIDM4My4yMTA5MzggMjY2LjAxNTYyNSBMIDM4Mi42NzE4NzUgMjY4LjUzMTI1IEwgMzY0LjA0Mjk2OSAyNjQuNDY4NzUgTCAzNjQuNjE3MTg4IDI2MS43ODUxNTYgQyAzNjUuMzc4OTA2IDI1OC4xNjc5NjkgMzY5Ljc0MjE4OCAyNTkuMTEzMjgxIDM3NC43MDcwMzEgMjYwLjE5MTQwNiBDIDM4MS40Mzc1IDI2MS42Njc5NjkgMzgzLjg2NzE4OCAyNjIuODM5ODQ0IDM4My4yMTA5MzggMjY2LjAxNTYyNSBaIE0gMzgzLjIxMDkzOCAyNjYuMDE1NjI1ICIvPgo8cGF0aCBzdHlsZT0iIHN0cm9rZTpub25lO2ZpbGwtcnVsZTpub256ZXJvO2ZpbGw6cmdiKDAlLDQ0LjcwNTg4MiUsODAuNzg0MzE0JSk7ZmlsbC1vcGFjaXR5OjE7IiBkPSJNIDM0OC43ODEyNSAxNjkuNjkxNDA2IEwgMzY1Ljk4ODI4MSAxNjEuMzg2NzE5IEwgMzY2LjAxMTcxOSAxNjEuNDQ1MzEyIEwgMzUxLjY1NjI1IDE3NS44NTE1NjIgTCAzNTQuNjkxNDA2IDE4Mi4zNDM3NSBMIDM3OS41MzkwNjIgMTcwLjM0NzY1NiBMIDM3Ny40NDkyMTkgMTY1Ljg2MzI4MSBMIDM1OS4yNjk1MzEgMTc0LjYzNjcxOSBMIDM1OS4yNDIxODggMTc0LjU3ODEyNSBMIDM3NC40ODQzNzUgMTU5LjUzNTE1NiBMIDM3MS41MjczNDQgMTUzLjIxMDkzOCBMIDM0Ni42Nzk2ODggMTY1LjIwNzAzMSBaIE0gMzQ4Ljc4MTI1IDE2OS42OTE0MDYgIi8+CjxwYXRoIHN0eWxlPSIgc3Ryb2tlOm5vbmU7ZmlsbC1ydWxlOm5vbnplcm87ZmlsbDpyZ2IoMCUsNDQuNzA1ODgyJSw4MC43ODQzMTQlKTtmaWxsLW9wYWNpdHk6MTsiIGQ9Ik0gMzY1LjI5Njg3NSAyOTEuNzczNDM4IEMgMzU4LjgwODU5NCAyODguNDIxODc1IDM1Mi42Mjg5MDYgMjg1LjIyNjU2MiAzNDguNzEwOTM4IDI5My4wMjczNDQgQyAzNDQuODA0Njg4IDMwMC44Mzk4NDQgMzUwLjk3MjY1NiAzMDQuMDQ2ODc1IDM1Ny40NzI2NTYgMzA3LjM4NjcxOSBDIDM2My44OTA2MjUgMzEwLjcwMzEyNSAzNzAuMTQwNjI1IDMxMy45MjE4NzUgMzc0LjA0Njg3NSAzMDYuMTA5Mzc1IEMgMzc3Ljk1MzEyNSAyOTguMjk2ODc1IDM3MS43MTQ4NDQgMjk1LjA3NDIxOSAzNjUuMjk2ODc1IDI5MS43NzM0MzggWiBNIDM3MC4zODY3MTkgMzA0LjIyMjY1NiBDIDM2OS4wNTA3ODEgMzA2Ljg5NDUzMSAzNjYuMTUyMzQ0IDMwNS44MjgxMjUgMzU5Ljg3ODkwNiAzMDIuNTg1OTM4IEMgMzUzLjYwMTU2MiAyOTkuMzM5ODQ0IDM1MS4wNDI5NjkgMjk3LjU5Mzc1IDM1Mi4zODI4MTIgMjk0LjkyMTg3NSBDIDM1My43MTg3NSAyOTIuMjUzOTA2IDM1Ni42MDU0NjkgMjkzLjMyMDMxMiAzNjIuODkwNjI1IDI5Ni41NjI1IEMgMzY5LjE2Nzk2OSAyOTkuODA4NTk0IDM3MS43MTQ4NDQgMzAxLjU2NjQwNiAzNzAuMzg2NzE5IDMwNC4yMjI2NTYgWiBNIDM3MC4zODY3MTkgMzA0LjIyMjY1NiAiLz4KPHBhdGggc3R5bGU9IiBzdHJva2U6bm9uZTtmaWxsLXJ1bGU6bm9uemVybztmaWxsOnJnYigwJSw0NC43MDU4ODIlLDgwLjc4NDMxNCUpO2ZpbGwtb3BhY2l0eToxOyIgZD0iTSAzODYuOTE3OTY5IDIzNi42NjAxNTYgTCAzODYuMjUgMjQ1LjQ2ODc1IEwgMzc4LjIzNDM3NSAyNDQuODQ3NjU2IEwgMzc4LjgyNDIxOSAyMzYuOTg4MjgxIEwgMzc0LjYxMzI4MSAyMzYuNjYwMTU2IEwgMzc0LjAxMTcxOSAyNDQuNTA3ODEyIEwgMzY3LjI1NzgxMiAyNDMuOTkyMTg4IEwgMzY3Ljg5MDYyNSAyMzUuNDY0ODQ0IEwgMzYzLjY3OTY4OCAyMzUuMTI1IEwgMzYyLjY0NDUzMSAyNDguOTYwOTM4IEwgMzkwLjA3NDIxOSAyNTEuMDg5ODQ0IEwgMzkxLjE0MDYyNSAyMzYuOTg4MjgxIFogTSAzODYuOTE3OTY5IDIzNi42NjAxNTYgIi8+CjxwYXRoIHN0eWxlPSIgc3Ryb2tlOm5vbmU7ZmlsbC1ydWxlOm5vbnplcm87ZmlsbDpyZ2IoMCUsNDQuNzA1ODgyJSw4MC43ODQzMTQlKTtmaWxsLW9wYWNpdHk6MTsiIGQ9Ik0gMzgxLjg1OTM3NSAyMDEuMzIwMzEyIEwgMzYwLjk5MjE4OCAyMDQuNTUwNzgxIEwgMzYxLjc3NzM0NCAyMDkuODAwNzgxIEwgMzgzLjAzNTE1NiAyMDYuNTE5NTMxIEMgMzg0LjE5NTMxMiAyMDYuMzQzNzUgMzg1LjQ5NjA5NCAyMDcgMzg1LjY3MTg3NSAyMDguMTcxODc1IEMgMzg2LjA4NTkzOCAyMTAuOTI1NzgxIDM4Mi43NzczNDQgMjEwLjk3MjY1NiAzODAuNTkzNzUgMjExLjMwMDc4MSBMIDM4MS40MDIzNDQgMjE2LjY2NDA2MiBDIDM4Ny41NzQyMTkgMjE1LjcwMzEyNSAzOTAuODQ3NjU2IDIxNC44ODI4MTIgMzg5Ljc0NjA5NCAyMDcuNTM5MDYyIEMgMzg5LjE3OTY4OCAyMDMuODI0MjE5IDM4Ni42MTMyODEgMjAwLjU4MjAzMSAzODEuODU5Mzc1IDIwMS4zMjAzMTIgWiBNIDM4MS44NTkzNzUgMjAxLjMyMDMxMiAiLz4KPHBhdGggc3R5bGU9IiBzdHJva2U6bm9uZTtmaWxsLXJ1bGU6bm9uemVybztmaWxsOnJnYigwJSw0NC43MDU4ODIlLDgwLjc4NDMxNCUpO2ZpbGwtb3BhY2l0eToxOyIgZD0iTSAzNTkuMDQyOTY5IDE5Ni43MTQ4NDQgTCAzODcuMzg2NzE5IDE5NS41NDI5NjkgTCAzODUuOTIxODc1IDE5MC41MTk1MzEgTCAzNzkuNjY3OTY5IDE5MC44OTQ1MzEgTCAzNzcuNjQ4NDM4IDE4My45Mzc1IEwgMzgzLjEwNTQ2OSAxODAuODQzNzUgTCAzODEuNTQyOTY5IDE3NS40Njg3NSBMIDM1Ny4wNzQyMTkgMTkwLjAwMzkwNiBaIE0gMzczLjkxNzk2OSAxODYuMjMwNDY5IEwgMzc1LjMzOTg0NCAxOTEuMDkzNzUgTCAzNjMuMjU3ODEyIDE5Mi4xODM1OTQgTCAzNjMuMjM0Mzc1IDE5Mi4xMjUgWiBNIDM3My45MTc5NjkgMTg2LjIzMDQ2OSAiLz4KPHBhdGggc3R5bGU9IiBzdHJva2U6bm9uZTtmaWxsLXJ1bGU6bm9uemVybztmaWxsOnJnYigwJSw0NC43MDU4ODIlLDgwLjc4NDMxNCUpO2ZpbGwtb3BhY2l0eToxOyIgZD0iTSAyOTMuNTk3NjU2IDM1MS4xNDg0MzggTCAyODUuOTE0MDYyIDM1NS4zNTU0NjkgTCAyOTguOTYwOTM4IDM3OS45NjQ4NDQgTCAzMDYuNDU3MDMxIDM3NS44NTU0NjkgQyAzMTQuMzI4MTI1IDM3MS41NTQ2ODggMzA5LjIyMjY1NiAzNjMuMTc5Njg4IDMwNy4yMTg3NSAzNTkuNDA2MjUgQyAzMDMuMTYwMTU2IDM1MS43MjI2NTYgMjk5LjY0MDYyNSAzNDcuODQ3NjU2IDI5My41OTc2NTYgMzUxLjE0ODQzOCBaIE0gMzAzLjc4MTI1IDM3Mi40NDUzMTIgTCAzMDEuNTUwNzgxIDM3My42NjQwNjIgTCAyOTIuNTE5NTMxIDM1Ni42MDkzNzUgTCAyOTQuOTAyMzQ0IDM1NS4zMDg1OTQgQyAyOTguMTAxNTYyIDM1My41NTA3ODEgMzAwLjIxNDg0NCAzNTcuNTM1MTU2IDMwMi42MjEwOTQgMzYyLjA3ODEyNSBDIDMwNS44Nzg5MDYgMzY4LjI1MzkwNiAzMDYuNTk3NjU2IDM3MC45MTAxNTYgMzAzLjc4MTI1IDM3Mi40NDUzMTIgWiBNIDMwMy43ODEyNSAzNzIuNDQ1MzEyICIvPgo8cGF0aCBzdHlsZT0iIHN0cm9rZTpub25lO2ZpbGwtcnVsZTpub256ZXJvO2ZpbGw6cmdiKDAlLDQ0LjcwNTg4MiUsODAuNzg0MzE0JSk7ZmlsbC1vcGFjaXR5OjE7IiBkPSJNIDMzNS41NTg1OTQgMTQ4Ljc4MTI1IEwgMzU2Ljk0NTMxMiAxMzEuMjEwOTM4IEwgMzUzLjY2MDE1NiAxMjcuMDg5ODQ0IEwgMzMyLjI2MTcxOSAxNDQuNjYwMTU2IFogTSAzMzUuNTU4NTk0IDE0OC43ODEyNSAiLz4KPHBhdGggc3R5bGU9IiBzdHJva2U6bm9uZTtmaWxsLXJ1bGU6bm9uemVybztmaWxsOnJnYigwJSw0NC43MDU4ODIlLDgwLjc4NDMxNCUpO2ZpbGwtb3BhY2l0eToxOyIgZD0iTSAyNDIuMTcxODc1IDM2Ni45MTc5NjkgTCAyMzMuNDc2NTYyIDM2Ny42Nzk2ODggTCAyMzUuODQ3NjU2IDM5NS41MjM0MzggTCAyNDQuMzUxNTYyIDM5NC43NzM0MzggQyAyNTMuMjU3ODEyIDM5My45ODgyODEgMjUxLjgyNDIxOSAzODQuMjQyMTg4IDI1MS40NzI2NTYgMzc5Ljk2NDg0NCBDIDI1MC43MTA5MzggMzcxLjI5Njg3NSAyNDkuMDExNzE5IDM2Ni4zMjAzMTIgMjQyLjE3MTg3NSAzNjYuOTE3OTY5IFogTSAyNDMuMjAzMTI1IDM5MC41NjY0MDYgTCAyNDAuNjc5Njg4IDM5MC43ODkwNjIgTCAyMzkuMDM5MDYyIDM3MS41MDc4MTIgTCAyNDEuNzM4MjgxIDM3MS4yNjE3MTkgQyAyNDUuMzUxNTYyIDM3MC45NDUzMTIgMjQ1LjczODI4MSAzNzUuNDU3MDMxIDI0Ni4xNzE4NzUgMzgwLjU4NTkzOCBDIDI0Ni43ODEyNSAzODcuNTU0Njg4IDI0Ni4zODI4MTIgMzkwLjI4NTE1NiAyNDMuMjAzMTI1IDM5MC41NjY0MDYgWiBNIDI0My4yMDMxMjUgMzkwLjU2NjQwNiAiLz4KPHBhdGggc3R5bGU9IiBzdHJva2U6bm9uZTtmaWxsLXJ1bGU6bm9uemVybztmaWxsOnJnYigwJSw0NC43MDU4ODIlLDgwLjc4NDMxNCUpO2ZpbGwtb3BhY2l0eToxOyIgZD0iTSAyNjEuMTc1NzgxIDM2My4yODUxNTYgQyAyNTIuNzg1MTU2IDM2NS4zMjQyMTkgMjU0LjM5NDUzMSAzNzIuMTc1NzgxIDI1Ni4wOTM3NSAzNzkuMzY3MTg4IEMgMjU3Ljc3MzQzOCAzODYuNDY4NzUgMjU5LjQwMjM0NCAzOTMuNDAyMzQ0IDI2Ny43ODkwNjIgMzkxLjM2MzI4MSBDIDI3Ni4xNzk2ODggMzg5LjMxMjUgMjc0LjU0Njg3NSAzODIuNDAyMzQ0IDI3Mi44NzEwOTQgMzc1LjI4MTI1IEMgMjcxLjE3OTY4OCAzNjguMTAxNTYyIDI2OS41NTA3ODEgMzYxLjI0NjA5NCAyNjEuMTc1NzgxIDM2My4yODUxNTYgWiBNIDI2Ni44MjgxMjUgMzg3LjI5Njg3NSBDIDI2My45NjQ4NDQgMzg4IDI2Mi44ODY3MTkgMzg1LjA3NDIxOSAyNjEuMjQ2MDk0IDM3OC4xMDE1NjIgQyAyNTkuNjAxNTYyIDM3MS4xNDQ1MzEgMjU5LjI1IDM2OC4wNDI5NjkgMjYyLjEyNSAzNjcuMzUxNTYyIEMgMjY0Ljk4ODI4MSAzNjYuNjQ4NDM4IDI2Ni4wNzgxMjUgMzY5LjU3NDIxOSAyNjcuNzA3MDMxIDM3Ni41NDY4NzUgQyAyNjkuMzYzMjgxIDM4My41MDM5MDYgMjY5LjcwMzEyNSAzODYuNjA5Mzc1IDI2Ni44MjgxMjUgMzg3LjI5Njg3NSBaIE0gMjY2LjgyODEyNSAzODcuMjk2ODc1ICIvPgo8cGF0aCBzdHlsZT0iIHN0cm9rZTpub25lO2ZpbGwtcnVsZTpub256ZXJvO2ZpbGw6cmdiKDAlLDQ0LjcwNTg4MiUsODAuNzg0MzE0JSk7ZmlsbC1vcGFjaXR5OjE7IiBkPSJNIDI3NS42OTkyMTkgMjkxLjE1MjM0NCBMIDI3Mi4zNDM3NSAyOTEuMTUyMzQ0IEMgMjcyLjM0Mzc1IDI5MS4yOTI5NjkgMjcyLjM1NTQ2OSAyOTEuNTAzOTA2IDI3Mi4zNjcxODggMjkxLjc5Njg3NSBDIDI3Mi4zNzg5MDYgMjkyLjA2NjQwNiAyNzIuMzkwNjI1IDI5Mi4yNzczNDQgMjcyLjM5MDYyNSAyOTIuMzk0NTMxIEMgMjcyLjM5MDYyNSAyOTMuNjM2NzE5IDI3Mi4yNzM0MzggMjk0LjU3NDIxOSAyNzIuMDYyNSAyOTUuMTc5Njg4IEMgMjcxLjg1MTU2MiAyOTUuODAwNzgxIDI3MS41MTk1MzEgMjk2LjA5Mzc1IDI3MS4wNzQyMTkgMjk2LjA5Mzc1IEMgMjcwLjYwNTQ2OSAyOTYuMDkzNzUgMjcwLjI3NzM0NCAyOTUuODQ3NjU2IDI3MC4wNzgxMjUgMjk1LjM0Mzc1IEMgMjY5Ljg3ODkwNiAyOTQuODU1NDY5IDI2OS43ODUxNTYgMjkzLjk1MzEyNSAyNjkuNzg1MTU2IDI5Mi42NjQwNjIgQyAyNjkuNzg1MTU2IDI4OC4zNzUgMjY5LjM4NjcxOSAyODUuNjM2NzE5IDI2OC41ODk4NDQgMjg0LjQ0MTQwNiBDIDI2Ny43ODkwNjIgMjgzLjI1NzgxMiAyNjYuMjc3MzQ0IDI4Mi40OTYwOTQgMjY0LjAyMzQzOCAyODIuMjAzMTI1IEMgMjY2LjI2NTYyNSAyODEuNzEwOTM4IDI2Ny45NzY1NjIgMjgwLjc2MTcxOSAyNjkuMTk5MjE5IDI3OS4zNjcxODggQyAyNzAuNDE3OTY5IDI3Ny45OTYwOTQgMjcxLjAyNzM0NCAyNzYuMjg5MDYyIDI3MS4wMjczNDQgMjc0LjI3MzQzOCBDIDI3MS4wMjczNDQgMjcxLjI2MTcxOSAyNzAuMDQyOTY5IDI2OS4wMTE3MTkgMjY4LjA2MjUgMjY3LjUyMzQzOCBDIDI2Ni4wNzgxMjUgMjY2LjAzOTA2MiAyNjMuMDg1OTM4IDI2NS4zMDA3ODEgMjU5LjA2MjUgMjY1LjMwMDc4MSBMIDIzNi4zMjgxMjUgMjY1LjMwMDc4MSBMIDIzNi4zMjgxMjUgMjcwLjQwNjI1IEwgMjM3Ljk4NDM3NSAyNzAuNDA2MjUgQyAyMzkuMTU2MjUgMjcwLjQwNjI1IDIzOS44OTQ1MzEgMjcwLjU3MDMxMiAyNDAuMjIyNjU2IDI3MC44OTg0MzggQyAyNDAuNTUwNzgxIDI3MS4yMjY1NjIgMjQwLjcwMzEyNSAyNzIuMDgyMDMxIDI0MC43MDMxMjUgMjczLjQ2NDg0NCBMIDI0MC43MDMxMjUgMjkzLjA5NzY1NiBDIDI0MC43MDMxMjUgMjk0LjUwMzkwNiAyNDAuNTM5MDYyIDI5NS4zNzg5MDYgMjQwLjIxMDkzOCAyOTUuNzA3MDMxIEMgMjM5Ljg4MjgxMiAyOTYuMDQ2ODc1IDIzOS4xMzI4MTIgMjk2LjIxMDkzOCAyMzcuOTg0Mzc1IDI5Ni4yMTA5MzggTCAyMzYuMzI4MTI1IDI5Ni4yMTA5MzggTCAyMzYuMzI4MTI1IDMwMS4zMzIwMzEgTCAyNTYuMTg3NSAzMDEuMzMyMDMxIEwgMjU2LjE4NzUgMjk2LjIxMDkzOCBMIDI1NC4zMjQyMTkgMjk2LjIxMDkzOCBDIDI1My4xODc1IDI5Ni4yMTA5MzggMjUyLjQ1NzAzMSAyOTYuMDM1MTU2IDI1Mi4xMTcxODggMjk1LjcwNzAzMSBDIDI1MS43ODkwNjIgMjk1LjM3ODkwNiAyNTEuNjI1IDI5NC41MTU2MjUgMjUxLjYyNSAyOTMuMDk3NjU2IEwgMjUxLjYyNSAyODUuMDUwNzgxIEwgMjU0LjU3MDMxMiAyODUuMDUwNzgxIEMgMjU2LjQyMTg3NSAyODUuMDUwNzgxIDI1Ny42NDQ1MzEgMjg1LjM3ODkwNiAyNTguMjE4NzUgMjg2LjAzMTI1IEMgMjU4LjgxNjQwNiAyODYuNjc1NzgxIDI1OS4wOTc2NTYgMjg4LjIxMDkzOCAyNTkuMDk3NjU2IDI5MC42MDE1NjIgTCAyNTkuMDk3NjU2IDI5My42MjUgQyAyNTkuMDk3NjU2IDI5Ni42MDkzNzUgMjU5Ljc3NzM0NCAyOTguNzc3MzQ0IDI2MS4xNTIzNDQgMzAwLjE0ODQzOCBDIDI2Mi41MTE3MTkgMzAxLjUwNzgxMiAyNjQuNzA3MDMxIDMwMi4xOTkyMTkgMjY3LjY4MzU5NCAzMDIuMTk5MjE5IEMgMjcwLjUgMzAyLjE5OTIxOSAyNzIuNTQyOTY5IDMwMS40Mzc1IDI3My44MDg1OTQgMjk5LjkxNDA2MiBDIDI3NS4wNzQyMTkgMjk4LjM5MDYyNSAyNzUuNzEwOTM4IDI5NS45NDE0MDYgMjc1LjcxMDkzOCAyOTIuNTgyMDMxIEMgMjc1LjcxMDkzOCAyOTIuNDI5Njg4IDI3NS42OTkyMTkgMjkyLjE5NTMxMiAyNzUuNjg3NSAyOTEuODY3MTg4IEMgMjc1LjcxMDkzOCAyOTEuNTM5MDYyIDI3NS42OTkyMTkgMjkxLjMwNDY4OCAyNzUuNjk5MjE5IDI5MS4xNTIzNDQgWiBNIDI1OC42OTkyMTkgMjc5LjA4NTkzOCBDIDI1Ny44Nzg5MDYgMjc5Ljc4OTA2MiAyNTYuNDQ1MzEyIDI4MC4xNTIzNDQgMjU0LjQyOTY4OCAyODAuMTUyMzQ0IEwgMjUxLjU0Mjk2OSAyODAuMTUyMzQ0IEwgMjUxLjU0Mjk2OSAyNzAuNjQwNjI1IEwgMjU0Ljc4MTI1IDI3MC42NDA2MjUgQyAyNTYuNjk1MzEyIDI3MC42NDA2MjUgMjU4LjAzMTI1IDI3MS4wMDM5MDYgMjU4Ljc4MTI1IDI3MS43MzA0NjkgQyAyNTkuNTQyOTY5IDI3Mi40Njg3NSAyNTkuOTI5Njg4IDI3My43MzQzNzUgMjU5LjkyOTY4OCAyNzUuNTUwNzgxIEMgMjU5LjkyOTY4OCAyNzcuMjEwOTM4IDI1OS41MTk1MzEgMjc4LjM4MjgxMiAyNTguNjk5MjE5IDI3OS4wODU5MzggWiBNIDI1OC42OTkyMTkgMjc5LjA4NTkzOCAiLz4KPHBhdGggc3R5bGU9IiBzdHJva2U6bm9uZTtmaWxsLXJ1bGU6bm9uemVybztmaWxsOnJnYigwJSw0NC43MDU4ODIlLDgwLjc4NDMxNCUpO2ZpbGwtb3BhY2l0eToxOyIgZD0iTSAzNjEuNDYwOTM4IDE0NS4wMzUxNTYgTCAzNTQuNzYxNzE5IDE0OS41NTQ2ODggTCAzNTAuNDY4NzUgMTQyLjk4NDM3NSBMIDM0Ni45NDkyMTkgMTQ1LjM1MTU2MiBMIDM1MS4yMzA0NjkgMTUxLjkyMTg3NSBMIDM0NS41ODk4NDQgMTU1LjczMDQ2OSBMIDM0MC45MzM1OTQgMTQ4LjYwNTQ2OSBMIDMzNy40MTQwNjIgMTUwLjk3MjY1NiBMIDM0NC45NTcwMzEgMTYyLjUzNTE1NiBMIDM2Ny44OTA2MjUgMTQ3LjA4NTkzOCBMIDM2MC4xODM1OTQgMTM1LjMwMDc4MSBMIDM1Ni42NTIzNDQgMTM3LjY2Nzk2OSBaIE0gMzYxLjQ2MDkzOCAxNDUuMDM1MTU2ICIvPgo8cGF0aCBzdHlsZT0iIHN0cm9rZTpub25lO2ZpbGwtcnVsZTpub256ZXJvO2ZpbGw6cmdiKDAlLDQ0LjcwNTg4MiUsODAuNzg0MzE0JSk7ZmlsbC1vcGFjaXR5OjE7IiBkPSJNIDMwMC42NjAxNTYgMzAxLjU2NjQwNiBDIDMwMi4zODY3MTkgMzAxLjAwMzkwNiAzMDMuODE2NDA2IDMwMC4xMzY3MTkgMzA0Ljk3NjU2MiAyOTguOTc2NTYyIEMgMzA1Ljk4NDM3NSAyOTcuOTgwNDY5IDMwNi43MDMxMjUgMjk2Ljc3MzQzOCAzMDcuMTM2NzE5IDI5NS4zNTU0NjkgQyAzMDcuNTcwMzEyIDI5My45NDE0MDYgMzA3Ljc4MTI1IDI5MS45MTQwNjIgMzA3Ljc4MTI1IDI4OS4yNTM5MDYgTCAzMDcuNzgxMjUgMjczLjE3MTg3NSBDIDMwNy43ODEyNSAyNzEuODU5Mzc1IDMwNy45NTcwMzEgMjcxLjA1MDc4MSAzMDguMjg1MTU2IDI3MC43Njk1MzEgQyAzMDguNjEzMjgxIDI3MC40ODgyODEgMzA5LjMyODEyNSAyNzAuMzU5Mzc1IDMxMC40MjE4NzUgMjcwLjM1OTM3NSBMIDMxMS45NTcwMzEgMjcwLjM1OTM3NSBMIDMxMS45NTcwMzEgMjY1LjMwMDc4MSBMIDI5Mi4yNSAyNjUuMzAwNzgxIEwgMjkyLjI1IDI3MC4zNTkzNzUgTCAyOTQuMDg5ODQ0IDI3MC4zNTkzNzUgQyAyOTUuMjY1NjI1IDI3MC4zNTkzNzUgMjk2LjAwMzkwNiAyNzAuNTIzNDM4IDI5Ni4zMjAzMTIgMjcwLjgzOTg0NCBDIDI5Ni42NDg0MzggMjcxLjE2Nzk2OSAyOTYuODAwNzgxIDI3Mi4wMjM0MzggMjk2LjgwMDc4MSAyNzMuNDQxNDA2IEwgMjk2LjgwMDc4MSAyODguNzI2NTYyIEMgMjk2LjgwMDc4MSAyOTEuOTYwOTM4IDI5Ni40NDkyMTkgMjk0LjExNzE4OCAyOTUuNzQ2MDk0IDI5NS4yMDMxMjUgQyAyOTUuMDQyOTY5IDI5Ni4yNjk1MzEgMjkzLjc4NTE1NiAyOTYuNzk2ODc1IDI5MS45ODA0NjkgMjk2Ljc5Njg3NSBDIDI5MS4wODk4NDQgMjk2Ljc5Njg3NSAyOTAuMzEyNSAyOTYuNTg1OTM4IDI4OS42NTYyNSAyOTYuMTUyMzQ0IEMgMjg5IDI5NS43MTg3NSAyODguNDcyNjU2IDI5NS4wNTA3ODEgMjg4LjA3NDIxOSAyOTQuMTg3NSBDIDI4OC4zMzIwMzEgMjk0LjI0NjA5NCAyODguNTY2NDA2IDI5NC4yODEyNSAyODguNzg5MDYyIDI5NC4zMDQ2ODggQyAyODkuMDIzNDM4IDI5NC4zMjgxMjUgMjg5LjIzNDM3NSAyOTQuMzM5ODQ0IDI4OS40NDUzMTIgMjk0LjMzOTg0NCBDIDI5MC42OTkyMTkgMjk0LjMzOTg0NCAyOTEuNjk5MjE5IDI5My45MDYyNSAyOTIuNDcyNjU2IDI5My4wMjczNDQgQyAyOTMuMjQ2MDk0IDI5Mi4xNDg0MzggMjkzLjYyMTA5NCAyOTAuOTg4MjgxIDI5My42MjEwOTQgMjg5LjU1ODU5NCBDIDI5My42MjEwOTQgMjg4LjA0Njg3NSAyOTMuMTk5MjE5IDI4Ni44MjgxMjUgMjkyLjM0Mzc1IDI4NS45Mzc1IEMgMjkxLjUgMjg1LjAzOTA2MiAyOTAuMzQ3NjU2IDI4NC41OTM3NSAyODguODgyODEyIDI4NC41OTM3NSBDIDI4Ni45MzM1OTQgMjg0LjU5Mzc1IDI4NS4zMzk4NDQgMjg1LjI5Njg3NSAyODQuMTMyODEyIDI4Ni42OTkyMTkgQyAyODIuOTEwMTU2IDI4OC4xMDU0NjkgMjgyLjMwMDc4MSAyODkuOTQ1MzEyIDI4Mi4zMDA3ODEgMjkyLjIwNzAzMSBDIDI4Mi4zMDA3ODEgMjk1LjIwMzEyNSAyODMuNDQxNDA2IDI5Ny42NDA2MjUgMjg1LjcxNDg0NCAyOTkuNTUwNzgxIEMgMjg4LjAwMzkwNiAzMDEuNDYwOTM4IDI5MC45NjA5MzggMzAyLjM5ODQzOCAyOTQuNjA1NDY5IDMwMi4zOTg0MzggQyAyOTYuOTA2MjUgMzAyLjQxMDE1NiAyOTguOTM3NSAzMDIuMTQwNjI1IDMwMC42NjAxNTYgMzAxLjU2NjQwNiBaIE0gMzAwLjY2MDE1NiAzMDEuNTY2NDA2ICIvPgo8L2c+Cjwvc3ZnPgo="
st.markdown(
    f"""
    <div class="footer-content-wrapper">
        <p class="footer-text">Developed by Núcleo de Estudos em Economia Empírica - 2025</p>
        <img src="{logo_uerj_base64_string}" class="footer-logo">
    </div>
    """,
    unsafe_allow_html=True
)