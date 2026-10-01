"""Guards for source boundaries and retrieval, not proof of reader persuasion."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read


class RepeatedExperienceTests(unittest.TestCase):
    def test_chapter_retains_the_actual_disagreement(self):
        text = (ROOT / "book/03-novelty.md").read_text()
        for phrase in (
            "同样的快乐，为什么一到第二次就像贬值了",
            "实际重看确实比首看低", "下降没有预测得那么陡",
            "两组不同的人", "| 58名预测者 | 5.29 | 预测重看：3.47 |",
            "| 62名实际重看者 | 5.40 | 实际重看：4.52 |",
            "没有安排第二轮观看", "并未实际扣款",
            "最强的反对意见", "机会的期限", "共同选择的冲突",
            "重复本身也不必靠产生新发现来辩护",
            "不是永远更新，也不是永远忍住",
        ):
            self.assertIn(phrase, text)
        html = build.markdown(text, "book/03-novelty.md")
        for link in ('href="#b37"', 'href="#n37"'):
            self.assertIn(link, html)
        for identifier in ("novelty-repeat", "novelty-intensity", "novelty-cube",
                           "novelty-learning", "novelty-uncertainty"):
            self.assertIn('id="' + identifier + '"', html)

    def test_source_design_and_uncertainties_survive_export(self):
        text = (ROOT / "docs/evidence/B37-repeat-experiences.md").read_text()
        for phrase in (
            "不表示逐字审核全部七项研究", "未与出版社当前版本逐字比对",
            "没有下载数据文件或重新分析", "58人", "62人",
            "−1.83与−0.89", "−1.82与−0.88", "文字与数字不一致",
            "整个观看过程", "未检出差异不是等效证明",
            "201人", "177人", "163人", "75人", "1人报2美元",
            "没有实际扣款，也没有第二轮观看结果",
            "不是对全部动机的中性、完整测量",
        ):
            self.assertIn(phrase, text)
        for row in ("| 预测重复 | 205 | 5.92 |", "| 预测新片 | 196 | 6.40 |",
                    "| 实际重复 | 198 | 6.24 |", "| 实际新片 | 204 | 6.28 |"):
            self.assertIn(row, text)
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        note = next(n for n in notes if n["id"] == "N37")
        self.assertEqual(note["text"], text)
        self.assertEqual(note["source_kind"], "study_reading_note")
        self.assertIn(text, (ROOT / "llms-full.txt").read_text())

    def test_full_retrieval_and_visible_route_targets(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {r["id"]: r for r in documents}
        for identifier, path in (
            ("C03", "book/03-novelty.md"),
            ("N37", "docs/evidence/B37-repeat-experiences.md"),
        ):
            raw = (ROOT / path).read_bytes()
            self.assertEqual(by_id[identifier]["text"], raw.decode())
            self.assertEqual(by_id[identifier]["source_sha256"], hashlib.sha256(raw).hexdigest())
        route = next(r for r in routes if r["id"] == "R69")
        self.assertEqual(set(route["targets"]), {"C03", "B37", "N37", "C12", "C13", "C22", "E04"})
        route_text = (ROOT / "docs/reading-map.md").read_text().split('<a id="r69"></a>')[1]
        for identifier in route["targets"]:
            self.assertIn("[" + identifier, route_text)
        for phrase in ("实际也有下降", "不是等效证明", "没有扣款或第二轮观看",
                       "不能逐人判错", "共同选择与真实厌倦"):
            self.assertIn(phrase, route_text)

    def test_research_is_not_card_validation(self):
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        record = next(r for r in records if r["id"] == "B37")
        self.assertEqual(record["doi"], "10.1037/pspa0000147")
        self.assertEqual(record["verified_at"], "2026-10-01")
        self.assertEqual(record["access_level"], "full_text")
        self.assertFalse(record["directly_validates_cards"])
        self.assertIn("不是全部七项研究逐字审核", record["fields"]["实际读取"])
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("B37" not in card["background_ids"] for card in cards))
        self.assertTrue(all(card["evidence_type"] == "original_proposal" for card in cards))


if __name__ == "__main__":
    unittest.main()
