"""Protect the reading arc and full qualifications, not reader comprehension."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import check
import read


class WaitingArcTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = "essays/03-now-or-later.md"
        cls.raw = (ROOT / cls.source).read_bytes()
        cls.text = cls.raw.decode()
        cls.main_anchors = (
            "waiting-credible-promise", "waiting-long-term-defense",
            "waiting-not-a-patience-score", "waiting-real-window",
            "waiting-future-self",
        )

    def test_five_questions_put_the_promised_argument_first(self):
        opening = self.text.split('<a id="', 1)[0]
        positions = [self.text.index(f'<a id="{a}"') for a in self.main_anchors]
        self.assertEqual(positions, sorted(positions))
        for anchor in self.main_anchors:
            self.assertIn(f"](#{anchor})", opening)
        self.assertEqual(len(re.findall(r"^## ", self.text, re.M)), 5)
        self.assertNotIn("<details>", self.text)
        self.assertLess(self.text.index("阿宁和朋友原定"),
                        self.text.index("等待有没有在替你工作"))
        self.assertLess(self.text.index("一项与“越快越好”冲突的研究"),
                        self.text.index("以后不是“同一份快乐"))
        self.assertLess(self.text.index("真正会关的窗口"),
                        self.text.index('## 未来的你'))

    def test_waiting_components_can_coexist_without_diagnosis(self):
        for phrase in (
            "这些成分可能同时存在，不是三类人，也不是互斥选项",
            "一边攒钱、一边享受期待",
            "钱够了以后，却又给自己追加不相关的门槛",
            "不是临床量表",
            "不确定的计划可以诚实",
            "我们并不主张把朋友关系变成验收合同",
            "小份有自己的价值，不等于大愿望已被满足",
            "独自不是升级版，共同也不是必需版",
        ):
            self.assertIn(phrase, self.text)

    def test_studies_remain_qualified_and_do_not_decide_values(self):
        for phrase in (
            "28名幼儿", "1/14和9/14", "900秒是观察上限",
            "这项研究没有证明自控无关", "补充材料未取得",
            "不能让28个孩子替我们投票",
            "它们不是四场安排人真实等待的实验",
            "物品组的等待评分也在正向一侧",
            "幸福评分的差别并未达到常用的统计显著性门槛",
            "不是上述研究的发现",
            "假想答卷", "脚注14", "不能把前者讲成已观察到后者",
            "及时享乐不等于及时省事",
            "改善入口不等于锁住出口",
        ):
            self.assertIn(phrase, self.text)

    def test_full_text_and_epub_keep_routes_and_old_destinations(self):
        docs, routes = read.load_documents(ROOT)
        doc = next(d for d in docs if d["id"] == "E03")
        self.assertEqual(doc["text"], self.text)
        self.assertEqual(doc["source_sha256"], hashlib.sha256(self.raw).hexdigest())
        self.assertIn(self.text, (ROOT / "llms-full.txt").read_text())
        essays = json.loads((ROOT / "data/essays.json").read_text())["essays"]
        self.assertEqual(next(e for e in essays if e["id"] == "E03")["text"], self.text)
        route = next(r for r in routes if r["id"] == "R04")
        self.assertEqual(set(route["targets"]), {"E03", "E01", "E04", "E05", "E11", "B23", "N23"})
        self.assertIn("不是互斥分类或人格诊断", route["text"])
        html = build.markdown(self.text, self.source)
        for anchor in self.main_anchors + (
            "waiting-anticipation", "两种等待外表相似体验未必相同",
            "waiting-reversal", "waiting-plan-revision",
            "waiting-pleasure-procrastination", "waiting-commitment-objection",
            "一个不装精确的决定办法", "三个虚构例子",
        ):
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            xml = ET.fromstring(archive.read("EPUB/text/essays--03-now-or-later.xhtml"))
        ids = [el.attrib["id"] for el in xml.iter() if "id" in el.attrib]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(check.anchors_for(self.text).issubset(set(ids)))
        rendered = "".join(xml.itertext())
        for heading in re.findall(r"^#{2,3} (.+)$", self.text, re.M):
            self.assertIn(heading, rendered)


if __name__ == "__main__":
    unittest.main()
