"""C19 argument fidelity and navigation, not a measure of reader interest."""
import hashlib
import json
import re
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check
import read

SOURCE = "book/19-games.md"
SECTIONS = ("games-value", "games-materials", "games-outcomes",
            "games-participation", "games-not-hours")
RETAINED = (
    "games-paid-skip", "games-skip-example", "games-skip-menu",
    "games-skip-objection", "games-delegation", "games-othello",
    "games-hanabi", "games-chosen-rules", "games-uncertainty",
    "games-difficulty", "games-hints",
    "规则不是快乐的敌人但每条规则都值得认领",
)


class GameArgumentStructureTests(unittest.TestCase):
    def test_price_question_precedes_selection_menu_without_losing_destinations(self):
        text = (ROOT / SOURCE).read_text()
        self.assertEqual(len(re.findall(r"^## ", text, re.M)), len(SECTIONS))
        positions = [text.index(f'id="{anchor}"') for anchor in SECTIONS]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(text.index('id="games-skip-example"'),
                        text.index("### 先问想经历什么"))
        for anchor in SECTIONS + RETAINED:
            self.assertIn(anchor, check.anchors_for(text))
        for phrase in ("不涉及下注、付费抽取或真实收益",
                       "抽前不知编号", "耗时、操作与胜利结果相同",
                       "没有其他奖励、线索或后续回合",
                       "胜率为4/6", "为2/6", "额外信息",
                       "选了不同目标", "不能把所有不利结果"):
            self.assertIn(phrase, text)

    def test_rules_sources_and_cost_objections_remain_distinct(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in ("没有证明乙是最优解", "原规则、共同商定的变体、没说出口的暗号",
                       "乙此前没有收到", "不是随机分配人去玩",
                       "愿意购买一个出口，不等于希望入口越来越难走",
                       "不是额外收费政策", "15 + 20 + 5 = 40分钟"):
            self.assertIn(phrase, text)
        for target in ("F42-othello-choice.md", "F43-hanabi-information.md",
                       "F09-game-difficulty.md", "B09-games.md"):
            self.assertIn(target, text)
        self.assertIn("对具体人的承诺", text)
        self.assertIn("系统列出的收集进度和每日任务", text)
        self.assertNotIn("<!-- pick:", text)

    def test_full_text_exports_contain_the_complete_argument(self):
        documents, _ = read.load_documents(ROOT)
        chapter = next(d for d in documents if d["id"] == "C19")
        raw = (ROOT / SOURCE).read_bytes()
        self.assertEqual(chapter["text"], raw.decode())
        self.assertEqual(chapter["source_sha256"], hashlib.sha256(raw).hexdigest())
        export = next(c for c in json.loads(
            (ROOT / "data/chapters.json").read_text())["chapters"] if c["id"] == "C19")
        self.assertEqual(export["text"], raw.decode().strip())
        self.assertIn(raw.decode(), (ROOT / "llms-full.txt").read_text())

    def test_reader_and_epub_keep_structure_and_example(self):
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            chapter = archive.read("EPUB/text/book--19-games.xhtml").decode()
        for anchor in SECTIONS + RETAINED:
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
            self.assertEqual(chapter.count(f'id="{anchor}"'), 1)
        for phrase in ("六张背面相同", "实际翻到5", "额外信息",
                       "两条路没有其他差别", "不是额外收费政策"):
            self.assertIn(phrase, chapter)
        self.assertIn("<h2", chapter)
        self.assertIn("<h3", chapter)
        self.assertIn("<h4", chapter)


if __name__ == "__main__":
    unittest.main()
