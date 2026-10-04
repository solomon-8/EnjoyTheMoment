"""Check truthful entry routes, not reader preference or social attention."""
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check
import epub


class ReadingEntryTests(unittest.TestCase):
    def test_reading_navigation_precedes_optional_activities(self):
        text = (ROOT / "README.md").read_text()
        self.assertLess(text.index("## 目录"), text.index("## 现在就选一件"))
        self.assertLess(
            text.index("## 按问题找到完整论证"),
            text.index("## 现在就选一件"),
        )
        menu = text.split("## 现在就选一件\n", 1)[1].split("## 怎么读一张卡", 1)[0]
        self.assertIn(
            "<summary>需要一个玩法时，再展开这十个入口</summary>", menu
        )
        self.assertNotIn("<details open", menu)
        self.assertEqual(len(re.findall(r"\]\(book/[^)]+#j\d+\)", menu)), 10)
        self.assertIn("这些入口是配套", menu.split("<details>", 1)[0])
        self.assertIn("不是实时市场报价", menu)
        self.assertIn('<a id="先试一口再决定信不信"></a>', text)
        self.assertIn("不必先尝试活动才有资格反驳", text)
        catalog = text.split("## 目录\n", 1)[1].split(
            "## 按问题找到完整论证", 1
        )[0]
        rows = [line for line in catalog.splitlines() if line.startswith("|")]
        self.assertEqual(len(rows), 40)  # headings, separator, 38 chapters
        self.assertTrue(all(len(line.split("|")) == 4 for line in rows))
        self.assertNotIn("独立正文", catalog)
        self.assertEqual(
            len(re.findall(r"\]\(book/[^)]+\.md\)", catalog)), 38
        )

    def test_payment_chapter_exposes_its_actual_questions(self):
        text = (ROOT / "book/06-spending.md").read_text()
        opening = text.split("\n## ", 1)[0]
        self.assertIn("# 06 · 买都买了，不必再赔上今晚", opening)
        for anchor in (
            "spending-stay-or-leave", "spending-two-ledgers",
            "spending-next-purchase", "spending-own-evening",
        ):
            self.assertIn(f"](#{anchor})", opening)
        anchors = check.anchors_for(text)
        for anchor in (
            "06--钱可以换快乐不必换身份",
            "已经花出去的钱不应该自动获得你剩下的晚上",
            "spending-stay-or-leave",
        ):
            self.assertIn(anchor, anchors)
        section = text.split('<a id="spending-stay-or-leave"></a>', 1)[1].split(
            '<a id="spending-admission"></a>', 1
        )[0]
        for phrase in (
            "买票后还没出门", "仍可退转的钱", "已经答应的同行安排",
            "都可以是继续的理由", "别把“果断止损”也做成性格比赛",
        ):
            self.assertIn(phrase, section)

    def test_ordinary_phrase_locates_complete_chapter_without_new_search_logic(self):
        for phrase in ("买票", "回本", "不想去了"):
            result = json.loads(subprocess.check_output(
                [sys.executable, str(ROOT / "tools/read.py"),
                 "--query", phrase, "--kind", "chapter", "--limit", "20"],
                cwd=ROOT, text=True,
            ))
            self.assertEqual(result["scope"], "literal_and")
            self.assertFalse(result["complete_text_returned"])
            self.assertIn("C06", [item["id"] for item in result["results"]])
        source = "book/06-spending.md"
        text = (ROOT / source).read_text()
        result = json.loads(subprocess.check_output(
            [sys.executable, str(ROOT / "tools/read.py"), "--id", "C06"],
            cwd=ROOT, text=True,
        ))
        self.assertTrue(result["complete"])
        self.assertEqual(result["record"]["text"], text)
        self.assertIn(text.split('<a id="j031">', 1)[0].strip(),
                      (ROOT / "llms-full.txt").read_text())
        web = (ROOT / "index.html").read_text()
        self.assertIn('href="#spending-stay-or-leave"', web)
        self.assertIn('id="spending-stay-or-leave"', web)
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            body = archive.read("EPUB/" + epub.document_name(source)).decode()
            nav = archive.read("EPUB/nav.xhtml").decode()
        self.assertIn("买都买了，不必再赔上今晚", nav)
        for phrase in (
            "买票后不想去了，还要为“回本”继续吗？",
            "仍可退转的钱", "已经答应的同行安排",
        ):
            self.assertIn(phrase, body)


if __name__ == "__main__":
    unittest.main()
