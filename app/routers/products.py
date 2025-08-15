from typing import List

from fastapi import Depends, HTTPException, APIRouter, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.notifications import notify_critical_stock
from app.repositories.product_repository import ProductRepository
from app.schemas import ProductUpdate, ProductCreate, ProductOut
from app.tasks import  send_email_critical_product

router = APIRouter()

@router.put("/update/{product_id}")
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    repo = ProductRepository(db)
    product = await repo.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Price güncelle
    if product_update.price is not None:
        product.price = product_update.price

    # Stock güncelle
    if product_update.stock is not None:
        product.stock = product_update.stock

    # Veritabanı commit ve refresh
    db.add(product)
    await db.commit()
    await db.refresh(product)

    # Kullanıcıya kritik stok bildirimi (sadece bu ürün için)
    user_email = "berna@example.com"
    await notify_critical_stock(user_email, product)
    await send_email_critical_product(user_email, product)

    return product

@router.post("/create/", response_model=ProductOut)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    repo = ProductRepository(db)
    db_product = await repo.create(product)
    return db_product

@router.get("/list/")
async def list_products(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    repo = ProductRepository(db)
    products = await repo.list(skip, limit)
    total = await repo.count()

    return {
        "data": products,
        "total": total
    }

@router.get("/critical_stock_list/", response_model=List[ProductOut])
async def list_critical_stock_products(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    repo = ProductRepository(db)
    products = await repo.get_critical_stock_products(skip=skip, limit=limit)
    return products
