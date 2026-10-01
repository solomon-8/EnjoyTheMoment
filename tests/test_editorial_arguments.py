"""Narrative and evidence guards, not reader-comprehension or attention scores."""
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import check


def section(text, anchor):
    """Read the complete anchored argument up to the next explicit anchor."""
    start = text.index(f'<a id="{anchor}"></a>')
    end = text.find('<a id="', start + 1)
    return text[start:end if end != -1 else None]


class EditorialArgumentsTests(unittest.TestCase):
    def test_experience_and_skill_are_separated_before_practice_statistics(self):
        text = (ROOT / "essays/05-play-is-not-performance.md").read_text()
        # The value question is answered before research is asked to qualify it.
        self.assertLess(text.index('id="amateur-want-better"'),
                        text.index('id="amateur-two-scores"'))
        self.assertLess(text.index('id="amateur-two-scores"'),
                        text.index('id="amateur-practice-study"'))
        argument = section(text, "amateur-two-scores")
        for outcome in ("有进步也尽兴", "有进步但不好玩",
                        "没进步却尽兴", "两者都没有"):
            self.assertIn(outcome, argument)
        self.assertIn("答案不应靠温柔改成准了", argument)
        self.assertIn("不是论文验证过的分类工具", argument)
        self.assertIn("../docs/research.md#b02", argument)
        # The counterargument has moved, not disappeared or been duplicated.
        heading = "什么时候成就感就是你想要的？"
        self.assertEqual(len(re.findall(r"^#{2,3} " + re.escape(heading) + "$",
                                        text, re.M)), 1)
        self.assertIn("什么时候成就感就是你想要的", check.anchors_for(text))

    def test_flavor_counterargument_keeps_standards_contract_and_preference(self):
        path = "book/14-flavor.md"
        text = (ROOT / path).read_text()
        argument = section(text, "flavor-coffee-standards")
        for question in ("做出了什么", "是否符合约定", "我喜欢什么",
                         "我愿意为它付出什么"):
            self.assertIn(question, argument)
        self.assertIn("店家不能只用“口味主观”取消承诺", argument)
        self.assertIn("昨天与今天不同", argument)
        self.assertIn("认真辨认、比较、制作，本身也可以是乐趣", argument)
        # The opening can route directly to the objection, not just activities.
        opening = text.split("\n## ", 1)[0]
        self.assertIn("](#flavor-coffee-standards)", opening)
        for note in ("F05-flavor", "F25-ice-cream-structure", "B29-coffee-sensory"):
            self.assertIn("../docs/evidence/" + note + ".md", opening)
        html = build.markdown(text, path)
        self.assertIn('href="#flavor-coffee-standards"', html)
        for target in ("f05", "f25", "n29"):
            self.assertIn(f'href="#{target}"', html)

    def test_editing_does_not_make_uncertainty_or_individual_constraints_optional(self):
        flavor = (ROOT / "book/14-flavor.md").read_text()
        amateur = (ROOT / "essays/05-play-is-not-performance.md").read_text()
        for boundary in ("不是独立消费者试验", "不是专业感官量表",
                         "温度和配方", "配料或晶体", "“奶更多”",
                         "可选的少，不等于享受能力低",
                         "不是证明完全相同",
                         "不是试吃报告、餐厅榜单或营养处方"):
            self.assertIn(boundary, flavor)
        for boundary in ("未解决的遗憾", "没有复核双方引用的全部底层研究",
                         "未与正式发表版逐字核对",
                         "未达到常用显著性门槛", "共同承诺"):
            self.assertIn(boundary, amateur)


if __name__ == "__main__":
    unittest.main()
