import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from starlette.middleware.cors import CORSMiddleware

from app.routers import auth, users, ws, products, metrics, orders
from app.database import Base, engine
from app.routers.ws import manager
from app.security import verify_token
from app.tasks import periodic_critical_stock_check

app = FastAPI(title="Stok ve Sipariş Yönetim Sistemi")
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
app.include_router(ws.router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    # ceritabanı tablolarını oluşturur
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # periyodik kritik stok kontrolünü başlat
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