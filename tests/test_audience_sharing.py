"""Protect abstract-only provenance and the value argument, not its popularity."""
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

ESSAY = "essays/08-life-without-an-audience.md"
NOTE = "docs/evidence/B44-sharing-intention.md"


class AudienceSharingTests(unittest.TestCase):
    def test_abstract_is_not_silently_upgraded_to_full_text(self):
        records = build.research_records(ROOT)
        record = next(r for r in records if r["id"] == "B44")
        self.assertEqual(record["access_level"], "abstract_only")
        self.assertEqual(record["doi"], "10.1093/jcr/ucx112")
        self.assertEqual(record["verified_at"], "2026-10-02")
        self.assertFalse(record["directly_validates_cards"])
        self.assertEqual(sum(r["access_level"] == "full_text" for r in records), 45)
        self.assertEqual([r["id"] for r in records
                          if r["access_level"] == "abstract_only"], ["B44"])
        note = (ROOT / NOTE).read_text()
        for phrase in (
            "2017年11月14日", "2018年4月1日", "只核对题名与出处",
            "本次返回403", "未取得主文", "不等于证明不存在更正",
            "对作者摘要报告的归属说明", "不是五次独立团队复现",
            "不能把B10当作B44全文的替代", "只读摘要不表示研究质量差",
            "没有把这项设定包装成B44的统计结果",
        ):
            self.assertIn(phrase, note)

    def test_comparisons_and_unmeasured_outcomes_are_not_conflated(self):
        essay = (ROOT / ESSAY).read_text()
        part = essay.split('<a id="audience-sharing-intention"></a>', 1)[1]
        part = part.split('<a id="audience-chosen-tradeoff"></a>', 1)[0]
        for phrase in (
            "两项现场与三项实验室研究", "两种拍摄目的的比较",
            "不是“发帖”与“完全不用手机”的比较",
            "只读到作者公开的摘要", "不能独立核查这些机制",
            "不能把两篇压成“拍照有益、分享有害”",
            "净收益结论", "原创假想", "不是上述研究里的参与者故事",
        ):
            self.assertIn(phrase, part)
        for phrase in (
            "223名线上参与者", "这不证明效果严格相等",
            "刻意没有让参与者回看照片", "发布与点赞也不是这篇论文直接验证",
        ):
            self.assertIn(phrase, essay)

    def test_value_argument_keeps_losses_and_the_strong_objection(self):
        part = (ROOT / ESSAY).read_text().split(
            '<a id="audience-chosen-tradeoff"></a>', 1)[1].split(
            '<a id="audience-staging"></a>', 1)[0]
        for phrase in (
            "不能倒过来说这些损失从未存在", "选择里可以有不划算的局部",
            "只要说“这是我想要的”", "都需要重新判断",
            "没有因为曾答应帮拍", "不保证成功", "可以觉得这个晚上不太值",
            "不必用“我确实费了力”要求别人交付感动",
            "接受一些等待和不被接住的可能", "代价由谁承担",
        ):
            self.assertIn(phrase, part)

    def test_full_retrieval_and_exports_preserve_access_boundaries(self):
        documents, routes = read.load_documents(ROOT)
        documents = {d["id"]: d for d in documents}
        for ident, source in (("E08", ESSAY), ("N44", NOTE)):
            raw = (ROOT / source).read_bytes()
            self.assertEqual(documents[ident]["text"], raw.decode())
            self.assertEqual(documents[ident]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertIn(raw.decode(), (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R45")
        self.assertEqual(set(route["targets"]),
                         {"E08", "C20", "B10", "N10", "B44", "N44"})
        for phrase in ("abstract_only", "未核主文", "原创假想", "观众不欠回应"):
            self.assertIn(phrase, route["text"])
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertTrue(all("B44" not in c["background_ids"] for c in cards))
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            essay = archive.read("EPUB/text/essays--08-life-without-an-audience.xhtml").decode()
            note = archive.read("EPUB/text/docs--evidence--B44-sharing-intention.xhtml").decode()
        for anchor in ("audience-sharing-intention", "audience-chosen-tradeoff"):
            self.assertEqual(html.count('id="' + anchor + '"'), 1)
            self.assertEqual(essay.count('id="' + anchor + '"'), 1)
            self.assertIn("essays--08-life-without-an-audience.xhtml#" + anchor, note)
        self.assertIn("docs--evidence--B44-sharing-intention.xhtml", essay)
        self.assertIn("abstract_only", note)


if __name__ == "__main__":
    unittest.main()
