from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Order, Product
from app.schemas import OrderCreate
from app.tasks import update_stock


class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, order_create: OrderCreate):
        product_result = await self.db.execute(
            select(Product).where(Product.id == order_create.product_id)
        )
        product = product_result.scalar_one_or_none()

        if not product:
            raise ValueError("Product not found")

        total = product.price * order_create.quantity

        order = Order(
            product_id=order_create.product_id,
            quantity=order_create.quantity,
            total=total
        )
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)

        await update_stock(order_create.product_id, order_create.quantity)

        return order

    async def list(self, skip: int = 0, limit: int = 100):
        result = await self.db.execute(
            select(Order).offset(skip).limit(limit)
        )
        return result.scalars().all()
