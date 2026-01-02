from typing import List, Dict, Any
import json
import logging
from .llm_client import LLMClient

class PokerAgent:
    def __init__(self, name: str, profile: str = "A professional poker player", client: LLMClient = None): # type: ignore
        self.name = name
        self.profile = profile
        self.client = client if client else LLMClient()
        self.memories: List[str] = []

    def add_memory(self, event: str):
        """Adds a memory of a past hand/event."""
        self.memories.append(event)
        # Keep last 10 memories to fit in context
        if len(self.memories) > 10:
            self.memories.pop(0)

    def get_action(self, game_info: Dict[str, Any], valid_actions: List[str]) -> Dict[str, Any]:
        """
        Decides an action based on game state using LLM reasoning.
        Returns dict like: {"action": "raise", "amount": 10, "chat": "..."}
        """
        if not valid_actions:
            return {"action": "fold", "reasoning": "No valid actions"}

        memory_str = "\n".join([f"- {m}" for m in self.memories])
        if memory_str:
            memory_section = f"\nRecent History:\n{memory_str}\n"
        else:
            memory_section = ""

        # Enhanced System Message
        system_message = (
            f"You are {self.name}, playing Texas Hold'em. {self.profile}\n"
            "Your goal is to win chips over the long run. "
            "You must make decisions by Analyzing the following factors yourself:\n"
            "1. **Hand Strength**: How strong is your hand? (e.g., Pair, Set, Flush Draw)\n"
            "2. **Board Texture**: Is the board wet (many draws) or dry?\n"
            "3. **Position**: Are you late position (BTN, CO) or early?\n"
            "4. **Pot Odds**: Are the odds favorable for a call?\n"
            "5. **Opponent Actions**: Did they show strength (raise) or weakness (check)?\n\n"
            f"{memory_section}"
            "You must output JSON only."
        )

        # Construct Game State Description
        state_desc = self._format_state(game_info)
        
        user_message = (
            f"Game State:\n{state_desc}\n\n"
            f"Valid Actions: {', '.join(valid_actions)}\n"
            "Analyze the situation and decide your move. Respond in JSON format with fields: "
            "'action', 'amount' (optional if not raising), 'reasoning', 'chat'.\n"
            "Example: {\"action\": \"call\", \"amount\": 0, \"reasoning\": \"Pot odds are good with a flush draw\", \"chat\": \"I'm staying in.\"}"
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
                return {"action": "check", "reasoning": "LLM Error - checking", "chat": "Hmm..."}
            elif "call" in valid_actions:
                return {"action": "call", "reasoning": "LLM Error - calling", "chat": "I call."}
            return {"action": "fold", "reasoning": "LLM Error", "chat": "I fold."}

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
        lines.append(f"Community Cards: {info.get('board')}")
        lines.append(f"Game Stage: {info.get('stage', 'Unknown')}")
        lines.append(f"My Position: {info.get('position', 'Unknown')}")
        lines.append(f"Pot Size: {info.get('pot')}")
        lines.append(f"My Chips: {info.get('my_chips')}")
        lines.append(f"Current Bet to Match: {info.get('to_call')}")
        lines.append(f"My Current Round Bet: {info.get('my_bet')}")
        
        # Add pot odds info if available
        pot_odds = info.get('pot_odds', {})
        if pot_odds:
            # If it's a dict, format it nicely
            if isinstance(pot_odds, dict):
                 pct = pot_odds.get('pot_odds_pct', 'N/A')
                 desc = pot_odds.get('description', '')
                 lines.append(f"Pot Odds: {pct} ({desc})")
            else:
                 lines.append(f"Pot Odds: {pot_odds}")
        
        # Add history/players info if available
        if 'players' in info:
           lines.append(f"Table Summary: {info['players']}")
        
        lines.append(f"Active Players Count: {info.get('num_active_players', 'Unknown')}")

        return "\n".join(lines)
