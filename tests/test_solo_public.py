"""Text, source-boundary and disclosure checks, not audience-effect evidence."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read


class SoloPublicTests(unittest.TestCase):
    def test_argument_is_not_a_solo_activity_list(self):
        source = "book/07-solo.md"
        text = (ROOT / source).read_text()
        for phrase in (
            "一个人坐着，为什么非得假装在等人",
            "不是一项关于所有服务员或所有城市的调查",
            "隐私不是谎言", "不应该以毫不介意别人的目光为考试",
            "注意到了细节，不等于获得了关于一个人的全部证据",
            "行走路线可以被写得很详细",
            "关于他人的事实", "单人版本有缺点，不代表应该停演",
            "最强的反对意见", "可能分摊不了固定费用",
        ):
            self.assertIn(phrase, text)
        rendered = build.markdown(text, source)
        for identifier in (
            "solo-public-alibi", "solo-man-of-crowd",
            "solo-public-without-performance", "solo-own-pace",
            "solo-walden", "solo-room", "solo-availability", "solo-not-audition",
        ):
            self.assertIn(f'id="{identifier}"', rendered)
        self.assertIn('href="#f72"', rendered)
        self.assertIn("<details>", rendered)
        self.assertIn("包含《人群中的人》的追踪过程与结尾", rendered)
        self.assertNotIn("<details open", rendered)

    def test_primary_text_has_real_version_and_fiction_boundaries(self):
        source = "docs/evidence/F72-man-of-the-crowd.md"
        text = (ROOT / source).read_text()
        for phrase in (
            "Text-03c", "219–228", "1840年12月", "1845–1849",
            "脚注末尾增添句号", "2015-08-09", "2026-06-02",
            "没有查验首刊影印", "通读该数字页面的小说正文",
            "叙述者，不是作者本人或调查员",
            "不是独立摄影、访谈或交叉验证过的证据",
            "不是唯一学术结论", "刻板描写与贬损判断",
            "非小说情节、实地观察或受访者经历",
            "尾随行为不是行动建议",
        ):
            self.assertIn(phrase, text)
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        note = next(n for n in notes if n["id"] == "F72")
        self.assertEqual(note["source_kind"], "literary_primary_text")
        self.assertEqual(note["text"], text)
        self.assertIn(text, (ROOT / "llms-full.txt").read_text())
        self.assertIn('href="#solo-man-of-crowd"', build.markdown(text, source))

    def test_retrieval_and_no_spoiler_route_are_complete(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {d["id"]: d for d in documents}
        for identifier, path in (
            ("C07", "book/07-solo.md"),
            ("F72", "docs/evidence/F72-man-of-the-crowd.md"),
        ):
            data = (ROOT / path).read_bytes()
            self.assertEqual(by_id[identifier]["text"], data.decode())
            self.assertEqual(by_id[identifier]["source_sha256"], hashlib.sha256(data).hexdigest())
        route = next(r for r in routes if r["id"] == "R72")
        self.assertEqual(set(route["targets"]),
                         {"C07", "F72", "B06", "N06", "F47", "F48", "C15", "E08"})
        text = (ROOT / "docs/reading-map.md").read_text().split('<a id="r72"></a>')[1]
        for identifier in route["targets"]:
            self.assertIn("[" + identifier, text)
        self.assertIn("用户要求无剧透时只讲开头与问题", text)
        self.assertIn("不声称唯一学术解释", text)

    def test_not_an_added_experiment_or_new_card(self):
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(records), 50)
        self.assertNotIn("F72", {r["id"] for r in records})
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("F72" not in c["background_ids"] for c in cards))
        self.assertTrue(all(c["evidence_type"] == "original_proposal" for c in cards))


if __name__ == "__main__":
    unittest.main()
