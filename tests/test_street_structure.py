"""Keep source types, counterargument and retrieval together; no quality score."""
import json
from pathlib import Path
import re
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read

SOURCE = "book/15-neighborhood.md"
NOTE = "docs/evidence/F88-paley-park.md"


class StreetStructureTests(unittest.TestCase):
    def test_three_arguments_are_not_an_activity_checklist(self):
        text = (ROOT / SOURCE).read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M), [
            "一、“待得住”，不是给环境打一个好评",
            "二、街上有多少人，与这些人怎样生活，是两个问题",
            "三、不想消费的人，能不能也拥有一个下午？",
        ])
        for phrase in ("不必先成为顾客", "可这不还是一份精致的消费指南",
                       "批评环境与在其中过一个好下午",
                       "不需要先提高鉴赏力才配提出要求",
                       "公共生活不是把人流做大",
                       "支持不参加的人继续过自己的生活"):
            self.assertIn(phrase, text)
        self.assertNotIn("<!-- pick:", text)
        self.assertNotIn("共同经历不是必须同步反应", text)

    def test_description_does_not_become_measurement_or_a_travel_promise(self):
        text = (ROOT / SOURCE).read_text()
        note = (ROOT / NOTE).read_text()
        for phrase in ("没有给出现场声级、频谱或对照测量",
                       "不是本书在现场观察到的三组访客",
                       "不保证现在每张椅子都可以任意移动",
                       "需要稳定支撑的人",
                       "允许自带食物", "明确园内没有厕所",
                       "没有核实附近替代设施"):
            self.assertIn(phrase, text)
        for phrase in ("2026-10-03", "不是声学测量", "未读取Visitor Information",
                       "本次没有观看", "Henry Bertoia", "Harry Bertoia",
                       "Zion & Breene", "Zion & Breen", "不复制来源图片"):
            self.assertIn(phrase, note)
        data = json.loads((ROOT / "data/evidence.json").read_text())
        n = next(n for n in data["notes"] if n["id"] == "F88")
        self.assertEqual(n["source_kind"], "practice_case_and_operator_description")
        self.assertEqual(n["text"], note)
        self.assertEqual(len(data["notes"]), 134)
        self.assertEqual(len(json.loads((ROOT / "data/catalog.json").read_text())["cards"]), 60)
        self.assertEqual(len(json.loads((ROOT / "data/research.json").read_text())["records"]), 47)

    def test_full_text_route_and_epub_keep_limits_with_the_case(self):
        text, note = (ROOT / SOURCE).read_text(), (ROOT / NOTE).read_text()
        full = (ROOT / "llms-full.txt").read_text()
        self.assertIn(text, full)
        self.assertIn(note, full)
        documents, routes = read.load_documents(ROOT)
        route = next(r for r in routes if r["id"] == "R15")
        self.assertEqual(set(route["targets"]), {"C15", "F35", "F36", "F88"})
        for phrase in ("没有声级、频谱或访客样本", "必须同时保留"):
            self.assertIn(phrase, route["text"])
        self.assertEqual(next(d for d in documents if d["id"] == "F88")["text"], note)
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            epub = z.read("EPUB/text/book--15-neighborhood.xhtml").decode()
            n = z.read("EPUB/text/docs--evidence--F88-paley-park.xhtml").decode()
        html = build.markdown(text, SOURCE)
        self.assertIn('href="#street-paley"', build.markdown(note, NOTE))
        for anchor in ("street-staying", "street-conditions", "street-welcome",
                       "street-counts", "street-midtown", "street-seats",
                       "street-unscheduled", "street-conflicts", "street-paley"):
            self.assertEqual(html.count('id="' + anchor + '"'), 1)
            self.assertEqual(epub.count('id="' + anchor + '"'), 1)
        self.assertEqual(epub.count("<table>"), 3)
        for anchor in ("f88-sound", "f88-seating", "f88-operation"):
            self.assertIn("docs--evidence--F88-paley-park.xhtml#" + anchor, epub)
            self.assertIn('id="' + anchor + '"', n)
        self.assertIn("book--15-neighborhood.xhtml#street-paley", n)
        self.assertIn("可这不还是一份精致的消费指南", epub)


if __name__ == "__main__":
    unittest.main()
