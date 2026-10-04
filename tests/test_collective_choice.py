"""Protect source limits and the distinction between individual and shared choice."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import read


class CollectiveChoiceTests(unittest.TestCase):
    def test_argument_keeps_the_counterargument_and_costs(self):
        text = (ROOT / "essays/10-pleasure-not-retention.md").read_text()
        for phrase in (
            "退出按钮很好找，朋友却都还在里面",
            "在现有安排里选择留下，都不自动等于希望这套安排一直存在",
            "她比较的可能是", "也要认真听他的“我喜欢”",
            "没有实施大规模共同停用", "不能代表全部用户",
            "数字来自研究的报价区间及估值方法，不是快乐分数",
            "不能互相替代", "不能仅凭存在这种依赖",
            "为什么你的不喜欢就比我的喜欢更重要",
            "谁维护两个入口", "不是经过研究验证的等价替代",
            "可以留下却继续批评安排", "不能用多数人的估值替少数人签字",
        ):
            self.assertIn(phrase, text)
        for anchor in ("digital-shared-exit", "digital-collective-study",
                       "digital-shared-disagreement"):
            self.assertEqual(text.count(f'<a id="{anchor}"></a>'), 1)
            self.assertEqual((ROOT / "index.html").read_text().count(
                f'id="{anchor}"'), 1)

    def test_new_source_is_not_a_deactivation_outcome_or_card_validation(self):
        note = (ROOT / "docs/evidence/B50-collective-traps.md").read_text()
        for phrase in (
            "大规模共同停用未实施", "没有观察到这些人已经掏出这些金额", "371名活跃用户",
            "235名活跃用户", "2023年7月", "2023年8–9月",
            "女性占比较高", "未指定后来采用", "60%、46%",
            "Instagram中位数仍为正10美元", "概率较低",
            "不够证明产品市场陷阱", "没有验证永久共同退出能否持续",
            "不是要求决定者为全校支付补偿",
        ):
            self.assertIn(phrase, note)
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        record = next(r for r in records if r["id"] == "B50")
        self.assertEqual(record["doi"], "10.1257/aer.20231468")
        self.assertEqual(record["access_level"], "full_text")
        self.assertFalse(record["directly_validates_cards"])
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertTrue(all("B50" not in c["background_ids"] for c in cards))

    def test_ai_route_keeps_full_text_and_local_limits(self):
        documents, routes = read.load_documents(ROOT)
        documents = {d["id"]: d for d in documents}
        for ident, path in (
            ("E10", "essays/10-pleasure-not-retention.md"),
            ("N50", "docs/evidence/B50-collective-traps.md"),
        ):
            raw = (ROOT / path).read_bytes()
            self.assertEqual(documents[ident]["text"], raw.decode())
            self.assertEqual(documents[ident]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertIn(raw.decode().strip(), (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R82")
        self.assertEqual(set(route["targets"]),
                         {"E10", "B50", "N50", "B28", "N28", "B14", "N14", "F20"})
        for phrase in ("大规模共同停用未实施", "不是幸福分数或实际付款",
                       "不能据此确认平台意图", "均不验证行动卡"):
            self.assertIn(phrase, route["text"])
        common = next(r for r in routes if r["id"] == "R29")
        self.assertTrue({"B50", "N50"} <= set(common["targets"]))

    def test_epub_preserves_argument_and_reciprocal_sources(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            essay = z.read("EPUB/text/essays--10-pleasure-not-retention.xhtml").decode()
            note = z.read("EPUB/text/docs--evidence--B50-collective-traps.xhtml").decode()
            self.assertIn("没有实施大规模共同停用", essay)
            self.assertIn("docs--evidence--B50-collective-traps.xhtml", essay)
            self.assertIn("essays--10-pleasure-not-retention.xhtml#digital-shared-disagreement",
                          note)
            self.assertIn("谁维护两个入口", essay)


if __name__ == "__main__":
    unittest.main()
