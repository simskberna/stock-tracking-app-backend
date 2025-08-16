from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from app.database import AsyncSessionLocal
from app.services.forecast_service import forecast_product_demand, is_stock_critical
from app.websocket_manager import manager


# from app.ws import notify   # mevcut websocket yayın fonksiyonun varsa

async def _retrain_and_alert():
    async with AsyncSessionLocal() as db:  # projendeki factory ismi farklıysa uyarlayın
        # Örnek: aktif ürünleri çek
        rows = (await db.execute(text("SELECT id FROM products WHERE is_active = true"))).all()
        product_ids = [r[0] for r in rows]
        for pid in product_ids:
            result = await forecast_product_demand(db, pid, horizon_days=30, lead_time_days=7)
            # Stok-out 7 gün içinde mi?
            so = result.get("stockout_date")
            # notify(...)  # burada kendi yayın mekanizmana göre uyarı gönder

def setup_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(_retrain_and_alert, "cron", hour=3, minute=0)
    scheduler.start()

async def periodic_forecast_check():
    async with AsyncSessionLocal() as db:  # async DB session
        # Tüm aktif ürünleri çek
        from app.models import Product
        result = await db.execute(select(Product).where(Product.is_active == True))
        products = result.scalars().all()

        for product in products:
            forecast = await forecast_product_demand(db, product.id, horizon_days=30, lead_time_days=7)
            if is_stock_critical(forecast, threshold_days=7):
                # WebSocket üzerinden yayınla
                message = {
                    "type": "critical_stock_forecast",
                    "product_id": product.id,
                    "product_name": product.name,
                    "stockout_date": forecast["stockout_date"],
                    "recommended_order_qty": forecast["recommended_order_qty"]
                }
                # manager.connected_users: dict[user_email, websocket]
                for user_email, websocket in manager.active_connections.items():
                    await manager.send_personal_message(user_email, message)