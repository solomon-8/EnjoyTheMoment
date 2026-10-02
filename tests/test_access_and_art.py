"""Guard provenance and complete retrieval, not accessibility certification."""
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


class AccessAndArtTests(unittest.TestCase):
    def test_scene_does_not_confuse_events_speech_and_interpretation(self):
        text = (ROOT / "book/09-constrained.md").read_text()
        scene = text.split('<a id="constrained-access-scene"></a>', 1)[1].split(
            '<a id="constrained-access-tension"></a>', 1)[0]
        for phrase in (
            "本书原创", "不是实际演出方案",
            "桌上有两只杯子", "两下敲门声", "这里只有我一个人",
            "没有揭示此前是否有人来过", "两只杯子不证明有两个人",
            "不该擅自补上的判断", "把角色台词当全知说明",
            "本例没有完成这些设计", "有意且可选择的作品安排",
        ):
            self.assertIn(phrase, scene)
        self.assertEqual(len([line for line in scene.splitlines()
                              if line.startswith("|")]), 5)
        self.assertEqual(build.markdown(text, "book/09-constrained.md").count(
            "<table>"), 3)
        for phrase in (
            "被允许参加，与有机会决定大家怎样参加",
            "不是每个观众都必须成为策划",
            "受资源限制",
            "没能和原来的朋友一起看",
            "被考虑，不等于欠一份感动",
            "不必先把这些愿望翻译成康复",
        ):
            self.assertIn(phrase, text)

    def test_practice_account_does_not_become_outcome_evidence(self):
        note = (ROOT / "docs/evidence/F84-access-and-theatre-making.md").read_text()
        for phrase in (
            "2026-08-04", "2026年2月", "2023-08-22", "2024-05-13",
            "发布日期不替代活动日期", "Hana Pascal Keegan", "Laura Guthrie",
            "British Sign Language是英国手语",
            "未参加活动、未观看现场", "不是本书核读该剧剧本或演出的证据",
            "每位参与者同等拥有最终决定权",
            "本书没有依据这个标签推断灯光",
            "不是给具体障碍群体做过测试的剧本",
            "没有用本记录验证J049–J054",
        ):
            self.assertIn(phrase, note)
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        record = next(n for n in notes if n["id"] == "F84")
        self.assertEqual(record["text"], note)
        self.assertEqual(record["source_kind"],
                         "theatre_practitioner_account_and_production_description")
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(records), 44)
        self.assertNotIn("F84", {r["id"] for r in records})
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("F84" not in c["background_ids"] for c in cards))

    def test_anchors_and_full_text_keep_objections_with_the_argument(self):
        documents, routes = read.load_documents(ROOT)
        docs = {d["id"]: d for d in documents}
        route = next(r for r in routes if r["id"] == "R81")
        self.assertEqual(set(route["targets"]), {"C09", "F84", "E06", "C13", "C12", "E11"})
        self.assertTrue(set(route["targets"]) <= {
            d["id"] for d in read.linked_records(route, documents, ROOT)
        })
        for phrase in ("不自动改答成出门训练", "不要求观众变成顾问",
                       "不是效果研究或合规标准", "角色台词", "不验证J卡"):
            self.assertIn(phrase, route["text"])
        full = (ROOT / "llms-full.txt").read_text()
        for ident, path in (
            ("C09", "book/09-constrained.md"),
            ("F84", "docs/evidence/F84-access-and-theatre-making.md"),
        ):
            raw = (ROOT / path).read_bytes()
            self.assertEqual(docs[ident]["text"], raw.decode())
            self.assertEqual(docs[ident]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            prose = raw.decode().partition('<a id="j')[0].strip()
            self.assertIn(prose, full)
        html = (ROOT / "index.html").read_text()
        for anchor in (
            "constrained-access", "constrained-access-authorship",
            "constrained-access-making", "constrained-access-scene",
            "constrained-access-tension", "constrained-access-taste",
            "constrained-cognitive", "constrained-three-arrangements",
            "constrained-authority",
        ):
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
        for path in ("essays/06-real-life-constraints.md", "book/13-live-events.md"):
            self.assertIn("#constrained-access-", (ROOT / path).read_text())

    def test_epub_keeps_source_backlinks_and_existing_cards(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            chapter = z.read("EPUB/text/book--09-constrained.xhtml").decode()
            note = z.read(
                "EPUB/text/docs--evidence--F84-access-and-theatre-making.xhtml").decode()
            for phrase in ("被考虑，不等于欠一份感动", "本例没有完成这些设计",
                           "没能和原来的朋友一起看"):
                self.assertIn(phrase, chapter)
            self.assertIn("docs--evidence--F84-access-and-theatre-making.xhtml", chapter)
            self.assertIn("book--09-constrained.xhtml#constrained-access-scene", note)
            for n in range(49, 55):
                self.assertIn(f'id="j{n:03d}"', chapter)


if __name__ == "__main__":
    unittest.main()
