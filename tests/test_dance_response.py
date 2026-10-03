"""Finite-rule integrity and retrieval; not evidence of reader persuasion."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import check
import dance_examples
import read

SOURCE = "book/27-dance.md"
PARTS = (
    ("dance-standards", "一、先说清楚，这次在乎哪一种好"),
    ("dance-response", "二、动作怎样成为表达与回应"),
    ("dance-composition", "三、材料没换，组织方式也能改变经历"),
    ("dance-viewing", "四、观看和学习，不只剩一张分数表"),
)


class DanceResponseTests(unittest.TestCase):
    def test_stipulated_rules_agree_once_but_not_for_both_permitted_inputs(self):
        self.assertEqual(dance_examples.response_sequences("P"),
                         {"fixed": ("P", "Q"), "conditional": ("P", "Q")})
        self.assertEqual(dance_examples.response_sequences("R"),
                         {"fixed": ("R", "Q"), "conditional": ("R", "S")})
        for invalid in ("Q", "S", "", "p", None):
            with self.assertRaises(ValueError):
                dance_examples.response_sequences(invalid)
        text = (ROOT / SOURCE).read_text()
        for rule in ("fixed", "conditional"):
            sequences = ["→".join(dance_examples.response_sequences(first)[rule])
                         for first in ("P", "R")]
            self.assertIn(" | ".join(sequences) + " |", text)

    def test_argument_order_has_four_parts_and_preserves_the_counterargument(self):
        text = (ROOT / SOURCE).read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M),
                         [title for _, title in PARTS])
        self.assertEqual(len(re.findall(r"^### .+$", text, re.M)), 15)
        opening = text.split("\n## ", 1)[0]
        for anchor, _ in PARTS:
            self.assertIn(f"](#{anchor})", opening)
        self.assertLess(text.index("### 最强的反对意见"),
                        text.index('id="dance-response"'))
        self.assertLess(text.index('id="dance-choice-response"'),
                        text.index('id="dance-composition"'))
        self.assertLess(text.index('id="dance-time-grid"'),
                        text.index('id="dance-rosas"'))
        self.assertLess(text.index('id="dance-viewing"'),
                        text.index('id="dance-remix"'))
        html = build.markdown(text, SOURCE)
        self.assertEqual(html.count("<h3"), 4)
        self.assertEqual(html.count("<h4"), 15)
        self.assertEqual(html.count("<table>"), 3)
        self.assertEqual(html.count('src="data:image/png;base64,'), 1)

    def test_model_is_not_misrepresented_as_a_study_or_improvisation_ranking(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in (
            "本书原创的有限模型", "乙事先知道采用哪一种规则，甲也知道",
            "不是鼓励突然变招去测试真人", "第二种规则也不是",
            "这个模型并没有把编好的舞蹈说成没有互动",
            "把后续留空，也不会自动产生有意思的回应",
            "它不保证比预排更快乐", "没有记录真实舞者、测量感受",
            "相同的一次结果，不足以证明相同的回应关系",
        ):
            self.assertIn(phrase, text)
        note = (ROOT / "docs/evidence/F17-dance-language.md").read_text()
        self.assertIn("不来自上述课程或作品", note)
        self.assertIn("不证明真实舞者的动机、默契或享乐效果", note)
        self.assertIn("dance-choice-response", note)
        routes = (ROOT / "docs/reading-map.md").read_text()
        section = routes.split('{"id":"R22"', 1)[1].split('{"id":"R23"', 1)[0]
        self.assertIn("dance-choice-response", section)
        self.assertIn("不把即兴评为更高级", section)

    def test_full_text_route_and_epub_retain_new_reasoning_and_old_entrypoints(self):
        raw = (ROOT / SOURCE).read_bytes()
        text = raw.decode()
        docs, routes = read.load_documents(ROOT)
        chapter = next(d for d in docs if d["id"] == "C27")
        self.assertEqual(chapter["text"], text)
        self.assertEqual(chapter["source_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertIn(text, (ROOT / "llms-full.txt").read_text())
        self.assertEqual(set(next(r for r in routes if r["id"] == "R22")["targets"]),
                         {"C27", "F51", "F52"})
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            epub = archive.read("EPUB/text/book--27-dance.xhtml").decode()
        for anchor in check.anchors_for(text):
            self.assertEqual(epub.count(f'id="{anchor}"'), 1)
        for sequence in ("P→Q", "R→Q", "R→S"):
            self.assertIn(sequence, epub)
        data = json.loads((ROOT / "data/chapters.json").read_text())["chapters"]
        self.assertEqual(next(d for d in data if d["id"] == "C27")["text"], text.strip())

    def test_singing_link_labels_match_their_existing_targets(self):
        text = (ROOT / "book/33-singing.md").read_text()
        for path, destination in (
            ("book/13-live-events.md", "13-live-events.md"),
            ("essays/05-play-is-not-performance.md", "../essays/05-play-is-not-performance.md"),
        ):
            title = re.search(r"^# (.+)$", (ROOT / path).read_text(), re.M).group(1)
            label = title.split(" · ", 1)[1]
            self.assertIn(f"[{label}]({destination})", text)


if __name__ == "__main__":
    unittest.main()
