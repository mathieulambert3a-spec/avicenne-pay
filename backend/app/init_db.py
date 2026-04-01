# backend/app/init_db.py
from app.database import engine, Base
# On importe tous nos modèles pour que SQLAlchemy les connaisse
from app.models.user import User
from app.models.mission import Mission
from app.models.declaration import Declaration, LigneDeclaration

def init_database():
    print("⏳ Création des tables dans PostgreSQL...")
    # Cette ligne magique compare nos modèles avec la base de données 
    # et crée les tables si elles n'existent pas !
    Base.metadata.create_all(bind=engine)
    print("✅ Toutes les tables ont été créées avec succès !")

if __name__ == "__main__":
    init_database()