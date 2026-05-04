"""
Seed Data Script - Math-Change
Genera usuarios y puntuaciones de prueba usando SQLAlchemy (PostgreSQL directo).

Uso:
  docker compose exec backend python seed_data.py
"""

import asyncio
import uuid
import random
from datetime import datetime, timedelta
from app.db.session import engine, AsyncSessionLocal
from app.db.base import Base
from app.models.sql_models import User, Score
from app.auth import get_password_hash

CATEGORIES = ["addition", "subtraction", "multiplication", "division", "mixed_add_sub", "all_mixed"]
DIFFICULTIES = ["easy", "easy_medium", "medium", "medium_hard", "hard"]

USERS_DATA = [
    {
        "username": "prueba1",
        "email": "prueba1@test.com",
        "password": "123456",
        "level": 5,
        "skill": "mixed",
        "games_count": 20
    },
    {
        "username": "prueba2",
        "email": "prueba2@test.com",
        "password": "123456",
        "level": 2,
        "skill": "beginner",
        "games_count": 10
    },
    {
        "username": "prueba3",
        "email": "prueba3@test.com",
        "password": "123456",
        "level": 10,
        "skill": "expert",
        "games_count": 30
    }
]


async def create_users():
    print("Creating users...")
    created_users = []

    async with AsyncSessionLocal() as session:
        for u in USERS_DATA:
            from sqlalchemy import select
            result = await session.execute(select(User).where(User.email == u["email"]))
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  User {u['username']} already exists. Skipping.")
                created_users.append({**u, "id": existing.id})
                continue

            user_id = str(uuid.uuid4())
            new_user = User(
                id=user_id,
                username=u["username"],
                email=u["email"],
                password_hash=get_password_hash(u["password"]),
                role="USER",
                status="ACTIVE",
                unlocked_level=u["level"],
                settings={}
            )
            session.add(new_user)
            print(f"  Created user: {u['username']}")
            created_users.append({**u, "id": user_id})

        await session.commit()

    return created_users


def generate_score(user, date_offset_days):
    category = random.choice(CATEGORIES)
    difficulty = random.choice(DIFFICULTIES)

    if user["skill"] == "expert":
        correct = random.randint(18, 20)
        error = random.randint(0, 2)
        base_score = correct * 100
        avg_time = random.uniform(1.5, 4.0)
    elif user["skill"] == "beginner":
        correct = random.randint(5, 12)
        error = random.randint(5, 10)
        base_score = correct * 50
        avg_time = random.uniform(8.0, 15.0)
    else:  # mixed
        if category == "addition":
            correct = random.randint(15, 20)
            error = random.randint(0, 5)
            avg_time = random.uniform(3.0, 6.0)
        else:
            correct = random.randint(8, 15)
            error = random.randint(3, 8)
            avg_time = random.uniform(5.0, 10.0)
        base_score = correct * 80

    total_q = correct + error
    if total_q == 0:
        total_q = 1
        correct = 1

    date = datetime.now() - timedelta(days=date_offset_days)

    return Score(
        user_id=user["id"],
        score=base_score,
        correct_count=correct,
        error_count=error,
        avg_time=round(avg_time, 2),
        category=category,
        difficulty=difficulty,
        date=date
    )


async def seed_scores(users):
    print("Seeding scores...")
    count = 0

    async with AsyncSessionLocal() as session:
        for user in users:
            print(f"  Generating {user['games_count']} games for {user['username']}...")
            for i in range(user['games_count']):
                days_ago = random.randint(0, 30)
                score = generate_score(user, days_ago)
                session.add(score)
                count += 1

        await session.commit()

    print(f"  Successfully inserted {count} score records.")


async def main():
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    users = await create_users()
    await seed_scores(users)
    await engine.dispose()
    print("\n✅ Seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
