from __future__ import annotations

import asyncio
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import game_service
from .global_state import state, STATIC_DIR

# Initialize FastAPI App
app = FastAPI()

# Mount Static Files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Request Models
class AIJoinRequest(BaseModel):
    player_id: str
    name: str = "AI"
    chips: int = 200

class AIRemoveRequest(BaseModel):
    player_id: str

# --- HTTP Endpoints ---

@app.get("/health")
def health() -> Dict[str, bool]:
    """Health check endpoint."""
    return {"ok": True}

@app.get("/")
def index() -> FileResponse:
    """Serves the main game page."""
    return FileResponse(STATIC_DIR / "index.html")

@app.post("/ai")
async def add_ai(request: AIJoinRequest) -> Dict[str, Any]:
    """Adds an AI player to the game."""
    async with state.engine_lock:
        return await game_service.add_ai_player(request.player_id, request.name, request.chips)

@app.post("/ai/remove")
async def remove_ai(request: AIRemoveRequest) -> Dict[str, Any]:
    """Removes an AI player from the game."""
    async with state.engine_lock:
        return await game_service.remove_ai_player(request.player_id)

# --- WebSocket Endpoint ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Handles real-time game communication."""
    player_id = ""
    try:
        await websocket.accept()
        
        # 1. Wait for Join Message
        join_msg = await websocket.receive_json()
        if join_msg.get("type") != "join":
            await websocket.close(code=1008)
            return
            
        data = join_msg.get("data", {})
        player_id = data.get("player_id", "")
        name = data.get("name", "Player")

        if not player_id:
            await websocket.close(code=1008)
            return

        # 2. Join Logic
        async with state.engine_lock:
            await game_service.handle_player_connect(websocket, player_id, name)

        # 3. Message Loop
        while True:
            message = await websocket.receive_json()
            msg_type = message.get("type")
            
            if msg_type == "ready":
                ready_value = bool(message.get("data", {}).get("ready", True))
                async with state.engine_lock:
                    await game_service.handle_player_ready(player_id, ready_value, websocket)
                continue
                
            if msg_type == "action":
                action_data = message.get("data", {})
                action = action_data.get("action", "")
                amount = int(action_data.get("amount", 0) or 0)
                
                async with state.engine_lock:
                    await game_service.handle_player_action(player_id, action, amount, websocket)
                continue

    except WebSocketDisconnect:
        async with state.engine_lock:
            await game_service.handle_player_disconnect(websocket, player_id)
