import streamlit as st
import time
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game.engine import TexasHoldemGame, GameStage, PlayerState
from game.models import Player
from ai.agent import PokerAgent
from ui.card_svg import cards_to_html, generate_card_back_svg

# Page Config
st.set_page_config(page_title="Texas Hold'em AI", page_icon="♠️", layout="wide")

# Session State Initialization
if "game" not in st.session_state:
    st.session_state.game = TexasHoldemGame()
    # Add Human
    human = Player("Human", chips=1000)
    st.session_state.game.add_player(human)
    st.session_state.human_name = "Human" # Track which is human
    
    # Add AI
    ai_names = ["Alice", "Bob", "Charlie"]
    profiles = [
        "You are a tight-aggressive player. You only play strong hands but when you do, you bet and raise confidently. Consider pot odds before calling.",
        "You are a loose-aggressive player. You like to play many hands and apply pressure with bets. You occasionally bluff but also value bet strong hands.",
        "You are a balanced player who calculates pot odds and equity. You make mathematically sound decisions based on your win probability."
    ]
    st.session_state.agents = {}
    for i, name in enumerate(ai_names):
        p = Player(name, is_ai=True, chips=1000)
        st.session_state.game.add_player(p)
        st.session_state.agents[name] = PokerAgent(name, profile=profiles[i])
        
    st.session_state.game.start_hand()
    st.session_state.hand_recorded = False

game = st.session_state.game

# Sidebar
st.sidebar.title("🎰 Controls")
if st.sidebar.button("🔄 Restart Game"):
    # Reset game logic
    st.session_state.game = TexasHoldemGame()
    # Re-add human player
    human = Player("Human", chips=1000)
    st.session_state.game.add_player(human)
    st.session_state.human_name = "Human"
    
    # Re-add AI players with profiles (must match initial setup)
    ai_names = ["Alice", "Bob", "Charlie"]
    profiles = [
        "You are a tight-aggressive player. You only play strong hands but when you do, you bet and raise confidently. Consider pot odds before calling.",
        "You are a loose-aggressive player. You like to play many hands and apply pressure with bets. You occasionally bluff but also value bet strong hands.",
        "You are a balanced player who calculates pot odds and equity. You make mathematically sound decisions based on your win probability."
    ]
    st.session_state.agents = {}
    for i, name in enumerate(ai_names):
        p = Player(name, is_ai=True, chips=1000)
        st.session_state.game.add_player(p)
        st.session_state.agents[name] = PokerAgent(name, profile=profiles[i])
    
    st.session_state.game.start_hand()
    st.session_state.hand_recorded = False
    st.rerun()

