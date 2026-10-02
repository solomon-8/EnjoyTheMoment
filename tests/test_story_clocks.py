"""Check the finite examples and export boundaries, not player experience."""

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build


class StoryClockTests(unittest.TestCase):
    def test_published_clock_rows_form_the_declared_finite_ledger(self):
        text = (ROOT / "book/34-shared-stories.md").read_text()
        rows = re.findall(
            r"(?m)^\| ([^\n|]+) \| (\d+)/(\d+) \| (\d+)/(\d+) \|$", text)
        self.assertEqual(len(rows), 4)
        values = [(int(a), int(c)) for _, a, b, c, d in rows]
        capacities = {(int(b), int(d)) for _, a, b, c, d in rows}
        self.assertEqual(capacities, {(6, 4)})
        self.assertEqual(values, [(0, 0), (2, 1), (3, 3), (6, 4)])
        changes = [tuple(after[i] - before[i] for i in (0, 1))
                   for before, after in zip(values, values[1:])]
        self.assertEqual(changes, [(2, 1), (1, 2), (3, 1)])
        self.assertTrue(all(0 <= a <= 6 and 0 <= b <= 4 for a, b in values))
        self.assertTrue(all(a < 6 and b < 4 for a, b in values[:-1]))
        self.assertEqual(values[-1], (6, 4))
        for phrase in ("不模拟完整检定", "已经裁定的三个事件",
                       "钟箱已经在船上，离港窗口也已经关闭",
                       "不能因此宣布成功率是百分之五十"):
            self.assertIn(phrase, text)

    def test_chronology_and_costs_are_not_rewritten_as_guaranteed_success(self):
        text = (ROOT / "book/34-shared-stories.md").read_text()
        table = text.split("| 当前已经知道什么 |", 1)[1].split("\n\n", 1)[0]
        self.assertEqual(len([line for line in table.splitlines()
                              if line.startswith("| ") and not line.startswith("| ---")]), 3)
        for phrase in ("不是自动成功", "不因为句子短就免费", "不能靠闪回直接改写"):
            self.assertIn(phrase, table)
        for phrase in ("不是时间旅行", "二或更多", "不是花了压力就保证结果",
                       "一 coin 或一 rep", "不会让开场处境永久锁住",
                       "约定被换掉了", "隐藏故事信息与隐藏参与条件不一样"):
            self.assertIn(phrase, text)
        note = (ROOT / "docs/evidence/F65-clocks-and-flashbacks.md").read_text()
        for phrase in ("初始处境", "1—3为绝望", "4—5为冒险", "6为可控",
                       "零效果或极大效果", "不能取消当前已确立的事实",
                       "不是随机模拟", "未实际游玩"):
            self.assertIn(phrase, note)

    def test_source_is_complete_attributed_and_not_a_new_behavioral_study(self):
        path = ROOT / "docs/evidence/F65-clocks-and-flashbacks.md"
        text = path.read_text()
        note = next(n for n in json.loads((ROOT / "data/evidence.json").read_text())["notes"]
                    if n["id"] == "F65")
        self.assertEqual(note["source_kind"], "official_game_srd_and_original_examples")
        self.assertEqual(note["text"], text)
        rendered = build.markdown(text, note["source"])
        self.assertIn('href="#story-flashbacks"', rendered)
        self.assertIn('href="#story-uncertainty"', rendered)
        retrieved = json.loads(subprocess.check_output(
            [sys.executable, "tools/read.py", "--id", "F65"], cwd=ROOT))
        self.assertTrue(retrieved["complete"])
        self.assertEqual(retrieved["record"]["text"], text)
        self.assertEqual(retrieved["record"]["source_sha256"],
                         hashlib.sha256(path.read_bytes()).hexdigest())
        for source in ("progress-clocks", "effect", "planning-engagement", "licensing"):
            self.assertIn("https://bladesinthedark.com/" + source, text)
        self.assertEqual(len(re.findall(r"`[0-9a-f]{64}`", text)), 4)
        attribution = next(line for line in text.splitlines()
                           if line.startswith("This work is based on"))
        for filename in ("LICENSE", "book/34-shared-stories.md"):
            self.assertIn(attribution, (ROOT / filename).read_text())
        self.assertIn(str(path.relative_to(ROOT)), (ROOT / "LICENSE").read_text())
        studies = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(studies), 44)
        self.assertNotIn("F65", {r["id"] for r in studies})

    def test_chapter_and_route_have_visible_full_text_targets(self):
        path = ROOT / "book/34-shared-stories.md"
        text = path.read_text()
        chapter = next(c for c in json.loads((ROOT / "data/chapters.json").read_text())["chapters"]
                       if c["id"] == "C34")
        self.assertEqual(chapter["scope"], "full_chapter")
        self.assertEqual(chapter["text"], text.strip())
        self.assertEqual(chapter["card_ids"], [])
        self.assertIn(text, (ROOT / "llms-full.txt").read_text())
        self.assertEqual(len(re.findall(r"(?m)(?:^\|.*\n)+", text)), 5)
        html = build.markdown(text, "book/34-shared-stories.md")
        for anchor in ("story-clocks", "story-flashbacks", "story-uncertainty"):
            self.assertEqual(html.count('id="' + anchor + '"'), 1)
            self.assertIn('href="#' + anchor + '"', html)
        self.assertIn('href="#f65"', html)
        routes = json.loads((ROOT / "data/reading-map.json").read_text())["routes"]
        route = next(r for r in routes if r["id"] == "R61")
        self.assertEqual(set(route["targets"]), {"C34", "F65", "F32", "F33", "C04", "C19"})
        self.assertIn("不自动把询问价值与规则改成活动推荐", route["text"])


if __name__ == "__main__":
    unittest.main()
