from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import UserCreate, UserOut
from app.repositories.user_repository import UserRepository
from app.security import create_access_token, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES
from app.database import get_db

router = APIRouter()

async def get_user(db: AsyncSession, email: str):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(email)
    return user

@router.post("/register", response_model=UserOut)
async def register(user_create: UserCreate, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    existing_user = await repo.get_by_email(user_create.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await repo.create(user_create)
    return user

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),  # form-data olarak gelir
    db: AsyncSession = Depends(get_db),
):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(form_data.username)  # username yerine email kullanıyoruz

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}
