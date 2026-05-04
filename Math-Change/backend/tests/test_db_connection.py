"""
Test Database Connection - Math-Change
Verifica la conexión a PostgreSQL usando SQLAlchemy async.

Uso:
  docker compose exec backend python tests/test_db_connection.py
  python -m tests.test_db_connection
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()
load_dotenv(dotenv_path='../.env')


async def test_connection():
    print("--- Testing Database Connection ---")

    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ ERROR: DATABASE_URL not set in .env")
        sys.exit(1)

    print(f"\nConnecting to: {DATABASE_URL[:40]}...")

    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"✅ SUCCESS! DB Version: {version}")

            tables_result = await conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in tables_result]
            print(f"📋 Tables found: {tables}")

        await engine.dispose()
        return True

    except Exception as e:
        print(f"❌ Connection FAILED: {e}")
        return False


if __name__ == "__main__":
    if asyncio.run(test_connection()):
        print("\n--- ✅ TEST PASSED: Database connection verified ---")
        sys.exit(0)
    else:
        print("\n--- ❌ TEST FAILED: Could not connect ---")
        sys.exit(1)
