from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, engine, Base
from app.config import SECRET_KEY
from app.dependencies import get_current_user, get_current_user_optional
from app.models.user import User, Role
from app.routers import auth, profile, missions, declarations, admin

app = FastAPI(title="Avicenne Pay")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(missions.router)
app.include_router(declarations.router)
app.include_router(admin.router)


@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse("/dashboard", status_code=302)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "user": current_user}
    )


@app.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.role == Role.admin))
    admin_exists = result.scalar_one_or_none()
    if admin_exists:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("setup.html", {"request": request})


@app.post("/setup")
async def setup_create_admin(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.role == Role.admin))
    admin_exists = result.scalar_one_or_none()
    if admin_exists:
        return RedirectResponse("/login", status_code=302)

    form_data = await request.form()
    email = str(form_data.get("email", ""))
    password = str(form_data.get("password", ""))

    if not email or not password:
        return templates.TemplateResponse(
            "setup.html", {"request": request, "error": "Email et mot de passe requis"}
        )

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_context.hash(password)
    admin_user = User(email=email, hashed_password=hashed, role=Role.admin)
    db.add(admin_user)
    await db.commit()
    return RedirectResponse("/login?setup=ok", status_code=302)
