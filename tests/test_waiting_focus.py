"""Protect consolidated routes and exports, not comprehension or literary quality."""
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read

SOURCE = "essays/03-now-or-later.md"
ALIASES = (
    "两种等待外表相似体验未必相同",
    "期待现实限制与资格加码不是同一件事",
    "四种很像规划却需要拆开的句子",
    "waiting-reasons",
)


class WaitingFocusTests(unittest.TestCase):
    def test_consolidated_section_keeps_published_fragment_destinations(self):
        text = (ROOT / SOURCE).read_text()
        html = build.markdown(text, SOURCE)
        for anchor in ALIASES:
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
            self.assertLess(html.index(f'id="{anchor}"'),
                            html.index("等待有没有在替你工作"))
        section = text.split('### 等待有没有在替你工作？', 1)[1].split(
            '<a id="waiting-marshmallow">', 1)[0]
        self.assertIn("不是互斥选项", section)
        self.assertIn("不是临床量表", section)
        self.assertIn("小份有自己的价值，不等于大愿望已被满足", section)
        self.assertIn("独自不是升级版，共同也不是必需版", section)
        self.assertNotIn("<table>", build.markdown(section, SOURCE))
        self.assertNotIn("### 四种很像规划", section)

    def test_conclusion_routes_to_three_distinct_arguments_not_activity_cards(self):
        text = (ROOT / SOURCE).read_text()
        section = text.split('### 作决定前，先说清这一票投给什么', 1)[1].split(
            '### 改变主意，不等于当初的期待作废', 1)[0]
        for anchor in ("waiting-reliable-more", "waiting-reversal",
                       "waiting-changed-taste", "waiting-open-future",
                       "waiting-reasons", "waiting-different-goods"):
            self.assertIn(f"](#{anchor})", section)
        self.assertNotIn("#j0", section)
        self.assertIn("不靠抹去另一边的所得来赢", section)
        self.assertIn("挪用共同资金", section)

    def test_machine_and_epub_readers_keep_consolidated_text_and_aliases(self):
        text = (ROOT / SOURCE).read_text()
        docs, _ = read.load_documents(ROOT)
        self.assertEqual(next(d for d in docs if d["id"] == "E03")["text"], text)
        self.assertIn(text, (ROOT / "llms-full.txt").read_text())
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            xml = ET.fromstring(z.read("EPUB/text/essays--03-now-or-later.xhtml"))
        ids = [el.attrib["id"] for el in xml.iter() if "id" in el.attrib]
        for anchor in ALIASES:
            self.assertEqual(ids.count(anchor), 1)
        self.assertIn("我们偏爱让今天有生活", "".join(xml.itertext()))


if __name__ == "__main__":
    unittest.main()
