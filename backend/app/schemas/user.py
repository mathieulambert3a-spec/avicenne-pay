# backend/schemas/user.py

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from app.core.referentiels import MATIERES, Role, Site, TypeContrat

# ── 1. LE SCHÉMA DE BASE (Champs communs) ───────────────────────────────────
class UserBase(BaseModel):
    email: EmailStr
    nom: str
    prenom: str
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None


# ── 2. INSCRIPTION / CRÉATION ───────────────────────────────────────────────
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: Role = Role.admin
    site: Optional[Site] = None
    programme: Optional[str] = None
    matiere: Optional[str] = None


# ── 3. MISE À JOUR PAR L'UTILISATEUR (Son Profil) ──────────────────────────
class UserProfileUpdate(BaseModel):
    """
    Champs que l'utilisateur lambda peut modifier lui-même.
    Le NSS et l'IBAN arrivent en CLAIR du front (on s'occupe de les chiffrer après).
    """
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None
    nss: Optional[str] = None   
    iban: Optional[str] = None  


# ── 4. MISE À JOUR PAR L'ADMIN (Anciennement ton UserUpdate) ────────────────
class UserUpdate(UserProfileUpdate):
    """
    L'admin hérite de tout ce que le user peut modifier, 
    mais lui peut toucher au pro (rôle, etc).
    """
    email: Optional[EmailStr] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None
    site: Optional[Site] = None
    programme: Optional[str] = None
    matiere: Optional[str] = None

    @field_validator("programme")
    @classmethod
    def validate_programme(cls, v: str):
        if v and v not in MATIERES.keys():
            raise ValueError(f"Le programme doit être l'un des suivants : {list(MATIERES.keys())}")
        return v

    @field_validator("matiere")
    @classmethod
    def validate_matiere(cls, v: str, values):
        # Récupération sécurisée des données de la requête
        programme_saisi = values.data.get("programme")
        
        if v and programme_saisi:
            matieres_possibles = MATIERES.get(programme_saisi, [])
            if v not in matieres_possibles:
                raise ValueError(f"La matière '{v}' n'existe pas pour le programme '{programme_saisi}'.")
        return v


# ── 5. SORTIE (Ce que l'API renvoie au Front) ──────────────────────────────
class UserOut(UserBase):
    id: int
    role: Role
    is_active: bool
    site: Optional[Site] = None
    programme: Optional[str] = None
    matiere: Optional[str] = None
    profil_complete: bool
    
    # Propriété déduite du rôle (calculée automatiquement)
    type_contrat: Optional[TypeContrat] = None 

    class Config:
        from_attributes = True

# ── 6. SÉCURITÉ MOTS DE PASSE ──────────────────────────────────────────────
class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

class AdminPasswordReset(BaseModel):
    new_password: str = Field(..., min_length=6)