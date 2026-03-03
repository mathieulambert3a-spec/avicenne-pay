from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload
from passlib.context import CryptContext
from typing import Optional, List

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User, Role, Site, Programme, MATIERES
from app.models.mission import Mission
from app.models.sub_mission import SousMission 

router = APIRouter(prefix="/users")
templates = Jinja2Templates(directory="app/templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.get("", response_class=HTMLResponse)
async def list_users(
    request: Request, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # --- FILTRAGE ET TRI PAR NOM/PRENOM ---
    query = select(User).order_by(User.nom, User.prenom)
    
    if current_user.role == Role.admin:
        pass 
    elif current_user.role == Role.coordo:
        query = query.where(User.site == current_user.site)
    elif current_user.role == Role.resp:
        query = query.where(
            or_(
                User.id == current_user.id,
                and_(
                    User.role == Role.tcp,
                    User.site == current_user.site,
                    User.matiere == current_user.matiere
                )
            )
        )
    else: 
        query = query.where(User.id == current_user.id)

    result = await db.execute(query)
    users = result.scalars().all()
    
    return templates.TemplateResponse(
        "users.html", 
        {
            "request": request, 
            "users": users, 
            "current_user": current_user, 
            "roles": list(Role),
            "sites": list(Site),
            "programmes": list(Programme),
            "matieres": MATIERES 
        }
    )

# --- NOUVELLE ROUTE : AFFICHER LE FORMULAIRE DE PERMISSIONS ---
@router.get("/{user_id}/permissions", response_class=HTMLResponse)
async def get_user_permissions(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Récupérer l'utilisateur cible
    res = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.missions_autorisees))
    )
    target_user = res.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # --- Bloquer si c'est un coordinateur ---
    if target_user.role == Role.coordo:
        raise HTTPException(
            status_code=400, 
            detail="Les coordinateurs n'ont pas de déclarations à paramétrer."
        )

    # 2. Vérification des droits d'accès
    allowed = False
    if current_user.role == Role.admin:
        allowed = True
    elif current_user.role == Role.coordo:
        allowed = (target_user.site == current_user.site)
    elif current_user.role == Role.resp:
        allowed = (target_user.role == Role.tcp and target_user.site == current_user.site and target_user.matiere == current_user.matiere)

    if not allowed:
        raise HTTPException(status_code=403, detail="Accès refusé à ce périmètre.")

    # 3. Récupérer le catalogue complet des missions
    missions_res = await db.execute(
        select(Mission).options(selectinload(Mission.sous_missions)).order_by(Mission.ordre)
    )
    all_missions = missions_res.scalars().all()

    # 4. Préparer les IDs déjà cochés
    current_permissions_ids = [sm.id for sm in target_user.missions_autorisees]

    return templates.TemplateResponse(
        "user_permissions.html",
        {
            "request": request,
            "target_user": target_user,
            "all_missions": all_missions,
            "current_permissions_ids": current_permissions_ids,
            "current_user": current_user
        }
    )

# --- ENREGISTRER LES PERMISSIONS ---
@router.post("/{user_id}/permissions")
async def update_user_permissions(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Récupérer les données du formulaire
    form_data = await request.form()
    sous_mission_ids = form_data.getlist("sous_mission_ids")
    
    try:
        sous_mission_ids = [int(sid) for sid in sous_mission_ids]
    except ValueError:
        raise HTTPException(status_code=400, detail="Identifiants de missions invalides.")

    # 2. Récupérer l'utilisateur cible
    res = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.missions_autorisees))
    )
    target_user = res.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # --- 2.5 RÈGLE MÉTIER : Pas de missions pour les coordinateurs ---
    if target_user.role == Role.coordo:
        raise HTTPException(
            status_code=400, 
            detail="Les coordinateurs ne remplissent pas de déclarations."
        )

    # 3. SÉCURITÉ : Vérification des droits (votre code existant)
    allowed = False
    if current_user.role == Role.admin:
        allowed = True
    elif current_user.role == Role.coordo:
        allowed = (target_user.site == current_user.site)
    elif current_user.role == Role.resp:
        allowed = (
            target_user.role == Role.tcp and 
            target_user.site == current_user.site and 
            target_user.matiere == current_user.matiere
        )

    if not allowed:
        raise HTTPException(status_code=403, detail="Opération non autorisée.")

    # 4. MISE À JOUR
    if sous_mission_ids:
        sm_res = await db.execute(
            select(SousMission).where(SousMission.id.in_(sous_mission_ids))
        )
        target_user.missions_autorisees = list(sm_res.scalars().all())
    else:
        target_user.missions_autorisees = []

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Erreur : {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'enregistrement.")

    return RedirectResponse(url="/users", status_code=303)

@router.post("/create")
async def create_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    nom: str = Form(""),       # Ajouté si absent
    prenom: str = Form(""),    # Ajouté si absent
    site: Optional[str] = Form(None),
    programme: Optional[str] = Form(None),
    matiere: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        target_role = Role(role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Rôle invalide")

    # Initialisation des variables de sécurité
    new_user_site = None
    new_user_prog = None
    new_user_matiere = None

    # --- LOGIQUE MÉTIER AVICENNE ---
    
    if current_user.role == Role.admin:
        # L'admin peut tout créer, mais on suit ta règle :
        # On ne convertit en Enum que SI la valeur n'est pas vide
        if target_role != Role.admin:
            if site and site.strip(): 
                new_user_site = Site(site)
            
            # Si c'est un vacataire/resp, il lui faut programme et matière
            if target_role in [Role.resp, Role.tcp]:
                if programme and programme.strip():
                    new_user_prog = Programme(programme)
                new_user_matiere = matiere if matiere and matiere.strip() else None

    elif current_user.role == Role.coordo:
        # Le Coordo ne crée que des Resp ou TCP sur SON site
        if target_role not in [Role.resp, Role.tcp]:
            raise HTTPException(status_code=403, detail="Un coordinateur ne peut créer que des Responsables ou des Vacataires.")
        
        new_user_site = current_user.site # Héritage forcé du site
        if programme and programme.strip():
            new_user_prog = Programme(programme)
        new_user_matiere = matiere

    elif current_user.role == Role.resp:
        # Le Resp ne crée que des TCP sur SON site, SON programme et SA matière
        if target_role != Role.tcp:
            raise HTTPException(status_code=403, detail="Un Responsable ne peut créer que des Vacataires (TCP).")
        
        new_user_site = current_user.site
        new_user_prog = current_user.programme
        new_user_matiere = current_user.matiere

    # --- ENREGISTREMENT ---
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email déjà utilisé.")

    new_user = User(
        email=email,
        nom=nom,
        prenom=prenom,
        hashed_password=pwd_context.hash(password),
        role=target_role,
        site=new_user_site,
        programme=new_user_prog, 
        matiere=new_user_matiere,
        profil_complete=False
    )

    db.add(new_user)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Erreur commit: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la création.")

    return RedirectResponse(url="/users", status_code=303)

@router.post("/{user_id}/delete")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user_to_delete = result.scalar_one_or_none()

    if not user_to_delete or user_to_delete.id == current_user.id:
        raise HTTPException(status_code=403)

    await db.delete(user_to_delete)
    await db.commit()
    return RedirectResponse(url="/users", status_code=303)