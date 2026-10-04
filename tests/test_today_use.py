"""Keep the opening argument distinct from card utility and empirical effects."""
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

CHAPTER = "book/01-start-now.md"
PARTS = (
    ("today-value", "一、今天的生活，不必先由成绩批准"),
    ("today-objects", "二、喜欢的东西，怎样真正进入生活"),
    ("today-opportunity", "三、机会兑现了，不等于愿望兑现了"),
    ("today-time", "四、让今天有位置，不把它排成另一份作业"),
)


class TodayUseTests(unittest.TestCase):
    def test_four_argument_parts_precede_optional_unchanged_cards(self):
        text = (ROOT / CHAPTER).read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M),
                         [title for _, title in PARTS] + ["配套：从已有的生活里开始"])
        prose, cards = text.split('<a id="j001"></a>', 1)
        self.assertEqual(len(re.findall(r"^### .+$", prose, re.M)), 14)
        self.assertEqual(len(re.findall(r"^#### .+$", prose, re.M)), 4)
        opening = text.split("\n## ", 1)[0]
        for anchor, _ in PARTS:
            self.assertIn(f"](#{anchor})", opening)
        for first, second in (
            ("today-priority", "today-after-failure"),
            ("today-after-failure", "today-use"),
            ("today-first-page", "today-making-an-occasion"),
            ("today-first-use", "today-not-turnover"),
            ("today-voucher", "today-future"),
            ("today-not-redemption", "today-time"),
        ):
            self.assertLess(text.index(f'id="{first}"'), text.index(f'id="{second}"'))
        for number in range(1, 7):
            self.assertIn(f"J{number:03d}", cards)
        self.assertIn("不是你的物品先问", cards)
        self.assertIn("不是普遍事实", cards)

    def test_unfinished_work_does_not_become_unlimited_punishment(self):
        text = (ROOT / CHAPTER).read_text()
        section = text.split('<a id="today-after-failure"></a>', 1)[1].split(
            '<a id="today-objects"></a>', 1)[0]
        for phrase in (
            "快乐不必全部归庆功宴管",
            "看一个原创假想",
            "稿子不需要今晚交给别人",
            "不准备再写，却坚持把电影取消",
            "不能单靠这一点，说明剩下的时间必须变成惩罚",
            "可以真心选择某项有条件的奖励",
            "不保证放松会提高效率",
            "不保证取消奖励能让她下次做到",
            "初稿原本答应今晚交给小夏",
            "需要取消电影",
            "小夏可以失望，不欠她一句“没关系”",
            "下一步必须等明早的材料",
            "看电影不等于事情已经解决，不看电影也不自动完成了补救",
            "不能要求受影响的人陪自己开心",
            "不是心理治疗或行为干预建议",
        ):
            self.assertIn(phrase, section)
        self.assertNotRegex(section, r"\[(?:B\d{2}|N\d{2}|F\d{2}|J\d{3})")
        self.assertIn("#waiting-plan-revision", section)

    def test_old_evidence_scope_and_table_still_constrain_the_argument(self):
        text = (ROOT / CHAPTER).read_text()
        for phrase in (
            "另有 80 名学生", "后续原因调查只有 33 人",
            "| 三周 | 平均 50% | 10 / 32 |",
            "| 两个月 | 平均 68% | 2 / 32 |",
            "59 / 120", "42 / 120",
            "这段访谈不是论文全文",
            "他的商业讨论与本书的生活主张，不是同一个目标",
            "不是所有喜欢都必须消耗",
            "写了第一页，不欠这本本子一本完整日记",
        ):
            self.assertIn(phrase, text)
        research = json.loads((ROOT / "data/research.json").read_text())["records"]
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        self.assertEqual(len(research), 50)
        self.assertEqual(len(notes), len(build.EVIDENCE))
        self.assertEqual(next(n for n in notes if n["id"] == "F79")["source_kind"],
                         "researcher_edited_interview_not_full_paper")

    def test_route_exact_text_and_html_epub_use_canonical_arguments(self):
        documents, routes = read.load_documents(ROOT)
        chapter = next(d for d in documents if d["id"] == "C01")
        raw = (ROOT / CHAPTER).read_bytes()
        self.assertEqual(chapter["text"], raw.decode())
        self.assertEqual(chapter["source_sha256"], hashlib.sha256(raw).hexdigest())
        prose = raw.decode().split('<a id="j001"></a>', 1)[0].strip()
        self.assertIn(prose, (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R02")
        self.assertEqual(set(route["targets"]),
                         {"C01", "B17", "N17", "F79", "F95", "E01", "E03", "E10", "C18"})
        self.assertIn("均不验证这一价值主张", route["text"])
        self.assertIn("四条主线不是四步行动法", route["text"])
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            epub = archive.read("EPUB/text/book--01-start-now.xhtml").decode()
        for anchor in [a for a, _ in PARTS] + ["today-after-failure"]:
            for output in (html, epub):
                self.assertEqual(output.count(f'id="{anchor}"'), 1)
            self.assertIn(f'href="#{anchor}"', html)
            self.assertIn(f'href="book--01-start-now.xhtml#{anchor}"', epub)
        self.assertIn("essays--03-now-or-later.xhtml#waiting-plan-revision", epub)
        self.assertIn("book--08-permission.xhtml", epub)
        self.assertEqual(epub.count("<table>"), 1)


if __name__ == "__main__":
    unittest.main()
