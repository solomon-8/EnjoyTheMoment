"""Argument structure and publication fidelity, not a test of reader interest."""
import hashlib
from pathlib import Path
import re
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check
import read

SOURCE = "essays/08-life-without-an-audience.md"
PARTS = (
    ("audience-purpose", "一、想被看见，不必先证明自己的快乐很纯粹"),
    ("audience-costs", "二、表达可以占用当下，但代价不能只算自己的"),
    ("audience-judgments", "三、作品、传播与经历，不能互相代判"),
    ("audience-companion", "配套：一个可选的比较，不是新的生活作业"),
)


class AudienceMeaningTests(unittest.TestCase):
    def test_three_arguments_precede_optional_experiment(self):
        text = (ROOT / SOURCE).read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M),
                         [title for _, title in PARTS])
        self.assertEqual(len(re.findall(r"^### .+$", text, re.M)), 19)
        opening = text.split('\n## ', 1)[0]
        for anchor, _ in PARTS:
            self.assertIn(f"](#{anchor})", opening)
        for first, second in (
            ("### 不要用“不发朋友圈”建立另一条鄙视链", 'id="audience-costs"'),
            ('id="audience-chosen-tradeoff"', 'id="audience-staging"'),
            ("### 如果你的工作本来就需要展示生活", 'id="audience-judgments"'),
            ('id="audience-verdict"', 'id="audience-misread-success"'),
            ('id="audience-misread-success"', "### 谁来给普通日子签收"),
            ("### 谁来给普通日子签收", 'id="audience-companion"'),
        ):
            self.assertLess(text.index(first), text.index(second))
        for title in ("三份快乐，不必争一个正统", "拍别人之前，先分清谁是主角",
                      "一个不必停用社交平台的小实验", "谁来给普通日子签收"):
            self.assertTrue(check.anchors_for("# " + title) <= check.anchors_for(text))

    def test_popularity_does_not_substitute_for_meaning_or_approval(self):
        text = (ROOT / SOURCE).read_text()
        part = text.split('<a id="audience-misread-success"></a>', 1)[1].split(
            "### 谁来给普通日子签收", 1)[0]
        for phrase in (
            "继续前面三位朋友的原创假想", "没有真实账号、传播数据或访谈",
            "曝光可能满足了其中一项", "更多人看见了，不等于更多人看见了你想表达的东西",
            "作品的唯一解释权", "仍觉得短片乏味", "只喜欢配乐",
            "理解也不欠作者赞同", "不能把观众据此形成的事实判断全推给",
            "隐私变成真实性的抵押物", "目标可以改，不能假装旧目标已经完成",
            "不能替伙伴一起改", "没有约定的追加工作或公开范围",
            "不保证错误版本消失", "不以热闹证明一切已经值得",
        ):
            self.assertIn(phrase, part)
        self.assertNotIn("[B", part)

    def test_existing_source_limits_and_counterarguments_remain(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in (
            "不能当作鉴定真心的试纸", "也不把这个目标偷偷缩小",
            "不需要被安慰成", "不是“禁止享受被夸”的规定",
            "不是“发帖”与“完全不用手机”的比较", "只读到作者公开的摘要",
            "不能独立核查这些机制", "不必用“我确实费了力”要求别人交付感动",
            "场景有没有被安排，作者对场景作了什么声称，参与者是否愿意",
            "我们不要求从每个失败里挖出隐藏的幸福",
            "没有哪种天然更好", "不是因果实验",
        ):
            self.assertIn(phrase, text)
        self.assertEqual(len(re.findall(r"^\| ---", text, re.M)), 1)

    def test_route_full_text_and_epub_preserve_the_same_argument(self):
        raw = (ROOT / SOURCE).read_bytes()
        text = raw.decode()
        documents, routes = read.load_documents(ROOT)
        essay = next(d for d in documents if d["id"] == "E08")
        self.assertEqual(essay["text"], text)
        self.assertEqual(essay["source_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertIn(text, (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R45")
        self.assertEqual(set(route["targets"]), {"E08", "C20", "B10", "N10", "B44", "N44"})
        for phrase in ("原创假想", "不是平台数据或B10/B44的研究结果",
                       "观众不欠作者唯一读法", "不能追认旧目标已经达成",
                       "澄清不保证错误消失或热度保留", "abstract_only"):
            self.assertIn(phrase, route["text"])
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            epub = archive.read("EPUB/text/essays--08-life-without-an-audience.xhtml").decode()
        for anchor in [a for a, _ in PARTS] + ["audience-misread-success"]:
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
            self.assertEqual(epub.count(f'id="{anchor}"'), 1)
            self.assertIn(f'href="#{anchor}"', html)
        self.assertIn("docs--evidence--B44-sharing-intention.xhtml", epub)
        self.assertIn("book--20-photography.xhtml#photo-sequence", epub)


if __name__ == "__main__":
    unittest.main()
