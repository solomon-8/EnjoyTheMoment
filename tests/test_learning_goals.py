"""Research fidelity and retrieval checks, not persuasion or training efficacy."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read

ESSAY = "essays/05-play-is-not-performance.md"
NOTE = "docs/evidence/B43-testing-and-retention.md"


class LearningGoalsTests(unittest.TestCase):
    def test_equal_time_and_delay_are_not_silently_generalized(self):
        essay = (ROOT / ESSAY).read_text()
        note = (ROOT / NOTE).read_text()
        part = essay.split('<a id="amateur-learning-study"></a>', 1)[1].split(
            '<a id="amateur-effective-for-what"></a>', 1)[0]
        for phrase in (
            "120名18—24岁", "都为7分钟", "不是同一批人被连续测了三次",
            "14个百分点", "不是“每个人提高14%”", "180人",
            "不能把三个均值排序写成每一对都显著不同",
            "学习与初测时段也不等长", "短文本身有多有趣",
            "不是整个过程的享受量表",
        ):
            self.assertIn(phrase, part)
        rows = re.findall(r"^\| (5分钟后|2天后|1周后) \| (\d+)% \| (\d+)% \|$",
                          part, re.M)
        self.assertEqual(rows, [("5分钟后", "81", "75"),
                                ("2天后", "54", "68"),
                                ("1周后", "42", "56")])
        for phrase in (
            "7页、带期刊排版", "未另与出版社下载逐字比对",
            "不能据此宣称没有勘误", "没有明确报告所有分组环节的随机分派",
            "20、25、35分钟", "实验2不是等总时长比较",
            "t(58) = 1.21", "没有在该处给出精确p值",
            "高分更难", "| SSSS | 3.8 | 2.5 | 4.8 |",
            "不是整段学习经历的享受", "没有把有反馈与无反馈随机比较",
        ):
            self.assertIn(phrase, note)
        self.assertEqual([4*5, 3*5+10, 5+3*10], [20, 25, 35])

    def test_effective_methods_do_not_choose_the_goal(self):
        essay = (ROOT / ESSAY).read_text()
        part = essay.split('<a id="amateur-effective-for-what"></a>', 1)[1].split(
            "\n## 为什么这里没有连续签到？", 1)[0]
        for phrase in (
            "先接受这个反对意见最有力的版本", "更好的练习可能减少",
            "原创假想", "没有把阅读实验直接当成唱歌教学",
            "取得替你选择目标的权力", "答应过明天脱稿演出",
            "不把“耍起”说成兼得保证", "可以先练",
            "不能仅因喜欢现在的过程，就宣布练习已经没有必要",
        ):
            self.assertIn(phrase, part)
        for phrase in (
            "未解决的遗憾", "不是论文验证过的分类工具",
            "没有复核双方引用的全部底层研究",
            "不是每件喜欢的事，都必须再负责养活另一部分生活",
        ):
            self.assertIn(phrase, essay)

    def test_new_source_is_complete_and_distinct_not_card_validation(self):
        documents, routes = read.load_documents(ROOT)
        documents = {d["id"]: d for d in documents}
        route = next(r for r in routes if r["id"] == "R47")
        self.assertEqual(set(route["targets"]),
                         {"E05", "C04", "E08", "B02", "N02", "B25", "N25",
                          "B43", "N43"})
        for ident, source in (("E05", ESSAY), ("N43", NOTE)):
            raw = (ROOT / source).read_bytes()
            self.assertEqual(documents[ident]["text"], raw.decode())
            self.assertEqual(documents[ident]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertIn(raw.decode(), (ROOT / "llms-full.txt").read_text())
        record = next(r for r in build.research_records(ROOT) if r["id"] == "B43")
        self.assertEqual(record["doi"], "10.1111/j.1467-9280.2006.01693.x")
        self.assertEqual(record["verified_at"], "2026-10-02")
        self.assertEqual(record["access_level"], "full_text")
        self.assertFalse(record["directly_validates_cards"])
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("B43" not in card["background_ids"] for card in cards))
        self.assertIn("不同延迟组不是同一批人追踪", route["text"])
        self.assertIn("研究没有验证演唱教学", route["text"])

    def test_web_epub_and_existing_destinations_remain(self):
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            essay = archive.read("EPUB/text/essays--05-play-is-not-performance.xhtml").decode()
            note = archive.read("EPUB/text/docs--evidence--B43-testing-and-retention.xhtml").decode()
        for anchor in (
            "amateur-want-better", "amateur-two-scores", "amateur-time-vs-practice",
            "amateur-practice-study", "amateur-shared-standards",
            "amateur-criticism", "amateur-maintenance",
            "amateur-learning-study", "amateur-effective-for-what",
        ):
            self.assertEqual(html.count('id="' + anchor + '"'), 1)
            self.assertEqual(essay.count('id="' + anchor + '"'), 1)
        self.assertIn("docs--evidence--B43-testing-and-retention.xhtml", essay)
        self.assertIn("essays--05-play-is-not-performance.xhtml#amateur-effective-for-what",
                      note)


if __name__ == "__main__":
    unittest.main()
