from __future__ import annotations

from typing import Dict, List, Tuple

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, player_id: str, accept: bool = True) -> None:
        if accept:
            await websocket.accept()
        for existing_ws, existing_player_id in list(self._connections.items()):
            if existing_player_id == player_id and existing_ws is not websocket:
                self._connections.pop(existing_ws, None)
                try:
                    await existing_ws.close(code=1000)
                except RuntimeError:
                    pass
        self._connections[websocket] = player_id

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.pop(websocket, None)

    def player_id_for(self, websocket: WebSocket) -> str:
        return self._connections[websocket]

    async def broadcast_json(self, payload: dict) -> None:
        for websocket in list(self._connections.keys()):
            await self.send_json(websocket, payload)

    async def send_json(self, websocket: WebSocket, payload: dict) -> None:
        try:
            await websocket.send_json(payload)
        except RuntimeError:
            self.disconnect(websocket)

    def connections(self) -> List[Tuple[WebSocket, str]]:
        return list(self._connections.items())
