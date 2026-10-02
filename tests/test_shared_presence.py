"""Check preservation and retrieval of distinctions, not audience persuasion."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read


class SharedPresenceTests(unittest.TestCase):
    def test_scenario_separates_presence_response_choice_and_performance(self):
        source = "book/13-live-events.md"
        text = (ROOT / source).read_text()
        for phrase in (
            "所有情节和安排都是本书原创假想",
            "不对应实际作品，也不是观众研究",
            "在场，不等于答应被点名",
            "四行没有从低到高排列",
            "观众不是必须升级成演员的初级身份",
            "红信三票、蓝信两票",
            "如果票数相反，顺序就相反",
            "再假定红信是辩解、蓝信是指责",
            "本例没有测出某种必然效果",
            "有限的选择可以是真选择",
            "不等于他的票没算",
            "五个人分别指定五首不同的歌",
            "不必被劝成“安静欣赏也一样”",
            "我愿意把这一段交给别人，不等于把自己的生活交出去",
            "不是某种票务法律规则",
        ):
            self.assertIn(phrase, text)
        html = build.markdown(text, source)
        for anchor in (
            "live-medium", "live-participation", "live-choice",
            "live-control-objection", "live-space", "live-convention",
            "live-anticipation", "live-understanding",
        ):
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
            self.assertIn(f'href="#{anchor}"', html)
        section = text.split('id="live-participation"', 1)[1].split(
            '<a id="live-choice"', 1)[0]
        rows = [line for line in section.splitlines() if line.startswith("|")]
        self.assertEqual(len(rows), 6)  # heading, separator and four arrangements
        self.assertNotIn("<!-- pick:", text)

    def test_cross_chapter_routes_keep_complete_arguments_and_limits(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {d["id"]: d for d in documents}
        expected = {
            "R14": {"C13", "F40", "F41", "C05", "E08", "E11", "C18", "C34"},
            "R17": {"C18", "F44", "F45", "F81", "B08", "N08",
                    "C05", "C08", "E08", "C21"},
        }
        for route_id, targets in expected.items():
            route = next(r for r in routes if r["id"] == route_id)
            self.assertEqual(set(route["targets"]), targets)
            self.assertTrue(targets <= {
                d["id"] for d in read.linked_records(route, documents, ROOT)
            })
        self.assertIn("少数票未胜不等于没被计入", by_id["R14"]["text"])
        self.assertIn("不是票务法律意见", by_id["R14"]["text"])
        for identifier, path in (
            ("C13", "book/13-live-events.md"),
            ("C18", "book/18-celebration.md"),
        ):
            raw = (ROOT / path).read_bytes()
            self.assertEqual(by_id[identifier]["scope"], "full_file")
            self.assertEqual(by_id[identifier]["text"], raw.decode())
            self.assertEqual(by_id[identifier]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertEqual((ROOT / "llms-full.txt").read_text().count(
                raw.decode().strip()), 1)

    def test_trimmed_celebration_keeps_literature_tradeoff_and_old_links(self):
        text = (ROOT / "book/18-celebration.md").read_text()
        for phrase in (
            "虚构的年末聚会", "此刻还有谁也在做",
            "不由这桌人另选日期",
            "不是一次调查归纳出的游客画像",
            "前面被分开的第三类与第五类",
            "不据此编造一份劳动史",
            "不必通过一次动机审查才准出门",
            "可替代的安排，不一定是等价的生活",
            "不是人群安全或延长营业的建议",
            "展开完整情节与结尾讨论",
        ):
            self.assertIn(phrase, text)
        self.assertIn("05-connection.md#connection-shared-attention", text)
        self.assertIn("21-free-time.md#time-common", text)
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        research = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(notes), 123)
        self.assertEqual(len(research), 41)
        by_id = {n["id"]: n for n in notes}
        self.assertEqual(by_id["F81"]["source_kind"], "literary_primary_text")
        self.assertEqual(by_id["F40"]["source_kind"], "theatre_educational_reference")
        self.assertEqual(by_id["F41"]["source_kind"], "heritage_description_and_nomination")

    def test_epub_contains_argument_table_objection_and_cross_chapter_links(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            live = archive.read("EPUB/text/book--13-live-events.xhtml").decode()
            celebration = archive.read("EPUB/text/book--18-celebration.xhtml").decode()
            self.assertEqual(live.count("<table>"), 3)
            for anchor in ("live-participation", "live-choice",
                           "live-control-objection"):
                self.assertIn(f'id="{anchor}"', live)
            self.assertIn("红信三票、蓝信两票", live)
            self.assertIn("我愿意把这一段交给别人", live)
            self.assertIn("essays--11-pleasure-and-reality.xhtml#pleasure-promises", live)
            self.assertIn("book--34-shared-stories.xhtml#story-choice", live)
            self.assertIn("book--18-celebration.xhtml#celebration-same-night", live)
            self.assertIn("book--05-connection.xhtml#connection-shared-attention", celebration)
            self.assertIn("docs--evidence--F81-west-lake-festival.xhtml", celebration)
            self.assertIn("卖掉了金表来买发梳", celebration)


if __name__ == "__main__":
    unittest.main()