# === LUXURY GOLD-BLACK THEME CSS ===
st.markdown("""
<style>
    /* Global Dark Theme */
    .stApp {
        background: linear-gradient(135deg, #0d0d1a 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    /* Compact Main Container */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 0.75rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Poker Table Container */
    .poker-table-container {
        position: relative;
        width: 100%;
        max-width: 800px;
        height: 360px;
        margin: 0 auto;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    /* Poker Table */
    .poker-table {
        width: 860px;
        height: 360px;
        background: radial-gradient(ellipse at center, #0d4a2e 0%, #073d1f 100%);
        border-radius: 180px;
        border: 8px solid #d4af37;
        box-shadow: 
            0 0 30px rgba(0, 0, 0, 0.5),
            inset 0 0 60px rgba(0, 0, 0, 0.5);
        position: relative;
        margin: 0 auto;
    }
    
    /* Pot Display - Now Floating inside Table */
    .pot-display {
        position: absolute;
        top: 18%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(212, 175, 55, 0.5);
        border-radius: 20px;
        padding: 5px 20px;
        text-align: center;
        z-index: 10;
        min-width: 140px;
    }
    
    .pot-display h2 {
        color: #ffd700;
        font-family: 'Georgia', serif;
        margin: 0;
        font-size: 1.1em;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
    }
    
    .pot-display p {
        color: #ddd;
        margin: 0;
        font-size: 0.7em;
        letter-spacing: 1px;
    }
    
    /* Community Cards - Now Floating inside Table */
    .community-cards {
        position: absolute;
        top: 58%;
        left: 50%;
        transform: translate(-50%, -50%);
        display: flex;
        gap: 5px;
        padding: 5px;
        background: transparent;
        border: none;
        z-index: 10;
    }
    
    /* Player Card Styles */
    .player-seat {
        background: linear-gradient(145deg, #1a1a2e, #16213e);
        border: 1px solid #d4af37;
        border-radius: 12px; /* More rectangular */
        padding: 5px 8px; /* More compact */
        min-width: 160px;
        max-width: 160px;
        height: 200px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5);
        transition: all 0.3s ease;
        margin: 5px auto; /* Centered horizontally */
        z-index: 20; /* Above table if overlaps */
    }

    /* Individual Seat Tuning */
    .seat-top { margin-bottom: 2px; }
    .seat-bottom { margin-top: 2px; }
    .seat-left { margin-right: 2px; }
    .seat-right { margin-left: 2px; }

    /* Tighter column gaps for layout rows */
    div[data-testid="stHorizontalBlock"] {
        gap: 0.6rem;
    }
    
    .player-seat:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(212, 175, 55, 0.3);
    }
    
    .player-seat.active {
        border-color: #ffd700;
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.6);
        animation: pulse-gold 2s infinite;
    }
    
    .player-seat.folded {
        opacity: 0.4;
        border-color: #444;
        transform: scale(0.95);
    }
    
    .player-seat.human {
        border-width: 2px;
        background: linear-gradient(145deg, #252540, #1a1a2e);
    }
    
    @keyframes pulse-gold {
        0%, 100% { box-shadow: 0 0 10px rgba(255, 215, 0, 0.5); }
        50% { box-shadow: 0 0 25px rgba(255, 215, 0, 0.8); }
    }
    
    .player-name {
        color: #d4af37;
        font-family: 'Georgia', serif;
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 0;
        text-shadow: 0 1px 2px rgba(0,0,0,0.8);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .player-chips {
        color: #4ade80;
        font-size: 1.2em;
        font-weight: bold;
        line-height: 1.2;
    }
    
    .player-bet {
        color: #fbbf24;
        font-size: 1.2em;
        margin-top: 1px;
    }
    
    .player-status {
        color: #94a3b8;
        font-size: 0.6em;
        text-transform: uppercase;
        margin-top: 1px;
    }
    
    .player-cards {
        display: flex;
        justify-content: center;
        gap: 2px;
        margin: 3px 0;
        height: 45px; /* Fixed height container */
    }
    
    /* SVG Card Styling */
    .poker-card {
        height: 100px !important; /* Force smaller cards */
        width: auto !important;
        display: inline-block;
        filter: drop-shadow(1px 1px 2px rgba(0, 0, 0, 0.5));
    }
    
    .poker-card svg {
        height: 100% !important;
        width: auto !important;
    }
    
    /* Stage Badge */
    .stage-badge {
        background: linear-gradient(145deg, #d4af37, #b8972e);
        color: #1a1a2e;
        padding: 2px 12px; /* Thinner */
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: bold;
        font-family: 'Georgia', serif;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
        
    /* Action Buttons */
    .stButton > button {
        padding: 5px 15px !important;
        font-size: 0.9em !important;
        margin-top: 5px;
    }
    
    /* Subheaders */
    h2, h3 {
        color: #f5f5f5 !important;
        font-size: 1.2em !important;
        margin-bottom: 10px !important;
    }
        
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 1px solid #d4af37;
    }
</style>
""", unsafe_allow_html=True)

# === MAIN UI ===
# Title removed to save space


# Stage display
st.markdown(f'<div style="text-align: center; margin-bottom: 5px;"><span class="stage-badge">{game.stage.name}</span></div>', unsafe_allow_html=True)

# === HELPER FUNCTIONS ===

def get_player_position(index, total):
    """Map player index to position around table"""
    if total == 4:
        return ["bottom", "left", "top", "right"][index]
    elif total == 3:
        return ["bottom", "left", "right"][index]
    elif total == 2:
        return ["bottom", "top"][index]
    else:
        return "bottom"

