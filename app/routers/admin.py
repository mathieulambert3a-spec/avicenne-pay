from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List
import csv
import io
import zipfile
from io import BytesIO
from datetime import datetime
from cryptography.fernet import Fernet, InvalidToken
from weasyprint import HTML 

from app.database import get_db
from app.dependencies import require_role
from app.config import FERNET_KEY

# Imports des modèles
from app.models.user import User, Role, Site, Programme
from app.models.declaration import Declaration, LigneDeclaration, StatutDeclaration
from app.models.sub_mission import SousMission
from app.models.mission import Mission

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

# --- SÉCURITÉ : Définition des niveaux d'accès ---
staff_required = require_role([Role.admin, Role.coordo, Role.resp])
delete_allowed = require_role([Role.admin, Role.coordo])
admin_only = require_role([Role.admin])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- UTILS (Chiffrement pour NSS et IBAN) ---
def get_fernet():
    if FERNET_KEY:
        return Fernet(FERNET_KEY.encode() if isinstance(FERNET_KEY, str) else FERNET_KEY)
    return None

def decrypt(value: str, f) -> str:
    if f and value:
        try:
            return f.decrypt(value.encode()).decode()
        except (InvalidToken, Exception):
            return value
    return value or ""

# --- PILOTAGE (Statistiques & Dashboard Admin) ---
@router.get("/stats", response_class=HTMLResponse)
async def get_stats(
    request: Request,
    current_user: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    # 1. Stats par Site (Total Brut validé)
    stmt_sites = (
        select(User.site, func.sum(LigneDeclaration.quantite * SousMission.tarif).label("total"))
        .join(Declaration, User.id == Declaration.user_id)
        .join(LigneDeclaration, Declaration.id == LigneDeclaration.declaration_id)
        .join(SousMission, LigneDeclaration.sous_mission_id == SousMission.id)
        .where(Declaration.statut == StatutDeclaration.validee)
        .group_by(User.site)
    )
    res_sites = await db.execute(stmt_sites)
    stats_sites = res_sites.all()

    # 2. Top 10 Intervenants
    stmt_users = (
        select(
            User, 
            func.sum(LigneDeclaration.quantite * SousMission.tarif).label("total_brut"),
            func.sum(LigneDeclaration.quantite).label("total_heures")
        )
        .join(Declaration, User.id == Declaration.user_id)
        .join(LigneDeclaration, Declaration.id == LigneDeclaration.declaration_id)
        .join(SousMission, LigneDeclaration.sous_mission_id == SousMission.id)
        .where(Declaration.statut == StatutDeclaration.validee)
        .group_by(User.id)
        .order_by(func.sum(LigneDeclaration.quantite * SousMission.tarif).desc())
        .limit(10)
    )
    res_users = await db.execute(stmt_users)
    stats_users = res_users.all()

    return templates.TemplateResponse(
        "admin/stats.html", 
        {
            "request": request, 
            "user": current_user, 
            "current_user": current_user, 
            "stats_sites": stats_sites,
            "stats_users": stats_users
        }
    )

# --- GESTION DES UTILISATEURS ---
@router.get("/users", response_class=HTMLResponse)
async def list_users(
    request: Request, 
    current_user: User = Depends(staff_required), 
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Role.admin:
        stmt = select(User)
    elif current_user.role == Role.coordo:
        stmt = select(User).where(User.site == current_user.site)
    else: # RESP
        stmt = select(User).where(
            User.site == current_user.site,
            User.programme == current_user.programme,
            User.matiere == current_user.matiere
        )
    
    result = await db.execute(stmt.order_by(User.id))
    users = result.scalars().all()

    MATIERES_PAR_PROG = {
        "PASS": ["UE_1", "UE_2", "UE_3", "UE_4", "UE_5", "UE_6", "UE_7", "UE_8", "MMOK", "PHARMA", "Min SVE", "Min SVH", "Min SPS", "Min EEEA", "Min PHY_MECA", "Min MATH", "Min CHIMIE", "Min STAPS", "Min DROIT", "ORAUX"],
        "LAS 1": ["Physiologie", "Anatomie", "Biologie Cell", "Biochimie", "Biostats", "Biophysique", "Chimie", "SSH", "Santé Publique", "ICM", "HBDV"],
        "LAS 2": ["Microbiologie", "Biocell / Immuno", "Biologie Dev", "Enzmo / Métabo", "Génétique", "Physiologie", "Statistiques", "MES GSE"]
    }

    return templates.TemplateResponse(
        "admin/users.html", 
        {
            "request": request, 
            "user": current_user,          
            "current_user": current_user,
            "users": users,
            "sites": [s.value for s in Site],
            "programmes": list(MATIERES_PAR_PROG.keys()),
            "matieres": MATIERES_PAR_PROG
        }
    )

@router.post("/users/create")
async def create_user(
    email: str = Form(...), 
    password: str = Form(...), 
    role: str = Form(...),
    site: Optional[str] = Form(None),
    programme: Optional[str] = Form(None),
    matiere: Optional[str] = Form(None),
    current_user: User = Depends(staff_required), 
    db: AsyncSession = Depends(get_db)
):
    final_role = Role(role)
    final_site = site
    final_prog = programme
    final_matiere = matiere

    if current_user.role == Role.resp:
        final_role = Role.tcp
        final_site = current_user.site.value
        final_prog = current_user.programme.value
        final_matiere = current_user.matiere
    elif current_user.role == Role.coordo:
        final_site = current_user.site.value

    new_user = User(
        email=email, 
        hashed_password=pwd_context.hash(password), 
        role=final_role,
        site=Site(final_site) if final_site else None,
        programme=Programme(final_prog) if final_prog else None,
        matiere=final_matiere
    )
    db.add(new_user)
    await db.commit()
    return RedirectResponse("/admin/users", status_code=303)

@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_form(
    request: Request, 
    user_id: int, 
    current_user: User = Depends(staff_required), 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    edit_user = result.scalar_one_or_none()
    if not edit_user: 
        return RedirectResponse("/admin/users", status_code=303)
    
    f = get_fernet()
    nss = decrypt(edit_user.nss_encrypted or "", f)
    iban = decrypt(edit_user.iban_encrypted or "", f)
    
    return templates.TemplateResponse("admin/user_form.html", {
        "request": request, 
        "current_user": current_user, 
        "edit_user": edit_user, 
        "roles": list(Role),
        "sites": list(Site),
        "programmes": list(Programme),
        "nss": nss, 
        "iban": iban
    })

@router.post("/users/{user_id}/edit")
async def edit_user_save(
    user_id: int,
    email: str = Form(...),
    role: str = Form(...),
    site: Optional[str] = Form(None),
    programme: Optional[str] = Form(None),
    matiere: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    current_user: User = Depends(staff_required),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u: raise HTTPException(status_code=404)

    u.email = email
    u.role = Role(role)
    u.site = Site(site) if site else None
    u.programme = Programme(programme) if programme else None
    u.matiere = matiere
    if password and len(password.strip()) >= 8:
        u.hashed_password = pwd_context.hash(password)

    await db.commit()
    return RedirectResponse("/admin/users?msg=updated", status_code=303)

@router.post("/users/{user_id}/delete")
async def delete_user(
    user_id: int, 
    current_user: User = Depends(delete_allowed), 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()

    if not target_user or target_user.id == current_user.id:
        return RedirectResponse("/admin/users", status_code=303)

    if current_user.role == Role.coordo:
        if target_user.site != current_user.site or target_user.role not in [Role.resp, Role.tcp]:
            raise HTTPException(status_code=403, detail="Hors périmètre")

    await db.delete(target_user)
    await db.commit()
    return RedirectResponse("/admin/users?msg=deleted", status_code=303)

# --- EXPORT CSV ---
@router.get("/export/csv")
async def export_declarations_csv(
    current_user: User = Depends(staff_required),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(LigneDeclaration, Declaration, User, SousMission, Mission)
        .join(Declaration, LigneDeclaration.declaration_id == Declaration.id)
        .join(User, Declaration.user_id == User.id)
        .join(SousMission, LigneDeclaration.sous_mission_id == SousMission.id)
        .join(Mission, SousMission.mission_id == Mission.id)
        .where(Declaration.statut == StatutDeclaration.validee)
        .order_by(Declaration.id.desc()) 
    )
    
    result = await db.execute(stmt)
    rows = result.all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["Date", "Collaborateur", "Rôle", "Site", "Programme", "Matière", "Mission", "Sous-Mission", "Quantité", "Tarif", "Total Brut"])

    for ligne_dec, dec, u, sm, m in rows:
        total_ligne = ligne_dec.quantite * sm.tarif
        date_display = dec.created_at.strftime("%d/%m/%Y") if dec.created_at else "N/C"
        writer.writerow([
            date_display,
            f"{u.prenom} {u.nom}" if (u.prenom or u.nom) else u.email,
            u.role.value.upper(),
            u.site.value if u.site else "N/C",
            u.programme.value if u.programme else "N/C",
            u.matiere or "N/C",
            m.nom, sm.nom,
            str(ligne_dec.quantite).replace('.', ','),
            str(sm.tarif).replace('.', ','),
            str(total_ligne).replace('.', ',')
        ])

    filename = f"export_avicenne_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# --- GÉNÉRATION DES FACTURES ---
@router.post("/generate-factures")
async def generate_factures(
    date_debut: str = Form(...),
    date_fin: str = Form(...),
    current_user: User = Depends(staff_required),
    db: AsyncSession = Depends(get_db)
):
    try:
        start_dt = datetime.strptime(date_debut, "%Y-%m-%d")
        end_dt = datetime.strptime(date_fin, "%Y-%m-%d")
    except ValueError:
        return RedirectResponse(url="/admin/stats?error=invalid_date", status_code=303)

    stmt = (
        select(User, func.sum(LigneDeclaration.quantite * SousMission.tarif).label("total_brut"))
        .join(Declaration, User.id == Declaration.user_id)
        .join(LigneDeclaration, Declaration.id == LigneDeclaration.declaration_id)
        .join(SousMission, LigneDeclaration.sous_mission_id == SousMission.id)
        .where(
            Declaration.statut == StatutDeclaration.validee,
            Declaration.created_at >= start_dt,
            Declaration.created_at <= end_dt
        )
        .group_by(User.id)
    )
    
    result = await db.execute(stmt)
    rows = result.all()

    if not rows:
        return RedirectResponse(url="/admin/stats?warning=no_data_period", status_code=303)

    f_fernet = get_fernet()
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for u, total_brut in rows:
            nss_decrypte = decrypt(u.nss_encrypted or "", f_fernet)
            context = {
                "user_fullname": f"{u.prenom} {u.nom}".upper() if (u.prenom or u.nom) else u.email,
                "user_nss": nss_decrypte or "Non renseigné",
                "user_address": u.adresse or "Adresse non renseignée",
                "user_cp_ville": f"{u.code_postal or ''} {u.ville or ''}",
                "date_facture": datetime.now().strftime("%d/%m/%Y"),
                "programme": u.programme.value if u.programme else "PASS",
                "matiere": u.matiere or "Supports pédagogiques",
                "total_du": f"{total_brut:.2f}".replace('.', ',')
            }
            html_content = templates.get_template("admin/invoice_pdf.html").render(context)
            pdf_data = HTML(string=html_content).write_pdf()
            filename = f"Facture_{u.nom}_{u.prenom}_{datetime.now().strftime('%Y%m%d')}.pdf"
            zip_file.writestr(filename, pdf_data)

    zip_buffer.seek(0)
    return StreamingResponse(zip_buffer, media_type="application/x-zip-compressed", headers={"Content-Disposition": "attachment; filename=Factures_Avicenne.zip"})

# --- SAISIE DE DÉCLARATION POUR UN TIERS ---
@router.get("/declarations/create", response_class=HTMLResponse)
async def admin_create_declaration_form(
    request: Request,
    user_id: int,
    current_user: User = Depends(staff_required),
    db: AsyncSession = Depends(get_db)
):
    # 1. Récupération de l'utilisateur cible
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        return RedirectResponse("/admin/users", status_code=303)

    # 2. Récupération des missions ET de leurs sous-missions (le secret est ici)
    stmt_missions = select(Mission).options(selectinload(Mission.sous_missions))
    res_missions = await db.execute(stmt_missions)
    missions = res_missions.scalars().all()

    # 3. Préparation des données
    today_str = datetime.now().strftime('%Y-%m-%d')
    mois_labels = {
        1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
        5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
        9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
    }

    return templates.TemplateResponse("admin/declaration_directe.html", {
        "request": request,
        "current_user": current_user,
        "target_user": target_user,
        "missions": missions,
        "today_date": today_str,
        "mois_labels": mois_labels,
        "default_mois": datetime.now().month,
        "default_annee": datetime.now().year
    })

@router.post("/declarations/save")
async def admin_save_declaration(
    user_id: int = Form(...),
    date_declaration: str = Form(...),
    mission_ids: List[int] = Form(...),
    quantites: List[float] = Form(...),
    current_user: User = Depends(staff_required),
    db: AsyncSession = Depends(get_db)
):
    new_dec = Declaration(user_id=user_id, statut=StatutDeclaration.en_attente, created_at=datetime.strptime(date_declaration, "%Y-%m-%d"))
    db.add(new_dec)
    await db.flush()
    for m_id, qty in zip(mission_ids, quantites):
        if qty > 0:
            db.add(LigneDeclaration(declaration_id=new_dec.id, sous_mission_id=m_id, quantite=qty))
    await db.commit()
    return RedirectResponse("/admin/users?msg=success", status_code=303)

# --- MISE À JOUR STATUT & COMMENTAIRE ---
@router.post("/declarations/{declaration_id}/update")
async def update_status(
    declaration_id: int,
    statut: str = Form(...),
    commentaire_admin: Optional[str] = Form(None),
    current_user: User = Depends(staff_required),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Declaration).where(Declaration.id == declaration_id)
    result = await db.execute(stmt)
    declaration = result.scalar_one_or_none()
    if declaration:
        declaration.statut = StatutDeclaration(statut)
        declaration.commentaire_admin = commentaire_admin
        await db.commit()
    return RedirectResponse(url="/admin/declarations?msg=updated", status_code=303)

@router.get("/referentiel/missions", response_class=HTMLResponse)
async def manage_referentiel(
    request: Request,
    current_user: User = Depends(staff_required),
    db: AsyncSession = Depends(get_db)
):
    # On utilise .titre au lieu de .nom et on trie par .ordre
    stmt = (
        select(Mission)
        .options(selectinload(Mission.sous_missions))
        .order_by(Mission.ordre, Mission.titre)
    )
    result = await db.execute(stmt)
    missions = result.scalars().all()

    return templates.TemplateResponse("admin/referentiel_missions.html", {
        "request": request,
        "current_user": current_user,
        "missions": missions
    })

# --- ACTION : AJOUTER MISSION PARENT ---
@router.post("/referentiel/mission/add")
async def admin_add_mission(
    nom: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(staff_required)
):
    new_mission = Mission(titre=nom, ordre=0, is_active=True)
    db.add(new_mission)
    await db.commit()
    # On redirige vers l'URL de la liste (définie dans le @router.get ci-dessus)
    return RedirectResponse(url="/referentiel/missions", status_code=303)

# --- ACTION : AJOUTER SOUS-MISSION ---
@router.post("/admin/referentiel/sub-mission/add")
async def admin_add_sub_mission(
    parent_id: int = Form(...),
    nom: str = Form(...),
    tarif: float = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(staff_required)
):
    new_sm = SousMission(mission_id=parent_id, titre=nom, tarif=tarif, is_active=True)
    db.add(new_sm)
    await db.commit()
    return RedirectResponse(url="/admin/referentiel/missions", status_code=303)