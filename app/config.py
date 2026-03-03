import os
from dotenv import load_dotenv
from pathlib import Path

# chemin absolu du dossier 'app'
BASE_DIR = Path(__file__).resolve().parent

# chargement du .env qui est dans ce même dossier
load_dotenv(dotenv_path=BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
FERNET_KEY = os.getenv("FERNET_KEY")