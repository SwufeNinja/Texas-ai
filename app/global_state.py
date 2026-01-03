from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from .ai_agent import AIAgent
from .connection_mgr import ConnectionManager
from .game_engine import GameEngine
from .models import Room

# Constants
ROOM_ID = "default"
MAX_SEATS = 8
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# Global State Container
class GlobalState:
    def __init__(self):
        self.manager = ConnectionManager()
        self.ai_agent = AIAgent()
        self.engine_lock = asyncio.Lock()
        self.room = Room(id=ROOM_ID, players=[], small_blind=5, big_blind=10)
        self.engine = GameEngine(self.room)
        self.seq_counter = 0

    def reset(self):
        """Resets the game state but keeps connection manager."""
        self.room = Room(id=ROOM_ID, players=[], small_blind=5, big_blind=10)
        self.engine = GameEngine(self.room)
        self.seq_counter = 0

# Singleton instance
state = GlobalState()
