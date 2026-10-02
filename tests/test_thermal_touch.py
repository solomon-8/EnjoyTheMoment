"""Retrieval and source-boundary guards, not evidence of reader persuasion."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read


class ThermalTouchTests(unittest.TestCase):
    def test_argument_separates_contact_preference_and_explanation(self):
        text = (ROOT / "book/02-senses.md").read_text()
        for phrase in (
            "同样温度，为什么有的东西摸起来更凉",
            "一样的初始温度，不代表一样的接触",
            "不是同一个问题", "98%", "70%", "68%",
            "一件东西的触感，不是一张材料身份证",
            "不等于已经推翻她感觉到的差别",
            "个人感受不替产品广告签字",
            "最强的反对意见", "妥协应该被说成妥协",
        ):
            self.assertIn(phrase, text)
        rendered = build.markdown(text, "book/02-senses.md")
        for anchor in (
            "senses-thermal-touch", "senses-contact-not-label",
            "senses-knowledge-and-pleasure", "senses-three-layers",
            "senses-price-expectation", "senses-blind-test", "senses-intensity",
        ):
            self.assertIn(f'id="{anchor}"', rendered)
        self.assertIn('href="#b38"', rendered)
        self.assertIn('href="#n38"', rendered)

    def test_note_distinguishes_trials_measurements_and_reading_scope(self):
        source = "docs/evidence/B38-thermal-touch.md"
        text = (ROOT / source).read_text()
        for phrase in (
            "实验2用于定位论文范围", "未完整核读其方法和结果",
            "84次是每人的试次数，不是84名参与者",
            "不要求说出材料名称或评价喜欢程度",
            "不倒推出精确作答计数", "等效检验",
            "未检出显著效应", "不证明这些线索完全没有贡献",
            "0.25℃", "1.44℃", "p = .11", "半无限体",
            "传感器贴在接触边缘", "没有取得原始数据",
            "不是本实验测试过的产品",
        ):
            self.assertIn(phrase, text)
        for row in ("| 铜—ABS | 98% |", "| 铜—青铜 | 70% |",
                    "| 青铜—不锈钢 | 68% |"):
            self.assertIn(row, text)
        note = next(n for n in json.loads((ROOT / "data/evidence.json").read_text())["notes"]
                    if n["id"] == "N38")
        self.assertEqual(note["text"], text)
        self.assertEqual(note["source_kind"], "study_reading_note")
        self.assertIn(text, (ROOT / "llms-full.txt").read_text())
        self.assertIn('href="#senses-thermal-touch"', build.markdown(text, source))

    def test_full_text_and_visible_route_targets(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {d["id"]: d for d in documents}
        for identifier, path in (
            ("C02", "book/02-senses.md"),
            ("N38", "docs/evidence/B38-thermal-touch.md"),
        ):
            raw = (ROOT / path).read_bytes()
            self.assertEqual(by_id[identifier]["text"], raw.decode())
            self.assertEqual(by_id[identifier]["source_sha256"], hashlib.sha256(raw).hexdigest())
        route = next(r for r in routes if r["id"] == "R71")
        self.assertEqual(set(route["targets"]),
                         {"C02", "B38", "N38", "B19", "N19", "B46", "N46",
                          "F05", "C14", "C16", "E04"})
        text = (ROOT / "docs/reading-map.md").read_text().split('<a id="r71"></a>')[1]
        for identifier in route["targets"]:
            self.assertIn("[" + identifier, text)
        self.assertIn("不是六物件与手原先等温", text)
        self.assertIn("不是喜欢评分", text)

    def test_new_background_does_not_change_card_claims(self):
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        record = next(r for r in records if r["id"] == "B38")
        self.assertEqual(record["doi"].lower(), "10.3758/bf03193662")
        self.assertEqual(record["verified_at"], "2026-10-01")
        self.assertEqual(record["access_level"], "full_text")
        self.assertFalse(record["directly_validates_cards"])
        self.assertIn("实验2未完整核读", record["fields"]["实际读取"])
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("B38" not in c["background_ids"] for c in cards))
        self.assertTrue(all(c["evidence_type"] == "original_proposal" for c in cards))


if __name__ == "__main__":
    unittest.main()
