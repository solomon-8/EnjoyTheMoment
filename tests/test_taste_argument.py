"""Preserve source scope and retrieval, not certify taste or reader persuasion."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read


class TasteArgumentTests(unittest.TestCase):
    def test_three_questions_and_strong_counterargument_remain_distinct(self):
        text = (ROOT / "essays/11-pleasure-and-reality.md").read_text()
        for phrase in (
            "**感受：**", "**判断：**", "**选择：**",
            "三次副歌完全相同", "第三次换了歌词",
            "喜欢不需要获得批准，对喜欢的解释却仍然可以被纠正",
            "这次改动怎样处理了前面的期待",
            "小满甚至同意，另一首在她认可的标准下完成得更好",
            "若小满写的是一篇比较乐评",
            "当然可以说差", "不意味着作品的表达与现实后果不能受批评",
            "不是声称用一把钥匙就推翻了他的全文",
            "没有资格凭一次娱乐选择判断别人是不是退化了",
            "品味可以长出新枝",
        ):
            self.assertIn(phrase, text)
        rendered = build.markdown(text, "essays/11-pleasure-and-reality.md")
        for anchor in (
            "pleasure-taste-claims", "pleasure-taste-key",
            "pleasure-taste-choice", "pleasure-taste-criticism",
            "pleasure-quality", "pleasure-promises", "pleasure-ended-world",
            "pleasure-position",
        ):
            self.assertEqual(rendered.count(f'id="{anchor}"'), 1)
            self.assertIn(f'href="#{anchor}"', rendered)
        self.assertNotIn("<!-- pick:", text)

    def test_primary_text_does_not_become_an_experiment_or_a_blanket_endorsement(self):
        text = (ROOT / "docs/evidence/F83-standard-of-taste.md").read_text()
        for phrase in (
            "ST 6–9、14–16、18–25、28–30", "1777",
            "没有与纸本扫描、手稿或其他校勘本逐字核对",
            "ST 7", "ST 8", "ST 23", "ST 24", "ST 25",
            "本次没有独立核读塞万提斯原作",
            "没有把 ST 29 的年龄例子当作现代年龄规律",
            "不接受的阶层和族群贬低", "不是实际歌曲、访谈或原书案例",
            "不新增 B 系列研究", "不是密尔或休谟共同认可的结论",
        ):
            self.assertIn(phrase, text)
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        note = next(n for n in notes if n["id"] == "F83")
        self.assertEqual(note["text"], text)
        self.assertEqual(note["source_kind"], "philosophical_primary_text")
        self.assertEqual(len(notes), 127)
        research = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(research), 44)
        self.assertNotIn("F83", {r["id"] for r in research})
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("F83" not in c["background_ids"] for c in cards))

    def test_route_keeps_philosophy_full_text_and_visible_links(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {d["id"]: d for d in documents}
        route = next(r for r in routes if r["id"] == "R06")
        targets = {"E11", "F27", "F83", "C11", "C31"}
        self.assertEqual(set(route["targets"]), targets)
        self.assertTrue(targets <= {d["id"] for d in read.linked_records(route, documents, ROOT)})
        self.assertEqual(len(routes), 81)
        for phrase in ("不强行改答成活动推荐", "不把全部趣味说成等价",
                       "没有独立核读《堂吉诃德》", "不据此命令读者改掉爱好"):
            self.assertIn(phrase, route["text"])
        for identifier, path in (
            ("E11", "essays/11-pleasure-and-reality.md"),
            ("F83", "docs/evidence/F83-standard-of-taste.md"),
        ):
            raw = (ROOT / path).read_bytes()
            self.assertEqual(by_id[identifier]["text"], raw.decode())
            self.assertEqual(by_id[identifier]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertEqual((ROOT / "llms-full.txt").read_text().count(raw.decode().strip()), 1)

    def test_epub_preserves_source_limits_and_cross_chapter_links(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            essay = archive.read("EPUB/text/essays--11-pleasure-and-reality.xhtml").decode()
            note = archive.read("EPUB/text/docs--evidence--F83-standard-of-taste.xhtml").decode()
            for anchor in (
                "pleasure-taste-claims", "pleasure-taste-key", "pleasure-taste-choice",
                "pleasure-taste-criticism", "pleasure-digital-life", "pleasure-ended-world",
                "pleasure-quality", "pleasure-position",
            ):
                self.assertEqual(essay.count(f'id="{anchor}"'), 1)
            self.assertIn("承认一件作品更好", essay)
            self.assertIn("较弱的结尾", essay)
            self.assertIn("F83-standard-of-taste.xhtml#taste-source-key", essay)
            self.assertIn("不是心理实验", archive.read("EPUB/text/docs--reading-map.xhtml").decode())
            self.assertEqual(note.count("<table>"), 0)
            for anchor in ("taste-source-key", "taste-source-judges", "taste-source-difference"):
                self.assertEqual(note.count(f'id="{anchor}"'), 1)
            self.assertIn("essays--11-pleasure-and-reality.xhtml#pleasure-taste-criticism", note)
            self.assertIn("本次没有独立核读塞万提斯原作", note)


if __name__ == "__main__":
    unittest.main()
