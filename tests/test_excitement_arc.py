"""Reading-order and preservation checks, not comprehension or appeal scores."""
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


class ExcitementArcTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = "essays/02-excitement-without-escalation.md"
        cls.raw = (ROOT / cls.source).read_bytes()
        cls.text = cls.raw.decode()
        cls.main_anchors = (
            "excitement-costs", "excitement-information",
            "excitement-mixed-feelings", "excitement-boundaries",
            "excitement-scoreboard",
        )

    def test_main_questions_have_ordered_direct_links_without_folding(self):
        opening = self.text.split('<a id="excitement-costs"', 1)[0]
        positions = [self.text.index(f'<a id="{a}"') for a in self.main_anchors]
        self.assertEqual(positions, sorted(positions))
        for anchor in self.main_anchors:
            self.assertIn(f"](#{anchor})", opening)
        self.assertNotIn("<details>", self.text)
        self.assertEqual(len(re.findall(r"^## ", self.text, re.M)), 5)
        self.assertLess(self.text.index("设想小梁"),
                        self.text.index("四种不同的刺激"))
        html = build.markdown(self.text, self.source)
        for anchor in self.main_anchors + (
            "excitement-study", "excitement-richness", "excitement-uncertainty",
            "excitement-fear", "excitement-check-before", "excitement-arrange",
            "另一个反对你是不是只肯为刺激付很小的代价",
            "一个更有野心但不靠冒险的版本",
        ):
            self.assertEqual(html.count(f'id="{anchor}"'), 1)

    def test_active_control_is_not_the_definition_of_all_participation(self):
        for phrase in (
            "参与感不按动了多少次手计算",
            "这里特指获得行动和改变进程的机会",
            "不是否认观看也有参与感",
            "若你想看的正是好故事，就不必被劝上台",
            "不能用“难得一次”替他们完成决定",
            "可以愿意出丑，却不愿公开影像",
            "公开活动不天然适合所有人，更不自动等于没有风险",
            "不是“花一百元就能买到刺激”的价格承诺",
            "小梁散场后可以说“不太值”",
        ):
            self.assertIn(phrase, self.text)
        self.assertNotIn("**参与**来自自己会影响过程", self.text)

    def test_studies_and_counterexamples_still_qualify_the_argument(self):
        for phrase in (
            "243名大学生和147名网络受访者", "这是偏好问卷，不是刺激剂量实验",
            "66名网络受访者", "48—58个回答", "59%", "37%", "82%", "56%",
            "分母变了", "没有实际展示", "不是临床诊断",
            "作者托管页校样", "没有相应的积极情绪差异",
            "丰富人生不是多数人的首选", "也没有检验即时满足比延迟更好",
            "喜欢作品带来的难过，不等于同意别人真的让你难过",
            "探索可能无效", "耍起不该给日历配一个排行榜",
        ):
            self.assertIn(phrase, self.text)
        for note in ("../docs/evidence/B03-richness.md",
                     "../docs/evidence/B24-hedonic-reversals.md"):
            self.assertIn(note, self.text)

    def test_full_retrieval_and_epub_keep_every_subsection(self):
        docs, routes = read.load_documents(ROOT)
        essay = next(d for d in docs if d["id"] == "E02")
        self.assertEqual(essay["text"], self.text)
        self.assertEqual(essay["source_sha256"],
                         hashlib.sha256(self.raw).hexdigest())
        self.assertIn(self.text, (ROOT / "llms-full.txt").read_text())
        exported = json.loads((ROOT / "data/essays.json").read_text())["essays"]
        self.assertEqual(next(d for d in exported if d["id"] == "E02")["text"],
                         self.text)
        route = next(r for r in routes if r["id"] == "R03")
        self.assertEqual(set(route["targets"]), {"E02", "E03", "C05", "C06", "C21", "C27", "B24", "N24", "B45", "N45", "B48", "N48", "F86"})
        self.assertIn("观看也可以投入", route["text"])
        self.assertIn("小梁、小何、阿澄均为假想", route["text"])
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            xml = ET.fromstring(archive.read(
                "EPUB/text/essays--02-excitement-without-escalation.xhtml"))
        ids = [element.attrib["id"] for element in xml.iter()
               if "id" in element.attrib]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(check.anchors_for(self.text).issubset(set(ids)))
        rendered_text = "".join(xml.itertext())
        for heading in re.findall(r"^#{2,3} (.+)$", self.text, re.M):
            self.assertIn(heading, rendered_text)


if __name__ == "__main__":
    unittest.main()
