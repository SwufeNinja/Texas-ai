import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'texas-holdem-ai'))

from game.engine import TexasHoldemGame
from game.models import Player, PlayerState

def test_game_flow():
    game = TexasHoldemGame()
    p1 = Player("Alice", chips=100)
    p2 = Player("Bob", chips=100)
    
    game.add_player(p1)
    game.add_player(p2)
    
    print("Starting Hand...")
    game.start_hand()
    
    print(f"Board: {game.board}") # Should be empty
    print(f"Bob Hand: {p2.hand}")
    print(f"Alice Hand: {p1.hand}")
    print(f"Pot: {game.pot}")
    
    # Pre-flop
    print("\n--- Pre-Flop ---")
    current_actor = p1 # Alice is SB (if dealer is 0) -> Wait. 
    # dealer=0 (Alice). SB=Bob, BB=Alice? 
    # Logic in engine: 
    # sb_idx = (dealer + 1) % 2 -> 1 (Bob)
    # bb_idx = (dealer + 2) % 2 -> 0 (Alice)
    # So Bob is SB, Alice is BB.
    
    print(f"Bob chips: {p2.chips} (Bet: {p2.current_bet})")
    print(f"Alice chips: {p1.chips} (Bet: {p1.current_bet})")
    
    # Bob calls
    print("Bob calls...")
    game.process_action(p2, "call")
    print(f"Pot: {game.pot}")
    
    # Alice checks
    print("Alice checks...")
    game.process_action(p1, "check")
    
    # Flop
    print("\n--- Flop ---")
    game.deal_community_cards(3)
    print(f"Board: {game.board}")
    
    # Check winners just to test evaluator
    print("\n--- Showdown (Early) ---")
    winners = game.determine_winners()
    for w in winners:
        print(f"Winner: {w.name}")

if __name__ == "__main__":
    test_game_flow()
