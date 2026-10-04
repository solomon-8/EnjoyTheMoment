"""Content/export fidelity, not a test of moral correctness or reader response."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import read

CHAPTER = "book/05-connection.md"
ESSAY = "essays/09-friends-not-assets.md"
ANCHORS = ("connection-changed-mind", "connection-promise-value")


class SharedPromisesTests(unittest.TestCase):
    def test_promises_follow_arrangements_and_precede_optional_cards(self):
        text = (ROOT / CHAPTER).read_text()
        headings = re.findall(r"^## (.+)$", text, re.M)
        self.assertEqual(headings, [
            "一、坐在一起，究竟多了什么？",
            "二、不同样喜欢，为什么仍愿意一起？",
            "三、相聚需要劳动，谁答应了哪一部分？",
            "四、散场不必全票满意，承诺仍要各自交代",
            "配套：把愿望说具体，不把回应当绩效",
        ])
        positions = [text.index(f'id="{a}"') for a in
                     ("connection-ending",) + ANCHORS + ("connection-companions", "j025")]
        self.assertEqual(positions, sorted(positions))
        for anchor in ANCHORS:
            self.assertEqual(text.count(f'<a id="{anchor}"></a>'), 1)
            self.assertIn(f"](#{anchor})", text)
        self.assertEqual(text.count("<!-- pick:"), 6)

    def test_changed_mind_reliance_and_changed_invitation_stay_distinct(self):
        text = (ROOT / CHAPTER).read_text()
        section = text.split('<a id="connection-changed-mind"></a>', 1)[1].split(
            '<a id="connection-promise-value"></a>', 1)[0]
        for phrase in (
            "第一个晚上，两人还没有约定",
            "第二个晚上，小然已答应",
            "另一个人已经依据她的回答安排了自己的晚上",
            "第三个晚上，小然答应的是两个人看演出",
            "也不是任何细节不合意",
            "没有一份自动适用的赔偿表",
            "更没有“出钱就买断失望”的公式",
            "无法继续、现在不喜欢、约定本身被改变",
        ):
            self.assertIn(phrase, section)
        for phrase in (
            "原创假想", "这不是关于失约率的研究结论",
            "他们仍可能碰巧同时有空", "不要求最后一定尽兴",
            "答应一晚不是答应以后每一晚",
            "而是为了让这个有人一起的今天能够发生",
        ):
            self.assertIn(phrase, text)

    def test_complete_retrieval_and_route_keep_limits_without_new_study(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {item["id"]: item for item in documents}
        for ident, path in (("C05", CHAPTER), ("E09", ESSAY)):
            raw = (ROOT / path).read_bytes()
            self.assertEqual(by_id[ident]["text"], raw.decode())
            self.assertEqual(by_id[ident]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
        route = next(item for item in routes if item["id"] == "R09")
        self.assertEqual(set(route["targets"]),
                         {"C05", "B21", "B22", "N21", "N22", "E01", "E05"})
        for phrase in ("不是失约率研究或法律责任表", "即时改选与可靠的共同时间存在取舍",
                       "不证明所有约定都应维持", "不将B21/B22或关系规则实验"):
            self.assertIn(phrase, route["text"])
        self.assertIn("E09", {item["id"] for item in
                             read.linked_records(by_id["C05"], documents, ROOT)})
        self.assertIn("C05", {item["id"] for item in
                             read.linked_records(by_id["E09"], documents, ROOT)})

    def test_html_epub_and_full_text_keep_reciprocal_argument_links(self):
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            chapter = archive.read("EPUB/text/book--05-connection.xhtml").decode()
            essay = archive.read("EPUB/text/essays--09-friends-not-assets.xhtml").decode()
        for anchor in ANCHORS:
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
            self.assertEqual(chapter.count(f'id="{anchor}"'), 1)
        self.assertIn("essays--09-friends-not-assets.xhtml#friends-reciprocity", chapter)
        self.assertIn("book--05-connection.xhtml#connection-changed-mind", essay)
        self.assertEqual(chapter.count("<table>"), 1)
        self.assertEqual(essay.count("<table>"), 1)
        full = (ROOT / "llms-full.txt").read_text()
        chapters = json.loads((ROOT / "data/chapters.json").read_text())["chapters"]
        self.assertIn(next(c for c in chapters if c["id"] == "C05")["text"].strip(), full)
        self.assertIn((ROOT / ESSAY).read_text().strip(), full)
        self.assertIn("更没有“出钱就买断失望”的公式", chapter)


if __name__ == "__main__":
    unittest.main()
