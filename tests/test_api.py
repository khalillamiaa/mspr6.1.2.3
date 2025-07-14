import os
import requests
from dotenv import load_dotenv
import pytest
import psycopg2
from psycopg2 import OperationalError

# Charger les variables d'environnement
load_dotenv()

# L'URL de base de l'API
API_URL = "http://127.0.0.1:8000"

def test_api_health_check():
    """Teste si l'API est bien en ligne."""
    try:
        response = requests.get(f"{API_URL}/docs")
        assert response.status_code == 200, "L'API ne répond pas."
    except requests.exceptions.ConnectionError as e:
        pytest.fail(f"La connexion à l'API a échoué. Erreur: {e}")

def test_forecasting_endpoint_success():
    """Teste l'endpoint de prévision avec une requête valide."""
    response = requests.get(f"{API_URL}/api/forecasting/COVID/France")
    assert response.status_code == 200, f"L'API a renvoyé une erreur : {response.text}"
    data = response.json()
    assert "country" in data and "forecast_data" in data

def test_forecasting_endpoint_not_found():
    """Teste le cas où l'on demande un pays invalide."""
    response = requests.get(f"{API_URL}/api/forecasting/COVID/PaysQuiNexistePas")
    assert response.status_code == 404

def test_database_connection():
    """Teste si la connexion à la base de données PostgreSQL est possible."""
    DATABASE_URL = os.getenv("DATABASE_URL")
    assert DATABASE_URL is not None, "DATABASE_URL n'est pas définie."
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("\nConnexion à la base de données réussie.")
        conn.close()
        assert True
    except OperationalError as e:
        pytest.fail(f"Impossible de se connecter à la BDD. Erreur: {e}")