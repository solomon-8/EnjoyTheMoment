"""Preserve a normative thought experiment and its concessions, not score lives."""
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

SOURCE = "essays/03-now-or-later.md"
ANCHOR = "waiting-reliable-more"


class ReliableFutureTests(unittest.TestCase):
    def test_thought_experiment_grants_later_real_advantages(self):
        text = (ROOT / SOURCE).read_text()
        passage = text.split(f'<a id="{ANCHOR}"></a>', 1)[1].split(
            '<a id="waiting-anticipation"></a>', 1)[0]
        for phrase in (
            "写定的思想实验", "不是雇佣制度、收入案例或推荐的作息",
            "不是在声称现实工作都有这样的效率差",
            "甲：前六个晚上用来玩，后八个晚上完成任务",
            "乙：前六个晚上完成任务，后八个晚上用来玩",
            "这十四个时段之外，两种安排相同",
            "也不把工作或照料转给别人", "八个晚上一定兑现",
            "林安到时仍会喜欢", "没有错过某个人",
            "甲也不会靠回忆、效率或人脉偷偷补回收益",
            "少得到两个玩乐的晚上，也多用两个晚上完成同一任务",
        ):
            self.assertIn(phrase, passage)
        # Check the stated hypothetical only, not a real-world efficiency model.
        early = ["leisure"] * 6 + ["task"] * 8
        later = ["task"] * 6 + ["leisure"] * 8
        self.assertEqual(len(early), len(later))
        self.assertEqual(later.count("leisure") - early.count("leisure"), 2)
        self.assertEqual(early.count("task") - later.count("task"), 2)
        self.assertLess(text.index(f'id="{ANCHOR}"'), text.index('id="waiting-anticipation"'))

    def test_value_choice_does_not_become_an_empirical_victory(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in (
            "仅仅指出两种安排不同，还没有证明甲更值得",
            "若林安只在乎愉快总量",
            "不能替他创造一个他并不认同的优先项",
            "甲可以被选择，不意味着甲应被规定给所有人",
            "可这不是在美化短视吗", "也多用两个晚上",
            "甲包含后来完成任务", "此刻的理由不是今后每次延期的空白授权",
            "本书没有兑换率", "如果根本没有可选择的甲",
            "不验证林安的选择", "不是说选乙的六周毫无快乐",
        ):
            self.assertIn(phrase, text)
        self.assertEqual(len(re.findall(r"^## ", text, re.M)), 5)
        self.assertEqual(build.markdown(text, SOURCE).count("<table>"), 1)
        for phrase in ("28名幼儿", "900秒是观察上限",
                       "它们不是四场安排人真实等待的实验"):
            self.assertIn(phrase, text)

    def test_entrypoints_lead_to_argument_not_a_card(self):
        entry = build.entry_arguments(ROOT)
        self.assertEqual(len(re.findall(r"^### ", entry, re.M)), 5)
        self.assertIn("essays/03-now-or-later.md#" + ANCHOR, entry)
        self.assertIn("我们不只是在赌未来不会兑现", entry)
        for source in ("SHUAQI.md", "README.en.md"):
            self.assertIn("essays/03-now-or-later.md#" + ANCHOR,
                          (ROOT / source).read_text())
        docs, routes = read.load_documents(ROOT)
        self.assertEqual(next(d for d in docs if d["id"] == "E03")["text"],
                         (ROOT / SOURCE).read_text())
        route = next(r for r in routes if r["id"] == "R04")
        self.assertIn("E11", route["targets"])
        for phrase in ("甲少玩两晚且多做两晚任务", "均为假定",
                       "不偷偷借失信", "甲不可行时不能靠态度制造资源"):
            self.assertIn(phrase, route["text"])
        self.assertEqual(len(json.loads((ROOT / "data/catalog.json").read_text())["cards"]), 60)
        self.assertEqual(len(json.loads((ROOT / "data/research.json").read_text())["records"]), 50)
        self.assertEqual(len(json.loads((ROOT / "data/evidence.json").read_text())["notes"]), 141)

    def test_complete_export_retains_concession_and_cross_links(self):
        text = (ROOT / SOURCE).read_text()
        full = (ROOT / "llms-full.txt").read_text()
        self.assertIn(text, full)
        self.assertEqual(full.count(text), 1)
        html = (ROOT / "index.html").read_text()
        self.assertEqual(html.count(f'id="{ANCHOR}"'), 1)
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            essay = z.read("EPUB/text/essays--03-now-or-later.xhtml").decode()
            manifesto = z.read("EPUB/text/SHUAQI.xhtml").decode()
        self.assertEqual(essay.count(f'id="{ANCHOR}"'), 1)
        self.assertIn("若林安只在乎愉快总量", essay)
        self.assertIn("essays--11-pleasure-and-reality.xhtml#pleasure-position", essay)
        self.assertIn("essays--03-now-or-later.xhtml#" + ANCHOR, manifesto)


if __name__ == "__main__":
    unittest.main()
