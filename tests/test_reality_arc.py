"""Argument and source-boundary preservation, not a philosophical correctness score."""
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

SOURCE = "essays/11-pleasure-and-reality.md"
PARTS = (
    ("reality-values", "一、快乐值得，不等于只有快乐值得"),
    ("reality-events", "二、真实不是媒介标签：要看发生了什么"),
    ("reality-judgments", "三、判断可以更充分，选择不必交给排名"),
    ("reality-position", "四、回到耍起：承认取舍，不交出今天"),
)


class RealityArcTests(unittest.TestCase):
    def test_value_events_and_judgments_are_separate_sections(self):
        text = (ROOT / SOURCE).read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M),
                         [title for _, title in PARTS])
        self.assertEqual(len(re.findall(r"^### .+$", text, re.M)), 19)
        opening = text.split("\n## ", 1)[0]
        for anchor, _ in PARTS:
            self.assertIn(f"](#{anchor})", opening)
        for first, second in (
            ('id="pleasure-machine"', 'id="reality-events"'),
            ('id="pleasure-promises"', 'id="pleasure-ended-world"'),
            ('id="pleasure-ended-world"', 'id="pleasure-rebuilt-world"'),
            ('id="pleasure-rebuilt-world"', 'id="pleasure-medium"'),
            ('id="pleasure-medium"', 'id="reality-judgments"'),
            ('id="pleasure-taste-criticism"', 'id="reality-position"'),
        ):
            self.assertLess(text.index(first), text.index(second))
        self.assertIn("真实没有免除评价，评价也没有自动取得决定权", text)
        self.assertEqual(len(re.findall(r"^\| ---", text, re.M)), 2)

    def test_reconstruction_is_not_a_false_all_or_nothing_choice(self):
        text = (ROOT / SOURCE).read_text()
        part = text.split('<a id="pleasure-rebuilt-world"></a>', 1)[1].split(
            '<a id="pleasure-medium"></a>', 1)[0]
        for phrase in (
            "原来的修改记录、留言", "不是某个产品已经具备的迁移能力",
            "也不是查尔默斯论文中的案例", "不能先把后者解释成不懂数字",
            "重建可以提供新的快乐，不必假装旧的损失已经全部补回",
            "并没有先立一条数字物件必须只有一份的规则",
            "若备份保留了双方在意的状态和记录",
            "不裁决物体同一性的全部哲学问题",
            "先说明恢复了什么、没有恢复什么",
            "另一位朋友现在是否愿意回来",
            "不等于他此刻重新答应参加", "重演本身也可以值得",
            "不是在判断任何现有系统有没有意识",
            "一人愿意在新海港继续做，另一人不愿重来",
            "不许诺只要解释清楚就一定达成和解",
            "也不该被用来宣布每一种损失都已获赔",
            "喜欢新的，不需要改口说旧的从来不重要",
        ):
            self.assertIn(phrase, part)
        self.assertNotIn("[F59]", part)

    def test_old_arguments_and_source_status_are_not_lost(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in (
            "本仓库接受第一句，但不因此接受其余三句",
            "不把平静作为所有人的终点", "不是直接核读诺齐克原书",
            "不是从低到高的娱乐等级", "感动可以是真的",
            "不能拿“在线上”代替评价", "不能把二者说成永远可互换",
            "没有资格凭一次娱乐选择判断别人是不是退化了",
            "不是声称用一把钥匙就推翻了他的全文",
            "承认一件作品更好，不等于把自己的每个晚上都交给“最好”",
            "可以给作品差评，不必给喜欢它的人判刑",
            "如果任何反例都能靠改名消失", "也让别的价值仍然可以说话",
        ):
            self.assertIn(phrase, text)
        for title in ("享乐主义不等于每次都选更强的刺激",
                      "最强的反对意见：这会不会只是我们害怕离开熟悉世界？",
                      "如果真实、关系和成长也重要，这还算反对延迟享乐吗？"):
            self.assertTrue(check.anchors_for("# " + title) <= check.anchors_for(text))

    def test_reading_routes_and_published_formats_keep_boundaries(self):
        raw = (ROOT / SOURCE).read_bytes()
        documents, routes = read.load_documents(ROOT)
        essay = next(d for d in documents if d["id"] == "E11")
        self.assertEqual(essay["text"], raw.decode())
        self.assertEqual(essay["source_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertIn(raw.decode(), (ROOT / "llms-full.txt").read_text())
        routes = {r["id"]: r for r in routes}
        self.assertEqual(set(routes["R06"]["targets"]), {"E11", "F27", "F83", "F98", "C11", "C31"})
        self.assertEqual(set(routes["R52"]["targets"]), {"E11", "C19", "E09", "F59", "F27"})
        for phrase in ("照截图重新摆放", "备份恢复又是另一种条件",
                       "旧留言不替人续上同意", "不保证澄清后一定和解",
                       "不是F59实验或原文案例"):
            self.assertIn(phrase, routes["R52"]["text"])
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            epub = z.read("EPUB/text/essays--11-pleasure-and-reality.xhtml").decode()
        for anchor in [a for a, _ in PARTS] + ["pleasure-rebuilt-world"]:
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
            self.assertEqual(epub.count(f'id="{anchor}"'), 1)
            self.assertIn(f'href="#{anchor}"', html)
        self.assertIn("book--26-collecting.xhtml", epub)
        self.assertIn("F59-virtual-and-real.xhtml", epub)
        self.assertIn("F83-standard-of-taste.xhtml", epub)


if __name__ == "__main__":
    unittest.main()
