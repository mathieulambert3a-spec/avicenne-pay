from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import Role, Filiere, Annee, Site, Programme


class UserCreate(BaseModel):
    email: str
    password: str
    role: Role


class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[Role] = None
    nom: Optional[str] = None
    prenom: Optional[str] = None
    adresse: Optional[str] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None
    telephone: Optional[str] = None
    nss: Optional[str] = None
    iban: Optional[str] = None
    filiere: Optional[Filiere] = None
    annee: Optional[Annee] = None
    site: Optional[Site] = None
    programme: Optional[Programme] = None
    matiere: Optional[str] = None
    profil_complete: Optional[bool] = None


class UserRead(BaseModel):
    id: int
    email: str
    role: Role
    nom: Optional[str] = None
    prenom: Optional[str] = None
    profil_complete: bool

    class Config:
        from_attributes = True
