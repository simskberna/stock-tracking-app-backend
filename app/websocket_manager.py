from typing import Dict
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.security import decode_access_token


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # key user_email

    async def connect(self, websocket: WebSocket, token: str, db: AsyncSession):
        payload = decode_access_token(token)
        if not payload:
            await websocket.close(code=1008)  # Policy Violation
            return None
        user_email = payload.get("sub")
        user_repo = UserRepository(db)
        user = await user_repo.get_by_email(user_email)
        if not user:
            await websocket.close(code=1008)
            return None
        await websocket.accept()
        self.active_connections[user_email] = websocket
        return user_email

    def disconnect(self, user_email: str):
        self.active_connections.pop(user_email, None)

    async def send_personal_message(self, user_email: str, message: dict):
        websocket = self.active_connections.get(user_email)
        if websocket:
            await websocket.send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    user_email = await manager.connect(websocket, token, db)
    if not user_email:
        return  # Connection closed due to invalid token or user
    try:
        while True:
            data = await websocket.receive_text()
            # echo message
            await manager.send_personal_message(user_email, {"message": f"You wrote: {data}"})
    except WebSocketDisconnect:
        manager.disconnect(user_email)
