import asyncio

from app.models import Product
from app.database import AsyncSessionLocal, get_db
from app.models import Product
from sqlalchemy.future import select

from app.repositories.product_repository import ProductRepository
from app.routers.ws import manager

CRITICAL_STOCK_LEVEL = 5

async def update_stock(product_id: int, quantity: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Product).filter(Product.id == product_id))
        product = result.scalars().first()
        if not product:
            return "Product not found"
        if product.stock < quantity:
            return "Insufficient stock"
        product.stock -= quantity
        await session.commit()

        return "Stock updated"

async def check_critical_stock_and_notify():
    async for db in get_db():

        product_repo = ProductRepository(db)
        products = await product_repo.list()
        for product in products:
            if product.stock <= product.critical_stock:
                message = f"Product '{product.name}' stock is critical: {product.stock}"
                for user_id in manager.active_connections.keys():
                    await manager.send_personal_message(message, user_id)

async def periodic_critical_stock_check():
    while True:
        await check_critical_stock_and_notify()
        await asyncio.sleep(300)  # 5 dakikada bir çalışır