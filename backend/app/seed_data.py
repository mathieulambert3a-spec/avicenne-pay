# backend/app/seed_data.py
from app.database import SessionLocal
from app.models.mission import Mission, TypeContratMission
from app.core.referentiels import MISSIONS_INITIALES

def seed_missions():
    print("⏳ Remplissage du catalogue des missions et tarifs...")
    db = SessionLocal()
    
    try:
        total_ajoute = 0
        
        for categorie, liste_niveaux in MISSIONS_INITIALES.items():
            for niveau in liste_niveaux:
                titre = niveau["titre"]
                
                # On vérifie si la mission existe déjà dans cette catégorie pour éviter les doublons
                existing_mission = db.query(Mission).filter(
                    Mission.categorie == categorie,
                    Mission.titre == titre
                ).first()
                
                if not existing_mission:
                    # On crée l'objet en mappant exactement tes colonnes
                    nouvelle_mission = Mission(
                        categorie=categorie,
                        titre=titre,
                        tarif_unitaire=float(niveau["tarif"]),
                        unite=niveau["unite"],
                        is_resp_only=niveau.get("is_resp", False),
                        type_contrat=TypeContratMission.both # On met BOTH par défaut pour couvrir tous les cas
                    )
                    db.add(nouvelle_mission)
                    total_ajoute += 1
        
        db.commit()
        print(f"✅ Succès ! {total_ajoute} missions et tarifs importés dans Neon.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Une erreur est survenue lors de l'import : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_missions()