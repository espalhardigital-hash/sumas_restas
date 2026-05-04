"""
Check Schema Script - Math-Change
Verifica que las tablas existen y muestra su estructura.

Uso:
  docker compose exec backend python check_schema.py
"""

import asyncio
from sqlalchemy import text
from app.db.session import engine


async def check_schema():
    print("=" * 50)
    print("Math-Change - Schema Check")
    print("=" * 50)

    try:
        async with engine.connect() as conn:
            # Check tables exist
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = result.fetchall()

            if not tables:
                print("❌ No tables found! Run setup_db.py first.")
                return

            print(f"\n✅ Found {len(tables)} table(s):")
            for table in tables:
                table_name = table[0]
                print(f"\n--- Table: {table_name} ---")

                # Get columns
                cols = await conn.execute(text(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position;
                """))

                for col in cols:
                    nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                    default = f" DEFAULT {col[3]}" if col[3] else ""
                    print(f"  {col[0]:20s} {col[1]:20s} {nullable}{default}")

                # Count rows
                count = await conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = count.scalar()
                print(f"  → {row_count} rows")

        await engine.dispose()
        print("\n✅ Schema check complete!")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(check_schema())
