# Étape 1: Utiliser une image Python officielle
FROM python:3.10-slim

# Étape 2: Définir le répertoire de travail
WORKDIR /app

# Étape 3: Copier et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Étape 4: Copier uniquement le code source de l'application
# C'EST LA CORRECTION LA PLUS IMPORTANTE. On copie le contenu de mspr6.1/
# directement dans /app. Les dossiers 'api' et 'scripts' seront à la racine.
COPY mspr6.1/ .

# Étape 5: Copier le dossier des tests
COPY tests/ ./tests/

# Étape 6: Exposer le port
EXPOSE 8000

# Étape 7: Commande de lancement
# La commande est simple car 'api' est maintenant un dossier à la racine de /app.
CMD ["uvicorn", "api.api:app", "--host", "0.0.0.0", "--port", "8000"]