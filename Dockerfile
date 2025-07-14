# Étape 1: Utiliser une image Python officielle
FROM python:3.10-slim

# Étape 2: Définir le répertoire de travail
WORKDIR /app

# Étape 3: Définir le PYTHONPATH
# C'est la solution la plus robuste pour que Python trouve vos modules.
# Elle dit à Python : "Quand tu cherches des modules, regarde aussi dans /app".
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Étape 4: Copier et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Étape 5: Copier TOUT le projet (y compris mspr6.1/ et tests/)
COPY . .

# Étape 6: Exposer le port de l'API
EXPOSE 8000

# Étape 7: Commande de lancement
# Python va chercher dans /app (grâce au PYTHONPATH) et trouvera le package mspr6.1
CMD ["uvicorn", "mspr6.1.api.api:app", "--host", "0.0.0.0", "--port", "8000"]