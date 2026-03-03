from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.config import FERNET_KEY
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User, Filiere, Annee, Site, Programme, MATIERES

router = APIRouter(prefix="/profile")
templates = Jinja2Templates(directory="app/templates")


def get_fernet():
    if FERNET_KEY:
        return Fernet(FERNET_KEY.encode() if isinstance(FERNET_KEY, str) else FERNET_KEY)
    return None


def encrypt(value: str, f: Optional[Fernet]) -> str:
    if f and value:
        return f.encrypt(value.encode()).decode()
    return value


def decrypt(value: str, f: Optional[Fernet]) -> str:
    if f and value:
        try:
            return f.decrypt(value.encode()).decode()
        except (InvalidToken, Exception):
            return value
    return value or ""


@router.get("", response_class=HTMLResponse)
async def profile_page(request: Request, current_user: User = Depends(get_current_user)):
    f = get_fernet()
    nss = decrypt(current_user.nss_encrypted or "", f)
    iban = decrypt(current_user.iban_encrypted or "", f)
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": current_user,
            "nss": nss,
            "iban": iban,
            "filieres": list(Filiere),
            "annees": list(Annee),
            "sites": list(Site),
            "programmes": list(Programme),
            "matieres": MATIERES,
        },
    )


@router.post("", response_class=HTMLResponse)
async def update_profile(
    request: Request,
    nom: str = Form(""),
    prenom: str = Form(""),
    adresse: str = Form(""),
    code_postal: str = Form(""),
    ville: str = Form(""),
    telephone: str = Form(""),
    nss: str = Form(""),
    iban: str = Form(""),
    filiere: str = Form(""),
    annee: str = Form(""),
    site: str = Form(""),
    programme: str = Form(""),
    matiere: str = Form(""),
    profil_complete: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    f = get_fernet()
    current_user.nom = nom or None
    current_user.prenom = prenom or None
    current_user.adresse = adresse or None
    current_user.code_postal = code_postal or None
    current_user.ville = ville or None
    current_user.telephone = telephone or None
    if nss:
        current_user.nss_encrypted = encrypt(nss, f)
    if iban:
        current_user.iban_encrypted = encrypt(iban, f)

    current_user.filiere = Filiere(filiere) if filiere else None
    current_user.annee = Annee(annee) if annee else None
    current_user.site = Site(site) if site else None
    current_user.programme = Programme(programme) if programme else None
    current_user.matiere = matiere or None
    current_user.profil_complete = profil_complete == "on"

    await db.commit()
    await db.refresh(current_user)

    nss_display = decrypt(current_user.nss_encrypted or "", f)
    iban_display = decrypt(current_user.iban_encrypted or "", f)

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": current_user,
            "nss": nss_display,
            "iban": iban_display,
            "filieres": list(Filiere),
            "annees": list(Annee),
            "sites": list(Site),
            "programmes": list(Programme),
            "matieres": MATIERES,
            "success": "Profil mis à jour avec succès.",
        },
    )
