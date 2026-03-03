from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
import os
from sqlalchemy import event
from sqlalchemy.engine import Engine

# On essaie de récupérer l'URL de la config, sinon on utilise SQLite par défaut
try:
    from app.config import DATABASE_URL
    # Si DATABASE_URL commence par postgresql, on s'assure qu'il utilise le driver asyncpg
    if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
except ImportError:
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# FORCE SQLite pour le développement local si le réseau est inaccessible
# Tu pourras remettre DATABASE_URL plus tard pour la production
FINAL_URL = "sqlite+aiosqlite:///./test.db" 

engine = create_async_engine(FINAL_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()