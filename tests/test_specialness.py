"""Retrieval and source-scope guards, not tests of persuasion or psychology."""
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


class SpecialnessTests(unittest.TestCase):
    def test_argument_keeps_original_scenario_objection_and_old_source_boundaries(self):
        source = "book/01-start-now.md"
        text = (ROOT / source).read_text()
        for phrase in (
            "接下来是一个原创假想，不是调查记录",
            "本来是让本子参与日子，后来却变成让日子配得上本子",
            "过去没用，并不自动证明今天更不该用",
            "这段访谈不是论文全文",
            "今天不必先发生好事，才有资格用好东西",
            "珍惜空白因此并不一定是误会",
            "写了第一页，不欠这本本子一本完整日记",
            "他的商业讨论与本书的生活主张，不是同一个目标",
            "不意味着用得越快越好",
            "J001", "J006", "另有 80 名学生", "后续原因调查只有 33 人",
        ):
            self.assertIn(phrase, text)
        rendered = build.markdown(text, source)
        for anchor in (
            "today-priority", "today-use", "today-first-page",
            "today-making-an-occasion", "today-first-use", "today-not-turnover",
            "today-voucher", "today-future", "today-not-redemption",
        ):
            self.assertEqual(rendered.count(f'id="{anchor}"'), 1)
        self.assertEqual(rendered.count("<table>"), 1)
        self.assertIn('href="#f79"', rendered)
        self.assertIn('href="#pleasure-options"', rendered)
        self.assertIn('href="#home-continuity"', rendered)

    def test_interview_is_not_upgraded_to_a_read_study_or_card_evidence(self):
        source = "docs/evidence/F79-specialness-interview.md"
        text = (ROOT / source).read_text()
        for phrase in (
            "edited transcript", "没有收听录音", "没有核读论文正文",
            "本次查询的索引", "未取得补充材料", "鞋并不是从未穿过",
            "使用意向也不能写成观察到真实开瓶",
            "没有样本量、完整流程、统计表",
            "不新增B系列背景研究", "不把开封率、兑换率或库存周转当生活成绩",
        ):
            self.assertIn(phrase, text)
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        note = next(n for n in notes if n["id"] == "F79")
        self.assertEqual(note["text"], text)
        self.assertEqual(note["source_kind"], "researcher_edited_interview_not_full_paper")
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual({r["id"] for r in records}, {f"B{n:02d}" for n in range(1, 51)})
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("F79" not in c["background_ids"] for c in cards))

    def test_retrieval_keeps_complete_prose_and_original_route(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {d["id"]: d for d in documents}
        full = (ROOT / "llms-full.txt").read_text()
        for identifier, source in (
            ("C01", "book/01-start-now.md"),
            ("F79", "docs/evidence/F79-specialness-interview.md"),
        ):
            data = (ROOT / source).read_bytes()
            self.assertEqual(by_id[identifier]["text"], data.decode())
            self.assertEqual(by_id[identifier]["source_sha256"], hashlib.sha256(data).hexdigest())
            prose = data.decode().partition('<a id="j')[0].strip()
            self.assertIn(prose, full)
        route = next(r for r in routes if r["id"] == "R02")
        self.assertEqual(set(route["targets"]),
                         {"C01", "B17", "N17", "F79", "F95", "E01", "E03", "E10", "C18"})
        self.assertIn("先回应完整论证和保留理由", route["text"])
        self.assertIn("不自动生成清库存或采购清单", route["text"])
        self.assertEqual(len(routes), 82)

    def test_epub_preserves_new_argument_and_existing_voucher_table(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            chapter = archive.read("EPUB/text/book--01-start-now.xhtml").decode()
            source = archive.read("EPUB/text/docs--evidence--F79-specialness-interview.xhtml").decode()
            for anchor in ("today-first-page", "today-making-an-occasion",
                           "today-first-use", "today-not-turnover", "today-voucher"):
                self.assertEqual(chapter.count(f'id="{anchor}"'), 1)
            self.assertEqual(chapter.count("<table>"), 1)
            self.assertIn("10 / 32", chapter)
            self.assertIn("2 / 32", chapter)
            self.assertIn("F79-specialness-interview.xhtml", chapter)
            self.assertIn("没有核读论文正文", source)
            self.assertIn("book--01-start-now.xhtml#today-first-page", source)


if __name__ == "__main__":
    unittest.main()
