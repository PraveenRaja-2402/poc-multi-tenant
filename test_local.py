import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:praveenraja2402@localhost:5433/taskflow"

async def main():
    engine = create_async_engine(DATABASE_URL, pool_size=5, max_overflow=10, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        await session.execute(text("SET LOCAL search_path TO tenant_poc_a, public;"))
        result = await session.execute(text("SELECT * FROM tasks;"))
        print("Tenant A tasks:", result.fetchall())
        await session.commit()
    
    # Try different tenant
    async with AsyncSessionLocal() as session:
        await session.execute(text("SET LOCAL search_path TO tenant_poc_b, public;"))
        result = await session.execute(text("SELECT * FROM tasks;"))
        print("Tenant B tasks:", result.fetchall())
        await session.commit()

        # check what is search path now
        result = await session.execute(text("SHOW search_path;"))
        print("Search path after commit:", result.fetchall())

if __name__ == "__main__":
    asyncio.run(main())
