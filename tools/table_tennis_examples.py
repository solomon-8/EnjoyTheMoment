#!/usr/bin/env python3
"""Check C38's invented first-game sequences, not matches or suitable activity.

Fixed A1/A2 versus B1/B2, with A1 serving to B1 in the first, non-deciding
game. No expedite system, wheelchair exception, penalties or later games.
L means a let already adjudicated by an official; this code does not judge it.
"""
from collections import Counter
from itertools import combinations
import json

PAIRS = (("A1", "B1"), ("B1", "A2"), ("A2", "B2"), ("B2", "A1"))
HIT_ORDER = ("A1", "B1", "A2", "B2")


def first_game(events):
    """Process already adjudicated A/B points and L lets; reject extra points."""
    if not isinstance(events, str):
        raise ValueError("events must be an A/B/L string")
    score, rows, counted = [0, 0], [], 0
    for event in events:
        if event not in "ABL":
            raise ValueError("only A/B points and adjudicated L lets are supported")
        if max(score) >= 11 and abs(score[0] - score[1]) >= 2:
            raise ValueError("event after a completed game")
        group = counted // 2 if counted < 20 else 10 + counted - 20
        server, receiver = PAIRS[group % 4]
        rows.append({"before": score.copy(), "server": server,
                     "receiver": receiver, "event": event})
        if event != "L":
            score[event == "B"] += 1
            counted += 1
    winner = ("A" if score[0] > score[1] else "B") if (
        max(score) >= 11 and abs(score[0] - score[1]) >= 2) else None
    group = counted // 2 if counted < 20 else 10 + counted - 20
    return {"score": score, "winner": winner, "events": rows,
            "next_pair": None if winner else PAIRS[group % 4]}


def participation(fixtures):
    """Appearances only: not minutes, ball contacts, fairness or enjoyment."""
    counts = Counter({name: 0 for name in "ABCDEF"})
    for pair in fixtures:
        if (not isinstance(pair, str) or len(pair) != 2 or pair[0] == pair[1]
                or any(name not in counts for name in pair)):
            raise ValueError("each fixture needs two different players from A–F")
        counts.update(pair)
    return dict(sorted(counts.items()))


def examples():
    winner_stays = ("AB", "AC", "AD", "AE", "AF", "AB")
    two_rounds = ("AB", "CD", "EF", "AC", "BE", "DF")
    round_robin = tuple("".join(pair) for pair in combinations("ABCDEF", 2))
    return {
        "kind": "original_constructions_not_observed_matches",
        "deuce_finish": first_game("AB" * 10 + "ALBLAA"),
        "winner_stays": participation(winner_stays),
        "two_rounds": participation(two_rounds),
        "round_robin_games": len(round_robin),
        "round_robin": participation(round_robin),
    }


if __name__ == "__main__":
    print(json.dumps(examples(), ensure_ascii=False, indent=2))
