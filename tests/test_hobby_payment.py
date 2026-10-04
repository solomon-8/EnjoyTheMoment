"""Preserve the literary source limits and payment argument across exports."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import read


class HobbyPaymentTests(unittest.TestCase):
    def test_argument_keeps_payment_benefits_and_distinct_choices(self):
        text = (ROOT / "essays/05-play-is-not-performance.md").read_text()
        for phrase in (
            "钱有时买走选择，有时也让选择成为可能",
            "同一把刷子，为什么有人逃，有人付钱抢着接",
            "不是“人一收钱就失去热爱”的普遍定律",
            "不借汤姆的成功教人怎样让别人抢着替自己干活",
            "卖掉已经画完的图，与卖出未来几个周末",
            "报酬可以是让热爱继续的条件，不是热爱的反证",
            "无报酬的空间并不自动自由",
            "不保证提高价格、减少订单或另找工作",
            "不等于让每一种快乐都有义务上班",
        ):
            self.assertIn(phrase, text)
        html = (ROOT / "index.html").read_text()
        for anchor in ("amateur-payment", "amateur-tom-fence",
                       "amateur-future-order", "amateur-payment-objection"):
            self.assertEqual(text.count(f'<a id="{anchor}"></a>'), 1)
            self.assertEqual(html.count(f'id="{anchor}"'), 1)

    def test_literary_source_does_not_become_an_effect_study(self):
        note = (ROOT / "docs/evidence/F92-tom-sawyer-and-work.md").read_text()
        for phrase in ("完整核读第二章", "不是小说首版日期", "不是心理实验",
                       "没有据此宣称通读全书", "不是小说情节",
                       "不能证明“付钱一定更喜欢”", "种族化称谓"):
            self.assertIn(phrase, note)
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        record = next(x for x in notes if x["id"] == "F92")
        self.assertEqual(record["source_kind"], "literary_primary_text")
        research = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(research), 50)
        self.assertNotIn("F92", {x["id"] for x in research})
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertTrue(all("F92" not in x["background_ids"] for x in cards))

    def test_ai_retrieval_preserves_full_text_and_counterargument(self):
        documents, routes = read.load_documents(ROOT)
        documents = {x["id"]: x for x in documents}
        for ident, path in (
            ("E05", "essays/05-play-is-not-performance.md"),
            ("F92", "docs/evidence/F92-tom-sawyer-and-work.md"),
        ):
            raw = (ROOT / path).read_bytes()
            self.assertEqual(documents[ident]["text"], raw.decode())
            self.assertEqual(documents[ident]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertIn(raw.decode().strip(), (ROOT / "llms-full.txt").read_text())
        route = next(x for x in routes if x["id"] == "R47")
        self.assertIn("F92", route["targets"])
        for phrase in ("不是动机实验", "不是合同类型的法律分类",
                       "报酬支持热爱的反方", "不否定谋生需要"):
            self.assertIn(phrase, route["text"])

    def test_epub_preserves_argument_and_source_links(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            essay = z.read("EPUB/text/essays--05-play-is-not-performance.xhtml").decode()
            note = z.read("EPUB/text/docs--evidence--F92-tom-sawyer-and-work.xhtml").decode()
            self.assertIn("无报酬的空间并不自动自由", essay)
            self.assertIn("docs--evidence--F92-tom-sawyer-and-work.xhtml", essay)
            self.assertIn("essays--05-play-is-not-performance.xhtml#amateur-payment-objection",
                          note)
            self.assertIn("不是心理实验", note)


if __name__ == "__main__":
    unittest.main()
