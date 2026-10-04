"""Source/argument preservation, not a test of enjoyment or artistic correctness."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import read
SOURCE = "book/26-collecting.md"
NOTE = "docs/evidence/F87-candy-and-continuity.md"
ANCHORS = ("collecting-preservation", "collecting-candy", "collecting-not-refill")

class CollectingContinuityTests(unittest.TestCase):
    def test_material_change_is_not_permission_to_change_everything(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in ("糖果少了，作品就少了吗", "是否补充", "谁也不能拿", "删掉了允许个人取糖的条件", "取糖不等于取得全部布置权", "不能从作品说明直接推出它们都可替代", "三种收藏目的", "没有调查这件作品各次展示的人员", "不保证更保值"):
            self.assertIn(phrase, text)
        self.assertIn("01-start-now.md#today-first-use", text)
        self.assertIn("36-home.md#home-continuity", text)
        self.assertIn('**“允许”不是“要求”**', text)

    def test_in_process_source_is_not_an_experiment_or_installed_state(self):
        note = (ROOT / NOTE).read_text()
        for phrase in ("Draft – 1 September 2026", "仍在发展的", "第1—3页正文与脚注", "CC BY 4.0", "未复制图像", "不是永久不变的终稿", "不把175磅写成已独立证实", "每天补满", "未经授权摆放也不构成它"):
            self.assertIn(phrase, note)
        data = json.loads((ROOT / "data/evidence.json").read_text())
        n = next(n for n in data["notes"] if n["id"] == "F87")
        self.assertEqual(n["source_kind"], "artwork_record_and_in_process_manifestation_tenets")
        self.assertEqual(n["text"], note)
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(records), 50)
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("F87" not in card["background_ids"] for card in cards))

    def test_full_retrieval_and_route_preserve_objections_and_source_dates(self):
        docs, routes = read.load_documents(ROOT)
        for ident, source in (("C26", SOURCE), ("F87", NOTE)):
            raw = (ROOT / source).read_bytes()
            d = next(d for d in docs if d["id"] == ident)
            self.assertEqual(d["text"], raw.decode())
            self.assertEqual(d["source_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertIn(raw.decode(), (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R21")
        targets = {"C26", "F14", "F38", "F39", "F87", "C01", "C36"}
        self.assertEqual(set(route["targets"]), targets)
        self.assertTrue(targets <= {d["id"] for d in read.linked_records(route, docs, ROOT)})
        for phrase in ("2026-09-01", "未核实时展示", "不声称观看过作品图像", "允许取糖不等于要求取"):
            self.assertIn(phrase, route["text"])

    def test_exports_keep_legacy_art_and_new_reciprocal_links(self):
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            chapter = z.read("EPUB/text/book--26-collecting.xhtml").decode()
            note = z.read("EPUB/text/docs--evidence--F87-candy-and-continuity.xhtml").decode()
        for anchor in ANCHORS:
            self.assertEqual(html.count('id="' + anchor + '"'), 1)
            self.assertEqual(chapter.count('id="' + anchor + '"'), 1)
        for anchor in ("collecting-crosses", "collecting-layers", "collecting-digital", "collecting-return", "collecting-abundance"):
            self.assertIn('id="' + anchor + '"', chapter)
        self.assertEqual(chapter.count("<table>"), 3)
        self.assertEqual(chapter.count("<img "), 2)
        self.assertIn("book--26-collecting.xhtml#collecting-not-refill", note)
        self.assertIn("docs--evidence--F87-candy-and-continuity.xhtml#f87-tenets", chapter)
        self.assertIn("book--36-home.xhtml#home-continuity", chapter)
        self.assertIn("book--01-start-now.xhtml#today-first-use", chapter)

if __name__ == "__main__":
    unittest.main()
