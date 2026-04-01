from app.database import Base, engine
# Importe tous tes modèles pour que SQLAlchemy les connaisse
from app.models.user import User

print("Création des tables en cours...")
Base.metadata.create_all(bind=engine)
print("Tables créées avec succès !")