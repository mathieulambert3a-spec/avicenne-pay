from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.database import get_db
from app.dependencies import require_role
from app.models.user import Role
from app.models.mission import Mission
from app.models.sub_mission import SousMission

router = APIRouter(prefix="/missions")
templates = Jinja2Templates(directory="app/templates")
admin_required = require_role(Role.admin)


@router.get("", response_class=HTMLResponse)
async def list_missions(
    request: Request,
    current_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Mission).order_by(Mission.ordre))
    missions = result.scalars().all()
    # Eagerly load sous_missions
    for mission in missions:
        await db.refresh(mission, ["sous_missions"])
    return templates.TemplateResponse(
        "missions/list.html", {"request": request, "user": current_user, "missions": missions}
    )


@router.get("/new", response_class=HTMLResponse)
async def new_mission_form(request: Request, current_user=Depends(admin_required)):
    return templates.TemplateResponse(
        "missions/form.html", {"request": request, "user": current_user, "mission": None}
    )


@router.post("/new")
async def create_mission(
    request: Request,
    titre: str = Form(...),
    ordre: int = Form(0),
    is_active: str = Form("on"),
    current_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    mission = Mission(titre=titre, ordre=ordre, is_active=(is_active == "on"))
    db.add(mission)
    await db.commit()
    return RedirectResponse("/missions", status_code=302)


@router.get("/{mission_id}/edit", response_class=HTMLResponse)
async def edit_mission_form(
    request: Request,
    mission_id: int,
    current_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()
    if not mission:
        return RedirectResponse("/missions", status_code=302)
    return templates.TemplateResponse(
        "missions/form.html", {"request": request, "user": current_user, "mission": mission}
    )


@router.post("/{mission_id}/edit")
async def update_mission(
    mission_id: int,
    titre: str = Form(...),
    ordre: int = Form(0),
    is_active: str = Form(""),
    current_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()
    if mission:
        mission.titre = titre
        mission.ordre = ordre
        mission.is_active = (is_active == "on")
        await db.commit()
    return RedirectResponse("/missions", status_code=302)


@router.post("/{mission_id}/delete")
async def delete_mission(
    mission_id: int,
    current_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()
    if mission:
        await db.delete(mission)
        await db.commit()
    return RedirectResponse("/missions", status_code=302)


# --- Sous-missions ---

@router.get("/{mission_id}/sous-missions/new", response_class=HTMLResponse)
async def new_sub_mission_form(
    request: Request,
    mission_id: int,
    current_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()
    return templates.TemplateResponse(
        "missions/sub_mission_form.html",
        {"request": request, "user": current_user, "mission": mission, "sous_mission": None},
    )


@router.post("/{mission_id}/sous-missions/new")
async def create_sub_mission(
    mission_id: int,
    titre: str = Form(...),
    tarif: float = Form(...),
    unite: str = Form(""),
    ordre: int = Form(0),
    is_active: str = Form("on"),
    current_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    sm = SousMission(
        mission_id=mission_id,
        titre=titre,
        tarif=tarif,
        unite=unite or None,
        ordre=ordre,
        is_active=(is_active == "on"),
    )
    db.add(sm)
    await db.commit()
    return RedirectResponse("/missions", status_code=302)


@router.get("/{mission_id}/sous-missions/{sm_id}/edit", response_class=HTMLResponse)
async def edit_sub_mission_form(
    request: Request,
    mission_id: int,
    sm_id: int,
    current_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()
    result2 = await db.execute(select(SousMission).where(SousMission.id == sm_id))
    sous_mission = result2.scalar_one_or_none()
    return templates.TemplateResponse(
        "missions/sub_mission_form.html",
        {"request": request, "user": current_user, "mission": mission, "sous_mission": sous_mission},
    )


@router.post("/{mission_id}/sous-missions/{sm_id}/edit")
async def update_sub_mission(
    mission_id: int,
    sm_id: int,
    titre: str = Form(...),
    tarif: float = Form(...),
    unite: str = Form(""),
    ordre: int = Form(0),
    is_active: str = Form(""),
    current_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SousMission).where(SousMission.id == sm_id))
    sm = result.scalar_one_or_none()
    if sm:
        sm.titre = titre
        sm.tarif = tarif
        sm.unite = unite or None
        sm.ordre = ordre
        sm.is_active = (is_active == "on")
        await db.commit()
    return RedirectResponse("/missions", status_code=302)


@router.post("/{mission_id}/sous-missions/{sm_id}/delete")
async def delete_sub_mission(
    mission_id: int,
    sm_id: int,
    current_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SousMission).where(SousMission.id == sm_id))
    sm = result.scalar_one_or_none()
    if sm:
        await db.delete(sm)
        await db.commit()
    return RedirectResponse("/missions", status_code=302)
