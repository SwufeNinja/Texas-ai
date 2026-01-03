import random
import unittest

from app.game_engine import GameEngine
from app.models import Player, Room, Stage


def _make_engine() -> GameEngine:
    players = [
        Player(id="p1", name="One", is_ai=False, chips=200, ready=True),
        Player(id="p2", name="Two", is_ai=False, chips=200, ready=True),
    ]
    room = Room(id="test", players=players, small_blind=5, big_blind=10)
    engine = GameEngine(room, rng=random.Random(0))
    engine.start_hand()
    return engine


class GameEngineTest(unittest.TestCase):
    def test_min_raise_error_details(self) -> None:
        engine = _make_engine()
        current = engine.room.players[engine.room.current_actor_index]
        ok, reason = engine.process_action(current.id, "raise", 5)
        self.assertFalse(ok)
        self.assertEqual(reason, "raise below minimum")
        details = engine.action_error_details(current.id, "raise", 5, reason)
        self.assertEqual(details["min_raise"], 10)
        self.assertEqual(details["current_bet"], 10)
        self.assertEqual(details["player_bet"], 5)

    def test_round_advances_to_flop(self) -> None:
        engine = _make_engine()
        sb = engine.room.players[engine.room.current_actor_index]
        ok, _ = engine.process_action(sb.id, "call", 0)
        self.assertTrue(ok)
        bb = engine.room.players[engine.room.current_actor_index]
        ok, _ = engine.process_action(bb.id, "check", 0)
        self.assertTrue(ok)
        self.assertEqual(engine.room.stage, Stage.FLOP)
        self.assertEqual(len(engine.room.community_cards), 3)
        self.assertEqual(engine.room.current_bet, 0)
        self.assertEqual(engine.room.players[0].bet, 0)
        self.assertEqual(engine.room.players[1].bet, 0)

    def test_fold_ends_hand(self) -> None:
        engine = _make_engine()
        sb = engine.room.players[engine.room.current_actor_index]
        ok, _ = engine.process_action(sb.id, "fold", 0)
        self.assertTrue(ok)
        self.assertEqual(engine.room.stage, Stage.SHOWDOWN)
        self.assertEqual(engine.room.pot, 0)
        self.assertEqual(engine.room.winners, ["p1"])
        self.assertEqual(engine.room.players[0].chips, 205)


if __name__ == "__main__":
    unittest.main()
