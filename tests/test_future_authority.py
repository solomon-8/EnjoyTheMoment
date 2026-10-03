"""Preserve the argument and retrieval scope; not a test of persuasion or age effects."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import check
import read


class FutureAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = "essays/03-now-or-later.md"
        cls.raw = (ROOT / cls.path).read_bytes()
        cls.text = cls.raw.decode()
        cls.anchors = ("waiting-changed-taste", "waiting-later-knowledge", "waiting-open-future")

    def test_case_is_written_not_a_longitudinal_observation(self):
        for phrase in (
            "不是对年龄变化的预测", "不是真人回访", "二十四岁的小岑",
            "可以支配的那部分钱", "没有新发现被漏掉的费用或失约",
            "这足以支持她现在不再去，还不足以证明当年的她不该去",
            "当时快乐", "那个选择不妥", "后来不再去，不等于当年不该去",
        ):
            self.assertIn(phrase, self.text)
        self.assertNotIn("Quoidbach", self.text)
        self.assertNotIn("<!-- pick:", self.text)

    def test_strong_objection_and_long_commitments_remain(self):
        for phrase in (
            "后来知道得更多，就更有资格裁决过去吗",
            "作品、一次参与和一种长期生活安排",
            "前面那张演出票的假想，不能拿来替所有不可逆决定开路",
            "最难的一种分歧甚至没有漏算", "她当然可以对过去作出负面判断",
            "需要理由的意见，不是带日期的判决书",
            "既然将来可能变", "让同伴按她的承诺安排时间",
            "短承诺也不是普遍优解", "没有承诺，可能得不到连续性",
            "不要求一种喜欢先保证终身有效",
        ):
            self.assertIn(phrase, self.text)
        self.assertEqual(build.markdown(self.text, self.path).count("<table>"), 2)

    def test_complete_text_routes_and_inventory(self):
        documents, routes = read.load_documents(ROOT)
        doc = next(d for d in documents if d["id"] == "E03")
        self.assertEqual(doc["text"], self.text)
        self.assertEqual(doc["source_sha256"], hashlib.sha256(self.raw).hexdigest())
        self.assertIn(self.text, (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R04")
        self.assertEqual(set(route["targets"]), {"E03", "E04", "E05", "E11", "B23", "N23"})
        for phrase in ("不是年龄变化实验", "没有真人回访", "不预测哪个年龄更明智",
                       "不把短承诺当普遍最优", "不把三文的相通原则重复当成独立证据"):
            self.assertIn(phrase, route["text"])
        self.assertEqual(len(json.loads((ROOT / "data/research.json").read_text())["records"]), 47)
        self.assertEqual(len(json.loads((ROOT / "data/evidence.json").read_text())["notes"]), 134)
        self.assertEqual(len(json.loads((ROOT / "data/catalog.json").read_text())["cards"]), 60)

    def test_all_anchors_and_related_arguments_reach_epub(self):
        rendered = build.markdown(self.text, self.path)
        html = (ROOT / "index.html").read_text()
        for anchor in self.anchors:
            self.assertEqual(self.text.count(f'<a id="{anchor}"></a>'), 1)
            self.assertEqual(rendered.count(f'id="{anchor}"'), 1)
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            xml = ET.fromstring(z.read("EPUB/text/essays--03-now-or-later.xhtml"))
        ids = [e.attrib["id"] for e in xml.iter() if "id" in e.attrib]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(check.anchors_for(self.text).issubset(set(ids)))
        links = [e.attrib["href"] for e in xml.iter() if "href" in e.attrib]
        self.assertTrue(any("essays--04-buying-pleasure.xhtml#" in h for h in links))
        self.assertIn("essays--05-play-is-not-performance.xhtml#amateur-changing-group", links)
        body = "".join(xml.itertext())
        for phrase in ("不是带日期的判决书", "后来不再去，不等于当年不该去"):
            self.assertIn(phrase, body)


if __name__ == "__main__":
    unittest.main()
