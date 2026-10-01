"""Source/retrieval contracts, not replication, comprehension or attention evidence."""
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


class AftertastePeakTests(unittest.TestCase):
    def test_chapter_retains_design_and_value_boundaries(self):
        text = (ROOT / "book/10-aftertaste.md").read_text()
        for phrase in (
            "DVD送达前", "没有“先泡泡糖、后巧克力”组",
            "没有随机操纵事件边界", "看后重建", "44.3%和44.2%",
            "不是一个“成功改造结尾”的因果实验",
            "好结尾可以是这次经历的理由，不能成为坏过程的赦免",
            "回忆不是附带的假货", "没有一项验证下面卡片的动作"):
            self.assertIn(phrase, text)
        for anchor in (
            "aftertaste-three-questions", "aftertaste-preference",
            "aftertaste-story", "aftertaste-memory", "aftertaste-gifts",
            "aftertaste-one-episode", "aftertaste-peak-boundary",
            "aftertaste-not-a-score", "aftertaste-memory-objection"):
            self.assertIn('id="' + anchor + '"', text)
        self.assertEqual(re.findall(r'<!-- pick: .*?"id":"(J\d+)"', text),
                         ["J055", "J056", "J057", "J058", "J059", "J060"])
        self.assertEqual(build.markdown(text, "book/10-aftertaste.md").count("<table>"), 3)

    def test_gift_results_do_not_become_experienced_utility(self):
        note = (ROOT / "docs/evidence/B34-gifts-and-endings.md").read_text()
        for phrase in (
            "104人", "排除4人", "分析100人", "随后才送达DVD",
            "| A | 29 | 5.21 |", "| A+B | 21 | 4.14 |",
            "| B+A | 17 | 4.82 |", "p = .045", "没有B+A组",
            "least pleased", "neutral", "没有随机操纵事件边界",
            "未据此宣称CC BY", "没有开展参与者实验"):
            self.assertIn(phrase, note)

    def test_vr_measurement_and_conflicting_results(self):
        note = (ROOT / "docs/evidence/B35-complex-experience-and-memory.md").read_text()
        for phrase in (
            "40名Tilburg大学一年级学生", "13分14秒", "14分26秒",
            "平均间隔8.70天", "先给整体体验", "没有观看时实时连续评分",
            "每秒快乐的积分", "α = .006", "α = .007",
            "| 峰终平均peak-end | .099 / .049 | .291 / < .001 |",
            "| average | .472 | .443 |", "| peak-end | .265 | .442 |",
            "只差0.1个百分点", "F = .087", "未观看XSTNCE影片",
            "没有随机比较一组", "Samsung提供Gear VR"):
            self.assertIn(phrase, note)

    def test_canonical_fulltext_hashes_and_backlinks(self):
        for identifier, path, anchor in (
            ("C10", "book/10-aftertaste.md", None),
            ("N34", "docs/evidence/B34-gifts-and-endings.md", "aftertaste-gifts"),
            ("N35", "docs/evidence/B35-complex-experience-and-memory.md", "aftertaste-peak-boundary")):
            result = json.loads(subprocess.check_output(
                [sys.executable, "tools/read.py", "--id", identifier], cwd=ROOT))
            self.assertTrue(result["complete"])
            self.assertEqual(result["record"]["text"], (ROOT / path).read_text())
            self.assertEqual(result["record"]["source_sha256"],
                             hashlib.sha256((ROOT / path).read_bytes()).hexdigest())
            self.assertIn("R65", {r["id"] for r in result["reading_guidance"]})
            if anchor:
                html = build.markdown(result["record"]["text"], path)
                self.assertIn('href="#' + anchor + '"', html)

    def test_route_and_registry_do_not_validate_cards(self):
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(notes), 112)
        self.assertEqual(len(records), 38)
        studies = {r["id"]: r for r in records}
        for identifier, doi in (
            ("B34", "10.3758/PBR.15.1.96"),
            ("B35", "10.3389/fpsyg.2019.01705")):
            self.assertEqual(studies[identifier]["doi"], doi)
            self.assertFalse(studies[identifier]["directly_validates_cards"])
        for note in (n for n in notes if n["id"] in {"N34", "N35"}):
            self.assertEqual(note["source_kind"], "study_reading_note")
        routes = json.loads((ROOT / "data/reading-map.json").read_text())["routes"]
        route = next(r for r in routes if r["id"] == "R65")
        self.assertEqual(set(route["targets"]),
                         {"C10", "B34", "N34", "B35", "N35", "B18", "N18", "C09", "C13", "E03"})
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all(not {"B34", "B35", "N34", "N35"} & set(c["background_ids"]) for c in cards))


if __name__ == "__main__":
    unittest.main()
