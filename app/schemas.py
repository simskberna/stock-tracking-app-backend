from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: str | None = None
    price: int = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)
    critical_stock: int = Field(default=10, ge=0)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    description: str | None = None
    price: int | None = None
    stock: int | None = None
    critical_stock: int | None = None

class ProductOut(ProductBase):
    id: int

    class Config:
        orm_mode = True

class OrderCreate(BaseModel):
    product_id: int
    quantity: int

class OrderOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    total: int
    order_date: datetime

    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"