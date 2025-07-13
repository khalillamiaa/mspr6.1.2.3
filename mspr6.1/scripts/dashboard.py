import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # Importation nécessaire
from dotenv import load_dotenv
from sqlalchemy import create_engine
import requests

# --- Config Streamlit & Styles ---
st.set_page_config(page_title="Dashboard IA - COVID & Mpox", layout="wide", initial_sidebar_state="expanded")
st.markdown(
    """
    <style>
    .main-header { text-align: center; font-size: 2.5rem; margin-top: 1rem; font-weight: bold; }
    .metric-box { background: rgba(255, 255, 255, 0.05); border-radius: 1rem; padding: 1.25rem; margin-bottom: 1rem; }
    .section-header { font-size: 1.75rem; margin-top: 2rem; font-weight: 600; }
    .stMetric-value { font-size: 1.5rem !important; }
    [data-testid="stSidebar"] { background-color: #1e1e1e !important; color: white !important; }
    .stSidebar label, .stRadio label, .stSelectbox label { color: white !important; font-weight: 500; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Fonctions ---
@st.cache_data
def load_db_table(table_name: str) -> pd.DataFrame:
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(DATABASE_URL)
    df = pd.read_sql(f"SELECT * FROM {table_name};", con=engine)
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    for col in df.columns:
        if col.startswith('country'):
            df.rename(columns={col: 'country'}, inplace=True)
            break
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    return df

@st.cache_data
def load_performance_data(disease: str):
    """Charge les données de performance pour une maladie donnée."""
    try:
        script_dir = os.path.dirname(__file__)
        perf_path = os.path.abspath(os.path.join(script_dir, '..', 'api', f'performance_{disease.lower()}.csv'))
        return pd.read_csv(perf_path)
    except FileNotFoundError:
        return None

def api_request(url: str):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.ConnectionError:
        st.error("Connexion à l'API impossible.", icon="🚨")
        return None

# --- Barre latérale de navigation ---
st.sidebar.title("Navigation")
# --- CORRECTION ICI ---
app_mode = st.sidebar.radio(
    "Choisissez une page",
    ["Analyse Détaillée", "Analyse IA"] # Le nom correspond maintenant à la condition ci-dessous
)
st.sidebar.divider()

# --- Header ---
st.markdown("<div class='main-header'>Dashboard d'Analyse des Pandémies</div>", unsafe_allow_html=True)

# =================================================
# PAGE 1 : Analyse Détaillée (Dashboard initial)
# =================================================
if app_mode == "Analyse Détaillée":
    st.sidebar.header("Filtres")
    maladie = st.sidebar.radio("Maladie:", ["COVID-19", "Mpox"], index=0)
    
    covid_df = load_db_table('covid19_daily')
    mpox_df = load_db_table('mpox')
    raw_df = covid_df if maladie == 'COVID-19' else mpox_df
    
    if not raw_df.empty:
        latest_df = raw_df.sort_values('date').groupby('country', as_index=False).last()
        visu_type = st.sidebar.selectbox("Type de visualisation:", ["Indicateurs Clés & Carte", "Comparaison de pays", "Détails par pays"])
        st.markdown(f"<div class='section-header'>Analyse pour : {maladie}</div>", unsafe_allow_html=True)

        if visu_type == "Indicateurs Clés & Carte":
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("<div class='metric-box' style='border-left: 5px solid orange;'>", unsafe_allow_html=True)
                st.metric("Total Cas", f"{int(latest_df['total_cases'].sum()):,}")
                st.markdown("</div>", unsafe_allow_html=True)
            with col2:
                st.markdown("<div class='metric-box' style='border-left: 5px solid green;'>", unsafe_allow_html=True)
                st.metric("Guéris", f"{int(latest_df['total_gueris'].sum()):,}")
                st.markdown("</div>", unsafe_allow_html=True)
            with col3:
                st.markdown("<div class='metric-box' style='border-left: 5px solid red;'>", unsafe_allow_html=True)
                st.metric("Décès", f"{int(latest_df['total_deaths'].sum()):,}")
                st.markdown("</div>", unsafe_allow_html=True)
            st.divider()
            metric = st.radio("Métrique pour la carte", ["Décès", "Guéris"], horizontal=True)
            color_col, scale, title = ('total_deaths', 'Reds', 'Décès par pays') if metric == "Décès" else ('total_gueris', 'Greens', 'Guéris par pays')
            fig_map = px.choropleth(latest_df, locations='country', locationmode='country names', color=color_col, hover_name='country', color_continuous_scale=scale, title=title)
            st.plotly_chart(fig_map, use_container_width=True)

        elif visu_type == "Comparaison de pays":
            countries = sorted(raw_df['country'].dropna().unique())
            sel = st.multiselect("Sélectionner pays", countries, default=countries[:3] if len(countries) > 2 else countries)
            if sel:
                comp_df = raw_df[raw_df['country'].isin(sel)]
                fig = px.line(comp_df, x='date', y='total_cases', color='country', title='Évolution des cas')
                st.plotly_chart(fig, use_container_width=True)

        elif visu_type == "Détails par pays":
            pays_sel = st.selectbox("Pays", sorted(raw_df['country'].unique()))
            filt = raw_df[raw_df['country'] == pays_sel]
            fig1 = px.area(filt, x='date', y='total_cases', title=f'Cas pour {pays_sel}')
            fig2 = px.bar(filt, x='date', y='total_deaths', title=f'Décès pour {pays_sel}')
            st.plotly_chart(fig1, use_container_width=True)
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Aucune donnée disponible pour la maladie sélectionnée.")

# =================================================
# PAGE 2 : Analyse IA (Forecasting)
# =================================================
elif app_mode == "Analyse IA":
    st.sidebar.header("Filtres de Prévision")
    
    maladie_fc = st.sidebar.radio("Maladie à prédire:", ["COVID", "MPOX"])
    
    perf_df = load_performance_data(maladie_fc)
    if perf_df is not None:
        countries_with_models = sorted(perf_df['country'].unique())
        
        if maladie_fc == 'MPOX':
            countries_with_models = [c for c in countries_with_models if c != 'Africa']

        selected_country = st.sidebar.selectbox("Choisissez un pays:", countries_with_models)
        days_to_predict = st.sidebar.slider("Nombre de jours à prédire:", 7, 90, 30)
        
        st.markdown(f"<div class='section-header'>Prévision des Cas pour {maladie_fc}</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader(f"Prévision pour {selected_country}")
            url = f"http://127.0.0.1:8000/api/forecasting/{maladie_fc}/{selected_country}?days={days_to_predict}"
            forecast_data = api_request(url)
            
            if forecast_data:
                df_forecast = pd.DataFrame(forecast_data['forecast_data'])
                df_forecast['date'] = pd.to_datetime(df_forecast['date'])
                
                db_table = 'covid19_daily' if maladie_fc == 'COVID' else 'mpox'
                df_hist = load_db_table(db_table)
                df_hist = df_hist[df_hist['country'] == selected_country]

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_hist['date'], y=df_hist['total_cases'], mode='lines', line=dict(color='rgb(0, 123, 255)'), name='Cas Historiques'))
                fig.add_trace(go.Scatter(x=df_forecast['date'], y=df_forecast['predicted_cases'], mode='lines', line=dict(color='rgb(255, 165, 0)', dash='dash'), name='Prédiction'))
                fig.add_trace(go.Scatter(x=pd.concat([df_forecast['date'], df_forecast['date'][::-1]]), y=pd.concat([df_forecast['predicted_upper_bound'], df_forecast['predicted_lower_bound'][::-1]]), fill='toself', fillcolor='rgba(255, 165, 0, 0.2)', line=dict(color='rgba(255,255,255,0)'), hoverinfo="skip", name='Intervalle de confiance'))
                fig.update_layout(title=f"Prévision des cas totaux pour {selected_country}", xaxis_title="Date", yaxis_title="Nombre total de cas")
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Interprétation de la Prévision")

            # --- Calcul des nouveaux cas ---
            if forecast_data and not df_hist.empty:
                last_historical_cases = df_hist['total_cases'].iloc[-1]
                last_predicted_cases = df_forecast['predicted_cases'].iloc[-1]
                new_predicted_cases = max(0, last_predicted_cases - last_historical_cases) 
                st.metric(
                    label=f"Nouveaux cas prédits sur {days_to_predict} jours",
                    value=f"{int(new_predicted_cases):,}"
                )
                st.write(f"Le modèle estime qu'il y aura environ **{int(new_predicted_cases):,}** nouveaux cas dans les **{days_to_predict}** prochains jours pour ce pays.")
                st.divider()

            # ---  Verdict de fiabilité simplifié ---
            st.subheader("Verdict de Fiabilité du Modèle")
            # Assurez-vous que le pays sélectionné existe dans le dataframe de performance
            if not perf_df[perf_df['country'] == selected_country].empty:
                country_perf = perf_df[perf_df['country'] == selected_country].iloc[0]
                mape = country_perf['mape']
                
                verdict = ""
                
                if mape <= 0.05: # Moins de 5% d'erreur
                    verdict = "Excellente"
                    
                elif mape <= 0.15: # Moins de 15% d'erreur
                    verdict = "Bonne"
                   
                else:
                    verdict = "Moyenne"
                    

                st.markdown(f"### Fiabilité : **{verdict}**")
                st.write(f"En moyenne, les prédictions de ce modèle ont une marge d'erreur de **{mape:.2%}** par rapport aux données réelles. Plus ce chiffre est bas, plus la prédiction est fiable.")
            else:
                st.warning(f"Aucune donnée de performance trouvée pour {selected_country}.")
            
    else:
        st.error(f"Le fichier de performance pour {maladie_fc} est introuvable. Veuillez lancer le script d'entraînement.")