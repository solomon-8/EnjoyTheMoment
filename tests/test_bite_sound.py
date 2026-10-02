"""Publication and retrieval guards, not a replication or an attention test."""
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


class BiteSoundTests(unittest.TestCase):
    def test_chapter_distinguishes_feedback_texture_freshness_and_liking(self):
        text = (ROOT / "book/02-senses.md").read_text()
        section = text.split('<a id="senses-bite-sound"></a>', 1)[1]
        section = section.split('<a id="senses-thermal-touch"></a>', 1)[0]
        for phrase in (
            "这一口的脆，为什么还要问耳朵", "20名成人", "不咀嚼、不吞咽",
            "没有给某一组播放背景音乐", "细分结果的文字还与图示方向冲突",
            "实验没有让声音把食物变新鲜", "实验没有测享受或喜欢程度",
            "不等于把餐厅音乐开大", "不建议自行放大咬声",
            "同一个性质",
        ):
            self.assertIn(phrase, section)
        html = build.markdown(text, "book/02-senses.md")
        self.assertEqual(html.count('id="senses-bite-sound"'), 1)
        for href in ("#n46", "#b46", "#flavor-ice-cream"):
            self.assertIn(f'href="{href}"', html)
        flavor = (ROOT / "book/14-flavor.md").read_text()
        self.assertIn("02-senses.md#senses-bite-sound", flavor)
        self.assertNotIn("90次", flavor)  # A handoff, not a duplicate study summary.

    def test_note_keeps_the_two_conflicts_and_access_limits(self):
        text = (ROOT / "docs/evidence/B46-bite-sound.md").read_text()
        for phrase in (
            "第三方镜像", "出版社页面本次返回403", "未与出版社下载逐字比较",
            "90是每人的正式试次数，不是90名参与者", "另有18次练习",
            "不是同时评两种", "不是耳边声压为零",
            "把75归给高频减弱、54归给增强",
            "把81归给减弱、60归给增强",
            "不是已经证明完全无差别", "two-way", "未提供的原始编码",
            "没有独立复核那篇早期研究", "非正式询问",
            "没有验证J007–J012",
        ):
            self.assertIn(phrase, text)
        record = next(r for r in build.research_records(ROOT) if r["id"] == "B46")
        self.assertEqual(record["doi"], "10.1111/j.1745-459x.2004.080403.x")
        self.assertEqual(record["verified_at"], "2026-10-03")
        self.assertEqual(record["access_level"], "full_text")
        self.assertFalse(record["directly_validates_cards"])
        self.assertNotIn("10.1068/p5321", text)

    def test_full_text_route_and_original_card_meanings(self):
        documents, routes = read.load_documents(ROOT)
        documents = {document["id"]: document for document in documents}
        for identifier, source in (
            ("C02", "book/02-senses.md"),
            ("C14", "book/14-flavor.md"),
            ("N46", "docs/evidence/B46-bite-sound.md"),
        ):
            raw = (ROOT / source).read_bytes()
            self.assertEqual(documents[identifier]["text"], raw.decode())
            self.assertEqual(documents[identifier]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
        full = (ROOT / "llms-full.txt").read_text()
        self.assertIn(documents["N46"]["text"], full)
        self.assertIn(documents["C02"]["text"].split('<a id="j007">', 1)[0].strip(),
                      full)
        route = next(route for route in routes if route["id"] == "R71")
        self.assertTrue({"C02", "C14", "B46", "N46"} <= set(route["targets"]))
        for phrase in ("图2与355页两处细分文字方向冲突", "0 dB表示不衰减而非无声",
                       "没有安全检测", "#senses-bite-sound"):
            self.assertIn(phrase, route["text"])
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        note = next(note for note in notes if note["id"] == "N46")
        self.assertEqual(note["source_kind"], "study_reading_note")
        self.assertEqual(note["text"], documents["N46"]["text"])
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("B46" not in card["background_ids"] for card in cards))

    def test_epub_retains_source_text_and_bidirectional_links(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            for source, entry, targets in (
                ("book/02-senses.md", "book--02-senses.xhtml",
                 {"docs--evidence--B46-bite-sound.xhtml",
                  "docs--research.xhtml#b46",
                  "book--14-flavor.xhtml#flavor-ice-cream"}),
                ("book/14-flavor.md", "book--14-flavor.xhtml",
                 {"book--02-senses.xhtml#senses-bite-sound"}),
                ("docs/evidence/B46-bite-sound.md",
                 "docs--evidence--B46-bite-sound.xhtml",
                 {"book--02-senses.xhtml#senses-bite-sound",
                  "docs--research.xhtml#b46"}),
            ):
                xml = ET.fromstring(archive.read("EPUB/text/" + entry))
                ids = [element.attrib["id"] for element in xml.iter()
                       if "id" in element.attrib]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertTrue(check.anchors_for((ROOT / source).read_text())
                                <= set(ids))
                hrefs = {element.attrib["href"] for element in xml.iter()
                         if "href" in element.attrib}
                self.assertTrue(targets <= hrefs, targets - hrefs)
            note_xml = ET.fromstring(archive.read(
                "EPUB/text/docs--evidence--B46-bite-sound.xhtml"))
            self.assertIn("把81归给减弱、60归给增强", "".join(note_xml.itertext()))


if __name__ == "__main__":
    unittest.main()
