from datetime import datetime
from fastapi import APIRouter, Request, Depends, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User, Role, Site
from app.models.mission import Mission
from app.models.sub_mission import SousMission
from app.models.declaration import Declaration, LigneDeclaration, StatutDeclaration

router = APIRouter(prefix="/declarations")
templates = Jinja2Templates(directory="app/templates")

MOIS_LABELS = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
    5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre",
}

# --- FONCTION DE FILTRAGE DES MISSIONS ---
def filter_missions_for_user(missions: list, user: User) -> list:
    # Récupération des IDs autorisés si la relation existe
    authorized_sm_ids = [sm.id for sm in user.missions_autorisees] if hasattr(user, 'missions_autorisees') and user.missions_autorisees else []
    
    filtered_missions = []
    for m in missions:
        # 1. Filtre Rôle : certaines missions sont réservées au management (RESP_ONLY)
        if m.resp_only and user.role not in (Role.admin, Role.coordo, Role.resp):
            continue
            
        # 2. Filtre Périmètre personnalisé (Si l'admin a restreint ses sous-missions)
        if authorized_sm_ids:
            # On ne garde que les sous-missions dont l'ID est dans la liste blanche
            m.sous_missions = [sm for sm in m.sous_missions if sm.id in authorized_sm_ids]
            if not m.sous_missions:
                continue
        
        filtered_missions.append(m)
    return filtered_missions

# --- LISTE DES DÉCLARATIONS ---
@router.get("", response_class=HTMLResponse)
async def list_declarations(
    request: Request,
    site: Optional[str] = Query(None),
    mois: Optional[str] = Query(None),
    annee: Optional[str] = Query(None),
    statut: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Declaration).join(User, Declaration.user_id == User.id).options(selectinload(Declaration.user))

    # Filtrage selon les droits
    if current_user.role == Role.admin:
        if site and site != "":
            query = query.where(User.site == Site(site))
    elif current_user.role == Role.coordo:
        query = query.where(User.site == current_user.site)
    elif current_user.role == Role.resp:
        query = query.where(
            or_(
                Declaration.user_id == current_user.id,
                and_(
                    User.role == Role.tcp,
                    User.site == current_user.site,
                    User.matiere == current_user.matiere
                )
            )
        )
    else: # TCP
        query = query.where(Declaration.user_id == current_user.id)

    # Filtres de recherche
    if mois and mois.isdigit():
        query = query.where(Declaration.mois == int(mois))
    if annee and annee.isdigit():
        query = query.where(Declaration.annee == int(annee))
    if statut and statut != "":
        query = query.where(Declaration.statut == StatutDeclaration(statut))

    query = query.order_by(Declaration.annee.desc(), Declaration.mois.desc())
    result = await db.execute(query)
    declarations = result.scalars().all()

    return templates.TemplateResponse(
        "declarations/list.html",
        {
            "request": request, "user": current_user, "declarations": declarations,
            "mois_labels": MOIS_LABELS, "sites": list(Site), 
            "current_site": site,
            "current_mois": int(mois) if (mois and mois.isdigit()) else None, 
            "current_annee": int(annee) if (annee and annee.isdigit()) else None, 
            "current_statut": statut,
            "statuts": list(StatutDeclaration),
        },
    )

