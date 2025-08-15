import asyncio
from datetime import datetime
from sqlalchemy.future import select

from app.emails import send_bulk_test_email
from app.models import Product
from app.database import AsyncSessionLocal, get_db
from app.repositories.product_repository import ProductRepository
from app.events.event_bus import event_bus, EventType, logger
from app.websocket_manager import manager


async def update_stock(product_id: int, quantity: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Product).filter(Product.id == product_id))
        product = result.scalars().first()
        if not product:
            return "Product not found"
        if product.stock < quantity:
            return "Insufficient stock"

        old_stock = product.stock
        product.stock -= quantity
        await session.commit()

        # Stok kritik seviyeye düştüyse event publish et
        if product.stock <= product.critical_stock and old_stock > product.critical_stock:
            await event_bus.publish(EventType.CRITICAL_STOCK, {
                "product_id": product.id,
                "product_name": product.name,
                "stock_level": product.stock,
                "critical_level": product.critical_stock,
                "timestamp": datetime.now().isoformat()
            })

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
        try:
            await check_critical_stock_and_notify()
        except Exception as e:
            logger.error(f"Error in periodic stock check: {e}")
        await asyncio.sleep(300)  # 5 dakikada bir çalışır


async def send_email_critical_product(user_email: str, product):
    """
    Güncellenen ürün kritik stok seviyesindeyse email bildirimi gönderir
    """
    try:
        if product.stock <= product.critical_stock:
            print(f"📧 Sending email notification for product {product.id} to {user_email}...")
            await send_bulk_test_email([product])
        else:
            print(f"✅ Product {product.id} stock is sufficient ({product.stock})")
    except Exception as e:
        print(f"❌ Error sending email for product {product.id}: {e}")