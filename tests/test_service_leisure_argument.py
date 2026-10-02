"""Protect the argument and export scope, not a quality or attention score."""
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


class ServiceLeisureArgumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = "essays/07-rest-is-not-work.md"
        cls.raw = (ROOT / cls.source).read_bytes()
        cls.text = cls.raw.decode()
        cls.anchors = (
            "rest-service-work", "rest-service-ending",
            "rest-paid-service", "rest-less-convenience",
        )
        cls.section = cls.text.split('<a id="rest-service-work">', 1)[1].split(
            '<a id="rest-position">', 1)[0]

    def test_entrypoints_reach_the_argument_not_an_activity_card(self):
        opening = self.text[:self.text.index("## 一、")]
        self.assertIn("](#rest-shared)", opening)
        shared_intro = self.text.split('<a id="rest-shared">', 1)[1].split(
            "### 第二个反对意见", 1)[0]
        self.assertIn("](#rest-service-work)", shared_intro)
        for anchor in self.anchors[1:]:
            self.assertIn(f"](#{anchor})", self.section)
        for name in ("SHUAQI.md", "docs/reading-map.md"):
            self.assertIn(self.source + "#rest-service-work", (ROOT / name).read_text())
        self.assertNotIn("<details>", self.section)
        html = build.markdown(self.text, self.source)
        for anchor in self.anchors:
            self.assertEqual(html.count(f'id="{anchor}"'), 1)

    def test_cooperation_refusal_and_service_failure_are_distinct(self):
        for phrase in (
            "别人可以用工作支持我的快乐",
            "不要求所有人同一刻下班",
            "不是某家场馆的经历、行业调查或劳动法律解释",
            "如果大家事先已经按更晚结束安排好",
            "需要重新确认受影响的人和条件",
            "负责人答应观众继续",
            "小林也可能想多挣这笔钱",
            "不能拿“尊重劳动”把服务失约变成顾客必须体谅",
            "这里不是说经济需要让一切同意作废",
            "不应被要求审查每位工作人员的生活",
        ):
            self.assertIn(phrase, self.section)

    def test_less_convenience_is_a_real_cost_not_a_universal_solution(self):
        for phrase in (
            "愿意让自己的快乐少一点",
            "更高的价格可能把原本负担得起的人挡在门外",
            "本篇没有证据保证它们能保住全部体验、收入和可及性",
            "不愿把一群人永远待命",
            "没有提出一张适用于所有行业的轮休表",
            "耍起，不该只对买单的人说",
        ):
            self.assertIn(phrase, self.section)
        self.assertNotRegex(self.section, r"\[B\d{2}\]")
        self.assertNotRegex(self.section, r"\[J\d{3}")

    def test_full_retrieval_route_and_epub_keep_the_counterarguments(self):
        docs, routes = read.load_documents(ROOT)
        essay = next(d for d in docs if d["id"] == "E07")
        self.assertEqual(essay["text"], self.text)
        self.assertEqual(essay["source_sha256"], hashlib.sha256(self.raw).hexdigest())
        self.assertIn(self.text, (ROOT / "llms-full.txt").read_text())
        exported = json.loads((ROOT / "data/essays.json").read_text())["essays"]
        self.assertEqual(next(d for d in exported if d["id"] == "E07")["text"], self.text)
        route = next(r for r in routes if r["id"] == "R41")
        self.assertIn("经济需要不自动取消同意", route["text"])
        self.assertIn("不把F82/B05借来背书", route["text"])
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            xml = ET.fromstring(archive.read(
                "EPUB/text/essays--07-rest-is-not-work.xhtml"))
        ids = [el.attrib["id"] for el in xml.iter() if "id" in el.attrib]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(check.anchors_for(self.text).issubset(set(ids)))
        rendered = "".join(xml.itertext())
        for heading in re.findall(r"^#{2,4} (.+)$", self.section, re.M):
            self.assertIn(heading, rendered)


if __name__ == "__main__":
    unittest.main()
