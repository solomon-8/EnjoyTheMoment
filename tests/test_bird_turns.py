"""Reading and delivery regression checks; not behavioural or reader-effect tests."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import read

CHAPTER = "book/30-birdwatching.md"
NOTE = "docs/evidence/B49-flock-turns.md"
MAIN = ("birds-identification", "birds-relations", "birds-encounter", "birds-recording")
NEW = ("birds-turn-sequence", "birds-turn-fluctuations", "birds-turn-position")


class BirdTurnsTests(unittest.TestCase):
    def test_four_lines_keep_identification_nature_and_records(self):
        text = (ROOT / CHAPTER).read_text()
        self.assertEqual(len(re.findall(r"^## ", text, re.M)), 4)
        self.assertEqual(len(re.findall(r"^### ", text, re.M)), 18)
        for anchor in MAIN + NEW:
            self.assertEqual(text.count(f'<a id="{anchor}"></a>'), 1)
        for anchor in MAIN:
            self.assertIn(f"](#{anchor})", text)
        original = ["名字很有用", "先描述形状", "一个具体例子", "看行为",
                    "一群鸟的精彩", "“离我多远”", "“六七个邻居”",
                    "知道一点机制", "值得专门出门", "等待不是什么",
                    "鸟没有离开", "认鸟软件", "清单有两种用途",
                    "“可是追稀有鸟", "可以带走一个问题"]
        positions = [text.index("### " + title) for title in original]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(len(re.findall(r"^\| ---", text, re.M)), 3)
        self.assertEqual(len(re.findall(r"!\[.*?\]\(", text)), 1)
        for old in ("birds-flock", "birds-neighbors", "birds-field-study",
                    "birds-without-guarantee"):
            self.assertEqual(text.count(f'<a id="{old}"></a>'), 1)

    def test_timing_is_not_leadership_or_a_measured_motive(self):
        text = (ROOT / CHAPTER).read_text()
        for phrase in (
            "同一批鸟长期领导身份的认证",
            "不能把12次事件说成12个完全独立的群体",
            "没有看见外界变化", "排除了所有外界原因",
            "偏离占了多少时间，以及最强的一次偏离有多大",
            "不能写成已经测到“它害怕了”",
            "没有画出连续转弯轨迹",
            "结构方向仍在变化", "两次连续事件",
            "B30的2008年论文还做了二维粒子模型",
        ):
            self.assertIn(phrase, text)

    def test_reference_direction_changes_without_exchanging_locations(self):
        # This rechecks only the authored static example, not flight mechanics.
        points = {"A": (0, 1), "B": (1, 0)}
        def role(point, forward):
            x, y = point
            fx, fy = forward
            ahead = x * fx + y * fy
            left = fx * y - fy * x
            return "前方" if ahead > 0 else ("左侧" if left > 0 else "右侧")
        self.assertEqual([role(points["A"], f) for f in [(1, 0), (0, 1)]],
                         ["左侧", "前方"])
        self.assertEqual([role(points["B"], f) for f in [(1, 0), (0, 1)]],
                         ["前方", "右侧"])
        text = (ROOT / CHAPTER).read_text()
        self.assertIn("| A在O北侧 | 左侧 | 前方 |", text)
        self.assertIn("| B在O东侧 | 前方 | 右侧 |", text)
        self.assertIn("不模拟鸟的速度、反应或转弯半径", text)

    def test_ledger_and_full_retrieval_preserve_scope(self):
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual({r["id"] for r in records},
                         {f"B{n:02d}" for n in range(1, 50)})
        record = next(r for r in records if r["id"] == "B49")
        self.assertEqual(record["doi"], "10.1098/rsif.2015.0319")
        self.assertEqual(record["access_level"], "full_text")
        self.assertEqual(record["verified_at"], "2026-10-04")
        self.assertFalse(record["directly_validates_cards"])
        documents, routes = read.load_documents(ROOT)
        for identifier, path in [("C30", CHAPTER), ("N49", NOTE)]:
            doc = next(d for d in documents if d["id"] == identifier)
            self.assertEqual(doc["text"], (ROOT / path).read_text())
            self.assertEqual(doc["source_sha256"],
                             hashlib.sha256((ROOT / path).read_bytes()).hexdigest())
        route = next(r for r in routes if r["id"] == "R58")
        self.assertEqual(set(route["targets"]),
                         {"C30", "C29", "C15", "C20", "B30", "N30",
                          "F22", "F23", "B49", "N49"})
        for phrase in ("E11/E12同群连续", "未见外界变化", "不是等半径仿真",
                       "持续偏离", "永久领导身份", "PDF/补充为检查页"):
            self.assertIn(phrase, route["text"])
        note = (ROOT / NOTE).read_text()
        for phrase in ("HTML检查页", "未审核补充表S1", "1.8至12.9秒",
                       "170帧/秒"):
            self.assertIn(phrase, note)
        self.assertIn("E11与E12是同一鸟群", note)
        self.assertIn("没有设置连续轨迹", note)

    def test_exports_include_the_new_material_and_links(self):
        html = (ROOT / "index.html").read_text()
        full = (ROOT / "llms-full.txt").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            chapter = archive.read("EPUB/text/book--30-birdwatching.xhtml").decode()
            note = archive.read("EPUB/text/docs--evidence--B49-flock-turns.xhtml").decode()
        for anchor in MAIN + NEW:
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
            self.assertEqual(chapter.count(f'id="{anchor}"'), 1)
        self.assertEqual(chapter.count("<table>"), 3)
        self.assertEqual(chapter.count("<img "), 1)
        self.assertIn("docs--evidence--B49-flock-turns.xhtml", chapter)
        self.assertIn("book--30-birdwatching.xhtml#birds-turn-position", note)
        self.assertIn((ROOT / CHAPTER).read_text().strip(), full)
        self.assertIn((ROOT / NOTE).read_text().strip(), full)


if __name__ == "__main__":
    unittest.main()
