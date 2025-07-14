# MSPr6.1 - Pipeline Données & Dashboard

**Table des matières**

- [Présentation](#présentation)
- [Structure du projet](#structure-du-projet)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Pipeline ETL](#pipeline-etl)
- [API FastAPI](#api-fastapi)
- [Dashboard Streamlit](#dashboard-streamlit)
- [Bonnes pratiques](#bonnes-pratiques)
- [Dépannage rapide](#dépannage-rapide)

---

## Présentation

Ce projet met en place un **pipeline complet** pour télécharger, nettoyer, stocker et visualiser des données sur la COVID-19 et le Mpox. Les données brutes sont obtenues via Kaggle, nettoyées avec pandas, stockées dans PostgreSQL, exposées via une API FastAPI et visualisées dans un dashboard Streamlit.

---

## Structure du projet


mspr6.1-main/
|
├── api/
│   ├── api.py                      # Le code de l'API FastAPI
│   ├── covid_models.joblib         # Modèles IA pour le COVID
│   ├── mpox_models.joblib          # Modèles IA pour le Mpox
│   |── performance_mpox.csv        # Fichiers de performance des modèles
│   └── performance_covid.csv 
|
└── scripts/
├── download_data.py            # 1. Téléchargement des données
├── clean_datasets.py           # 2. Nettoyage des données
├── store_data.py               # 3. Stockage en base de données
├── train_prevision_models.py   # 4. Entraînement des modèles IA
└── dashboard.py                # Le dashboard Streamlit
│
├── data/                               # Données brutes téléchargées
├── cleaned_data/                       # Données nettoyées (temporaire)
├── .env                                # Variables d'environnement
├── requirements.txt                    # Dépendances Python
└── README.md                           # Ce fichier
```

---

## Prérequis

- Python 3.10+
- Git
- PostgreSQL 14+ (ou 16)
- Compte Kaggle (`kaggle.json` ou variables d'environnement)

---

## Installation

1. **Cloner le dépôt**
   ```bash
git clone https://github.com/MAHRAZ-Oussama/mspr6.1.git
cd mspr6.1
   ```
2. **Créer et activer l'environnement virtuel**
   ```bash
python3 -m venv .venv
source .venv/bin/activate   
 Windows : .venv\Scripts\activate
   ```
3. **Installer les dépendances**
   ```bash
pip install -r requirements.txt
   ```

---

## Configuration

Créer un fichier `.env` à la racine (fourni) contenant :

```dotenv
DATABASE_URL=postgresql://mspr_user:Mspr6.1%40@localhost:5432/mspr_db
KAGGLE_USERNAME=<votre_kaggle_user>
KAGGLE_KEY=<votre_kaggle_key>
```

- Le mot de passe `Mspr6.1@` doit être encodé (`%40`).
- La base `mspr_db` et l'utilisateur `mspr_user` doivent exister.

---

## Pipeline ETL

1. **Téléchargement**
   ```bash
python mspr6.1/scripts/download_data.py
   ```
   - Télécharge les CSV via l'API Kaggle dans `data/`.

2. **Nettoyage**
   ```bash
python mspr6.1/scripts/clean_datasets.py
   ```
   - Conserve uniquement le dernier jour du mois par pays.
   - Ajoute la colonne `Total_Gueris`.
   - Écrit les CSV dans `cleaned_data/`.

3. **Stockage en base**
   ```bash
python mspr6.1/scripts/store_data.py
   ```
   - Insère les CSV nettoyés dans PostgreSQL (`covid19_daily`, `mpox`).

---

## API FastAPI

```bash
uvicorn api.api:app --reload
```

- **Base URL** : `http://localhost:8000`
- **Swagger** : `http://localhost:8000/docs`
- **Endpoint principal** :
  - `GET /query?sql=<votre_SQL>` exécute la requête et retourne JSON.

---

4. **Generer le model ia **
   ```bash
python mspr6.1/scripts/train_prevision_models.py
   ```
   - Insère les CSV nettoyés dans PostgreSQL (`covid19_daily`, `mpox`).

---

## API FastAPI

```bash
uvicorn mspr6.1.api.main:app --reload
```

- **Base URL** : `http://localhost:8000`
- **Swagger** : `http://localhost:8000/docs`
- **Endpoint principal** :
  - `GET /query?sql=<votre_SQL>` exécute la requête et retourne JSON.

---

## Dashboard Streamlit





## Dashboard Streamlit

```bash
streamlit run mspr6.1/scripts/dashboard.py
```

- **Affiche** les indicateurs globaux basés sur le cumul **dernier jour** par pays.
- **Comparaison** des courbes, carte choroplèthe, détails par pays.

---


### Sauvegarde de la Base de Données

Pour sauvegarder les données de la base PostgreSQL qui tourne dans Docker, exécutez la commande suivante depuis votre terminal :

```sh
docker exec postgres_db_mspr pg_dump -U mspr_user -d mspr_db > sauvegarde.sql

#### **Procédure de Restauration de la Base de Données**

```markdown
### Restauration de la Base de Données

Pour restaurer la base de données à partir d'un fichier de sauvegarde nommé `sauvegarde.sql` :

1.  Copiez le fichier de sauvegarde dans le conteneur :
    ```sh
    docker cp sauvegarde.sql postgres_db_mspr:/sauvegarde.sql
    ```
2.  Exécutez la commande de restauration :
    ```sh
    docker exec -it postgres_db_mspr psql -U mspr_user -d mspr_db -f /sauvegarde.sql
    ```



### Procédure de Rollback

En cas de problème après une mise à jour, la méthode la plus simple pour revenir à la version précédente est d'utiliser l'historique de Git :

1.  Affichez l'historique des commits :
    ```sh
    git log
    ```
2.  Identifiez le commit de la version stable précédente et revenez-y :
    ```sh
    git checkout <id_du_commit_precedent>
    ```
3.  Reconstruisez l'image Docker avec l'ancienne version du code :
    ```sh
    docker-compose up --build -d
    ```


Pour lancer le processus complet de ré-entraînement :

1.  **Mettez à jour les données** en lançant les scripts de pipeline initiaux :
    ```sh
    python mspr6.1/scripts/download_data.py
    python mspr6.1/scripts/clean_datasets.py
    python mspr6.1/scripts/store_data.py
    ```

2.  **Lancez le script de ré-entraînement** depuis la racine du projet :
    ```sh
    python retrain_models.py
    ```
    Ce script va automatiquement exécuter le processus d'entraînement et de validation, et écrasera les anciens fichiers `.joblib` et `performance.csv` avec les nouvelles versions.

3.  **Redémarrez le service de l'API** pour qu'il charge les nouveaux modèles :
    ```sh
    docker compose restart app
    ```
