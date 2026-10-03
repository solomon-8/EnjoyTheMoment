"""Protect discovery/proof distinctions and access, not literary superiority."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check
import read

PATH = "book/32-puzzles.md"
SECTIONS = ("puzzle-purpose", "puzzle-proof", "puzzle-help",
            "puzzle-structure", "puzzle-after")
DESTINATIONS = ("puzzle-cards", "puzzle-answer-vs-discovery", "puzzle-roads",
                "puzzle-invariants", "puzzle-rule-change", "puzzle-knowing")


class PuzzleArgumentTests(unittest.TestCase):
    def test_hierarchy_and_choice_of_reading_path(self):
        text = (ROOT / PATH).read_text()
        self.assertEqual(len(re.findall(r"^## ", text, re.M)), 5)
        self.assertEqual(len(re.findall(r"^### ", text, re.M)), 14)
        positions = [text.index(f'id="{s}"') for s in SECTIONS]
        self.assertEqual(positions, sorted(positions))
        for anchor in SECTIONS + DESTINATIONS:
            self.assertIn(anchor, check.anchors_for(text))
            self.assertIn(f"](#{anchor})", text)
        self.assertIn("解谜不是一种必须不断提速的查资料", check.anchors_for(text))
        self.assertEqual(text.count("<details>"), 8)
        self.assertEqual(text.count("</details>"), 8)

    def test_discovery_is_distinct_from_proof_and_does_not_require_no_help(self):
        text = (ROOT / PATH).read_text()
        argument = text.split('id="puzzle-answer-vs-discovery"', 1)[1].split(
            "### 卡住不只有一种原因", 1)[0]
        for phrase in ("原创假想", "不增加条件", "符合条件的排列始终只有一种",
                       "没有改变题目允许哪些排列", "不是说提示越少越高级",
                       "直接给完整排列恰好有用", "不是人的等级",
                       "必须能由条件说明", "不是撤销刚才揭晓的按钮"):
            self.assertIn(phrase, argument)
        self.assertIn("02-excitement-without-escalation.md#excitement-spoiler-choice",
                      argument)
        self.assertIn("34-shared-stories.md#story-fixed-or-authored", text)

    def test_full_retrieval_and_route_keep_participation_limits(self):
        text = (ROOT / PATH).read_text()
        documents, routes = read.load_documents(ROOT)
        record = next(d for d in documents if d["id"] == "C32")
        self.assertEqual(record["text"], text)
        self.assertEqual(record["source_sha256"],
                         hashlib.sha256(text.encode()).hexdigest())
        self.assertIn(text, (ROOT / "llms-full.txt").read_text())
        exported = next(c for c in json.loads(
            (ROOT / "data/chapters.json").read_text())["chapters"] if c["id"] == "C32")
        self.assertEqual(exported["text"], text.strip())
        route = next(r for r in routes if r["id"] == "R23")
        self.assertEqual(set(route["targets"]), {"C32", "F46"})
        for phrase in ("不是心理效果实验", "不得概括为越少帮助越好",
                       "避免泄露折叠答案", "#puzzle-answer-vs-discovery", "#puzzle-help"):
            self.assertIn(phrase, route["text"])

    def test_epub_preserves_argument_and_cross_chapter_links(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            text = archive.read("EPUB/text/book--32-puzzles.xhtml").decode()
        for anchor in SECTIONS + DESTINATIONS:
            self.assertIn(f'id="{anchor}"', text)
        self.assertIn("帮助的分寸，不只看说了几句话", text)
        self.assertIn("essays--02-excitement-without-escalation.xhtml#excitement-spoiler-choice",
                      text)
        self.assertIn("book--34-shared-stories.xhtml#story-fixed-or-authored", text)


if __name__ == "__main__":
    unittest.main()
