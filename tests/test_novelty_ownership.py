"""Reading-path guards; not an assessment of persuasiveness or popularity."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import check
import read


class NoveltyOwnershipTests(unittest.TestCase):
    def test_old_title_link_survives_and_moved_questions_keep_their_context(self):
        source = "book/03-novelty.md"
        text = (ROOT / source).read_text()
        self.assertIn('# 03 · 已经玩过，就不值得再来吗？', text)
        self.assertIn('<a id="03--给日常制造一点意外"></a>', text)
        for parent, child, next_section in (
            ("novelty-uncertainty", "novelty-surprise", "novelty-learning"),
            ("novelty-learning", "novelty-depth", "novelty-repeat"),
        ):
            self.assertLess(text.index(f'id="{parent}"'), text.index(f'id="{child}"'))
            self.assertLess(text.index(f'id="{child}"'), text.index(f'id="{next_section}"'))
            child_text = text.split(f'<a id="{child}"></a>', 1)[1].lstrip()
            self.assertTrue(child_text.startswith("#### "))
        html = build.markdown(text, source)
        for anchor in ("03--给日常制造一点意外", "novelty-surprise", "novelty-depth"):
            self.assertEqual(html.count(f'id="{anchor}"'), 1)

    def test_cross_chapter_links_point_to_the_argument_not_the_activity_cards(self):
        chapter = (ROOT / "book/03-novelty.md").read_text()
        essay = (ROOT / "essays/02-excitement-without-escalation.md").read_text()
        intensity = chapter.split('<a id="novelty-intensity"></a>', 1)[1].split("\n### ", 2)[1]
        for anchor in ("excitement-costs", "excitement-information"):
            self.assertIn(f"02-excitement-without-escalation.md#{anchor}", intensity)
            self.assertIn(f'href="#{anchor}"',
                          build.markdown(intensity, "book/03-novelty.md"))
        scoreboard = essay.split('<a id="excitement-scoreboard"></a>', 1)[1]
        scoreboard = scoreboard.split('<a id="excitement-continue"></a>', 1)[0]
        self.assertIn("03-novelty.md#novelty-repeat", scoreboard)
        self.assertNotRegex(scoreboard, r"\]\([^)]*#j\d")
        self.assertIn("不必先找到新细节", scoreboard)
        self.assertIn("已经不喜欢，也不必强迫重复", scoreboard)
        self.assertIn("把从未经历过当成价值门槛", chapter)
        self.assertNotIn("如果新鲜必须等于从没经历过", chapter)

    def test_four_arguments_and_practice_are_not_one_flat_list(self):
        text = (ROOT / "book/03-novelty.md").read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M), [
            "一、新鲜究竟换了什么？",
            "二、未知怎样成为乐趣，而不是只剩困惑？",
            "三、重来一次，还要重新证明值得吗？",
            "四、愿望不必按新旧排队",
            "配套：试一种变化，不是完成体验指标",
        ])
        default = text.split('<a id="novelty-default"></a>', 1)[1].split(
            '<a id="novelty-wishes"></a>', 1)[0]
        for phrase in ("原创假想，不是饮食建议", "小满", "最后甚至还是点了原来那道",
                       "自主可以包括让一个愿意保留的决定继续有效",
                       "不把“曾经选过”当无限期许可",
                       "不等于所有人都必须把发现最好吃的东西当作每顿饭的任务",
                       "本书不给“每周换几次”的配额"):
            self.assertIn(phrase, default)
        self.assertNotIn("<!-- pick:", default)
        for anchor in ("novelty-default", "novelty-reselection",
                       "novelty-default-objection", "novelty-practice"):
            self.assertEqual(build.markdown(text, "book/03-novelty.md").count(
                'id="' + anchor + '"'), 1)

    def test_default_argument_is_not_attributed_to_repeat_experiment(self):
        _, routes = read.load_documents(ROOT)
        route = next(item for item in routes if item["id"] == "R69")
        for phrase in ("原创小满情境", "没有测定决策疲劳", "最佳探索频率"):
            self.assertIn(phrase, route["text"])
        for anchor in ("novelty-change", "novelty-understanding", "novelty-return",
                       "novelty-wishes", "novelty-default", "novelty-reselection"):
            self.assertIn("#" + anchor, route["text"])
        for filename, key in (("data/evidence.json", "notes"),
                              ("data/research.json", "records")):
            for item in json.loads((ROOT / filename).read_text())[key]:
                self.assertNotIn("每天吃一样，是省掉麻烦", item.get("text", ""))

    def test_complete_retrieval_and_route_separate_the_two_arguments(self):
        docs, routes = read.load_documents(ROOT)
        by_id = {doc["id"]: doc for doc in docs}
        full_text = (ROOT / "llms-full.txt").read_text()
        for identifier, source in (
            ("C03", "book/03-novelty.md"),
            ("E02", "essays/02-excitement-without-escalation.md"),
        ):
            raw = (ROOT / source).read_bytes()
            self.assertEqual(by_id[identifier]["text"], raw.decode())
            self.assertEqual(by_id[identifier]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            # Chapters with cards are exported as prose followed by a separate
            # card collection. Exact read-by-ID still returns the whole file.
            prose = raw.decode().split('<a id="j013"></a>', 1)[0].strip()
            self.assertTrue(prose in full_text, f"{identifier} prose missing from AI export")
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        for card in cards:
            if card["id"] in {f"J{i:03d}" for i in range(13, 19)}:
                self.assertTrue(card["body"] in full_text,
                                f"{card['id']} body missing from AI export")
        route = next(route for route in routes if route["id"] == "R08")
        self.assertEqual(set(route["targets"]), {"C03", "F49", "B03", "N03", "E02"})
        for anchor in ("novelty-surprise", "novelty-depth", "excitement-costs"):
            self.assertIn("#" + anchor, route["text"])
        self.assertIn("丰富性≠积极情绪", route["text"])
        chapters = json.loads((ROOT / "data/chapters.json").read_text())["chapters"]
        chapter = next(chapter for chapter in chapters if chapter["id"] == "C03")
        self.assertEqual(chapter["title"], "03 · 已经玩过，就不值得再来吗？")
        self.assertEqual(chapter["card_ids"], [f"J{i:03d}" for i in range(13, 19)])

    def test_epub_retains_headings_and_resolves_both_reading_directions(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            for source, entry in (
                ("book/03-novelty.md", "book--03-novelty.xhtml"),
                ("essays/02-excitement-without-escalation.md",
                 "essays--02-excitement-without-escalation.xhtml"),
            ):
                text = (ROOT / source).read_text()
                xml = ET.fromstring(archive.read("EPUB/text/" + entry))
                ids = [element.attrib["id"] for element in xml.iter()
                       if "id" in element.attrib]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertTrue(check.anchors_for(text).issubset(set(ids)))
                rendered = "".join(xml.itertext())
                for heading in re.findall(r"^#{1,4} (.+)$", text, re.M):
                    self.assertIn(heading, rendered)
                hrefs = [element.attrib["href"] for element in xml.iter()
                         if "href" in element.attrib]
                required = (
                    ["essays--02-excitement-without-escalation.xhtml#excitement-costs",
                     "essays--02-excitement-without-escalation.xhtml#excitement-information"]
                    if source.startswith("book/") else
                    ["book--03-novelty.xhtml#novelty-repeat"]
                )
                for href in required:
                    self.assertIn(href, hrefs)


if __name__ == "__main__":
    unittest.main()
