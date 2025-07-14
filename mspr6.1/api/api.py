import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import uvicorn
import pandas as pd
import joblib

# --- Chargement initial ---
load_dotenv()
app = FastAPI(title="API MSPR - Déploiement Dynamique")

# --- MODIFICATION CLÉ : Lire la cible de déploiement depuis les variables d'environnement ---
# Par défaut, si la variable n'est pas trouvée, on considère que c'est pour les USA.
DEPLOYMENT_TARGET = os.getenv("DEPLOYMENT_TARGET", "USA").upper()
print(f"--- Lancement de l'API en mode de déploiement : {DEPLOYMENT_TARGET} ---")

# --- Chargement des modèles d'IA ---
forecasting_models = {}
print("--- Début du chargement des modèles ---")
try:
    # Charger les modèles pour le COVID
    covid_models_path = os.path.join(os.path.dirname(__file__), 'prophet_covid_models.joblib')
    print(f"Tentative de chargement du modèle COVID depuis : {os.path.abspath(covid_models_path)}")
    forecasting_models['COVID'] = joblib.load(covid_models_path)
    
    # Charger les modèles pour le MPOX
    mpox_models_path = os.path.join(os.path.dirname(__file__), 'prophet_mpox_models.joblib')
    print(f"Tentative de chargement du modèle MPOX depuis : {os.path.abspath(mpox_models_path)}")
    forecasting_models['MPOX'] = joblib.load(mpox_models_path)
    print("Modèles de forecasting chargés avec succès.")
    
except FileNotFoundError as e:
    print(f" Un fichier de modèle est introuvable. {e}")

# --- Connexion à la base de données ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env")
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True

# --- Modèles Pydantic (Structures de données) ---
class CovidItem(BaseModel):
    id: int
    country_region: str
    date: str
    total_cases: float
    total_deaths: float
    total_gueris: float

class CovidCreate(BaseModel):
    country_region: str
    date: str
    total_cases: float
    total_deaths: float
    total_gueris: float

class MpoxItem(BaseModel):
    id: int
    country_region: str
    date: str
    total_cases: float
    total_deaths: float
    total_recovered: float

class MpoxCreate(BaseModel):
    country_region: str
    date: str
    total_cases: float
    total_deaths: float
    total_recovered: float

class ForecastResponse(BaseModel):
    country: str
    forecast_data: List[Dict[str, Any]]

# --- Fonctions d'aide (Helpers) ---
def fetchall_dicts(query: str, params=None):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query, params or ())
        return cur.fetchall()

def fetchone_dict(query: str, params=None):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query, params or ())
        return cur.fetchone()

# ===============================================
#               ENDPOINT IA (Toujours actif)
# ===============================================
@app.get("/api/forecasting/{disease}/{country_name}", response_model=ForecastResponse)
def get_country_forecast(disease: str, country_name: str, days: int = 30):
    disease_key = disease.upper()
    
    if disease_key not in forecasting_models:
        raise HTTPException(status_code=404, detail=f"Aucun modèle n'est disponible pour la maladie '{disease}'.")
        
    models_for_disease = forecasting_models[disease_key]
    
    if country_name not in models_for_disease:
        raise HTTPException(status_code=404, detail=f"Aucun modèle n'a été entraîné pour le pays '{country_name}' pour la maladie '{disease}'.")

    model = models_for_disease[country_name]
    future = model.make_future_dataframe(periods=days)
    forecast = model.predict(future)
    
    response_data = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
    response_data.rename(columns={'ds': 'date', 'yhat': 'predicted_cases', 'yhat_lower': 'predicted_lower_bound', 'yhat_upper': 'predicted_upper_bound'}, inplace=True)
    response_data['date'] = response_data['date'].dt.strftime('%Y-%m-%d')
    return ForecastResponse(country=country_name, forecast_data=response_data.to_dict('records'))

# ===============================================
# Routes CRUD (Conditionnelles au déploiement)
# ===============================================

