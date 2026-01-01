"""
SVG Poker Card Generator
Generates beautiful SVG playing cards for the Texas Hold'em UI
"""

from typing import Tuple

# Card dimensions
CARD_WIDTH = 70
CARD_HEIGHT = 100
BORDER_RADIUS = 8

# Colors
COLORS = {
    "background": "#ffffff",
    "border": "#d4af37",  # Gold
    "red": "#c41e3a",     # Hearts, Diamonds
    "black": "#1a1a2e",   # Spades, Clubs
    "back": "#1a1a2e",
    "back_pattern": "#d4af37"
}

# Suit symbols
SUITS = {
    "♠": ("spade", "black"),
    "♥": ("heart", "red"),
    "♦": ("diamond", "red"),
    "♣": ("club", "black"),
    "s": ("spade", "black"),
    "h": ("heart", "red"),
    "d": ("diamond", "red"),
    "c": ("club", "black"),
}

# Suit SVG paths
SUIT_PATHS = {
    "spade": "M35 15 C35 15 20 35 20 50 C20 60 28 65 35 60 L35 75 L30 75 L40 75 L35 75 L35 60 C42 65 50 60 50 50 C50 35 35 15 35 15 Z",
    "heart": "M35 25 C25 15 10 20 10 35 C10 55 35 70 35 70 C35 70 60 55 60 35 C60 20 45 15 35 25 Z",
    "diamond": "M35 10 L55 50 L35 90 L15 50 Z",
    "club": "M35 70 L35 85 L25 85 L45 85 L35 85 L35 70 M35 20 C30 20 25 25 25 32 C25 38 29 42 35 42 C29 42 20 42 20 55 C20 62 27 68 35 68 C43 68 50 62 50 55 C50 42 41 42 35 42 C41 42 45 38 45 32 C45 25 40 20 35 20 Z"
}


def get_suit_svg(suit_name: str, color: str, scale: float = 0.3, offset_x: float = 0, offset_y: float = 0) -> str:
    """Generate SVG path for a suit symbol"""
    path = SUIT_PATHS.get(suit_name, SUIT_PATHS["spade"])
    return f'<path d="{path}" fill="{COLORS[color]}" transform="translate({offset_x},{offset_y}) scale({scale})"/>'


def generate_card_svg(rank, suit):
    """
    Generate an SVG for a playing card.
    
    Args:
        rank: Card rank (A, 2-10, J, Q, K)
        suit: Card suit (spade, heart, diamond, club unicode char)
    
    Returns:
        SVG string for the card
    """
    suit_info = SUITS.get(suit, SUITS["s"])
    suit_name, color = suit_info
    text_color = COLORS[color]
    
    # Format rank display
    display_rank = rank.upper() if rank.upper() in ['A', 'K', 'Q', 'J'] else rank
    
    # Font size adjustments
    if display_rank == "10":
        corner_font_size = 12
        corner_x_offset = 2
    else:
        corner_font_size = 16
        corner_x_offset = 4
        
    center_font_size = 36
    
    # Suit symbol for display
    suit_symbol = {"spade": "♠", "heart": "♥", "diamond": "♦", "club": "♣"}[suit_name]
    
    # Suit symbol for display
    suit_symbol = {"spade": "♠", "heart": "♥", "diamond": "♦", "club": "♣"}[suit_name]
    
    # Use int for coordinates to ensure crisp rendering
    width = int(CARD_WIDTH)
    height = int(CARD_HEIGHT)
    
    svg = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="background-color: transparent;">
  <rect x="1" y="1" width="{width-2}" height="{height-2}" rx="{BORDER_RADIUS}" ry="{BORDER_RADIUS}" 
        fill="{COLORS['background']}" stroke="{COLORS['border']}" stroke-width="2"/>
  
  <text x="6" y="16" font-family="Arial, sans-serif" font-size="{corner_font_size}" font-weight="bold" fill="{text_color}" text-anchor="start">{display_rank}</text>
  <text x="6" y="28" font-family="Arial, sans-serif" font-size="{corner_font_size-2}" fill="{text_color}" text-anchor="start">{suit_symbol}</text>
  
  <text x="50%" y="55%" font-family="Arial, sans-serif" font-size="{center_font_size}" fill="{text_color}" text-anchor="middle" dominant-baseline="middle">{suit_symbol}</text>
  
  <g transform="rotate(180, {width/2}, {height/2})">
    <text x="6" y="16" font-family="Arial, sans-serif" font-size="{corner_font_size}" font-weight="bold" fill="{text_color}" text-anchor="start">{display_rank}</text>
    <text x="6" y="28" font-family="Arial, sans-serif" font-size="{corner_font_size-2}" fill="{text_color}" text-anchor="start">{suit_symbol}</text>
  </g>
