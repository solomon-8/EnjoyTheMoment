"""Check the argument's structure and evidence boundaries, not its popularity."""
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


class GrooveTests(unittest.TestCase):
    def test_four_onsets_change_position_not_count_or_duration(self):
        text = (ROOT / "book/37-nightlife.md").read_text()
        rows = {}
        for line in text.splitlines():
            if line.startswith("| A |") or line.startswith("| B |"):
                label, symbols = [s.strip() for s in line.split("|")[1:3]]
                rows[label] = symbols.strip("`").split()
        self.assertEqual(set(rows), {"A", "B"})
        for symbols in rows.values():
            self.assertEqual(len(symbols), 8)
            self.assertEqual(symbols.count("●"), 4)
            self.assertEqual(symbols.count("·"), 4)
        onsets = {k: {i for i, c in enumerate(v) if c == "●"}
                  for k, v in rows.items()}
        self.assertEqual(onsets["A"], {0, 2, 4, 6})
        self.assertEqual(onsets["B"], {0, 1, 4, 6})
        self.assertEqual(onsets["A"] - onsets["B"], {2})
        self.assertEqual(onsets["B"] - onsets["A"], {1})
        for phrase in (
            "不是在纸上证明听感", "没有计算论文的多声部切分指数",
            "不是“凡是落在`&`上的声音都叫切分”",
            "不标持续时间、音色或音量",
            "明明知道下一拍会来，为什么还想一直跳",
            "知道下一拍在哪里，不等于已经经历过下一拍",
            "这一刻没有升级，我仍想让它继续",
            "重复也可能真的无聊",
            "这个场面是说明，不是实验参与者的自述",
        ):
            self.assertIn(phrase, text)
        html = build.markdown(text, "book/37-nightlife.md")
        self.assertEqual(html.count("<table>"), 3)
        for anchor in (
            "nightlife-known-beat", "nightlife-syncopation",
            "nightlife-groove-study", "nightlife-repeat-participation",
            "nightlife-sequence", "nightlife-warehouse", "nightlife-objections",
        ):
            self.assertEqual(html.count(f'id="{anchor}"'), 1)

    def test_null_sensitivity_and_correction_stay_in_reader_and_note(self):
        chapter = (ROOT / "book/37-nightlife.md").read_text()
        self.assertIn("“想动”的二次模型整体检验不显著", chapter)
        self.assertIn("愉悦模型仍显著", chapter)
        self.assertIn("这又不等于两个指标之间的差异已经被检验成立", chapter)
        self.assertIn("这是解释性推测", chapter)
        text = (ROOT / "docs/evidence/B41-groove-syncopation.md").read_text()
        for phrase in (
            "2014-04-16", "2015-09-24", "10.1371/journal.pone.0139409",
            "Rouwen Canal-Bruland是编辑",
            "这是作者声明，不是本书复现结论",
            "修正版图S1—S4/S7未逐页核读",
            "包含17岁参与者", "66人", "余57人",
            "未试听50段实验音频", "没有记录实际运动",
            "17、17、16个刺激", "分母是50段刺激",
            "S = N − Ndi + I", "−1 − (−3) + 5 = 7",
            "不自行裁定并重算刺激指数",
            "R² = 4267", ".4267", ".3474",
            "不是“快乐提升34.74%／42.67%”",
            "一项显著、另一项不显著，不足以证明两项彼此差异显著",
            "p < .005", ".0448", "p = .178", ".2133", "p = .007",
            "尾部口径存在疑点", "筛选后的48人", "45人",
            "本实验没有实际运动记录，不能直接证实身体参与机制",
        ):
            self.assertIn(phrase, text)
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual({r["id"] for r in records},
                         {f"B{i:02d}" for i in range(1, 44)})
        record = next(r for r in records if r["id"] == "B41")
        self.assertEqual(record["doi"], "10.1371/journal.pone.0094446")
        self.assertEqual(record["verified_at"], "2026-10-01")
        self.assertEqual(record["access_level"], "full_text")
        self.assertFalse(record["directly_validates_cards"])
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("B41" not in c["background_ids"] for c in cards))

    def test_whole_source_and_route_remain_retrievable(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {d["id"]: d for d in documents}
        for identifier, path in (
            ("C37", "book/37-nightlife.md"),
            ("N41", "docs/evidence/B41-groove-syncopation.md"),
        ):
            raw = (ROOT / path).read_bytes()
            self.assertEqual(by_id[identifier]["text"], raw.decode())
            self.assertEqual(by_id[identifier]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertEqual((ROOT / "llms-full.txt").read_text().count(
                raw.decode().strip()), 1)
        route = next(r for r in routes if r["id"] == "R70")
        self.assertEqual(set(route["targets"]), {
            "C37", "F71", "B41", "N41", "C11", "C13", "C27", "C16",
            "C05", "C09", "C10", "F04", "E02", "E04",
        })
        self.assertTrue(set(route["targets"]) <= {
            r["id"] for r in read.linked_records(route, documents, ROOT)
        })
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        self.assertEqual(len(notes), 126)
        note = next(n for n in notes if n["id"] == "N41")
        self.assertEqual(note["source_kind"], "study_reading_note")
        self.assertEqual(note["text"], by_id["N41"]["text"])

    def test_epub_keeps_argument_table_and_linked_qualifications(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            chapter = archive.read("EPUB/text/book--37-nightlife.xhtml").decode()
            source = archive.read(
                "EPUB/text/docs--evidence--B41-groove-syncopation.xhtml").decode()
            self.assertIn('id="nightlife-syncopation"', chapter)
            self.assertIn('id="nightlife-repeat-participation"', chapter)
            self.assertEqual(chapter.count("<table>"), 3)
            self.assertIn("docs--evidence--B41-groove-syncopation.xhtml", chapter)
            self.assertIn("“想动”的二次模型整体检验不显著", chapter)
            self.assertIn("p = .178", source)
            self.assertIn("book--37-nightlife.xhtml#nightlife-known-beat", source)


if __name__ == "__main__":
    unittest.main()
