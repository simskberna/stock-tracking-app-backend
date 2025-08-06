from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import UserOut
from app.security import get_current_user
from app.database import get_db

router = APIRouter()

@router.get("/me", response_model=UserOut)
async def read_current_user(current_user=Depends(get_current_user)):
    return current_user
