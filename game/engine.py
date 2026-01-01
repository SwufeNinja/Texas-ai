from typing import List, Dict, Optional
from enum import Enum
from .models import Deck, Player, PlayerState, Card
from .evaluator import HandEvaluator

class GameStage(Enum):
    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3
    SHOWDOWN = 4
    GAME_OVER = 5

class TexasHoldemGame:
    def __init__(self, small_blind: int = 10, big_blind: int = 20):
        self.players: List[Player] = []
        self.deck = Deck()
        self.board: List[Card] = []
        self.pot = 0
        self.current_bet = 0
        self.dealer_index = 0
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.evaluator = HandEvaluator()
        
        # State Machine Attributes
        self.stage = GameStage.GAME_OVER
        self.current_player_index = 0 # Index in self.players
        self.aggressor_index = 0 # Who made the last raise (or BB start)
        self.round_bets_matched = False # If true, ready to deal next cards
        self.winners: List[Player] = []

    def add_player(self, player: Player):
        self.players.append(player)

    def start_hand(self):
        """Starts a new hand: shuffle, deal, blinds."""
        self.deck.reset()
        self.board = []
        self.pot = 0
        self.current_bet = 0
        self.stage = GameStage.PREFLOP
        self.winners = []
        
        # Reset players
        active_count = 0
        for p in self.players:
            if p.chips > 0:
                p.reset_for_round()
                active_count += 1
            else:
                p.status = PlayerState.OUT
        
        if active_count < 2:
            print("Not enough players.")
            return

        # Blinds - skip OUT players
        sb_idx = (self.dealer_index + 1) % len(self.players)
        while self.players[sb_idx].status == PlayerState.OUT:
            sb_idx = (sb_idx + 1) % len(self.players)
            if sb_idx == self.dealer_index:  # Safety: avoid infinite loop
                break
        
        bb_idx = (sb_idx + 1) % len(self.players)
        while self.players[bb_idx].status == PlayerState.OUT:
            bb_idx = (bb_idx + 1) % len(self.players)
            if bb_idx == sb_idx:  # Safety: avoid infinite loop
                break
        
        self.post_blind(self.players[sb_idx], self.small_blind)
        self.post_blind(self.players[bb_idx], self.big_blind)
        
        # Deal hole cards
        for _ in range(2):
            for p in self.players:
                if p.status == PlayerState.ACTIVE:
                    p.hand.append(self.deck.deal(1)[0])

        self.current_bet = self.big_blind
        
        # Current player is UTG (BB + 1)
        self.current_player_index = (bb_idx + 1) % len(self.players)
        self.aggressor_index = bb_idx # Last person who forced a bet amount
        self.round_bets_matched = False
        
        # Sanity check: Ensure current player is active
        self._ensure_active_current_player()

    # _ensure_active_current_player is defined later in the class (line ~248)

    def post_blind(self, player: Player, amount: int):
        actual_bet = min(player.chips, amount)
        player.chips -= actual_bet
        player.current_bet = actual_bet
        self.pot += actual_bet
        if player.chips == 0:
            player.status = PlayerState.ALL_IN

    def deal_community_cards(self, number: int):
        cards = self.deck.deal(number)
        self.board.extend(cards)

    def get_player_position(self, player: Player) -> str:
        """
        Returns the position name for a player (BTN, SB, BB, UTG, MP, CO, etc.)
        """
        player_idx = self.players.index(player)
        num_players = len([p for p in self.players if p.status != PlayerState.OUT])
        
        # Calculate relative position from dealer
        active_players = [p for p in self.players if p.status != PlayerState.OUT]
        if player not in active_players:
            return "OUT"
        
        active_idx = active_players.index(player)
        dealer_active_idx = 0
        for i, p in enumerate(active_players):
            if self.players.index(p) == self.dealer_index:
                dealer_active_idx = i
                break
        
        # Position relative to dealer (0 = dealer)
        rel_pos = (active_idx - dealer_active_idx) % num_players
        
        if num_players == 2:
            # Heads up: dealer is SB, other is BB
            return "SB/BTN" if rel_pos == 0 else "BB"
        
        position_names = {
            0: "BTN",   # Button/Dealer
            1: "SB",    # Small Blind
            2: "BB",    # Big Blind
        }
        
        if rel_pos in position_names:
            return position_names[rel_pos]
        
        # For other positions
        if num_players <= 6:
            if rel_pos == num_players - 1:
                return "CO"  # Cutoff
            return "MP"  # Middle Position
        else:
            if rel_pos == num_players - 1:
                return "CO"
            elif rel_pos == 3:
                return "UTG"
            elif rel_pos == 4:
                return "UTG+1"
            return "MP"

    def calculate_pot_odds(self, player: Player) -> dict:
        """
        Calculate pot odds for a player.
        Returns dict with pot_odds percentage and recommendation.
        """
        to_call = self.current_bet - player.current_bet
        
        if to_call <= 0:
            return {"to_call": 0, "pot_odds": 0, "pot_odds_pct": "0%", "description": "Free to check"}
        
        total_pot_after_call = self.pot + to_call
        pot_odds = to_call / total_pot_after_call
        pot_odds_pct = round(pot_odds * 100, 1)
        
        return {
            "to_call": to_call,
            "pot_odds": pot_odds,
            "pot_odds_pct": f"{pot_odds_pct}%",
            "description": f"Need {pot_odds_pct}% equity to call profitably"
        }


    def get_legal_actions(self, player: Player) -> List[str]:
        if player.status != PlayerState.ACTIVE:
            return []
        
        actions = ["fold"]
        call_amount = self.current_bet - player.current_bet
        
        if call_amount == 0:
            actions.append("check")
        else:
            if player.chips >= call_amount:
                actions.append("call")
            else:
                actions.append("all_in")
                
        if player.chips > call_amount:
            actions.append("raise")
            
        return actions

    def step(self, action: str, amount: int = 0):
        """
        Executes one step for the current player, then advances turn or stage.
        """
        player = self.players[self.current_player_index]
        self.process_action(player, action, amount)
        player.acted_in_round = True
        
        # If action was raise, update aggressor
        if action == "raise" or (action == "all_in" and player.current_bet > self.current_bet):
            self.aggressor_index = self.current_player_index
            self.current_bet = player.current_bet
            # Everyone else needs to act again (except all-in), so their acted_in_round might remain/reset?
            # Actually, standard logic: if someone raises, everyone else must match.
            # We can just reset acted_in_round for everyone ELSE?
            # Or just rely on the "bets match" check.
            # But the "has acted" check is needed for checking (Big Blind option etc).
            # Simplest: check if (bet < current_bet) OR (not acted).
            pass # logic in _advance_turn handles "bet < current"
            
        # Setup next turn
        self._advance_turn()
        
    def _advance_turn(self):
        """
        Move to next active player. Check if round is complete.
        """
        # 1. Check if only one player left with chips (others folded or busted previously)
        active_players = [p for p in self.players if p.status in [PlayerState.ACTIVE, PlayerState.ALL_IN]]
        not_folded = [p for p in self.players if p.status != PlayerState.FOLDED and p.status != PlayerState.OUT]
        
        if len(not_folded) == 1:
            # Everyone else folded
            self.stage = GameStage.SHOWDOWN # Or just end immediately
            self.determine_winners()
            self.stage = GameStage.GAME_OVER
            return

        # 2. Check if round is complete
        # Round is complete if: 
        # All ACTIVE players have acted AND their bets match current_bet (or they are all-in)
        
        active_indices = [i for i, p in enumerate(self.players) if p.status == PlayerState.ACTIVE]
        
        round_complete = True
        for i in active_indices:
            p = self.players[i]
            if not p.acted_in_round:
                round_complete = False
                break
            if p.current_bet != self.current_bet:
                round_complete = False
                break
        
        # Edge case: All-in players don't need to match current_bet if they can't (handled by status ALL_IN)
        # But we need to ensure their action was processed.

        if round_complete:
            self.next_stage()
            return

        # 3. If not complete, find next active player
        start = self.current_player_index
        next_idx = (self.current_player_index + 1) % len(self.players)
        
        while True:
            p = self.players[next_idx]
            if p.status == PlayerState.ACTIVE:
                self.current_player_index = next_idx
                break
            # If all others are all-in, we might loop forever if we strip logic?
            # active_indices covers logic. If round not complete, there MUST be an active player who needs to act.
            next_idx = (next_idx + 1) % len(self.players)
            if next_idx == start:
                # Should not happen if round_complete calculated correctly?
                # It can happen if everyone is All-In?
                # If everyone All-in, round_complete should be True (active_indices empty)
                break
    
    def next_stage(self):
        """Move to next stage (Preflop -> Flop -> Turn -> River -> Showdown)"""
        if self.stage == GameStage.PREFLOP:
            self.stage = GameStage.FLOP
            self.deal_community_cards(3)
        elif self.stage == GameStage.FLOP:
            self.stage = GameStage.TURN
            self.deal_community_cards(1)
        elif self.stage == GameStage.TURN:
            self.stage = GameStage.RIVER
            self.deal_community_cards(1)
        elif self.stage == GameStage.RIVER:
            self.stage = GameStage.SHOWDOWN
            self.determine_winners()
            self.stage = GameStage.GAME_OVER
            return # End
        
        # Prepare for new betting round
        self.current_bet = 0
        for p in self.players:
            p.current_bet = 0
            p.acted_in_round = False
            # Fix status if needed? Active remains active.
        
        # Dealer + 1 starts post-flop
        # Find first active player after dealer
        self.current_player_index = (self.dealer_index + 1) % len(self.players)
        self._ensure_active_current_player()
        
        # If everyone is All-In, we should auto-advance stages?
        # Check if >= 2 active players.
        active_count = len([p for p in self.players if p.status == PlayerState.ACTIVE])
        if active_count < 2:
            # Everyone else is All-in or Folded. 
            # We should just deal remaining cards and show down.
            # Auto-step recursively
            # But wait, we might want animation delay in UI.
            # For now, just let UI call 'next_stage' or handle it? 
            # Ideally the engine should handle "no actions left".
            pass # Keep it manual for now or Streamlit loop will handle "check" automatically? No.
            # If no active players, get_legal_actions returns empty? or we auto-call step?
            # Let's leave it. UI will see no legal actions -> verify logic.
            
    def _ensure_active_current_player(self):
        """Rotates current_player_index until it hits an active player (or circles back)."""
        start = self.current_player_index
        count = 0
        while self.players[self.current_player_index].status != PlayerState.ACTIVE:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            count += 1
            if count > len(self.players):
                # Everyone is All-In or Folded
                break

    def process_action(self, player: Player, action: str, amount: int = 0):
        """
        Process a player's action. 
        """
        if action == "fold":
            player.status = PlayerState.FOLDED
        elif action == "check":
            pass 
        elif action == "call":
            call_amount = self.current_bet - player.current_bet
            actual_call = min(player.chips, call_amount)
            player.chips -= actual_call
            player.current_bet += actual_call
            self.pot += actual_call
            if player.chips == 0:
                player.status = PlayerState.ALL_IN
        elif action == "raise":
            call_amount = self.current_bet - player.current_bet
            total_cost = call_amount + amount
            if total_cost > player.chips:
                # Correct to all-in raise? Or error?
                # Assume valid input for now or clamp
                total_cost = player.chips
                
            player.chips -= total_cost
            player.current_bet += total_cost
            self.pot += total_cost
            if player.current_bet > self.current_bet:
                self.current_bet = player.current_bet
            if player.chips == 0:
                player.status = PlayerState.ALL_IN
        elif action == "all_in":
             bet = player.chips
             player.chips = 0
             player.current_bet += bet
             self.pot += bet
             player.status = PlayerState.ALL_IN
             if player.current_bet > self.current_bet:
                 self.current_bet = player.current_bet

    def determine_winners(self) -> List[Player]:
        active_players = [p for p in self.players if p.status in [PlayerState.ACTIVE, PlayerState.ALL_IN]]
        if not active_players:
            return []
            
        # If only one player left (everyone else folded)
        # Note: This checks showdown strength. Fold logic usually handled before.
        if len(active_players) == 1:
            return active_players

        best_score = float('inf')
        winners = []
        
        for p in active_players:
            score = self.evaluator.evaluate(p.hand, self.board)
            if score < best_score:
                best_score = score
                winners = [p]
            elif score == best_score:
                winners.append(p)
                
        return winners
