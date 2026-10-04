"""Guard text provenance and retrieval, not persuasion or enjoyment."""
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

CHAPTER = "book/01-start-now.md"
NOTE = "docs/evidence/F95-montaigne-and-living.md"


class TodayMontaigneTests(unittest.TestCase):
    def test_main_argument_keeps_the_counterpressure_of_achievement(self):
        text = (ROOT / CHAPTER).read_text()
        section = text.split('<a id="today-montaigne"></a>', 1)[1].split(
            '<a id="today-after-failure"></a>', 1)[0]
        for phrase in (
            "哪些事配被当作人的主要事业", "在蒙田笔下",
            "把普通生活看作本职", "大体被放到生活的附属与支撑位置",
            "如果支撑物总占满一天，被它支撑的生活何时发生",
            "并不是一场不许走神的专注考试",
            "不是一套保证快乐的注意训练",
            "他也重视节制", "没有它就不许开饭",
            "需要问的是今天究竟缺了什么",
        ):
            self.assertIn(phrase, section)
        self.assertIn("F95-montaigne-and-living.md", section)
        rendered = build.markdown(text, CHAPTER)
        for anchor in ("today-montaigne", "today-seasoning"):
            self.assertEqual(rendered.count(f'id="{anchor}"'), 1)
        self.assertIn('href="#f95"', rendered)
        self.assertEqual(rendered.count("<table>"), 1)

    def test_primary_text_is_not_upgraded_to_an_effect_study(self):
        text = (ROOT / NOTE).read_text()
        for phrase in (
            "1598年", "1603年", "EC7zA", "UH2xw", "ha5Wz", "vh9YM",
            "法文相邻长段不是全段核读",
            "未通读本章全部内容或整部《随笔集》",
            "不是纸本页码", "不是各活动效用的实测排名",
            "成就与午餐的关系", "不采用这种归责作为普遍结论",
            "不把它提炼成行动建议", "不是原作现成的两条定理",
            "不增加一项B系列研究", "没有转载整章",
        ):
            self.assertIn(phrase, text)
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        self.assertEqual(len(notes), len(build.EVIDENCE))
        note = next(n for n in notes if n["id"] == "F95")
        self.assertEqual(note["source_kind"], "philosophical_primary_text")
        self.assertEqual(note["text"], text)
        research = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertNotIn("F95", {r["id"] for r in research})
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertTrue(all("F95" not in c["background_ids"] for c in cards))

    def test_ai_route_preserves_original_text_and_limits(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {d["id"]: d for d in documents}
        for identifier, path in (("C01", CHAPTER), ("F95", NOTE)):
            raw = (ROOT / path).read_bytes()
            self.assertEqual(by_id[identifier]["text"], raw.decode())
            self.assertEqual(by_id[identifier]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            prose = raw.decode().partition('<a id="j')[0].strip()
            self.assertIn(prose, (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R02")
        self.assertIn("F95", route["targets"])
        for phrase in ("成就可以为乐趣调味", "不是全章校勘",
                       "禁止走神", "不冒充作者原话"):
            self.assertIn(phrase, route["text"])

    def test_epub_keeps_canonical_argument_and_two_way_source_links(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            chapter = z.read("EPUB/text/book--01-start-now.xhtml").decode()
            note = z.read("EPUB/text/docs--evidence--F95-montaigne-and-living.xhtml").decode()
            for anchor in ("today-montaigne", "today-seasoning"):
                self.assertEqual(chapter.count(f'id="{anchor}"'), 1)
            self.assertIn("docs--evidence--F95-montaigne-and-living.xhtml", chapter)
            self.assertIn("book--01-start-now.xhtml#today-seasoning", note)
            self.assertIn("montaigne-reading-scope", note)
            self.assertIn("没有它就不许开饭", chapter)
            self.assertEqual(chapter.count("<table>"), 1)


if __name__ == "__main__":
    unittest.main()
