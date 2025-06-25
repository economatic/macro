import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
import requests

# --- Função para carregar dados do BCB ---
@st.cache_data
def fetch_bcb_series(sgs_code, start_date_obj, end_date_obj, col_name):
    start_date_str_bcb = start_date_obj.strftime('%d/%m/%Y')
    end_date_str_bcb = end_date_obj.strftime('%d/%m/%Y')
    bcb_api_url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{sgs_code}/dados?formato=json&dataInicial={start_date_str_bcb}&dataFinal={end_date_str_bcb}"

    try:
        response = requests.get(bcb_api_url)
        response.raise_for_status()
        raw_data = response.json()

        if raw_data:
            df = pd.DataFrame(raw_data)
            df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
            df.rename(columns={'data': 'Date', 'valor': col_name}, inplace=True)
            df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
            df.set_index('Date', inplace=True)
            df.dropna(subset=[col_name], inplace=True)
            return df
        else:
            st.warning(f"No data found for {col_name} for the selected period.")
            return pd.DataFrame(columns=['Date', col_name]).set_index('Date')
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching {col_name} data from BCB API: {e}")
        return pd.DataFrame(columns=['Date', col_name]).set_index('Date')
    except ValueError as e:
        st.error(f"Error decoding {col_name} data JSON: {e}. Raw response: {response.text if 'response' in locals() else 'N/A'}")
        return pd.DataFrame(columns=['Date', col_name]).set_index('Date')
    except Exception as e:
        st.error(f"An unexpected error occurred while loading {col_name} data: {e}")
        return pd.DataFrame(columns=['Date', col_name]).set_index('Date')

# --- Função para carregar dados do IBGE SIDRA ---
@st.cache_data
def fetch_ibge_sidra_series(table_code, variable_code, start_date_obj, end_date_obj, col_name, locality='N1', classification=''):
    # Adjust start_date_obj to fetch enough data for rolling calculations if needed
    # For monthly data, fetch 12 months prior for 12M averages
    adjusted_start_date_obj = start_date_obj - timedelta(days=365 * 2) # Fetch 2 years prior for safety

    start_period_ibge = adjusted_start_date_obj.strftime('%Y%m')
    end_period_ibge = end_date_obj.strftime('%Y%m')

    # Base URL for IBGE SIDRA API
    ibge_api_url = f"https://sidra.ibge.gov.br/api/tables/{table_code}/data?variable={variable_code}&locality={locality}&period={start_period_ibge}-{end_period_ibge}&formato=json"
    if classification:
        ibge_api_url += f"&classificacao={classification}"

    try:
        response = requests.get(ibge_api_url)
        response.raise_for_status()
        raw_data = response.json()

        if raw_data and len(raw_data) > 1: # Skip header row
            df = pd.DataFrame(raw_data[1:])
            # Identify period column (usually 'D2C', 'D3C', etc.) and value column ('V')
            period_col = next((col for col in df.columns if col.startswith('D') and 'C' in col), None)
            
            if period_col:
                df.rename(columns={period_col: 'Period', 'V': col_name}, inplace=True)
                df['Date'] = pd.to_datetime(df['Period'], format='%Y%m') # Assuming YYYYMM format

                df[col_name] = df[col_name].str.replace(',', '.', regex=False)
                df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
                df.dropna(subset=[col_name], inplace=True)
                df.set_index('Date', inplace=True)
                # Filter to requested period AFTER calculations
                df = df.loc[start_date_obj:end_date_obj]
                return df[[col_name]]
            else:
                st.warning(f"Could not identify period column for {col_name} from IBGE API. Raw data: {raw_data[:2]}")
                return pd.DataFrame(columns=['Date', col_name]).set_index('Date')
        else:
            st.warning(f"No data found for {col_name} from IBGE API for the selected period.")
            return pd.DataFrame(columns=['Date', col_name]).set_index('Date')
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching {col_name} data from IBGE API: {e}")
        return pd.DataFrame(columns=['Date', col_name]).set_index('Date')
    except ValueError as e:
        st.error(f"Error processing {col_name} data JSON: {e}. Raw response: {response.text if 'response' in locals() else 'N/A'}")
        return pd.DataFrame(columns=['Date', col_name]).set_index('Date')
    except Exception as e:
        st.error(f"An unexpected error occurred while loading {col_name} data: {e}")
        return pd.DataFrame(columns=['Date', col_name]).set_index('Date')


