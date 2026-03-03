from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

# Imports internes
from app.database import get_db, engine, Base
from app.config import SECRET_KEY
from app.dependencies import get_current_user, get_current_user_optional
from app.models.user import User, Role
from app.models.declaration import Declaration  # <-- AJOUTÉ : Nécessaire pour le dashboard
from app.routers import auth, profile, missions, declarations, admin, users
from app.models.mission import Mission
from app.models.sub_mission import SousMission

app = FastAPI(title="Avicenne Pay")

# Configuration des fichiers statiques et templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
async def startup_event():
    print("🚀 Vérification de la base de données...")
    async with engine.begin() as conn:
        # Cette ligne crée toutes les tables définies dans tes modèles 
        # (Mission, SousMission, etc.) si elles n'existent pas encore.
        await conn.run_sync(Base.metadata.create_all)
        
        # Ton script pour la colonne commentaire_admin
        try:
            await conn.execute(text("ALTER TABLE declarations ADD COLUMN commentaire_admin VARCHAR(500);"))
            print("✅ Colonne 'commentaire_admin' ajoutée.")
        except Exception:
            print("ℹ️ La colonne 'commentaire_admin' existe déjà.")

# Inclusion des routeurs
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(missions.router)
app.include_router(declarations.router)
app.include_router(admin.router)
app.include_router(users.router)

# --- ROUTES PRINCIPALES ---

@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse("/dashboard", status_code=302)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Affiche le tableau de bord avec les notifications de l'administration.
    """
    # Récupération des 5 dernières déclarations pour afficher les statuts et commentaires
    stmt = (
        select(Declaration)
        .where(Declaration.user_id == current_user.id)
        .order_by(Declaration.updated_at.desc())
        .limit(5)
    )
    result = await db.execute(stmt)
    user_declarations = result.scalars().all()

    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request, 
            "user": current_user, 
            "declarations": user_declarations
        }
    )

# --- CONFIGURATION INITIALE (SETUP) ---

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