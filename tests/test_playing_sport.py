"""Validate C38's source, finite examples and retrieval, not its pleasure value."""
import hashlib
from itertools import product
import json
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read
import table_tennis_examples as tt


class PlayingSportTests(unittest.TestCase):
    def test_opening_service_sequence_and_lets(self):
        game = tt.first_game("ALBABABL")
        self.assertEqual([row["server"] for row in game["events"]],
                         ["A1", "A1", "A1", "B1", "B1", "A2", "A2", "B2"])
        self.assertEqual(game["score"], [3, 3])
        self.assertEqual(game["next_pair"], ("B2", "A1"))
        self.assertIsNone(game["winner"])
        self.assertEqual(tt.HIT_ORDER, ("A1", "B1", "A2", "B2"))
        # The names happen to cycle in the same order; the unit differs.
        self.assertEqual(tuple(a for a, _ in tt.PAIRS), tt.HIT_ORDER)
        ordinary = tt.first_game("ABAB")
        self.assertNotEqual(tuple(row["server"] for row in ordinary["events"]), tt.HIT_ORDER)

    def test_deuce_switches_every_counted_point_not_every_event(self):
        game = tt.first_game("AB" * 10 + "ALBLAA")
        self.assertEqual([row["server"] for row in game["events"][20:]],
                         ["A2", "B2", "B2", "A1", "A1", "B1"])
        self.assertEqual(game["score"], [13, 11])
        self.assertEqual(game["winner"], "A")
        self.assertIsNone(game["next_pair"])
        self.assertIsNone(tt.first_game("AB" * 10 + "A")["winner"])
        self.assertEqual(tt.first_game("AB" * 10 + "AA")["score"], [12, 10])

    def test_order_is_independent_of_point_winners_before_completion(self):
        for winners in product("AB", repeat=8):
            game = tt.first_game("".join(winners))
            self.assertEqual(game["next_pair"], ("A1", "B1"))
            self.assertEqual([row["server"] for row in game["events"]],
                             ["A1", "A1", "B1", "B1", "A2", "A2", "B2", "B2"])

    def test_invalid_input_and_postgame_events_are_not_silently_accepted(self):
        for value in (None, [], "AXB", "A" * 11 + "B", "B" * 11 + "L"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                tt.first_game(value)

    def test_appearances_do_not_claim_complete_round_robin_or_equal_time(self):
        data = tt.examples()
        self.assertEqual(data["winner_stays"], dict(A=6, B=2, C=1, D=1, E=1, F=1))
        self.assertEqual(data["two_rounds"], dict.fromkeys("ABCDEF", 2))
        self.assertEqual(sum(data["two_rounds"].values()), 12)
        self.assertEqual(data["round_robin_games"], 15)
        self.assertEqual(data["round_robin"], dict.fromkeys("ABCDEF", 5))
        for fixtures in (["AA"], ["AG"], ["ABC"], [None]):
            with self.assertRaises(ValueError):
                tt.participation(fixtures)

    def test_chapter_preserves_rules_original_example_and_value_boundaries(self):
        source = "book/38-playing-sport.md"
        text = (ROOT / source).read_text()
        for phrase in ("一起续回合", "轮椅", "10比10", "20分", "非决胜局",
                       "十二个人次", "15场", "不是完整单循环", "让分、让球、让出场地",
                       "最强的反对意见", "不是真实参与记录", "不提供统一的让分数值"):
            self.assertIn(phrase, text)
        self.assertNotIn("<!-- pick:", text)
        rendered = build.markdown(text, source)
        self.assertIn('href="#f73"', rendered)
        self.assertIn('href="#f74"', rendered)
        self.assertEqual(rendered.count("<table>"), 2)
        self.assertEqual(rendered.count("<figure"), 1)

    def test_sources_and_reading_route_are_full_and_not_new_studies(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {item["id"]: item for item in documents}
        for identifier, source in (
            ("C38", "book/38-playing-sport.md"),
            ("F73", "docs/evidence/F73-table-tennis-laws.md"),
            ("F74", "docs/evidence/F74-social-table-tennis.md"),
        ):
            self.assertEqual(by_id[identifier]["text"], (ROOT / source).read_text())
            self.assertEqual(by_id[identifier]["source_sha256"],
                             hashlib.sha256((ROOT / source).read_bytes()).hexdigest())
        route = next(r for r in routes if r["id"] == "R73")
        self.assertEqual(set(route["targets"]),
                         {"C38", "F73", "F74", "C04", "C05", "C28", "E02", "E05"})
        for phrase in ("2026-01-01", "274页", "41—45页", "Jul-2026", "2.8.3",
                       "Vimeo教学视频", "主站目录当次访问403", "不因文件成功下载就宣称已穷尽最新版本"):
            self.assertIn(phrase, by_id["F73"]["text"])
        for phrase in ("玻璃物品", "没有招募参与者", "次数不等于", "15场"):
            if phrase == "次数不等于":
                self.assertIn(phrase, route["text"])
            else:
                self.assertIn(phrase, by_id["F74"]["text"])
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(records), 43)
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertFalse(any("F73" in c["background_ids"] or "F74" in c["background_ids"]
                             for c in cards))
        chapter = next(c for c in json.loads((ROOT / "data/chapters.json").read_text())["chapters"]
                       if c["id"] == "C38")
        self.assertEqual(chapter["scope"], "full_chapter")
        self.assertEqual(chapter["card_ids"], [])

    def test_original_diagram_has_text_alternative_and_fixed_dimensions(self):
        svg = ROOT / "assets/media/table-tennis-order.svg"
        tree = ET.parse(svg).getroot()
        self.assertEqual(tree.attrib["viewBox"], "0 0 400 840")
        ns = "{http://www.w3.org/2000/svg}"
        self.assertIn("不是站位或跑动图", tree.find(ns + "desc").text)
        png = (ROOT / "assets/media/table-tennis-order.png").read_bytes()
        self.assertEqual(int.from_bytes(png[16:20], "big"), 800)
        self.assertEqual(int.from_bytes(png[20:24], "big"), 1680)
        self.assertIn("table-tennis-order.svg", (ROOT / "assets/media/README.md").read_text())


if __name__ == "__main__":
    unittest.main()
