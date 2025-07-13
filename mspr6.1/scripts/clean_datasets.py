import os
import pandas as pd

# Répertoires de données
base_dir   = os.getcwd()
data_dir   = os.path.join(base_dir, "data")
output_dir = os.path.join(base_dir, "cleaned_data")
os.makedirs(output_dir, exist_ok=True)

def clean_and_standardize(file_path, output_name, columns_map, relevant_columns, continents=None):
    """
    Nettoie et standardise le fichier CSV :
    - Conserve les colonnes pertinentes.
    - Remplace les valeurs manquantes par 0.
    - Renomme les colonnes selon columns_map.
    - Calcule 'total_recovered' si les colonnes existent.
    - Exclut les continents si demandé.
    """
    df = pd.read_csv(file_path)
    print(f"Nettoyage du fichier : {file_path}")

    # Garder uniquement les colonnes pertinentes
    df = df[relevant_columns]

    # Renommer les colonnes pour la standardisation
    df.rename(columns=columns_map, inplace=True)
    
    # Remplir les valeurs manquantes
    # Pour les colonnes numériques, on remplit avec 0
    for col in ['total_cases', 'total_deaths', 'total_recovered']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Harmonisation du nom du pays
    if 'Country/Region' in df.columns:
        df.rename(columns={'Country/Region': 'country_region'}, inplace=True)

    # Conversion de la date
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df.dropna(subset=['date', 'country_region'], inplace=True)

    # Calcul uniformisé de 'total_gueris'
    if 'total_cases' in df.columns and 'total_deaths' in df.columns:
        df['total_gueris'] = df['total_cases'] - df['total_deaths']

    # Exclusion des continents si demandé
    if continents and 'country_region' in df.columns:
        df = df[~df['country_region'].isin(continents)]
    
    # Sauvegarde du fichier nettoyé complet
    out_path = os.path.join(output_dir, output_name)
    df.to_csv(out_path, index=False)
    print(f"Fichier nettoyé et complet sauvegardé dans : {out_path}")
    return df

# --- Configuration ---
continents_to_exclude = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania", "Antarctica"]

# Mapping et colonnes pour COVID-19
columns_map_covid = {
    'date': 'date',
    'country': 'country_region',
    'cumulative_total_cases': 'total_cases',
    'cumulative_total_deaths': 'total_deaths'
   
}
relevant_covid = ['date', 'country', 'cumulative_total_cases', 'cumulative_total_deaths']

# Mapping et colonnes pour Mpox
columns_map_mpox = {
    'date': 'date',
    'location': 'country_region',
    'total_cases': 'total_cases',
    'total_deaths': 'total_deaths'
    # La colonne des guéris sera également calculée
}
relevant_mpox = ['date', 'location', 'total_cases', 'total_deaths']

# Fichiers sources
covid_file  = os.path.join(data_dir, 'worldometer_coronavirus_daily_data.csv')
mpox_file  = os.path.join(data_dir, 'owid-monkeypox-data.csv')

# Exécution du nettoyage
clean_and_standardize(covid_file, 'cleaned_covid19_daily_dataset.csv', columns_map_covid, relevant_covid, continents_to_exclude)
clean_and_standardize(mpox_file,  'cleaned_mpox_dataset.csv', columns_map_mpox, relevant_mpox, continents_to_exclude)