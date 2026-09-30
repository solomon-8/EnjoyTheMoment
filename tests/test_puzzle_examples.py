import itertools
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import puzzle_examples as puzzles


class PuzzleExamplesTests(unittest.TestCase):
    def test_road_problem_and_changed_problem(self):
        self.assertEqual(puzzles.degrees(puzzles.ROADS),
                         {"A": 3, "B": 3, "C": 3, "D": 3})
        self.assertEqual(puzzles.trails(puzzles.ROADS), [])
        paths = puzzles.trails(puzzles.REDUCED_ROADS)
        self.assertIn(puzzles.REDUCED_WALK, paths)
        for path in paths:
            actual = [tuple(sorted(edge)) for edge in zip(path, path[1:])]
            expected = [tuple(sorted(edge)) for edge in puzzles.REDUCED_ROADS]
            self.assertCountEqual(actual, expected)
            self.assertEqual({path[0], path[-1]}, {"B", "C"})
        # An even-degree disconnected graph has no single edge-once walk.
        two_triangles = (("A", "B"), ("B", "C"), ("A", "C"),
                         ("D", "E"), ("E", "F"), ("D", "F"))
        self.assertFalse(puzzles.connected_on_roads(two_triangles))
        self.assertTrue(all(d % 2 == 0 for d in puzzles.degrees(two_triangles).values()))
        self.assertEqual(puzzles.trails(two_triangles), [])

    def test_criterion_against_every_nonempty_four_vertex_simple_graph(self):
        possible = list(itertools.combinations("ABCD", 2))
        for mask in range(1, 1 << len(possible)):
            roads = tuple(edge for i, edge in enumerate(possible) if mask >> i & 1)
            odd = sum(value % 2 for value in puzzles.degrees(roads).values())
            criterion = puzzles.connected_on_roads(roads) and odd in (0, 2)
            self.assertEqual(bool(puzzles.trails(roads)), criterion, roads)

    def test_lamp_transitions_and_all_reachable_states(self):
        all_states = {"".join(bits) for bits in itertools.product("01", repeat=5)}
        even = {state for state in all_states if state.count("1") % 2 == 0}
        actual = puzzles.reachable("00000", puzzles.LAMP_MOVES)
        self.assertEqual(len(actual), 16)
        self.assertEqual(actual, even)
        self.assertNotIn("10000", actual)
        for state in all_states:
            for move in puzzles.LAMP_MOVES:
                changed = puzzles.toggle(state, move)
                self.assertEqual(changed.count("1") % 2, state.count("1") % 2)
                self.assertEqual(puzzles.toggle(changed, move), state)
        for before, after, move in zip(puzzles.LAMP_WALK, puzzles.LAMP_WALK[1:], puzzles.LAMP_MOVES):
            self.assertEqual(puzzles.toggle(before, move), after)

    def test_removed_move_preserves_more_than_total_parity(self):
        states = puzzles.reachable("00000", puzzles.SPLIT_MOVES)
        expected = {"".join(bits) for bits in itertools.product("01", repeat=5)
                    if bits[:2].count("1") % 2 == 0 and bits[2:].count("1") % 2 == 0}
        self.assertEqual(states, expected)
        self.assertEqual(len(states), 8)
        self.assertNotIn("10100", states)
        self.assertEqual(set(itertools.chain.from_iterable(puzzles.SPLIT_MOVES)), set(range(5)))

    def test_models_reject_different_rules(self):
        for edges in ((("A", "A"),), (("A", "B"), ("B", "A"))):
            with self.assertRaises(ValueError):
                puzzles.trails(edges)
        for state, move in (("", (0, 1)), ("00102", (0, 1)),
                            ("00000", (0, 0)), ("00000", (-1, 2)),
                            ("00000", (0, 5))):
            with self.assertRaises(ValueError):
                puzzles.toggle(state, move)

    def test_diagram_and_published_example_match_models(self):
        svg = (ROOT / "assets/media/puzzle-roads.svg").read_text()
        self.assertEqual(svg, puzzles.road_svg())
        tree = ET.fromstring(svg)
        lines = tree.findall("{http://www.w3.org/2000/svg}g/{http://www.w3.org/2000/svg}line")
        self.assertEqual({line.attrib["data-road"] for line in lines},
                         {a + b for a, b in puzzles.ROADS})
        for line in lines:
            a, b = line.attrib["data-road"]
            self.assertEqual(tuple(map(int, (line.attrib["x1"], line.attrib["y1"]))), puzzles.POINTS[a])
            self.assertEqual(tuple(map(int, (line.attrib["x2"], line.attrib["y2"]))), puzzles.POINTS[b])
        text = (ROOT / "book/32-puzzles.md").read_text()
        for phrase in ("AB、AC、BC、AD、BD、CD", "B → A → C → B → D → C",
                       "00000 → 11000 → 10100 → 10010 → 10001",
                       "00000", "10000", "10100", "16", "8"):
            self.assertIn(phrase, text)
        puzzles.report()


if __name__ == "__main__":
    unittest.main()