def render_player_card(player, index, game, pos):
    """Render a player's seat with their cards and info"""
    is_current = (index == game.current_player_index)
    is_human = player.name == st.session_state.human_name
    is_folded = player.status == PlayerState.FOLDED
    
    # CSS classes
    classes = ["player-seat", f"seat-{pos}"]
    if is_current:
        classes.append("active")
    if is_folded:
        classes.append("folded")
    if is_human:
        classes.append("human")
    
    # Determine card display
    show_cards = is_human or game.stage == GameStage.SHOWDOWN or player.status == PlayerState.ALL_IN
    
    if player.hand:
        cards_html = cards_to_html([str(c) for c in player.hand], hidden=not show_cards)
    else:
        cards_html = ""
    
    # Status icon
    status_icon = ""
    if index == game.dealer_index:
        status_icon = "🔘 "
    if player.status == PlayerState.FOLDED:
        status_icon += "❌"
    elif player.status == PlayerState.ALL_IN:
        status_icon += "⚡"
    elif player.status == PlayerState.OUT:
        status_icon += "💀"
    
    player_html = f'''
    <div class="{' '.join(classes)}">
        <div class="player-name">{status_icon}{player.name}</div>
        <div class="player-chips">💰 ${player.chips}</div>
        <div class="player-bet">Bet: ${player.current_bet}</div>
        <div class="player-cards">{cards_html}</div>
        <div class="player-status">{player.status.value}</div>
    </div>
    '''
    st.markdown(player_html, unsafe_allow_html=True)

# === POKER TABLE LAYOUT ===

# Create table layout
# Container wrapper removed


# Top player area
top_col1, top_col2, top_col3 = st.columns([1, 2, 1])
with top_col2:
    for i, p in enumerate(game.players):
        pos = get_player_position(i, len(game.players))
        if pos == "top":
            render_player_card(p, i, game, pos)

# Middle row: Left - Table - Right
left_col, center_col, right_col = st.columns([1, 3, 1])

with left_col:
    for i, p in enumerate(game.players):
        pos = get_player_position(i, len(game.players))
        if pos == "left":
            render_player_card(p, i, game, pos)

with center_col:
    # The poker table with pot and community cards
    
    # 1. Prepare Pot HTML
    pot_html = f'''<div class="pot-display">
    <h2>💰 ${game.pot}</h2>
    <p>Current Bet: ${game.current_bet}</p>
</div>'''
    
    # 2. Prepare Community Cards HTML
    if game.board:
        board_cards_html = cards_to_html([str(c) for c in game.board])
        community_html = f'<div class="community-cards">{board_cards_html}</div>'
    else:
        community_html = '<div class="community-cards" style="color: #888; font-style: italic;">Waiting for flop...</div>'
    
    # 3. Combine into Single Parent Helper
    # This ensures .pot-display and .community-cards are children of .poker-table
    table_html = f'''<div class="poker-table">
    {pot_html}
    {community_html}
</div>'''
    
    st.markdown(table_html, unsafe_allow_html=True)

with right_col:
    for i, p in enumerate(game.players):
        pos = get_player_position(i, len(game.players))
        if pos == "right":
            render_player_card(p, i, game, pos)

# Bottom player area (Human)
bot_col1, bot_col2, bot_col3 = st.columns([1, 2, 1])
with bot_col2:
    for i, p in enumerate(game.players):
        pos = get_player_position(i, len(game.players))
        if pos == "bottom":
             render_player_card(p, i, game, pos)

# End container removed






