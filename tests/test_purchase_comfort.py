"""Guard source scope and argument availability, not reader persuasion."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import read

ESSAY = "essays/04-buying-pleasure.md"
NOTE = "docs/evidence/F93-materialism-and-a-purchase.md"


class PurchaseComfortTests(unittest.TestCase):
    def test_comfort_is_not_a_cure_or_an_automatic_acquittal(self):
        text = (ROOT / ESSAY).read_text()
        for phrase in (
            "没有修好坏消息，不等于没给这个晚上增加任何好东西",
            "这里的舒服是情境写定的结果",
            "认可局部所得，与宣布全部满意",
            "不是论文全文",
            "不是同一个问题",
            "没有替后面的每一次预付理由",
            "没有一种统一次数",
            "安慰不必根治问题，安慰也不能被拿来否认问题",
            "不能仅凭收下礼物或露出笑容",
            "她可以说“这个礼物我很喜欢，那件事我仍然想谈”",
            "不替具体关系判赔偿",
        ):
            self.assertIn(phrase, text)
        html = (ROOT / "index.html").read_text()
        for anchor in (
            "purchase-comfort", "purchase-comfort-evidence",
            "purchase-comfort-objection", "purchase-comfort-accountability",
        ):
            self.assertEqual(text.count(f'<a id="{anchor}"></a>'), 1)
            self.assertEqual(html.count(f'id="{anchor}"'), 1)

    def test_abstract_is_not_counted_as_a_full_paper_or_card_validation(self):
        text = (ROOT / NOTE).read_text()
        for phrase in (
            "仅摘要，未取得主文", "不是全文审读",
            "259个独立样本", "753个效应量", "Copyright not evaluated",
            "不计入B系列已核读主文研究", "不验证购物疗法",
        ):
            self.assertIn(phrase, text)
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        note = next(x for x in notes if x["id"] == "F93")
        self.assertEqual(note["source_kind"], "author_abstract_only")
        research = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(research), 50)
        self.assertNotIn("F93", {x["id"] for x in research})
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertTrue(all("F93" not in x["background_ids"] for x in cards))

    def test_full_retrieval_keeps_the_objection_and_local_source_limit(self):
        documents, routes = read.load_documents(ROOT)
        documents = {x["id"]: x for x in documents}
        for identifier, path in [("E04", ESSAY), ("F93", NOTE)]:
            raw = (ROOT / path).read_bytes()
            self.assertEqual(documents[identifier]["text"], raw.decode())
            self.assertEqual(
                documents[identifier]["source_sha256"],
                hashlib.sha256(raw).hexdigest(),
            )
            self.assertIn(raw.decode().strip(), (ROOT / "llms-full.txt").read_text())
        route = next(x for x in routes if x["id"] == "R46")
        self.assertIn("F93", route["targets"])
        for phrase in (
            "仅核读作者摘要", "不承诺购物疗愈",
            "不由一次愉快担保以后每次合理", "未同意结清争议",
        ):
            self.assertIn(phrase, route["text"])

    def test_epub_preserves_bidirectional_source_links(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            essay = archive.read(
                "EPUB/text/essays--04-buying-pleasure.xhtml"
            ).decode()
            note = archive.read(
                "EPUB/text/docs--evidence--F93-materialism-and-a-purchase.xhtml"
            ).decode()
        self.assertIn("不是论文全文", essay)
        self.assertIn("docs--evidence--F93-materialism-and-a-purchase.xhtml", essay)
        self.assertIn(
            "essays--04-buying-pleasure.xhtml#purchase-comfort-accountability",
            note,
        )
        self.assertIn("不验证购物疗法", note)


if __name__ == "__main__":
    unittest.main()
