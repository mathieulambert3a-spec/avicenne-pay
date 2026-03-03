import asyncio
from app.database import engine, AsyncSessionLocal, Base
from app.models.user import User, Role
from passlib.context import CryptContext
from sqlalchemy import select

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def init_db():
    # 1. Création des tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 2. Création de l'utilisateur admin
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "admin@test.com"))
        if not result.scalar_one_or_none():
            new_user = User(
                email="admin@test.com",
                hashed_password=pwd_context.hash("admin123"),
                nom="Lambert",
                prenom="Mathieu",
                role=Role.ADMIN if hasattr(Role, 'ADMIN') else "admin"
            )
            session.add(new_user)
            await session.commit()
            print("✅ Succès ! Tables créées et utilisateur admin prêt.")
        else:
            print("ℹ️ L'utilisateur admin@test.com existe déjà.")

if __name__ == "__main__":
    asyncio.run(init_db())