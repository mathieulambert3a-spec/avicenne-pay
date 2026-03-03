# Avicenne Pay

Application web de gestion des déclarations d'activité pour les collaborateurs de la faculté de médecine.

## Stack technique

- **Backend** : FastAPI
- **Base de données** : PostgreSQL via SQLAlchemy (async) + Alembic
- **Templates** : Jinja2 + Bootstrap 5
- **Auth** : Sessions cookie signées avec itsdangerous
- **Chiffrement** : Fernet (NSS et IBAN)

## Installation locale

```bash
# Créer et activer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -e .

# Copier et configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs

# Appliquer les migrations
alembic upgrade head

# Lancer l'application
uvicorn app.main:app --reload
```

## Variables d'environnement

| Variable | Description |
|---|---|
| `DATABASE_URL` | URL de connexion PostgreSQL (asyncpg) |
| `SECRET_KEY` | Clé secrète pour les sessions (min 32 chars) |
| `FERNET_KEY` | Clé Fernet base64 pour chiffrement NSS/IBAN |

Générer une clé Fernet :
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

## Premier utilisateur Admin

Accéder à `/setup` pour créer le premier compte admin (uniquement si aucun admin n'existe).

## Déploiement Render.com

1. Créer un service Web Python
2. Build command : `pip install -e .`
3. Start command : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Ajouter les variables d'environnement (`DATABASE_URL`, `SECRET_KEY`, `FERNET_KEY`)
5. Créer une base de données PostgreSQL sur Render et lier l'URL
6. Ajouter une migration step : `alembic upgrade head`
