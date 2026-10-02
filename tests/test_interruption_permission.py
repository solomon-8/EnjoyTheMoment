"""Retrieval and evidence-boundary checks; not a persuasion or welfare test."""
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


class InterruptionPermissionTests(unittest.TestCase):
    def test_strong_counterargument_and_delegation_are_both_present(self):
        text = (ROOT / "essays/10-pleasure-not-retention.md").read_text()
        for phrase in (
            "直接测出用户更喜欢", "给反方更有利的假设",
            "结果更合意，不等于过程已经获得授权",
            "愿意交出一部分安排权，本身可以是享受",
        ):
            self.assertIn(phrase, text)
        self.assertIn("事后补签的同意书", text)
        self.assertIn("尊重选择不等于许诺所有愿望都有免费方案", text)
        for anchor in ("digital-pleasure-permission", "digital-interruption-study",
                       "digital-interruption-delegation", "digital-commercial-costs"):
            self.assertEqual(text.count(f'<a id="{anchor}"></a>'), 1)
            self.assertEqual((ROOT / "index.html").read_text().count(
                f'id="{anchor}"'), 1)

    def test_study_replication_and_stages_do_not_collapse(self):
        note = (ROOT / "docs/evidence/B47-interruption-and-permission.md").read_text()
        for phrase in (
            "2020-06-03", "2020-06-12", "第12节", "第27节", "第28节",
            "5.38", "4.47", "p = .016", "4.27", "4.57", "p = .015",
            "p = .887", "不是380加1,125", "对数均值不是美元",
            "未显著不等于证明同等好看", "不是线上线下等效的证明",
            "未在本段交代分派算法", "没有下载原始数据",
            "不能独自决定谁有安排权", "不是两个新样本都推翻整篇论文",
        ):
            self.assertIn(phrase, note)
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        record = next(r for r in records if r["id"] == "B47")
        self.assertEqual(record["doi"], "10.1086/597030")
        self.assertEqual(record["access_level"], "full_text")
        self.assertEqual(record["verified_at"], "2026-10-03")
        self.assertFalse(record["directly_validates_cards"])
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("B47" not in c["background_ids"] for c in cards))
        self.assertNotIn("view_only=", note)

    def test_reading_route_preserves_complete_sources_and_limits(self):
        documents, routes = read.load_documents(ROOT)
        documents = {d["id"]: d for d in documents}
        for ident, path in (
            ("E10", "essays/10-pleasure-not-retention.md"),
            ("N47", "docs/evidence/B47-interruption-and-permission.md"),
        ):
            raw = (ROOT / path).read_bytes()
            self.assertEqual(documents[ident]["text"], raw.decode())
            self.assertEqual(documents[ident]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertIn(raw.decode().strip(), (ROOT / "llms-full.txt").read_text())
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        self.assertEqual(next(n for n in notes if n["id"] == "N47")["source_kind"],
                         "study_and_replication_reading_note")
        route = next(r for r in routes if r["id"] == "R80")
        self.assertTrue({"E10", "B42", "N42", "B28", "N28", "B47", "N47"}
                        <= set(route["targets"]))
        for phrase in ("两个阶段算两次独立复现", "预试未显著不证明等效",
                       "停止规则改变", "对数报价不是美元", "主动委托"):
            self.assertIn(phrase, route["text"])

    def test_epub_preserves_reciprocal_links_and_new_table(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            essay = z.read("EPUB/text/essays--10-pleasure-not-retention.xhtml").decode()
            note = z.read("EPUB/text/docs--evidence--B47-interruption-and-permission.xhtml").decode()
            self.assertIn("事后补签的同意书", essay)
            self.assertIn("docs--evidence--B47-interruption-and-permission.xhtml", essay)
            self.assertIn("essays--10-pleasure-not-retention.xhtml#digital-interruption-delegation", note)
            self.assertIn("对数均值不是美元", note)
            self.assertIn("<table", essay)
            self.assertIn("<table", note)


if __name__ == "__main__":
    unittest.main()
