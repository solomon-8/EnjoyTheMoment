"""Preserve argument order and distinctions, not claims of reader persuasion."""
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

SOURCE = "essays/05-play-is-not-performance.md"
PARTS = (
    ("amateur-purpose", "一、爱好的价值，不只是一条水平曲线"),
    ("amateur-methods", "二、方法可以改善表现，不能替你决定今晚的目标"),
    ("amateur-together", "三、自己可以不求进步，但共同标准由谁决定？"),
    ("amateur-companions", "配套：记录、装备与重新开始，按需要使用"),
)


class AmateurArgumentTests(unittest.TestCase):
    def test_core_arguments_precede_optional_product_material(self):
        text = (ROOT / SOURCE).read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M),
                         [title for _, title in PARTS])
        self.assertEqual(len(re.findall(r"^### .+$", text, re.M)), 18)
        self.assertEqual(len(re.findall(r"^#### .+$", text, re.M)), 3)
        opening = text.split("\n## ", 1)[0]
        for anchor, _ in PARTS:
            self.assertIn(f"](#{anchor})", opening)
        for left, right in (
            ('id="amateur-maintenance"', 'id="amateur-methods"'),
            ('id="amateur-practice-study"', 'id="amateur-together"'),
            ('id="amateur-shared-standards"', 'id="amateur-changing-group"'),
            ('id="amateur-changing-group"', 'id="amateur-criticism"'),
            ('id="amateur-criticism"', 'id="amateur-companions"'),
            ('id="amateur-companions"', '### 为什么这里没有连续签到？'),
        ):
            self.assertLess(text.index(left), text.index(right))
        for title in ("三种“业余”，不是三个等级", "一个可试、也可否定的比较",
                      "学习、装备与社群，各自占什么位置", "停一阵以后，怎样回来才不像补欠账"):
            self.assertTrue(check.anchors_for("# " + title) <= check.anchors_for(text))

    def test_changing_group_has_no_automatic_winner_or_costless_exit(self):
        text = (ROOT / SOURCE).read_text()
        part = text.split('<a id="amateur-changing-group"></a>', 1)[1].split(
            '<a id="amateur-criticism"></a>', 1)[0]
        for phrase in (
            "小遥和四位朋友", "接下来几次相聚", "只有原来那个共同空档",
            "没有约定多数人可以替所有人报名", "原创假想",
            "不能自己生出小遥答应排练的事实", "永远不改变的合同",
            "不能只在自己占优势时临时发明规则", "与每个人愿意为它承诺什么",
            "不是原来快乐的无损替代", "共同时间并没有因此增加",
            "退出可以是被允许的，也可以是令人难过的", "难过不自动证明别人做错",
            "原来承担组织的人也不必无限维护", "不能用改组取消已有责任",
            "原来的固定聚会结束了", "不把这个结局包装成人人成长",
        ):
            self.assertIn(phrase, part)
        self.assertNotIn("[B", part)

    def test_evidence_and_distinct_existing_positions_remain(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in (
            "未解决的遗憾", "不是论文验证过的分类工具",
            "88项研究、111个独立样本", "不是“努力只占成功的14%”",
            "没有复核双方引用的全部底层研究", "120名18—24岁", "14个百分点",
            "不是同一批人被连续测了三次", "不能把三个均值排序写成每一对都显著不同",
            "不是整个过程的享受量表", "不能推出所有计步器、日记或进度记录都坏",
            "共同承诺不能默认不算数", "不是免于评价的作品",
            "拒绝进步的义务，不是签下永不进步的义务",
        ):
            self.assertIn(phrase, text)
        self.assertEqual(len(re.findall(r"^\| ---", text, re.M)), 4)

    def test_full_retrieval_route_and_epub_keep_the_new_boundary(self):
        raw = (ROOT / SOURCE).read_bytes()
        text = raw.decode()
        documents, routes = read.load_documents(ROOT)
        essay = next(d for d in documents if d["id"] == "E05")
        self.assertEqual(essay["text"], text)
        self.assertEqual(essay["source_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertIn(text, (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R47")
        self.assertEqual(set(route["targets"]),
                         {"E05", "C04", "E08", "B02", "N02", "B25", "N25", "B43", "N43"})
        for phrase in ("原创假想", "人数不自动构成新增承诺", "分组不保证无损替代",
                       "不是B02/B25/B43的结果", "不替实际组织制定规则"):
            self.assertIn(phrase, route["text"])
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            epub = archive.read("EPUB/text/essays--05-play-is-not-performance.xhtml").decode()
            note = archive.read("EPUB/text/docs--evidence--B43-testing-and-retention.xhtml").decode()
        for anchor in [a for a, _ in PARTS] + ["amateur-changing-group"]:
            self.assertIn("#" + anchor, route["text"])
            self.assertEqual(html.count('id="' + anchor + '"'), 1)
            self.assertEqual(epub.count('id="' + anchor + '"'), 1)
        self.assertIn("essays--05-play-is-not-performance.xhtml#amateur-effective-for-what", note)


if __name__ == "__main__":
    unittest.main()
