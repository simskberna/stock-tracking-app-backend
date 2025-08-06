import asyncio
from app.database import engine, Base
from app.models import User, Product

async def init_db():
    async with engine.begin() as conn:
        # Tabloları oluşturur
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(init_db())
