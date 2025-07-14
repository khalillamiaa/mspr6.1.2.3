# retrain_models.py
import subprocess
import sys

def run_training_pipeline():
    """
    Lance le pipeline complet de ré-entraînement des modèles d'IA.
    """
    script_path = "mspr6.1/scripts/train_prevision_models.py"
    
    try:
        # Utiliser subprocess pour appeler le script d'entraînement
        process = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Afficher la sortie du script d'entraînement
        print("\n--- Sortie du script d'entraînement ---")
        print(process.stdout)
        print("\n--- Ré-entraînement terminé  ---")
        
    except subprocess.CalledProcessError as e:
        print("\n--- ERREUR lors du ré-entraînement ---")
        print(e.stderr)

if __name__ == "__main__":
    run_training_pipeline()