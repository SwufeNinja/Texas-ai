import sys
import os
import time
from typing import List, Dict

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game.engine import TexasHoldemGame
from game.models import Player, PlayerState
from ai.agent import PokerAgent
from ui.cli import GameCLI

def get_agent_for_player(player: Player, agents: Dict[str, PokerAgent]) -> PokerAgent:
    return agents.get(player.name)  # pyright: ignore[reportReturnType]

def run_betting_round(game: TexasHoldemGame, cli: GameCLI, agents: Dict[str, PokerAgent], human: Player):
    """
    Executes a single betting round (Preflop, Flop, Turn, or River).
    Continues until all active players have matched the current bet or folded/all-in.
    """
    # Simply keep rotating until settlement. 
    # A round ends when: All players have acted at least once AND (folded OR all-in OR bet == current_bet)
    
    # Track who has acted this round
    has_acted = {p.name: False for p in game.players if p.status == PlayerState.ACTIVE}
    
    # Start loop
    # Determine playing order: standard is usually SB -> BB -> UTG.
    # But simplified: just iterate index from dealer+1, wrap around.
    
    start_index = (game.dealer_index + 1) % len(game.players)
    active_indices = []
    for i in range(len(game.players)):
        idx = (start_index + i) % len(game.players)
        p = game.players[idx]
        if p.status == PlayerState.ACTIVE:
            active_indices.append(idx)
            
    if not active_indices:
        return

    # To simplify infinite loop check:
    # We continue while there is any active player who:
    # 1. Has not acted yet
    # 2. OR current_bet is < game.current_bet (needs to call)
    
    unfinished = True
    while unfinished:
        unfinished = False
        
        # Iterate through players in order
        # Need to re-evaluate order dynamic if we want true poker structure, but simplified simple loop is okay if we restart loop on raise?
        # A common simple way: Cycle through players. If anyone raises, everyone else must act again.
        
        made_raise = False
        
        for idx in range(len(game.players)):
            p_idx = (start_index + idx) % len(game.players)
            player = game.players[p_idx]
            
            if player.status != PlayerState.ACTIVE:
                continue
            
            # Condition to act:
            # 1. Has not acted yet
            # 2. OR player.current_bet < game.current_bet
            if has_acted[player.name] and player.current_bet == game.current_bet:
                continue
                
            # It's this player's turn
            cli.render_state(game, human)
            print(f">>> {player.name}'s turn...")
            time.sleep(1) # small pause
            
            valid_actions = game.get_legal_actions(player)
            
            action = None
            amount = 0
            
            if player == human:
                # Prompt Human
                action = cli.get_action(valid_actions)
                if action == "raise":
                    min_raise = game.current_bet + game.big_blind
                    amount_input = cli.get_amount(min_raise, player.chips + player.current_bet) 
                    # Logic in engine for raise amount is "ADD info"? No, engine says "amount to add"? 
                    # Engine process_action: 
                    #   if raise: total_cost = call_amount + amount
                    #   meaning 'amount' is the EXTRA on top of matching.
                    #   Let's adjust.
                    
                    # If I input 100 total bet.
                    # call_amount = game.current_bet - player.current_bet
                    # amount_to_add = input_amount - (player.current_bet + call_amount) -> input_amount - game.current_bet
                    
                    amount_to_add = amount_input - game.current_bet
                    if amount_to_add <= 0:
                        print("Raise must be greater than current bet.")
                        action = "call" # fallback
                    else:
                        amount = amount_to_add
            else:
                # Prompt AI
                agent = get_agent_for_player(player, agents)
                
                # construct game_info
                game_info = {
                    "my_hand": [c.to_treys_str() for c in player.hand],
                    "board": [c.to_treys_str() for c in game.board],
                    "pot": game.pot,
                    "current_bet": game.current_bet,
                    "to_call": game.current_bet - player.current_bet,
                    "my_chips": player.chips,
                    "my_bet": player.current_bet,
                    "players": [str(p) for p in game.players]
                }
                
                decision = agent.get_action(game_info, valid_actions)
                action = decision.get("action", "fold")
                if action == "raise":
                    # AI usually returns simple stuff. 
                    # For MVP let's assume AI raises fixed amount (BB) or what it says
                    try:
                        amt = int(decision.get("amount", 0))
                    except:
                        amt = game.big_blind
                    amount = max(amt, game.big_blind) # Ensure min raise
                
                print(f"AI {player.name}: {action} {decision.get('chat', '')}")
                time.sleep(1)

            # Execution
            try:
                game.process_action(player, action, amount)
                has_acted[player.name] = True
                
                if action == "raise":
                    # Reset others has_acted status if raise happens?
                    # Yes, everyone else must act again if they haven't matched
                    for other_name in has_acted:
                        if other_name != player.name:
                            # If they are still active, they might need to call
                            # But technically if they already acted and now bet is higher, loop condition `player.current_bet < game.current_bet` handles it.
                            # We just need to ensure loop continues.
                            made_raise = True
            except Exception as e:
                print(f"Error processing action: {e}")
                # Loop safety? 
                
        # Check if we are done
        # Done if all active players have acts=True AND bets match
        all_done = True
        for p in game.players:
            if p.status == PlayerState.ACTIVE:
                if not has_acted[p.name] or p.current_bet != game.current_bet:
                    all_done = False
                    break
        
        if all_done:
            unfinished = False
        
        # Safety break for infinite loops in MVP
        # pass

