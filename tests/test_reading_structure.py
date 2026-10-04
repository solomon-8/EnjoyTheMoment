"""Protect text/interpretation boundaries and reading routes, not literary scores."""
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

SOURCE = "book/22-reading.md"
NOTE = "docs/evidence/F11-reading-texts.md"


class ReadingStructureTests(unittest.TestCase):
    def test_three_lines_keep_text_experience_and_choices_separate(self):
        text = (ROOT / SOURCE).read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M), [
            "一、书怎样让人愿意留在其中？",
            "二、细读是乐趣，还是另一场考试？",
            "三、怎样读、读到哪里、和谁谈？",
        ])
        order = ['id="reading-experience"', 'id="reading-austen-position"',
                 'id="reading-open-window"', 'id="reading-enjoyment-not-extraction"',
                 'id="reading-not-exam"', "二十个字，怎样把独处变成一种关系",
                 'id="reading-mary"', "不是每次都要分析", 'id="reading-choices"',
                 "笔记可以保存喜欢", "讨论作品，不必变成争夺标准答案"]
        locations = [text.index(x) for x in order]
        self.assertEqual(locations, sorted(locations))
        self.assertNotIn("<!-- pick:", text)

    def test_mary_scene_does_not_invent_a_private_answer_or_an_experiment(self):
        text = (ROOT / SOURCE).read_text()
        part = text.split('<a id="reading-mary"></a>', 1)[1].split(
            "### 不是每次都要分析", 1)[0]
        for phrase in ("贝内特太太", "点名问玛丽", "想说点很有见地的话",
                       "才揭晓自己已经拜访", "没有在这个场景里展示",
                       "全部智力或阅读价值的排名",
                       "不必替玛丽编一个更聪明的内心答案",
                       "可这不就是在讽刺读了很多", "不能为了维护享乐立场",
                       "小说没有把三项证明一起交出来",
                       "不是奥斯汀替我们发表宣言", "不必随时变成答辩",
                       "真正想练表达的人也不必被劝成"):
            self.assertIn(phrase, part)
        self.assertIn("essays/05-play-is-not-performance.md#amateur-criticism", part)
        note = (ROOT / NOTE).read_text()
        for phrase in ("2026-10-03", "读者在章首先得到",
                       "列举来自父亲", "想说却不知怎样说来自叙述",
                       "不拿序言作者的评价冒充小说正文",
                       "不代作全书人物结论", "没有取得新底本"):
            self.assertIn(phrase, note)

    def test_spoiler_choice_and_existing_reading_limits_survive_structure(self):
        text = (ROOT / SOURCE).read_text()
        before, tail = text.split("<details>", 1)
        folded, after = tail.split("</details>", 1)
        self.assertIn("完整情节与结局", folded)
        self.assertIn("恒河", folded)
        self.assertNotIn("恒河", before + after)
        self.assertNotIn("<details open", text)
        self.assertEqual(text.count("<details>"), 1)
        for phrase in ("搭在手臂上", "披在肩上", "不是文学作品引文",
                       "本章没有比较具体中文译本", "允许停止",
                       "人物的话不能未经区分就当成作者主张"):
            self.assertIn(phrase, text)
        self.assertEqual(len(json.loads((ROOT / "data/catalog.json").read_text())["cards"]), 60)
        self.assertEqual(len(json.loads((ROOT / "data/research.json").read_text())["records"]), 50)

    def test_full_exports_and_routes_keep_mary_with_her_counterreading(self):
        text = (ROOT / SOURCE).read_text()
        html = build.markdown(text, SOURCE)
        note = (ROOT / NOTE).read_text()
        note_html = build.markdown(note, NOTE)
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            epub = z.read("EPUB/text/book--22-reading.xhtml").decode()
            source_epub = z.read("EPUB/text/docs--evidence--F11-reading-texts.xhtml").decode()
        for anchor in ("reading-experience", "reading-not-exam", "reading-choices",
                       "reading-mary", "reading-austen-position", "reading-open-window",
                       "reading-detail-and-cause", "reading-second-story",
                       "reading-enjoyment-not-extraction"):
            self.assertEqual(html.count('id="' + anchor + '"'), 1)
            self.assertEqual(epub.count('id="' + anchor + '"'), 1)
        self.assertIn('href="#reading-mary-source"', html)
        self.assertIn('href="#reading-mary"', note_html)
        self.assertIn('docs--evidence--F11-reading-texts.xhtml#reading-mary-source', epub)
        self.assertIn('book--22-reading.xhtml#reading-mary', source_epub)
        documents, routes = read.load_documents(ROOT)
        self.assertEqual(next(d for d in documents if d["id"] == "C22")["text"], text)
        self.assertEqual(next(d for d in documents if d["id"] == "F11")["text"], note)
        route = next(r for r in routes if r["id"] == "R40")
        self.assertIn("E05", route["targets"])
        self.assertIn("不能替她补一个未写出的聪明答案", route["text"])
        self.assertIn("不免除具体解释的证据责任", route["text"])
        self.assertIn("不因检索命中就直接揭底", route["text"])


if __name__ == "__main__":
    unittest.main()
