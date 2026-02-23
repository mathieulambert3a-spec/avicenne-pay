from datetime import datetime
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User, Role, Site
from app.models.mission import Mission
from app.models.sub_mission import SousMission
from app.models.declaration import Declaration, StatutDeclaration
from app.models.ligne_declaration import LigneDeclaration

router = APIRouter(prefix="/declarations")
templates = Jinja2Templates(directory="app/templates")

MOIS_LABELS = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
    5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre",
}

def filter_missions_for_user(missions: list, user: User) -> list:
    """Filtre les missions selon le rôle de l'utilisateur.
    La mission resp_only n'est visible que pour le rôle RESP.
    """
    filtered = []
    for m in missions:
        if m.resp_only and user.role != Role.resp:
            continue
        filtered.append(m)
    return filtered


@router.get("", response_class=HTMLResponse)
async def list_declarations(
    request: Request,
    site: Optional[str] = None,
    mois: Optional[int] = None,
    annee: Optional[int] = None,
    statut: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Declaration).options(selectinload(Declaration.user))

    # Visibility rules
    if current_user.role in (Role.admin, Role.coordo, Role.resp, Role.tcp):
        if site:
            query = query.join(Declaration.user).where(User.site == Site(site))
    else:
        query = query.where(Declaration.user_id == current_user.id)

    if mois:
        query = query.where(Declaration.mois == mois)
    if annee:
        query = query.where(Declaration.annee == annee)
    if statut:
        query = query.where(Declaration.statut == StatutDeclaration(statut))

    query = query.order_by(Declaration.annee.desc(), Declaration.mois.desc())
    result = await db.execute(query)
    declarations = result.scalars().all()

    return templates.TemplateResponse(
        "declarations/list.html",
        {
            "request": request,
            "user": current_user,
            "declarations": declarations,
            "mois_labels": MOIS_LABELS,
            "sites": list(Site),
            "current_site": site,
            "current_mois": mois,
            "current_annee": annee,
            "current_statut": statut,
            "statuts": list(StatutDeclaration),
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def new_declaration_form(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.profil_complete:
        return RedirectResponse("/profile?warning=profil_incomplet", status_code=302)

    missions_result = await db.execute(
        select(Mission).where(Mission.is_active == True).order_by(Mission.ordre)
    )
    missions = missions_result.scalars().all()
    for m in missions:
        await db.refresh(m, ["sous_missions"])

    missions = filter_missions_for_user(missions, current_user)

    now = datetime.now()
    return templates.TemplateResponse(
        "declarations/form.html",
        {
            "request": request,
            "user": current_user,
            "declaration": None,
            "missions": missions,
            "default_mois": now.month,
            "default_annee": now.year,
            "mois_labels": MOIS_LABELS,
            "lignes_map": {},
        },
    )


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

    declaration = Declaration(
        user_id=current_user.id,
        mois=mois,
        annee=annee,
        statut=StatutDeclaration.brouillon,
    )
    db.add(declaration)
    await db.flush()

    # Charger toutes les missions resp_only pour validation
    resp_only_missions_result = await db.execute(
        select(Mission).where(Mission.resp_only == True)
    )
    resp_only_missions = resp_only_missions_result.scalars().all()
    resp_only_sm_ids = set()
    for m in resp_only_missions:
        await db.refresh(m, ["sous_missions"])
        for sm in m.sous_missions:
            resp_only_sm_ids.add(sm.id)

    for key, value in form_data.items():
        if key.startswith("quantite_") and value:
            try:
                sm_id = int(key.split("_")[1])
                # Bloquer si la sous-mission est resp_only et que l'utilisateur n'est pas RESP
                if sm_id in resp_only_sm_ids and current_user.role != Role.resp:
                    continue
                quantite = float(value)
                # Pour les sous-missions resp_only, forcer la quantité à 1
                if sm_id in resp_only_sm_ids:
                    quantite = 1.0
                if quantite > 0:
                    ligne = LigneDeclaration(
                        declaration_id=declaration.id,
                        sous_mission_id=sm_id,
                        quantite=quantite,
                    )
                    db.add(ligne)
            except (ValueError, IndexError):
                pass

    if action == "soumettre":
        declaration.statut = StatutDeclaration.soumise
        declaration.soumise_le = datetime.now()

    await db.commit()
    return RedirectResponse("/declarations", status_code=302)


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
    if not declaration:
        return RedirectResponse("/declarations", status_code=302)

    # Access control
    if current_user.role not in (Role.admin, Role.coordo, Role.resp, Role.tcp):
        if declaration.user_id != current_user.id:
            return RedirectResponse("/declarations", status_code=302)

    total = sum(l.quantite * l.sous_mission.tarif for l in declaration.lignes)

    return templates.TemplateResponse(
        "declarations/detail.html",
        {
            "request": request,
            "user": current_user,
            "declaration": declaration,
            "mois_labels": MOIS_LABELS,
            "total": total,
        },
    )


@router.get("/{decl_id}/edit", response_class=HTMLResponse)
async def edit_declaration_form(
    request: Request,
    decl_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Declaration)
        .options(selectinload(Declaration.lignes))
        .where(Declaration.id == decl_id)
    )
    declaration = result.scalar_one_or_none()
    if not declaration:
        return RedirectResponse("/declarations", status_code=302)

    # Permissions
    can_edit = False
    if declaration.statut == StatutDeclaration.brouillon:
        can_edit = (declaration.user_id == current_user.id) or current_user.role in (Role.admin, Role.coordo)
    elif declaration.statut == StatutDeclaration.soumise:
        can_edit = current_user.role in (Role.admin, Role.coordo)

    if not can_edit:
        return RedirectResponse(f"/declarations/{{decl_id}}", status_code=302)

    missions_result = await db.execute(
        select(Mission).where(Mission.is_active == True).order_by(Mission.ordre)
    )
    missions = missions_result.scalars().all()
    for m in missions:
        await db.refresh(m, ["sous_missions"])

    missions = filter_missions_for_user(missions, current_user)

    lignes_map = {l.sous_mission_id: l.quantite for l in declaration.lignes}

    return templates.TemplateResponse(
        "declarations/form.html",
        {
            "request": request,
            "user": current_user,
            "declaration": declaration,
            "missions": missions,
            "default_mois": declaration.mois,
            "default_annee": declaration.annee,
            "mois_labels": MOIS_LABELS,
            "lignes_map": lignes_map,
        },
    )


@router.post("/{decl_id}/edit")
async def update_declaration(
    request: Request,
    decl_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Declaration)
        .options(selectinload(Declaration.lignes))
        .where(Declaration.id == decl_id)
    )
    declaration = result.scalar_one_or_none()
    if not declaration:
        return RedirectResponse("/declarations", status_code=302)

    # Permissions
    can_edit = False
    if declaration.statut == StatutDeclaration.brouillon:
        can_edit = (declaration.user_id == current_user.id) or current_user.role in (Role.admin, Role.coordo)
    elif declaration.statut == StatutDeclaration.soumise:
        can_edit = current_user.role in (Role.admin, Role.coordo)

    if not can_edit:
        return RedirectResponse(f"/declarations/{{decl_id}}", status_code=302)

    form_data = await request.form()
    action = form_data.get("action", "brouillon")

    # Charger toutes les missions resp_only pour validation
    resp_only_missions_result = await db.execute(
        select(Mission).where(Mission.resp_only == True)
    )
    resp_only_missions = resp_only_missions_result.scalars().all()
    resp_only_sm_ids = set()
    for m in resp_only_missions:
        await db.refresh(m, ["sous_missions"])
        for sm in m.sous_missions:
            resp_only_sm_ids.add(sm.id)

    # Delete existing lines
    for ligne in declaration.lignes:
        await db.delete(ligne)
    await db.flush()

    for key, value in form_data.items():
        if key.startswith("quantite_") and value:
            try:
                sm_id = int(key.split("_")[1])
                # Bloquer si la sous-mission est resp_only et que l'utilisateur n'est pas RESP
                if sm_id in resp_only_sm_ids and current_user.role != Role.resp:
                    continue
                quantite = float(value)
                # Pour les sous-missions resp_only, forcer la quantité à 1
                if sm_id in resp_only_sm_ids:
                    quantite = 1.0
                if quantite > 0:
                    ligne = LigneDeclaration(
                        declaration_id=declaration.id,
                        sous_mission_id=sm_id,
                        quantite=quantite,
                    )
                    db.add(ligne)
            except (ValueError, IndexError):
                pass

    if action == "soumettre" and declaration.statut == StatutDeclaration.brouillon:
        declaration.statut = StatutDeclaration.soumise
        declaration.soumise_le = datetime.now()

    await db.commit()
    return RedirectResponse(f"/declarations/{{decl_id}}", status_code=302)