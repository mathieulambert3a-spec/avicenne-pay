# backend/core/security.py

import os
from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, Role
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt

# 1. On importe de quoi lire le fichier .env
from dotenv import load_dotenv

# 2. On force le chargement du fichier .env
load_dotenv()

# On force la clé directement ici en dur pour court-circuiter le bug de cache Windows
CLÉ_FORCÉE = b"8QI1FzU5ueVovWz7pWrbplAkB0YLvAkIHwYezaSVvS4="
fernet = Fernet(CLÉ_FORCÉE)

def encrypt_data(plain_text: str) -> str:
    """Chiffre une chaîne de caractères en clair (ex: IBAN)."""
    if not plain_text:
        return None
    # Fernet travaille avec des bytes, on doit encoder en utf-8
    encrypted_bytes = fernet.encrypt(plain_text.encode('utf-8'))
    return encrypted_bytes.decode('utf-8')

def decrypt_data(encrypted_text: str) -> str:
    """Déchiffre une chaîne de caractères cryptée venant de la base de données."""
    if not encrypted_text:
        return None
    try:
        decrypted_bytes = fernet.decrypt(encrypted_text.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception:
        # Si la clé a changé entre temps ou que la donnée est corrompue
        return "[Erreur de déchiffrement]"

# On configure passlib pour utiliser l'algorithme bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ⚠️ EN PRODUCTION : Mettre une vraie clé secrète complexe dans le fichier .env !
SECRET_KEY = "AVICENNE_SUPER_SECRET_KEY_2026" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Fonction 1 : Hacher un mot de passe
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Fonction 2 : Vérifier un mot de passe (pendant la connexion)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Fonction 3 : Créer le jeton de connexion (JWT)
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    
    # 💡 Utilisation de datetime.now(timezone.utc) moderne
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    
    # Encodage du token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# On indique à FastAPI où aller chercher le Token (dans le header Authorization)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Vérifie la validité du token JWT fourni et retourne l'utilisateur s'il existe.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # On décode le token avec notre clé secrète
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
    except jwt.PyJWTError:
        # S'affiche si le token a été modifié ou s'il a expiré
        raise credentials_exception
        
    # On va chercher l'utilisateur en base de données
    user = db.query(User).filter(User.id == int(user_id)).first()
    
    if user is None:
        raise credentials_exception
        
    # Si le compte a été désactivé entre temps
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce compte utilisateur est désactivé."
        )
    return user

def check_is_admin(current_user: User = Depends(get_current_user)) -> User:
    """Vérifie si l'utilisateur est un administrateur."""
    if current_user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Réservé aux administrateurs."
        )
    return current_user

def check_is_at_least_coordo(current_user: User = Depends(get_current_user)) -> User:
    """Vérifie si l'utilisateur est au moins Coordinateur ou Admin."""
    if current_user.role not in [Role.admin, Role.coordo]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux coordinateurs et administrateurs."
        )
    return current_user

def check_peut_creer_user(current_user: User = Depends(get_current_user)) -> User:
    """Bloque les exécutants qui n'ont aucun droit de création."""
    if current_user.role in [Role.top, Role.com, Role.tcp]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Votre rôle ne vous autorise pas à créer des utilisateurs."
        )
    return current_user

def check_peut_valider_declaration(current_user: User = Depends(get_current_user)) -> User:
    """Vérifie si l'utilisateur a le droit de valider/rejeter (Admin et Coordo uniquement)."""
    if current_user.role not in [Role.admin, Role.coordo]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les Administrateurs et les Coordinateurs peuvent valider ou rejeter des déclarations."
        )
    return current_user