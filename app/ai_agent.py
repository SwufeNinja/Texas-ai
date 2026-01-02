from __future__ import annotations

import random
from typing import Tuple

from .game_engine import GameEngine


class AIAgent:
    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()

    def choose_action(self, engine: GameEngine, player_id: str) -> Tuple[str, int]:
        options = engine.legal_actions(player_id)
        if not options:
            return "fold", 0

        if options.get("check"):
            return "check", 0

        to_call = options.get("call", 0)
        raise_info = options.get("raise")

        if to_call > 0:
            if to_call <= engine.room.big_blind or self._rng.random() < 0.2:
                return "call", 0
            return "fold", 0

        if raise_info and self._rng.random() < 0.15:
            amount = min(max(raise_info["min"], engine.room.big_blind), raise_info["max"])
            if amount >= raise_info["min"]:
                return "raise", amount

        if options.get("allin") and self._rng.random() < 0.02:
            return "allin", 0

        return "fold", 0
