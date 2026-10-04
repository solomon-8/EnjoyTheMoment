"""Content and delivery regression checks, not reader-outcome validation."""
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

CHAPTER = "book/20-photography.md"
MAIN = ("photo-language", "photo-truth", "photo-experience", "photo-editing")
NEW = MAIN + ("photo-sharing-goal",)


class PhotographySharingTests(unittest.TestCase):
    def test_four_lines_preserve_the_original_photographic_questions(self):
        text = (ROOT / CHAPTER).read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M), [
            "一、技术让你多一种选择，不替你选好愿望",
            "二、照片不必保留全部，但要说清保留了什么",
            "三、拍摄可以属于经历，也可能改变经历",
            "四、照片怎样成组，回应怎样不吞掉经历",
        ])
        self.assertEqual(len(re.findall(r"^### ", text, re.M)), 20)
        for anchor in NEW:
            self.assertEqual(text.count(f'<a id="{anchor}"></a>'), 1)
            self.assertIn(f"](#{anchor})", text)
        original = [
            "记录、观看、表达与分享", "画框先决定", "先看看光在做什么",
            "一个普通场景", "几个技术词", "变焦不等于走近",
            "清晰不等于有意思", "三种“不满意”", "不从镜头看过去",
            "一页蓝晒", "少记录一些", "摆出来的", "最强的反对意见：这会不会",
            "拍照未必妨碍享受", "想拍的人和陪你的人",
            "拍下、保存", "选片不是选冠军", "喜欢被看见",
            "最强的反对意见：这不还是",
        ]
        positions = [text.index("### " + prefix) for prefix in original]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(len(re.findall(r"^\| ---", text, re.M)), 4)
        self.assertEqual(len(re.findall(r"!\[.*?\]\(", text)), 3)

    def test_summary_only_counterevidence_is_not_a_net_benefit_prescription(self):
        text = (ROOT / CHAPTER).read_text()
        passage = text.split('<a id="photo-sharing-goal"></a>', 1)[1].split(
            "### 想拍的人和陪你的人", 1)[0]
        for phrase in (
            "作者摘要报告", "两种拍摄目的", "不是“发帖”与“完全不用手机”",
            "只读到作者公开摘要，未取得主文",
            "不能逐项复核样本、效应量或机制",
            "不能把两篇研究拼成“先拍就赚、发了就亏”的处方",
            "现场、编辑、沟通和日后回看的全部得失",
            "不能冒充实验附赠的结论",
            "作品失败、观众没有回应和伙伴拒绝追加劳动",
        ):
            self.assertIn(phrase, passage)
        self.assertIn("B44-sharing-intention.md", passage)
        self.assertIn("08-life-without-an-audience.md#audience-chosen-tradeoff", passage)

    def test_retrieval_preserves_source_scope_and_existing_route_targets(self):
        documents, routes = read.load_documents(ROOT)
        doc = next(x for x in documents if x["id"] == "C20")
        raw = (ROOT / CHAPTER).read_bytes()
        self.assertEqual(doc["text"], raw.decode())
        self.assertEqual(doc["source_sha256"], hashlib.sha256(raw).hexdigest())
        route = next(x for x in routes if x["id"] == "R19")
        self.assertEqual(set(route["targets"]),
                         {"C20", "E08", "F34", "B10", "N10", "B44", "N44"})
        for phrase in ("abstract_only", "未取得主文", "不是实际发帖与不用手机",
                       "不能补写样本、效应量或机制验证", "不是新增实验结果"):
            self.assertIn(phrase, route["text"])
        audience = next(x for x in routes if x["id"] == "R45")
        self.assertIn("不是第二项独立证据", audience["text"])

    def test_exports_keep_hierarchy_images_and_new_destinations(self):
        html = (ROOT / "index.html").read_text()
        full = (ROOT / "llms-full.txt").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            chapter = archive.read("EPUB/text/book--20-photography.xhtml").decode()
        for anchor in NEW + (
            "photo-viewpoint", "photo-duration", "photo-contact",
            "photo-cyanotype-object", "photo-selective-truth",
            "photo-arranged-presence", "photo-process-objection",
            "photo-sequence", "photo-audience",
        ):
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
            self.assertEqual(chapter.count(f'id="{anchor}"'), 1)
        self.assertEqual(chapter.count("<table>"), 4)
        self.assertEqual(chapter.count("<img "), 3)
        self.assertIn("docs--evidence--B44-sharing-intention.xhtml", chapter)
        self.assertIn("essays--08-life-without-an-audience.xhtml#audience-chosen-tradeoff", chapter)
        self.assertIn((ROOT / CHAPTER).read_text().strip(), full)
        chapters = json.loads((ROOT / "data/chapters.json").read_text())["chapters"]
        self.assertEqual(next(x for x in chapters if x["id"] == "C20")["text"],
                         (ROOT / CHAPTER).read_text().strip())


if __name__ == "__main__":
    unittest.main()
