"""Content, diagram and retrieval guards; not material tests or reader experiments."""
import base64
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build


class RepairIntentionsTests(unittest.TestCase):
    def test_goal_distinctions_and_nonclaims(self):
        text = (ROOT / "book/17-making.md").read_text()
        for phrase in (
            "功能、外观和来路", "不是馆藏", "黄铜粉而不是金粉",
            "准确起源未知", "列为后来传说", "该访谈描述的修复取向",
            "外观整合与干预可辨认", "不必把自己的每一次介入都做成签名",
            "不把器物工艺转成心理疗效", "旧东西不必恢复成从未坏过"):
            self.assertIn(phrase, text)
        for anchor in ("making-weave", "making-sample", "making-zine", "making-handmade",
                       "making-repair-goals", "making-kintsugi", "making-conservation",
                       "making-repair-history", "making-repair-choice"):
            self.assertIn('id="' + anchor + '"', text)
        html = build.markdown(text, "book/17-making.md")
        self.assertEqual(html.count('src="data:image/png;base64,'), 3)
        self.assertIn('href="#f68"', html)

    def test_source_scope_retains_material_and_ownership_differences(self):
        note = (ROOT / "docs/evidence/F68-repair-and-conservation.md").read_text()
        for phrase in (
            "2026-08-24T14:37:35+00:00", "2021-08-04", "Abigail Duckor",
            "Supna Kapoor", "私人碗，而非馆藏", "黄铜粉替代金粉",
            "调整练习", "起源未知", "后来传说", "没有观看",
            "没有亲手实践", "不是材料性能实验", "均403", "没有复制"):
            self.assertIn(phrase, note)

    def test_diagram_same_geometry_not_a_material_model(self):
        xml = ET.parse(ROOT / "assets/media/repair-intentions.svg").getroot()
        ns = {"s": "http://www.w3.org/2000/svg"}
        self.assertEqual(xml.attrib["viewBox"], "0 0 440 990")
        for identifier in ("quiet", "visible", "redesigned"):
            group = xml.find(".//s:g[@id='" + identifier + "']", ns)
            refs = [n.attrib["href"] for n in group.findall("s:use", ns)]
            self.assertEqual(refs, ["#base-shape", "#gap"])
        svg = (ROOT / "assets/media/repair-intentions.svg").read_text()
        self.assertIn("不是器物或教程", svg)
        self.assertIn("不比较牢固", svg)
        png = (ROOT / "assets/media/repair-intentions.png").read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", png[16:24]), (880, 1980))
        self.assertIn("data:image/png;base64," + base64.b64encode(png).decode(),
                      (ROOT / "index.html").read_text())
        self.assertIn("repair-intentions.svg", (ROOT / "assets/media/README.md").read_text())

    def test_fulltext_hashes_and_body_backlinks(self):
        for identifier, path in (
            ("C17", "book/17-making.md"),
            ("F68", "docs/evidence/F68-repair-and-conservation.md")):
            result = json.loads(subprocess.check_output(
                [sys.executable, "tools/read.py", "--id", identifier], cwd=ROOT))
            self.assertTrue(result["complete"])
            self.assertEqual(result["record"]["text"], (ROOT / path).read_text())
            self.assertEqual(result["record"]["source_sha256"],
                             hashlib.sha256((ROOT / path).read_bytes()).hexdigest())
            self.assertIn("R66", {x["id"] for x in result["reading_guidance"]})
        html = build.markdown((ROOT / "docs/evidence/F68-repair-and-conservation.md").read_text(),
                              "docs/evidence/F68-repair-and-conservation.md")
        for anchor in ("making-repair-goals", "making-conservation", "making-repair-choice"):
            self.assertIn('href="#' + anchor + '"', html)

    def test_not_an_added_behavioral_study_or_card_validation(self):
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        self.assertEqual(len(notes), 115)
        note = next(n for n in notes if n["id"] == "F68")
        self.assertEqual(note["source_kind"], "cultural_craft_explainer_and_conservator_interview")
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(records), 39)
        self.assertNotIn("F68", {r["id"] for r in records})
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("F68" not in c["background_ids"] for c in cards))
        routes = json.loads((ROOT / "data/reading-map.json").read_text())["routes"]
        route = next(r for r in routes if r["id"] == "R66")
        self.assertEqual(set(route["targets"]),
                         {"C17", "F68", "F28", "F29", "B07", "N07", "C20", "C25", "C26"})


if __name__ == "__main__":
    unittest.main()
