from typing import List

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.notifications import notify_critical_stock
from app.repositories.product_repository import ProductRepository
from app.schemas import ProductUpdate, ProductCreate, ProductOut

router = APIRouter()

@router.put("/update/{product_id}")
async def update_product(product_id: int, product_update: ProductUpdate, db: AsyncSession = Depends(get_db)):
    repo = ProductRepository(db)
    product = await repo.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product_update.price is not None:
        product.price = product_update.price
    if product_update.stock is not None:
        product = await repo.update_stock(product_id, product_update.stock)
    else:
        db.add(product)
        await db.commit()
        await db.refresh(product)

    user_email = "berna@example.com"  # gerçek sistemde kullanıcıyı bulup geçireceğiz
    await notify_critical_stock(user_email, product)

    return product

@router.post("/create/", response_model=ProductOut)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    repo = ProductRepository(db)
    db_product = await repo.create(product)
    return db_product

@router.get("/list/", response_model=List[ProductOut])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    repo = ProductRepository(db)
    products = await repo.list(skip, limit)
    return products




