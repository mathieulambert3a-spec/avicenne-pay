import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def fix():
    url = "postgresql+asyncpg://postgres:2%2BGMa5nf%2FrJ.S4z@db.rwhpqgyowtwivfirwdoc.supabase.co:5432/postgres"
    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE declarations ADD COLUMN IF NOT EXISTS commentaire_admin VARCHAR(500);"))
            print("✅ SUCCÈS : La colonne commentaire_admin est maintenant sur Supabase !")
    except Exception as e:
        print(f"❌ ERREUR : {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix())
