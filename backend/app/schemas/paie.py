# backend/schemas/paie.py

from pydantic import BaseModel
from typing import List

class LigneSynthesePaie(BaseModel):
    user_id: int
    nom: str
    prenom: str
    site: str
    total_missions: int
    montant_brut_total: float

class SynthesePaieOut(BaseModel):
    mois: int
    annee: int
    total_intervenants: int
    montant_global: float
    details: List[LigneSynthesePaie]