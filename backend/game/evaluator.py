from treys import Evaluator as TreysEvaluator
from treys import Card as TreysCard
from .models import Card
from typing import List, Tuple

class HandEvaluator:
    def __init__(self):
        self._evaluator = TreysEvaluator()

    def evaluate(self, hand: List[Card | str], board: List[Card | str]) -> int:
        """
        Evaluate the strength of a hand given the board.
        Returns a score (lower is better, range 1-7462).
        """
        if len(hand) != 2:
            raise ValueError("Hand must have exactly 2 cards")
        
        # Helper to convert to treys int
        def to_treys(c):
            if isinstance(c, str):
                # Handle symbols if present
                replacements = {'♠': 's', '♥': 'h', '♦': 'd', '♣': 'c'}
                clean_c = c
                for sym, char in replacements.items():
                    clean_c = clean_c.replace(sym, char)
                return TreysCard.new(clean_c)
            return TreysCard.new(c.to_treys_str())

        t_hand = [to_treys(c) for c in hand]
        t_board = [to_treys(c) for c in board]
        
        # Treys evaluate method needs board and hand
        return self._evaluator.evaluate(t_board, t_hand)

    def get_rank_name(self, score: int) -> str:
        """
        Convert score to string like 'Full House', 'Pair' etc.
        """
        rank_class = self._evaluator.get_rank_class(score)
        return self._evaluator.class_to_string(rank_class)
