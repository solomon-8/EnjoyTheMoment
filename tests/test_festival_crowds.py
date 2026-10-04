"""Preserve close reading, invented scenes and source limits across formats."""
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


class FestivalCrowdsTests(unittest.TestCase):
    def test_argument_has_an_event_not_just_an_activity_to_reschedule(self):
        text = (ROOT / "book/18-celebration.md").read_text()
        for phrase in (
            "为什么偏要在大家都出门的那天出门",
            "此刻还有谁也在做",
            "虚构的年末聚会", "阿禾", "小乔",
            "不是一次调查归纳出的游客画像",
            "前面被分开的第三类与第五类",
            "不是永远没有人的西湖",
            "变化的是文本怎样分配视线、声音与篇幅",
            "不据此编造一份劳动史",
            "可支配条件包装成性格优点",
            "不必通过一次动机审查才准出门",
            "可替代的安排，不一定是等价的生活",
            "我知道平时也能吃这顿饭，但我想要的是今晚",
        ):
            self.assertIn(phrase, text)
        html = build.markdown(text, "book/18-celebration.md")
        for anchor in (
            "celebration-top", "celebration-calendar",
            "celebration-repetition", "celebration-same-night",
            "celebration-west-lake", "celebration-after-crowd",
            "celebration-crowd-objection", "celebration-magi",
            "celebration-generosity", "celebration-objection",
        ):
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
        self.assertEqual(html.count("<details>"), 1)
        self.assertIn("展开完整情节与结尾讨论", html)
        self.assertIn('href="#f81"', html)
        self.assertIn('href="#f45"', html)
        self.assertIn('href="#n08"', html)
        self.assertNotIn("<!-- pick:", text)

    def test_five_groups_and_later_gathering_are_not_a_survey(self):
        path = "docs/evidence/F81-west-lake-festival.md"
        text = (ROOT / path).read_text()
        for phrase in (
            "2026-10-02", "2327158", "2703674", "2703798",
            "2023-10-27", "未提供版本信息的页面",
            "没有通读卷七其他篇目",
            "不算两份独立历史见证",
            "“簫鼓”", "“蕭鼓”", "谁说话、谁害怕",
            "正文不采用这句的争议归属",
            "没有抽样、访谈、人数比例或分类可靠性",
            "前者并非完全不看景，后者并非独自一人",
            "结尾并不是“所有人散光，叙述者终于独自看月”",
            "不能替他宣布人与人之间已经一律平等",
            "没有报酬、同意、休息或劳动安排的完整记录",
            "不是古文情节、真实读者来信或实验案例",
            "不改写成中秋节",
            "不是今天的饮酒、夜航或人群安全建议",
            "不新增B系列研究",
        ):
            self.assertIn(phrase, text)
        labels = [line.split("|")[1].strip() for line in text.splitlines()
                  if line.startswith("| 第")]
        self.assertEqual(labels, ["第一类", "第二类", "第三类", "第四类", "第五类"])
        rendered = build.markdown(text, path, omit_title=True)
        self.assertIn('href="#celebration-west-lake"', rendered)
        self.assertEqual(rendered.count("<table>"), 1)
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        self.assertEqual(len(notes), 144)
        note = next(n for n in notes if n["id"] == "F81")
        self.assertEqual(note["source_kind"], "literary_primary_text")
        self.assertEqual(note["text"], text)
        research = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual({r["id"] for r in research}, {
            f"B{i:02d}" for i in range(1, 51)
        })
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("F81" not in c["background_ids"] for c in cards))

    def test_full_sources_and_route_remain_available(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {d["id"]: d for d in documents}
        for identifier, path in (
            ("C18", "book/18-celebration.md"),
            ("F81", "docs/evidence/F81-west-lake-festival.md"),
        ):
            raw = (ROOT / path).read_bytes()
            self.assertEqual(by_id[identifier]["text"], raw.decode())
            self.assertEqual(by_id[identifier]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertEqual((ROOT / "llms-full.txt").read_text().count(
                raw.decode().strip()), 1)
        route = next(r for r in routes if r["id"] == "R17")
        self.assertEqual(set(route["targets"]), {
            "C18", "F44", "F45", "F81", "B08", "N08", "C05", "C08", "E08", "C21",
        })
        self.assertTrue(set(route["targets"]) <= {
            r["id"] for r in read.linked_records(route, documents, ROOT)
        })

    def test_epub_keeps_new_argument_and_old_spoiler_text(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            chapter = archive.read("EPUB/text/book--18-celebration.xhtml").decode()
            note = archive.read(
                "EPUB/text/docs--evidence--F81-west-lake-festival.xhtml").decode()
            self.assertIn('id="celebration-same-night"', chapter)
            self.assertIn('id="celebration-after-crowd"', chapter)
            self.assertIn("可替代的安排，不一定是等价的生活", chapter)
            self.assertIn("展开完整情节与结尾讨论", chapter)
            self.assertIn("卖掉了金表来买发梳", chapter)
            self.assertIn("docs--evidence--F81-west-lake-festival.xhtml", chapter)
            self.assertIn("book--18-celebration.xhtml#celebration-west-lake", note)
            self.assertEqual(note.count("<table>"), 1)


if __name__ == "__main__":
    unittest.main()
