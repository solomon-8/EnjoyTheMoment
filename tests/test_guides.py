import itertools
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from guides import load_guides
from pick import load_cards


class PlaybookTests(unittest.TestCase):
    def test_four_card_chapter_puzzle_and_relaxed_constraint(self):
        text = (ROOT / "book/32-puzzles.md").read_text()
        clue_section = text.split("只使用三条条件：", 1)[1].split("问题：", 1)[0]
        clues = re.findall(r"^\d\. (.+)$", clue_section, re.M)
        self.assertEqual(clues, [
            "月亮紧挨着船的右边。",
            "地图不在最左边，也不在最右边。",
            "伞在月亮左边，但不要求紧挨着。",
        ])
        self.assertIn("每张卡恰好用一次，每个位置恰好一张卡", text)
        arrangements = list(itertools.permutations(("伞", "地图", "船", "月亮")))
        self.assertEqual(len(arrangements), 24)

        def valid(order, include_map=True):
            positions = {item: order.index(item) for item in order}
            return (positions["月亮"] == positions["船"] + 1
                    and (not include_map or positions["地图"] not in (0, 3))
                    and positions["伞"] < positions["月亮"])

        unique = [order for order in arrangements if valid(order)]
        self.assertEqual(unique, [("伞", "地图", "船", "月亮")])
        relaxed = {order for order in arrangements if valid(order, False)}
        self.assertEqual(relaxed, {
            ("伞", "地图", "船", "月亮"),
            ("伞", "船", "月亮", "地图"),
            ("地图", "伞", "船", "月亮"),
        })
        self.assertIn("**伞、地图、船、月亮**", text)
        answer_section = text.split("删掉地图位置条件后，有哪些答案？</summary>", 1)[1]
        answer_section = answer_section.split("</details>", 1)[0]
        listed = re.findall(r"^\d\. (.+)[；。]$", answer_section, re.M)
        self.assertEqual({tuple(row.split("、")) for row in listed}, relaxed)
        self.assertFalse(valid(("船", "月亮", "地图", "伞")))
        self.assertFalse(valid(("伞", "船", "月亮", "地图")))

    def test_metadata_and_exports(self):
        guides = load_guides()
        cards = {c.id for c in load_cards()}
        exported = json.loads((ROOT / "data/guides.json").read_text())["guides"]
        self.assertEqual(guides, exported)
        for guide in guides:
            self.assertTrue(set(guide["card_ids"]).issubset(cards))
            self.assertGreater(guide["minutes"], 0)
            self.assertGreaterEqual(guide["budget"], 0)
            self.assertIn(guide["company"], {"solo", "social", "either"})
            self.assertIn(guide["energy"], {"low", "medium", "high"})
            self.assertGreater(len(re.findall(r"[\u3400-\u9fff]", guide["text"])), 1000)
            self.assertIn('id="' + guide["id"].lower() + '"', (ROOT / "index.html").read_text())

    def test_letter_puzzle_unique_solution(self):
        # Names: Lan, Bei, Cheng. Letters: invitation, apology, postcard.
        solutions = []
        for names in itertools.permutations((18, 19, 20)):
            lan, bei, cheng = names
            for letters in itertools.permutations((18, 19, 20)):
                invite, apology, postcard = letters
                if (postcard == bei + 1 and lan != 18 and apology != 20
                        and cheng < invite and invite == 19):
                    solutions.append((names, letters))
        self.assertEqual(solutions, [((20, 19, 18), (19, 18, 20))])
        text = (ROOT / "guides/10-desk-detective.md").read_text()
        # Tie the verifier to the actual published clue set, not an unrelated model.
        clues = [
            "明信片比阿北收到的信晚一小时到达。",
            "阿岚不是最早收到信的人。",
            "道歉信不是最后到达的信。",
            "阿澄比收到邀请函的人更早收到信。",
            "邀请函在 19 点到达。",
        ]
        actual = re.findall(r"^\d\. (.+)$", text, re.M)
        self.assertEqual(actual, clues)
        self.assertIn("| 18 点 | 阿澄 | 道歉信 |", text)
        self.assertIn("| 19 点 | 阿北 | 邀请函 |", text)
        self.assertIn("| 20 点 | 阿岚 | 明信片 |", text)
        self.assertEqual(text.count("<details>"), 4)
