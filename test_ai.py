import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'texas-holdem-ai'))

from ai.agent import PokerAgent
from ai.llm_client import LLMClient
from unittest.mock import MagicMock

def test_ai_agent():
    # Mock LLM Client
    mock_client = MagicMock(spec=LLMClient)
    # Return a dummy response when chat_completion is called
    mock_client.chat_completion.return_value = {
        "action": "call",
        "amount": 10,
        "reasoning": "I have a pair",
        "chat": "Let's see the flop"
    }

    agent = PokerAgent(name="Bot1", client=mock_client)
    
    game_state = {
        "my_hand": ["Ah", "Kd"],
        "board": ["Th", "Jh", "Qc"],
        "pot": 100,
        "current_bet": 20,
        "to_call": 10,
        "my_chips": 500,
        "my_bet": 10
    }
    
    valid_actions = ["fold", "call", "raise"]
    
    print("Asking Agent for decision...")
    decision = agent.get_action(game_state, valid_actions)
    
    print(f"Decision: {decision}")
    
    if decision['action'] == 'call':
        print("TEST PASSED: Agent called as expected.")
    else:
        print("TEST FAILED: Agent did not call.")

if __name__ == "__main__":
    test_ai_agent()
