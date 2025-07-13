import os
import pandas as pd
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
import joblib
import logging
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Désactiver les logs de Prophet pour ne pas surcharger la console
logging.getLogger('prophet').setLevel(logging.ERROR)
logging.getLogger('cmdstanpy').setLevel(logging.ERROR)

def train_and_evaluate(nom_maladie: str, table_name: str, value_col: str, country_col: str):
    """
    Fonction générique pour charger les données depuis POSTGRESQL, préparer, entraîner,
    évaluer avec cross-validation et sauvegarder les modèles de forecasting.
    """
    
    # --- 1. Chargement des données depuis PostgreSQL ---
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL n'est pas défini.")
    
    engine = create_engine(DATABASE_URL)
    
    try:
        df = pd.read_sql_table(table_name, engine)
    except Exception as e:
        return

    # --- 2. Préparation des données ---
    # Harmonisation des nom_maladies de colonnes depuis la BDD
    df.rename(columns={
        'date': 'ds', 
        'Date': 'ds',
        value_col: 'y', 
        country_col: 'country'
    }, inplace=True)
    
    df['ds'] = pd.to_datetime(df['ds'])
    df['y'] = pd.to_numeric(df['y'], errors='coerce').fillna(0)
    
    all_countries = df['country'].unique()
    
    print(f"Données prêtes pour {len(all_countries)} pays.")

    # --- 3. Entraîner et évaluer un modèle pour chaque pays ---
    all_models = {}
    all_performance = []

    for country_name in all_countries:
        country_df = df[df['country'] == country_name].sort_values('ds')
        
        if len(country_df) < 90:
            continue

        print(f"Traitement pour {country_name}...")
        
        # Entraînement sur toutes les données disponibles
        model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
        model.fit(country_df[['ds', 'y']])
        all_models[country_name] = model
        
        # Évaluation par Cross-Validation
        try:
            df_cv = cross_validation(model, initial='180 days', period='90 days', horizon='30 days', parallel="processes")
            df_p = performance_metrics(df_cv)
            
            performance = df_p.head(1)[['mae','rmse', 'mape']].copy()
            performance['country'] = country_name
            all_performance.append(performance)
            
            print(f"  -> Modèle entraîné. Performance (MAPE): {performance['mape'].iloc[0]:.2%}")
        except Exception as e:
            print(f"  -> Impossible d'effectuer la cross-validation pour {country_name}. Raison: {e}")

    # --- 4. Sauvegarder les modèles et les performances ---
    if all_models:
        model_output_path = os.path.join(os.getcwd(), f'prophet_{nom_maladie.lower()}_models.joblib')
        joblib.dump(all_models, model_output_path)
        print(f"Modèles sauvegardés dans : {model_output_path}")

    if all_performance:
        perf_df = pd.concat(all_performance)
        perf_output_path = os.path.join(os.getcwd(), f'performance_{nom_maladie.lower()}.csv')
        perf_df.to_csv(perf_output_path, index=False)
        print(f"Performances sauvegardées dans : {perf_output_path}")


if __name__ == "__main__":
    # Entraîner les modèles pour le COVID-19 en lisant depuis la table 'covid19_daily'
    train_and_evaluate(
        nom_maladie="COVID",
        table_name="covid19_daily",
        value_col="total_cases",
        country_col="country_region"
    )

    # Entraîner les modèles pour le Mpox en lisant depuis la table 'mpox'
    train_and_evaluate(
        nom_maladie="MPOX",
        table_name="mpox",
        value_col="Total_Cases",
        country_col="Country/Region"
    )