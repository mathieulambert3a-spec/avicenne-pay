# backend/routers/paie.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.user import User, Role
from app.models.declaration import Declaration, StatutDeclaration, LigneDeclaration
from app.schemas.paie import SynthesePaieOut, LigneSynthesePaie
from app.core.security import check_is_at_least_coordo # 👈 On réutilise notre brique !

router = APIRouter(prefix="/paie", tags=["Paie & Synthèses"])

@router.get("/synthese-mensuelle", response_model=SynthesePaieOut)
def get_synthese_mensuelle(
    mois: int,
    annee: int,
    db: Session = Depends(get_db),
    # 🛡️ 1. Sécurité : Seuls les admins et coordos peuvent voir la paie globale
    current_user: User = Depends(check_is_at_least_coordo)
):
    # 📊 2. Construction de la requête SQL d'agrégation (Sécurisée)
    # On calcule la somme des rémunérations par utilisateur sur les déclarations VALIDÉES
    query = db.query(
        User.id.label("user_id"),
        User.nom.label("nom"),
        User.prenom.label("prenom"),
        User.site.label("site"),
        func.count(Declaration.id).label("total_declarations"),
        # 💡 On fait la somme du montant total de chaque déclaration validée
        func.sum(
            db.query(func.sum(LigneDeclaration.quantite * LigneDeclaration.tarif_applique))
            .filter(LigneDeclaration.declaration_id == Declaration.id)
            .scalar_subquery()
        ).label("montant_brut")
    ).join(Declaration, User.id == Declaration.user_id)\
     .filter(
         Declaration.mois == mois,
         Declaration.annee == annee,
         Declaration.statut == StatutDeclaration.validee
     )

    # 🔒 3. Le Coordo ne voit que son site (L'admin voit tout)
    if current_user.role == Role.coordo:
        query = query.filter(User.site == current_user.site)

    # On groupe par utilisateur
    resultats = query.group_by(User.id).all()

    # 🚀 4. On formate la réponse
    lignes_details = []
    montant_global = 0.0

    for res in resultats:
        montant_brut = round(res.montant_brut, 2) if res.montant_brut else 0.0
        montant_global += montant_brut
        
        lignes_details.append(
            LigneSynthesePaie(
                user_id=res.user_id,
                nom=res.nom,
                prenom=res.prenom,
                site=res.site,
                # On affiche le nombre de déclarations validées traitées
                total_declarations=res.total_declarations, 
                montant_brut_total=montant_brut
            )
        )

    return SynthesePaieOut(
        mois=mois,
        annee=annee,
        total_intervenants=len(lignes_details),
        montant_global=round(montant_global, 2),
        details=lignes_details
    )