from __future__ import annotations

from collections import Counter
from typing import List, Optional, Tuple


RANK_MAP = {r: i for i, r in enumerate("23456789TJQKA", start=2)}


def evaluate_best_hand(cards: List[str]) -> Tuple[int, List[int], str]:
    if len(cards) < 5:
        raise ValueError("Need at least 5 cards to evaluate.")

    ranks = [RANK_MAP[c[0]] for c in cards]
    suits = [c[1] for c in cards]
    rank_counts = Counter(ranks)
    suit_counts = Counter(suits)

    flush_suit = _find_flush_suit(suit_counts)
    if flush_suit:
        flush_ranks = sorted(
            [RANK_MAP[c[0]] for c in cards if c[1] == flush_suit],
            reverse=True,
        )
        straight_flush_high = _find_straight(flush_ranks)
        if straight_flush_high:
            return 8, [straight_flush_high], "straight_flush"

    quad_rank = _find_rank_with_count(rank_counts, 4)
    if quad_rank:
        kicker = max(r for r in ranks if r != quad_rank)
        return 7, [quad_rank, kicker], "four_kind"

    trips = sorted([r for r, c in rank_counts.items() if c >= 3], reverse=True)
    pairs = sorted([r for r, c in rank_counts.items() if c >= 2], reverse=True)
    if trips:
        trip_rank = trips[0]
        remaining_pairs = [r for r in pairs if r != trip_rank]
        if len(trips) > 1:
            remaining_pairs.append(trips[1])
        if remaining_pairs:
            pair_rank = max(remaining_pairs)
            return 6, [trip_rank, pair_rank], "full_house"

    if flush_suit:
        top_flush = sorted(
            [RANK_MAP[c[0]] for c in cards if c[1] == flush_suit],
            reverse=True,
        )[:5]
        return 5, top_flush, "flush"

    straight_high = _find_straight(sorted(set(ranks), reverse=True))
    if straight_high:
        return 4, [straight_high], "straight"

    if trips:
        trip_rank = trips[0]
        kickers = _top_kickers(ranks, [trip_rank], 2)
        return 3, [trip_rank] + kickers, "three_kind"

    if len(pairs) >= 2:
        high_pair, low_pair = pairs[0], pairs[1]
        kicker = _top_kickers(ranks, [high_pair, low_pair], 1)
        return 2, [high_pair, low_pair] + kicker, "two_pair"

    if len(pairs) == 1:
        pair_rank = pairs[0]
        kickers = _top_kickers(ranks, [pair_rank], 3)
        return 1, [pair_rank] + kickers, "one_pair"

    return 0, sorted(ranks, reverse=True)[:5], "high_card"


def _find_flush_suit(suit_counts: Counter[str]) -> Optional[str]:
    for suit, count in suit_counts.items():
        if count >= 5:
            return suit
    return None


def _find_rank_with_count(rank_counts: Counter[int], count: int) -> Optional[int]:
    candidates = [r for r, c in rank_counts.items() if c == count]
    return max(candidates) if candidates else None


def _find_straight(ranks_desc: List[int]) -> Optional[int]:
    unique = sorted(set(ranks_desc))
    if 14 in unique:
        unique.insert(0, 1)
    best_high = None
    run = 1
    for i in range(1, len(unique)):
        if unique[i] == unique[i - 1] + 1:
            run += 1
            if run >= 5:
                best_high = unique[i]
        else:
            run = 1
    if best_high == 5:
        return 5
    return best_high


def _top_kickers(ranks: List[int], exclude: List[int], count: int) -> List[int]:
    remaining = [r for r in ranks if r not in exclude]
    return sorted(remaining, reverse=True)[:count]