# --- MODIFICATION CLÉ : On n'active ces routes que pour le cluster USA ---
if DEPLOYMENT_TARGET == "USA":
    print("Mode de déploiement 'USA' : Activation des routes CRUD (API Technique).")
    
    # --- Routes COVID19_DAILY ---
    @app.get("/api/covid19_daily", response_model=List[CovidItem], tags=["API Technique (CRUD)"])
    def read_covid():
        query = "SELECT id, country_region, date, total_cases, total_deaths, total_gueris FROM covid19_daily"
        return fetchall_dicts(query)

    @app.post("/api/covid19_daily", response_model=CovidItem, status_code=201, tags=["API Technique (CRUD)"])
    def create_covid(item: CovidCreate):
        query = "INSERT INTO covid19_daily (country_region, date, total_cases, total_deaths, total_gueris) VALUES (%s, %s, %s, %s, %s) RETURNING id, country_region, date, total_cases, total_deaths, total_gueris"
        row = fetchone_dict(query, [item.country_region, item.date, item.total_cases, item.total_deaths, item.total_gueris])
        return row

    @app.put("/api/covid19_daily/{id}", response_model=CovidItem, tags=["API Technique (CRUD)"])
    def update_covid(id: int, item: CovidCreate):
        query = "UPDATE covid19_daily SET country_region = %s, date = %s, total_cases = %s, total_deaths = %s, total_gueris = %s WHERE id = %s RETURNING id, country_region, date, total_cases, total_deaths, total_gueris"
        row = fetchone_dict(query, [item.country_region, item.date, item.total_cases, item.total_deaths, item.total_gueris, id])
        if not row:
            raise HTTPException(status_code=404, detail="Data not found")
        return row

    @app.delete("/api/covid19_daily/{id}", response_model=CovidItem, tags=["API Technique (CRUD)"])
    def delete_covid(id: int):
        query = "DELETE FROM covid19_daily WHERE id = %s RETURNING id, country_region, date, total_cases, total_deaths, total_gueris"
        row = fetchone_dict(query, [id])
        if not row:
            raise HTTPException(status_code=404, detail="Data not found")
        return row

    # --- Routes MPOX ---
    @app.get("/api/mpox", response_model=List[MpoxItem], tags=["API Technique (CRUD)"])
    def read_mpox():
        query = """
            SELECT id, "Country/Region" AS country_region, "Date" AS date, 
                   "Total_Cases" AS total_cases, "Total_Deaths" AS total_deaths, 
                   "Total_Gueris" AS total_recovered
            FROM mpox
        """
        return fetchall_dicts(query)

    @app.post("/api/mpox", response_model=MpoxItem, status_code=201, tags=["API Technique (CRUD)"])
    def create_mpox(item: MpoxCreate):
        query = """
            INSERT INTO mpox ("Country/Region", "Date", "Total_Cases", "Total_Deaths", "Total_Gueris")
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, "Country/Region" AS country_region, "Date" AS date, "Total_Cases" AS total_cases, 
                      "Total_Deaths" AS total_deaths, "Total_Gueris" AS total_recovered
        """
        row = fetchone_dict(query, [item.country_region, item.date, item.total_cases, item.total_deaths, item.total_recovered])
        return row

    @app.put("/api/mpox/{id}", response_model=MpoxItem, tags=["API Technique (CRUD)"])
    def update_mpox(id: int, item: MpoxCreate):
        query = """
            UPDATE mpox SET "Country/Region" = %s, "Date" = %s, "Total_Cases" = %s, 
                             "Total_Deaths" = %s, "Total_Gueris" = %s
            WHERE id = %s
            RETURNING id, "Country/Region" AS country_region, "Date" AS date, "Total_Cases" AS total_cases,
                      "Total_Deaths" AS total_deaths, "Total_Gueris" AS total_recovered
        """
        row = fetchone_dict(query, [item.country_region, item.date, item.total_cases, item.total_deaths, item.total_recovered, id])
        if not row:
            raise HTTPException(status_code=404, detail="Data not found")
        return row

    @app.delete("/api/mpox/{id}", response_model=MpoxItem, tags=["API Technique (CRUD)"])
    def delete_mpox(id: int):
        query = """
            DELETE FROM mpox WHERE id = %s
            RETURNING id, "Country/Region" AS country_region, "Date" AS date, "Total_Cases" AS total_cases,
                      "Total_Deaths" AS total_deaths, "Total_Gueris" AS total_recovered
        """
        row = fetchone_dict(query, [id])
        if not row:
            raise HTTPException(status_code=404, detail="Data not found")
        return row
else:
    print(f"Mode de déploiement '{DEPLOYMENT_TARGET}' : Les routes CRUD (API Technique) sont désactivées.")

if __name__ == "__main__":
    uvicorn.run("api.api:app", host="0.0.0.0", port=8000, reload=True)