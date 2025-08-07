from fastapi import Depends, APIRouter
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Product, Order

router = APIRouter()


@router.get("/")
async def get_overall_metrics(db: AsyncSession = Depends(get_db)):
    critical_stock_count = await db.scalar(
        select(func.count()).select_from(Product).where(Product.stock <= Product.critical_stock)
    )
    total_products_count = await db.scalar(
        select(func.count()).select_from(Product)
    )
    total_orders_quantity = await db.scalar(
        select(func.coalesce(func.sum(Order.quantity), 0))
    )
    total_orders_revenue = await db.scalar(
        select(func.coalesce(func.sum(Order.total), 0))
    )

    return {
        "critical_stock_count": critical_stock_count,
        "total_products_count": total_products_count,
        "total_orders": total_orders_quantity,
        "total_orders_revenue":total_orders_revenue
    }