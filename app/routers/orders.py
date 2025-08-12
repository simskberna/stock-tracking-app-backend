from typing import List

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.notifications import notify_critical_stock
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.routers.auth import get_current_user
from app.schemas import OrderOut, OrderCreate

router = APIRouter()

@router.post("/create/", response_model=OrderOut)
async def create_order(
    order: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    order_repo = OrderRepository(db)
    product_repo = ProductRepository(db)

    try:
        new_order = await order_repo.create(order)
        product = await product_repo.get(order.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        await notify_critical_stock(current_user.email, product)

        return new_order
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/list/", response_model=List[OrderOut])
async def list_orders(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    repo = OrderRepository(db)
    return await repo.list(skip, limit)

