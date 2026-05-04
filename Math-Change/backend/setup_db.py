"""
Setup DB Script - Math-Change
Crea las tablas en la base de datos PostgreSQL usando SQLAlchemy.

Uso:
  docker compose exec backend python setup_db.py
  
  O directamente:
  python setup_db.py
"""

import asyncio
from app.db.session import engine
from app.db.base import Base
from app.models.sql_models import User, Score


async def setup():
    print("=" * 50)
    print("Math-Change - Database Setup")
    print("=" * 50)

    try:
        async with engine.begin() as conn:
            print("Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Tables created successfully!")

        await engine.dispose()
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(setup())
