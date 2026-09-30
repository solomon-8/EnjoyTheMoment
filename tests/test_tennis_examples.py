import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import tennis_examples as tennis


class TennisExampleTests(unittest.TestCase):
    def test_original_match_has_fewer_points_and_games_but_more_sets(self):
        sequences = tennis.example_sequences()
        result = tennis.best_of_three(sequences)
        self.assertEqual([len(s) for s in sequences], [6, 10, 10])
        self.assertEqual(sum(len(g) for s in sequences for g in s), 128)
        self.assertEqual(result["winner"], "A")
        self.assertEqual(result["sets"], [2, 1])
        self.assertEqual(result["games"], [12, 14])
        self.assertEqual(result["points"], [48, 80])
        self.assertEqual([s["games"] for s in result["by_set"]],
                         [[0, 6], [6, 4], [6, 4]])
        self.assertEqual([s["points"] for s in result["by_set"]],
                         [[0, 24], [24, 28], [24, 28]])
        # Compute raw totals independently of the hierarchical scorer.
        raw = "".join(g for s in sequences for g in s)
        self.assertEqual([raw.count("A"), raw.count("B")], [48, 80])
        # The text's AABBAA / BBBB game choices do not imply a serve model.
        self.assertEqual([g for s in sequences for g in s].count("AABBAA"), 12)

    def test_standard_deuce_can_repeat_but_no_extra_points_after_a_game(self):
        result = tennis.standard_game("AAABBBABAA")
        self.assertEqual(result, {"winner": "A", "points": [6, 4]})
        for sequence in ("", "AAABBB", "AAABBBA", "AABB", "AAAAX", "AAAAB"):
            with self.subTest(sequence=sequence), self.assertRaises(ValueError):
                tennis.standard_game(sequence)
        self.assertEqual(tennis.standard_game("AABBAA")["points"], [4, 2])

    def test_no_games_or_sets_added_after_the_earliest_legal_end(self):
        a, b = "AAAA", "BBBB"
        for sequences in ([a] * 6 + [b], [a, b] * 6 + [a, a], [a] * 5):
            with self.subTest(sequences=sequences), self.assertRaises(ValueError):
                tennis.ordinary_set(sequences)
        # At 5-5, two games can finish 7-5; at 6-6 a different procedure is needed.
        self.assertEqual(tennis.ordinary_set([a, b] * 5 + [a, a])["games"], [7, 5])
        with self.assertRaises(ValueError):
            tennis.best_of_three(([a] * 6, [a] * 6, [b] * 6))
        with self.assertRaises(ValueError):
            tennis.best_of_three(([a] * 6,))

    def test_prose_source_and_route_preserve_format_and_evidence_limits(self):
        chapter = (ROOT / "book/28-watching-sport.md").read_text()
        note = (ROOT / "docs/evidence/F64-tennis-scoring.md").read_text()
        for phrase in ("48 分", "80 分", "12∶14", "48∶80",
                       "甲、乙、甲、乙、甲、乙、甲、乙、甲、甲",
                       "局部重新开始", "不能替运动员选下一步", "不是所有比赛"):
            self.assertIn(phrase, chapter)
        for phrase in ("212", "2026-10-01", "18–19／6–7", "36–37／24–25",
                       "2025 edition", "拦截 HTML", "没有收集真实观赛体验",
                       "不是通用网球裁判程序", "替代决胜整盘"):
            self.assertIn(phrase, note)
        notes = {n["id"]: n for n in json.loads((ROOT / "data/evidence.json").read_text())["notes"]}
        self.assertEqual(notes["F64"]["text"], note)
        self.assertEqual(notes["F64"]["source_kind"], "official_sport_rules")
        chapters = json.loads((ROOT / "data/chapters.json").read_text())["chapters"]
        self.assertEqual(next(c for c in chapters if c["id"] == "C28")["text"], chapter.strip())
        routes = json.loads((ROOT / "data/reading-map.json").read_text())["routes"]
        self.assertEqual(set(next(r for r in routes if r["id"] == "R59")["targets"]),
                         {"C28", "C04", "C19", "F18", "F19", "F64"})
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(records), 30)
        self.assertNotIn("F64", {r["id"] for r in records})


if __name__ == "__main__":
    unittest.main()
