import asyncio
from fastapi import APIRouter, WebSocket, Query, Depends, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.websocket_manager import manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    user_email = await manager.connect(websocket, token, db)
    if not user_email:
        return

    try:
        while True:
            data_task = asyncio.create_task(websocket.receive_text())
            ping_task = asyncio.create_task(asyncio.sleep(30))

            done, pending = await asyncio.wait(
                [data_task, ping_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            if ping_task in done:
                await websocket.send_json({"type": "ping"})

            if data_task in done:
                try:
                    data = data_task.result()
                    await manager.send_personal_message(user_email, {"message": f"You wrote: {data}"})
                except Exception as e:
                    await websocket.send_json({"error": str(e)})

            for task in pending:
                task.cancel()

    except WebSocketDisconnect:
        manager.disconnect(user_email)