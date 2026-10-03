"""Retrieval and source-scope contracts; not proof of comprehension or persuasion."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read


class TimeChoiceTests(unittest.TestCase):
    def test_argument_separates_timing_reasons_and_plan_changes(self):
        source = "essays/03-now-or-later.md"
        text = (ROOT / source).read_text()
        for phrase in (
            "选择现在，不等于给耐心交了一张不及格答卷",
            "不该草率骂她短视，与她一定选对，是两回事",
            "条件变了", "目标变了", "目标仍在",
            "事后懊悔也可能来自别人施压",
            "及时享乐不等于及时省事",
            "防住一种反悔，不等于防住所有选错",
            "改善入口不等于锁住出口",
            "不预设小说比短视频高级",
            "特定模型的可能结果",
            "不能让28个孩子替我们投票",
            "小份只是另一种可选经历",
        ):
            self.assertIn(phrase, text)
        self.assertNotIn("<!-- pick:", text)
        rendered = build.markdown(text, source)
        # Waiting reasons are prose; only the dated preference-reversal comparison is tabular.
        self.assertEqual(rendered.count("<table>"), 1)
        self.assertIn('href="#f75"', rendered)
        self.assertIn('href="#digital-limit-authority"', rendered)

    def test_hypothetical_timeline_is_attributed_and_not_a_longitudinal_result(self):
        text = (ROOT / "essays/03-now-or-later.md").read_text()
        for phrase in (
            "假想答卷", "A还要等30天，B还要等31天",
            "A今天可得，B明天可得", "表格按综述所举的比较结构改写",
            "脚注14", "不是同一种证据", "不能把前者讲成已观察到后者",
        ):
            self.assertIn(phrase, text)
        dates = (30, 31)
        self.assertEqual(tuple(date - 30 for date in dates), (0, 1))
        self.assertEqual(dates[1] - dates[0], 1)

    def test_old_and_new_anchors_survive_generated_readers(self):
        text = (ROOT / "essays/03-now-or-later.md").read_text()
        rendered = build.markdown(text, "essays/03-now-or-later.md")
        online = (ROOT / "index.html").read_text()
        for anchor in (
            "waiting-credible-promise", "waiting-marshmallow",
            "waiting-different-goods", "waiting-long-term-defense",
            "waiting-future-self", "waiting-ordinary-window",
            "一个不装精确的决定办法", "三个虚构例子",
            "waiting-not-a-patience-score", "waiting-reversal",
            "waiting-plan-revision", "waiting-pleasure-procrastination",
            "waiting-commitment-objection",
        ):
            with self.subTest(anchor=anchor):
                marker = 'id="' + anchor + '"'
                self.assertEqual(rendered.count(marker), 1)
                self.assertEqual(online.count(marker), 1)

    def test_review_is_scoped_and_does_not_invent_a_new_effect_study(self):
        source = "docs/evidence/F75-time-choice-and-discounting.md"
        text = (ROOT / source).read_text()
        for phrase in (
            "2002年6月", "351–401", "51页", "10.1257/jel.40.2.351",
            "登录／购买入口的HTML", "没有可直接抽取的文字层",
            "脚注14", "synchronic", "diachronic", "平稳折扣假设",
            "没有通读51页", "底层实验", "不宣称首创",
            "模型参数", "不是量表", "不验证任何J卡",
        ):
            self.assertIn(phrase, text)
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        record = next(n for n in notes if n["id"] == "F75")
        self.assertEqual(record["text"], text)
        self.assertEqual(record["source_kind"], "economic_review_concepts_models_and_methods")
        research = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(research), 47)
        self.assertNotIn("F75", {r["id"] for r in research})
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("F75" not in c["background_ids"] for c in cards))

    def test_full_text_and_route_keep_the_same_sources_and_limits(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {r["id"]: r for r in documents}
        full_text = (ROOT / "llms-full.txt").read_text()
        for identifier, source in (
            ("E03", "essays/03-now-or-later.md"),
            ("F75", "docs/evidence/F75-time-choice-and-discounting.md"),
        ):
            text = (ROOT / source).read_text()
            self.assertEqual(by_id[identifier]["text"], text)
            self.assertEqual(by_id[identifier]["source_sha256"],
                             hashlib.sha256((ROOT / source).read_bytes()).hexdigest())
            self.assertIn(text, full_text)
        route = next(r for r in routes if r["id"] == "R74")
        self.assertEqual(set(route["targets"]), {"E03", "F75", "E01", "E10", "C01", "B23", "N23"})
        for phrase in ("不是同一证据", "假想答卷而非纵向数据", "不根据单次行为诊断失控",
                       "小份不是总答案", "未独立核验底层实验"):
            self.assertIn(phrase, route["text"])
        rendered = build.markdown(by_id["F75"]["text"], by_id["F75"]["source"])
        for anchor in ("waiting-not-a-patience-score", "waiting-reversal",
                       "waiting-pleasure-procrastination", "waiting-commitment-objection"):
            self.assertIn('href="#' + anchor + '"', rendered)
