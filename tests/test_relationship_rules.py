"""Source/retrieval regression checks, not proof of persuasion or relationship effects."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read


class RelationshipRulesTests(unittest.TestCase):
    def test_argument_keeps_question_evidence_and_normative_claims_distinct(self):
        text = (ROOT / "essays/09-friends-not-assets.md").read_text()
        for phrase in (
            "没有利用价值，不等于没有相处价值",
            "这不是把真实朋友与真实交易伙伴随机分组",
            "每格10人", "不是交友成功率",
            "没有收到帮助", "未获显著支持",
            "不是两项实验实际检验的结果",
            "谈清一笔费用，不等于给一段友情标价",
            "关心也不要求提前替所有判断签字",
            "不是上面实验检验过的沟通疗效",
            "关系的范围可以有限",
            "不必把辛苦偷偷改名成享受",
            "不要求先把过去写坏",
        ):
            self.assertIn(phrase, text)
        rendered = build.markdown(text, "essays/09-friends-not-assets.md")
        for anchor in ("friends-not-a-service", "friends-aristotle", "friends-reciprocity",
                       "friends-hard-times", "friends-limited", "friends-ending",
                       "friends-exchange-study", "friends-clear-terms",
                       "friends-comfort-and-agreement"):
            self.assertEqual(rendered.count(f'id="{anchor}"'), 1)
        self.assertIn('href="#n39"', rendered)
        for row in ("| 交换式 | 173 | 149 |", "| 关怀式 | 156 | 191 |"):
            self.assertIn(row, text)

    def test_note_preserves_full_design_and_unsuccessful_prediction(self):
        source = "docs/evidence/B39-relationship-rules.md"
        text = (ROOT / source).read_text()
        for phrase in (
            "96名未婚男性", "80名女性", "每格24人", "每格10人",
            "另有8人", "12人", "4人", "预录影像", "多条线索同时变化",
            "不是已婚女性不能发展友情的事实",
            "未与出版社当前文件逐字比较", "没有取得原始数据",
            "p < .06", "p < .10", "不是显著下降",
            "这项预测没有得到支持",
        ):
            self.assertIn(phrase, text)
        for row in (
            "| 交换式期待 | 193 | 176 |",
            "| 关怀式期待 | 177 | 194 |",
            "| 交换式期待 | 173 | 149 | 149 | 173 |",
            "| 关怀式期待 | 156 | 191 | 179 | 177 |",
            "| 交换式期待 | 56 | 59 | 58 | 59 |",
            "| 关怀式期待 | 63 | 72 | 70 | 52 |",
        ):
            self.assertIn(row, text)
        note = next(n for n in json.loads((ROOT / "data/evidence.json").read_text())["notes"]
                    if n["id"] == "N39")
        self.assertEqual(note["text"], text)
        self.assertEqual(note["source_kind"], "study_reading_note")
        self.assertIn(text, (ROOT / "llms-full.txt").read_text())
        record = next(r for r in json.loads((ROOT / "data/research.json").read_text())["records"]
                      if r["id"] == "B39")
        self.assertEqual(record["doi"], "10.1037/0022-3514.37.1.12")
        self.assertEqual(record["verified_at"], "2026-10-01")
        self.assertEqual(record["access_level"], "full_text")
        self.assertFalse(record["directly_validates_cards"])
        self.assertIn("未测长期结果", record["fields"]["关键限制"])

    def test_full_text_route_and_card_boundary(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {d["id"]: d for d in documents}
        for identifier, source in (("E09", "essays/09-friends-not-assets.md"),
                                   ("N39", "docs/evidence/B39-relationship-rules.md")):
            raw = (ROOT / source).read_bytes()
            self.assertEqual(by_id[identifier]["text"], raw.decode())
            self.assertEqual(by_id[identifier]["source_sha256"], hashlib.sha256(raw).hexdigest())
        route = next(r for r in routes if r["id"] == "R75")
        self.assertEqual(set(route["targets"]), {"E09", "B39", "N39", "F57", "C05", "C06"})
        for identifier in route["targets"]:
            self.assertIn("[" + identifier, route["text"])
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("B39" not in c["background_ids"] for c in cards))
        excerpt = (ROOT / "README.md").read_text().split("<!-- entry-arguments:start -->")[1].split("<!-- entry-arguments:end -->")[0]
        self.assertIn("没有利用价值，不等于没有相处价值", excerpt)


if __name__ == "__main__":
    unittest.main()
