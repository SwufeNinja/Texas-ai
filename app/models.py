from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class Stage(str, Enum):
    PREFLOP = "PREFLOP"
    FLOP = "FLOP"
    TURN = "TURN"
    RIVER = "RIVER"
    SHOWDOWN = "SHOWDOWN"


class PlayerStatus(str, Enum):
    WAITING = "WAITING"
    PLAYING = "PLAYING"
    FOLDED = "FOLDED"
    ALLIN = "ALLIN"


@dataclass
class Player:
    id: str
    name: str
    is_ai: bool
    chips: int
    hand: List[str] = field(default_factory=list)
    status: PlayerStatus = PlayerStatus.WAITING
    bet: int = 0
    has_acted: bool = False
    ready: bool = False
    seated: bool = True

    def can_act(self) -> bool:
        return self.status == PlayerStatus.PLAYING

    def is_active(self) -> bool:
        return self.status in (PlayerStatus.PLAYING, PlayerStatus.ALLIN)


@dataclass
class Room:
    id: str
    players: List[Player]
    small_blind: int = 5
    big_blind: int = 10
    deck: List[str] = field(default_factory=list)
    community_cards: List[str] = field(default_factory=list)
    pot: int = 0
    dealer_index: int = 0
    current_actor_index: int = 0
    current_bet: int = 0
    last_raise_size: int = 0
    stage: Stage = Stage.PREFLOP
    winners: List[str] = field(default_factory=list)
    winning_hand: str = ""
    awaiting_ready: bool = False
