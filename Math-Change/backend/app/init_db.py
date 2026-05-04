import asyncio
from app.db.session import engine
from app.db.base import Base
# Import models so they are registered with Base
from app.models.sql_models import User, Score

async def init_models():
    async with engine.begin() as conn:
        print("Dropping existing tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating tables with fresh schema...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully!")
    
    await engine.dispose()

if __name__ == "__main__":
    import sys
    # Ensure current directory is in python path if running directly
    # But usually run as: python -m app.init_db
    try:
        asyncio.run(init_models())
    except Exception as e:
        print(f"Error creating tables: {e}")