def main():
    game = TexasHoldemGame()
    cli = GameCLI()
    cli.print_welcome()
    
    # Setup Players
    human_name = cli.console.input("Enter your name: ")
    human = Player(human_name, chips=1000)
    game.add_player(human)
    
    # Add AI
    ai_count = 3
    agents = {}
    names = ["Alice", "Bob", "Charlie", "David"]
    profiles = [
        "Conservative. Folds weak hands.",
        "Aggressive. Bluffs often.",
        "Mathematical. Calculates odds.",
        "Wild. Unpredictable."
    ]
    
    for i in range(ai_count):
        p_name = names[i]
        p = Player(p_name, is_ai=True, chips=1000)
        game.add_player(p)
        agents[p_name] = PokerAgent(p_name, profile=profiles[i])
        
    # Game Loop
    running = True
    while running:
        game.start_hand()
        
        # Helper to check if we should proceed (at least 2 players still with cards)
        def players_in_hand():
            return len([p for p in game.players if p.status in [PlayerState.ACTIVE, PlayerState.ALL_IN]]) >= 2

        # PRE-FLOP
        cli.render_state(game, human)
        print("\n--- PRE-FLOP ---")
        run_betting_round(game, cli, agents, human)
        
        # FLOP
        if players_in_hand():
            game.deal_community_cards(3)
            cli.render_state(game, human)
            print("\n--- FLOP ---")
            run_betting_round(game, cli, agents, human)
            
        # TURN
        if players_in_hand():
            game.deal_community_cards(1)
            cli.render_state(game, human)
            print("\n--- TURN ---")
            run_betting_round(game, cli, agents, human)
            
        # RIVER
        if players_in_hand():
            game.deal_community_cards(1)
            cli.render_state(game, human)
            print("\n--- RIVER ---")
            run_betting_round(game, cli, agents, human)
            
        # SHOWDOWN
        print("\n--- SHOWDOWN ---")
        # Ensure all community cards are dealt if we reached showdown with all-in players?
        # If players_in_hand() is true but we skipped rounds because everyone was all-in?
        # My logic above: run_betting_round returns early if no ACTIVE players. 
        # But we still dealt cards.
        # So if P1, P2 all in pre-flop:
        # 1. Pre-flop round ends.
        # 2. players_in_hand() is True. Deal 3.
        # 3. run_betting_round -> returns imm.
        # 4. Deal 1.
        # 5. run_betting_round -> returns imm.
        # 6. Deal 1.
        # 7. run_betting_round -> returns imm.
        # 8. Showdown.
        # Logic is correct.
        
        cli.render_state(game, human) 
        winners = game.determine_winners()
        
        if winners:
            winner_names = [w.name for w in winners]
            print(f"[bold green]Winner(s): {', '.join(winner_names)}[/bold green]")
            # Distribute pot
            share = game.pot // len(winners)
            for w in winners:
                w.chips += share
                print(f"{w.name} wins {share} chips!")
        else:
            print("No winners? (Everyone folded maybe)")
            
        game.dealer_index = (game.dealer_index + 1) % len(game.players)
        
        # Check if human busted
        if human.chips <= 0:
            print("You are busted! Game Over.")
            break
            
        action = cli.console.input("\nPlay another round? (y/n): ")
        if action.lower() != 'y':
            running = False

if __name__ == "__main__":
    main()
