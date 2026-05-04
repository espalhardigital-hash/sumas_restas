import asyncio
from app.db.session import engine
from app.models.sql_models import User
from sqlalchemy import update

async def update_admin():
    async with engine.begin() as conn:
        result = await conn.execute(
            update(User)
            .where(User.email == 'amilcar.najul@gmail.com')
            .values(role='ADMIN')
        )
        print(f"User amilcar.najul@gmail.com updated to ADMIN role")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(update_admin())
