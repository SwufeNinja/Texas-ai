import random
from typing import List, Tuple
from .models import Card, Deck, Suit, Rank
from .evaluator import HandEvaluator

class EquityCalculator:
    def __init__(self):
        self.evaluator = HandEvaluator()
        self.deck = Deck()

    def calculate_equity(self, my_hand: List[str], board: List[str], num_active_players: int = 2, simulations: int = 500) -> float:
        """
        Calculates the equity (win probability) of a hand using Monte Carlo simulation.
        
        Args:
            my_hand: List of 2 card strings (e.g., ['Ah', 'Kd'])
            board: List of board card strings (e.g., ['2s', '5d', '9c'])
            num_active_players: Number of players still in the hand (including self)
            simulations: Number of random deals to simulate
            
        Returns:
            Float between 0.0 and 1.0 representing win probability.
        """
        if num_active_players < 2:
            return 1.0
            
        wins = 0
        ties = 0
        
        # Build base deck once - filter out known cards
        # Convert known cards to treys format for consistent comparison
        known_cards_strs = set(my_hand + board)
        self.deck.reset()
        # Use to_treys_str() for filtering and dealing to match input format (e.g., 'Ah', not 'A♥')
        base_deck = [c for c in self.deck.cards if c.to_treys_str() not in known_cards_strs]
        
        # Pre-calculate cards needed
        cards_needed_opponent = (num_active_players - 1) * 2
        cards_needed_board = 5 - len(board)
        total_cards_needed = cards_needed_opponent + cards_needed_board
        
        if len(base_deck) < total_cards_needed:
            # Should not happen in normal poker
            return 0.5

        for _ in range(simulations):
            # Shuffle a copy of the filtered deck (more efficient than resetting)
            simulation_deck = base_deck.copy()
            random.shuffle(simulation_deck)
                 
            # Deal Opponents - use to_treys_str() for consistent format
            opponents_hands = []
            for _ in range(num_active_players - 1):
                op_hand = [simulation_deck.pop().to_treys_str(), simulation_deck.pop().to_treys_str()]
                opponents_hands.append(op_hand)
                
            # Deal Board
            sim_board_cards = []
            for _ in range(cards_needed_board):
                sim_board_cards.append(simulation_deck.pop().to_treys_str())
                
            final_board = board + sim_board_cards
            
            # Evaluate using Treys (expects strings)
            # Evaluator returns score (Lower is better)
            my_score = self.evaluator.evaluate(my_hand, final_board)
            
            best_opponent_score = float('inf')
            for op_h in opponents_hands:
                s = self.evaluator.evaluate(op_h, final_board)
                if s < best_opponent_score:
                    best_opponent_score = s
            
            if my_score < best_opponent_score:
                wins += 1
            elif my_score == best_opponent_score:
                ties += 1
                
        # Equity = Win% + (Tie% / 2) ? 
        # Actually in multi-way tie, it's 1/N. But 1/2 is decent approx for AI logic.
        return (wins + ties * 0.5) / simulations
