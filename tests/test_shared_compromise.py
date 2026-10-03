"""Fidelity checks for C05, not evidence of persuasion or comprehension."""
import hashlib
import json
import re
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check
import read

SOURCE = "book/05-connection.md"
STRUCTURE = ("connection-experience", "connection-wishes", "connection-arrangements", "connection-ending")
ARGUMENTS = ("connection-compromise", "connection-compromise-objection")
OLD_ANCHORS = ("05--关系不是人脉", "connection-shared-attention", "connection-amplification", "connection-distance", "connection-difference", "connection-not-a-tool")


class SharedCompromiseTests(unittest.TestCase):
    def test_four_argument_lines_precede_optional_cards(self):
        text = (ROOT / SOURCE).read_text()
        headings = re.findall(r"^## (.+)$", text, re.M)
        self.assertEqual(len(headings), 5)
        self.assertTrue(headings[-1].startswith("配套："))
        positions = [text.index('id="' + anchor + '"') for anchor in STRUCTURE]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(positions[-1], text.index('id="j025"'))
        for anchor in STRUCTURE + ARGUMENTS + OLD_ANCHORS:
            self.assertIn(anchor, check.anchors_for(text))
        for anchor in ("connection-shared-attention", "connection-amplification", "connection-not-a-tool"):
            self.assertIn("](#" + anchor + ")", text)
        for phrase in ("同样喜欢你，也可以不喜欢你推荐的东西", "人均消费之外，还藏着另一张账单", "惊喜加人，可能已经换了一场相处", "亲密不靠一种标准气氛来证明"):
            self.assertIn(phrase, text)

    def test_willingness_is_not_identical_enjoyment_or_a_permanent_assignment(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in ("继续这个原创假想", "也确实可以不去", "没有因此挪用共同资金或耽误已有约定", "愿意为你让一步，也不必被改名为我其实最喜欢", "小然更兴奋，也不能代替阿树对自己那部分作决定", "一句“我愿意”本身不足以", "拒绝被怎样对待", "一次自愿，不是永久分工", "长期不对称，也不能只凭次数宣布谁必然受委屈", "轮流忍完两晚没有凭空产生共同乐趣", "不是无损替代", "不把愿意迁就叫作不会享乐", "不把不愿迁就叫作不会做人"):
            self.assertIn(phrase, text)
        for link in ("../essays/01-pleasure-is-an-end.md#pleasure-consent-scope", "../essays/05-play-is-not-performance.md#amateur-changing-group"):
            self.assertIn(link, text)
        self.assertEqual(text.count("<!-- pick:"), 6)
        self.assertIn("不是四档亲密排行榜", text)
        self.assertIn("注意力是不是中间机制，论文没有证明", text)

    def test_full_file_and_route_do_not_turn_an_argument_into_a_study_result(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {d["id"]: d for d in documents}
        raw = (ROOT / SOURCE).read_bytes()
        self.assertEqual(by_id["C05"]["text"], raw.decode())
        self.assertEqual(by_id["C05"]["source_sha256"], hashlib.sha256(raw).hexdigest())
        full_text = (ROOT / "llms-full.txt").read_text()
        chapter = next(c for c in json.loads((ROOT / "data/chapters.json").read_text())["chapters"] if c["id"] == "C05")
        self.assertEqual(full_text.count(chapter["text"].strip()), 1)
        for card in json.loads((ROOT / "data/catalog.json").read_text())["cards"]:
            if card["id"] in {"J025", "J026", "J027", "J028", "J029", "J030"}:
                self.assertIn("## " + card["source"], full_text)
                for value in card["fields"].values():
                    self.assertIn(value, full_text)
        route = next(r for r in routes if r["id"] == "R09")
        expected = {"C05", "B21", "B22", "N21", "N22", "E01", "E05"}
        self.assertEqual(set(route["targets"]), expected)
        self.assertTrue(expected <= {r["id"] for r in read.linked_records(route, documents, ROOT)})
        self.assertIn("不是B21/B22实验结论", route["text"])
        self.assertIn("不能用C05替实际关系分配责任", route["text"])
        self.assertIn("两篇同团队，非独立复现", route["text"])

    def test_html_epub_and_directory_keep_argument_and_destinations(self):
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            chapter = archive.read("EPUB/text/book--05-connection.xhtml").decode()
        for anchor in STRUCTURE + ARGUMENTS + OLD_ANCHORS:
            self.assertEqual(html.count('id="' + anchor + '"'), 1)
            self.assertEqual(chapter.count('id="' + anchor + '"'), 1)
        self.assertEqual(chapter.count("<table>"), 1)
        self.assertIn("essays--01-pleasure-is-an-end.xhtml#pleasure-consent-scope", chapter)
        self.assertIn("essays--05-play-is-not-performance.xhtml#amateur-changing-group", chapter)
        for phrase in ("23名女性本科生", "22名女性本科生", "两种情况下助手都在场", "不是无损替代", "不是心理治疗指南"):
            self.assertIn(phrase, chapter)
        self.assertIn("05 · 一起耍，不是把几个人捏成一个愿望", (ROOT / "README.md").read_text())
        self.assertIn("Being together does not mean wanting the same thing", (ROOT / "README.en.md").read_text())


if __name__ == "__main__":
    unittest.main()