# --- Central Data Loading Function ---
@st.cache_data
def load_national_data(start_date_obj, end_date_obj):
    all_national_dfs = {}

    # 1. Selic (BCB SGS 432)
    selic_df = fetch_bcb_series(432, start_date_obj, end_date_obj, 'Selic (%)')
    if not selic_df.empty:
        all_national_dfs['Selic (%)'] = selic_df

    # 2. IPCA (IBGE SIDRA 1737, Var 2266 - Monthly Variation)
    # This fetches monthly variations. We need to calculate 12M here.
    ipca_monthly_df = fetch_ibge_sidra_series(1737, 2266, start_date_obj, end_date_obj, 'Monthly_IPCA_Variation', classification='C315/7169')
    if not ipca_monthly_df.empty:
        ipca_monthly_df['IPCA_12M_Factor'] = 1 + (ipca_monthly_df['Monthly_IPCA_Variation'] / 100)
        ipca_monthly_df['IPCA 12M'] = (ipca_monthly_df['IPCA_12M_Factor'].rolling(window=12, min_periods=12).apply(lambda x: x.prod() - 1, raw=False) * 100)
        ipca_12m_df = ipca_monthly_df[['IPCA 12M']].dropna()
        if not ipca_12m_df.empty:
            all_national_dfs['IPCA 12M'] = ipca_12m_df
        # You might also want the monthly IPCA as a separate option
        all_national_dfs['IPCA Mensal'] = ipca_monthly_df[['Monthly_IPCA_Variation']]


    # 3. Desemprego (IBGE SIDRA 6738, Var 4099 - Taxa de desocupação)
    desemprego_df = fetch_ibge_sidra_series(6738, 4099, start_date_obj, end_date_obj, 'Taxa de Desocupação (%)', locality='N1/BR')
    if not desemprego_df.empty:
        all_national_dfs['Taxa de Desocupação (%)'] = desemprego_df

    # 4. IBC-Br (BCB SGS 24372)
    ibcbr_df = fetch_bcb_series(24372, start_date_obj, end_date_obj, 'IBC-Br (SA)')
    if not ibcbr_df.empty:
        all_national_dfs['IBC-Br (SA)'] = ibcbr_df

    # 5. IGP-M (BCB SGS 189)
    igpm_df = fetch_bcb_series(189, start_date_obj, end_date_obj, 'IGP-M (%)')
    if not igpm_df.empty:
        all_national_dfs['IGP-M (%)'] = igpm_df

    # --- Simulated Data for other indicators (replace with real APIs later) ---
    # Ensure they are generated for the correct period
    start_dt_for_sim = pd.to_datetime(start_date_obj)
    end_dt_for_sim = pd.to_datetime(end_date_obj)
    dates_for_simulated = pd.to_datetime(pd.date_range(start=start_dt_for_sim, end=end_dt_for_sim, freq='MS'))

    if not dates_for_simulated.empty:
        pib_sim_df = pd.DataFrame({
            'Date': dates_for_simulated,
            'PIB Trimestral (%)': [1.0 + (i%5)*0.1 for i in range(len(dates_for_simulated))] # Quarterly-like
        }).set_index('Date')
        all_national_dfs['PIB Trimestral (%)'] = pib_sim_df

        hiato_produto_sim_df = pd.DataFrame({
            'Date': dates_for_simulated,
            'Hiato do Produto (%)': [0.1 + (i%10)*0.02 - 0.1 for i in range(len(dates_for_simulated))]
        }).set_index('Date')
        all_national_dfs['Hiato do Produto (%)'] = hiato_produto_sim_df

        ipc_sim_df = pd.DataFrame({
            'Date': dates_for_simulated,
            'IPC (%)': [0.3 + (i%6)*0.03 for i in range(len(dates_for_simulated))]
        }).set_index('Date')
        all_national_dfs['IPC (%)'] = ipc_sim_df

        incc_sim_df = pd.DataFrame({
            'Date': dates_for_simulated,
            'INCC (%)': [0.4 + (i%8)*0.04 for i in range(len(dates_for_simulated))]
        }).set_index('Date')
        all_national_dfs['INCC (%)'] = incc_sim_df


    # --- Merge all loaded DataFrames into a single one ---
    # Create a full date range for the merge to ensure all dates are covered
    full_date_range = pd.date_range(start=start_date_obj, end=end_date_obj, freq='MS') # Monthly frequency
    merged_national_df = pd.DataFrame(index=full_date_range)

    for indicator_name, df in all_national_dfs.items():
        if not df.empty:
            # Resample daily/quarterly data to monthly for consistency if needed, e.g., using mean or last
            # For simplicity, if the loaded DF is already monthly, it will just merge.
            # If it's quarterly (like PIB), we need a specific strategy.
            # For this example, we assume most are monthly or will be merged as is.
            # For PIB, you might want to forward-fill or resample to monthly.
            if indicator_name == 'PIB Trimestral (%)': # Specific handling for quarterly data
                 merged_national_df = merged_national_df.merge(df, left_index=True, right_index=True, how='left')
                 merged_national_df[indicator_name] = merged_national_df[indicator_name].ffill() # Fill forward for monthly comparison
            else:
                merged_national_df = merged_national_df.merge(df, left_index=True, right_index=True, how='left')

    merged_national_df.index.name = 'Date'
    merged_national_df.reset_index(inplace=True)

    return merged_national_df

