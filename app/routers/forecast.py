from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.forecast_service import forecast_product_demand

router = APIRouter(prefix="/forecast", tags=["forecast"])

@router.get("/{product_id}")
async def get_forecast(
    product_id: int,
    horizon_days: int = Query(30, ge=7, le=180),
    lead_time_days: int = Query(7, ge=0, le=60),
    db: AsyncSession = Depends(get_db)
):
    """
    Belirtilen ürün için günlük talep tahmini ve yeniden sipariş önerisi döndürür.
    """
    result = await forecast_product_demand(db, product_id, horizon_days, lead_time_days)
    return result
