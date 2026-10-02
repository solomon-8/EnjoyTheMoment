"""Check source boundaries and full text, not the merits of a work-time policy."""
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


class IdlenessArgumentTests(unittest.TestCase):
    def test_argument_keeps_difficult_conditions_and_counterarguments(self):
        text = (ROOT / "essays/07-rest-is-not-work.md").read_text()
        for phrase in (
            "劳动值得尊重", "劳动越多越值得尊重",
            "社会主义立场的论战文章",
            "原文的主张，不是本书核实过的当代效果",
            "质量、收入、需求和人员都不变",
            "维护与交接也已包含在六小时里",
            "额外的物品也有人愿意使用",
            "不能把它先说成没人要的垃圾",
            "如果那些东西正有人急需呢",
            "少做事的自由，不必用多消费来偿还",
            "不能把每一句都当可执行政策",
            "没有休息，是因为你不懂休息",
            "设想一个虚构周六", "不喜欢这次安排，不等于没有资格拥有这段时间",
        ):
            self.assertIn(phrase, text)
        rendered = build.markdown(text, "essays/07-rest-is-not-work.md")
        for anchor in ("rest-lafargue", "rest-productivity-defense", "rest-leisure-command",
                       "rest-returns", "rest-real-income", "rest-paid-evening",
                       "rest-no-verdict"):
            self.assertEqual(rendered.count(f'id="{anchor}"'), 1)
            self.assertIn(f'href="#{anchor}"', rendered)
        self.assertIn('id="rest-work-authority"', text)
        self.assertNotIn("<!-- pick:", text)

    def test_two_versions_are_not_two_experiments_or_a_policy(self):
        text = (ROOT / "docs/evidence/F82-right-to-be-lazy.md").read_text()
        for phrase in (
            "#77029", "#52984", "2025-10-11", "2016-09-05", "2024-10-23",
            "Henri Oriol", "Henry ORIOL", "Charles H. Kerr",
            "不是全书校勘", "没有另查1880年原刊",
            "英译第四节开头", "法文转录中仍位于III内",
            "强制消费和休闲安排", "反犹贬称", "不接受",
            "数字页码", "不是本次亲阅扫描的证明",
            "不把两种语言版本算作两项独立支持",
            "不证明三小时工作制",
        ):
            self.assertIn(phrase, text)
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        note = next(n for n in notes if n["id"] == "F82")
        self.assertEqual(note["text"], text)
        self.assertEqual(note["source_kind"],
                         "historical_social_polemic_primary_and_translation")
        self.assertEqual(len(notes), 132)
        research = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(research), 47)
        self.assertNotIn("F82", {r["id"] for r in research})
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("F82" not in c["background_ids"] for c in cards))

    def test_route_retrieves_full_text_and_visible_context(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {d["id"]: d for d in documents}
        route = next(r for r in routes if r["id"] == "R41")
        targets = {"E07", "F82", "C08", "C09", "C21", "E01", "B05", "N05"}
        self.assertEqual(set(route["targets"]), targets)
        self.assertTrue(targets <= {d["id"] for d in read.linked_records(route, documents, ROOT)})
        self.assertIn("不自动给时间表", route["text"])
        self.assertEqual(len(routes), 81)
        for identifier, path in (
            ("E07", "essays/07-rest-is-not-work.md"),
            ("F82", "docs/evidence/F82-right-to-be-lazy.md"),
        ):
            raw = (ROOT / path).read_bytes()
            self.assertEqual(by_id[identifier]["text"], raw.decode())
            self.assertEqual(by_id[identifier]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertEqual((ROOT / "llms-full.txt").read_text().count(raw.decode().strip()), 1)

    def test_epub_keeps_new_source_and_old_tradeoffs(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            essay = archive.read("EPUB/text/essays--07-rest-is-not-work.xhtml").decode()
            note = archive.read("EPUB/text/docs--evidence--F82-right-to-be-lazy.xhtml").decode()
            for anchor in ("rest-lafargue", "rest-productivity-defense",
                           "rest-leisure-command", "rest-work-authority", "rest-paid-evening"):
                self.assertEqual(essay.count(f'id="{anchor}"'), 1)
            self.assertIn("质量、收入、需求和人员都不变", essay)
            self.assertIn("永远拿不到那次任务的报酬", essay)
            self.assertIn("F82-right-to-be-lazy.xhtml", essay)
            self.assertIn("book--21-free-time.xhtml#time-empty", essay)
            self.assertIn("essays--01-pleasure-is-an-end.xhtml#pleasure-not-quota", essay)
            self.assertIn("不是全书校勘", note)
            self.assertIn("essays--07-rest-is-not-work.xhtml#rest-productivity-defense", note)
            self.assertEqual(note.count("<table>"), 0)
            for anchor in ("source-labor-dogma", "source-machine-leisure",
                           "source-production-defense", "source-forced-leisure"):
                self.assertEqual(note.count(f'id="{anchor}"'), 1)
            self.assertIn("今日工时或消费配额", note)


if __name__ == "__main__":
    unittest.main()
