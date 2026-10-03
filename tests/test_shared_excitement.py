"""Preserve argument, evidence limits and access; not reader appeal scores."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import read

ESSAY = "essays/02-excitement-without-escalation.md"
NOTE = "docs/evidence/B48-dancing-in-time.md"
ANCHORS = ("excitement-together", "excitement-shared-cost",
           "excitement-synchrony-study")


class SharedExcitementTests(unittest.TestCase):
    def test_conflict_precedes_evidence_and_keeps_a_real_cost(self):
        text = (ROOT / ESSAY).read_text()
        self.assertEqual([text.index(f'id="{a}"') for a in ANCHORS],
                         sorted(text.index(f'id="{a}"') for a in ANCHORS))
        for phrase in (
            "这是原创假想，不是实验结果",
            "共同经历不是把两份私人自由原样叠起来",
            "同一遍不能既随时由小禾重启",
            "轮流能分配机会，不会让同一遍同时成为两个版本",
            "不能用同频要求所有人交出同一种感受",
            "不需要再靠增进人脉、提高合作效率来报销",
            "这项研究不裁定两位朋友该怎样选",
        ):
            self.assertIn(phrase, text)
        self.assertIn("](#excitement-together)", text.split(ANCHORS[0] + '"></a>')[0])

    def test_primary_source_identity_scope_and_nonvalidation(self):
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        record = next(r for r in records if r["id"] == "B48")
        self.assertEqual(record["doi"], "10.1177/20592043231155416")
        self.assertEqual(record["access_level"], "full_text")
        self.assertFalse(record["directly_validates_cards"])
        self.assertEqual({r["id"] for r in records},
                         {f"B{n:02d}" for n in range(1, 49)})
        self.assertEqual([r["id"] for r in records
                          if r["access_level"] == "abstract_only"], ["B44"])
        note = (ROOT / NOTE).read_text()
        for phrase in (
            "大学封面加印刷1–13页，共14页", "没有与出版方下载逐字比对",
            "没有取得底层数据、代码或独立预注册",
            "48人组成24对", "主要动作分析剩19对", "剩17对",
            "其余四个问题没有报告显著条件效应",
            "未显著不等于证明等效", "没有直接问社会联结强弱",
            "F(2,54)", "115到121.675", "无法确认实际检验怎样执行",
            "不是眼动仪", "没有被彼此排除", "原创规范论证",
        ):
            self.assertIn(phrase, note)
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("B48" not in c["background_ids"] for c in cards))

    def test_original_claim_and_results_are_not_collapsed(self):
        text = (ROOT / ESSAY).read_text()
        for phrase in (
            "只有**同步与错开四分之一拍**之间的差异显著",
            "其余四项自报也没有显著条件效应",
            "也不能把未显著改写成确定没有影响",
            "可用头部资料剩19对", "平均人际距离却没有显著差异",
            "时间上配合、觉得互动不错、自己尽兴，是可以分别回答的问题",
        ):
            self.assertIn(phrase, text)

    def test_full_text_route_and_cross_format_links(self):
        documents, routes = read.load_documents(ROOT)
        docs = {d["id"]: d for d in documents}
        full = (ROOT / "llms-full.txt").read_text()
        for ident, path in (("E02", ESSAY), ("N48", NOTE)):
            raw = (ROOT / path).read_bytes()
            self.assertEqual(docs[ident]["text"], raw.decode())
            self.assertEqual(docs[ident]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertIn(raw.decode(), full)
        route = next(r for r in routes if r["id"] == "R03")
        self.assertEqual(set(route["targets"]), {
            "E02", "E03", "C05", "C06", "C21", "C27",
            "B24", "N24", "B45", "N45", "B48", "N48",
        })
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            essay = archive.read(
                "EPUB/text/essays--02-excitement-without-escalation.xhtml").decode()
            note = archive.read(
                "EPUB/text/docs--evidence--B48-dancing-in-time.xhtml").decode()
        for anchor in ANCHORS:
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
            self.assertEqual(essay.count(f'id="{anchor}"'), 1)
        self.assertIn('href="#n48"', html)
        self.assertIn("docs--evidence--B48-dancing-in-time.xhtml#synchrony-limits",
                      essay)
        self.assertIn("essays--02-excitement-without-escalation.xhtml"
                      "#excitement-shared-cost", note)


if __name__ == "__main__":
    unittest.main()
