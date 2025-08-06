from typing import List

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.order_repository import OrderRepository
from app.schemas import OrderOut, OrderCreate

router = APIRouter()

@router.post("/create", response_model=OrderOut)
async def create_order(order: OrderCreate, db: AsyncSession = Depends(get_db)):
    repo = OrderRepository(db)
    try:
        new_order = await repo.create(order)
        return new_order
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/list", response_model=List[OrderOut])
async def list_orders(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    repo = OrderRepository(db)
    return await repo.list(skip, limit)

