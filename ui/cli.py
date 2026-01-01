from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from typing import List

class GameCLI:
    def __init__(self):
        self.console = Console()

    def print_welcome(self):
        self.console.print(Panel.fit("[bold green]Welcome to Texas Hold'em AI[/bold green]", border_style="green"))

    def render_state(self, game, human_player=None):
        """
        Renders the current game state to the console.
        """
        # Create a layout
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="board", size=10),
            Layout(name="players"),
            Layout(name="footer", size=5)
        )
        
        # Header
        layout["header"].update(Panel(f"Pot: [gold1]{game.pot}[/gold1] | Blind: {game.small_blind}/{game.big_blind}", style="bold white"))
        
        # Board
        board_text = Text()
        if not game.board:
            board_text.append("Waiting for deal...")
        else:
            for card in game.board:
                self._append_card(board_text, card)
                board_text.append("  ")
        layout["board"].update(Panel(board_text, title="Community Cards", border_style="blue"))
        
        # Players Table
        table = Table(box=box.ROUNDED)
        table.add_column("Player", style="cyan")
        table.add_column("Role", style="magenta")
        table.add_column("Chips", justify="right")
        table.add_column("Bet", justify="right")
        table.add_column("Status")
        table.add_column("Hand") # Show hand if human or showdown
        
        for i, p in enumerate(game.players):
             role = ""
             if i == game.dealer_index: role = "D "
             
             # Show hand for human or all if showdown?
             # For now, just show human hand or if debug mode
             hand_str = "HIDDEN"
             if p == human_player or p.is_ai == False: # Assume human if not AI
                 hand_str = " ".join([str(c) for c in p.hand])
             
             table.add_row(
                 p.name,
                 role,
                 str(p.chips),
                 str(p.current_bet),
                 p.status.value,
                 hand_str
             )
        
        layout["players"].update(Panel(table, title="Players"))
        
        # Footer
        layout["footer"].update(Panel("Press Enter to continue...", style="dim"))
        
        self.console.print(layout)

    def _append_card(self, text_obj, card):
        color = "black"
        if card.suit.name in ['HEARTS', 'DIAMONDS']:
            color = "red"
        text_obj.append(str(card), style=f"bold {color} on white")

    def get_action(self, valid_actions: List[str]) -> str:
        self.console.print(f"\n[bold yellow]Your turn![/bold yellow] Valid actions: {', '.join(valid_actions)}")
        while True:
            choice = self.console.input("Enter action: ").strip().lower()
            if choice in valid_actions:
                return choice
            self.console.print("[red]Invalid action. Try again.[/red]")

    def get_amount(self, min_amt, max_amt) -> int:
        while True:
             try:
                 amt = int(self.console.input(f"Enter amount ({min_amt}-{max_amt}): "))
                 if min_amt <= amt <= max_amt:
                     return amt
                 self.console.print("[red]Amount out of range.[/red]")
             except ValueError:
                 self.console.print("[red]Invalid number.[/red]")
