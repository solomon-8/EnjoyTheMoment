"""Argument structure and source boundaries; not evidence of reader preference."""
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

SOURCE = "book/07-solo.md"


class SoloStructureTests(unittest.TestCase):
    def test_argument_has_three_distinct_lines_before_optional_cards(self):
        text = (ROOT / SOURCE).read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M), [
            "一、独享不是共同生活的减配版",
            "二、坐在公共生活里，不必先成为谁的同伴",
            "三、有一间安静的房间，还缺什么？",
            "配套：不是独处能力测试",
        ])
        public = text.index('<a id="solo-public"></a>')
        conditions = text.index('<a id="solo-conditions"></a>')
        self.assertLess(text.index("独享不是“等不到别人”的次等版本"), public)
        self.assertLess(text.index("什么都能自己做，会不会越来越不联系别人"), public)
        self.assertLess(public, text.index('<a id="solo-man-of-crowd"></a>'))
        self.assertLess(text.index("单人安排确实更贵、更麻烦"), conditions)
        self.assertLess(conditions, text.index('<a id="solo-room"></a>'))
        self.assertLess(text.index('<a id="solo-companions"></a>'),
                        text.index('<a id="j037"></a>'))
        self.assertIn("一个人的生活，不是多人生活的候补席", text)

    def test_chairs_are_a_literary_argument_not_a_distance_prescription(self):
        text = (ROOT / SOURCE).read_text()
        part = text.split('<a id="solo-conversation-space"></a>', 1)[1].split(
            "### 一项不替任何一边站队的研究", 1)[0]
        for phrase in ("思想像船一样", "两块石头", "相反的墙角",
                       "比喻与叙述安排", "不是“坐远一点更容易交流”的实验结论",
                       "不冒充梭罗对当代关系的建议", "代价落在哪里",
                       "不必解释每一种口味，与不必回应任何约定，是两回事",
                       "喜欢紧挨着聊天也不比隔着湖讲话浅薄"):
            self.assertIn(phrase, part)
        note = (ROOT / "docs/evidence/F47-walden-solitude.md").read_text()
        for phrase in ("主章只选航行与水波展开", "不是通读整本",
                       "不建议读者按文中距离布置座位",
                       "不是唯一读法", "不证明 J037–J042"):
            self.assertIn(phrase, note)

    def test_shared_principles_have_explicit_routes_instead_of_another_scenario(self):
        text = (ROOT / SOURCE).read_text()
        part = text.split('<a id="solo-availability"></a>', 1)[1].split(
            '<a id="solo-not-audition"></a>', 1)[0]
        self.assertNotIn("设想两个人都有一个安静的晚上", part)
        for phrase in ("[时间章](21-free-time.md)",
                       "09-constrained.md#constrained-three-arrangements",
                       "缺人手也不是更坚定地说话就能解决",
                       "未经同意地继续待命", "可能买到的是使用条件"):
            self.assertIn(phrase, part)
        documents, routes = read.load_documents(ROOT)
        by_id = {d["id"]: d for d in documents}
        self.assertEqual(by_id["C07"]["text"], text)
        r11 = next(r for r in routes if r["id"] == "R11")
        self.assertEqual(set(r11["targets"]),
                         {"C07", "F47", "F48", "B06", "N06", "C05", "C09", "C21"})
        self.assertIn("三条主线并不对应三个效果指标", r11["text"])
        self.assertIn("不把重复出现计算为新发现", r11["text"])

    def test_reader_anchors_and_spoiler_choice_remain_available(self):
        text = (ROOT / SOURCE).read_text()
        html = build.markdown(text, SOURCE)
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            epub = z.read("EPUB/text/book--07-solo.xhtml").decode()
        for identifier in ("solo-experience", "solo-public", "solo-conditions",
                           "solo-conversation-space", "solo-companions",
                           "solo-own-pace", "solo-walden", "solo-room",
                           "solo-availability", "solo-not-audition",
                           "solo-public-alibi", "solo-man-of-crowd",
                           "solo-public-without-performance"):
            self.assertEqual(html.count('id="' + identifier + '"'), 1)
            self.assertEqual(epub.count('id="' + identifier + '"'), 1)
        self.assertEqual(html.count("<details>"), 1)
        self.assertNotIn("<details open", html)
        self.assertIn("行走路线可以被写得很详细", epub)
        self.assertIn('href="#connection-shared-attention"', html)
        self.assertIn('href="#constrained-three-arrangements"', html)
        self.assertIn("book--09-constrained.xhtml#constrained-three-arrangements", epub)
        self.assertEqual(len(json.loads((ROOT / "data/catalog.json").read_text())["cards"]), 60)
        self.assertEqual(len(json.loads((ROOT / "data/research.json").read_text())["records"]), 47)


if __name__ == "__main__":
    unittest.main()