@st.cache_data
def load_regional_data(start_date_obj, end_date_obj):
    regional_data = {}

    start_dt_for_sim = pd.to_datetime(start_date_obj)
    end_dt_for_sim = pd.to_datetime(end_date_obj)

    dates_monthly = pd.to_datetime(pd.date_range(start=start_dt_for_sim, end=end_dt_for_sim, freq='MS'))
    dates_yearly = pd.to_datetime(pd.date_range(start=start_dt_for_sim, end=end_dt_for_sim, freq='YS'))

    if not dates_monthly.empty:
        regional_data['Unemployment_RJ'] = pd.DataFrame({
            'Date': dates_monthly,
            'Value': [9 + (i%8)*0.3 for i in range(len(dates_monthly))]
        })
        regional_data['Unemployment_SP'] = pd.DataFrame({
            'Date': dates_monthly,
            'Value': [7 + (i%6)*0.2 for i in range(len(dates_monthly))]
        })
    else:
        regional_data['Unemployment_RJ'] = pd.DataFrame(columns=['Date', 'Value'])
        regional_data['Unemployment_SP'] = pd.DataFrame(columns=['Date', 'Value'])

    if not dates_yearly.empty:
        regional_data['GDP_SP'] = pd.DataFrame({
            'Date': dates_yearly,
            'Value': [1500 + i*50 + (i%3)*10 for i in range(len(dates_yearly))]
        })
    else:
        regional_data['GDP_SP'] = pd.DataFrame(columns=['Date', 'Value'])

    return regional_data

# --- Streamlit App Layout ---
st.set_page_config(layout="wide")
st.title("Dashboard de Análise Macroeconômica")

# --- Sidebar Elements ---
st.sidebar.header("Navegação")
page_selection = st.sidebar.radio(
    "Escolha o Tipo de Análise:",
    ["Análise Nacional", "Análise Regional"]
)

st.sidebar.header("Período de Análise")
today = date.today()
default_start_date = today - timedelta(days=365 * 5)
default_end_date = today

start_date_input = st.sidebar.date_input("Data de Início", value=default_start_date, key="start_date_picker")
end_date_input = st.sidebar.date_input("Data de Fim", value=default_end_date, key="end_date_picker")

if start_date_input > end_date_input:
    st.sidebar.error("Erro: A data de fim deve ser posterior à data de início.")
    st.stop()

# Load all national data once based on date range
full_national_data_df = load_national_data(start_date_input, end_date_input)
regional_data_loaded = load_regional_data(start_date_input, end_date_input)


# --- Sidebar - Indicadores Nacionais ---
if page_selection == "Análise Nacional":
    st.sidebar.header("Indicadores Nacionais")

    # Get available indicators from the loaded data (excluding 'Date' column)
    available_national_indicators = [col for col in full_national_data_df.columns if col != 'Date']

    # Use st.sidebar.multiselect for multiple selections
    selected_indicators = st.sidebar.multiselect(
        "Selecione os Indicadores para Comparar:",
        options=available_national_indicators,
        default=['Selic (%)', 'IPCA 12M'] if 'Selic (%)' in available_national_indicators and 'IPCA 12M' in available_national_indicators else available_national_indicators[:2], # Default selection
        key="national_indicators_multiselect"
    )

    st.header("Análise Macroeconômica Nacional")

    if selected_indicators:
        # Filter the main DataFrame to include only selected indicators and 'Date'
        df_to_plot = full_national_data_df[['Date'] + selected_indicators].copy()
        
        # Drop rows where ALL selected indicator values are NaN for a cleaner plot
        df_to_plot.dropna(subset=selected_indicators, how='all', inplace=True)

        if not df_to_plot.empty:
            fig = px.line(df_to_plot, x='Date', y=selected_indicators,
                          title='Comparativo de Indicadores Macroeconômicos Nacionais')
            fig.update_traces(mode='lines+markers', marker=dict(size=4))
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig)
            st.write(df_to_plot)
        else:
            st.warning("Nenhum dado disponível para os indicadores e período selecionados.")
    else:
        st.info("Selecione um ou mais indicadores no sidebar para visualizar os dados.")


elif page_selection == "Análise Regional":
    st.header("Análise Macroeconômica Regional")

    all_regions = sorted(list(set([key.split('_')[1] if '_' in key else key for key in regional_data_loaded.keys() if '_' in key])))
    if not all_regions and regional_data_loaded:
        all_regions = sorted(list(regional_data_loaded.keys()))

    st.sidebar.header("Indicadores Regionais")
    region_choice = st.sidebar.selectbox(
        "Escolha uma Região:",
        all_regions,
        key="regional_choice_select"
    )

    available_regional_indicators = []
    if region_choice:
        available_regional_indicators = [
            key for key in regional_data_loaded.keys() if region_choice in key
        ]

    regional_indicator_choice = st.sidebar.selectbox(
        "Escolha um Indicador Regional:",
        available_regional_indicators,
        key="regional_indicator_select"
    )

    if regional_indicator_choice:
        st.subheader(f"Tendência de {regional_indicator_choice} em {region_choice}")
        df_to_plot = regional_data_loaded[regional_indicator_choice]

        if not df_to_plot.empty:
            fig = px.line(df_to_plot, x='Date', y='Value', title=f'{regional_indicator_choice} ao Longo do Tempo em {region_choice}')
            st.plotly_chart(fig)
            st.write(df_to_plot)
        else:
            st.warning("Nenhum dado disponível para o período selecionado para este indicador nesta região.")