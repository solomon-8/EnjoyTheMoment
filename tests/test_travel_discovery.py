"""Content transmission checks, not empirical or philosophical validation."""
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

CHAPTER = "book/23-travel.md"
MAIN = ("travel-wishes", "travel-arrangements", "travel-looking", "travel-aftermath")
NEW = MAIN + ("travel-discovery", "travel-discovery-objection")


class TravelDiscoveryTests(unittest.TestCase):
    def test_four_lines_preserve_original_topic_order_and_spoiler_boundary(self):
        text = (ROOT / CHAPTER).read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M), [
            "一、想要什么，与到了才发现什么",
            "二、共同出发，不必共同每一分钟",
            "三、谁告诉你怎样看，谁决定怎样喜欢？",
            "四、落空的愿望，与已经发生的日子",
        ])
        self.assertEqual(len(re.findall(r"^### ", text, re.M)), 18)
        self.assertEqual(len(re.findall(r"^#### ", text, re.M)), 1)
        for anchor in NEW:
            self.assertEqual(text.count(f'<a id="{anchor}"></a>'), 1)
            self.assertIn(f"](#{anchor})", text)
        old = ["目的地是名词", "地图上的两个点", "住得更远", "紧凑不是原罪",
               "如果这辈子可能只来一次", "与朋友出门", "预约先解决依赖",
               "临时改变路线", "攻略可以替你", "一位反对攻略", "所谓“像当地人",
               "“真实”究竟", "不如想象中好", "回来以后又普通了", "回程也是",
               "最强的反对意见", "还有一个反对"]
        positions = [text.index("### " + prefix) for prefix in old]
        self.assertEqual(positions, sorted(positions))
        before, tail = text.split("<details>", 1)
        details, after = tail.split("</details>", 1)
        self.assertIn("Miss Lavish", details)
        self.assertNotIn("Miss Lavish", before + after)
        self.assertEqual(text.count("<details>"), 1)
        self.assertNotIn("<details open", text)

    def test_new_interest_does_not_erase_loss_or_retroactively_validate_planning(self):
        text = (ROOT / CHAPTER).read_text()
        passage = text.split('<a id="travel-discovery"></a>', 1)[1].split(
            "### 地图上的两个点", 1)[0]
        for phrase in (
            "原创假想", "虚构展馆", "也允许最终没有遇见",
            "不必只服务出发前写计划的那个人",
            "不知道自己会被哪幅画吸引，不等于不知道能不能进去",
            "不能由一个人的新发现取消其他人的一天",
            "再改一个前提", "也不能倒过来证明准备没有问题",
            "喜欢其中一段，与认可整趟取舍，是两个判断",
            "不必替整趟旅行报销",
        ):
            self.assertIn(phrase, passage)
        self.assertNotIn("[B12", passage)
        self.assertNotIn("[F58", passage)

    def test_complete_retrieval_and_route_do_not_promote_fiction_to_evidence(self):
        documents, routes = read.load_documents(ROOT)
        chapter = next(x for x in documents if x["id"] == "C23")
        raw = (ROOT / CHAPTER).read_bytes()
        self.assertEqual(chapter["text"], raw.decode())
        self.assertEqual(chapter["source_sha256"], hashlib.sha256(raw).hexdigest())
        route = next(x for x in routes if x["id"] == "R50")
        self.assertEqual(set(route["targets"]),
                         {"C23", "C03", "C25", "F58", "B12", "N12", "F12"})
        for phrase in ("不是F58情节或B12的发现", "反应未知不等于参与条件不明",
                       "不证明准备正确", "也不替同行者同意改约"):
            self.assertIn(phrase, route["text"])

    def test_exports_keep_hierarchy_tables_new_and_existing_destinations(self):
        html = (ROOT / "index.html").read_text()
        full = (ROOT / "llms-full.txt").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            chapter = archive.read("EPUB/text/book--23-travel.xhtml").decode()
            note = archive.read("EPUB/text/docs--evidence--F58-travel-and-guidebooks.xhtml").decode()
        for anchor in NEW + ("travel-once", "travel-guide", "travel-forster",
                             "travel-authenticity", "travel-incomplete"):
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
            self.assertEqual(chapter.count(f'id="{anchor}"'), 1)
        self.assertEqual(chapter.count("<table>"), 3)
        self.assertIn("book--03-novelty.xhtml#novelty-uncertainty", chapter)
        self.assertIn("book--23-travel.xhtml#travel-forster", note)
        self.assertIn((ROOT / CHAPTER).read_text().strip(), full)
        chapters = json.loads((ROOT / "data/chapters.json").read_text())["chapters"]
        self.assertEqual(next(x for x in chapters if x["id"] == "C23")["text"],
                         (ROOT / CHAPTER).read_text().strip())


if __name__ == "__main__":
    unittest.main()
