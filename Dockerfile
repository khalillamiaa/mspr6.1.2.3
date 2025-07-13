# Étape 1: Utiliser une image Python officielle
FROM python:3.10-slim

# Étape 2: Définir le répertoire de travail
WORKDIR /app

# Étape 3: Copier et installer les dépendances
# On copie d'abord requirements.txt pour optimiser le cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Étape 4: Copier le code source de l'application
# C'EST LA CORRECTION LA PLUS IMPORTANTE :
# On copie le contenu du dossier mspr6.1/ (api, scripts, etc.)
# directement dans le répertoire de travail /app.
COPY mspr6.1/ .

# Étape 5: Exposer le port de l'API
EXPOSE 8000

# Étape 6: La commande de lancement, maintenant simple
# Elle cherche un dossier 'api', puis un fichier 'api.py' dedans.
CMD ["uvicorn", "api.api:app", "--host", "0.0.0.0", "--port", "8000"]