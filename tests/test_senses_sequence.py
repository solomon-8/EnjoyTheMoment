"""Guard argument order and publication; not evidence of reader preference."""
import hashlib
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

PARTS = (
    ("senses-contact", "一、只看东西，为什么还不够解释感受？"),
    ("senses-expectations", "二、受影响的喜欢，就不算真的喜欢了吗？"),
    ("senses-preferences", "三、认真喜欢，不等于必须更贵、更强、更多"),
    ("senses-shared", "四、同一个晚上，谁在尽兴，谁在迁就？"),
)


class SensesSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / "book/02-senses.md").read_text()

    def test_parts_distinguish_contact_expectation_preference_and_shared_cost(self):
        self.assertEqual(re.findall(r"^## (.+)$", self.text, re.M),
                         [title for _, title in PARTS])
        positions = []
        for anchor, title in PARTS:
            marker = f'<a id="{anchor}"></a>\n## {title}'
            self.assertEqual(self.text.count(marker), 1)
            self.assertIn(f"](#{anchor})", self.text)
            positions.append(self.text.index(marker))
        self.assertEqual(positions, sorted(positions))
        for anchor in ("senses-three-layers", "senses-bite-sound",
                       "senses-thermal-touch", "senses-contact-not-label",
                       "senses-knowledge-and-pleasure"):
            self.assertLess(positions[0], self.text.index(f'id="{anchor}"'))
            self.assertLess(self.text.index(f'id="{anchor}"'), positions[1])
        for anchor in ("senses-price-expectation", "senses-blind-test"):
            self.assertLess(positions[1], self.text.index(f'id="{anchor}"'))
            self.assertLess(self.text.index(f'id="{anchor}"'), positions[2])
            self.assertIn(f"](#{anchor})", self.text)
        self.assertLess(positions[2], self.text.index('id="senses-intensity"'))
        self.assertLess(self.text.index('id="senses-intensity"'), positions[3])
        self.assertIn("初始温度相同的不同材料", self.text)
        self.assertIn("两项研究问的不是同一个问题", self.text)
        self.assertIn("不替后面的价值选择作决定", self.text)

    def test_blind_comparison_does_not_supply_evidence_of_deception(self):
        section = self.text.split('<a id="senses-blind-test"></a>', 1)[1]
        section = section.split('<a id="senses-preferences"></a>', 1)[0]
        for phrase in (
            "两种选择都可能前后一致",
            "如果她另外核实了店家用来解释价格的说法不实",
            "但这需要另外的事实证据",
            "“不看包装时更喜欢另一杯”，本身不能证明店家撒谎",
            "口味比较、核查宣传和下一次是否购买，相关却不能互相冒充",
            "不是识破虚荣的考试",
        ):
            self.assertIn(phrase, section)
        self.assertNotIn("这个发现至少允许三种后续", section)

    def test_counterarguments_and_original_card_ids_remain(self):
        self.assertEqual(re.findall(r"^#### (.+)$", self.text, re.M), [
            "最强的反对意见：这不是把每一点不适都当成不能妥协吗？",
            "受影响的快乐，不必被判成假；被欺骗也不必被原谅",
        ])
        self.assertEqual(len(re.findall(r"^\| ---", self.text, re.M)), 3)
        self.assertEqual(re.findall(r"^### (J\d+) ·", self.text, re.M),
                         [f"J{i:03d}" for i in range(7, 13)])
        html = build.markdown(self.text, "book/02-senses.md")
        for anchor, title in PARTS:
            self.assertIn(f'id="{anchor}"', html)
            self.assertRegex(html, r"<h3\b[^>]*>" + re.escape(title) + r"</h3>")

    def test_full_text_and_route_keep_the_same_reasoning(self):
        documents, routes = read.load_documents(ROOT)
        chapter = next(d for d in documents if d["id"] == "C02")
        self.assertEqual(chapter["text"], self.text)
        self.assertEqual(chapter["source_sha256"],
                         hashlib.sha256(self.text.encode()).hexdigest())
        full = (ROOT / "llms-full.txt").read_text()
        self.assertIn(self.text.split('<a id="j007">', 1)[0].strip(), full)
        route = next(r for r in routes if r["id"] == "R71")
        self.assertEqual(route["targets"], [
            "C02", "B38", "N38", "B19", "N19", "B46", "N46",
            "F05", "C14", "C16", "E04",
        ])
        for anchor, _ in PARTS:
            self.assertIn(f"02-senses.md#{anchor}", route["text"])
        for phrase in ("不是四项实证结果", "需要独立事实证据",
                       "阿青是原创假想", "不要求先做J卡"):
            self.assertIn(phrase, route["text"])

    def test_epub_has_parts_subquestions_and_argument_boundary(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            xml = ET.fromstring(archive.read("EPUB/text/book--02-senses.xhtml"))
            ns = {"h": "http://www.w3.org/1999/xhtml"}
            headings = ["".join(e.itertext()) for e in xml.findall(".//h:h2", ns)]
            self.assertEqual(headings, [title for _, title in PARTS])
            ids = [e.attrib["id"] for e in xml.iter() if "id" in e.attrib]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertTrue(check.anchors_for(self.text) <= set(ids))
            self.assertIn("本身不能证明店家撒谎", "".join(xml.itertext()))
            routes = ET.fromstring(archive.read("EPUB/text/docs--reading-map.xhtml"))
            hrefs = {e.attrib["href"] for e in routes.iter() if "href" in e.attrib}
            for anchor, _ in PARTS:
                self.assertIn("book--02-senses.xhtml#" + anchor, hrefs)


if __name__ == "__main__":
    unittest.main()
