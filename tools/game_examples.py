#!/usr/bin/env python3
"""Reproduce C19's finite examples, not a game solver or player-effect test."""
import argparse
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTIONS = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1)
                   if (r, c) != (0, 0))
OPENING = "." * 27 + "WB" + "." * 6 + "BW" + "." * 27
SEQUENCE = "D3 C5 C6 E3 B5 C3 F5 B6 D2 F6 F7 C7 B2 C1 F4 F3 D6 C2".split()
EXPECTED_ROWS = (
    "..W.....", ".BWW....", "..BWWW..", "...BWB..",
    ".BWBBB..", ".WWB.B..", "..W..B..", "........",
)
HAND = (("red", 1), ("blue", 1), ("red", 3), ("green", 2), ("white", 5))


def square(name):
    if len(name) != 2 or name[0] not in "ABCDEFGH" or name[1] not in "12345678":
        raise ValueError("Expected A1..H8")
    return (int(name[1]) - 1) * 8 + ord(name[0]) - ord("A")


def coordinate(index):
    if not 0 <= index < 64:
        raise ValueError("Square outside board")
    return chr(ord("A") + index % 8) + str(index // 8 + 1)


def flips(board, move, side):
    """Evaluate all rays on the unchanged board; do not chain new flips."""
    if len(board) != 64 or set(board) - {".", "B", "W"} or side not in ("B", "W"):
        raise ValueError("Invalid board or side")
    if not 0 <= move < 64:
        raise ValueError("Square outside board")
    if board[move] != ".":
        return ()
    row, col = divmod(move, 8)
    opponent = "W" if side == "B" else "B"
    result = []
    for dr, dc in DIRECTIONS:
        r, c = row + dr, col + dc
        line = []
        while 0 <= r < 8 and 0 <= c < 8 and board[r * 8 + c] == opponent:
            line.append(r * 8 + c)
            r, c = r + dr, c + dc
        if line and 0 <= r < 8 and 0 <= c < 8 and board[r * 8 + c] == side:
            result.extend(line)
    return tuple(sorted(result))


def legal_moves(board, side):
    return tuple(i for i in range(64) if flips(board, i, side))


def play(board, move, side):
    changed = flips(board, move, side)
    if not changed:
        raise ValueError("Move must outflank at least one opposing disc")
    result = list(board)
    for index in (move,) + changed:
        result[index] = side
    return "".join(result)


def replay():
    board = OPENING
    for turn, name in enumerate(SEQUENCE):
        board = play(board, square(name), "B" if turn % 2 == 0 else "W")
    if board != "".join(EXPECTED_ROWS):
        raise AssertionError("Published diagram and replay disagree")
    return board


def matching_positions(hand, kind, value):
    """One-based positions. Only a single basic-game colour or number clue."""
    if kind not in ("colour", "number"):
        raise ValueError("Choose colour OR number, not both")
    field = 0 if kind == "colour" else 1
    positions = tuple(i + 1 for i, card in enumerate(hand) if card[field] == value)
    if not positions:
        raise ValueError("This edition disallows clues with no matching card")
    return positions


def changing_position_report(swap_first_two=False):
    """Two compatible witnesses, not an exhaustive hand or strategy model."""
    if type(swap_first_two) is not bool:
        raise ValueError("swap_first_two must be a boolean")
    colours = ("red", "blue", "green", "white", "yellow")
    deck_counts = Counter({
        (colour, number): (3 if number == 1 else 1 if number == 5 else 2)
        for colour in colours for number in range(1, 6)
    })
    hands = [
        [("yellow", 1), ("green", 1), ("white", 1), ("yellow", 3), ("blue", 3)],
        list(HAND),
        [("red", 1), ("blue", 2), ("green", 3), ("white", 4), ("yellow", 4)],
    ]
    if swap_first_two:
        hands[1][0], hands[1][1] = hands[1][1], hands[1][0]
    initial_hands = [list(hand) for hand in hands]
    draws = [("yellow", 2), ("blue", 4)]
    allocated = Counter(card for hand in hands for card in hand) + Counter(draws)
    assert sum(deck_counts.values()) == 50
    assert all(count <= deck_counts[card] for card, count in allocated.items())
    fireworks = {colour: 0 for colour in colours}
    empty_playable = [card[1] == fireworks[card[0]] + 1 for card in hands[1][:2]]
    tokens = 8
    token_history = [tokens]
    events = []

    # A clues B's ones. B's first two positions stay fixed throughout.
    assert tokens > 0
    positions = matching_positions(hands[1], "number", 1)
    assert positions == (1, 2)
    tokens -= 1
    events.append({"actor": "A", "action": "clue", "target": "B",
                   "kind": "number", "value": 1, "positions": list(positions)})
    token_history.append(tokens)

    # B discards the fourth card; this is permitted only below eight tokens.
    assert tokens < 8
    discarded = hands[1].pop(3)
    assert discarded == ("green", 2)
    hands[1].append(draws[0])
    tokens += 1
    events.append({"actor": "B", "action": "discard", "card": list(discarded)})
    token_history.append(tokens)

    # C starts the red firework with its own red one, then draws.
    card = hands[2].pop(0)
    assert card == ("red", 1) and card[1] == fireworks[card[0]] + 1
    fireworks[card[0]] = card[1]
    hands[2].append(draws[1])
    events.append({"actor": "C", "action": "play", "card": list(card),
                   "successful": True})
    token_history.append(tokens)

    # A gives a separate, legal white clue to C, not another clue to B.
    assert tokens > 0
    positions = matching_positions(hands[2], "colour", "white")
    tokens -= 1
    events.append({"actor": "A", "action": "clue", "target": "C",
                   "kind": "colour", "value": "white", "positions": list(positions)})
    token_history.append(tokens)

    observation_b = {
        "visible_hands": {
            "A": [list(card) for card in hands[0]],
            "C": [list(card) for card in hands[2]],
        },
        "own_card_count": len(hands[1]),
        "known_own_number_one_positions": [1, 2],
        "fireworks": fireworks,
        "available_clues": tokens,
        "deck_size": 50 - 15 - len(draws),
        "discarded": [list(discarded)],
        "public_events": events,
    }
    return {
        "scope": "two_witnesses_literal_clues_only_not_complete_information_set",
        "initial_hands": [[list(card) for card in hand] for hand in initial_hands],
        "draw_prefix": [list(card) for card in draws],
        "deck_counts_valid": True,
        "turn_order": ["A", "B", "C", "A"],
        "next_player": "B",
        "token_history": token_history,
        "empty_columns_first_two_playable": empty_playable,
        "old_number_clue_still_true": all(card[1] == 1 for card in hands[1][:2]),
        "B_first_two_now": [list(card) for card in hands[1][:2]],
        "B_first_two_playable_now": [
            card[1] == fireworks[card[0]] + 1 for card in hands[1][:2]
        ],
        "B_observation": observation_b,
        "does_not_assign_probabilities_or_optimal_actions": True,
    }


def route_wins(route, card):
    """C19's original one-round example, not a commercial game or real payoff."""
    if route not in ("A", "B") or type(card) is not int or card not in range(1, 7):
        raise ValueError("Choose route A/B and an integer card 1..6")
    return card <= 4 if route == "A" else card >= 5


def route_report():
    outcomes = [
        {"card": card, "A_wins": route_wins("A", card),
         "B_wins": route_wins("B", card)}
        for card in range(1, 7)
    ]
    return {
        "scope": "original_six_equiprobable_cards_one_round_no_stakes",
        "outcomes": outcomes,
        "before_reveal_winning_cases": {
            route: sum(route_wins(route, card) for card in range(1, 7))
            for route in ("A", "B")
        },
        "after_reveal_winning_route": [
            "A" if route_wins("A", card) else "B" for card in range(1, 7)
        ],
        "not_a_claim_about_player_happiness_or_unknown_probabilities": True,
    }


def example_report():
    board = replay()
    branches = []
    for name in ("B1", "E1"):
        move = square(name)
        after = play(board, move, "B")
        white_a1 = flips(after, square("A1"), "W")
        branches.append({
            "black_move": name,
            "flips": [coordinate(i) for i in flips(board, move, "B")],
            "after_black": {"B": after.count("B"), "W": after.count("W")},
            "white_A1_legal": bool(white_a1),
            "white_A1_flips": [coordinate(i) for i in white_a1],
        })
    return {
        "scope": "finite_original_examples_not_optimal_strategy",
        "routes": route_report(),
        "othello": {
            "sequence": SEQUENCE,
            "rows": list(EXPECTED_ROWS),
            "to_move": "B",
            "count": {"B": board.count("B"), "W": board.count("W")},
            "black_legal_moves": [coordinate(i) for i in legal_moves(board, "B")],
            "branches": branches,
        },
        "hanabi": {
            "scope": "three_players_base_game_no_prior_clues_empty_fireworks",
            "hand": [{"colour": c, "number": n} for c, n in HAND],
            "red_clue_positions": matching_positions(HAND, "colour", "red"),
            "red_clue_excluded_positions": tuple(
                i for i in range(1, len(HAND) + 1)
                if i not in matching_positions(HAND, "colour", "red")),
            "one_clue_positions": matching_positions(HAND, "number", 1),
            "number_one_cards_start_empty_fireworks": all(
                HAND[i - 1][1] == 1 for i in matching_positions(HAND, "number", 1)),
            "not_a_complete_deal_or_best_clue": True,
            "changing_position_witnesses": [
                changing_position_report(False), changing_position_report(True)
            ],
        },
    }


def diagram_svg():
    board = replay()
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="440" height="570" '
        'viewBox="0 0 440 570" role="img" aria-labelledby="title desc">',
        '<title id="title">这步翻得多，就一定更好吗？</title>',
        '<desc id="desc">原创合法局面，黑方走，黑白各11枚。甲B1翻3枚，'
        '乙E1翻1枚；仅甲让白方下一手可下A1。甲乙不是仅有的合法着，也不是最优排序。</desc>',
        '<rect width="440" height="570" rx="16" fill="#fff8ec"/>',
        '<g font-family="PingFang SC, Microsoft YaHei, sans-serif" fill="#24231f">',
        '<text x="24" y="42" font-size="24" font-weight="700">这步翻得多，就一定更好吗？</text>',
        '<text x="24" y="76" font-size="20">黑方走 · 黑白各 11 枚 · 原创局面</text>',
    ]
    for i, column in enumerate("ABCDEFGH"):
        parts.append(f'<text x="{64 + 43 * i}" y="115" font-size="17" '
                     f'text-anchor="middle">{column}</text>')
        parts.append(f'<text x="26" y="{156 + 43 * i}" font-size="17" '
                     f'text-anchor="middle">{i + 1}</text>')
    for index, value in enumerate(board):
        row, col = divmod(index, 8)
        x, y = 43 + col * 43, 130 + row * 43
        name = coordinate(index)
        parts.append(f'<g data-square="{name}" data-disc="{value}">')
        parts.append(f'<rect x="{x}" y="{y}" width="43" height="43" '
                     'fill="#d8e9e5" stroke="#72928b" stroke-width="1"/>')
        if value != ".":
            colour = "#24231f" if value == "B" else "#fffdf8"
            parts.append(f'<circle cx="{x + 21.5}" cy="{y + 21.5}" r="15" '
                         f'fill="{colour}" stroke="#24231f" stroke-width="1.4"/>')
        if name in ("B1", "E1", "A1"):
            label = {"B1": "甲", "E1": "乙", "A1": "角"}[name]
            parts.append(f'<text x="{x + 21.5}" y="{y + 28}" font-size="20" '
                         f'font-weight="700" text-anchor="middle" fill="#9d3b1d">{label}</text>')
        parts.append("</g>")
    parts.extend([
        '<text x="24" y="511" font-size="20">甲 B1：翻 3 枚，白可走 A1</text>',
        '<text x="24" y="545" font-size="20">乙 E1：翻 1 枚，白不能走 A1</text>',
        "</g></svg>",
    ])
    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-diagram", action="store_true",
                        help="Regenerate the original SVG; PNG rendering is separate")
    args = parser.parse_args()
    report = example_report()
    if args.write_diagram:
        (ROOT / "assets/media/othello-choice.svg").write_text(diagram_svg(), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
