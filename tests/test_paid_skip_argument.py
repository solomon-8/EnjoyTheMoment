"""Check C19's written model and source boundaries, not enjoyment or fair prices."""
import hashlib
import itertools
import json
from pathlib import Path
import re
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import read

SOURCE = "book/19-games.md"
ANCHORS = ("games-paid-skip", "games-skip-example",
           "games-skip-menu", "games-skip-objection")


class PaidSkipArgumentTests(unittest.TestCase):
    def test_written_table_enumerates_options_not_a_happiness_optimum(self):
        text = (ROOT / SOURCE).read_text()
        rows = re.findall(
            r"^\| (都不买|只买甲|只买乙|甲乙都买) \| (\d+)元 \| ([^|]+) \| ([^|]+) \|$",
            text, re.M)
        self.assertEqual(len(rows), 4)
        observed = {}
        for label, fee, equation, phases in rows:
            # The printed arithmetic must itself be correct, not just the total.
            lhs, _, rhs = equation.strip().partition(" = ")
            if rhs:
                self.assertEqual(sum(map(int, lhs.split(" + "))), int(rhs.removesuffix("分钟")))
            total = int((rhs or lhs).removesuffix("分钟"))
            observed[label] = (int(fee), total, phases.strip().split("、"))
        expected = {}
        for a, b in itertools.product((False, True), repeat=2):
            label = {(False, False): "都不买", (True, False): "只买甲",
                     (False, True): "只买乙", (True, True): "甲乙都买"}[a, b]
            phases = ([] if a else ["运送"]) + ([] if b else ["解谜"]) + ["结尾"]
            expected[label] = (6 * (a + b), 15 * (not a) + 20 * (not b) + 5, phases)
        self.assertEqual(observed, expected)
        feasible = {label for label, (fee, time, _) in expected.items()
                    if fee <= 6 and time <= 30}
        self.assertEqual(feasible, {"只买甲", "只买乙"})
        preserves_puzzle = {label for label in feasible if "解谜" in expected[label][2]}
        self.assertEqual(preserves_puzzle, {"只买甲"})
        for phrase in ("不据此预测真实解谜速度", "只玩一部分，或者先停下",
                       "同一张表就不能替他得出相同判断", "运送虽没有新线索",
                       "不给这些人的快乐打分", "没有隐藏收费、额外奖励或多人排名"):
            self.assertIn(phrase, text)

    def test_choice_menu_and_accessibility_are_not_collapsed(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in (
            "愿意购买一个出口，不等于希望入口越来越难走",
            "不能断言设计者故意制造痛苦",
            "不能把这里写定的第三种情节移植过去",
            "不等于已经存在一个免费且同样可行的替代版本",
            "更高的一次性价格、更少内容",
            "不是额外收费政策",
            "可能是为了进入他想要的挑战，不是省掉那份挑战",
            "不能拿它替多人排名、竞赛规则或队友作决定",
        ):
            self.assertIn(phrase, text)
        for link in ("06-spending.md#spending-future-cost",
                     "../essays/10-pleasure-not-retention.md#digital-honest-cost"):
            self.assertIn(link, text)
        note = (ROOT / "docs/evidence/F09-game-difficulty.md").read_text()
        for phrase in ("2026-10-03", "2026-03-04", "没有观看示例视频",
                       "不等于本书已经独立核读那些文章", "不出自微软",
                       "不是市场报价", "指南没有给付费跳过背书",
                       "不增加B类研究"):
            self.assertIn(phrase, note)

    def test_full_retrieval_keeps_scenario_and_counterarguments(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {d["id"]: d for d in documents}
        for ident, source in (("C19", SOURCE),
                              ("F09", "docs/evidence/F09-game-difficulty.md")):
            raw = (ROOT / source).read_bytes()
            self.assertEqual(by_id[ident]["text"], raw.decode())
            self.assertEqual(by_id[ident]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertIn(raw.decode().strip(), (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R18")
        expected = {"C19", "C04", "C06", "E10", "F09", "F42", "F43", "B09", "N09"}
        self.assertEqual(set(route["targets"]), expected)
        self.assertTrue(expected <= {
            d["id"] for d in read.linked_records(route, documents, ROOT)})
        for phrase in ("未测快乐", "不是指南的收费政策", "不是B09的实验结论"):
            self.assertIn(phrase, route["text"])
        evidence = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        self.assertEqual(next(n["source_kind"] for n in evidence if n["id"] == "F09"),
                         "technical_guidance")

    def test_html_epub_and_source_have_reciprocal_argument_links(self):
        text = (ROOT / SOURCE).read_text()
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            chapter = archive.read("EPUB/text/book--19-games.xhtml").decode()
            note = archive.read("EPUB/text/docs--evidence--F09-game-difficulty.xhtml").decode()
        for anchor in ANCHORS:
            self.assertEqual(text.count(f'<a id="{anchor}"></a>'), 1)
            self.assertIn(f"](#{anchor})", text)
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
            self.assertEqual(chapter.count(f'id="{anchor}"'), 1)
        for anchor in ANCHORS[1:]:
            self.assertIn("book--19-games.xhtml#" + anchor, note)
        self.assertEqual(chapter.count("<table>"), 3)
        for phrase in ("15 + 20 + 5 = 40分钟", "不是额外收费政策", "没有证明乙是最优解"):
            self.assertIn(phrase, chapter)
        self.assertIn("book--06-spending.xhtml#spending-future-cost", chapter)
        self.assertIn("essays--10-pleasure-not-retention.xhtml#digital-honest-cost", chapter)


if __name__ == "__main__":
    unittest.main()
