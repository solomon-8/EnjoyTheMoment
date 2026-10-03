"""C04 fidelity and routing checks, not measures of persuasion or enjoyment."""
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

SOURCE = "book/04-play.md"
STRUCTURE = (
    "play-chosen-stakes", "play-common-terms",
    "play-shared-authorship", "play-leave-the-score",
)
OLD_ANCHORS = (
    "04--痛快地玩不必玩出名堂", "play-wanting-to-win",
    "play-changing-goals", "play-finish", "play-honest-result",
    "play-score-boundary", "play-shared-adjustment",
    "play-recommendation", "play-unrepeatable", "play-offer",
    "play-response", "play-improv-objection",
)


class PlayArgumentStructureTests(unittest.TestCase):
    def test_argument_lines_are_navigable_before_optional_cards(self):
        text = (ROOT / SOURCE).read_text()
        headings = re.findall(r"^## (.+)$", text, re.M)
        self.assertEqual(len(headings), 5)
        self.assertTrue(headings[-1].startswith("配套："))
        positions = [text.index(f'id="{anchor}"') for anchor in STRUCTURE]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(positions[-1], text.index('id="play-companions"'))
        self.assertLess(text.index('id="play-companions"'), text.index('id="j019"'))
        for anchor in STRUCTURE + OLD_ANCHORS + ("play-companions",):
            self.assertIn(anchor, check.anchors_for(text))
        for anchor in STRUCTURE + (
            "play-wanting-to-win", "play-changing-goals", "play-finish",
            "play-score-boundary", "play-offer",
        ):
            self.assertIn(f"](#{anchor})", text)
        self.assertEqual(len(re.findall(r"^### ", text, re.M)), 21)
        self.assertEqual(len(re.findall(r"^#### ", text, re.M)), 3)

    def test_stopping_is_not_erasing_results_or_other_peoples_claims(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in (
            "不必让它独自决定今晚值不值",
            "没有向别人许诺的私人创作",
            "不等于有权取消已经发生的结果或已经答应的事",
            "不是别人必须续场的义务",
            "旁人不能只凭玩了几小时",
            "局内的失败，与局外认为这一晚值得，并不互相抵消",
            "教学局、练习局、正式较量可以分开",
            "想进入某种复杂玩法，就可能需要花时间理解规则",
            "改变计划值得说明，却仍不包含必须喜欢的承诺",
            "不证明现实中人人都同样有权退出",
        ):
            self.assertIn(phrase, text)
        for href in (
            "19-games.md#games-delegation",
            "../essays/05-play-is-not-performance.md#amateur-purpose",
            "../essays/01-pleasure-is-an-end.md#pleasure-consent-scope",
        ):
            self.assertIn(href, text)
        self.assertEqual(text.count("<!-- pick:"), 6)

    def test_full_text_and_route_preserve_normative_source_boundary(self):
        documents, routes = read.load_documents(ROOT)
        chapter = next(d for d in documents if d["id"] == "C04")
        raw = (ROOT / SOURCE).read_bytes()
        self.assertEqual(chapter["text"], raw.decode())
        self.assertEqual(chapter["source_sha256"], hashlib.sha256(raw).hexdigest())
        export = next(c for c in json.loads(
            (ROOT / "data/chapters.json").read_text())["chapters"] if c["id"] == "C04")
        self.assertEqual(export["text"], raw.decode().partition('<a id="j')[0].strip())
        self.assertIn(export["text"], (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R56")
        expected = {"C04", "C19", "C12", "C13", "E01", "E05",
                    "E06", "E10", "F63", "F85"}
        self.assertEqual(set(route["targets"]), expected)
        self.assertTrue(expected <= {
            d["id"] for d in read.linked_records(route, documents, ROOT)})
        self.assertIn("不是F63/F85验证的普遍退出权", route["text"])
        self.assertIn("不能从参与推定必须喜欢", route["text"])

    def test_reader_and_epub_keep_hierarchy_and_old_destinations(self):
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            chapter = archive.read("EPUB/text/book--04-play.xhtml").decode()
        for anchor in STRUCTURE + OLD_ANCHORS + ("play-companions",):
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
            self.assertEqual(chapter.count(f'id="{anchor}"'), 1)
        for phrase in ("总和为 14", "总和正好为 9", "咱们帽子店",
                       "店钥匙到现在还在我手里", "不必让它独自决定今晚值不值"):
            self.assertIn(phrase, chapter)
        self.assertIn("essays--01-pleasure-is-an-end.xhtml#pleasure-consent-scope",
                      chapter)
        self.assertIn("book--19-games.xhtml#games-delegation", chapter)
        self.assertIn("04 · 这一局我想赢，但不把人生交给比分",
                      (ROOT / "README.md").read_text())
        self.assertIn("I want to win this game, not live by its score",
                      (ROOT / "README.en.md").read_text())


if __name__ == "__main__":
    unittest.main()
