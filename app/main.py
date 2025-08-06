import asyncio

from fastapi import FastAPI, Depends, HTTPException,WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.routers import auth, users, ws, products, metrics
from app.database import get_db, Base, engine
from app.routers.ws import manager
from app.schemas import ProductCreate, ProductOut, OrderCreate, OrderOut
from app.repositories.order_repository import OrderRepository
from app.security import verify_token
from app.tasks import periodic_critical_stock_check

app = FastAPI(title="Stok ve Sipariş Yönetim Sistemi")
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(products.router, prefix="/orders", tags=["orders"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
app.include_router(ws.router)


@app.on_event("startup")
async def startup():
    # Veritabanı tablolarını oluşturur
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Periyodik kritik stok kontrolünü başlat
    asyncio.create_task(periodic_critical_stock_check())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    user_email = verify_token(token)
    if user_email is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, user_email)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You said: {data}", user_email)
    except WebSocketDisconnect:
        manager.disconnect(user_email)