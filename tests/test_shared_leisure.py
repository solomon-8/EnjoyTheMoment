"""Keep the argument, source scope and reader paths distinct across formats."""
import json
import re
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SharedLeisureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chapter = (ROOT / "book/09-constrained.md").read_text()
        cls.note = (ROOT / "docs/evidence/F50-cognitive-labor.md").read_text()

    def test_five_main_sections_and_existing_scene_remain_navigable(self):
        prose = self.chapter.split('<a id="j049"></a>')[0]
        self.assertEqual(len(re.findall(r"^## ", prose, re.M)), 5)
        self.assertEqual(len(re.findall(r"^### ", prose, re.M)), 12)
        self.assertEqual(len(re.findall(r"^#### ", prose, re.M)), 4)
        html = (ROOT / "index.html").read_text()
        for anchor in ("constrained-time", "constrained-labor", "constrained-credit",
                       "constrained-shared", "constrained-participation",
                       "constrained-cognitive", "constrained-three-arrangements",
                       "constrained-authority", "constrained-access-scene"):
            self.assertEqual(prose.count(f'id="{anchor}"'), 1)
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
            self.assertIn(f'href="#{anchor}"', html)
        self.assertIn("同一幕里，谁可以同时发现那只杯子", prose)

    def test_credit_is_not_a_contribution_or_happiness_ranking(self):
        for phrase in ("临时策划可能非常费力", "没有得到感谢，不能单独证明",
                       "被看见、能拍板、能参加", "感谢可以让投入被看见，却不能替人参加聚会",
                       "更不必故意让安排失败", "不是该研究检验过的分工方案"):
            self.assertIn(phrase, self.chapter)
        self.assertIn("原创情境", self.chapter)
        self.assertIn("Holly", self.chapter)
        self.assertIn("Kendra", self.chapter)

    def test_dissertation_is_not_a_surrogate_for_unread_2019_article(self):
        for phrase in ("2022", "October 5, 2021", "PDF33–52", "44–49、59–76",
                       "136次个体访谈", "138人", "不能建立认知分工",
                       "不说明整章等于2019年文章", "不是已验证的家庭公平评分",
                       "不为J049–J054", "不能直接充当2019年论文的样本量"):
            self.assertIn(phrase, self.note)
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        note = next(n for n in notes if n["id"] == "F50")
        self.assertEqual(note["text"], self.note)
        self.assertEqual(note["source_kind"], "researcher_summary_and_dissertation_excerpt")
        self.assertIn(self.note, (ROOT / "llms-full.txt").read_text())
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertNotIn("10.1177/0003122419859007", {r["doi"] for r in records})

    def test_machine_route_and_epub_keep_limits_and_return_path(self):
        routes = json.loads((ROOT / "data/reading-map.json").read_text())["routes"]
        route = next(r for r in routes if r["id"] == "R12")
        self.assertEqual(route["targets"], ["C09", "E06", "F50"])
        serialized = json.dumps(route, ensure_ascii=False)
        for phrase in ("人数内部冲突", "非因果限制", "Holly/Kendra", "不自动缩成小份活动"):
            self.assertIn(phrase, serialized)
        epubs = list((ROOT / "downloads").glob("*.epub"))
        self.assertEqual(len(epubs), 1)
        with zipfile.ZipFile(epubs[0]) as z:
            chapter = z.read("EPUB/text/book--09-constrained.xhtml").decode()
            note = z.read("EPUB/text/docs--evidence--F50-cognitive-labor.xhtml").decode()
        self.assertIn('id="constrained-credit"', chapter)
        self.assertIn("被看见、能拍板、能参加", chapter)
        self.assertIn("136次个体访谈", note)
        self.assertIn("book--09-constrained.xhtml#constrained-credit", note)
        self.assertIn("docs--evidence--F50-cognitive-labor.xhtml", chapter)


if __name__ == "__main__":
    unittest.main()
