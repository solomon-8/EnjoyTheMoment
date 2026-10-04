"""Entry routes test publishing integrity, not attention or persuasion."""
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import epub


class EntryArgumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.block = build.entry_arguments(ROOT)
        cls.outputs = build.outputs()

    def test_one_canonical_excerpt_in_reader_and_ai_text(self):
        rendered = build.markdown(self.block, "README.md", heading_offset=0)
        self.assertEqual(self.outputs["index.html"].count(rendered), 1)
        self.assertEqual(self.outputs["llms-full.txt"].count(self.block), 1)
        self.assertNotIn("entry-arguments:start", rendered)
        self.assertNotIn("@@ENTRYARGUMENTS@@", self.outputs["index.html"])
        self.assertEqual(rendered.count("<h2>"), 1)
        self.assertEqual(rendered.count("<h3>"), 5)
        self.assertNotIn("&lt;br", rendered)

    def test_argument_routes_precede_activities_and_work_offline(self):
        page = self.outputs["index.html"]
        self.assertLess(page.index('id="disagreements"'), page.index('id="menu"'))
        excerpt = page.split('id="disagreements"', 1)[1].split("</section>", 1)[0]
        self.assertNotIn("<details", excerpt)
        links = re.findall(r'href="([^"]+)"', excerpt)
        self.assertEqual(links, [
            "#flavor-suiyuan", "#games-paid-skip", "#fear-two-wishes",
            "#rest-paid-evening", "#waiting-reliable-more", "#excitement-costs",
            "#friends-not-a-service", "#e10",
        ])
        for href in links:
            self.assertTrue(href.startswith("#"))
            self.assertEqual(page.count('id="' + href[1:] + '"'), 1)
            self.assertFalse(re.fullmatch(r"#j\d+", href))

    def test_concrete_entrances_are_chapter_arguments_not_activities(self):
        self.assertLess(self.block.index("book/14-flavor.md#flavor-suiyuan"),
                        self.block.index("### "))
        self.assertIn("不必靠“其实不害怕”来解释。\n\n**再往下", self.block)
        for phrase in ("做菜者的反对", "明确标为假想的游戏",
                       "希望人物安全", "两种愿望可以并存"):
            self.assertIn(phrase, self.block)
        for path, anchor, phrase in [
            ("book/14-flavor.md", "flavor-suiyuan", "没有责任表演每一口都惊艳"),
            ("book/19-games.md", "games-paid-skip", "被省掉的是我要付出的成本"),
            ("book/31-recreational-fear.md", "fear-two-wishes", "不是同一张订单"),
        ]:
            text = (ROOT / path).read_text()
            self.assertIn('<a id="' + anchor + '"></a>', text)
            self.assertIn(phrase, text)

    def test_short_introductions_keep_real_counterweights(self):
        for phrase in ("每个周末的累计代价", "必要支出", "谁还在",
                       "一个假想让我们选择", "选择现在仍然少得两晚",
                       "正文不抹去这笔代价", "为什么非得二选一，不能重新安排",
                       "也可能让等待胜出", "不让别人被迫代付",
                       "不能拿友情取消拒绝", "不授予旁人接管权",
                       "主动设限也可能有用", "不能把一切挽留都说成操控"):
            self.assertIn(phrase, self.block)
        self.assertNotIn("更吸引", self.block)
        self.assertNotIn("超越", self.block)

    def test_manifesto_keeps_distinct_claims_and_existing_anchors(self):
        text = (ROOT / "SHUAQI.md").read_text()
        for phrase in ("即时满足、感官快乐、新鲜感、投入与热烈",
                       "即使等待可靠、后来确实能得到更多",
                       "我们愿意少得到什么", "不是今天自动获胜",
                       "不是所有人都赞许你的品味",
                       "如果不追加他人时间就无法继续",
                       "也不对医学风险作统一折算",
                       "一次小快乐不应被拿来结清",
                       "不必责怪自己或替失约的安排开脱",
                       "不是社会调查结果"):
            self.assertIn(phrase, text)
        for anchor in ("shuaqi-position", "shuaqi-costs",
                       "shuaqi-objections", "shuaqi-reading",
                       "今天怎么耍", "不把耍起变成新的压力"):
            self.assertEqual(text.count('<a id="' + anchor + '"></a>'), 1)
        readme = (ROOT / "README.md").read_text()
        for old_heading in ("“耍起”，是我们的核心，不只是封面上的梗", "我们站在哪一边"):
            self.assertEqual(readme.count('<a id="' + epub.heading_slug(old_heading) + '"></a>'), 1)

    def test_original_research_and_cards_are_not_recast_as_validation(self):
        for path in ("SHUAQI.md", "essays/07-rest-is-not-work.md",
                     "essays/04-buying-pleasure.md", "essays/02-excitement-without-escalation.md",
                     "essays/10-pleasure-not-retention.md"):
            self.assertIn((ROOT / path).read_text(), self.outputs["llms-full.txt"])

    def test_excerpt_contributes_to_digest(self):
        baseline = build.source_digest(ROOT)
        with mock.patch.object(build, "entry_arguments", return_value=self.block + "\n\n另一种表述。"):
            self.assertNotEqual(build.source_digest(ROOT), baseline)

    def test_missing_duplicate_reversed_or_empty_markers_fail(self):
        start, end = "<!-- entry-arguments:start -->", "<!-- entry-arguments:end -->"
        valid = start + "\n" + self.block + "\n" + end
        for text in ("", start + self.block, valid + valid, end + self.block + start,
                     start + "\n\n" + end):
            with self.subTest(text=text[:40]), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "README.md").write_text(text)
                with self.assertRaises(ValueError):
                    build.entry_arguments(root)


if __name__ == "__main__":
    unittest.main()
