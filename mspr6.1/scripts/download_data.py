
from dotenv import load_dotenv
load_dotenv()

import kaggle
import os
import pandas as pd

# Définir le répertoire de destination pour les datasets (dossier "data" à la racine du projet)
destination_path = os.path.join(os.getcwd(), "data")
os.makedirs(destination_path, exist_ok=True)

def download_kaggle_dataset(dataset_url, destination_path):
    # Construction de l'ID du dataset à partir de l'URL
    dataset_id = dataset_url.split("/")[-2] + '/' + dataset_url.split("/")[-1]
    # Téléchargement et décompression des fichiers
    kaggle.api.dataset_download_files(dataset_id, path=destination_path, unzip=True)
    print(f"{dataset_id} téléchargé avec succès dans {destination_path}!")
    return dataset_id

# URLs des datasets sur Kaggle
covid_url = 'https://www.kaggle.com/datasets/josephassaker/covid19-global-dataset'
mpox_url = 'https://www.kaggle.com/datasets/utkarshx27/mpox-monkeypox-data'

# Télécharger les datasets
covid_dataset_id = download_kaggle_dataset(covid_url, destination_path)
mpox_dataset_id = download_kaggle_dataset(mpox_url, destination_path)

# Charger les données en mémoire
# On suppose ici que les noms des fichiers CSV sont connus après décompression.
covid_csv = os.path.join(destination_path, "worldometer_coronavirus_daily_data.csv")
mpox_csv = os.path.join(destination_path, "owid-monkeypox-data.csv")

dataframes = {}

if os.path.exists(covid_csv):
    dataframes["covid"] = pd.read_csv(covid_csv)
    print("Données COVID chargées en mémoire.")
else:
    print("Fichier CSV COVID non trouvé.")

if os.path.exists(mpox_csv):
    dataframes["mpox"] = pd.read_csv(mpox_csv)
    print("Données Mpox chargées en mémoire.")
else:
    print("Fichier CSV Mpox non trouvé.")

# Maintenant, le dictionnaire 'dataframes' contient les DataFrames chargés en mémoire
# Vous pouvez y accéder par exemple via dataframes["covid"] ou dataframes["mpox"]
