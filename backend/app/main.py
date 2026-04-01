from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, declarations, missions, paie, user 


app = FastAPI(
    title="Avicenne Pay API",
    # 🛡️ 2. LA NOUVELLE MÉTHODE PRO : On déclare le schéma de sécurité directement dans l'app
    swagger_ui_parameters={"persistAuthorization": True}, # Garde le token même si on actualise la page !
    openapi_components={
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    },
    # Applique la sécurité BearerAuth à TOUTES les routes dans la doc Swagger
    security=[{"BearerAuth": []}] 
)

# Liste des adresses autorisées à parler à notre backend
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://10.10.12.75:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Autorise toutes les méthodes (GET, POST, etc.)
    allow_headers=["*"], # Autorise tous les headers
)

# 🚦 3. AJOUT DU ROUTEUR USERS
app.include_router(user.router) # 👈 Ajouté ici !
app.include_router(missions.router) 
app.include_router(auth.router)
app.include_router(declarations.router)
app.include_router(paie.router)

@app.get("/", tags=["Root"]) # Un petit tag pour faire joli dans Swagger
def read_root():
    return {"message": "Bienvenue sur l'API d'Avicenne Pay !"}
