"""Fidelity and routing for C34's fixed facts versus shared authorship argument.

These checks protect the reviewed rule branches. They do not validate player
experience, the whole Fate ruleset, or comparative literary quality.
"""
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

CHAPTER = "book/34-shared-stories.md"
NOTE = "docs/evidence/F33-aspects-and-shared-fiction.md"
SECTIONS = ("story-agency", "story-results", "story-preparation",
            "story-world", "story-boundaries")
DESTINATIONS = ("story-choice", "story-dice", "story-aspects", "story-table",
                "story-clocks", "story-flashbacks", "story-uncertainty",
                "story-create-or-discover", "story-fixed-or-authored")


class StoryFactsTests(unittest.TestCase):
    def test_argument_hierarchy_and_existing_mechanics_remain_navigable(self):
        text = (ROOT / CHAPTER).read_text()
        self.assertEqual(len(re.findall(r"^## ", text, re.M)), 5)
        self.assertEqual(len(re.findall(r"^### ", text, re.M)), 14)
        positions = [text.index(f'id="{anchor}"') for anchor in SECTIONS]
        self.assertEqual(positions, sorted(positions))
        for anchor in SECTIONS + DESTINATIONS:
            self.assertIn(anchor, check.anchors_for(text))
            self.assertIn(f"](#{anchor})", text)
        for phrase in ("不是照搬前文", "零颗或负数骰子",
                       "不能推广成唯一规则", "不能靠闪回直接改写",
                       "不把这种请求交给多数票批准"):
            self.assertIn(phrase, text)

    def test_source_keeps_all_known_unknown_and_new_aspect_outcomes(self):
        text = (ROOT / NOTE).read_text()
        new = text.split("| 针对新特征 |", 1)[1].split("\n\n", 1)[0]
        known = text.split("| 针对已有特征 |", 1)[1].split("\n\n", 1)[0]
        new_rows = [line for line in new.splitlines()
                    if line.startswith("| ") and not line.startswith("| ---")]
        known_rows = [line for line in known.splitlines()
                      if line.startswith("| ") and not line.startswith("| ---")]
        self.assertEqual(len(new_rows), 4)
        self.assertEqual(len(known_rows), 4)
        self.assertIn("| 平局 | 不建立新特征，得到一个 boost |", new)
        self.assertIn("| 平局 | 得到一次免费调用 | 得到一个 boost，该特征仍未知 |", known)
        self.assertIn("最终特征可能需改写得对敌对方有利", new)
        self.assertIn("敌对方可选择揭示该特征", known)
        for table in (new, known):
            self.assertIn("普通成功", table)
            self.assertIn("高出至少3的成功", table)
            self.assertIn("两次免费调用", table)
        for phrase in ("不能用命运点再次调用，也不能 compel",
                       "不保留到场景结束之后",
                       "用掉一次免费调用不自动抹去特征",
                       "不是 SRD 中同名的分类"):
            self.assertIn(phrase, text)

    def test_fictional_examples_do_not_authorize_arbitrary_answers(self):
        text = (ROOT / CHAPTER).read_text()
        for phrase in ("两条各自开始的原创支线", "不是前后连续的回合",
                       "已有但未知的特征", "没有建立那个新特征", "原特征仍然未知",
                       "不等于厚布自动从钟箱上消失",
                       "不能因为布“还在”，就每次白拿同样的加成",
                       "未经说明地互换", "承诺让人查明的既定答案",
                       "不要求三份公开清单", "不是该规则已经测出的心理效果"):
            self.assertIn(phrase, text)
        self.assertIn("32-puzzles.md#puzzle-rule-change", text)
        self.assertIn("34-shared-stories.md#story-fixed-or-authored",
                      (ROOT / "book/32-puzzles.md").read_text())
        for line in text.splitlines():
            if line.startswith("This work is based on"):
                self.assertIn(line, (ROOT / "LICENSE").read_text())

    def test_ai_retrieval_is_complete_and_keeps_rule_limits(self):
        documents, routes = read.load_documents(ROOT)
        for identifier, path in (("C34", CHAPTER), ("F33", NOTE),
                                 ("C32", "book/32-puzzles.md")):
            record = next(d for d in documents if d["id"] == identifier)
            raw = (ROOT / path).read_bytes()
            self.assertEqual(record["text"], raw.decode())
            self.assertEqual(record["source_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertIn(raw.decode(), (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R25")
        self.assertEqual(set(route["targets"]), {"C34", "F32", "F33"})
        self.assertIn("平局的boost不等于未知特征已揭示", route["text"])
        self.assertIn("不是SRD官方分类", route["text"])
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        self.assertEqual(next(n for n in notes if n["id"] == "F33")["text"],
                         (ROOT / NOTE).read_text())

    def test_epub_and_reader_preserve_new_anchors_and_cross_chapter_links(self):
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            chapter = archive.read("EPUB/text/book--34-shared-stories.xhtml").decode()
            puzzle = archive.read("EPUB/text/book--32-puzzles.xhtml").decode()
            note = archive.read(
                "EPUB/text/docs--evidence--F33-aspects-and-shared-fiction.xhtml").decode()
        for anchor in SECTIONS + DESTINATIONS:
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
            self.assertEqual(chapter.count(f'id="{anchor}"'), 1)
        self.assertIn("book--34-shared-stories.xhtml#story-fixed-or-authored", puzzle)
        self.assertIn("book--32-puzzles.xhtml#puzzle-rule-change", chapter)
        self.assertIn('id="f33-create-advantage"', note)
        for phrase in ("查暗记", "裹厚布", "不是一张“已经找到暗记”的证明"):
            self.assertIn(phrase, chapter)


if __name__ == "__main__":
    unittest.main()
