"""Verify C28's invented score sequence, not tennis play or winning probabilities.

Only standard advantage games and best-of-three ordinary sets ending before
a tiebreak are supported. No no-ad, short-set, retirement or penalty logic.
Run: python3 tools/tennis_examples.py
"""

import json


def completed_winner(score, minimum):
    """Return the winner of a two-sided count, or None before its threshold."""
    if max(score) >= minimum and abs(score[0] - score[1]) >= 2:
        return "A" if score[0] > score[1] else "B"
    return None


def standard_game(sequence):
    """Reject invalid symbols, unfinished games and points after completion."""
    if not isinstance(sequence, str):
        raise ValueError("game must be a string of A/B point winners")
    points = [0, 0]
    for player in sequence:
        if player not in ("A", "B"):
            raise ValueError("point winner must be A or B")
        if completed_winner(points, 4):
            raise ValueError("point played after game completed")
        points[0 if player == "A" else 1] += 1
    winner = completed_winner(points, 4)
    if winner is None:
        raise ValueError("unfinished standard game")
    return {"winner": winner, "points": points}


def ordinary_set(sequences):
    """Validate complete standard games; reject a 6-all tiebreak boundary."""
    games, points = [0, 0], [0, 0]
    for sequence in sequences:
        if completed_winner(games, 6):
            raise ValueError("game played after set completed")
        if games == [6, 6]:
            raise ValueError("tiebreak boundary is outside this example")
        result = standard_game(sequence)
        games[0 if result["winner"] == "A" else 1] += 1
        points = [points[i] + result["points"][i] for i in (0, 1)]
    winner = completed_winner(games, 6)
    if winner is None:
        raise ValueError("unfinished ordinary set")
    return {"winner": winner, "games": games, "points": points}


def best_of_three(set_sequences):
    sets, games, points, results = [0, 0], [0, 0], [0, 0], []
    for sequences in set_sequences:
        if max(sets) == 2:
            raise ValueError("set played after match completed")
        result = ordinary_set(sequences)
        results.append(result)
        sets[0 if result["winner"] == "A" else 1] += 1
        for i in (0, 1):
            games[i] += result["games"][i]
            points[i] += result["points"][i]
    if max(sets) != 2:
        raise ValueError("unfinished best-of-three match")
    return {"winner": "A" if sets[0] == 2 else "B",
            "sets": sets, "games": games, "points": points, "by_set": results}


def example_sequences():
    """All 128 point winners, grouped into the 26 complete games / three sets."""
    by_winner = {"A": "AABBAA", "B": "BBBB"}
    return tuple(tuple(by_winner[p] for p in order)
                 for order in ("BBBBBB", "ABABABABAA", "ABABABABAA"))


if __name__ == "__main__":
    print(json.dumps({"kind": "original_scoring_construction_not_match_data",
                      "sequences": example_sequences(),
                      "result": best_of_three(example_sequences())}, indent=2))
