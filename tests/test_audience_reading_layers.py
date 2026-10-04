"""Keep source caveats visible while making research detail optional on the web."""
from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read

SOURCE = "essays/08-life-without-an-audience.md"


class CollapsedText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.visible = []
        self.hidden = []

    def handle_starttag(self, tag, attrs):
        if tag == "details":
            self.depth += 1

    def handle_endtag(self, tag):
        if tag == "details":
            self.depth -= 1

    def handle_data(self, data):
        (self.hidden if self.depth else self.visible).append(data)


class AudienceReadingLayersTests(unittest.TestCase):
    def test_abstract_status_and_actual_comparator_are_not_hidden(self):
        text = (ROOT / SOURCE).read_text()
        part = text.split('<a id="audience-photo-study"></a>', 1)[1].split(
            '<a id="audience-chosen-tradeoff"></a>', 1)[0]
        parser = CollapsedText()
        parser.feed(build.markdown(part, SOURCE))
        visible = "".join(parser.visible)
        hidden = "".join(parser.hidden)
        for phrase in (
            "没有直接验证发布与点赞的收益",
            "只读到作者公开的摘要，未取得主文",
            "两种拍摄目的的比较",
            "不是“发帖”与“完全不用手机”的比较",
            "没有回答现场、表达与回应合在一起是否值得",
            "相比为自己拍照",
            "原创假想", "不是上述研究里的参与者故事",
            "减少一种体验，与没有得到任何想要的东西",
        ):
            self.assertIn(phrase, visible)
        for phrase in (
            "223名线上参与者", "这不证明效果严格相等",
            "亲手制作的人中", "差异未显著",
            "刻意没有让参与者回看照片",
            "不能独立核查这些机制",
            "没有据此补写样本、效应量或逐项显著性",
            "不能把两篇压成“拍照有益、分享有害”",
            "净收益结论",
        ):
            self.assertIn(phrase, hidden)
        self.assertEqual(part.count("<details>"), 2)
        self.assertEqual(part.count("</details>"), 2)
        self.assertEqual(parser.depth, 0)

    def test_full_retrieval_and_epub_keep_all_optional_detail(self):
        text = (ROOT / SOURCE).read_text()
        documents, _ = read.load_documents(ROOT)
        essay = next(d for d in documents if d["id"] == "E08")
        self.assertTrue(essay["contains_folded_content"])
        self.assertEqual(essay["text"], text)
        self.assertIn(text, (ROOT / "llms-full.txt").read_text())
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            epub = archive.read(
                "EPUB/text/essays--08-life-without-an-audience.xhtml").decode()
        self.assertNotIn("<details", epub)
        for phrase in (
            "看研究：实际拍摄、只计划拍什么",
            "看证据边界：只读到摘要",
            "223名线上参与者", "净收益结论",
            "没有据此补写样本、效应量或逐项显著性",
            "不能倒过来说这些损失从未存在",
        ):
            self.assertIn(phrase, epub)


if __name__ == "__main__":
    unittest.main()
