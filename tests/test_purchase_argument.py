"""Guard argument order and qualifications, not persuasion or comprehension."""
import hashlib
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

SOURCE = "essays/04-buying-pleasure.md"
PARTS = (
    ("purchase-purpose", "一、先看买到了什么，再争论它值不值"),
    ("purchase-choice", "二、喜欢有资格竞争，但谁有权作决定？"),
    ("purchase-agency", "三、喜欢不必纯洁，也不必冒充另一种用途"),
    ("purchase-judgement", "四、尝试可以落空，选择也应接受反对"),
)


class PurchaseArgumentTests(unittest.TestCase):
    def test_four_disputes_not_a_shopping_procedure(self):
        text = (ROOT / SOURCE).read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M),
                         [title for _, title in PARTS])
        self.assertEqual(len(re.findall(r"^### .+$", text, re.M)), 20)
        opening = text.split("\n## ", 1)[0]
        self.assertIn("不是四步购物流程", opening)
        for anchor, _ in PARTS:
            self.assertIn(f"](#{anchor})", opening)
        self.assertLess(text.index("### “用很多年”"),
                        text.index('id="purchase-choice"'))
        self.assertLess(text.index('id="purchase-claim"'),
                        text.index('id="purchase-shared"'))
        self.assertLess(text.index('id="purchase-moving-rules"'),
                        text.index('id="purchase-options"'))
        self.assertLess(text.index('id="purchase-owning"'),
                        text.index('id="purchase-uncertainty"'))

    def test_reopening_an_agreement_keeps_counterexamples(self):
        text = (ROOT / SOURCE).read_text()
        section = text.split('<a id="purchase-moving-rules"></a>', 1)[1].split(
            '<a id="purchase-options"></a>', 1)[0]
        for phrase in (
            "虚构家庭", "个人额度与使用规则", "没有增加共同负担",
            "额度一开始就没谈妥", "从未存在的约定",
            "最强的反对", "原来的安排可能不再适用",
            "此前没有说清的占地、维护或他人劳动",
            "条件改变了，还是条件没变、只是不喜欢这次的答案",
            "这不是判断家庭公平的算法", "不能单凭一个反问裁决关系",
        ):
            self.assertIn(phrase, section)
        chapter = (ROOT / "book/06-spending.md").read_text()
        # The chapter now introduces these issues by argument line rather than
        # a single list of purchase problems; keep its boundary with E04.
        for anchor in ("spending-two-ledgers", "spending-next-purchase",
                       "spending-own-evening"):
            self.assertIn('id="' + anchor + '"', chapter)
            self.assertIn("](#" + anchor + ")", chapter)
        self.assertIn("谁来决定剩下的生活", chapter)
        self.assertIn("账单已经付过一次", chapter)

    def test_distinct_material_and_source_limits_remain(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in (
            "唯一的工作电脑已损坏", "多花的120元",
            "两个愿望都真，也可以只能实现一个",
            "温哥华招募 60 名工作成年人", "不能推出长期效果",
            "不验证 [J033]", "不能把所有互斥用途的好处相加",
            "没有从头重读", "不能给每件闲置物品追认一个收藏理由",
            "既真喜欢，也怕被落下", "好结果也不能自动证明",
            "本文的可支配额度前提", "我们不要求他把遗憾改写成",
        ):
            self.assertIn(phrase, text)
        self.assertEqual(build.markdown(text, SOURCE).count("<table>"), 2)
        for title in ("把愿望说成能观察的场景", "总价里，最容易漏掉的不是钱",
                      "一份不规定你该花多少的购买说明"):
            self.assertTrue(check.anchors_for("# " + title) <= check.anchors_for(text))

    def test_full_retrieval_and_offline_links_keep_the_argument(self):
        raw = (ROOT / SOURCE).read_bytes()
        text = raw.decode()
        documents, routes = read.load_documents(ROOT)
        essay = next(d for d in documents if d["id"] == "E04")
        self.assertEqual(essay["text"], text)
        self.assertEqual(essay["source_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertIn(text, (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R46")
        self.assertIn("条件确实改变", route["text"])
        self.assertIn("不是家庭公平算法", route["text"])
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            epub = archive.read("EPUB/text/essays--04-buying-pleasure.xhtml").decode()
        for anchor in [a for a, _ in PARTS] + ["purchase-moving-rules"]:
            self.assertIn("#" + anchor, route["text"])
            self.assertEqual(html.count('id="' + anchor + '"'), 1)
            self.assertEqual(epub.count('id="' + anchor + '"'), 1)


if __name__ == "__main__":
    unittest.main()