# === GAME LOGIC / ACTIONS ===
if game.stage == GameStage.GAME_OVER:
    winners = game.determine_winners()
    
    # Record Memory and Distribute Pot (Once per hand)
    if not st.session_state.get("hand_recorded", False):
        if winners:
            # Distribute pot to winners - only once!
            share = game.pot // len(winners)
            
            for w in winners:
                w.chips += share
            st.session_state.winning_share = share  # Store for display
            
            w_names = ", ".join([w.name for w in winners])
            summary = f"Hand ended. Winners: {w_names}. Pot: {game.pot}."
            for agent in st.session_state.agents.values():
                agent.add_memory(summary)
        st.session_state.hand_recorded = True

    if winners:
        st.balloons()
        w_names = ", ".join([w.name for w in winners])
        share = st.session_state.get("winning_share", game.pot // len(winners))
        st.markdown(f'<div class="winner-banner">🏆 {w_names} wins ${share}! 🏆</div>', unsafe_allow_html=True)
    
    # Reduced spacing

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🃏 Deal Next Hand"):
            # Rotate dealer position
            game.dealer_index = (game.dealer_index + 1) % len(game.players)
            # Skip OUT players for dealer
            while game.players[game.dealer_index].status == PlayerState.OUT:
                game.dealer_index = (game.dealer_index + 1) % len(game.players)
            
            game.start_hand()
            st.session_state.hand_recorded = False
            st.session_state.winning_share = 0
            st.rerun()

else:
    # Check whose turn
    current_player = game.players[game.current_player_index]
    
    if current_player.is_ai:
        st.markdown(f'<p class="thinking-indicator">⏳ {current_player.name} is thinking...</p>', unsafe_allow_html=True)
        time.sleep(1)  # Fake delay
        
        agent = st.session_state.agents[current_player.name]
        valid_actions = game.get_legal_actions(current_player)
        
        # Prepare info
        active_count = len([p for p in game.players if p.status in [PlayerState.ACTIVE, PlayerState.ALL_IN]])
        position = game.get_player_position(current_player)
        pot_odds_info = game.calculate_pot_odds(current_player)
        
        game_info = {
            "my_hand": [c.to_treys_str() for c in current_player.hand],
            "board": [c.to_treys_str() for c in game.board],
            "pot": game.pot,
            "current_bet": game.current_bet,
            "to_call": game.current_bet - current_player.current_bet,
            "my_chips": current_player.chips,
            "my_bet": current_player.current_bet,
            "players": [str(p) for p in game.players],
            "num_active_players": active_count,
            "position": position,
            "pot_odds": pot_odds_info,
            "stage": game.stage.name
        }
        
        decision = agent.get_action(game_info, valid_actions)
        
        action = decision.get("action", "fold")
        val = 0
        if action == "raise":
             try:
                 val = int(decision.get("amount", game.big_blind))
             except (TypeError, ValueError):
                 val = game.big_blind
             val = max(val, game.big_blind)
             
        # Execute
        try:
             msg = decision.get("chat", "")
             if msg:
                 st.toast(f"💬 {current_player.name}: {msg}")
             game.step(action, val)
        except Exception as e:
             st.error(f"AI Error: {e}")
             
        st.rerun()
        
    else:
        # Human Turn - Compact Layout
        # Align with the bottom player column structure [1, 2, 1] to fix "crooked" alignment
        _, main_col, _ = st.columns([1, 2, 1])
        
        with main_col:
            valid_actions = game.get_legal_actions(current_player)
            
            # Row 1: Primary Actions
            c1, c2, c3, c4 = st.columns(4)
            
            with c1:
                if "check" in valid_actions:
                    if st.button("✓ Check"):
                        game.step("check")
                        st.rerun()
                elif "call" in valid_actions:
                    cost = game.current_bet - current_player.current_bet
                    if st.button(f"📞 Call ${cost}"):
                        game.step("call")
                        st.rerun()
                        
            with c2:
                if "fold" in valid_actions:
                    if st.button("🚫 Fold"):
                        game.step("fold")
                        st.rerun()

            with c3:
                 if "all_in" in valid_actions:
                    if st.button(f"⚡ All In"):
                        game.step("all_in")
                        st.rerun()
                        
            # Row 2: Raise (conditionally shown in same block)
            if "raise" in valid_actions:
                with c4:
                    # Raise Button directly next to others
                    if st.button("💰 Raise"):
                         # Determine amount from session state or default
                         amt = st.session_state.get("raise_amount", game.current_bet + game.big_blind)
                         amt_to_add = amt - game.current_bet
                         if amt_to_add > 0:
                            game.step("raise", amt_to_add)
                            st.rerun()
                
                # Slider below - thin row
                min_r = game.current_bet + game.big_blind
                max_r = current_player.chips + current_player.current_bet
                if min_r < max_r:
                    st.slider("Raise Amount", min_value=min_r, max_value=max_r, value=min_r, key="raise_amount", label_visibility="collapsed")
