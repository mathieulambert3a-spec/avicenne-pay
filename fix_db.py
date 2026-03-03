import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def fix():
    # Remplacement du nom de domaine par l'IP directe
    url = "postgresql+asyncpg://postgres:2+GMa5nf/rJ.S4z@15.237.168.17:5432/postgres"
    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            # On force la création de la colonne
            await conn.execute(text("ALTER TABLE declarations ADD COLUMN IF NOT EXISTS commentaire_admin VARCHAR(500);"))
            print("\n✅ ENFIN ! La colonne est ajoutée sur Supabase.")
    except Exception as e:
        print(f"\n❌ TOUJOURS UNE ERREUR : {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix())