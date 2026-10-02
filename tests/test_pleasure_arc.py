"""Guard the argument's hierarchy and fidelity, not reader comprehension."""
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

PARTS = (
    ("pleasure-ground", "一、先争论快乐有没有价值，而不是先算它的用途"),
    ("pleasure-tradeoffs", "二、愿意付出什么，才是价值排序的分歧"),
    ("pleasure-conditions", "三、喜欢是理由，不是所有做法的通行证"),
    ("pleasure-feedback", "四、承认可能选错，也保留不尽兴的自由"),
    ("pleasure-self-test", "五、这套主张也必须接受自己的检验"),
)
SOURCE = "essays/01-pleasure-is-an-end.md"


class PleasureArcTests(unittest.TestCase):
    def test_five_questions_form_a_readable_hierarchy(self):
        text = (ROOT / SOURCE).read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M),
                         [title for _, title in PARTS])
        opening = text.split("\n## ", 1)[0]
        for anchor, _ in PARTS:
            self.assertIn(f"](#{anchor})", opening)
            self.assertEqual(text.count(f'id="{anchor}"'), 1)
        for title in (
            "把快乐也算成收益，不就还是性价比吗？",
            "做得更慢，就一定更不划算吗？",
            "人生选项变多，不等于人生已经发生",
            "喜欢是理由，为什么还需要讨论？",
            "把快乐当正事，不是给快乐定业绩",
        ):
            self.assertEqual(text.count("\n### " + title + "\n"), 1)
        self.assertIn("\n#### 一项研究把“重视”和“担忧不足”分开了\n", text)
        self.assertIn("\n#### 不要求尽兴，也不要求你把失望忍下去\n", text)

    def test_reordering_keeps_distinct_cases_and_objections(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in (
            "不把它安到参考作者头上",
            "没有证明它与“耍起”不相容",
            "原创假想，不是调查、计时结果或消费建议",
            "阿岚饿了", "小周却想在厨房里待一会儿",
            "变化不是成本消失", "尚未说清的别人劳动",
            "不要求它预知未来", "不存在的晚上",
            "不给统一比例", "共同资金却不能由一个人决定",
            "可能想象错一种体验", "当前的欲望也包含想清静",
            "没有预测幸福感的变化",
            "不是所有单项结果都毫无关系",
            "没有证明放弃追求就会更幸福",
            "不能用“降低期待”替提供者免除责任",
            "给自己少打一次分，并不会凭空增加时间",
        ):
            self.assertIn(phrase, text)
        # Same headings retain their implicit fragment even at another level.
        for anchor in (
            "三个不同的问题不要混着回答",
            "另一个反对意见只顾快乐会不会没有意义",
            "对照两笔都负担得起的支出",
            "一个会改变答案的反例",
            "这套主张也必须接受自己的检验",
        ):
            self.assertIn(anchor, check.anchors_for(text))
        self.assertLess(text.index("### 三个不同的问题"),
                        text.index('id="pleasure-tradeoffs"'))
        self.assertLess(text.index("### 另一个反对意见"),
                        text.index('id="pleasure-tradeoffs"'))
        self.assertEqual(build.markdown(text, SOURCE).count("<table>"), 2)

    def test_retrieval_preserves_the_entire_argument_not_only_its_map(self):
        raw = (ROOT / SOURCE).read_bytes()
        text = raw.decode()
        documents, routes = read.load_documents(ROOT)
        record = next(d for d in documents if d["id"] == "E01")
        self.assertEqual(record["text"], text)
        self.assertEqual(record["source_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertIn(text, (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R01")
        self.assertEqual(set(route["targets"]), {"SHUAQI", "E01", "F86"})
        self.assertIn("不是五步行动处方", route["text"])
        for anchor, _ in PARTS:
            self.assertIn("#" + anchor, route["text"])
        exported = json.loads((ROOT / "data/essays.json").read_text())["essays"]
        self.assertEqual(next(e for e in exported if e["id"] == "E01")["text"], text)

    def test_offline_and_epub_keep_new_parts_and_old_destinations(self):
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            epub = archive.read(
                "EPUB/text/essays--01-pleasure-is-an-end.xhtml").decode()
        for anchor in [a for a, _ in PARTS] + [
            "pleasure-value-metric", "pleasure-process", "pleasure-options",
            "pleasure-enough", "pleasure-not-quota", "pleasure-happiness-study",
            "pleasure-disappointment", "这套主张也必须接受自己的检验",
        ]:
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
            self.assertEqual(epub.count(f'id="{anchor}"'), 1)
        self.assertIn("docs--evidence--B40-happiness-concern.xhtml", epub)
        self.assertIn("没有预测幸福感的变化", epub)
        self.assertIn("EPUB", (ROOT / "docs/reading-editions.md").read_text())


if __name__ == "__main__":
    unittest.main()
