from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict
from ..game.engine import TexasHoldemGame
from ..game.models import Player

router = APIRouter()

# Simple in-memory game storage (for now, supports 1 game)
class GameManager:
    def __init__(self):
        self.game_instance = None

    def create_game(self):
        self.game_instance = TexasHoldemGame()
        # Add some initial players for testing
        self.game_instance.add_player(Player("Human", chips=1000))
        # Add generic AI for now, will be replaced by smarter AI integration later
        self.game_instance.add_player(Player("Bot", is_ai=True, chips=1000))
        self.game_instance.start_hand()
        return {"status": "created", "game_id": "default"}

    def get_game(self):
        if not self.game_instance:
             raise HTTPException(status_code=404, detail="Game not created")
        return self.game_instance

game_manager = GameManager()

@router.post("/game/create")
async def create_game():
    return game_manager.create_game()

@router.get("/game/state")
async def get_game_state():
    """Returns a simplified JSON representation of the current game state."""
    game = game_manager.get_game()
    
    # We need to manually construct a serializable dict since our objects aren't Pydantic models yet
    # This is a temporary serialization
    # Calculate legal actions for current player
    current_p = game.players[game.current_player_index]
    legal_actions = []
    if current_p.status == "ACTIVE": # Check if active (actually engine handles this but good to be safe)
        legal_actions = game.get_legal_actions(current_p)

    return {
        "stage": game.stage.name,
        "pot": game.pot,
        "current_bet": game.current_bet,
        "board": [str(c) for c in game.board],
        "current_player_index": game.current_player_index, 
        "legal_actions": legal_actions,
        "players": [
            {
                "name": p.name,
                "chips": p.chips,
                "bet": p.current_bet,
                "status": p.status.name,
                "is_active": p.status.name == "ACTIVE",
                "hand": [str(c) for c in p.hand] if p.name == "Human" or game.stage.name == "SHOWDOWN" else [] 
            }
            for p in game.players
        ]
    }

from .schemas import Action
import time

@router.post("/game/action")
async def take_action(action: Action):
    game = game_manager.get_game()
    current_p = game.players[game.current_player_index]
    
    # Validation
    if current_p.name != "Human":
        raise HTTPException(status_code=400, detail="Not your turn")
    
    # Execute Human Action
    try:
        game.step(action.action, action.amount)
    except Exception as e:
         raise HTTPException(status_code=400, detail=str(e))

    # After human acts, loop through AI turns until it's human's turn again or game over
    while game.stage.name != "GAME_OVER":
        current_p = game.players[game.current_player_index]
        if current_p.name == "Human":
            break # Back to human
        
        if current_p.status.name != "ACTIVE":
             # This shouldn't happen usually due to engine logic, but if so, step?
             # Engine handles skipping. If we are here, it's an active AI.
             pass

        # AI Turn
        # For now, simple AI: Check/Call or Fold if bet too high
        # In future: Call Agent.py
        
        # Simulate thinking
        # time.sleep(0.5) # Removed for speed in initial prototype
        
        # Simple Logic:
        legal = game.get_legal_actions(current_p)
        ai_action = "fold"
        ai_amt = 0
        if "check" in legal:
            ai_action = "check"
        elif "call" in legal:
            ai_action = "call"
        else:
            ai_action = "fold"
            
        print(f"AI {current_p.name} doing {ai_action}")
        game.step(ai_action, ai_amt)

    return {"status": "ok"}
    
@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    try:
        while True:
            # Simple echo for testing connection
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
