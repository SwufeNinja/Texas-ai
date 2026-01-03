from __future__ import annotations

import random
from typing import Tuple

from .game_engine import GameEngine


class AIAgent:
    """
    A simple rule-based AI agent for Texas Hold'em.
    
    Current strategy is purely probabilistic and reactive:
    1. Checks if checking is possible.
    2. Calls if the amount is small (<= BB) or with 20% probability.
    3. Raises with strong hands (randomly simulated 15% of the time if raising is valid).
    4. Goes All-in rarely (2%) if possible.
    5. Folds otherwise.
    
    TODO: Implement equity-based decision making (Monte Carlo simulations).
    """
    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()

    def choose_action(self, engine: GameEngine, player_id: str) -> Tuple[str, int]:
        """
        Decides on an action based on current game state.
        
        Args:
            engine: The GameEngine instance containing current game state.
            player_id: The ID of the AI player acting.
            
        Returns:
            Tuple[str, int]: The action name (fold, check, call, raise, allin) and amount.
        """
        options = engine.legal_actions(player_id)
        if not options:
            return "fold", 0

        # Always check if free
        if options.get("check"):
            return "check", 0

        to_call = options.get("call", 0)
        raise_info = options.get("raise")

        # Call Logic
        if to_call > 0:
            # Call if it's cheap (one big blind or less) or random bluff/strength
            if to_call <= engine.room.big_blind or self._rng.random() < 0.2:
                return "call", 0
            # Otherwise fold
            return "fold", 0

        # Raise Logic
        if raise_info and self._rng.random() < 0.15:
            # Raise diverse amounts between min and max
            amount = min(max(raise_info["min"], engine.room.big_blind), raise_info["max"])
            if amount >= raise_info["min"]:
                return "raise", amount

        # All-in Logic (Desperation or Value Shove)
        if options.get("allin") and self._rng.random() < 0.02:
            return "allin", 0

        return "fold", 0
