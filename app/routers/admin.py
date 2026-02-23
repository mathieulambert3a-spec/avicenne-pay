from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken

from app.database import get_db
from app.dependencies import require_role
from app.config import FERNET_KEY
from app.models.user import User, Role, Filiere, Annee, Site, Programme

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")
admin_required = require_role(Role.admin)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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


@router.get("/users", response_class=HTMLResponse)
async def list_users(
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    return templates.TemplateResponse(
        "admin/users.html", {"request": request, "user": current_user, "users": users}
    )


@router.get("/users/new", response_class=HTMLResponse)
async def new_user_form(request: Request, current_user: User = Depends(admin_required)):
    return templates.TemplateResponse(
        "admin/user_form.html",
        {"request": request, "user": current_user, "edit_user": None, "roles": list(Role)},
    )


@router.post("/users/new")
async def create_user(
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    hashed = pwd_context.hash(password)
    new_user = User(email=email, hashed_password=hashed, role=Role(role))
    db.add(new_user)
    await db.commit()
    return RedirectResponse("/admin/users", status_code=302)


@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_form(
    request: Request,
    user_id: int,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    edit_user = result.scalar_one_or_none()
    if not edit_user:
        return RedirectResponse("/admin/users", status_code=302)
    f = get_fernet()
    nss = decrypt(edit_user.nss_encrypted or "", f)
    iban = decrypt(edit_user.iban_encrypted or "", f)
    return templates.TemplateResponse(
        "admin/user_form.html",
        {
            "request": request,
            "user": current_user,
            "edit_user": edit_user,
            "roles": list(Role),
            "nss": nss,
            "iban": iban,
        },
    )


@router.post("/users/{user_id}/edit")
async def update_user(
    user_id: int,
    email: str = Form(...),
    role: str = Form(...),
    password: str = Form(""),
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    edit_user = result.scalar_one_or_none()
    if edit_user:
        edit_user.email = email
        edit_user.role = Role(role)
        if password:
            edit_user.hashed_password = pwd_context.hash(password)
        await db.commit()
    return RedirectResponse("/admin/users", status_code=302)


@router.post("/users/{user_id}/delete")
async def delete_user(
    user_id: int,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    edit_user = result.scalar_one_or_none()
    if edit_user and edit_user.id != current_user.id:
        await db.delete(edit_user)
        await db.commit()
    return RedirectResponse("/admin/users", status_code=302)
