import random
from typing import List, Optional
from enum import Enum

class Suit(Enum):
    SPADES = '♠'
    HEARTS = '♥'
    DIAMONDS = '♦'
    CLUBS = '♣'

class Rank(Enum):
    TWO = '2'
    THREE = '3'
    FOUR = '4'
    FIVE = '5'
    SIX = '6'
    SEVEN = '7'
    EIGHT = '8'
    NINE = '9'
    TEN = 'T'
    JACK = 'J'
    QUEEN = 'Q'
    KING = 'K'
    ACE = 'A'

class Card:
    def __init__(self, rank: Rank, suit: Suit):
        self.rank = rank
        self.suit = suit

    def __str__(self):
        return f"{self.rank.value}{self.suit.value}"

    def __repr__(self):
        return self.__str__()
    
    def to_treys_str(self):
        # treys expects 'Ah', '2d', 'Ts' etc.
        # suits: s, h, d, c
        s_map = {Suit.SPADES: 's', Suit.HEARTS: 'h', Suit.DIAMONDS: 'd', Suit.CLUBS: 'c'}
        return f"{self.rank.value}{s_map[self.suit]}"

class Deck:
    def __init__(self):
        self.cards: List[Card] = []
        self.reset()

    def reset(self):
        self.cards = [Card(rank, suit) for suit in Suit for rank in Rank]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, n: int = 1) -> List[Card]:
        if len(self.cards) < n:
            raise ValueError("Not enough cards in deck")
        return [self.cards.pop() for _ in range(n)]

class PlayerState(Enum):
    ACTIVE = "active"
    FOLDED = "folded"
    ALL_IN = "all_in"
    OUT = "out" # busted

class Player:
    def __init__(self, name: str, is_ai: bool = False, chips: int = 1000):
        self.name = name
        self.is_ai = is_ai
        self.chips = chips
        self.hand: List[Card] = []
        self.status = PlayerState.ACTIVE
        self.current_bet = 0 # Bet in the current round
        self.acted_in_round = False
        self.total_bet = 0  # Total chips committed this hand (used for pot/side-pot logic)

    def reset_for_round(self):
        self.hand = []
        self.status = PlayerState.ACTIVE if self.chips > 0 else PlayerState.OUT
        self.current_bet = 0
        self.acted_in_round = False
        self.total_bet = 0

    def __str__(self):
        status_str = ""
        if self.status != PlayerState.ACTIVE:
            status_str = f" [{self.status.value.upper()}]"
        
        return f"{self.name} (Chips: {self.chips}, Bet: {self.current_bet}{status_str})"
