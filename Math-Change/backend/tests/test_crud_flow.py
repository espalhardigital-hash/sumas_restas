"""
Test CRUD Flow - Math-Change
Prueba operaciones CRUD contra PostgreSQL usando SQLAlchemy async.

Uso:
  docker compose exec backend python tests/test_crud_flow.py
  python -m tests.test_crud_flow
"""
import asyncio
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine, AsyncSessionLocal
from app.db.base import Base
from app.models.sql_models import User, Score
from app.auth import get_password_hash
from sqlalchemy import select


async def run_test():
    print("--- 🚀 Starting CRUD Test (SQLAlchemy + PostgreSQL) ---")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    run_id = str(uuid.uuid4())[:8]
    test_email = f"test_crud_{run_id}@example.com"
    test_id = str(uuid.uuid4())

    async with AsyncSessionLocal() as session:
        # STEP 1: CREATE
        print(f"\n[1/4] Attempting INSERT user {test_email}...")
        try:
            new_user = User(
                id=test_id,
                username=f"TestBot_{run_id}",
                email=test_email,
                password_hash=get_password_hash("test_password"),
                role="TESTER",
                status="ACTIVE",
                unlocked_level=0,
                settings={"test_run": True}
            )
            session.add(new_user)
            await session.commit()
            print("   ✅ INSERT Successful")
        except Exception as e:
            print(f"   ❌ INSERT Exception: {e}")
            await engine.dispose()
            sys.exit(1)

        # STEP 2: READ
        print(f"\n[2/4] Attempting SELECT by email...")
        try:
            result = await session.execute(select(User).where(User.email == test_email))
            fetched_user = result.scalar_one_or_none()
            if fetched_user and fetched_user.username == f"TestBot_{run_id}":
                print("   ✅ READ Successful")
            else:
                print("   ❌ READ Failed")
                sys.exit(1)
        except Exception as e:
            print(f"   ❌ READ Exception: {e}")
            sys.exit(1)

        # STEP 3: UPDATE
        print(f"\n[3/4] Attempting UPDATE (unlocked_level 0 -> 5)...")
        try:
            fetched_user.unlocked_level = 5
            await session.commit()
            await session.refresh(fetched_user)
            if fetched_user.unlocked_level == 5:
                print("   ✅ UPDATE Successful")
            else:
                print("   ❌ UPDATE Failed")
                sys.exit(1)
        except Exception as e:
            print(f"   ❌ UPDATE Exception: {e}")
            sys.exit(1)

        # STEP 4: DELETE
        print(f"\n[4/4] Attempting DELETE cleanup...")
        try:
            await session.delete(fetched_user)
            await session.commit()
            check = await session.execute(select(User).where(User.id == test_id))
            if not check.scalar_one_or_none():
                print("   ✅ DELETE Successful")
            else:
                print("   ⚠️ DELETE Warning: User still exists")
        except Exception as e:
            print(f"   ❌ DELETE Exception: {e}")

    await engine.dispose()
    print("\n--- ✨ TEST COMPLETED SUCCESSFULLY ✨ ---")


if __name__ == "__main__":
    asyncio.run(run_test())