# --- FORMULAIRE NOUVELLE DÉCLARATION ---
@router.get("/new", response_class=HTMLResponse)
async def new_declaration_form(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role in (Role.admin, Role.coordo):
        return RedirectResponse("/declarations?error=saisie_interdite_management", status_code=302)

    if not current_user.profil_complete:
        return RedirectResponse("/profile?warning=profil_incomplet", status_code=302)

    res_user = await db.execute(
        select(User).where(User.id == current_user.id).options(selectinload(User.missions_autorisees))
    )
    user_full = res_user.scalar_one()

    now = datetime.now()
    existing_res = await db.execute(
        select(Declaration.mois).where(
            Declaration.user_id == current_user.id, 
            Declaration.annee == now.year
        )
    )
    mois_deja_faits = existing_res.scalars().all()

    missions_result = await db.execute(
        select(Mission)
        .where(Mission.is_active == True)
        .options(selectinload(Mission.sous_missions))
        .order_by(Mission.ordre)
    )
    missions = missions_result.scalars().all()
    missions = filter_missions_for_user(missions, user_full)

    return templates.TemplateResponse(
        "declarations/form.html",
        {
            "request": request, "user": user_full, "declaration": None,
            "missions": missions, "default_mois": now.month, "default_annee": now.year,
            "mois_labels": MOIS_LABELS, "lignes_map": {}, "mois_interdits": mois_deja_faits
        },
    )

# --- SAUVEGARDE NOUVELLE DÉCLARATION ---
@router.post("/new")
async def create_declaration(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.profil_complete:
        return RedirectResponse("/profile?warning=profil_incomplet", status_code=302)

    form_data = await request.form()
    mois = int(form_data.get("mois", datetime.now().month))
    annee = int(form_data.get("annee", datetime.now().year))
    action = form_data.get("action", "brouillon")

    # Vérification doublon
    existing_check = await db.execute(
        select(Declaration).where(
            Declaration.user_id == current_user.id,
            Declaration.mois == mois,
            Declaration.annee == annee
        )
    )
    if existing_check.scalars().first():
        return RedirectResponse("/declarations?error=deja_existant", status_code=302)

    declaration = Declaration(
        user_id=current_user.id,
        mois=mois,
        annee=annee,
        statut=StatutDeclaration.brouillon,
        site=current_user.site,
        programme=current_user.programme
    )
    db.add(declaration)
    await db.flush()

    # AJOUT DES LIGNES (FIXÉ : Utilise LigneDeclaration)
    for key, value in form_data.items():
        if key.startswith("quantite_") and value:
            try:
                sm_id = int(key.split("_")[1])
                quantite = float(value.replace(',', '.'))
                if quantite > 0:
                    db.add(LigneDeclaration(declaration_id=declaration.id, sous_mission_id=sm_id, quantite=quantite))
            except (ValueError, IndexError): pass

    if action == "soumettre":
        declaration.statut = StatutDeclaration.soumise
        declaration.soumise_le = datetime.now()

    await db.commit()
    return RedirectResponse("/declarations", status_code=302)

# --- DÉTAIL D'UNE DÉCLARATION ---
@router.get("/{decl_id}", response_class=HTMLResponse)
async def view_declaration(
    request: Request,
    decl_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Declaration)
        .options(
            selectinload(Declaration.user),
            selectinload(Declaration.lignes).selectinload(LigneDeclaration.sous_mission).selectinload(SousMission.mission),
        )
        .where(Declaration.id == decl_id)
    )
    declaration = result.scalar_one_or_none()
    if not declaration: return RedirectResponse("/declarations", status_code=302)

    # Vérification des droits d'accès
    allowed = False
    if current_user.role == Role.admin: allowed = True
    elif current_user.role == Role.coordo: allowed = (declaration.user.site == current_user.site)
    elif current_user.role == Role.resp:
        allowed = (declaration.user_id == current_user.id or (
            declaration.user.role == Role.tcp and 
            declaration.user.site == current_user.site and 
            declaration.user.matiere == current_user.matiere
        ))
    else: allowed = (declaration.user_id == current_user.id)

    if not allowed: return RedirectResponse("/declarations?error=acces_refuse", status_code=302)

    total = sum(l.quantite * l.sous_mission.tarif for l in declaration.lignes)
    return templates.TemplateResponse(
        "declarations/detail.html",
        {"request": request, "user": current_user, "declaration": declaration, "mois_labels": MOIS_LABELS, "total": total},
    )

# --- FORMULAIRE ÉDITION (BROUILLON) ---
@router.get("/{decl_id}/edit", response_class=HTMLResponse)
async def edit_declaration_form(
    request: Request,
    decl_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Declaration)
        .options(selectinload(Declaration.lignes).selectinload(LigneDeclaration.sous_mission))
        .where(Declaration.id == decl_id)
    )
    declaration = result.scalar_one_or_none()
    if not declaration: return RedirectResponse("/declarations", status_code=302)

    # Seul le proprio en brouillon ou admin peut éditer
    can_edit = (declaration.user_id == current_user.id and declaration.statut == StatutDeclaration.brouillon) or (current_user.role == Role.admin)
    if not can_edit: return RedirectResponse(f"/declarations/{decl_id}", status_code=302)

    res_user = await db.execute(
        select(User).where(User.id == declaration.user_id).options(selectinload(User.missions_autorisees))
    )
    user_full = res_user.scalar_one()

    missions_result = await db.execute(
        select(Mission).where(Mission.is_active == True).options(selectinload(Mission.sous_missions)).order_by(Mission.ordre)
    )
    missions = filter_missions_for_user(missions_result.scalars().all(), user_full)

    lignes_map = {l.sous_mission_id: l.quantite for l in declaration.lignes}
    return templates.TemplateResponse(
        "declarations/form.html",
        {
            "request": request, "user": current_user, "declaration": declaration, "missions": missions,
            "default_mois": declaration.mois, "default_annee": declaration.annee,
            "mois_labels": MOIS_LABELS, "lignes_map": lignes_map,
        },
    )

