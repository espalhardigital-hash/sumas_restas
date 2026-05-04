import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set in .env")
    exit(1)

async def check_connection():
    print(f"Connecting to: {DATABASE_URL}")
    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        async with engine.connect() as conn:
            files = await conn.execute(text("SELECT 1"))
            print("SUCCESS: Database connection verified!")
            print(f"Result: {files.scalar()}")
        await engine.dispose()
    except Exception as e:
        print(f"FAILURE: Could not connect to database.")
        print(e)

if __name__ == "__main__":
    asyncio.run(check_connection())
