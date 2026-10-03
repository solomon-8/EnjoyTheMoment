"""Guard argument order and source boundaries, not audience persuasion."""
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
import check
import read

SOURCE = "book/12-film.md"
TITLE = "12 · 我知道电影在煽情，我仍然可以喜欢"
PARTS = (
    ("film-judgments", "一、愿意被打动，不等于放弃判断"),
    ("film-expression", "二、不只看发生了什么，还看怎样让你经历"),
    ("film-measured-effects", "三、研究测到的改变，能不能回答你的问题"),
    ("film-viewing-choices", "四、怎样看，服务于你想经历的这一晚"),
)


class FilmArgumentTests(unittest.TestCase):
    def test_argument_precedes_materials_and_viewing_advice(self):
        text = (ROOT / SOURCE).read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M),
                         [title for _, title in PARTS])
        self.assertEqual(len(re.findall(r"^### .+$", text, re.M)), 18)
        opening = text.split("\n## ", 1)[0]
        self.assertIn("# " + TITLE, opening)
        for anchor, _ in PARTS:
            self.assertIn(f"](#{anchor})", opening)
        for earlier, later in (
            ('id="film-designed-emotion"', 'id="film-expression"'),
            ('id="film-editing-and-evidence"', 'id="film-expression"'),
            ('id="film-expression"', 'id="film-measured-effects"'),
            ('id="film-context-boundary"', 'id="film-viewing-choices"'),
        ):
            self.assertLess(text.index(earlier), text.index(later))
        self.assertIn("[第三部分](#film-measured-effects)的两项研究没有测试", text)
        self.assertNotIn("前两项研究没有测试", text)
        self.assertIn("### 最强的反对意见：这不还是把娱乐变成学习了吗？", text)

    def test_title_alias_and_argument_do_not_promise_immunity_or_effects(self):
        text = (ROOT / SOURCE).read_text()
        self.assertIn(TITLE, (ROOT / "README.md").read_text())
        self.assertIn("I know the film is trying to move me. I can still like it.",
                      (ROOT / "README.en.md").read_text())
        alias = "12--电影不是看完就能毕业的清单"
        self.assertEqual(text.count(f'id="{alias}"'), 1)
        self.assertEqual(build.markdown(text, SOURCE).count(f'id="{alias}"'), 1)
        for phrase in (
            "我已经哭了，我仍可以觉得它拍得不好",
            "不是一条禁止公式、煽情或浓烈风格的规则",
            "被打动，既不是丢失判断力的证据，也不是事实已经成立的证据",
            "同一段脸在一个序列内重复",
            "p = .879", "p = .293", "3.98、3.93、3.87",
            "这里使用的文件没有音轨",
            "想让作品吸引人，不等于可以拿宣传语充当效果",
        ):
            self.assertIn(phrase, text)

    def test_spoiler_and_images_remain_with_the_work_not_in_the_opening(self):
        text = (ROOT / SOURCE).read_text()
        self.assertEqual(text.count("<details>"), 1)
        self.assertEqual(text.count("</details>"), 1)
        ending = text.split("<details>", 1)[1].split("</details>", 1)[0]
        self.assertIn("展开后段与结尾分析", ending)
        self.assertIn("切回一个旧地方，时间一定就是“同时”吗？", ending)
        self.assertIn("train-closeup.jpg", ending)
        self.assertEqual(ending.count("!["), 1)
        self.assertEqual(text.count("!["), 3)
        self.assertLess(text.index('id="film-expression"'), text.index("<details>"))
        self.assertLess(text.index("</details>"), text.index('id="film-measured-effects"'))

    def test_full_retrieval_and_epub_keep_every_anchor(self):
        raw = (ROOT / SOURCE).read_bytes()
        text = raw.decode()
        docs, routes = read.load_documents(ROOT)
        chapter = next(d for d in docs if d["id"] == "C12")
        self.assertEqual(chapter["text"], text)
        self.assertEqual(chapter["source_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertIn(text, (ROOT / "llms-full.txt").read_text())
        data = json.loads((ROOT / "data/chapters.json").read_text())["chapters"]
        self.assertEqual(next(d for d in data if d["id"] == "C12")["title"], TITLE)
        self.assertEqual(set(next(r for r in routes if r["id"] == "R62")["targets"]),
                         {"C12", "B32", "N32", "B33", "N33", "F03", "F16", "C31", "E11"})
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            epub = archive.read("EPUB/text/book--12-film.xhtml").decode()
        for anchor in check.anchors_for(text):
            self.assertEqual(epub.count(f'id="{anchor}"'), 1)
        self.assertIn(TITLE, epub)


if __name__ == "__main__":
    unittest.main()
