"""Reading structure and export integrity, not a measure of reader interest."""
import json
from pathlib import Path
import re
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import check

SOURCE = "book/26-collecting.md"
GROUPS = (
    ("collecting-relations", "从喜欢一件，到看见一组"),
    ("collecting-differences", "两件看起来相似的东西，究竟差在哪里？"),
    ("collecting-completeness", "成套、重复、越来越多：完整由谁来定？"),
    ("collecting-continuing", "保存不是把今天暂停"),
)


class CollectingStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / SOURCE).read_text()

    def test_four_questions_and_a_separate_closing(self):
        self.assertEqual(
            re.findall(r"^## (.+)$", self.text, re.M),
            [title for _, title in GROUPS]
            + ["兴趣变了，不需要用贬低旧爱来准许自己离开"],
        )
        opening = self.text.split('<a id="collecting-relations">')[0]
        for anchor, title in GROUPS:
            self.assertIn("](#" + anchor + ")", opening)
            self.assertIn('<a id="' + anchor + '"></a>\n## ' + title, self.text)
        self.assertIn("本章的立场不是少买", opening)
        self.assertIn("不让下一张订单垄断收藏的快乐", opening)

    def test_examples_precede_notation_and_counterargument_stays_with_completeness(self):
        def position(heading):
            return self.text.index(heading)
        self.assertLess(position("### 两张同题版画"), position("### “原作”"))
        self.assertLess(position("### “原作”"), position("### 图面变了"))
        self.assertLess(position("### 图面变了"), position("### “7/50”"))
        self.assertLess(position("### “7/50”"), position("### 把“知道的事”"))
        self.assertLess(position("### 一件重复品"), position("### 为什么不把一切"))
        self.assertLess(position("### 为什么不把一切"), position("## 保存不是把今天暂停"))
        self.assertIn("### 保存不是永远封存", self.text)
        self.assertIn("#### 糖果少了，作品就少了吗？", self.text)
        self.assertIn("#### 可以补充，不等于什么都能补回来", self.text)

    def test_legacy_title_and_deep_links_remain_available(self):
        legacy = "26--收藏不必集齐别让喜欢永远差最后一件"
        self.assertIn(legacy, check.anchors_for(self.text))
        rendered = build.markdown(self.text, SOURCE)
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            chapter = archive.read("EPUB/text/book--26-collecting.xhtml").decode()
        for anchor in [legacy] + [a for a, _ in GROUPS] + [
            "collecting-crosses", "collecting-layers", "collecting-abundance",
            "collecting-preservation", "collecting-candy", "collecting-not-refill",
            "collecting-digital", "collecting-return",
        ]:
            self.assertEqual(rendered.count('id="' + anchor + '"'), 1)
            self.assertEqual(chapter.count('id="' + anchor + '"'), 1)
        self.assertEqual(chapter.count("<table>"), 3)
        self.assertEqual(chapter.count("<img "), 2)

    def test_entrypoints_and_ai_text_follow_canonical_structure(self):
        chapters = json.loads((ROOT / "data/chapters.json").read_text())["chapters"]
        chapter = next(c for c in chapters if c["id"] == "C26")
        self.assertEqual(chapter["text"], self.text.strip())
        self.assertIn(self.text, (ROOT / "llms-full.txt").read_text())
        self.assertIn("收藏：别让下一张订单垄断快乐", (ROOT / "README.md").read_text())
        self.assertIn("Collecting: pleasure beyond the next purchase",
                      (ROOT / "README.en.md").read_text())
        routes = (ROOT / "docs/reading-map.md").read_text()
        for anchor, _ in GROUPS:
            self.assertIn("26-collecting.md#" + anchor, routes)


if __name__ == "__main__":
    unittest.main()
