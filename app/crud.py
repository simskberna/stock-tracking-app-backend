from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Product
from schemas import ProductCreate, ProductUpdate

async def create_product(db: AsyncSession, product: ProductCreate) -> Product:
    db_product = Product(**product.dict())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product

async def get_product(db: AsyncSession, product_id: int) -> Product | None:
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalars().first()

async def get_products(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Product).offset(skip).limit(limit))
    return result.scalars().all()

async def update_product_stock(db: AsyncSession, product_id: int, new_stock: int) -> Product | None:
    product = await get_product(db, product_id)
    if not product:
        return None
    product.stock = new_stock
    await db.commit()
    await db.refresh(product)
    return product
