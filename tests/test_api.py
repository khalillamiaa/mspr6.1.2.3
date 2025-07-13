import os
import requests
from dotenv import load_dotenv
import pytest

# Charger les variables d'environnement pour connaître l'URL de l'API
# Bien que le .env ne soit pas sur GitHub, cette ligne est une bonne pratique
load_dotenv()

# L'URL de base de l'API qui tourne dans le conteneur Docker
# Pour les tests sur GitHub Actions, nous utiliserons l'adresse par défaut
API_URL = "http://127.0.0.1:8000"

def test_api_health_check():
    """
    Teste si l'API est bien en ligne en accédant à sa documentation.
    C'est un test simple pour vérifier que le service a bien démarré.
    """
    try:
        response = requests.get(f"{API_URL}/docs")
        # Un code 200 OK signifie que la page s'est chargée correctement
        assert response.status_code == 200, "L'API ne répond pas ou la page de documentation est introuvable."
    except requests.exceptions.ConnectionError as e:
        # Si le test échoue, on donne une erreur claire
        pytest.fail(f"La connexion à l'API a échoué. Assurez-vous que les conteneurs Docker sont bien lancés. Erreur: {e}")

def test_forecasting_endpoint_success():
    """
    Teste l'endpoint de prévision avec une requête valide pour le COVID.
    Vérifie que la réponse est correcte et contient les bonnes clés.
    """
    disease = "COVID"
    country = "France"
    
    response = requests.get(f"{API_URL}/api/forecasting/{disease}/{country}")
    
    # Vérifie que la requête a réussi (code 200)
    assert response.status_code == 200, f"L'API a renvoyé une erreur : {response.text}"
    
    data = response.json()
    
    # Vérifie que la structure de la réponse est correcte
    assert "country" in data
    assert "forecast_data" in data
    assert data["country"] == country
    assert isinstance(data["forecast_data"], list)
    print(f"\nTest de prévision pour {country} réussi.")

def test_forecasting_endpoint_not_found():
    """
    Teste le cas où l'on demande un pays pour lequel il n'y a pas de modèle.
    Vérifie que l'API renvoie bien une erreur 404 "Not Found".
    """
    disease = "COVID"
    country_invalid = "PaysQuiNexistePas"
    
    response = requests.get(f"{API_URL}/api/forecasting/{disease}/{country_invalid}")
    
    # On s'attend à recevoir une erreur 404
    assert response.status_code == 404, f"L'API aurait dû renvoyer une erreur 404 pour un pays invalide, mais a renvoyé {response.status_code}."
    print("\nTest d'erreur 404 pour un pays invalide réussi.")