"""
Test PostgreSQL database connection.

Run this inside the Docker container:
    docker-compose exec backend python test_db_connection.py
"""

import asyncio

from sqlalchemy import text

from app.config import settings
from app.database import AsyncSessionLocal, engine


async def test_connection():
    """Test database connection and display info."""

    print("=" * 60)
    print("PostgreSQL Connection Test")
    print("=" * 60)

    # Display configuration
    print("\n📋 Configuration:")
    print(f"   Database URL: {settings.DATABASE_URL}")
    print(f"   Project: {settings.PROJECT_NAME}")

    # Test connection
    try:
        async with engine.connect() as conn:
            print("\n✅ Successfully connected to PostgreSQL!")

            # Get database version
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print("\n📦 PostgreSQL Version:")
            print(f"   {version.split(',')[0]}")

            # Get current database
            result = await conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print(f"\n🗄️  Current Database: {db_name}")

            # List all tables
            result = await conn.execute(
                text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            )
            tables = result.fetchall()

            print("\n📊 Tables in database:")
            if tables:
                for table in tables:
                    print(f"   - {table[0]}")
            else:
                print("   (No tables yet - run migrations)")

            # Test session
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1 as test"))
                test_val = result.scalar()
                print(f"\n🧪 Session Test: {test_val == 1 and '✅ PASS' or '❌ FAIL'}")

    except Exception as e:
        print("\n❌ Connection failed!")
        print(f"   Error: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        return False

    print("\n" + "=" * 60)
    print("✅ All tests passed! PostgreSQL is ready.")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("   1. Create migration: alembic revision --autogenerate -m 'Initial'")
    print("   2. Run migration: alembic upgrade head")
    print("   3. Test API: curl http://localhost:8000/api/v1/auth/register")
    print()

    return True


if __name__ == "__main__":
    asyncio.run(test_connection())
