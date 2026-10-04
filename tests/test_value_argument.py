"""Publication and retrieval guards; not a verdict on argument quality."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import check
import read


class ValueArgumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = "essays/01-pleasure-is-an-end.md"
        cls.raw = (ROOT / cls.source).read_bytes()
        cls.text = cls.raw.decode()

    def test_objection_and_counterexamples_remain_with_the_claim(self):
        for phrase in (
            "不把它安到参考作者头上",
            "没有证明它与“耍起”不相容",
            "原创假想，不是调查、计时结果或消费建议",
            "变化不是成本消失",
            "尚未说清的别人劳动",
            "可以承认暂时做不到",
            "没有“有钱买时间才会享受”",
            "不让节省把原本想过的生活一起省掉",
        ):
            self.assertIn(phrase, self.text)

    def test_old_and_new_destinations_exist_once_in_offline_reader(self):
        html = (ROOT / "index.html").read_text()
        anchors = (
            "pleasure-value-metric", "pleasure-process",
            "pleasure-options", "pleasure-enough", "pleasure-not-quota",
            "pleasure-happiness-study", "pleasure-disappointment",
        )
        for anchor in anchors:
            self.assertIn(anchor, check.anchors_for(self.text))
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
        for anchor in anchors[:2]:
            self.assertIn(f"](#{anchor})", self.text.split("\n## ", 1)[0])
            self.assertIn(f'href="#{anchor}"', build.markdown(
                (ROOT / "SHUAQI.md").read_text(), "SHUAQI.md"))

    def test_full_text_retrieval_keeps_the_compatibility_concession(self):
        documents, routes = read.load_documents(ROOT)
        essay = next(item for item in documents if item["id"] == "E01")
        self.assertEqual(essay["text"], self.text)
        self.assertEqual(essay["source_sha256"],
                         hashlib.sha256(self.raw).hexdigest())
        self.assertIn(self.text, (ROOT / "llms-full.txt").read_text())
        exported = json.loads((ROOT / "data/essays.json").read_text())["essays"]
        self.assertEqual(next(x for x in exported if x["id"] == "E01")["text"],
                         self.text)
        route = next(x for x in routes if x["id"] == "R01")
        self.assertEqual(set(route["targets"]), {"SHUAQI", "E01", "F86", "F97"})
        self.assertIn("阿岚、小周不是受访者", route["text"])
        self.assertIn("比较可能与本项目相容", route["text"])

    def test_epub_keeps_clickable_internal_arguments(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            names = [n for n in archive.namelist()
                     if n.endswith("essays--01-pleasure-is-an-end.xhtml")]
            self.assertEqual(len(names), 1)
            text = archive.read(names[0]).decode()
        for anchor in ("pleasure-value-metric", "pleasure-process"):
            self.assertEqual(text.count(f'id="{anchor}"'), 1)
            self.assertIn("#" + anchor, text)
        for phrase in ("变化不是成本消失", "没有证明它与“耍起”不相容",
                       "尚未说清的别人劳动"):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
