import asyncio
import sys
import os
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
sys.path.append(os.getcwd())

from app.database import AsyncSessionLocal
from app.models.user import User

async def create_user():
    async with AsyncSessionLocal() as session:
        # On crée un utilisateur avec le rôle 'admin' (minuscules obligatoire)
        new_user = User(
            email="superadmin@avicenne.fr",
            hashed_password=pwd_context.hash("admin123"),
            role="admin",
            nom="ADMIN",
            prenom="Principal",
            profil_complete=True
        )
        session.add(new_user)
        await session.commit()
        print("✅ SUPER ADMIN créé avec succès !")
        print("📧 Email : superadmin@avicenne.fr")
        print("🔑 Pass : admin123")

if __name__ == "__main__":
    asyncio.run(create_user())
