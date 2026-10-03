"""Argument structure and retrieval contracts, not reader-response scores."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read

SOURCE = "book/10-aftertaste.md"
GROUPS = (
    ("aftertaste-value", "快乐结束了，为什么仍然算数？"),
    ("aftertaste-evaluation", "让回忆得高分，就等于把生活过好吗？"),
    ("aftertaste-next-choice", "喜欢过，也可以不再这样选"),
)


class AftertasteStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / SOURCE).read_text()

    def test_value_evaluation_and_next_choice_are_distinct_groups(self):
        self.assertEqual(re.findall(r"^## (.+)$", self.text, re.M),
                         [title for _, title in GROUPS])
        opening = self.text.split('<a id="aftertaste-value">')[0]
        for anchor, title in GROUPS:
            self.assertIn("](#" + anchor + ")", opening)
            self.assertIn('<a id="' + anchor + '"></a>\n## ' + title, self.text)
        self.assertIn("一个好晚上，不需要把第二天也变成好晚上", opening)
        self.assertIn("不是一套必须完成的善后任务", opening)

    def test_objection_belongs_with_tradeoff_and_studies_keep_their_sequence(self):
        text = self.text
        positions = [text.index('<a id="' + anchor + '"></a>') for anchor in (
            "aftertaste-story", "aftertaste-memory-objection", "aftertaste-memory",
            "aftertaste-evaluation", "aftertaste-gifts", "aftertaste-one-episode",
            "aftertaste-peak-boundary", "aftertaste-not-a-score", "aftertaste-next-choice",
        )]
        self.assertEqual(positions, sorted(positions))
        value = text.split('<a id="aftertaste-value"></a>')[1].split(
            '<a id="aftertaste-evaluation"></a>')[0]
        self.assertIn("回忆不是附带的假货", value)
        self.assertIn("不能把前者一律劝退成五分钟轻松版", value)
        evaluation = text.split('<a id="aftertaste-evaluation"></a>')[1].split(
            '<a id="aftertaste-next-choice"></a>')[0]
        for phrase in ("B18测的是受访者偏好", "DVD送达前", "没有随机操纵事件边界",
                       "看后重建", "44.3%和44.2%", "好结尾可以是这次经历的理由"):
            self.assertIn(phrase, evaluation)

    def test_related_arguments_are_linked_without_erasing_the_local_distinction(self):
        self.assertIn("04-buying-pleasure.md#purchase-uncertainty", self.text)
        self.assertIn("08-life-without-an-audience.md#audience-verdict", self.text)
        self.assertIn("没核实返程总是没关系", self.text)
        self.assertIn("前者关心安排有没有漏项，后者关心体验中才会获得的信息", self.text)
        self.assertIn("不是一个保证避免后悔的决策模型", self.text)
        docs, routes = read.load_documents(ROOT)
        route = next(r for r in routes if r["id"] == "R65")
        self.assertTrue({"E04", "E08"} <= set(route["targets"]))
        self.assertTrue({"E04", "E08"} <= {
            d["id"] for d in read.linked_records(route, docs, ROOT)})
        self.assertIn("不把共享原则或换一个情境重复计为独立证据", route["text"])

    def test_full_retrieval_and_separate_card_exports_both_remain_intact(self):
        docs, _ = read.load_documents(ROOT)
        full = next(d for d in docs if d["id"] == "C10")
        self.assertEqual(full["text"], self.text)
        self.assertEqual(full["source_sha256"],
                         hashlib.sha256(self.text.encode()).hexdigest())
        chapter = next(c for c in json.loads(
            (ROOT / "data/chapters.json").read_text())["chapters"] if c["id"] == "C10")
        self.assertEqual(chapter["scope"], "chapter_introduction")
        self.assertEqual(chapter["text"], self.text.partition('<a id="j')[0].strip())
        self.assertEqual(chapter["card_ids"], [
            "J055", "J056", "J057", "J058", "J059", "J060"])
        self.assertIn(chapter["text"], (ROOT / "llms-full.txt").read_text())
        rendered = build.markdown(self.text, SOURCE)
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            epub = archive.read("EPUB/text/book--10-aftertaste.xhtml").decode()
        for anchor, _ in GROUPS:
            self.assertEqual(rendered.count('id="' + anchor + '"'), 1)
            self.assertEqual(epub.count('id="' + anchor + '"'), 1)
        self.assertEqual(epub.count("<table>"), 3)
        self.assertIn("essays--04-buying-pleasure.xhtml#purchase-uncertainty", epub)
        self.assertIn("essays--08-life-without-an-audience.xhtml#audience-verdict", epub)


if __name__ == "__main__":
    unittest.main()
