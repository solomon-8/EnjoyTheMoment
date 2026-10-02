"""Arithmetic, compatibility and export checks, not evidence of persuasion."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read


class PurchaseEditorialTests(unittest.TestCase):
    def test_purchase_order_table_keeps_equal_outcome_counts(self):
        text = (ROOT / "book/06-spending.md").read_text()
        section = text.split('<a id="spending-learning"></a>', 1)[1].split(
            '### “花钱督促自己”', 1)[0]
        rows = [line for line in section.splitlines()
                if line.startswith("| ") and "＝" in line]
        self.assertEqual(len(rows), 3)
        actual = []
        for row in rows:
            cells = row.strip("|").split("|")
            actual.append(tuple(int(re.search(r"＝(\d+)元", cell).group(1))
                                for cell in cells[1:]))
        single, card, travel = 40, 240, 12
        expected = [
            (card + travel, card + travel * 10),
            (single + travel, single * 10 + travel * 10),
            (single + travel, single + card + travel * 10),
        ]
        self.assertEqual(actual, expected)
        self.assertEqual(expected[0][0] - expected[2][0], 200)
        self.assertEqual(expected[2][1] - expected[0][1], 40)
        self.assertEqual(expected[1][1] - expected[2][1], 120)
        for phrase in ("所有方式下都允许不喜欢就停止", "单次费用不能抵扣卡费",
                       "剩余次数在比较结束后没有用途", "本例没有给出概率",
                       "第一次并不能代表后面九次"):
            # Preserve assumptions alongside the calculation, not in a
            # separately retrieved caveat; these are not empirical findings.
            self.assertIn(phrase, section)

    def test_old_and_new_purchase_fragments_resolve_once(self):
        reader = (ROOT / "index.html").read_text()
        for source, anchors in (
            ("essays/04-buying-pleasure.md",
             ("purchase-work-label", "purchase-owning", "purchase-substitute",
              "purchase-claim", "purchase-shared", "purchase-options",
              "purchase-authorship", "purchase-uncertainty", "purchase-objections",
              "当购买本身成了唯一好玩的部分")),
            ("book/06-spending.md", ("spending-learning", "spending-pass-arithmetic",
                                     "spending-theatre-study", "spending-future-cost")),
        ):
            rendered = build.markdown((ROOT / source).read_text(), source)
            for anchor in anchors:
                with self.subTest(anchor=anchor):
                    self.assertEqual(rendered.count('id="' + anchor + '"'), 1)
                    self.assertEqual(reader.count('id="' + anchor + '"'), 1)
                    self.assertEqual(build.local_href(source + "#" + anchor, "README.md"),
                                     "#" + anchor)

    def test_full_text_keeps_arguments_objections_and_routes_together(self):
        documents, routes = read.load_documents(ROOT)
        documents = {document["id"]: document for document in documents}
        routes = {route["id"]: route for route in routes}
        full = (ROOT / "llms-full.txt").read_text()
        for identifier, source in (("C06", "book/06-spending.md"),
                                   ("E04", "essays/04-buying-pleasure.md")):
            data = (ROOT / source).read_bytes()
            self.assertEqual(documents[identifier]["text"], data.decode())
            self.assertEqual(documents[identifier]["source_sha256"],
                             hashlib.sha256(data).hexdigest())
            # Chapters are split into prose and cards in the combined export.
            prose = data.decode().partition('<a id="j')[0].strip()
            self.assertTrue(prose in full, identifier + " prose missing from full export")
        self.assertIn("必要工作投入可以优先", routes["R46"]["text"])
        self.assertIn("不以高频使用作唯一成功标准", routes["R46"]["text"])
        self.assertIn("该推演不是B20的实证结果", routes["R10"]["text"])
        self.assertIn("#spending-learning", routes["R10"]["text"])
        self.assertIn("#purchase-work-label", routes["R46"]["text"])
        self.assertIn("#purchase-owning", routes["R46"]["text"])
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual([card["id"] for card in cards if card["chapter_id"] == "06"],
                         ["J031", "J032", "J033", "J034", "J035", "J036"])

    def test_original_scenarios_do_not_become_research_records(self):
        research = json.loads((ROOT / "data/research.json").read_text())["records"]
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        for item in research + notes:
            self.assertNotIn(item["source"], ("book/06-spending.md",
                                              "essays/04-buying-pleasure.md"))
        essay = (ROOT / "essays/04-buying-pleasure.md").read_text()
        work = essay.split('<a id="purchase-work-label"></a>', 1)[1].split(
            "\n### “反消费主义”", 1)[0]
        self.assertIn("虚构情境", work)
        self.assertIn("最有力的反对", work)
        self.assertIn("不替现实困难排预算", work)
