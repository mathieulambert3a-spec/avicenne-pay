from typing import Optional, Union, List
from fastapi import Request, HTTPException, Depends, status
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import SECRET_KEY
from app.database import get_db
from app.models.user import User, Role

serializer = URLSafeTimedSerializer(SECRET_KEY)

def get_session_user_id(request: Request) -> Optional[int]:
    token = request.cookies.get("session")
    if not token:
        return None
    try:
        data = serializer.loads(token, max_age=86400 * 7)
        return data.get("user_id")
    except (BadSignature, SignatureExpired):
        return None

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = get_session_user_id(request)
    if not user_id:
        raise HTTPException(
            status_code=302,
            detail="Non authentifié",
            headers={"Location": "/login"}
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=302,
            detail="Utilisateur introuvable",
            headers={"Location": "/login"}
        )
    return user

async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    user_id = get_session_user_id(request)
    if not user_id:
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

def require_role(*roles_input):
    """
    Version ultra-flexible :
    Accepte : require_role(Role.admin)
    Accepte : require_role(Role.admin, Role.coordo)
    Accepte : require_role([Role.admin, Role.coordo])
    """
    allowed_roles = []
    for item in roles_input:
        if isinstance(item, list):
            allowed_roles.extend(item)
        else:
            allowed_roles.append(item)

    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403, 
                detail=f"Accès refusé. Rôles autorisés : {[r.value for r in allowed_roles]}"
            )
        return current_user
    return checker
    
async def validate_user_creation_rights(
    user_to_create_role: Role, 
    current_user: User = Depends(get_current_user)
) -> bool:
    if current_user.role == Role.tcp:
        raise HTTPException(status_code=403, detail="Un TCP ne peut pas créer d'utilisateurs.")

    if current_user.role == Role.resp:
        if user_to_create_role != Role.tcp:
            raise HTTPException(status_code=403, detail="Un Responsable ne peut créer que des TCP.")
    
    if current_user.role == Role.coordo:
        if user_to_create_role == Role.admin:
            raise HTTPException(status_code=403, detail="Un Coordinateur ne peut pas créer d'Admin.")

    if current_user.role != Role.admin and not current_user.site:
        raise HTTPException(
            status_code=400, 
            detail="Vous devez renseigner votre site dans votre profil avant de créer des utilisateurs."
        )

    return True