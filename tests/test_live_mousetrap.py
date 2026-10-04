"""Preserve a text-based argument and its limits, not measure persuasion."""
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

CHAPTER = "book/13-live-events.md"
NOTE = "docs/evidence/F94-hamlet-and-spectators.md"


class LiveMousetrapTests(unittest.TestCase):
    def test_specific_work_adds_nested_viewing_not_an_audience_effect(self):
        text = (ROOT / CHAPTER).read_text()
        self.assertLess(text.index('id="live-space"'),
                        text.index('id="live-mousetrap"'))
        self.assertLess(text.index('id="live-mousetrap-reading"'),
                        text.index('id="live-convention"'))
        for phrase in (
            "角色不再看戏的那一刻，恰好成为我们要看的戏",
            "无言表演", "不是弟弟", "本书没有观看指定版本",
            "不是本书提供的现实测谎方法",
            "录像当然也能呈现这些关系", "现场不自动胜出",
            "红信三票、蓝信两票",
        ):
            self.assertIn(phrase, text)
        self.assertEqual(text.count('id="live-mousetrap"'), 1)
        self.assertEqual(text.count('id="live-mousetrap-reading"'), 1)

    def test_plot_is_folded_but_full_text_is_explicitly_not_spoiler_free(self):
        text = (ROOT / CHAPTER).read_text()
        start = text.index("<details>", text.index('id="live-mousetrap"'))
        end = text.index("</details>", start)
        self.assertTrue(start < text.index('id="live-mousetrap-reading"') < end)
        self.assertTrue(start < text.index("卢西安纳斯") < end)
        self.assertIn("原始Markdown、全文导出和打印仍含剧透", text[:start])
        html = build.markdown(text, CHAPTER)
        self.assertIn('id="live-mousetrap-reading"', html)
        self.assertIn('href="#f94"', html)
        self.assertIn("展开《哈姆雷特》戏中戏细读（含关键剧透）", html)

    def test_source_keeps_line_order_version_and_character_boundaries(self):
        note = (ROOT / NOTE).read_text()
        for phrase in (
            "80—95", "145—160", "253—296", "313—316",
            "FTLN 2192", "编辑补充", "第二四开本",
            "不是剧院里的真实观众", "未校勘早期四开本",
            "文本细读不能证明现场比屏幕更好",
            "不是《哈姆雷特》的删节复述",
        ):
            self.assertIn(phrase, note)
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        self.assertEqual(len(notes), len(build.EVIDENCE))
        self.assertEqual(sum(n["id"] == "F94" for n in notes), 1)
        self.assertEqual(next(n for n in notes if n["id"] == "F94")["source_kind"],
                         "literary_primary_text")
        research = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertNotIn("F94", {r["id"] for r in research})
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertTrue(all("F94" not in c["background_ids"] for c in cards))

    def test_ai_retrieval_keeps_whole_text_spoilers_and_source_scope(self):
        documents, routes = read.load_documents(ROOT)
        documents = {d["id"]: d for d in documents}
        for identifier, source in (("C13", CHAPTER), ("F94", NOTE)):
            raw = (ROOT / source).read_bytes()
            self.assertEqual(documents[identifier]["text"], raw.decode())
            self.assertEqual(documents[identifier]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertIn(raw.decode().strip(), (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R14")
        self.assertIn("F94", route["targets"])
        for phrase in ("不是观演实录", "不是弟弟", "不要自行解释",
                       "默认折叠当作AI全文不含情节", "现场必胜屏幕"):
            self.assertIn(phrase, route["text"])

    def test_epub_retains_complete_plot_and_bidirectional_links(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            chapter = z.read("EPUB/text/book--13-live-events.xhtml").decode()
            note = z.read("EPUB/text/docs--evidence--F94-hamlet-and-spectators.xhtml").decode()
            self.assertIn('id="live-mousetrap-reading"', chapter)
            self.assertIn("不是弟弟", chapter)
            self.assertIn("docs--evidence--F94-hamlet-and-spectators.xhtml", chapter)
            self.assertIn("book--13-live-events.xhtml#live-mousetrap-reading", note)
            self.assertIn("FTLN 2192", note)
            self.assertEqual(chapter.count("<table>"), 3)


if __name__ == "__main__":
    unittest.main()
