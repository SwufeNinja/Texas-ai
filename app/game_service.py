from __future__ import annotations

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any

from fastapi import WebSocket

from .global_state import state, MAX_SEATS
from .models import Player, PlayerStatus, Stage

# --- Helper Functions (Private-ish) ---

def _find_player(player_id: str) -> Optional[Player]:
    """Finds a player in the current room by ID."""
    for player in state.room.players:
        if player.id == player_id:
            return player
    return None

def _next_seq() -> int:
    """Increments and returns the next sequence number."""
    state.seq_counter += 1
    return state.seq_counter

def _envelope(message_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Wraps data in a standard message envelope."""
    return {
        "type": message_type,
        "schema_version": 1,
        "room_id": state.room.id,
        "msg_id": f"srv-{uuid.uuid4().hex}",
        "seq": _next_seq(),
        "ts": int(time.time() * 1000),
        "data": data,
    }

def _hand_in_progress() -> bool:
    """Checks if a hand is currently active."""
    if state.room.awaiting_ready:
        return False
    if state.room.stage != Stage.PREFLOP:
        return True
    if state.room.community_cards or state.room.pot:
        return True
    if any(p.hand for p in state.room.players):
        return True
    return False

def _fill_open_seats() -> None:
    """Seats waiting players if there are open seats."""
    seated_count = len([p for p in state.room.players if p.seated])
    open_seats = MAX_SEATS - seated_count
    if open_seats <= 0:
        return
    for player in state.room.players:
        if open_seats <= 0:
            break
        if not player.seated and player.chips > 0:
            player.seated = True
            player.ready = False
            open_seats -= 1

def _prune_disconnected_players() -> None:
    """Removes players who are disconnected and not in a critical state."""
    active_ids = {pid for _, pid in state.manager.connections()}
    current_players = list(state.room.players)
    state.room.players.clear()
    for player in current_players:
        # Keep player if AI, connected, or has chips (and thus might return)
        # Simplification: Only prune if completely gone and not AI?
        # Original logic: keep if AI or connected or chips > 0
        if player.is_ai or player.id in active_ids or player.chips > 0:
            state.room.players.append(player)
        else:
            print(f"Pruning disconnected player: {player.id}")
    _fill_open_seats()

# --- Game Logic Services ---

async def broadcast_system(event: str, data: Dict[str, Any]) -> None:
    """Broadcasts a system event to all connected clients."""
    payload = {"event": event, **data}
    await state.manager.broadcast_json(_envelope("system", payload))

async def broadcast_state() -> None:
    """Broadcasts the current game state to all connected clients."""
    for websocket, player_id in state.manager.connections():
        await state.manager.send_json(
            websocket,
            _envelope("game_update", state.engine.state_snapshot(player_id)),
        )

async def run_ai_turns() -> None:
    """Executes AI turns until a human player needs to act or round ends."""
    while True:
        if state.room.stage == Stage.SHOWDOWN:
            return
        
        current_index = state.room.current_actor_index
        # Safety check for empty players list or out of bounds
        if not state.room.players or current_index >= len(state.room.players):
             return

        current = state.room.players[current_index]
        if not current.is_ai or not current.can_act():
            return

        # Simulate thinking time
        await asyncio.sleep(1)
        
        action, amount = state.ai_agent.choose_action(state.engine, current.id)
        ok, _ = state.engine.process_action(current.id, action, amount)
        
        if not ok:
            # Fallback if AI chooses invalid action
            fallback = state.engine.legal_actions(current.id)
            if fallback.get("check"):
                state.engine.process_action(current.id, "check", 0)
            elif fallback.get("call", 0) > 0:
                state.engine.process_action(current.id, "call", 0)
            else:
                state.engine.process_action(current.id, "fold", 0)
        
        await broadcast_state()

async def maybe_start_hand() -> None:
    """Starts a new hand if conditions are met."""
    # Need at least 2 seated players with chips
    if len([p for p in state.room.players if p.seated and p.chips > 0]) < 2:
        return

    active_ids = {pid for _, pid in state.manager.connections()}
    
    # Check if all seated active players are ready
    # Note: AI are always "ready" effectively, but we check specific flag
    if any(
        p.seated
        and p.chips > 0
        and not p.ready
        and (p.is_ai or p.id in active_ids)
        for p in state.room.players
    ):
        return

    if state.room.awaiting_ready:
        return
    
    # Don't start if hand already in progress
    if _hand_in_progress():
        return
        
    state.engine.start_hand()

async def maybe_start_next_hand() -> None:
    """Checks if the current hand is over and prepares the next one."""
    if state.room.stage != Stage.SHOWDOWN:
        return
    
    # Prune players before next hand
    _prune_disconnected_players()

    # Reset ready status for next hand
    if not state.room.awaiting_ready:
        for player in state.room.players:
            if player.seated and player.chips > 0:
                # auto-ready AI, unready humans
                player.ready = player.is_ai
            elif not player.seated:
                player.ready = False
        
        state.room.awaiting_ready = True
        await broadcast_system("ready_reset", {})
        await broadcast_state()
        return

    # If everyone is ready, start!
    if len([p for p in state.room.players if p.chips > 0]) < 2:
        return

    active_ids = {pid for _, pid in state.manager.connections()}
    if any(
        p.seated
        and p.chips > 0
        and not p.ready
        and (p.is_ai or p.id in active_ids)
        for p in state.room.players
    ):
        return

    state.room.awaiting_ready = False
    state.engine.start_hand()
    await broadcast_state()
    await run_ai_turns()

# --- Public API Services ---

async def add_ai_player(player_id: str, name: str, chips: int) -> Dict[str, Any]:
    """Adds an AI player to the game."""
    if _find_player(player_id) is not None:
        return {"ok": False, "message": "player exists"}
    
    if _hand_in_progress():
        return {"ok": False, "message": "game already started"}

    seated = len([p for p in state.room.players if p.seated]) < MAX_SEATS
    state.room.players.append(
        Player(
            id=player_id,
            name=name,
            is_ai=True,
            chips=chips,
            ready=seated,
            seated=seated,
        )
    )
    _fill_open_seats()
    
    await broadcast_system("player_joined", {"player_id": player_id})
    await maybe_start_hand()
    await broadcast_state()
    await run_ai_turns()
    await maybe_start_next_hand()
    return {"ok": True}

async def remove_ai_player(player_id: str) -> Dict[str, Any]:
    """Removes an AI player from the game."""
    player = _find_player(player_id)
    if player is None or not player.is_ai:
        return {"ok": False, "message": "ai not found"}
    
    if _hand_in_progress():
        return {"ok": False, "message": "game already started"}
        
    state.room.players = [p for p in state.room.players if p.id != player_id]
    _fill_open_seats()
    
    await broadcast_system("player_left", {"player_id": player_id})
    await maybe_start_hand()
    await broadcast_state()
    return {"ok": True}

async def handle_player_connect(websocket: WebSocket, player_id: str, name: str):
    """Handles a new player connection."""
    if not state.manager.connections():
        state.reset()
        
    if state.manager.is_connected(player_id):
        await state.manager.send_json(
            websocket,
            _envelope(
                "error",
                {
                    "code": "ALREADY_CONNECTED",
                    "message": "player already connected",
                    "details": {"player_id": player_id},
                },
            ),
        )
        await websocket.close(code=1008)
        return

    player = _find_player(player_id)
    hand_in_progress = _hand_in_progress()
    
    if player is None:
        if hand_in_progress:
            seated = False
        else:
            seated = len([p for p in state.room.players if p.seated]) < MAX_SEATS
        # Create new player
        state.room.players.append(
            Player(id=player_id, name=name, is_ai=False, chips=200, seated=seated)
        )
        await broadcast_system(
            "player_joined",
            {"player_id": player_id, "seated": seated, "waiting": not seated},
        )
    else:
        # Reconnecting player
        player.name = name
        if not player.seated and not hand_in_progress:
            _fill_open_seats()

    await state.manager.connect(websocket, player_id, accept=False, allow_replace=False)
    
    await state.manager.send_json(
        websocket,
        _envelope("join_ok", {"player_id": player_id}),
    )
    
    await maybe_start_hand()
    await broadcast_state()
    await run_ai_turns()
    await maybe_start_next_hand()

async def handle_player_disconnect(websocket: WebSocket, player_id: str):
    """Handles player disconnection."""
    state.manager.disconnect(websocket)
    
    if not _hand_in_progress():
        _prune_disconnected_players()
        await maybe_start_hand()
        # If the stage changed (game started), broadcast
        if state.room.stage != Stage.PREFLOP:
            await broadcast_state()
            await run_ai_turns()
            await maybe_start_next_hand()

    if player_id:
        player = _find_player(player_id)
        if player is not None:
            player.ready = False
            # Check if player needs to act
            if player.can_act():
                if state.engine._current_player() is player:
                    # Fold if it's their turn
                    state.engine.process_action(player_id, "fold", 0)
                else:
                    # Just mark folded/away?
                    player.status = PlayerStatus.FOLDED
                    player.has_acted = True
            
            await broadcast_system("player_left", {"player_id": player_id})
            await broadcast_state()
            await maybe_start_next_hand()
            
    if not state.manager.connections():
        state.reset()

async def handle_player_ready(player_id: str, ready_value: bool, websocket: WebSocket):
    """Handles player ready toggle."""
    player = _find_player(player_id)
    if player is None:
        return
    
    if not player.seated:
        await state.manager.send_json(
            websocket,
            _envelope(
                "error",
                {
                    "code": "NOT_SEATED",
                    "message": "player not seated",
                    "details": {"player_id": player_id},
                },
            ),
        )
        return

    if _hand_in_progress() and not ready_value and not state.room.awaiting_ready:
        await state.manager.send_json(
            websocket,
            _envelope(
                "error",
                {
                    "code": "HAND_IN_PROGRESS",
                    "message": "cannot unready during an active hand",
                    "details": {"player_id": player_id},
                },
            ),
        )
        return

    player.ready = ready_value
    await broadcast_system(
        "player_ready",
        {"player_id": player_id, "ready": ready_value},
    )
    
    await maybe_start_hand()
    await broadcast_state()
    await run_ai_turns()
    await maybe_start_next_hand()

async def handle_player_action(player_id: str, action: str, amount: int, websocket: WebSocket):
    """Handles a game action (check, call, raise, fold)."""
    ok, reason = state.engine.process_action(player_id, action, amount)
    if not ok:
        details = state.engine.action_error_details(player_id, action, amount, reason)
        if reason == "unknown player":
            active_ids = [pid for _, pid in state.manager.connections()]
            details.update(
                {
                    "connected_player_id": player_id,
                    "active_player_ids": active_ids,
                    "room_player_ids": [p.id for p in state.room.players],
                }
            )
        await state.manager.send_json(
            websocket,
            _envelope(
                "error",
                {
                    "code": "INVALID_ACTION",
                    "message": reason,
                    "details": details,
                },
            ),
        )
        return

    await broadcast_state()
    await run_ai_turns()
    await maybe_start_next_hand()

