import asyncio
import sys
from sqlalchemy import select
from app.database import engine, Base, AsyncSessionLocal
from app.models.mission import Mission
from app.models.sub_mission import SousMission

# Tentative d'import dynamique pour éviter l'erreur de module
try:
    from app.schemas.constants import MISSIONS_INITIALES
    print("DEBUG: Import de MISSIONS_INITIALES réussi.")
except ImportError as e:
    print(f"DEBUG: Erreur d'import des constantes : {e}")
    sys.exit(1)

async def init_db():
    print("DEBUG: Entrée dans la fonction init_db")
    
    async with engine.begin() as conn:
        print("DEBUG: Suppression et recréation des tables...")
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        print("DEBUG: Tables créées avec succès.")

    async with AsyncSessionLocal() as session:
        # On vérifie le contenu de la constante
        print(f"DEBUG: Contenu de MISSIONS_INITIALES: {list(MISSIONS_INITIALES.keys())}")
        
        if not MISSIONS_INITIALES:
            print("ERREUR: Le dictionnaire MISSIONS_INITIALES est VIDE !")
            return

        print("🌱 Début de l'insertion...")
        for m_idx, (m_titre, subs) in enumerate(MISSIONS_INITIALES.items()):
            mission = Mission(titre=m_titre, ordre=m_idx, is_active=True)
            session.add(mission)
            await session.flush()
            print(f"   ✅ Mission insérée : {m_titre} (ID: {mission.id})")
            
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
                print(f"      - Sous-mission : {s['titre']}")
        
        await session.commit()
        print("✅ FIN DU SCRIPT : Tout est en base.")

if __name__ == "__main__":
    asyncio.run(init_db())