from typing import List, Dict, Any
import json
import logging
from .llm_client import LLMClient
from game.equity import EquityCalculator

class PokerAgent:
    def __init__(self, name: str, profile: str = "A professional poker player", client: LLMClient = None): # type: ignore
        self.name = name
        self.profile = profile
        self.client = client if client else LLMClient()
        self.equity_calculator = EquityCalculator()
        self.memories: List[str] = []

    def add_memory(self, event: str):
        """Adds a memory of a past hand/event."""
        self.memories.append(event)
        # Keep last 10 memories to fit in context
        if len(self.memories) > 10:
            self.memories.pop(0)

    def get_action(self, game_info: Dict[str, Any], valid_actions: List[str]) -> Dict[str, Any]:
        """
        Decides an action based on game state.
        Returns dict like: {"action": "raise", "amount": 10, "chat": "..."}
        """
        if not valid_actions:
            return {"action": "fold", "reasoning": "No valid actions"}

        # Calculate Equity
        my_hand = game_info.get('my_hand', [])
        board = game_info.get('board', [])
        
        # Determine num players (active)
        # game_info should ideally provide this. If not, guess from 'players' list length or default 2
        all_players_info = game_info.get('players', [])
        # We need active count. If string list, we can't tell easily unless parsed.
        # Fallback: assume 2 if heads up or unknown, or try to parse string? 
        # Better: let caller provide 'num_active_players'
        num_active = game_info.get('num_active_players', 2)
        
        equity = 0.0
        if my_hand:
            try:
                equity = self.equity_calculator.calculate_equity(my_hand, board, num_active_players=num_active)
            except Exception as e:
                logging.error(f"Equity calc error: {e}")
                equity = 0.0 # Ignore

        equity_percent = round(equity * 100, 1)

        memory_str = "\n".join([f"- {m}" for m in self.memories])
        if memory_str:
            memory_section = f"\nRecent History:\n{memory_str}\n"
        else:
            memory_section = ""

        system_message = (
            f"You are {self.name}, playing Texas Hold'em. {self.profile}\n"
            "Your goal is to win chips. You must make logical decisions based on your hand, the board, and pot odds.\n"
            f"{memory_section}"
            "You must output JSON only."
        )

        # Construct Game State Description
        state_desc = self._format_state(game_info)
        state_desc += f"\nYour Calculated Win Probability (Equity): {equity_percent}%"
        
        user_message = (
            f"Game State:\n{state_desc}\n\n"
            f"Valid Actions: {', '.join(valid_actions)}\n"
            "What is your move? Respond in JSON format with fields: 'action', 'amount' (optional if not raising), 'reasoning', 'chat'."
            "Example: {\"action\": \"call\", \"amount\": 0, \"reasoning\": \"Pot odds are good\", \"chat\": \"I call.\"}"
        )

        response = self.client.chat_completion(
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
        )
        
        # Check for error or fallback
        if "error" in response:
            # Fallback to check/call instead of always folding
            if "check" in valid_actions:
                return {"action": "check", "reasoning": "LLM Error - checking", "chat": "..."}
            elif "call" in valid_actions:
                return {"action": "call", "reasoning": "LLM Error - calling", "chat": "..."}
            return {"action": "fold", "reasoning": "LLM Error", "chat": "..."}

        # Validate action
        action = response.get("action", "").lower()
        if action not in valid_actions:
            # Simple correction: try to check if possible, then call, else fold
            if "check" in valid_actions:
                return {"action": "check", "reasoning": "Invalid action fallback"}
            elif "call" in valid_actions:
                return {"action": "call", "reasoning": "Invalid action fallback"}
            return {"action": "fold", "reasoning": "Invalid action fallback"}

        return response

    def _format_state(self, info: Dict[str, Any]) -> str:
        """
        Formats the game state dictionary into a readable definition for the LLM.
        """
        lines = []
        lines.append(f"My Hand: {info.get('my_hand')}")
        lines.append(f"Community Cards (Board): {info.get('board')}")
        lines.append(f"Game Stage: {info.get('stage', 'Unknown')}")
        lines.append(f"My Position: {info.get('position', 'Unknown')}")
        lines.append(f"Pot Size: {info.get('pot')}")
        lines.append(f"Current Bet to match: {info.get('current_bet')}")
        lines.append(f"Cost to Call: {info.get('to_call')}")
        lines.append(f"My Chips: {info.get('my_chips')}")
        lines.append(f"My Previous Bet: {info.get('my_bet')}")
        
        # Add pot odds info
        pot_odds = info.get('pot_odds', {})
        if pot_odds:
            lines.append(f"Pot Odds: {pot_odds.get('pot_odds_pct', 'N/A')} ({pot_odds.get('description', '')})")
        
        # Add history/players info if available
        if 'players' in info:
           lines.append(f"Other Players: {info['players']}")

        return "\n".join(lines)
