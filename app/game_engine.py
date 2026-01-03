from __future__ import annotations

import random
from typing import Iterable, List, Optional, Tuple

from .hand_eval import evaluate_best_hand
from .models import Player, PlayerStatus, Room, Stage


RANKS = "23456789TJQKA"
SUITS = "shdc"


class GameEngine:
    """
    Core logic engine for Texas Hold'em.
    
    Manages the state of a single room, including:
    - Deck management and dealing
    - Betting rounds (Preflop, Flop, Turn, River)
    - Action processing and validation
    - Pot calculation and side pots (basic implementation)
    - Showdown and winner determination
    """
    def __init__(self, room: Room, rng: Optional[random.Random] = None) -> None:
        self.room = room
        self.rng = rng or random.Random()

    def start_hand(self) -> None:
        """
        Initializes a new hand.
        
        Resets deck, pot, and community cards.
        Sets player statuses, posts blinds, and deals hole cards.
        """
        self._reset_deck()
        self.room.community_cards = []
        self.room.pot = 0
        self.room.stage = Stage.PREFLOP
        self.room.winners = []
        self.room.winning_hand = ""
        
        # Reset player state for valid players
        for player in self.room.players:
            player.bet = 0
            player.has_acted = False
            player.hand = []
            if player.seated and player.chips > 0 and player.ready:
                player.status = PlayerStatus.PLAYING
            else:
                player.status = PlayerStatus.WAITING

        active_indexes = [i for i, p in enumerate(self.room.players) if p.status == PlayerStatus.PLAYING]
        if len(active_indexes) < 2:
            raise ValueError("Need at least two active players to start a hand.")

        # Move dealer button
        self.room.dealer_index = self._next_active_index(self.room.dealer_index, include_start=True)
        sb_index = self._next_active_index(self.room.dealer_index)
        bb_index = self._next_active_index(sb_index)

        self._deal_hole_cards()

        # Post Blinds
        self.room.current_bet = 0
        self.room.last_raise_size = self.room.big_blind
        self._post_blind(sb_index, self.room.small_blind)
        self._post_blind(bb_index, self.room.big_blind)
        self.room.current_bet = self.room.big_blind

        # Set first actor (UTG)
        self.room.current_actor_index = self._next_active_index(bb_index)
        self._reset_has_acted(exclude_indexes={bb_index})

    def process_action(self, player_id: str, action: str, amount: int = 0) -> Tuple[bool, str]:
        """
        Processes a player's action.
        
        Args:
            player_id: The ID of the player acting.
            action: One of 'fold', 'check', 'call', 'raise', 'allin'.
            amount: The amount to raise (if applicable).
            
        Returns:
            Tuple[bool, str]: (Success, Message/Reason).
        """
        player = self._find_player(player_id)
        if player is None:
            return False, "unknown player"
        if self._current_player() is not player:
            return False, "not your turn"
        if not player.can_act():
            return False, "player cannot act"

        action = action.lower()
        if action == "fold":
            player.status = PlayerStatus.FOLDED
            player.has_acted = True
        elif action == "check":
            if player.bet != self.room.current_bet:
                return False, "cannot check when facing a bet"
            player.has_acted = True
        elif action == "call":
            to_call = self.room.current_bet - player.bet
            if to_call <= 0:
                return False, "nothing to call"
            self._commit_chips(player, min(to_call, player.chips))
            if player.chips == 0:
                player.status = PlayerStatus.ALLIN
            player.has_acted = True
        elif action == "raise":
            if amount <= 0:
                return False, "raise amount required"
            to_call = self.room.current_bet - player.bet
            min_raise = max(self.room.big_blind, self.room.last_raise_size)
            if amount < min_raise:
                return False, "raise below minimum"
            total = to_call + amount
            if total > player.chips:
                return False, "insufficient chips for raise"
            self._commit_chips(player, total)
            self.room.last_raise_size = amount
            self.room.current_bet = player.bet
            player.has_acted = True
            self._mark_others_pending(player)
        elif action == "allin":
            if player.chips <= 0:
                return False, "no chips to go all-in"
            to_call = self.room.current_bet - player.bet
            all_in_amount = player.chips
            self._commit_chips(player, all_in_amount)
            player.status = PlayerStatus.ALLIN
            
            # If all-in constitutes a raise, reopen betting
            if player.bet > self.room.current_bet:
                raise_amount = player.bet - self.room.current_bet
                min_raise = max(self.room.big_blind, self.room.last_raise_size)
                if raise_amount >= min_raise:
                    self.room.last_raise_size = raise_amount
                    self.room.current_bet = player.bet
                    self._mark_others_pending(player)
            player.has_acted = True
        else:
            return False, "unknown action"

        # Check for hand end (everyone folded or won)
        if self._hand_should_end():
            self.room.stage = Stage.SHOWDOWN
            self._resolve_showdown()
            return True, "hand ended"

        # Check if everyone is all-in or folded except one checks/calls
        if self._no_players_can_act():
            self._deal_remaining_community()
            self.room.stage = Stage.SHOWDOWN
            self._resolve_showdown()
            return True, "hand ended"

        # Check if round is complete (everyone matched bet or folded)
        if self._round_complete():
            self._advance_stage()
            if self.room.stage == Stage.SHOWDOWN:
                self._resolve_showdown()
            return True, "stage advanced"

        # Next player
        self.room.current_actor_index = self._next_active_index(self.room.current_actor_index)
        return True, "action applied"

    def action_error_details(
        self,
        player_id: str,
        action: str,
        amount: int,
        reason: str,
    ) -> dict:
        """Returns detailed context for why an action failed, for UI/Debug."""
        player = self._find_player(player_id)
        details: dict = {}
        if player is None:
            return {"player_id": player_id}

        to_call = max(0, self.room.current_bet - player.bet)
        min_raise = max(self.room.big_blind, self.room.last_raise_size)
        max_raise = max(0, player.chips - to_call)

        details = {
            "player_id": player.id,
            "player_chips": player.chips,
            "player_bet": player.bet,
            "current_bet": self.room.current_bet,
        }

        if reason == "raise below minimum":
            details.update({"min_raise": min_raise, "raise_amount": amount})
        elif reason == "cannot check when facing a bet":
            details.update({"to_call": to_call})
        elif reason == "insufficient chips for raise":
            details.update(
                {
                    "to_call": to_call,
                    "raise_amount": amount,
                    "total_needed": to_call + max(0, amount),
                    "max_raise": max_raise,
                }
            )
        elif reason == "nothing to call":
            details.update({"to_call": 0})
        elif reason == "raise amount required":
            details.update({"min_raise": min_raise})
        elif reason == "no chips to go all-in":
            details.update({})
        elif reason == "not your turn":
            details.update({"current_player_id": self._current_player().id})
        elif reason == "player cannot act":
            details.update({"status": player.status.value})
        elif reason == "unknown action":
            details.update({"action": action})
        return details

    def state_snapshot(self, viewer_id: Optional[str] = None) -> dict:
        """Returns a serializeable snapshot of the current game state from a player's perspective."""
        reveal_all = self.room.stage == Stage.SHOWDOWN
        return {
            "stage": self.room.stage.value,
            "pot": self.room.pot,
            "community_cards": list(self.room.community_cards),
            "current_bet": self.room.current_bet,
            "big_blind": self.room.big_blind,
            "last_raise_size": self.room.last_raise_size,
            "current_player_id": self._current_player().id,
            "awaiting_ready": self.room.awaiting_ready,
            "winners": list(self.room.winners),
            "winning_hand": self.room.winning_hand,
            "players": [
                {
                    "id": p.id,
                    "name": p.name,
                    "is_ai": p.is_ai,
                    "chips": p.chips,
                    "bet": p.bet,
                    "status": p.status.value,
                    # Hide opponents' cards unless showdown
                    "hand": list(p.hand) if (reveal_all or p.id == viewer_id) else [],
                    "ready": p.ready,
                    "seated": p.seated,
                }
                for p in self.room.players
            ],
        }

    def legal_actions(self, player_id: str) -> dict:
        """Returns a dictionary of legal actions and constraints for a player."""
        player = self._find_player(player_id)
        if player is None:
            return {}
        if self._current_player() is not player or not player.can_act():
            return {}
        to_call = max(0, self.room.current_bet - player.bet)
        min_raise = max(self.room.big_blind, self.room.last_raise_size)
        max_raise = max(0, player.chips - to_call)
        return {
            "fold": True,
            "check": player.bet == self.room.current_bet,
            "call": to_call if to_call > 0 else 0,
            "raise": {"min": min_raise, "max": max_raise} if max_raise >= min_raise else None,
            "allin": player.chips > 0,
        }

    def _reset_deck(self) -> None:
        self.room.deck = [f"{r}{s}" for r in RANKS for s in SUITS]
        self.rng.shuffle(self.room.deck)

    def _deal_hole_cards(self) -> None:
        for _ in range(2):
            for player in self.room.players:
                if player.status == PlayerStatus.PLAYING:
                    player.hand.append(self.room.deck.pop())

    def _post_blind(self, player_index: int, blind_amount: int) -> None:
        player = self.room.players[player_index]
        commit = min(player.chips, blind_amount)
        self._commit_chips(player, commit)
        if player.chips == 0:
            player.status = PlayerStatus.ALLIN

    def _commit_chips(self, player: Player, amount: int) -> None:
        player.chips -= amount
        player.bet += amount
        self.room.pot += amount

    def _find_player(self, player_id: str) -> Optional[Player]:
        for player in self.room.players:
            if player.id == player_id:
                return player
        return None

    def _current_player(self) -> Player:
        return self.room.players[self.room.current_actor_index]

    def _next_active_index(self, start_index: int, include_start: bool = False) -> int:
        count = len(self.room.players)
        for offset in range(count):
            idx = (start_index + offset) % count
            if offset == 0 and not include_start:
                continue
            if self.room.players[idx].can_act():
                return idx
        raise ValueError("No active players available for action.")

    def _mark_others_pending(self, raiser: Player) -> None:
        for player in self.room.players:
            if player is raiser:
                continue
            if player.can_act():
                player.has_acted = False

    def _round_complete(self) -> bool:
        """Checks if the current betting round is complete."""
        for player in self.room.players:
            if not player.is_active():
                continue
            if player.status == PlayerStatus.ALLIN:
                continue
            if not player.has_acted:
                return False
            if player.bet != self.room.current_bet:
                return False
        return True

    def _hand_should_end(self) -> bool:
        """Checks if only one player remains (others folded)."""
        active = [p for p in self.room.players if p.status in (PlayerStatus.PLAYING, PlayerStatus.ALLIN)]
        return len(active) <= 1

    def _no_players_can_act(self) -> bool:
        """Checks if further action is impossible (e.g., all-ins)."""
        return all(
            p.status in (PlayerStatus.FOLDED, PlayerStatus.ALLIN)
            for p in self.room.players
        )

    def _advance_stage(self) -> None:
        """Moves game to the next stage (Flop, Turn, River, Showdown)."""
        if self.room.stage == Stage.PREFLOP:
            self._burn_and_deal(3)
            self.room.stage = Stage.FLOP
        elif self.room.stage == Stage.FLOP:
            self._burn_and_deal(1)
            self.room.stage = Stage.TURN
        elif self.room.stage == Stage.TURN:
            self._burn_and_deal(1)
            self.room.stage = Stage.RIVER
        elif self.room.stage == Stage.RIVER:
            self.room.stage = Stage.SHOWDOWN
        else:
            return

        self._reset_round_state()
        self.room.current_actor_index = self._first_postflop_actor()

        # Handle case where everyone is all-in immediately after stage change
        # This will be caught by next process_action call or main loop, 
        # but pure engine state update is sufficient here.

    def _burn_and_deal(self, count: int) -> None:
        if self.room.deck:
            self.room.deck.pop() # Burn
        for _ in range(count):
            if self.room.deck:
                self.room.community_cards.append(self.room.deck.pop())

    def _deal_remaining_community(self) -> None:
        """Deals remaining cards if hand ends early (e.g. all-in showdown)."""
        while len(self.room.community_cards) < 5:
            if len(self.room.community_cards) == 0:
                self._burn_and_deal(3)
            else:
                self._burn_and_deal(1)

    def _reset_round_state(self) -> None:
        """Resets bets and acting status for a new round."""
        self.room.current_bet = 0
        self.room.last_raise_size = self.room.big_blind
        for player in self.room.players:
            player.bet = 0
            if player.status == PlayerStatus.PLAYING:
                player.has_acted = False

    def _first_postflop_actor(self) -> int:
        """Finds the first player to act post-flop (SB or next active)."""
        return self._next_active_index(self._small_blind_index())

    def _small_blind_index(self) -> int:
        return self._next_active_index(self.room.dealer_index)

    def _reset_has_acted(self, exclude_indexes: Optional[Iterable[int]] = None) -> None:
        exclude = set(exclude_indexes or [])
        for idx, player in enumerate(self.room.players):
            if idx in exclude:
                continue
            if player.status == PlayerStatus.PLAYING:
                player.has_acted = False

    def _resolve_showdown(self) -> None:
        """
        Determines the winner(s) and distributes the pot.
        
        Currently handles simple main pot distribution.
        Split pots are supported.
        Side pots are NOT fully supported yet (logic follows main pot).
        """
        contenders = [
            p for p in self.room.players
            if p.status in (PlayerStatus.PLAYING, PlayerStatus.ALLIN)
        ]
        if not contenders:
            return
        
        # If everyone else folded
        if len(contenders) == 1:
            winner = contenders[0]
            winner.chips += self.room.pot
            self.room.winners = [winner.id]
            self.room.winning_hand = "uncontested"
            self.room.pot = 0
            return

        # Showdown evaluation
        best_score = None
        winners = []
        for player in contenders:
            score = evaluate_best_hand(player.hand + self.room.community_cards)
            if best_score is None or score > best_score:
                best_score = score
                winners = [player]
            elif score == best_score:
                winners.append(player)

        if best_score:
            self.room.winning_hand = best_score[2]
            
        if winners:
            share = self.room.pot // len(winners)
            remainder = self.room.pot % len(winners)
            for idx, winner in enumerate(winners):
                # Distribute remainder to first players (simplification)
                winner.chips += share + (1 if idx < remainder else 0)
            self.room.winners = [p.id for p in winners]
            self.room.pot = 0
