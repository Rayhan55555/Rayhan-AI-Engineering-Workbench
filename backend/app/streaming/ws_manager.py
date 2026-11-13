import json
import asyncio
from typing import Dict, List, Any
from fastapi import WebSocket


class ConnectionManager:
    """
    WebSocket connection manager for pushing real-time workbench notifications:
    - Tool approval pending alerts
    - Agent execution lifecycle changes
    - Budget / cost threshold alerts
    """

    def __init__(self):
        self._active_connections: Dict[str, List[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            if user_id not in self._active_connections:
                self._active_connections[user_id] = []
            self._active_connections[user_id].append(websocket)

    async def disconnect(self, user_id: str, websocket: WebSocket):
        async with self._lock:
            if user_id in self._active_connections:
                if websocket in self._active_connections[user_id]:
                    self._active_connections[user_id].remove(websocket)
                if not self._active_connections[user_id]:
                    del self._active_connections[user_id]

    async def send_personal_message(self, message: Dict[str, Any], user_id: str):
        payload = json.dumps(message)
        async with self._lock:
            sockets = list(self._active_connections.get(user_id, []))

        for socket in sockets:
            try:
                await socket.send_text(payload)
            except Exception:
                await self.disconnect(user_id, socket)

    async def broadcast(self, message: Dict[str, Any]):
        payload = json.dumps(message)
        async with self._lock:
            all_sockets = [
                (uid, ws)
                for uid, sockets in self._active_connections.items()
                for ws in sockets
            ]

        for uid, ws in all_sockets:
            try:
                await ws.send_text(payload)
            except Exception:
                await self.disconnect(uid, ws)

    def count_active_users(self) -> int:
        return len(self._active_connections)


ws_manager = ConnectionManager()
