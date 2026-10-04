"""Preserve the argument's identity and limits; not a proof of its ethical position."""
import contextlib
import io
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check
import epub
import read


class PleasureAndHelpTests(unittest.TestCase):
    def fetch(self, identifier):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = read.main(["--id", identifier], ROOT)
        self.assertEqual(code, 0)
        return json.loads(output.getvalue())

    def test_full_argument_source_and_route_remain_distinct(self):
        essay = self.fetch("E01")
        note = self.fetch("F97")
        self.assertTrue(essay["complete"])
        self.assertTrue(note["complete"])
        self.assertEqual(note["record"]["source_kind"], "philosophical_primary_argument")
        self.assertEqual(note["record"]["text"],
                         (ROOT / "docs/evidence/F97-famine-affluence-morality.md").read_text())
        self.assertIn("F97", {r["id"] for r in essay["linked_records"]})
        self.assertIn("E01", {r["id"] for r in note["linked_records"]})
        self.assertTrue(all("text" not in r for r in essay["linked_records"]))
        self.assertIn("pleasure-and-help", check.anchors_for(essay["record"]["text"]))
        self.assertIn("singer-demanding-help", check.anchors_for(note["record"]["text"]))
        route = self.fetch("R01")["record"]
        self.assertIn("F97", route["targets"])
        for marker in ("强弱原则", "持续投入", "政府责任", "不是效果研究",
                       "仍有争议", "道德理由不自动授予强迫权限"):
            self.assertIn(marker, route["text"])

    def test_canonical_text_preserves_actual_disagreement_and_limits(self):
        text = self.fetch("E01")["record"]["text"]
        section = text.split('<a id="pleasure-and-help"></a>', 1)[1].split(
            '<a id="即时满足是否天生低级"></a>', 1)[0]
        for marker in ("原创假想", "应当先帮助", "受助者也不欠她感谢",
                       "一项小牺牲", "没有推翻那项原则", "仍然成立为一个追问",
                       "有些本来能提供的帮助没有提供", "普遍适用的捐助比例或免责线",
                       "快乐不必先证明有用"):
            self.assertIn(marker, section)
        self.assertIn("不是提供现场救援方法", section)
        exported = next(r for r in json.loads((ROOT / "data/essays.json").read_text())["essays"]
                        if r["id"] == "E01")
        self.assertEqual(exported["text"], text)
        source = next(r for r in json.loads((ROOT / "data/evidence.json").read_text())["notes"]
                      if r["id"] == "F97")
        self.assertEqual(source["text"], self.fetch("F97")["record"]["text"])

    def test_entry_and_reader_routes_reach_argument_not_activity(self):
        for path in ("README.md", "README.en.md", "SHUAQI.md"):
            text = (ROOT / path).read_text()
            self.assertIn("essays/01-pleasure-is-an-end.md#pleasure-and-help", text)
        webpage = (ROOT / "index.html").read_text()
        self.assertIn('href="#pleasure-and-help"', webpage)
        self.assertIn('id="pleasure-and-help"', webpage)
        self.assertIn('href="#singer-demanding-help"', webpage)
        self.assertIn('id="singer-demanding-help"', webpage)

    def test_epub_keeps_forward_and_return_links_and_source_limits(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            essay = archive.read("EPUB/" + epub.document_name(
                "essays/01-pleasure-is-an-end.md")).decode()
            note = archive.read("EPUB/" + epub.document_name(
                "docs/evidence/F97-famine-affluence-morality.md")).decode()
        self.assertIn('id="pleasure-and-help"', essay)
        self.assertIn("F97-famine-affluence-morality.xhtml#singer-demanding-help", essay)
        self.assertIn("01-pleasure-is-an-end.xhtml#pleasure-and-help", note)
        self.assertIn("PDF文字提取只得到封面", note)
        self.assertIn("不是原文结论，也不是已获证明的反驳", note)
        self.assertIn("未独立核验文中1971年", note)


if __name__ == "__main__":
    unittest.main()
