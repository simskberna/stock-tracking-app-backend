from fastapi import APIRouter, WebSocket, Query, Depends, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.websocket_manager import manager
from app.security import decode_access_token

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...), db: AsyncSession = Depends(get_db)):
    user_email = await manager.connect(websocket, token, db)
    if not user_email:
        return
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(user_email, {"message": f"You wrote: {data}"})
    except WebSocketDisconnect:
        manager.disconnect(user_email)
