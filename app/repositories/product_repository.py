from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Product
from app.schemas import ProductCreate, ProductUpdate

class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, product_create: ProductCreate) -> Product:
        product = Product(**product_create.dict())
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def get(self, product_id: int) -> Product | None:
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        return result.scalars().first()

    async def list(self, skip: int = 0, limit: int = 100):
        result = await self.db.execute(select(Product).offset(skip).limit(limit))
        return result.scalars().all()

    async def filter(self):
        result = await self.db.execute(select(Product).where(Product.stock <= Product.critical_stock))
        return result.scalars().all()

    async def update_stock(self, product_id: int, new_stock: int) -> Product | None:
        product = await self.get(product_id)
        if not product:
            return None
        product.stock = new_stock
        await self.db.commit()
        await self.db.refresh(product)
        return product
