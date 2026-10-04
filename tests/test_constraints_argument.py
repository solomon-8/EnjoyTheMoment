"""Protect the argument and its limits; these are not reader-effect tests."""
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

SOURCE = "essays/06-real-life-constraints.md"
PARTS = (
    ("constraints-wishes", "一、资源有限，是否连愿望也要降级？"),
    ("constraints-shared-evening", "二、快乐值得认真对待，谁来承担腾出的那个晚上？"),
    ("constraints-conditions", "三、今天笑过，是否就不能继续说生活很难？"),
    ("constraints-options", "配套：需要具体选项时，再看这些条件"),
)


class ConstraintsArgumentTests(unittest.TestCase):
    def test_argument_precedes_optional_tools(self):
        text = (ROOT / SOURCE).read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M),
                         [title for _, title in PARTS])
        self.assertEqual(len(re.findall(r"^### .+$", text, re.M)), 18)
        self.assertEqual(len(re.findall(r"^#### .+$", text, re.M)), 4)
        opening = text.split("\n## ", 1)[0]
        for anchor, _ in PARTS:
            self.assertIn(f"](#{anchor})", opening)
        self.assertLess(text.index('id="constraints-prudence"'),
                        text.index('id="constraints-shared-evening"'))
        self.assertLess(text.index('id="constraints-help"'),
                        text.index('id="constraints-conditions"'))
        self.assertLess(text.index('id="constraints-options"'),
                        text.index("### 为什么我们的筛选器"))
        self.assertIn("不必先完成一次活动", text)

    def test_conflict_keeps_real_losses_and_counterarguments(self):
        text = (ROOT / SOURCE).read_text()
        section = text.split('<a id="constraints-conflicting-evenings"></a>', 1)[1]
        section = section.split("### 真正支持一个人的享乐", 1)[0]
        for phrase in (
            "设想阿岚与小雨", "没有可用的第三位接替者",
            "不把无人负责当作备选方案", "新的喜欢不会让旧约定自动失效",
            "也不能单方面替另一人排好留守", "没有优先约定，两个机会都不可替代",
            "没有一条能够证明谁更配快乐的公式", "既有共同责任",
            "不能把已经错过的演出或朋友原样还回来", "不必建立永久记分牌",
            "反复出现的模式", "即使分配更公平，也不保证人人都能如愿",
            "不是家庭裁决、照护指令或B26研究的结论",
        ):
            self.assertIn(phrase, section)

    def test_original_research_and_distinct_examples_remain(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in (
            "200名参与者", "73%", "87%", "有差别，不等于大多数人",
            "不自行补正", "不能证明购买越多越自由",
            "不必表演快乐来回报你", "承诺的选择空间",
            "零元，不等于零资源", "长期失去兴趣", "不进行诊断",
            "没有接替资源", "也不等于本来就不需要喜欢",
        ):
            self.assertIn(phrase, text)
        for heading in (
            "谁的“半小时”，实际上只有三次五分钟",
            "情境二：照料中，没有完整半小时",
            "为什么我们的筛选器不替你判定“适合”？",
            "真实反馈应该长什么样？",
        ):
            self.assertTrue(check.anchors_for("# " + heading) <=
                            check.anchors_for(text))

    def test_retrieval_and_exports_keep_limits_with_the_claim(self):
        raw = (ROOT / SOURCE).read_bytes()
        text = raw.decode()
        documents, routes = read.load_documents(ROOT)
        essay = next(d for d in documents if d["id"] == "E06")
        self.assertEqual(essay["text"], text)
        self.assertEqual(essay["source_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertIn(text, (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R48")
        self.assertEqual(set(route["targets"]),
                         {"E06", "C09", "E04", "E01", "B26", "N26"})
        for phrase in ("原创假想", "已有承诺", "不能原样归还错过",
                       "没有通用公平公式", "这不是B26研究结果"):
            self.assertIn(phrase, route["text"])
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            epub = archive.read(
                "EPUB/text/essays--06-real-life-constraints.xhtml").decode()
        for anchor in [a for a, _ in PARTS] + ["constraints-conflicting-evenings"]:
            self.assertIn("#" + anchor, route["text"])
            self.assertEqual(html.count('id="' + anchor + '"'), 1)
            self.assertEqual(epub.count('id="' + anchor + '"'), 1)

    def test_optional_scenes_link_to_full_arguments_without_losing_conditions(self):
        text = (ROOT / SOURCE).read_text()
        care = text.split("#### 情境二：", 1)[1].split("#### 情境三：", 1)[0]
        access = text.split("#### 情境三：", 1)[1].split("#### 情境四：", 1)[0]
        for phrase in ("愿意且有能力", "不是护理方案",
                       "不允许把被照料者留在无人负责的状态",
                       "没有接替资源", "也可能增加负担",
                       "若总是同一个人接班"):
            self.assertIn(phrase, care)
        for phrase in ("不是通用替代", "感官、动作或设备条件",
                       "由本人判断", "承认没有给出合适方案",
                       "不宣称“效果一样”", "谁能参与定义好玩"):
            self.assertIn(phrase, access)
        chapter = (ROOT / "book/09-constrained.md").read_text()
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            epub = archive.read(
                "EPUB/text/essays--06-real-life-constraints.xhtml").decode()
        for section, anchor in ((care, "constrained-shared"),
                                (access, "constrained-access-authorship")):
            self.assertIn("../book/09-constrained.md#" + anchor, section)
            self.assertEqual(chapter.count(f'id="{anchor}"'), 1)
            self.assertIn(f'href="#{anchor}"', html)
            self.assertIn(f'book--09-constrained.xhtml#{anchor}', epub)


if __name__ == "__main__":
    unittest.main()
