# Étape 1: Utiliser une image Python officielle
FROM python:3.10-slim

# Étape 2: Définir le répertoire de travail
WORKDIR /app

# Étape 3: Ajouter le répertoire de l'application au PYTHONPATH
# C'EST LA CORRECTION LA PLUS IMPORTANTE.
# Elle dit à Python : "Quand tu cherches des modules, regarde aussi dans le dossier /app".
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Étape 4: Copier et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Étape 5: Copier tout le code du projet (y compris mspr6.1/ et tests/)
COPY . .

# Étape 6: Exposer le port
EXPOSE 8000

# Étape 7: Commande de lancement
# Python cherchera dans /app (grâce au PYTHONPATH) et trouvera le package mspr6.1
CMD ["uvicorn", "mspr6.1.api.api:app", "--host", "0.0.0.0", "--port", "8000"]