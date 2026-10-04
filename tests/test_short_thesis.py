"""Guard short-form fidelity and links, not persuasion or social attention."""
from pathlib import Path
import re
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check
import epub


class ShortThesisTests(unittest.TestCase):
    def test_short_claims_keep_costs_and_existing_commitments(self):
        text = (ROOT / "docs/manifesto.md").read_text()
        self.assertEqual(len(re.findall(r"^## ", text, re.M)), 8)
        for phrase in (
            "买不起，不等于不配喜欢",
            "有些愿望确实需要资源",
            "不是原愿望已经被满足的证明",
            "钱未必退得回",
            "已经答应的组织、收尾或同行安排",
            "仍要说明、协商和处理影响",
            "改变主意，不等于约定自动作废",
            "少得到一些产出、便利或赞许",
            "不保证最后补赚回来",
            "好玩，可以是理由的终点",
        ):
            self.assertIn(phrase, text)
        self.assertIn(
            "../essays/06-real-life-constraints.md#constraints-necessity", text
        )
        self.assertIn("../SHUAQI.md#shuaqi-exit", text)
        self.assertLess(len(text), len((ROOT / "SHUAQI.md").read_text()))

    def test_old_short_manifesto_anchors_and_epub_content_survive(self):
        source = "docs/manifesto.md"
        text = (ROOT / source).read_text()
        anchors = check.anchors_for(text)
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            body = archive.read("EPUB/" + epub.document_name(source)).decode()
            constraints = archive.read(
                "EPUB/" + epub.document_name("essays/06-real-life-constraints.md")
            ).decode()
            manifesto = archive.read(
                "EPUB/" + epub.document_name("SHUAQI.md")
            ).decode()
        for anchor in (
            "五钱是门票不是入场资格", "八允许无聊允许难过允许退票",
            "五买不起不等于不配喜欢", "八允许无聊允许难过也允许改主意",
        ):
            self.assertIn(anchor, anchors)
            self.assertIn(f'id="{anchor}"', body)
        self.assertIn(
            "essays--06-real-life-constraints.xhtml#constraints-necessity", body
        )
        self.assertIn('id="constraints-necessity"', constraints)
        self.assertIn("SHUAQI.xhtml#shuaqi-exit", body)
        self.assertIn('id="shuaqi-exit"', manifesto)
        self.assertIn("钱未必退得回", body)
        self.assertIn("仍要说明、协商和处理影响", body)

    def test_reference_relationship_states_our_tradeoff_not_a_false_opponent(self):
        text = (ROOT / "README.md").read_text()
        section = text.split("## 与参考仓库的关系\n", 1)[1].split(
            "## 许可与参与", 1
        )[0]
        for phrase in (
            "不只是长寿", "不继承其数据或健康结论",
            "不把它塑造成“反对享受”的靶子",
            "甚至让以后少得到一点", "并把真实代价写出来",
            "若一种性价比比较已经认真考虑当下快乐，我们可以同意它",
            "分歧在实际取舍",
        ):
            self.assertIn(phrase, section)
        self.assertIn(
            "essays/01-pleasure-is-an-end.md#pleasure-value-metric", section
        )
        self.assertNotIn("超越", section)


if __name__ == "__main__":
    unittest.main()
