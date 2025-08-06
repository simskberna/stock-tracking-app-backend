from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Order
from app.schemas import OrderCreate
from app.tasks import update_stock


class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, order_create: OrderCreate):
        # Siparişi önce veritabanına ekle
        order = Order(
            product_id=order_create.product_id,
            quantity=order_create.quantity
        )
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)

        # Arka planda stok güncelle
        await update_stock(order_create.product_id, order_create.quantity)

        return order

    async def list(self, skip: int = 0, limit: int = 100):
        result = await self.db.execute(
            select(Order).offset(skip).limit(limit)
        )
        return result.scalars().all()
