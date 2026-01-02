from __future__ import annotations

import asyncio
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .ai_agent import AIAgent
from .connection_mgr import ConnectionManager
from .game_engine import GameEngine
from .models import Player, PlayerStatus, Room, Stage

app = FastAPI()
manager = ConnectionManager()
ai_agent = AIAgent()
engine_lock = asyncio.Lock()
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

ROOM_ID = "default"
room = Room(id=ROOM_ID, players=[], small_blind=5, big_blind=10)
engine = GameEngine(room)
seq_counter = 0


class AIJoinRequest(BaseModel):
    player_id: str
    name: str = "AI"
    chips: int = 200


def _find_player(player_id: str) -> Optional[Player]:
    for player in room.players:
        if player.id == player_id:
            return player
    return None


def _maybe_start_hand() -> None:
    if len([p for p in room.players if p.chips > 0]) < 2:
        return
    if any(p.chips > 0 and not p.ready for p in room.players):
        return
    if room.awaiting_ready:
        return
    if room.stage != Stage.PREFLOP or room.community_cards or room.pot:
        return
    if any(p.hand for p in room.players):
        return
    engine.start_hand()


def _hand_in_progress() -> bool:
    if room.stage != Stage.PREFLOP:
        return True
    if room.community_cards or room.pot:
        return True
    if any(p.hand for p in room.players):
        return True
    return False


def _prune_disconnected_players() -> None:
    active_ids = {pid for _, pid in manager.connections()}
    current_players = list(room.players)
    room.players.clear()
    for player in current_players:
        if player.is_ai or player.id in active_ids:
            room.players.append(player)
        else:
            print(f"Pruning disconnected player: {player.id}")


def _next_seq() -> int:
    global seq_counter
    seq_counter += 1
    return seq_counter


def _reset_game() -> None:
    global room, engine, seq_counter
    room = Room(id=ROOM_ID, players=[], small_blind=5, big_blind=10)
    engine = GameEngine(room)
    seq_counter = 0


def _envelope(message_type: str, data: dict) -> dict:
    return {
        "type": message_type,
        "schema_version": 1,
        "room_id": room.id,
        "msg_id": f"srv-{uuid.uuid4().hex}",
        "seq": _next_seq(),
        "ts": int(time.time() * 1000),
        "data": data,
    }


async def _send_state_to(websocket: WebSocket, player_id: str) -> None:
    await manager.send_json(
        websocket,
        _envelope("game_update", engine.state_snapshot(player_id)),
    )


async def _broadcast_state() -> None:
    for websocket, player_id in manager.connections():
        await _send_state_to(websocket, player_id)


async def _broadcast_system(event: str, data: dict) -> None:
    payload = {"event": event, **data}
    await manager.broadcast_json(_envelope("system", payload))


async def _run_ai_turns() -> None:
    while True:
        if room.stage == Stage.SHOWDOWN:
            return
        current = room.players[room.current_actor_index]
        if not current.is_ai or not current.can_act():
            return
        await asyncio.sleep(1)
        action, amount = ai_agent.choose_action(engine, current.id)
        ok, _ = engine.process_action(current.id, action, amount)
        if not ok:
            fallback = engine.legal_actions(current.id)
            if fallback.get("check"):
                engine.process_action(current.id, "check", 0)
            elif fallback.get("call", 0) > 0:
                engine.process_action(current.id, "call", 0)
            else:
                engine.process_action(current.id, "fold", 0)
        await _broadcast_state()


async def _maybe_start_next_hand() -> None:
    if room.stage != Stage.SHOWDOWN:
        return
    
    # Caller must hold engine_lock
    _prune_disconnected_players()

    if not room.awaiting_ready:
        for player in room.players:
            if player.chips > 0:
                player.ready = player.is_ai
        room.awaiting_ready = True
        await _broadcast_system("ready_reset", {})
        await _broadcast_state()
        return
    if len([p for p in room.players if p.chips > 0]) < 2:
        return
    if any(p.chips > 0 and not p.ready for p in room.players):
        return
    room.awaiting_ready = False
    engine.start_hand()
    await _broadcast_state()
    await _run_ai_turns()


@app.get("/health")
def health() -> dict:
    return {"ok": True}


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/ai")
async def add_ai(request: AIJoinRequest) -> dict:
    async with engine_lock:
        if _find_player(request.player_id) is not None:
            return {"ok": False, "message": "player exists"}
        if _hand_in_progress():
            return {"ok": False, "message": "game already started"}
        room.players.append(
            Player(
                id=request.player_id,
                name=request.name,
                is_ai=True,
                chips=request.chips,
                ready=True,
            )
        )
        await _broadcast_system("player_joined", {"player_id": request.player_id})
        _maybe_start_hand()
        await _broadcast_state()
        await _run_ai_turns()
        await _maybe_start_next_hand()
        return {"ok": True}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    player_id = ""
    try:
        await websocket.accept()
        join = await websocket.receive_json()
        if join.get("type") != "join":
            await websocket.close(code=1008)
            return
        data = join.get("data", {})
        player_id = data.get("player_id", "")
        name = data.get("name", "Player")
        if not player_id:
            await websocket.close(code=1008)
            return

        async with engine_lock:
            if _hand_in_progress():
                await manager.send_json(
                    websocket,
                    _envelope("error", {"code": "GAME_STARTED", "message": "game already started"}),
                )
                await websocket.close(code=1008)
                return
            player = _find_player(player_id)
            if player is None:
                room.players.append(
                    Player(id=player_id, name=name, is_ai=False, chips=200)
                )
                await _broadcast_system("player_joined", {"player_id": player_id})

            await manager.connect(websocket, player_id, accept=False)
            _maybe_start_hand()
            await _broadcast_state()
            await _run_ai_turns()
            await _maybe_start_next_hand()

        while True:
            message = await websocket.receive_json()
            msg_type = message.get("type")
            if msg_type == "ready":
                ready_value = bool(message.get("data", {}).get("ready", True))
                async with engine_lock:
                    player = _find_player(player_id)
                    if player is None:
                        continue
                    player.ready = ready_value
                    await _broadcast_system(
                        "player_ready",
                        {"player_id": player_id, "ready": ready_value},
                    )
                    _maybe_start_hand()
                    await _broadcast_state()
                    await _run_ai_turns()
                    await _maybe_start_next_hand()
                continue
            if msg_type != "action":
                continue
            action_data = message.get("data", {})
            action = action_data.get("action", "")
            amount = int(action_data.get("amount", 0) or 0)
            async with engine_lock:
                ok, reason = engine.process_action(player_id, action, amount)
                if not ok:
                    await manager.send_json(
                        websocket,
                        _envelope("error", {"code": "INVALID_ACTION", "message": reason}),
                    )
                    continue
                await _broadcast_state()
                await _run_ai_turns()
                await _maybe_start_next_hand()
    except WebSocketDisconnect:
        async with engine_lock:
            manager.disconnect(websocket)
            if not _hand_in_progress():
                _prune_disconnected_players()
                _maybe_start_hand()
                if engine.room.stage != Stage.PREFLOP:
                    await _broadcast_state()
                    await _run_ai_turns()
                    await _maybe_start_next_hand()

            if player_id:
                player = _find_player(player_id)
                if player is not None:
                    player.ready = False
                    if player.can_act():
                        if engine._current_player() is player:
                            engine.process_action(player_id, "fold", 0)
                        else:
                            player.status = PlayerStatus.FOLDED
                            player.has_acted = True
                    await _broadcast_system("player_left", {"player_id": player_id})
                    await _broadcast_state()
                    await _maybe_start_next_hand()
            if not manager.connections():
                _reset_game()
