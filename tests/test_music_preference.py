"""Guards for the published reading, not a replication of participant data."""

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build


class MusicPreferenceTests(unittest.TestCase):
    def test_original_period_examples_are_arithmetic_not_sound_evaluations(self):
        text = (ROOT / "book/11-music.md").read_text()
        for low, high, denominator, cycles in (
                (220, 330, 110, (2, 3)), (220, 440, 220, (1, 2))):
            period = Fraction(1, denominator)
            self.assertEqual((low * period, high * period), cycles)
        self.assertEqual(Fraction(330, 220), Fraction(3, 2))
        self.assertEqual(Fraction(440, 220), 2)
        tempered = 2 ** Fraction(7, 12)
        self.assertAlmostEqual(tempered, 1.4983, places=4)
        self.assertNotEqual(tempered, 1.5)
        for marker in ("220 与 330 Hz", "220 与 440 Hz", "1/110", "1/220",
                       "不是精确的 1.5", "没有播放声音", "也不是实验配方"):
            self.assertIn(marker, text)

    def test_sample_arithmetic_does_not_turn_groups_into_independent_studies(self):
        self.assertEqual(145 - 19 - 19, 107)
        self.assertEqual(52 + 55, 107)
        self.assertEqual(sum((107, 26, 42, 28, 32)), 235)
        self.assertEqual(65 + 34, 99)
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(records), 47)
        record = next(r for r in records if r["id"] == "B31")
        self.assertEqual(record["verified_at"], "2026-10-01")
        self.assertEqual(record["access_level"], "full_text")
        self.assertFalse(record["directly_validates_cards"])
        for marker in ("145人筛后107人", "52/55", "非纵向追踪", "2018–2024"):
            self.assertIn(marker, record["fields"]["设计与对象"])
        self.assertIn("非随机文化干预", record["fields"]["设计与对象"])
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertTrue(all("B31" not in c["background_ids"] for c in cards))

    def test_within_group_and_interaction_results_remain_separate(self):
        text = (ROOT / "docs/evidence/B31-consonance-and-culture.md").read_text()
        expected = (
            "| 协和／不协和音程 | p = .03／.32 | F(1,105) = 1.05，p = .31 |",
            "| 协和／不协和和弦 | p = .04／.09 | F(1,105) = 0.28，p = .60 |",
            "| 谐波／非谐波复合音 | p < .001／.19 | F(1,105) = 13.7，p = .0003 |",
        )
        for row in expected:
            self.assertIn(row, text)
        for marker in ("不能单独成为交互的证据", "第三项的显著性不能移植",
                       "两组组内均p > .60", "403", "未下载原始数据",
                       "平均年龄及标准差配置相反", "最终分析28人",
                       "听力排除条件", "不擅改p值", "不是本书生成／试听的音频"):
            self.assertIn(marker, text)

    def test_full_text_and_routes_preserve_provenance_and_original_boundaries(self):
        note_path = ROOT / "docs/evidence/B31-consonance-and-culture.md"
        text = note_path.read_text()
        note = next(n for n in json.loads((ROOT / "data/evidence.json").read_text())["notes"]
                    if n["id"] == "N31")
        self.assertEqual(note["source_kind"], "study_reading_note")
        self.assertEqual(note["text"], text)
        retrieved = json.loads(subprocess.check_output(
            [sys.executable, "tools/read.py", "--id", "N31"], cwd=ROOT))
        self.assertTrue(retrieved["complete"])
        self.assertEqual(retrieved["record"]["text"], text)
        self.assertEqual(retrieved["record"]["source_sha256"],
                         hashlib.sha256(note_path.read_bytes()).hexdigest())
        chapter_path = ROOT / "book/11-music.md"
        chapter = next(c for c in json.loads((ROOT / "data/chapters.json").read_text())["chapters"]
                       if c["id"] == "C11")
        self.assertEqual(chapter["text"], chapter_path.read_text().strip())
        html = build.markdown(chapter_path.read_text(), "book/11-music.md")
        self.assertEqual(html.count('src="data:image/png;base64,'), 2)
        self.assertEqual(len(re.findall(r"(?m)(?:^\|.*\n)+", chapter_path.read_text())), 4)
        self.assertEqual(build.local_href("../docs/evidence/B31-consonance-and-culture.md",
                                         "book/11-music.md"), "#n31")
        routes = json.loads((ROOT / "data/reading-map.json").read_text())["routes"]
        self.assertEqual(set(next(r for r in routes if r["id"] == "R60")["targets"]),
                         {"C11", "C14", "C33", "B31", "N31", "F02", "F15"})
        for marker in ("喜欢有来历，不等于喜欢是假的", "不是先进与落后",
                       "也不意味着最后必须统一口味"):
            self.assertIn(marker, chapter["text"])


if __name__ == "__main__":
    unittest.main()
