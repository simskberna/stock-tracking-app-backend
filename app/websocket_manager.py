# app/websocket_manager.py
from typing import Dict, Optional
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.security import decode_access_token


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # key = user_email

    async def connect(
        self,
        websocket: WebSocket,
        token: str,
        db: AsyncSession
    ) -> Optional[str]:
        await websocket.accept()

        payload = decode_access_token(token)
        if not payload:
            await websocket.send_json({"error": "Invalid or missing token"})
            await websocket.close(code=1008)
            return None

        user_email = payload.get("sub")
        user_repo = UserRepository(db)
        user = await user_repo.get_by_email(user_email)
        if not user:
            await websocket.send_json({"error": "User not found"})
            await websocket.close(code=1008)
            return None

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
