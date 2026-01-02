from __future__ import annotations

import random
import sys
from pprint import pprint

from .game_engine import GameEngine
from .models import Player, Room, Stage


def run_demo_hand(mode: str) -> None:
    players = [
        Player(id="p1", name="Alice", is_ai=False, chips=200),
        Player(id="p2", name="Bob", is_ai=False, chips=200),
        Player(id="p3", name="Cleo", is_ai=True, chips=200),
    ]
    room = Room(id="demo", players=players, small_blind=5, big_blind=10)
    engine = GameEngine(room)
    engine.start_hand()

    print("== Hand start ==")
    pprint(engine.state_snapshot())

    scripted = [
        ("call", 0),
        ("call", 0),
        ("check", 0),
        ("check", 0),
        ("check", 0),
        ("check", 0),
        ("check", 0),
        ("check", 0),
    ]

    step = 0
    while room.stage != Stage.SHOWDOWN:
        current = room.players[room.current_actor_index]
        if mode == "random":
            action, amount = _random_action(engine, current.id)
        elif mode == "interactive" and not current.is_ai:
            action, amount = _prompt_action(engine, current.id)
        else:
            if step >= len(scripted):
                action, amount = _random_action(engine, current.id)
            else:
                action, amount = scripted[step]
        ok, message = engine.process_action(current.id, action, amount)
        print(f"{current.name} -> {action} ({message})")
        if not ok:
            break
        step += 1
        pprint(engine.state_snapshot())

    print("== Hand end ==")
    pprint(engine.state_snapshot())


def _random_action(engine: GameEngine, player_id: str) -> tuple[str, int]:
    options = engine.legal_actions(player_id)
    actions = []
    if options.get("fold"):
        actions.append(("fold", 0))
    if options.get("check"):
        actions.append(("check", 0))
    if options.get("call", 0) > 0:
        actions.append(("call", 0))
    raise_info = options.get("raise")
    if raise_info and raise_info["max"] >= raise_info["min"]:
        amount = random.randint(raise_info["min"], raise_info["max"])
        actions.append(("raise", amount))
    if options.get("allin"):
        actions.append(("allin", 0))
    return random.choice(actions)


def _prompt_action(engine: GameEngine, player_id: str) -> tuple[str, int]:
    options = engine.legal_actions(player_id)
    print("Your options:")
    print(options)
    raw = input("Action (fold/check/call/raise/allin): ").strip().lower()
    if raw == "raise":
        amount = int(input("Raise amount: ").strip())
        return "raise", amount
    if raw == "call":
        return "call", 0
    if raw == "check":
        return "check", 0
    if raw == "allin":
        return "allin", 0
    return "fold", 0


def _parse_mode(argv: list[str]) -> str:
    if len(argv) > 1:
        mode = argv[1].lower()
        if mode in ("scripted", "random", "interactive"):
            return mode
    return "scripted"


def run() -> None:
    mode = _parse_mode(sys.argv)
    run_demo_hand(mode)


if __name__ == "__main__":
    run()
