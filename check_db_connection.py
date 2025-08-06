import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.exc import DBAPIError

# Test database URL from conftest.py
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/hicrm_test"

async def check_connection():
    print(f"Attempting to connect to: {TEST_DATABASE_URL}")
    try:
        # Create test database engine
        test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        
        # Try to connect
        async with test_engine.begin() as conn:
            print("Connection successful. Running a simple ping...")
            # A simple query to test the connection
            await conn.execute("SELECT 1")
            print("Ping successful.")
            
        await test_engine.dispose()
        print("Engine disposed.")
        return True

    except Exception as e:
        print(f"Database connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(check_connection())
    if success:
        print("Database check passed.")
    else:
        print("Database check failed.")
