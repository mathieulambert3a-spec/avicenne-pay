# backend/app/database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
# 1. On importe la bibliothèque qui sait lire les fichiers .env
from dotenv import load_dotenv

# 2. On force le chargement du fichier .env
load_dotenv()

# 3. RÉCUPÉRATION DE L'URL (maintenant ça va marcher !)
DATABASE_URL = os.getenv("DATABASE_URL")

# SÉCURITÉ AU CAS OÙ .env SOIT MAL LU
if not DATABASE_URL:
    raise ValueError("⚠️ La variable d'environnement DATABASE_URL est manquante dans le fichier .env !")

# 4. Création du moteur SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True 
)

# 5. Création de la fabrique de sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 6. La classe Base dont héritent tous nos modèles
Base = declarative_base()

# 7. Fonction utilitaire pour obtenir une session de base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()