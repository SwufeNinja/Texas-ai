import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game.equity import EquityCalculator
from game.models import Card, Suit, Rank

def test_equity_fix():
    print("Testing Equity Calculator with fix...")
    
    eq = EquityCalculator()
    
    # Case 1: Strings (what AI Agent passes)
    my_hand = ["A♥", "K♦"]
    board = ["2♠", "5♦", "9♣"]
    
    try:
        equity = eq.calculate_equity(my_hand, board, num_active_players=2, simulations=100)
        print(f"✅ Symbol String input equity: {equity}")
    except Exception as e:
        print(f"❌ Symbol String input failed: {e}")
        
    # Case 2: Ensure existing engine calls (using Card objects) still work if they use this evaluator? 
    # Actually Engine uses Evaluator directly, not EquityCalculator. 
    # But let's verify Evaluator accepts Card objects too.
    from game.evaluator import HandEvaluator
    ev = HandEvaluator()
    c1 = Card(Rank.ACE, Suit.HEARTS)
    c2 = Card(Rank.KING, Suit.DIAMONDS)
    # evaluator.evaluate expects list of Card or str
    # But check Engine usage: engine passes [Card, Card]
    
    try:
        # We need 3 board cards for treys
        score = ev.evaluate([c1, c2], ["2s", "5d", "9c"]) # Mixed? Engine passes Card objects for board too usually
        # But wait, my fix handles mixed? 
        # "t_board = [to_treys(c) for c in board]"
        # Yes.
        print(f"✅ Card object input score: {score}")
    except Exception as e:
        print(f"❌ Card object input failed: {e}")

if __name__ == "__main__":
    test_equity_fix()
