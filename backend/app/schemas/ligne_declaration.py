# backend/schemas/ligne_declaration.py

from pydantic import BaseModel, computed_field

class LigneDeclarationOut(BaseModel):
    id: int
    declaration_id: int
    mission_id: int
    quantite: float
    tarif_applique: float

    # 💡 Pydantic v2 calcule automatiquement ce champ à la volée !
    @computed_field
    def sous_total(self) -> float:
        return round(self.quantite * self.tarif_applique, 2)

    class Config:
        from_attributes = True