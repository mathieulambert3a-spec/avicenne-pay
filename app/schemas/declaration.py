from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.declaration import StatutDeclaration

# --- SCHÉMAS DE RÉFÉRENCE (POUR LA LECTURE) ---

class SousMissionSimpleOut(BaseModel):
    """Affiche les détails de la sous-mission dans une ligne de déclaration"""
    id: int
    titre: str
    tarif: float
    unite: Optional[str] = None

    class Config:
        from_attributes = True


class LigneDeclarationOut(BaseModel):
    """Représente une ligne de mission avec le détail de la sous-mission associée"""
    id: int
    declaration_id: int
    sous_mission_id: int
    quantite: float
    # Cette relation permet d'afficher l'unité et le titre au frontend
    sous_mission: Optional[SousMissionSimpleOut] = None

    class Config:
        from_attributes = True


class DeclarationOut(BaseModel):
    """Schéma complet d'une déclaration renvoyée par l'API"""
    id: int
    user_id: int
    mois: int
    annee: int
    statut: StatutDeclaration
    commentaire_refus: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Liste des lignes avec détails
    lignes: List[LigneDeclarationOut] = []
    
    # Calculs automatiques
    total_montant: float = 0.0

    class Config:
        from_attributes = True


# --- SCHÉMAS POUR LA CRÉATION / MODIFICATION ---

class LigneDeclarationCreate(BaseModel):
    """Utilisé pour envoyer une ligne depuis le formulaire"""
    sous_mission_id: int
    quantite: float = Field(..., gt=0, description="La quantité doit être supérieure à 0")


class DeclarationCreate(BaseModel):
    """Utilisé pour créer une nouvelle déclaration"""
    mois: int = Field(..., ge=1, le=12)
    annee: int = Field(..., ge=2020)
    lignes: List[LigneDeclarationCreate]


class DeclarationUpdate(BaseModel):
    """Utilisé pour modifier une déclaration existante ou changer son statut"""
    mois: Optional[int] = None
    annee: Optional[int] = None
    statut: Optional[StatutDeclaration] = None
    commentaire_refus: Optional[str] = None
    lignes: Optional[List[LigneDeclarationCreate]] = None