# --- MISE À JOUR ÉDITION ---
@router.post("/{decl_id}/edit")
async def update_declaration(
    request: Request,
    decl_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Declaration).where(Declaration.id == decl_id))
    declaration = result.scalar_one_or_none()
    if not declaration: return RedirectResponse("/declarations", status_code=302)

    form_data = await request.form()
    action = form_data.get("action", "brouillon")

    # Suppression des anciennes lignes
    await db.execute(delete(LigneDeclaration).where(LigneDeclaration.declaration_id == decl_id))
    
    # Nouvelles lignes
    for key, value in form_data.items():
        if key.startswith("quantite_") and value:
            try:
                sm_id = int(key.split("_")[1])
                quantite = float(value.replace(',', '.'))
                if quantite > 0:
                    db.add(LigneDeclaration(declaration_id=decl_id, sous_mission_id=sm_id, quantite=quantite))
            except (ValueError, IndexError): pass

    if action == "soumettre":
        declaration.statut = StatutDeclaration.soumise
        declaration.soumise_le = datetime.now()
        declaration.commentaire_admin = None

    await db.commit()
    return RedirectResponse(f"/declarations/{decl_id}", status_code=302)

# --- ACTIONS ADMIN (VALIDER / REJETER / SUPPRIMER) ---
@router.post("/{decl_id}/valider")
async def valider_declaration(
    request: Request,
    decl_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in (Role.admin, Role.coordo):
        return RedirectResponse("/declarations?error=non_autorise", status_code=302)

    result = await db.execute(select(Declaration).options(selectinload(Declaration.user)).where(Declaration.id == decl_id))
    declaration = result.scalar_one_or_none()

    if declaration and declaration.statut == StatutDeclaration.soumise:
        if current_user.role == Role.coordo and declaration.user.site != current_user.site:
             return RedirectResponse("/declarations?error=hors_perimetre", status_code=302)
        
        declaration.statut = StatutDeclaration.validee
        await db.commit()
    
    return RedirectResponse(request.headers.get("referer", "/declarations"), status_code=302)

@router.post("/{decl_id}/rejeter")
async def rejeter_declaration(
    request: Request,
    decl_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in (Role.admin, Role.coordo):
        return RedirectResponse("/declarations?error=non_autorise", status_code=302)

    form_data = await request.form()
    commentaire = form_data.get("commentaire_admin", "").strip()

    result = await db.execute(select(Declaration).options(selectinload(Declaration.user)).where(Declaration.id == decl_id))
    declaration = result.scalar_one_or_none()

    if declaration and declaration.statut == StatutDeclaration.soumise:
        if current_user.role == Role.coordo and declaration.user.site != current_user.site:
             return RedirectResponse("/declarations?error=hors_perimetre", status_code=302)
        
        declaration.statut = StatutDeclaration.brouillon
        declaration.commentaire_admin = commentaire 
        await db.commit()
    
    return RedirectResponse(request.headers.get("referer", "/declarations"), status_code=302)

@router.post("/{decl_id}/delete")
async def delete_declaration(
    decl_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != Role.admin:
        return RedirectResponse(f"/declarations/{decl_id}?error=non_autorise", status_code=302)

    result = await db.execute(select(Declaration).where(Declaration.id == decl_id))
    declaration = result.scalar_one_or_none()

    if declaration:
        await db.execute(delete(LigneDeclaration).where(LigneDeclaration.declaration_id == decl_id))
        await db.delete(declaration)
        await db.commit()
        return RedirectResponse("/declarations?info=supprime", status_code=302)
    
    return RedirectResponse("/declarations", status_code=302)