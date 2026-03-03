import asyncio
import sys
import os

# On s'assure que Python trouve le dossier 'app'
sys.path.append(os.getcwd())

from app.database import engine, Base, AsyncSessionLocal
from app.models.user import User
from app.models.mission import Mission
from app.models.sub_mission import SousMission
from app.models.ligne_declaration import LigneDeclaration
from app.models.declaration import Declaration

# ON IMPORTE TES DONNÉES EXCEL ICI
from app.schemas.constants import MISSIONS_INITIALES

async def init():
    print("⏳ Suppression et création des tables en cours...")
    async with engine.begin() as conn:
        # On repart de zéro pour éviter les doublons
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    print("🌱 Importation des missions par défaut...")
    
    async with AsyncSessionLocal() as session:
        # On boucle sur ton dictionnaire MISSIONS_INITIALES
        for m_idx, (m_titre, subs) in enumerate(MISSIONS_INITIALES.items()):
            # 1. Créer la mission parente
            mission = Mission(titre=m_titre, ordre=m_idx, is_active=True)
            session.add(mission)
            await session.flush() # On récupère l'ID pour les sous-missions
            print(f"   ✅ Mission créée : {m_titre}")
            
            # 2. Créer les sous-missions rattachées
            for s_idx, s in enumerate(subs):
                sm = SousMission(
                    mission_id=mission.id,
                    titre=s["titre"],
                    unite=s["unite"],
                    tarif=s["tarif"],
                    ordre=s_idx,
                    is_active=True
                )
                session.add(sm)
                print(f"      - {s['titre']}")
        
        await session.commit()

    print("✅ Base de données initialisée avec TOUTES les données !")

if __name__ == "__main__":
    asyncio.run(init())