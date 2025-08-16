from datetime import date, timedelta
from typing import Dict, Any
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Product, Order  # modellerinizi import edin
from sqlalchemy.future import select


class ForecastResult(Dict[str, Any]):
    pass


async def fetch_daily_sales(db: AsyncSession, product_id: int) -> pd.Series:
    stmt = select(Order).where(Order.product_id == product_id)
    result = await db.execute(stmt)
    items = result.scalars().all()

    if not items:
        return pd.Series(dtype="float64")

    # DataFrame oluştur
    df = pd.DataFrame([{"day": item.created_at.date(), "qty": item.quantity} for item in items])
    s = df.groupby("day")["qty"].sum().asfreq("D", fill_value=0)
    return s


async def fetch_current_stock(db: AsyncSession, product_id: int) -> int:
    stmt = select(Product).where(Product.id == product_id)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    return product.stock_quantity if product else 0


def _naive_forecast(series: pd.Series, horizon: int) -> pd.Series:
    window = series.tail(min(7, len(series))).mean() if len(series) else 0
    idx = pd.date_range(series.index.max() + pd.Timedelta(days=1), periods=horizon, freq="D")
    return pd.Series([float(window)] * horizon, index=idx)


def _sarimax_forecast(series: pd.Series, horizon: int) -> pd.Series:
    model = SARIMAX(series, order=(1, 1, 1), seasonal_order=(1, 1, 1, 7),
                    enforce_stationarity=False, enforce_invertibility=False)
    res = model.fit(disp=False)
    fc = res.forecast(steps=horizon)
    fc[fc < 0] = 0.0
    return fc


def _recommended_order_qty(forecast: pd.Series, current_stock: int, lead_time_days: int, safety_days: int = 7) -> Dict[
    str, Any]:
    cum = forecast.cumsum()
    stockout_idx = None
    try:
        stockout_idx = cum[cum > current_stock].index[0]
    except Exception:
        pass

    target_days = max(lead_time_days + safety_days, 1)
    demand_target = float(forecast.head(target_days).sum())
    recommended = max(0.0, demand_target - current_stock)

    return {
        "stockout_date": stockout_idx.date().isoformat() if stockout_idx is not None else None,
        "target_cover_days": target_days,
        "recommended_order_qty": int(round(recommended))
    }


async def forecast_product_demand(db: AsyncSession, product_id: int, horizon_days: int = 30,
                                  lead_time_days: int = 7) -> ForecastResult:
    series = await fetch_daily_sales(db, product_id)
    current_stock = await fetch_current_stock(db, product_id)

    if len(series) < 28:
        fc = _naive_forecast(series, horizon_days)
        model_type = "naive_last7_mean"
    else:
        try:
            fc = _sarimax_forecast(series, horizon_days)
            model_type = "sarimax(1,1,1)(1,1,1)[7]"
        except Exception:
            fc = _naive_forecast(series, horizon_days)
            model_type = "fallback_naive"

    reorder = _recommended_order_qty(fc, current_stock, lead_time_days)

    return ForecastResult({
        "product_id": product_id,
        "model": model_type,
        "horizon_days": horizon_days,
        "lead_time_days": lead_time_days,
        "current_stock": current_stock,
        "forecast": [{"date": d.date().isoformat(), "demand": float(q)} for d, q in fc.items()],
        **reorder
    })
def is_stock_critical(forecast_result: dict, threshold_days: int = 7) -> bool:
    """
    Stok tükenme tarihi, threshold_days içinde ise kritik kabul edilir.
    """
    stockout = forecast_result.get("stockout_date")
    if stockout is None:
        return False
    from datetime import datetime, timedelta
    stockout_date = datetime.fromisoformat(stockout).date()
    return (stockout_date - datetime.today().date()).days <= threshold_days
