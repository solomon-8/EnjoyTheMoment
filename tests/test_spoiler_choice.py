"""Protect the study's scope and the distinction between enjoyment and consent."""
from pathlib import Path
import hashlib
import json
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read

ESSAY = "essays/02-excitement-without-escalation.md"
NOTE = "docs/evidence/B45-spoilers-and-experience.md"
ANCHORS = ("excitement-spoilers", "excitement-spoiler-study",
           "excitement-spoiler-choice")


class SpoilerChoiceTests(unittest.TestCase):
    def test_new_study_is_distinct_and_does_not_validate_cards(self):
        records = build.research_records(ROOT)
        self.assertEqual({r["id"] for r in records},
                         {f"B{i:02d}" for i in range(1, 48)})
        record = next(r for r in records if r["id"] == "B45")
        self.assertEqual(record["doi"], "10.61645/ssol.190")
        self.assertEqual(record["access_level"], "full_text")
        self.assertEqual(record["verified_at"], "2026-10-02")
        self.assertFalse(record["directly_validates_cards"])
        self.assertEqual(sum(r["access_level"] == "full_text"
                             for r in records), 46)
        self.assertEqual([r["id"] for r in records
                          if r["access_level"] == "abstract_only"], ["B44"])
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertTrue(all("B45" not in c["background_ids"] for c in cards))

    def test_observations_measures_and_reporting_limits_remain_visible(self):
        note = (ROOT / NOTE).read_text()
        for phrase in (
            "326名", "978次人—故事观察", "81次", "20次", "剩877次",
            "最多另少6次", "不是简单删掉101个人",
            "每人经历以下三种信息条件", "而非反复读同一篇",
            "随机斜率", "未收敛", "只有234人完成",
            "F(2, 579.5) = 1.25，p = .29", "F = 1.05",
            "不显著不是等效性证明", "F(2, 582.2) = 3.43，p = .03",
            "F(2, 580.1) = 6.04，p = .003", "不默默替作者改结果名称",
            "没有读取这些材料", "重跑分析或核对预注册偏离",
            "不复述那些结局",
        ):
            self.assertIn(phrase, note)
        self.assertNotIn("研究证明剧透无害", note)

    def test_suspense_is_not_reduced_to_unknown_outcomes(self):
        text = (ROOT / ESSAY).read_text()
        self.assertIn("**悬念**可以来自不知道接下来怎样", text)
        self.assertNotIn("**悬念**来自不知道接下来怎样", text)
        for phrase in (
            "不知道最终结果；在意过程怎样展开；愿不愿意再经历一次",
            "并不是每人把同一篇分别读三遍",
            "也没有证明三种安排等效",
            "不是877位读者", "不能将其说成重读效果实验",
            "不能给某个具体读者开一张“不许介意”的证明",
            "不必被教育成不懂作品",
        ):
            self.assertIn(phrase, text)
        opening = text.split('<a id="', 1)[0]
        self.assertIn("](#excitement-spoilers)", opening)

    def test_choice_argument_keeps_counterarguments_and_irreversibility(self):
        text = (ROOT / ESSAY).read_text()
        part = text.split('<a id="excitement-spoiler-choice"></a>', 1)[1]
        part = part.split('<a id="excitement-not-fun"></a>', 1)[0]
        for phrase in (
            "原创假想", "小满仍然很喜欢这个故事",
            "不能拿后来喜欢的事实", "事先并不存在的同意",
            "不欠所有人无限期沉默", "已经明确选择进入含结局的讨论",
            "只回答有没有，还是连过程与结果一起说",
            "不是要求每场讨论永远不能讲结局",
            "不能把一次已经说出的结局当作从未告知",
            "不把同意的论证说成实验结论",
        ):
            self.assertIn(phrase, part)

    def test_full_retrieval_route_and_reader_preserve_the_boundaries(self):
        documents, routes = read.load_documents(ROOT)
        docs = {d["id"]: d for d in documents}
        for ident, source in (("E02", ESSAY), ("N45", NOTE)):
            raw = (ROOT / source).read_bytes()
            self.assertEqual(docs[ident]["text"], raw.decode())
            self.assertEqual(docs[ident]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertIn(raw.decode(), (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R03")
        self.assertEqual(set(route["targets"]),
                         {"E02", "B24", "N24", "B45", "N45"})
        for phrase in ("不是人数", "不证明等效", "不能当重读研究",
                       "报告表述张力", "不是B45的实验结论"):
            self.assertIn(phrase, route["text"])
        html = (ROOT / "index.html").read_text()
        rendered_note = html.split('id="n45"', 1)[1].split("</details>", 1)[0]
        self.assertIn('href="#excitement-spoiler-study"', rendered_note)
        self.assertIn('href="#excitement-spoiler-choice"', rendered_note)
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            essay = archive.read(
                "EPUB/text/essays--02-excitement-without-escalation.xhtml").decode()
            note = archive.read(
                "EPUB/text/docs--evidence--B45-spoilers-and-experience.xhtml").decode()
        for anchor in ANCHORS:
            self.assertEqual(html.count('id="' + anchor + '"'), 1)
            self.assertEqual(essay.count('id="' + anchor + '"'), 1)
            self.assertIn("#" + anchor, route["text"])
        self.assertIn("essays--02-excitement-without-escalation.xhtml"
                      "#excitement-spoiler-study", note)
        self.assertIn("docs--evidence--B45-spoilers-and-experience.xhtml", essay)


if __name__ == "__main__":
    unittest.main()
