from pydantic import BaseModel
from typing import Optional, List
from app.models.declaration import StatutDeclaration


class LigneCreate(BaseModel):
    sous_mission_id: int
    quantite: float


class DeclarationCreate(BaseModel):
    mois: int
    annee: int
    lignes: List[LigneCreate] = []


class DeclarationUpdate(BaseModel):
    lignes: Optional[List[LigneCreate]] = None
