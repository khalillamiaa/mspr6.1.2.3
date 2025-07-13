import os
from sqlalchemy import create_engine
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("La variable DATABASE_URL est manquante")

engine = create_engine(DATABASE_URL)
cleaned_dir = os.path.join(os.getcwd(), "cleaned_data")

def store_data(file_name: str, table_name: str, columns_map: dict):
    """
    Charge les données depuis un CSV et les remplace dans la table PostgreSQL.
    
    Args:
        file_name (str): Le nom du fichier CSV à charger.
        table_name (str): Le nom de la table où stocker les données.
        columns_map (dict): Dictionnaire pour renommer les colonnes pour la BDD.
    """
    file_path = os.path.join(cleaned_dir, file_name)
    df = pd.read_csv(file_path)
    print(f"Chargement pour injection : {file_path}...")

    # Renommer les colonnes pour correspondre au schéma de la BDD
    df.rename(columns=columns_map, inplace=True)

    try:
        df.to_sql(
            table_name,
            engine,
            if_exists="replace", 
            index=False,
            # Le nom des colonnes du DataFrame doit correspondre à celui de la table
        )
    except Exception as e:
        print(f"Erreur lors de l'insertion dans '{table_name}' : {e}")

# --- Configuration et Exécution ---

# Renommage des colonnes pour correspondre au schéma de la BDD
# Le nom de la clé du dictionnaire est le nom dans le CSV
# La valeur est le nom attendu dans la table PostgreSQL
db_columns_map_covid = {
    "total_recovered": "total_gueris"
}

db_columns_map_mpox = {
    "country_region": "Country/Region",
    "date": "Date",
    "total_cases": "Total_Cases",
    "total_deaths": "Total_Deaths",
    "total_recovered": "Total_Gueris"
}

# Lancer le stockage pour chaque maladie
store_data("cleaned_covid19_daily_dataset.csv", "covid19_daily", db_columns_map_covid)
store_data("cleaned_mpox_dataset.csv", "mpox", db_columns_map_mpox)

print("\nStockage des données terminé.")