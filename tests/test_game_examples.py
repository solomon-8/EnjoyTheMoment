import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import game_examples as game


class GameExamplesTests(unittest.TestCase):
    def test_opening_and_known_legal_sequence(self):
        self.assertEqual([game.coordinate(i) for i in game.legal_moves(game.OPENING, "B")],
                         ["D3", "C4", "F5", "E6"])
        after = game.play(game.OPENING, game.square("C4"), "B")
        self.assertEqual([game.coordinate(i) for i in game.legal_moves(after, "W")],
                         ["C3", "E3", "C5"])
        self.assertEqual(game.replay(), "".join(game.EXPECTED_ROWS))
        self.assertEqual((game.replay().count("B"), game.replay().count("W")), (11, 11))

    def test_two_branches_start_from_same_board_not_a_best_move_claim(self):
        report = game.example_report()
        first, second = report["othello"]["branches"]
        self.assertEqual(first, {
            "black_move": "B1", "flips": ["C2", "D3", "E4"],
            "after_black": {"B": 15, "W": 8},
            "white_A1_legal": True, "white_A1_flips": ["B1"],
        })
        self.assertEqual(second, {
            "black_move": "E1", "flips": ["D2"],
            "after_black": {"B": 13, "W": 10},
            "white_A1_legal": False, "white_A1_flips": [],
        })
        board = game.play(game.replay(), game.square("B1"), "B")
        board = game.play(board, game.square("A1"), "W")
        self.assertEqual((board.count("B"), board.count("W")), (14, 10))
        self.assertGreater(len(report["othello"]["black_legal_moves"]), 2)
        self.assertIn("not_optimal_strategy", report["scope"])

    def test_no_chaining_skipping_empty_or_skipping_own_disc(self):
        board = list("." * 64)
        for name, side in (("A3", "W"), ("A4", "W"), ("A5", "B"),
                           ("B4", "W"), ("C4", "W"), ("D4", "B")):
            board[game.square(name)] = side
        board = "".join(board)
        self.assertEqual([game.coordinate(i) for i in game.flips(board, game.square("A2"), "B")],
                         ["A3", "A4"])
        after = game.play(board, game.square("A2"), "B")
        self.assertEqual(after[game.square("B4")], "W")
        self.assertEqual(after[game.square("C4")], "W")
        row = "." + "WBWWB" + "." * 2 + "." * 56
        self.assertEqual(game.flips(row, 0, "B"), (1,))
        self.assertEqual(game.flips(".W.B...." + "." * 56, 0, "B"), ())
        with self.assertRaises(ValueError):
            game.play(game.OPENING, game.square("A1"), "B")

    def test_all_direct_rays_and_corner_cannot_be_captured(self):
        board = list("." * 64)
        centre = game.square("D4")
        row, col = divmod(centre, 8)
        near = []
        for dr, dc in game.DIRECTIONS:
            a = (row + dr) * 8 + col + dc
            b = (row + 2 * dr) * 8 + col + 2 * dc
            board[a], board[b] = "W", "B"
            near.append(a)
        self.assertEqual(game.flips("".join(board), centre, "B"), tuple(sorted(near)))
        # For any line through a corner, one adjacent direction is outside the board.
        for corner in (0, 7, 56, 63):
            r, c = divmod(corner, 8)
            for dr, dc in game.DIRECTIONS:
                both = (0 <= r + dr < 8 and 0 <= c + dc < 8
                        and 0 <= r - dr < 8 and 0 <= c - dc < 8)
                self.assertFalse(both)

    def test_hanabi_complete_single_category_clues(self):
        self.assertEqual(game.matching_positions(game.HAND, "colour", "red"), (1, 3))
        self.assertEqual(game.matching_positions(game.HAND, "number", 1), (1, 2))
        with self.assertRaises(ValueError):
            game.matching_positions(game.HAND, "colour", "yellow")
        with self.assertRaises(ValueError):
            game.matching_positions(game.HAND, "colour_and_number", ("red", 1))
        report = game.example_report()["hanabi"]
        self.assertEqual(report["red_clue_excluded_positions"], (2, 4, 5))
        self.assertTrue(report["not_a_complete_deal_or_best_clue"])
        self.assertTrue(report["number_one_cards_start_empty_fireworks"])

    def test_published_svg_matches_replayed_board_and_labels(self):
        path = ROOT / "assets/media/othello-choice.svg"
        self.assertEqual(path.read_text(), game.diagram_svg())
        svg = ET.fromstring(path.read_text())
        ns = {"s": "http://www.w3.org/2000/svg"}
        cells = {g.get("data-square"): g for g in svg.findall(".//s:g", ns)
                 if g.get("data-square")}
        self.assertEqual(len(cells), 64)
        for i, side in enumerate(game.replay()):
            group = cells[game.coordinate(i)]
            self.assertEqual(group.get("data-disc"), side)
            self.assertEqual(len(group.findall("s:circle", ns)), int(side != "."))
        for coordinate, label in (("A1", "角"), ("B1", "甲"), ("E1", "乙")):
            self.assertEqual(cells[coordinate].find("s:text", ns).text, label)
        self.assertEqual(svg.findall(".//s:image", ns), [])


if __name__ == "__main__":
    unittest.main()