</svg>'''
    
    # Return as single line to avoid markdown issues
    return svg.replace('\n', '')


def generate_card_back_svg() -> str:
    """Generate an SVG for the back of a card"""
    svg = f'''<svg width="{CARD_WIDTH}" height="{CARD_HEIGHT}" viewBox="0 0 {CARD_WIDTH} {CARD_HEIGHT}" xmlns="http://www.w3.org/2000/svg">
  <!-- Card background -->
  <rect x="1" y="1" width="{CARD_WIDTH-2}" height="{CARD_HEIGHT-2}" rx="{BORDER_RADIUS}" ry="{BORDER_RADIUS}" 
        fill="{COLORS['back']}" stroke="{COLORS['back_pattern']}" stroke-width="2"/>
  
  <!-- Inner border -->
  <rect x="6" y="6" width="{CARD_WIDTH-12}" height="{CARD_HEIGHT-12}" rx="4" ry="4" 
        fill="none" stroke="{COLORS['back_pattern']}" stroke-width="1"/>
  
  <!-- Diamond pattern -->
  <pattern id="cardPattern" patternUnits="userSpaceOnUse" width="10" height="10">
    <path d="M5 0 L10 5 L5 10 L0 5 Z" fill="{COLORS['back_pattern']}" opacity="0.3"/>
  </pattern>
  <rect x="8" y="8" width="{CARD_WIDTH-16}" height="{CARD_HEIGHT-16}" fill="url(#cardPattern)"/>
  
  <!-- Center emblem -->
  <circle cx="{CARD_WIDTH//2}" cy="{CARD_HEIGHT//2}" r="15" fill="none" stroke="{COLORS['back_pattern']}" stroke-width="2"/>
  <text x="{CARD_WIDTH//2}" y="{CARD_HEIGHT//2 + 5}" font-family="Georgia, serif" font-size="14" font-weight="bold" 
        fill="{COLORS['back_pattern']}" text-anchor="middle">♠</text>
</svg>'''
    
    return svg


def card_to_svg(card_str: str) -> str:
    """
    Convert a card string to SVG.
    
    Args:
        card_str: Card in format like "As", "Kh", "10d", "2c" or "A♠", "K♥", etc.
    
    Returns:
        SVG string
    """
    if not card_str or card_str == "🂠":
        return generate_card_back_svg()
    
    # Parse card string
    card_str = card_str.strip()
    
    # Handle Unicode suit symbols
    if any(s in card_str for s in "♠♥♦♣"):
        for suit_char in "♠♥♦♣":
            if suit_char in card_str:
                rank = card_str.replace(suit_char, "")
                return generate_card_svg(rank, suit_char)
    
    # Handle letter suit format (As, Kh, etc.)
    if len(card_str) >= 2:
        suit = card_str[-1].lower()
        rank = card_str[:-1]
        if suit in "shdc":
            return generate_card_svg(rank, suit)
    
    # Fallback to card back
    return generate_card_back_svg()


def cards_to_html(cards: list, hidden: bool = False) -> str:
    """
    Convert a list of cards to HTML with SVG cards.
    
    Args:
        cards: List of card strings
        hidden: If True, show card backs instead
    
    Returns:
        HTML string with all cards
    """
    if not cards:
        return ""
    
    html_parts = ['<div style="display: flex; gap: 5px; justify-content: center;">']
    
    for card in cards:
        if hidden:
            svg = generate_card_back_svg()
        else:
            svg = card_to_svg(str(card))
        html_parts.append(f'<div class="poker-card">{svg}</div>')
    
    html_parts.append('</div>')
    return "".join(html_parts)


# Test
if __name__ == "__main__":
    print("Testing SVG generation...")
    print(generate_card_svg("A", "♠"))
    print("\nCard back:")
    print(generate_card_back_svg())
