"""Content, provenance, geometry and retrieval guards; not audience-effect tests."""
import base64
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read


class NightlifeTests(unittest.TestCase):
    def test_chapter_develops_experience_and_counterarguments(self):
        text = (ROOT / "book/37-nightlife.md").read_text()
        for phrase in (
            "夜生活不是把白天过坏了", "本章讨论成人的夜生活选择",
            "一间屋子让某些东西出现，也会让另一些东西退到后面",
            "1982", "游艇展厅", "原创假想",
            "没有对应真实录音", "甲合计八格，乙合计六格",
            "不需要密集说话", "相互看见不是允许拍摄",
            "值得晚一点回家，不等于越晚越值得",
            "最强的反对意见", "商家卖的就是一种",
            "共同负担和排斥", "规模不是价值的保证",
        ):
            self.assertIn(phrase, text)
        html = build.markdown(text, "book/37-nightlife.md")
        self.assertEqual(html.count("<table>"), 3)
        self.assertEqual(html.count('src="data:image/png;base64,'), 1)
        self.assertIn('href="#f71"', html)
        self.assertIn('href="#f04"', html)
        self.assertNotIn("<!-- pick:", text)

    def test_source_limits_are_not_replaced_by_heritage_praise(self):
        text = (ROOT / "docs/evidence/F71-clubs-design-and-house.md").read_text()
        for phrase in (
            "2026-10-01", "2018-03-17", "2021-05-01", "2022-01-09",
            "同一巡展", "2023年4月、同年6月修订重印",
            "Matt Crawford", "4、7—9、13—14、16、20—22",
            "不声称完整核验所有档案", "ArtBar", "2026-07-01",
            "第4页称Williams在1976年购入建筑，第7页写租用",
            "只有市议会通过的条例文字才是最终认定",
            "不改写成没有争议的唯一词源或单人发明论",
            "不是Knuckles演出转录", "不新增B系列背景实验",
        ):
            self.assertIn(phrase, text)
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        note = next(n for n in notes if n["id"] == "F71")
        self.assertEqual(note["text"], text)
        self.assertEqual(note["source_kind"],
                         "museum_exhibition_designer_account_and_historical_report")
        self.assertIn('href="#c37"',
                      build.markdown(text, "docs/evidence/F71-clubs-design-and-house.md",
                                     omit_title=True))

    def test_original_sequence_duration_overlap_and_asset_identity(self):
        tree = ET.parse(ROOT / "assets/media/nightlife-sequence.svg").getroot()
        ns = {"s": "http://www.w3.org/2000/svg"}
        self.assertEqual(tree.attrib["viewBox"], "0 0 400 670")
        spans = {}
        for name in ("sequential-a", "sequential-b", "overlapping-a", "overlapping-b"):
            rect = tree.find('.//s:rect[@id="' + name + '"]', ns)
            start = (int(rect.attrib["x"]) - 66) // 38
            length = int(rect.attrib["width"]) // 38
            self.assertEqual(length, 4)
            spans[name] = set(range(start, start + length))
        a, b = spans["sequential-a"], spans["sequential-b"]
        self.assertEqual(len(a & b), 0)
        self.assertEqual(len(a | b), 8)
        a, b = spans["overlapping-a"], spans["overlapping-b"]
        self.assertEqual(a & b, {2, 3})
        self.assertEqual(a | b, set(range(6)))
        raw = (ROOT / "assets/media/nightlife-sequence.png").read_bytes()
        self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", raw[16:24]), (800, 1340))
        self.assertIn("data:image/png;base64," + base64.b64encode(raw).decode(),
                      (ROOT / "index.html").read_text())
        self.assertIn("nightlife-sequence.svg", (ROOT / "assets/media/README.md").read_text())

    def test_full_text_route_links_and_not_an_activity_card(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {r["id"]: r for r in documents}
        for identifier, path in (
            ("C37", "book/37-nightlife.md"),
            ("F71", "docs/evidence/F71-clubs-design-and-house.md"),
        ):
            raw = (ROOT / path).read_bytes()
            self.assertEqual(by_id[identifier]["text"], raw.decode())
            self.assertEqual(by_id[identifier]["source_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual((ROOT / "llms-full.txt").read_text().count(raw.decode().strip()), 1)
        route = next(r for r in routes if r["id"] == "R70")
        self.assertEqual(set(route["targets"]),
                         {"C37", "F71", "B41", "N41", "C11", "C13", "C27", "C16", "C05", "C09", "C10", "F04", "E02", "E04"})
        self.assertTrue(set(route["targets"]) <=
                        {r["id"] for r in read.linked_records(route, documents, ROOT)})
        chapter = next(c for c in json.loads((ROOT / "data/chapters.json").read_text())["chapters"]
                       if c["id"] == "C37")
        self.assertEqual(chapter["scope"], "full_chapter")
        self.assertEqual(chapter["card_ids"], [])
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        studies = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(studies), 44)
        self.assertNotIn("F71", {s["id"] for s in studies})


if __name__ == "__main__":
    unittest.main()
