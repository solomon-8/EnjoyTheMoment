import contextlib
import hashlib
import io
import itertools
import json
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest import mock
from pathlib import Path
from fractions import Fraction

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import pick


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = build.outputs()
        cls.export = json.loads(cls.outputs["data/catalog.json"])

    def json_call(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = pick.main(list(args) + ["--json"])
        self.assertEqual(code, 0)
        return json.loads(output.getvalue())

    def test_generated_files_are_fresh(self):
        for path, content in self.outputs.items():
            self.assertEqual((ROOT / path).read_text(encoding="utf-8"), content, path)

    def test_json_is_bounded_and_deterministic(self):
        first = self.json_call("--query", "游戏", "--minutes", "60", "--limit", "2")
        self.assertEqual(first, self.json_call("--query", "游戏", "--minutes", "60", "--limit", "2"))
        self.assertLessEqual(len(first["cards"]), 2)
        self.assertGreaterEqual(first["total_matches"], len(first["cards"]))

    def test_exact_id_bypasses_filters_explicitly(self):
        result = self.json_call("--id", "j019", "--minutes", "0", "--budget", "0")
        self.assertEqual(result["scope"], "exact_id")
        self.assertEqual(result["cards"][0]["id"], "J019")

    def test_unknown_id_is_empty_json(self):
        result = self.json_call("--id", "J99999")
        self.assertEqual(result["total_matches"], 0)
        self.assertEqual(result["cards"], [])

    def test_json_fields_preserve_conditions(self):
        result = self.json_call("--id", "J019")["cards"][0]
        self.assertEqual(set(result["fields"]), set(pick.FIELDS))
        self.assertIn("原创试做", result["fields"]["性质"])
        self.assertIn("散场线", result["fields"])
        self.assertEqual(result["currency"], "CNY")
        self.assertEqual(result["evidence_type"], "original_proposal")

    def test_schema_required_fields_and_hashes(self):
        schema = json.loads((ROOT / "data/catalog.schema.json").read_text())
        self.assertEqual(set(self.export), set(schema["required"]))
        required = set(schema["$defs"]["card"]["required"])
        for card in self.export["cards"]:
            self.assertEqual(set(card), required)
            source = ROOT / card["source"].split("#")[0]
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), card["source_sha256"])

    def test_today_argument_and_research_stay_distinct_from_cards(self):
        records = {item["id"]: item for item in json.loads(self.outputs["data/research.json"])["records"]}
        record = records["B17"]
        self.assertEqual(record["doi"], "10.1509/jmkr.47.5.933")
        self.assertEqual(record["verified_at"], "2026-09-30")
        self.assertEqual(record["access_level"], "full_text")
        self.assertFalse(record["directly_validates_cards"])
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        note = notes["N17"]
        self.assertEqual(note["source_kind"], "study_reading_note")
        self.assertEqual(note["text"], (ROOT / "docs/evidence/B17-enjoyable-procrastination.md").read_text())
        for phrase in ("10 / 32", "2 / 32", "59 / 120", "42 / 120", "33", "175", "p = .10", "4.64", "并不完美", "原始数据"):
            self.assertIn(phrase, note["text"])
        self.assertIn(note["text"], self.outputs["llms-full.txt"])
        self.assertTrue(all("B17" not in card["background_ids"] for card in self.export["cards"]))
        chapter = next(item for item in json.loads(self.outputs["data/chapters.json"])["chapters"] if item["id"] == "C01")
        for anchor in ("today-priority", "today-use", "today-voucher", "today-future", "today-not-redemption"):
            self.assertIn('id="' + anchor + '"', chapter["text"])
            self.assertEqual(self.outputs["index.html"].count('id="' + anchor + '"'), 1)
        self.assertIn("兑换比例", chapter["text"])
        self.assertIn("不等于让生活过得更好", chapter["text"])
        self.assertIn('href="#n17"', self.outputs["index.html"])
        self.assertEqual(build.local_href("../../book/01-start-now.md#today-voucher", note["source"]), "#today-voucher")
        for path in ("docs/reading-map.md",):
            self.assertIn("C01/B17/N17", (ROOT / path).read_text())
        self.assertNotIn("二十六份", (ROOT / "docs/research.md").read_text())

    def test_aftertaste_distinguishes_preference_experience_and_memory(self):
        records = {item["id"]: item for item in json.loads(self.outputs["data/research.json"])["records"]}
        record = records["B18"]
        self.assertEqual(record["doi"], "10.1080/17439760.2018.1460688")
        self.assertEqual(record["verified_at"], "2026-09-30")
        self.assertEqual(record["access_level"], "full_text")
        self.assertFalse(record["directly_validates_cards"])
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        note = notes["N18"]
        self.assertEqual(note["source_kind"], "study_reading_note")
        self.assertEqual(note["text"], (ROOT / "docs/evidence/B18-experience-and-memory.md").read_text())
        for phrase in ("2018年4月5日", "2019年3月4日", "225 / 284", "140 / 285", "196 / 290", "37 / 62", "47 / 61", "强制", "组间", "p = .51", "p = 49", "民族性格", "不擅自"):
            self.assertIn(phrase, note["text"])
        self.assertIn(note["text"], self.outputs["llms-full.txt"])
        self.assertTrue(all("B18" not in card["background_ids"] for card in self.export["cards"]))
        chapter = next(item for item in json.loads(self.outputs["data/chapters.json"])["chapters"] if item["id"] == "C10")
        for anchor in ("aftertaste-three-questions", "aftertaste-preference", "aftertaste-story", "aftertaste-memory"):
            self.assertIn('id="' + anchor + '"', chapter["text"])
            self.assertEqual(self.outputs["index.html"].count('id="' + anchor + '"'), 1)
        self.assertIn("回忆不是当下的敌人", chapter["text"])
        self.assertIn("未来值得拥有回忆，今天的人也值得被善待", chapter["text"])
        self.assertIn('href="#n18"', self.outputs["index.html"])
        self.assertEqual(build.local_href("../../book/10-aftertaste.md#aftertaste-preference", note["source"]), "#aftertaste-preference")
        for path in ("docs/reading-map.md",):
            self.assertIn("C10/B18/N18", (ROOT / path).read_text())

    def test_senses_separates_stated_price_context_and_value(self):
        records = {item["id"]: item for item in json.loads(self.outputs["data/research.json"])["records"]}
        record = records["B19"]
        self.assertEqual(record["doi"], "10.1073/pnas.0706929105")
        self.assertEqual(record["verified_at"], "2026-09-30")
        self.assertEqual(record["access_level"], "full_text")
        self.assertFalse(record["directly_validates_cards"])
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        note = notes["N19"]
        self.assertEqual(note["source_kind"], "study_reading_note")
        self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
        for phrase in ("20人", "96次", "告知价格", "未读SI", "800%", "88.9%", "p < 0.000", "不擅自", "迎合", "长期"):
            self.assertIn(phrase, note["text"])
        self.assertIn(note["text"], self.outputs["llms-full.txt"])
        self.assertTrue(all("B19" not in card["background_ids"] for card in self.export["cards"]))
        chapter = next(item for item in json.loads(self.outputs["data/chapters.json"])["chapters"] if item["id"] == "C02")
        for anchor in ("senses-three-layers", "senses-price-expectation", "senses-blind-test", "senses-intensity"):
            self.assertIn('id="' + anchor + '"', chapter["text"])
            self.assertEqual(self.outputs["index.html"].count('id="' + anchor + '"'), 1)
        for phrase in ("身体还是生活发生的地方", "被欺骗也不必被原谅", "不是为了把欲望说小"):
            self.assertIn(phrase, chapter["text"])
        self.assertIn('href="#n19"', self.outputs["index.html"])
        self.assertIn('<p>回到<a href="#senses-price-expectation">身体与感官：价格、喜欢及选择</a>。</p>', self.outputs["index.html"])
        self.assertEqual(build.local_href("../../book/02-senses.md#senses-price-expectation", note["source"]), "#senses-price-expectation")
        for path in ("docs/reading-map.md",):
            self.assertIn("C02/B19/N19", (ROOT / path).read_text())

    def test_spending_distinguishes_sunk_cost_use_and_pleasure(self):
        records = {item["id"]: item for item in json.loads(self.outputs["data/research.json"])["records"]}
        record = records["B20"]
        self.assertEqual(record["doi"], "10.1016/0749-5978(85)90049-4")
        self.assertEqual(record["verified_at"], "2026-09-30")
        self.assertEqual(record["access_level"], "full_text")
        self.assertFalse(record["directly_validates_cards"])
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        note = notes["N20"]
        self.assertEqual(note["source_kind"], "study_reading_note")
        self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
        for phrase in ("第三方", "54人", "15、13、8美元", "4.11", "3.32", "3.29", "1.84", "单尾", "交互", "来宾", "去掉2人", "课程经历不是随机分配"):
            self.assertIn(phrase, note["text"])
        self.assertIn(note["text"], self.outputs["llms-full.txt"])
        self.assertTrue(all("B20" not in card["background_ids"] for card in self.export["cards"]))
        chapter = next(item for item in json.loads(self.outputs["data/chapters.json"])["chapters"] if item["id"] == "C06")
        for anchor in ("spending-pass-arithmetic", "spending-theatre-study", "spending-future-cost", "spending-admission"):
            self.assertIn('id="' + anchor + '"', chapter["text"])
            self.assertEqual(self.outputs["index.html"].count('id="' + anchor + '"'), 1)
        for phrase in ("钱买来的应该是你想过的生活", "平均值变好看，不等于钱回到口袋", "承认没那么喜欢，不该成为享乐者的败诉"):
            self.assertIn(phrase, chapter["text"])
        self.assertIn('href="#n20"', self.outputs["index.html"])
        self.assertIn('href="https://doi.org/10.1016/0749-5978%2885%2990049-4"', self.outputs["index.html"])
        self.assertNotIn('href="https://doi.org/10.1016/0749-5978(85"', self.outputs["index.html"])
        self.assertIn('<p>回到<a href="#spending-theatre-study">第6章：季票研究与剩下的晚上</a>。</p>', self.outputs["index.html"])
        for path in ("docs/reading-map.md",):
            self.assertIn("C06/B20/N20", (ROOT / path).read_text())

    def test_spending_pass_arithmetic_keeps_total_and_average_distinct(self):
        text = (ROOT / "book/06-spending.md").read_text()
        price, single, trip = 240, 40, 12
        for count in (3, 6, 10):
            self.assertIn(f"| {count}次 | {price + trip * count}元 | {(single + trip) * count}元 |", text)
        self.assertEqual(price / single, 6)
        for count, card_average, total_average in ((3, 80, 92), (4, 60, 72)):
            self.assertEqual(price / count, card_average)
            self.assertEqual((price + trip * count) / count, total_average)
            self.assertIn(str(card_average) + "元", text)
            self.assertIn(str(total_average) + "元", text)
        self.assertEqual((price + trip * 4) - (price + trip * 3), 12)
        for phrase in ("不对应任何实际商家", "没有其他费用", "用了第四次，之后就少一次可用", "不可退款"):
            self.assertIn(phrase, text)

    def test_shared_experience_sources_preserve_design_and_limits(self):
        records = {item["id"]: item for item in json.loads(self.outputs["data/research.json"])["records"]}
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        for bid, nid, doi in (
            ("B21", "N21", "10.1177/0956797614551162"),
            ("B22", "N22", "10.1177/0146167216662869"),
        ):
            self.assertEqual(records[bid]["doi"], doi)
            self.assertEqual(records[bid]["verified_at"], "2026-09-30")
            self.assertEqual(records[bid]["access_level"], "full_text")
            self.assertFalse(records[bid]["directly_validates_cards"])
            note = notes[nid]
            self.assertEqual(note["source_kind"], "study_reading_note")
            self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
            self.assertIn(note["text"], self.outputs["llms-full.txt"])
            self.assertTrue(all(bid not in card["background_ids"] for card in self.export["cards"]))
            self.assertIn('href="#' + nid.lower() + '"', self.outputs["index.html"])
        for phrase in ("没有独处组", "23名", "22名", "7.00", "5.46", "2.45", "3.16",
                       "p=.14", "p=.09", "助手在共同条件里实际吃的是较愉快的巧克力", "没有对品尝评价产生中介效应"):
            self.assertIn(phrase, notes["N21"]["text"])
        for phrase in ("44名", "另招21人", "40名", "p=.330", "p=.243", "p=.261",
                       "p=.127", "p=.064", "复合指标", "同一随机分配流程", "不是独立团队确认", "未明确说明空间条件的随机分配程序"):
            self.assertIn(phrase, notes["N22"]["text"])

    def test_connection_chapter_keeps_argument_and_deep_links(self):
        chapter = next(item for item in json.loads(self.outputs["data/chapters.json"])["chapters"] if item["id"] == "C05")
        # Chapter exports contain the full introduction; published action cards stay separate.
        text = (ROOT / "book/05-connection.md").read_text().split('<a id="j025">')[0].strip()
        self.assertIn("不是为了给未来存一笔人情", chapter["text"])
        for anchor in ("connection-shared-attention", "connection-amplification", "connection-distance",
                       "connection-difference", "connection-not-a-tool"):
            self.assertIn('id="' + anchor + '"', chapter["text"])
            self.assertEqual(self.outputs["index.html"].count('id="' + anchor + '"'), 1)
        for phrase in ("两种情况下助手都在场", "注意力是不是中间机制，论文没有证明",
                       "没有视频、语音或聊天", "共同注意和相互考核", "这一晚也可以已经兑现",
                       "不是四档亲密排行榜"):
            self.assertIn(phrase, text)
            self.assertIn(phrase, chapter["text"])
        for path in ("docs/reading-map.md",):
            self.assertIn("C05/B21/B22/N21/N22", (ROOT / path).read_text())
        self.assertIn('href="#connection-amplification"', self.outputs["index.html"])
        self.assertIn('href="#connection-distance"', self.outputs["index.html"])

    def test_waiting_source_keeps_population_censoring_and_version_limits(self):
        records = {item["id"]: item for item in json.loads(self.outputs["data/research.json"])["records"]}
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        record, note = records["B23"], notes["N23"]
        self.assertEqual(record["doi"], "10.1016/j.cognition.2012.08.004")
        self.assertEqual(record["verified_at"], "2026-09-30")
        self.assertEqual(record["access_level"], "full_text")
        self.assertFalse(record["directly_validates_cards"])
        self.assertEqual(note["source_kind"], "study_reading_note")
        self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
        self.assertIn(note["text"], self.outputs["llms-full.txt"])
        self.assertTrue(all("B23" not in card["background_ids"] for card in self.export["cards"]))
        for phrase in ("28名幼儿", "各14名", "181.57", "722.43", "1/14", "9/14",
                       "右截尾", "rank-sum", "signed-rank", "未取得补充材料A.1—A.3",
                       "所有孩子都等完了两次准备阶段", "没有证明自控无关",
                       "第三个随机组", "2012-10-09", "2013年1月"):
            self.assertIn(phrase, note["text"])

    def test_waiting_essay_retains_argument_and_deep_links(self):
        essay = next(item for item in json.loads(self.outputs["data/essays.json"])["essays"] if item["id"] == "E03")
        self.assertEqual(essay["text"], (ROOT / "essays/03-now-or-later.md").read_text())
        for anchor in ("waiting-credible-promise", "waiting-marshmallow", "waiting-different-goods",
                       "waiting-long-term-defense", "waiting-future-self", "waiting-ordinary-window"):
            self.assertIn('id="' + anchor + '"', essay["text"])
            self.assertEqual(self.outputs["index.html"].count('id="' + anchor + '"'), 1)
        for phrase in ("让人等的人，也应当交出理由", "有些好东西，就是快不了",
                       "未来的你有发言权，没有永久否决权", "不能让28个孩子替我们投票",
                       "不必是最后一次，才值得这一次"):
            self.assertIn(phrase, essay["text"])
        self.assertIn('href="#n23"', self.outputs["index.html"])
        self.assertIn('href="#waiting-marshmallow"', self.outputs["index.html"])
        for path in ("docs/reading-map.md",):
            self.assertIn("E03/B23/N23", (ROOT / path).read_text())

    def test_excitement_source_distinguishes_survey_and_threshold(self):
        records = {item["id"]: item for item in json.loads(self.outputs["data/research.json"])["records"]}
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        record, note = records["B24"], notes["N24"]
        self.assertEqual(record["doi"].lower(), "10.1017/s1930297500005295")
        self.assertEqual(record["verified_at"], "2026-09-30")
        self.assertEqual(record["access_level"], "full_text")
        self.assertFalse(record["directly_validates_cards"])
        self.assertEqual(note["source_kind"], "study_reading_note")
        self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
        self.assertIn(note["text"], self.outputs["llms-full.txt"])
        self.assertTrue(all("B24" not in card["background_ids"] for card in self.export["cards"]))
        for phrase in ("本科生243名", "受访者147名", "只有66名", "48—58人",
                       "不熟悉的回答按0处理", ">50", "82%", "56%", "2023-01-01",
                       "2013年7月", "96.3", "thrill seeking", "experience seeking",
                       "没有在现场", "未重算统计", "不是临床诊断"):
            self.assertIn(phrase, note["text"])

    def test_excitement_essay_supports_substantial_experiences_and_old_links(self):
        essay = next(item for item in json.loads(self.outputs["data/essays.json"])["essays"] if item["id"] == "E02")
        self.assertEqual(essay["text"], (ROOT / "essays/02-excitement-without-escalation.md").read_text())
        for anchor in ("excitement-information", "excitement-mixed-feelings", "excitement-study",
                       "excitement-costs", "excitement-scoreboard"):
            self.assertIn('id="' + anchor + '"', essay["text"])
            self.assertEqual(self.outputs["index.html"].count('id="' + anchor + '"'), 1)
        for phrase in ("参与感不按动了多少次手计算", "喜欢作品带来的难过，不等于同意别人真的让你难过",
                       "有些快乐值得占地方，不只值得塞进缝隙", "耍起不该给日历配一个排行榜",
                       "不是刺激剂量实验", "没有实际展示"):
            self.assertIn(phrase, essay["text"])
        self.assertIn('href="#n24"', self.outputs["index.html"])
        self.assertIn('href="#excitement-study"', self.outputs["index.html"])
        for path in ("docs/reading-map.md",):
            self.assertIn("E02/B24/N24", (ROOT / path).read_text())

    def test_rest_essay_retains_value_argument_and_deep_links(self):
        essay = next(item for item in json.loads(self.outputs["data/essays.json"])["essays"]
                     if item["id"] == "E07")
        self.assertEqual(essay["text"], (ROOT / "essays/07-rest-is-not-work.md").read_text())
        self.assertIn(essay["text"], self.outputs["llms-full.txt"])
        for anchor in ("rest-returns", "rest-real-income", "rest-paid-evening",
                       "rest-work-authority", "rest-no-verdict"):
            self.assertIn('id="' + anchor + '"', essay["text"])
            self.assertEqual(self.outputs["index.html"].count('id="' + anchor + '"'), 1)
        for phrase in ("附带收益获得资格", "假设，不是收入调查", "设想一个虚构周六",
                       "自愿安排能否止于本人", "不喜欢这次安排，不等于没有资格拥有这段时间",
                       "不是对任何劳动合同或法定权利作判断", "原创价值论证"):
            self.assertIn(phrase, essay["text"])
        self.assertIn('href="#rest-paid-evening"', self.outputs["index.html"])
        self.assertIn('href="#b05"', self.outputs["index.html"])
        index = (ROOT / "llms.txt").read_text()
        self.assertLess(index.index("essays/07-rest-is-not-work.md"),
                        index.index("## Optional practical companions"))

    def test_friendship_source_and_value_arguments_preserve_scope(self):
        essay = next(item for item in json.loads(self.outputs["data/essays.json"])["essays"]
                     if item["id"] == "E09")
        note = next(item for item in json.loads(self.outputs["data/evidence.json"])["notes"]
                    if item["id"] == "F57")
        self.assertEqual(essay["text"], (ROOT / "essays/09-friends-not-assets.md").read_text())
        self.assertEqual(note["text"], (ROOT / "docs/evidence/F57-friendship-and-reciprocity.md").read_text())
        self.assertEqual(note["source_kind"], "philosophical_primary_translation")
        self.assertIn(essay["text"], self.outputs["llms-full.txt"])
        self.assertIn(note["text"], self.outputs["llms-full.txt"])
        for anchor in ("friends-not-a-service", "friends-aristotle", "friends-reciprocity",
                       "friends-hard-times", "friends-limited", "friends-ending"):
            self.assertIn('id="' + anchor + '"', essay["text"])
            self.assertEqual(self.outputs["index.html"].count('id="' + anchor + '"'), 1)
        for phrase in ("不是对所有职场、城市或年轻人社交方式的统计判断",
                       "设想一个虚构场景", "关系的范围可以有限", "只有自己知道的期待",
                       "不必把辛苦偷偷改名成享受", "不要求先把过去写坏"):
            self.assertIn(phrase, essay["text"])
        for phrase in ("W. D. Ross", "2、3、4、13", "3、12", "没有通读全书",
                       "没有读取希腊文", "不是心理实验", "the must", "现代法律性质"):
            self.assertIn(phrase, note["text"])
        self.assertEqual(build.local_href("../docs/evidence/F57-friendship-and-reciprocity.md",
                                          "essays/09-friends-not-assets.md"), "#f57")
        self.assertIn('href="#friends-reciprocity"', self.outputs["index.html"])
        records = json.loads(self.outputs["data/research.json"])["records"]
        self.assertNotIn("F57", {record["id"] for record in records})
        self.assertTrue(all("F57" not in card["background_ids"] for card in self.export["cards"]))
        for path in ("docs/reading-map.md",):
            self.assertIn("E09/F57", (ROOT / path).read_text())

    def test_constraints_essay_keeps_argument_and_complete_sources(self):
        source = "essays/06-real-life-constraints.md"
        essay = next(item for item in json.loads(self.outputs["data/essays.json"])["essays"]
                     if item["id"] == "E06")
        self.assertEqual(essay["text"], (ROOT / source).read_text())
        self.assertIn(essay["text"], self.outputs["llms-full.txt"])
        for anchor in ("constraints-necessity", "constraints-permission-study",
                       "constraints-standing", "constraints-visible-pleasure",
                       "constraints-help", "constraints-prudence", "constraints-not-all-needs"):
            self.assertIn('id="' + anchor + '"', essay["text"])
            self.assertEqual(self.outputs["index.html"].count('id="' + anchor + '"'), 1)
        # Preservation assertions, not independent measures of persuasion or comprehension.
        for phrase in ("人的享乐资格不应按收入发放", "不能说实验已经排除了全部预算差异",
                       "有差别，不等于大多数人拒绝尊重低收入者",
                       "不要替她编一个感人的免责故事", "不满意就别接受",
                       "没有行动空间，是现实问题", "做一次不购买的决定"):
            self.assertIn(phrase, essay["text"])
        self.assertEqual(build.local_href("../docs/evidence/B26-permissible-consumption.md",
                                          source), "#n26")
        self.assertEqual(build.local_href("../../" + source + "#constraints-permission-study",
                                          "docs/evidence/B26-permissible-consumption.md"),
                         "#constraints-permission-study")
        self.assertIn('"id":"R48"', (ROOT / "docs/reading-map.md").read_text())

    def test_permissible_consumption_retains_exceptions_and_unresolved_reporting(self):
        records = {r["id"]: r for r in json.loads(self.outputs["data/research.json"])["records"]}
        notes = {r["id"]: r for r in json.loads(self.outputs["data/evidence.json"])["notes"]}
        record, note = records["B26"], notes["N26"]
        self.assertEqual(record["doi"], "10.1073/pnas.2005475117")
        self.assertEqual(record["verified_at"], "2026-09-30")
        self.assertEqual(record["access_level"], "full_text")
        self.assertFalse(record["directly_validates_cards"])
        self.assertEqual(note["source_kind"], "study_reading_note")
        self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
        for phrase in ("不是11篇独立论文", "不是PDF", "没有逐项比对预注册",
                       "4,179", "4,189", "t(197)", "5.28", "[3.95, 4.61]",
                       "不能猜一个4.28替换", "个人护理品没有显著组间差别",
                       "公共交通则方向相反", "73%", "87%",
                       "两组多数人都选了当事人希望得到的卡",
                       "没有在此跟踪真实援助接收者", "不能把统计中介直接当作"):
            self.assertIn(phrase, note["text"])
        self.assertIn(note["text"], self.outputs["llms-full.txt"])
        self.assertTrue(all("B26" not in card["background_ids"] for card in self.export["cards"]))
        self.assertEqual(len(records), 26)

    def test_amateur_essay_keeps_distinct_standards_and_complete_sources(self):
        source = "essays/05-play-is-not-performance.md"
        essay = next(item for item in json.loads(self.outputs["data/essays.json"])["essays"]
                     if item["id"] == "E05")
        self.assertEqual(essay["text"], (ROOT / source).read_text())
        self.assertIn(essay["text"], self.outputs["llms-full.txt"])
        for anchor in ("amateur-want-better", "amateur-time-vs-practice",
                       "amateur-practice-study", "amateur-two-scores",
                       "amateur-shared-standards", "amateur-criticism", "amateur-maintenance"):
            self.assertIn('id="' + anchor + '"', essay["text"])
            self.assertEqual(self.outputs["index.html"].count('id="' + anchor + '"'), 1)
        # Content retention checks, not independent evaluation of quality or understanding.
        for phrase in ("不等于要求一个想变好的人满意于现状", "未解决的遗憾",
                       "14%不是“努力只占成功的14%”", "不能全部归给天赋",
                       "不必先通过“没有观众也想做”的纯度测试",
                       "共同承诺不能默认不算数", "不被一次评价没收的生活",
                       "拒绝进步的义务，不是签下永不进步的义务",
                       "不必先用“小份”证明自己配回来"):
            self.assertIn(phrase, essay["text"])
        self.assertEqual(build.local_href("../docs/evidence/B25-practice-and-performance.md",
                                          source), "#n25")
        self.assertEqual(build.local_href("../../" + source + "#amateur-practice-study",
                                          "docs/evidence/B25-practice-and-performance.md"),
                         "#amateur-practice-study")
        self.assertIn('"id":"R47"', (ROOT / "docs/reading-map.md").read_text())

    def test_practice_study_exports_correction_and_not_causal_recipe(self):
        records = {r["id"]: r for r in json.loads(self.outputs["data/research.json"])["records"]}
        notes = {r["id"]: r for r in json.loads(self.outputs["data/evidence.json"])["notes"]}
        record, note = records["B25"], notes["N25"]
        self.assertEqual(record["doi"], "10.1177/0956797614535810")
        self.assertEqual(record["verified_at"], "2026-09-30")
        self.assertEqual(record["access_level"], "full_text")
        self.assertFalse(record["directly_validates_cards"])
        self.assertEqual(note["source_kind"], "study_reading_note")
        self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
        for phrase in ("111个独立样本", "157个效应量", "11,135",
                       "没有纳入操纵训练", "| 游戏领域 | 26% | 24% |",
                       "| 音乐领域 | 21% | 23% |", "| 体育领域 | 18% | 20% |",
                       "| 教育领域 | 4% | 5% |", "p = .377",
                       "摘要和图3仍显示原报告", "不能把未解释部分全归给天赋",
                       "出版商PDF未取得", "不是2014年研究的又一个独立样本",
                       "差距仍是60", "没有下载并重跑OSF数据"):
            self.assertIn(phrase, note["text"])
        self.assertIn(note["text"], self.outputs["llms-full.txt"])
        self.assertTrue(all("B25" not in card["background_ids"] for card in self.export["cards"]))
        self.assertEqual(len(records), 26)

    def test_purchase_essay_preserves_argument_anchors_and_source_scope(self):
        source = "essays/04-buying-pleasure.md"
        essay = next(item for item in json.loads(self.outputs["data/essays.json"])["essays"]
                     if item["id"] == "E04")
        self.assertEqual(essay["text"], (ROOT / source).read_text())
        self.assertIn(essay["text"], self.outputs["llms-full.txt"])
        for anchor in ("purchase-substitute", "purchase-claim", "purchase-shared",
                       "purchase-options", "purchase-authorship", "purchase-uncertainty",
                       "purchase-objections"):
            self.assertIn('id="' + anchor + '"', essay["text"])
            self.assertEqual(self.outputs["index.html"].count('id="' + anchor + '"'), 1)
        # Export retention only; these assertions do not evaluate persuasiveness.
        for phrase in ("功能上的替代品，不一定是愿望的替代品",
                       "两个愿望都真，也可以只能实现一个",
                       "不能把所有互斥用途的好处相加",
                       "不花钱可以是积极的偏好",
                       "未来收益需要诚实估计，当下享受也应得到诚实承认",
                       "本文不会用“多沟通”假装已经找到答案",
                       "仅凭结果，不能证明他购买前必然草率",
                       "我们不要求他把遗憾改写成“其实一样”",
                       "数字仅帮助看清差别，不是商品报价或预算建议",
                       "这个启发不验证"):
            self.assertIn(phrase, essay["text"])
        self.assertEqual(build.local_href("../docs/research.md#b01", source), "#b01")
        self.assertEqual(build.local_href("01-pleasure-is-an-end.md#pleasure-options", source),
                         "#pleasure-options")
        self.assertEqual(len(json.loads(self.outputs["data/research.json"])["records"]), 26)
        self.assertIn('"id":"R46"', (ROOT / "docs/reading-map.md").read_text())

    def test_audience_essay_exports_full_argument_and_scoped_source_links(self):
        source = "essays/08-life-without-an-audience.md"
        essay = next(item for item in json.loads(self.outputs["data/essays.json"])["essays"]
                     if item["id"] == "E08")
        note = next(item for item in json.loads(self.outputs["data/evidence.json"])["notes"]
                    if item["id"] == "N10")
        self.assertEqual(essay["text"], (ROOT / source).read_text())
        self.assertIn(essay["text"], self.outputs["llms-full.txt"])
        for anchor in ("audience-not-a-purity-test", "audience-three-requests",
                       "audience-photo-study", "audience-staging",
                       "audience-shared-creation", "audience-verdict", "audience-admiration"):
            self.assertIn('id="' + anchor + '"', essay["text"])
            self.assertEqual(self.outputs["index.html"].count('id="' + anchor + '"'), 1)
        # Guard selected distinctions at export boundaries, not a score of argument quality.
        for phrase in ("不能当作鉴定真心的试纸", "也不把这个目标偷偷缩小",
                       "这次合作仍然发生过", "并不愿意成为作品的一部分",
                       "没有产出可以尽兴，认真想产出也不必向尽兴道歉",
                       "作品、传播与经历可以互相影响", "不需要被安慰成",
                       "不必先把愿望洗成", "不是“禁止享受被夸”的规定"):
            self.assertIn(phrase, essay["text"])
        for phrase in ("223名线上参与者", "观看第一人称巴士观光视频",
                       "这不证明效果严格相等", "刻意没有让参与者回看照片",
                       "发布与点赞也不是这篇论文直接验证的收益"):
            self.assertIn(phrase, essay["text"])
        self.assertIn("不能把论文讨论中的未来研究问题", note["text"])
        self.assertEqual(build.local_href("../docs/evidence/B10-photography.md", source), "#n10")
        self.assertEqual(build.local_href("../../" + source + "#audience-photo-study",
                                          note["source"]), "#audience-photo-study")
        self.assertIn('href="#n10"', self.outputs["index.html"])
        self.assertIn("E08/B10/N10", (ROOT / "docs/reading-map.md").read_text())
        records = json.loads(self.outputs["data/research.json"])["records"]
        self.assertEqual(len(records), 26)  # Reuse of B10 is not a new study.

    def test_background_does_not_validate_cards(self):
        research = json.loads(self.outputs["data/research.json"])
        ids = {record["id"] for record in research["records"]}
        self.assertEqual(sum(record["access_level"] == "full_text" for record in research["records"]), 26)
        self.assertEqual(ids, {"B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B09", "B10", "B11", "B12", "B13", "B14", "B15", "B16", "B17", "B18", "B19", "B20", "B21", "B22", "B23", "B24", "B25", "B26"})
        for card in self.export["cards"]:
            self.assertTrue(card["background_is_not_validation"])
            self.assertTrue(set(card["background_ids"]).issubset(ids))
            self.assertEqual(card["evidence_type"], "original_proposal")
        self.assertTrue(all(not record["directly_validates_cards"] for record in research["records"]))

    def test_both_homepages_keep_research_count_in_sync(self):
        count = len(json.loads(self.outputs["data/research.json"])["records"])
        self.assertIn(f"{count} 篇背景研究", (ROOT / "README.md").read_text())
        self.assertIn(f"{count} background studies", (ROOT / "README.en.md").read_text())
        self.assertIn(f"{count}篇背景研究", (ROOT / "docs/research.md").read_text())

    def test_research_reading_dates_come_from_each_canonical_record(self):
        records = {item["id"]: item for item in json.loads(self.outputs["data/research.json"])["records"]}
        self.assertEqual(records["B14"]["verified_at"], "2026-09-30")
        self.assertEqual(records["B03"]["verified_at"], "2026-09-30")
        self.assertTrue(all(item["verified_at"] == "2026-09-29"
                            for key, item in records.items() if key not in {"B03", "B14", "B15", "B16", "B17", "B18", "B19", "B20", "B21", "B22", "B23", "B24", "B25", "B26"}))
        for item in records.values():
            self.assertEqual(item["verified_at"], item["fields"]["核读日期"].rstrip("。"))
        # A newly read source must not silently inherit a global date.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "docs").mkdir()
            document = root / "docs/research.md"
            prefix = "## B01 · 示例\n\n- **DOI**：[来源](https://doi.org/10.0000/example)。\n"
            for field in ("", "- **核读日期**：yesterday。\n", "- **核读日期**：2026-02-30。\n"):
                document.write_text(prefix + field)
                with self.assertRaises(ValueError):
                    build.research_records(root)
            document.write_text(prefix + "- **核读日期**：2026-09-30。\n")
            self.assertEqual(build.research_records(root)[0]["verified_at"], "2026-09-30")

    def test_dark_pattern_evidence_preserves_sample_versions_and_nonclaims(self):
        records = {item["id"]: item for item in json.loads(self.outputs["data/research.json"])["records"]}
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        self.assertEqual(notes["N14"]["source_kind"], "study_reading_note")
        self.assertEqual(notes["F20"]["source_kind"], "regulatory_staff_report")
        self.assertNotIn("F20", records)
        for phrase in ("11,286", "53,180", "不是消费者随机实验"):
            self.assertIn(phrase, records["B14"]["fields"]["设计与对象"])
        for phrase in ("1,841", "1,818", "v2", "157", "140", "0.74",
                       "不是 74% 的准确率", "不是对 11,286 名消费者的实验"):
            self.assertIn(phrase, notes["N14"]["text"])
        for phrase in ("2022", "六至九", "指控", "原创虚构例句", "出版商"):
            text = notes["N14"]["text"] if phrase == "出版商" else notes["F20"]["text"]
            self.assertIn(phrase, text)
        self.assertTrue(all("B14" not in card["background_ids"] for card in self.export["cards"]))
        self.assertEqual(build.local_href("../docs/evidence/B14-dark-patterns.md",
                                         "essays/10-pleasure-not-retention.md"), "#n14")
        self.assertEqual(build.local_href("../docs/evidence/F20-interface-report.md",
                                         "essays/10-pleasure-not-retention.md"), "#f20")

    def test_retention_argument_is_exported_as_an_argument_not_an_activity(self):
        essays = {item["id"]: item for item in json.loads(self.outputs["data/essays.json"])["essays"]}
        self.assertEqual(len(essays), 11)
        self.assertEqual(essays["E10"]["source"], "essays/10-pleasure-not-retention.md")
        text = (ROOT / essays["E10"]["source"]).read_text()
        for phrase in ("不是某个平台的内部实验", "不是市场报价", "开始、继续、再次回来",
                       "免费服务也要活下去", "拒绝一份快乐的报价，不等于拒绝快乐本身"):
            self.assertIn(phrase, text)
        page = self.outputs["index.html"]
        self.assertIn('id="e10"', page)
        self.assertIn('href="#b14"', page)
        self.assertIn('href="#n14"', page)
        self.assertIn('href="#f20"', page)
        self.assertIn(text, self.outputs["llms-full.txt"])
        self.assertEqual(len(self.export["cards"]), 60)

    def test_pleasure_argument_preserves_full_text_and_navigation(self):
        essays = {item["id"]: item for item in json.loads(self.outputs["data/essays.json"])["essays"]}
        essay = essays["E11"]
        self.assertEqual(essay["source"], "essays/11-pleasure-and-reality.md")
        text = (ROOT / essay["source"]).read_text()
        self.assertEqual(essay["text"], text)
        self.assertIn(text, self.outputs["llms-full.txt"])
        self.assertEqual(build.local_href("../docs/evidence/F27-pleasure-philosophy.md",
                                         essay["source"]), "#f27")
        self.assertEqual(build.local_href("11-pleasure-and-reality.md",
                                         "essays/01-pleasure-is-an-end.md"), "#e11")
        page = self.outputs["index.html"]
        for anchor in ("pleasure-four-claims", "pleasure-machine", "pleasure-virtual",
                       "pleasure-quality", "pleasure-position"):
            self.assertEqual(page.count('id="' + anchor + '"'), 1)
            self.assertIn('href="#' + anchor + '"', page)
        self.assertIn('id="e11"', page)
        self.assertIn('href="#f27"', page)
        self.assertEqual(len(self.export["cards"]), 60)
        self.assertTrue(all("E11" not in card["essay_ids"] for card in self.export["cards"]))

    def test_philosophy_sources_do_not_become_background_experiments(self):
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        note = notes["F27"]
        self.assertEqual(note["source_kind"], "philosophical_primary_and_secondary")
        self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
        self.assertIn(note["text"], self.outputs["llms-full.txt"])
        records = json.loads(self.outputs["data/research.json"])["records"]
        self.assertEqual(len(records), 26)
        self.assertNotIn("F27", {record["id"] for record in records})
        for phrase in ("没有直接核读", "1989", "二手", "不是行为实验",
                       "不声称独创", "不改变行动卡"):
            self.assertIn(phrase, note["text"])
        for path in ("README.md", "README.en.md", "docs/ai.md",
                     "llms.txt", "skills/enjoy-the-moment/SKILL.md"):
            self.assertIn("E11", (ROOT / path).read_text(), path)

    def test_leisure_research_preserves_nonclaims_and_links(self):
        records = {item["id"]: item for item in json.loads(self.outputs["data/research.json"])["records"]}
        self.assertIn("p = .053", records["B05"]["fields"]["关键限制"])
        self.assertIn("p = .84", records["B05"]["fields"]["关键限制"])
        self.assertIn("不能转成治疗建议", records["B05"]["fields"]["关键限制"])
        self.assertEqual(records["B03"]["access_level"], "full_text")
        self.assertEqual(build.local_href("../docs/evidence/B05-leisure-value.md", "book/08-permission.md"), "#n05")
        note = next(item for item in json.loads(self.outputs["data/evidence.json"])["notes"] if item["id"] == "N05")
        self.assertEqual(note["id"], "N05")
        self.assertIn("并未显著低于量表中点", note["text"])

    def test_solitude_and_statistics_keep_distinct_evidence_boundaries(self):
        records = {item["id"]: item for item in json.loads(self.outputs["data/research.json"])["records"]}
        self.assertIn("观察性", records["B06"]["fields"]["设计与对象"])
        self.assertIn("16.7", records["B06"]["fields"]["设计与对象"])
        self.assertIn("p = .032", records["B06"]["fields"]["关键限制"])
        self.assertIn(".01", records["B06"]["fields"]["关键限制"])
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        self.assertEqual(notes["N06"]["source_kind"], "study_reading_note")
        self.assertEqual(notes["F01"]["source_kind"], "official_statistics")
        self.assertNotIn("F01", records)
        self.assertIn("不能把它缩写成", notes["F01"]["text"])
        self.assertIn("不是每个人连续记了七天", notes["F01"]["text"])
        self.assertEqual(build.local_href("../docs/evidence/B06-solitude.md", "book/07-solo.md"), "#n06")
        self.assertEqual(build.local_href("../docs/evidence/F01-time-use.md", "book/09-constrained.md"), "#f01")

    def test_teaching_and_health_sources_do_not_become_experiments(self):
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        self.assertEqual(notes["F02"]["source_kind"], "educational_reference")
        self.assertEqual(notes["F03"]["source_kind"], "educational_reference")
        self.assertEqual(notes["F04"]["source_kind"], "official_health_guidance")
        self.assertIn("没有逐项操作和验证", notes["F02"]["text"])
        self.assertIn("没有声称观看并逐一复核全部示例片段", notes["F03"]["text"])
        self.assertIn("技术标准 PDF 本次未能成功获取", notes["F04"]["text"])
        for identifier in ("F02", "F03", "F04"):
            self.assertNotIn(identifier, {
                record["id"] for record in json.loads(self.outputs["data/research.json"])["records"]
            })

    def test_offline_page_contains_all_content_without_fetches(self):
        page = self.outputs["index.html"]
        self.assertEqual(len(re.findall(r'<details class="card"', page)), len(self.export["cards"]))
        for item in ("e01", "e06", "b01", "b04", "shuaqi", "culture"):
            self.assertIn('id="' + item + '"', page)
        self.assertNotRegex(page, r'<(?:script|link|img)[^>]+(?:src|href)=["\']https?://')
        self.assertNotIn("fetch(", page)
        self.assertNotIn("localStorage", page)
        self.assertNotIn("@@CARDS@@", page)

    def test_html_is_escaped(self):
        self.assertEqual(build.inline("<script>alert(1)</script>", "README.md"),
                         "&lt;script&gt;alert(1)&lt;/script&gt;")

    def test_position_precedes_actions_and_preserves_value_argument_scope(self):
        page = self.outputs["index.html"]
        position = (ROOT / "SHUAQI.md").read_text()
        essay = (ROOT / "essays/01-pleasure-is-an-end.md").read_text()
        self.assertLess(page.index('id="shuaqi"'), page.index('id="longreads"'))
        self.assertLess(page.index('id="shuaqi"'), page.index('id="menu"'))
        self.assertEqual(page.count('id="shuaqi-content"'), 1)
        self.assertIn('class="primary" href="#shuaqi-content"', page)
        for phrase in ("我们愿意少得到什么", "保留选择的能力", "第三种不是天然不合理",
                       "不必先证明它是世界上最好的东西", "不存在的晚上"):
            self.assertIn(phrase, position + essay)
        for phrase in ("不是一个普遍最优算法", "不是用户案例", "不是关于人们通常怎样后悔"):
            self.assertIn(phrase, essay)
        self.assertIn(position, self.outputs["llms-full.txt"])
        self.assertIn(essay, self.outputs["llms-full.txt"])
        self.assertEqual(self.outputs["llms-full.txt"].count(position), 1)
        self.assertLess(self.outputs["llms-full.txt"].index(position),
                        self.outputs["llms-full.txt"].index(essay))
        short = (ROOT / "docs/manifesto.md").read_text()
        self.assertIn("完整主张与反对意见", short)
        self.assertLess(len(short), len(position))
        for path in ("docs/reading-map.md",):
            self.assertIn("pleasure-options", (ROOT / path).read_text())

    def test_position_and_essay_deep_links_keep_explicit_anchors(self):
        for source, target, anchors in (
            ("essays/01-pleasure-is-an-end.md", "../SHUAQI.md",
             ("shuaqi-position", "shuaqi-costs", "shuaqi-objections", "shuaqi-reading")),
            ("SHUAQI.md", "essays/01-pleasure-is-an-end.md",
             ("pleasure-options", "pleasure-enough")),
        ):
            for anchor in anchors:
                self.assertEqual(build.local_href(target + "#" + anchor, source), "#" + anchor)
                self.assertIn(f'<span id="{anchor}"></span>', self.outputs["index.html"])
        self.assertEqual(build.local_href("SHUAQI.md", "README.md"), "#shuaqi")
        self.assertEqual(build.local_href("essays/01-pleasure-is-an-end.md", "README.md"), "#e01")

    def test_every_argument_and_evidence_note_is_exported(self):
        essay_files = {p.relative_to(ROOT).as_posix() for p in (ROOT / "essays").glob("*.md")}
        self.assertEqual(essay_files, {path for _, path in build.ESSAYS})
        evidence_files = {p.relative_to(ROOT).as_posix() for p in (ROOT / "docs/evidence").glob("*.md")}
        self.assertEqual(evidence_files, {path for _, path in build.EVIDENCE})
        for identifier, path in build.ESSAYS + build.EVIDENCE:
            self.assertIn('id="' + identifier.lower() + '"', self.outputs["index.html"])
            self.assertIn((ROOT / path).read_text(), self.outputs["llms-full.txt"])
        self.assertLess(self.outputs["index.html"].index('id="longreads"'),
                        self.outputs["index.html"].index('id="menu"'))

    def test_numbered_instructions_keep_numbers(self):
        result = build.markdown("1. 先写\n2. 再画\n\n- 任选", "README.md")
        self.assertIn('<ol start="1">', result)
        self.assertIn("</ol>", result)
        self.assertIn("<ul>", result)
        self.assertNotIn("<h2>", build.markdown("# 重复标题\n\n正文", "README.md", omit_title=True))

    def test_chapter_introductions_are_preserved_without_duplicating_cards(self):
        chapters = json.loads(self.outputs["data/chapters.json"])["chapters"]
        self.assertEqual({chapter["source"] for chapter in chapters},
                         {p.relative_to(ROOT).as_posix() for p in (ROOT / "book").glob("*.md")})
        self.assertEqual(len(chapters), 34)
        self.assertEqual(len({chapter["id"] for chapter in chapters}), len(chapters))
        for chapter in chapters:
            source = ROOT / chapter["source"]
            introduction = source.read_text().split('<a id="j', 1)[0].strip()
            self.assertEqual(chapter["text"], introduction)
            self.assertEqual(chapter["source_sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
            expected_scope = "chapter_introduction" if '<a id="j' in source.read_text() else "full_chapter"
            self.assertEqual(chapter["scope"], expected_scope)
            self.assertNotIn("<!-- pick:", chapter["text"])
            self.assertEqual(self.outputs["llms-full.txt"].count(introduction), 1)
            self.assertIn('id="' + chapter["id"].lower() + '"', self.outputs["index.html"])
            self.assertEqual(chapter["card_ids"], [
                card["id"] for card in self.export["cards"]
                if card["source"].split("#")[0] == chapter["source"]
            ])
        self.assertLess(self.outputs["index.html"].index('id="chapters"'),
                        self.outputs["index.html"].index('id="menu"'))
        self.assertEqual(build.local_href("../book/02-senses.md", "essays/02-excitement-without-escalation.md"), "#c02")
        self.assertEqual(build.local_href("../book/02-senses.md#j007", "essays/02-excitement-without-escalation.md"), "#j007")

    def test_standalone_chapters_have_complete_text_and_no_empty_action_footer(self):
        chapters = json.loads(self.outputs["data/chapters.json"])["chapters"]
        standalone = [chapter for chapter in chapters if chapter["scope"] == "full_chapter"]
        self.assertEqual({chapter["id"] for chapter in standalone},
                         {"C11", "C12", "C13", "C14", "C15", "C16", "C17", "C18", "C19", "C20", "C21", "C22", "C23", "C24", "C25", "C26", "C27", "C28", "C29", "C30", "C31", "C32", "C33", "C34"})
        for chapter in standalone:
            self.assertEqual(chapter["card_ids"], [])
            self.assertEqual(chapter["text"], (ROOT / chapter["source"]).read_text().strip())
            self.assertEqual(build.local_href(chapter["source"], "README.md"), "#" + chapter["id"].lower())
        self.assertNotIn("<p>配套行动：</p>", self.outputs["index.html"])
        self.assertEqual(len(self.export["cards"]), 60)

    def test_nature_chapters_preserve_scope_and_source_boundaries(self):
        chapters = {item["id"]: item for item in
                    json.loads(self.outputs["data/chapters.json"])["chapters"]}
        notes = {item["id"]: item for item in
                 json.loads(self.outputs["data/evidence.json"])["notes"]}
        research = {item["id"] for item in
                    json.loads(self.outputs["data/research.json"])["records"]}
        expected = {
            "F21": ("official_science_explainer", "docs/evidence/F21-night-sky.md"),
            "F22": ("species_identification_reference", "docs/evidence/F22-bird-identification.md"),
            "F23": ("birding_ethics_and_protocol", "docs/evidence/F23-bird-records-and-ethics.md"),
        }
        for identifier, (kind, source) in expected.items():
            self.assertEqual(notes[identifier]["source_kind"], kind)
            self.assertEqual(notes[identifier]["source"], source)
            self.assertNotIn(identifier, research)
            self.assertIn("2026-09-30", notes[identifier]["text"])
            self.assertEqual(build.local_href(source, "README.md"),
                             "#" + identifier.lower())
        for identifier in ("C29", "C30"):
            self.assertEqual(chapters[identifier]["scope"], "full_chapter")
            self.assertEqual(chapters[identifier]["card_ids"], [])
            self.assertIn(chapters[identifier]["text"], self.outputs["llms-full.txt"])
        for phrase in ("月相变化不是地球的影子", "29.5", "27.3", "多数纬度",
                       "不是某个日期地点的观测报告", "日食眼镜不能"):
            self.assertIn(phrase, chapters["C29"]["text"])
        for phrase in ("成年雄鸟", "不是你所在城市", "虚构的计数问题",
                       "不等于辨认出了当地存在的每一种鸟", "不是可靠的同意表达"):
            self.assertIn(phrase, chapters["C30"]["text"])
        for phrase in ("没有播放来源中的鸟声录音", "没有逐张目视核验照片"):
            self.assertIn(phrase, notes["F22"]["text"])
        for phrase in ("不是全球统一法律", "本书选择", "圈养鸟类", "未实际操作提交界面"):
            self.assertIn(phrase, notes["F23"]["text"])
        for chapter, identifiers in (("C29", ("F21",)), ("C30", ("F22", "F23"))):
            for identifier in identifiers:
                self.assertIn(notes[identifier]["source"].split("/")[-1],
                              chapters[chapter]["text"])
                self.assertIn('href="#' + identifier.lower() + '"', self.outputs["index.html"])

    def test_moon_geometry_source_and_reader_boundaries(self):
        chapters = {c["id"]: c for c in json.loads(self.outputs["data/chapters.json"])["chapters"]}
        notes = {n["id"]: n for n in json.loads(self.outputs["data/evidence.json"])["notes"]}
        text = chapters["C29"]["text"]
        note = notes["F56"]
        self.assertEqual(note["source_kind"], "official_science_explainer_and_visualization_metadata")
        self.assertEqual(chapters["C29"]["card_ids"], [])
        for phrase in ("同步自转", "近侧、远侧", "今天的地球并没有总以同一面",
                       "天球北方", "新鲜不只发生在目的地", "不是某个城市阳台"):
            self.assertIn(phrase, text)
        for phrase in ("未观看完整动画", "2025年12月11日", "2025年12月17日",
                       "不把静态占位当成2026年的有效星历", "不是本项目观测",
                       "1、0、-1、0", "没有研究看月亮是否增加快乐"):
            self.assertIn(phrase, note["text"])
        for anchor in ("moon-rotation", "moon-day-and-night", "moon-changing-view",
                       "moon-knowledge-and-wonder"):
            self.assertIn(f'<span id="{anchor}"></span>', self.outputs["index.html"])
            self.assertIn(f'href="#{anchor}"', self.outputs["index.html"])
            self.assertEqual(build.local_href(f"../../book/29-night-sky.md#{anchor}",
                                              note["source"]), "#" + anchor)
        self.assertEqual(build.local_href(note["source"], "README.md"), "#f56")
        self.assertIn(text, self.outputs["llms-full.txt"])
        self.assertIn(note["text"], self.outputs["llms-full.txt"])
        self.assertTrue(all("F56" not in c["background_ids"] for c in self.export["cards"]))
        for path in ("docs/reading-map.md",):
            self.assertIn("C29/F21/F56", (ROOT / path).read_text())

    def test_original_moon_model_geometry_and_svg_agree(self):
        import moon_examples
        sync, fixed = moon_examples.frames(True), moon_examples.frames(False)
        self.assertEqual([f["earth_alignment"] for f in sync], [1, 1, 1, 1])
        self.assertEqual([f["earth_alignment"] for f in fixed], [1, 0, -1, 0])
        self.assertEqual([f["marker"] for f in sync], [(-1, 0), (0, -1), (1, 0), (0, 1)])
        self.assertEqual([f["marker"] for f in fixed], [(-1, 0)] * 4)
        for i in range(4):
            self.assertEqual(moon_examples.quarter_turn(sync[i]["position"]),
                             sync[(i + 1) % 4]["position"])
            self.assertEqual(moon_examples.quarter_turn(sync[i]["marker"]),
                             sync[(i + 1) % 4]["marker"])
        with self.assertRaises(TypeError):
            moon_examples.frames("yes")
        svg = (ROOT / "assets/media/moon-rotation.svg").read_text()
        self.assertEqual(svg, moon_examples.svg())
        tree = ET.fromstring(svg)
        self.assertEqual(tree.attrib["viewBox"], "0 0 720 1480")
        for name, model in (("synchronous", sync), ("no-spin", fixed)):
            groups = [g for g in tree.iter() if g.attrib.get("data-panel") == name]
            self.assertEqual(len(groups), 4)
            for group, frame in zip(groups, model):
                self.assertEqual(int(group.attrib["data-position"]), frame["number"])
                self.assertEqual((int(group.attrib["data-marker-x"]),
                                  int(group.attrib["data-marker-y"])), frame["marker"])
        png = (ROOT / "assets/media/moon-rotation.png").read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(int.from_bytes(png[16:20], "big"), 720)
        self.assertEqual(int.from_bytes(png[20:24], "big"), 1480)

    def test_flavor_and_dress_close_readings_preserve_provenance(self):
        chapters = {item["id"]: item for item in
                    json.loads(self.outputs["data/chapters.json"])["chapters"]}
        notes = {item["id"]: item for item in
                 json.loads(self.outputs["data/evidence.json"])["notes"]}
        records = json.loads(self.outputs["data/research.json"])["records"]
        self.assertEqual(len(records), 26)
        self.assertEqual(notes["F25"]["source_kind"], "supplier_technical_handbook")
        self.assertEqual(notes["F26"]["source_kind"], "fashion_record_and_image")
        for identifier in ("F25", "F26"):
            self.assertFalse(any(item["id"] == identifier for item in records))
            self.assertIn("2026-09-30", notes[identifier]["text"])
            self.assertEqual(build.local_href(notes[identifier]["source"], "README.md"),
                             "#" + identifier.lower())
        for phrase in ("供应商", "不采用这两段数字换算", "不是配方"):
            self.assertIn(phrase, notes["F25"]["text"])
        self.assertIn("未独立核对销售账册", notes["F26"]["text"])
        for phrase in ("不把它们默认为同一件成衣", "T.381-2009", "2010CT4482",
                       "女性裤装的发明史", "没有复制到仓库"):
            self.assertIn(phrase, notes["F26"]["text"])
        for identifier, anchor, image in (
                ("C14", "flavor-ice-cream", "ice-cream-volume"),
                ("C16", "dress-form-examples", "clothing-color-relations")):
            chapter = chapters[identifier]
            self.assertEqual(chapter["scope"], "full_chapter")
            self.assertEqual(chapter["card_ids"], [])
            self.assertIn(chapter["text"], self.outputs["llms-full.txt"])
            rendered = build.markdown(chapter["text"], chapter["source"])
            self.assertIn('id="' + anchor + '"', rendered)
            self.assertIn('href="#' + anchor + '"', rendered)
            self.assertEqual(rendered.count('src="data:image/png;base64,'), 1)
            self.assertNotIn('src="https:', rendered)
            self.assertIn(image + ".png", chapter["text"])
            # PNG signature and dimensions; the SVG is kept as the editable source.
            data = (ROOT / "assets/media" / (image + ".png")).read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(int.from_bytes(data[16:20], "big"), 880)

    def test_original_volume_and_color_diagrams_match_their_stated_model(self):
        ns = "{http://www.w3.org/2000/svg}"
        volume = ET.parse(ROOT / "assets/media/ice-cream-volume.svg").getroot()
        rects = {element.get("id"): element for element in volume.iter(ns + "rect")
                 if element.get("id")}
        for suffix, added in (("a", 50), ("b", 100)):
            mix = float(rects["mix-" + suffix].get("width"))
            air = float(rects["air-" + suffix].get("width"))
            self.assertAlmostEqual(air / mix, added / 100)
            self.assertAlmostEqual(air / (mix + air), added / (100 + added))
        text = " ".join(volume.itertext())
        self.assertIn("50 ÷ 100 = 50%", text)
        self.assertIn("50 ÷ 150 ≈ 33.3%", text)
        self.assertIn("100 ÷ 200 = 50%", text)
        self.assertIn("不是内部切面", text)
        color = ET.parse(ROOT / "assets/media/clothing-color-relations.svg").getroot()
        accents = [element for element in color.iter(ns + "rect")
                   if element.get("id", "").startswith("accent-")]
        self.assertEqual(len(accents), 2)
        for key in ("width", "height", "fill"):
            self.assertEqual(accents[0].get(key), accents[1].get(key))
        self.assertIsNotNone(color.find(ns + "title"))
        self.assertIsNotNone(color.find(ns + "desc"))
        chapter = (ROOT / "book/14-flavor.md").read_text()
        self.assertIn("假设体积增加全部来自充入空气，并忽略其他体积变化", chapter)
        self.assertIn("100 毫升变成 150 毫升", chapter)
        self.assertIn("后一个约为 33.3%", chapter)
        note = (ROOT / "docs/evidence/F25-ice-cream-structure.md").read_text()
        self.assertIn("50 ÷ 150 ≈ 33.3%", note)
        self.assertIn("100 ÷ 200 = 50%", note)

    def test_comic_scene_source_and_chapter_roundtrip(self):
        chapters = {item["id"]: item for item in
                    json.loads(self.outputs["data/chapters.json"])["chapters"]}
        notes = {item["id"]: item for item in
                 json.loads(self.outputs["data/evidence.json"])["notes"]}
        chapter = chapters["C24"]
        text = (ROOT / "book/24-humor.md").read_text()
        self.assertEqual(chapter["text"], text.strip())
        self.assertEqual(chapter["scope"], "full_chapter")
        self.assertEqual(chapter["card_ids"], [])
        self.assertIn(text, self.outputs["llms-full.txt"])
        note = notes["F37"]
        self.assertEqual(note["source_kind"], "literary_primary_text")
        self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
        self.assertIn(note["text"], self.outputs["llms-full.txt"])
        rendered = build.markdown(text, chapter["source"])
        self.assertIn('href="#f37"', rendered)
        self.assertIn('href="#n13"', rendered)
        self.assertIn('href="#c24"', build.markdown(note["text"], note["source"]))
        self.assertEqual(len(json.loads(self.outputs["data/research.json"])["records"]), 26)
        self.assertTrue(all("F37" not in card["background_ids"]
                            for card in self.export["cards"]))

    def test_comic_scene_anchors_and_spoiler_fold_survive_rendering(self):
        text = (ROOT / "book/24-humor.md").read_text()
        rendered = build.markdown(text, "book/24-humor.md")
        for anchor in ("humor-sandwich", "humor-language", "humor-time",
                       "humor-return", "humor-attention"):
            self.assertIn('id="' + anchor + '"', rendered)
            self.assertIn('href="#' + anchor + '"', rendered)
        self.assertEqual(rendered.count("<details>"), 1)
        self.assertEqual(rendered.count("</details>"), 1)
        self.assertIn("<summary>展开局部情节", rendered)
        fold = rendered.split("<details>", 1)[1].split("</details>", 1)[0]
        self.assertIn("空盘", fold)
        self.assertNotIn("<details open", rendered)
        self.assertIn("空盘", self.outputs["llms-full.txt"])

    def test_comic_reading_preserves_interpretation_and_version_limits(self):
        note = (ROOT / "docs/evidence/F37-comic-scenes.md").read_text()
        text = (ROOT / "book/24-humor.md").read_text()
        for marker in ("1997-03-01", "2025-11-10", "2008-06-27", "2025-06-26",
                       "David Price", "Arthur DiBianca", "David Widger",
                       "没有观看", "未核读后来的序言", "不是受众效果研究"):
            self.assertIn(marker, note)
        self.assertIn("https://www.gutenberg.org/ebooks/844", note)
        self.assertIn("https://www.gutenberg.org/ebooks/11", note)
        for marker in ("beat time", "本书原创", "没有得到完整系统说明",
                       "不保证第二次更好笑"):
            self.assertIn(marker, text)
        self.assertNotIn("例句均由本书为解释而创作", text)
        self.assertIn("折叠区只包住三明治场景后段", (ROOT / "docs/reading-map.md").read_text())

    def test_making_chapter_preserves_complete_text_and_source_kinds(self):
        chapters = {item["id"]: item for item in
                    json.loads(self.outputs["data/chapters.json"])["chapters"]}
        notes = {item["id"]: item for item in
                 json.loads(self.outputs["data/evidence.json"])["notes"]}
        chapter = chapters["C17"]
        text = (ROOT / "book/17-making.md").read_text()
        self.assertEqual(chapter["text"], text.strip())
        self.assertEqual(chapter["scope"], "full_chapter")
        self.assertEqual(chapter["card_ids"], [])
        self.assertIn(text, self.outputs["llms-full.txt"])
        rendered = build.markdown(text, chapter["source"])
        self.assertEqual(rendered.count('src="data:image/png;base64,'), 2)
        for anchor in ("making-weave", "making-sample", "making-zine", "making-handmade"):
            self.assertIn('id="' + anchor + '"', rendered)
            self.assertIn('href="#' + anchor + '"', rendered)
        for identifier, kind in (("F28", "museum_teaching_and_artist_text"),
                                 ("F29", "museum_instructional_diagrams")):
            note = notes[identifier]
            self.assertEqual(note["source_kind"], kind)
            self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
            self.assertIn(note["text"], self.outputs["llms-full.txt"])
            self.assertIn('href="#' + identifier.lower() + '"', rendered)
            self.assertIn('href="#c17"', build.markdown(note["text"], note["source"]))
        self.assertEqual(len(json.loads(self.outputs["data/research.json"])["records"]), 26)
        self.assertIn("同一页面", notes["F28"]["text"])
        self.assertIn("1965 A.D.", notes["F28"]["text"])
        self.assertIn("未取得原始手稿", notes["F28"]["text"])
        self.assertIn("不是附带页码与文字朝向的拼版模板", notes["F29"]["text"])
        self.assertIn("没有实际折制", notes["F29"]["text"])
        self.assertEqual(len(self.export["cards"]), 60)

    def test_public_life_preserves_full_text_attribution_and_source_types(self):
        chapters = {item["id"]: item for item in
                    json.loads(self.outputs["data/chapters.json"])["chapters"]}
        notes = {item["id"]: item for item in
                 json.loads(self.outputs["data/evidence.json"])["notes"]}
        chapter = chapters["C15"]
        text = (ROOT / chapter["source"]).read_text()
        self.assertEqual(chapter["text"], text.strip())
        self.assertIn(text, self.outputs["llms-full.txt"])
        rendered = build.markdown(text, chapter["source"])
        for anchor in ("street-counts", "street-midtown", "street-seats",
                       "street-unscheduled", "street-conflicts"):
            self.assertIn('id="' + anchor + '"', rendered)
            self.assertIn('href="#' + anchor + '"', rendered)
        for identifier, kind in (("F35", "public_life_observation_protocol"),
                                 ("F36", "municipal_before_after_evaluation")):
            note = notes[identifier]
            self.assertEqual(note["source_kind"], kind)
            self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
            self.assertIn(note["text"], self.outputs["llms-full.txt"])
            self.assertIn('href="#' + identifier.lower() + '"', rendered)
            self.assertIn('href="#c15"', build.markdown(note["text"], note["source"]))
        attribution = next(line for line in text.splitlines()
                           if line.startswith("The Public Life Data Protocol was jointly"))
        for source in ("LICENSE", "docs/sources.md", notes["F35"]["source"]):
            self.assertIn(attribution, (ROOT / source).read_text())
        for phrase in ("1b051183e1764338b4823556922747c610e1d8de",
                       "小区域例外", "每小时完成一次", "没有相同的独立活动栏"):
            self.assertIn(phrase, notes["F35"]["text"])
        for phrase in ("不是日客流", "没有活动，也能算好地方吗", "安静、通行和清理由谁负责",
                       "即使一个人只是坐着吃自带的午饭", "不要求记录可识别个人"):
            self.assertIn(phrase, text)

    def test_public_life_hypothetical_snapshots_do_not_determine_visitors(self):
        scenarios = (
            [set(range(6)), set(range(6)), set(range(6))],
            [set(range(6)), set(range(6, 12)), set(range(12, 18))],
        )
        for scans in scenarios:
            self.assertEqual([len(scan) for scan in scans], [6, 6, 6])
            self.assertEqual(sum(map(len, scans)), 18)
            self.assertEqual(Fraction(sum(map(len, scans)), len(scans)), 6)
        self.assertEqual(len(set.union(*scenarios[0])), 6)
        self.assertEqual(len(set.union(*scenarios[1])), 18)
        text = (ROOT / "book/15-neighborhood.md").read_text()
        for phrase in ("三次扫描，每次都看到 6 人", "18 人次", "平均在场数是 6",
                       "未被扫描碰到的人还可能存在", "不能直接算出每人停留多久",
                       "活动还可能重叠"):
            self.assertIn(phrase, text)

    def test_midtown_table_keeps_site_values_units_and_peak_scope(self):
        chapter = (ROOT / "book/15-neighborhood.md").read_text()
        note = (ROOT / "docs/evidence/F36-midtown-public-space.md").read_text()
        pairs = [(int(a), int(b)) for a, b in re.findall(
            r"^\| (?:先驱广场|百老汇|时代广场)[^|]+\| (\d+) → (\d+) \|$",
            chapter, re.M)]
        note_pairs = [(int(a), int(b)) for a, b in re.findall(
            r"^\| (?:Herald Square|Broadway Blvd|Times Square)[^|]+\| (\d+) / (\d+) \|$",
            note, re.M)]
        self.assertEqual(pairs, [(94, 114), (57, 74), (17, 90)])
        self.assertEqual(note_pairs, pairs)
        for before, after in pairs:
            self.assertNotEqual(Fraction(after - before, before), Fraction(84, 100))
        for phrase in ("平日平均快照", "高峰时段", "不是随机试验",
                       "原始逐次记录", "NACTO", "不是报告作者", "2009 年 5 月和 10 月",
                       "没有把 2019 年 PLDP 仓库快照说成 2009 年项目使用的调查规范"):
            self.assertIn(phrase, note)

    def test_photography_preserves_complete_models_and_source_boundaries(self):
        chapters = {item["id"]: item for item in
                    json.loads(self.outputs["data/chapters.json"])["chapters"]}
        notes = {item["id"]: item for item in
                 json.loads(self.outputs["data/evidence.json"])["notes"]}
        chapter, note = chapters["C20"], notes["F34"]
        text = (ROOT / chapter["source"]).read_text()
        self.assertEqual(chapter["text"], text.strip())
        self.assertIn(text, self.outputs["llms-full.txt"])
        self.assertEqual(note["source_kind"], "educational_optics_and_original_models")
        self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
        self.assertIn(note["text"], self.outputs["llms-full.txt"])
        rendered = build.markdown(text, chapter["source"])
        for anchor in ("photo-viewpoint", "photo-duration", "photo-sequence", "photo-audience"):
            self.assertIn('id="' + anchor + '"', rendered)
            self.assertIn('href="#' + anchor + '"', rendered)
        self.assertIn('href="#f34"', rendered)
        self.assertIn('href="#c20"', build.markdown(note["text"], note["source"]))
        self.assertEqual(rendered.count('src="data:image/png;base64,'), 2)
        for phrase in ("理想中心投影", "原地裁剪", "不是实拍测量",
                       "速度方向不变", "尚未饱和", "不是观众实验",
                       "喜欢被看见，也没有错", "p = .058"):
            self.assertIn(phrase, text)
        for phrase in ("没有运行", "不是 2026 年设备能力报告",
                       "没有下载或视觉核对该网页样片", "不是本书推荐值"):
            self.assertIn(phrase, note["text"])
        attribution = (ROOT / "assets/media/README.md").read_text()
        for name in ("photo-viewpoint", "photo-duration"):
            self.assertIn(name + ".svg", attribution)
            for suffix in (".png", ".svg"):
                self.assertTrue((ROOT / "assets/media" / (name + suffix)).is_file())

    def test_photography_diagrams_match_geometry_and_time_models(self):
        ns = "{http://www.w3.org/2000/svg}"
        diagram = ET.parse(ROOT / "assets/media/photo-viewpoint.svg").getroot()
        rects = {el.get("id"): el for el in diagram.iter(ns + "rect") if el.get("id")}
        cases = (("near", 2, 4, 100), ("crop", 2, 4, 150), ("far", 8, 10, 150))
        for name, za, zb, expected_a in cases:
            a, b = rects[name + "-a"], rects[name + "-b"]
            ha, hb = Fraction(a.get("height")), Fraction(b.get("height"))
            self.assertEqual(ha, expected_a)
            self.assertEqual(hb / ha, Fraction(za, zb))
            self.assertEqual(Fraction(a.get("y")) + ha, Fraction(b.get("y")) + hb)
            self.assertEqual(ha, Fraction(a.get("data-height")))
            self.assertEqual(hb, Fraction(b.get("data-height")))
        self.assertEqual(4 - 2, 10 - 8)
        duration = ET.parse(ROOT / "assets/media/photo-duration.svg").getroot()
        paths = {el.get("id"): el for el in duration.iter(ns + "path")}
        for identifier, seconds, expected in (("long-path", Fraction(1, 30), 8),
                                               ("short-path", Fraction(1, 120), 2)):
            self.assertEqual(240 * seconds, expected)
            node = paths[identifier]
            self.assertEqual(int(node.get("data-pixels")), expected)
            match = re.fullmatch(r"M(\d+) (\d+)H(\d+)", node.get("d"))
            self.assertIsNotNone(match)
            self.assertEqual(int(match[3]) - int(match[1]), expected * 24)
        for root in (diagram, duration):
            self.assertIsNotNone(root.find(ns + "title"))
            self.assertIsNotNone(root.find(ns + "desc"))
        note = (ROOT / "docs/evidence/F34-photographic-space-and-time.md").read_text()
        for expression in ("2 / 4 | 1/2 | 100 / 50",
                           "2 / 4 | 1/2 | 150 / 75",
                           "8 / 10 | 4/5 | 150 / 120",
                           "240 × (1/30) = 8", "240 × (1/120) = 2"):
            self.assertIn(expression, note)

    def test_shared_stories_preserve_rules_scope_and_source_attribution(self):
        chapters = {item["id"]: item for item in
                    json.loads(self.outputs["data/chapters.json"])["chapters"]}
        notes = {item["id"]: item for item in
                 json.loads(self.outputs["data/evidence.json"])["notes"]}
        chapter = chapters["C34"]
        text = (ROOT / chapter["source"]).read_text()
        self.assertEqual(chapter["scope"], "full_chapter")
        self.assertEqual(chapter["card_ids"], [])
        self.assertEqual(chapter["text"], text.strip())
        self.assertIn(text, self.outputs["llms-full.txt"])
        rendered = build.markdown(text, chapter["source"])
        for anchor in ("story-choice", "story-dice", "story-aspects", "story-table"):
            self.assertIn('id="' + anchor + '"', rendered)
            self.assertIn('href="#' + anchor + '"', rendered)
        for identifier, kind in (("F32", "game_rules_and_original_probability"),
                                 ("F33", "official_game_srd")):
            note = notes[identifier]
            self.assertEqual(note["source_kind"], kind)
            self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
            self.assertIn(note["text"], self.outputs["llms-full.txt"])
            self.assertIn('href="#' + identifier.lower() + '"', rendered)
            self.assertIn('href="#c34"', build.markdown(note["text"], note["source"]))
        license_text = (ROOT / "LICENSE").read_text()
        attribution_lines = [
            line for line in text.splitlines()
            if line.startswith("This work is based on")
        ]
        self.assertEqual(len(attribution_lines), 2)
        for line, identifier in zip(attribution_lines, ("F32", "F33")):
            self.assertIn(line, license_text)
            self.assertIn(line, notes[identifier]["text"])
        self.assertIn("Leonard Balsera", attribution_lines[1])
        self.assertIn("Ryan Macklin", attribution_lines[1])
        self.assertIn("Fate-Condensed-SRD-CC-BY.html", notes["F33"]["text"])
        self.assertIn("page XX", notes["F33"]["text"])
        self.assertIn("零颗或负数骰子", text)
        self.assertIn("不能推广成唯一规则", text)
        self.assertIn("不是所有后果的发生率", text)
        self.assertIn("不是照搬前文", text)
        self.assertIn("四骰结果为 `+、0、−、+`", text)
        signs = {"+": 1, "0": 0, "−": -1}
        example = re.search(r"四骰结果为 `([^`]+)`", text).group(1).split("、")
        self.assertEqual(sum(signs[sign] for sign in example), 1)
        self.assertIn("技能为 2，合计 3，对难度 4 还差 1", text)
        self.assertIn("结果变为 5", text)
        self.assertEqual(len(self.export["cards"]), 60)
        self.assertEqual(len(json.loads(self.outputs["data/research.json"])["records"]), 26)

    def test_shared_stories_dice_table_matches_exhaustive_outcomes(self):
        text = (ROOT / "book/34-shared-stories.md").read_text()
        labels = ("1—3", "4—5", "至少一颗 6")
        table = {}
        for line in text.splitlines():
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) == 3 and cells[0] in labels:
                table[cells[0]] = cells[1:]
        self.assertEqual(set(table), set(labels))
        for size in (1, 2):
            outcomes = list(itertools.product(range(1, 7), repeat=size))
            groups = {
                "1—3": [dice for dice in outcomes if max(dice) <= 3],
                "4—5": [dice for dice in outcomes if 4 <= max(dice) <= 5],
                "至少一颗 6": [dice for dice in outcomes if max(dice) == 6],
            }
            self.assertEqual(sum(map(len, groups.values())), 6 ** size)
            for label, dice in groups.items():
                displayed = re.fullmatch(r"(\d+)/(\d+) [=≈] ([\d.]+)%", table[label][size - 1])
                self.assertIsNotNone(displayed)
                numerator, denominator, percentage = displayed.groups()
                expected = Fraction(len(dice), 6 ** size)
                self.assertEqual(Fraction(int(numerator), int(denominator)), expected)
                self.assertAlmostEqual(float(percentage), float(expected * 100), places=2)
        two_dice = list(itertools.product(range(1, 7), repeat=2))
        criticals = [dice for dice in two_dice if dice.count(6) > 1]
        exact_one = [dice for dice in two_dice if dice.count(6) == 1]
        self.assertEqual(len(criticals), 1)
        self.assertEqual(len(exact_one), 10)
        self.assertIn("占 1/36", text)
        self.assertIn("有 10 种", text)
        self.assertIn("表中的 11 种", text)
        # The zero-die exception must not accidentally use the ordinary 2d column.
        self.assertEqual(sum(min(dice) <= 3 for dice in two_dice), 27)
        self.assertNotEqual(sum(min(dice) <= 3 for dice in two_dice),
                            sum(max(dice) <= 3 for dice in two_dice))

    def test_singing_chapter_and_heterogeneous_sources_remain_complete(self):
        chapters = {item["id"]: item for item in
                    json.loads(self.outputs["data/chapters.json"])["chapters"]}
        notes = {item["id"]: item for item in
                 json.loads(self.outputs["data/evidence.json"])["notes"]}
        chapter = chapters["C33"]
        text = (ROOT / chapter["source"]).read_text()
        self.assertEqual(chapter["scope"], "full_chapter")
        self.assertEqual(chapter["card_ids"], [])
        self.assertEqual(chapter["text"], text.strip())
        self.assertIn(text, self.outputs["llms-full.txt"])
        rendered = build.markdown(text, chapter["source"])
        for anchor in ("singing-transpose", "singing-timbre",
                       "singing-together", "singing-microphone"):
            self.assertIn('id="' + anchor + '"', rendered)
            self.assertIn('href="#' + anchor + '"', rendered)
        for identifier, kind in (
                ("F30", "acoustics_and_music_education"),
                ("F31", "manufacturer_manual_and_health_guidance")):
            note = notes[identifier]
            self.assertEqual(note["source_kind"], kind)
            self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
            self.assertIn(note["text"], self.outputs["llms-full.txt"])
            self.assertIn('href="#' + identifier.lower() + '"', rendered)
            self.assertIn('href="#c33"', build.markdown(note["text"], note["source"]))
        self.assertIn("未播放页面音视频", notes["F30"]["text"])
        self.assertIn("Version: 6.4 (2024-F)", notes["F31"]["text"])
        self.assertIn("June 11, 2025", notes["F31"]["text"])
        self.assertEqual(len(json.loads(self.outputs["data/research.json"])["records"]), 26)
        self.assertEqual(len(self.export["cards"]), 60)

    def test_singing_examples_preserve_intervals_and_round_offset(self):
        text = (ROOT / "book/33-singing.md").read_text()
        note_values = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "B": 11}
        rows = {}
        for line in text.splitlines():
            if line.startswith("| ") and " → " in line:
                label, sequence = [cell.strip() for cell in line.strip("|").split("|")]
                pitches = []
                for token in sequence.split(" → "):
                    match = re.fullmatch(r"([CDEFGAB])(♭?)([0-9])", token)
                    self.assertIsNotNone(match, token)
                    letter, flat, octave = match.groups()
                    pitches.append(note_values[letter] - bool(flat) + 12 * (int(octave) - 3))
                rows[label] = pitches
        self.assertEqual(set(rows), {"起始版本", "整体低两个半音", "整体低一个八度"})
        base = rows["起始版本"]
        for name, offset in (("起始版本", 0), ("整体低两个半音", -2),
                             ("整体低一个八度", -12)):
            pitches = rows[name]
            self.assertEqual(pitches, [pitch + offset for pitch in base])
            self.assertEqual([b - a for a, b in zip(pitches, pitches[1:])],
                             [2, 2, 3, -3, -2, -2])
        self.assertIn("低八度本身也是移调的一种", text)
        temporal = {"第一组": [], "第二组": []}
        ticks = []
        for line in text.splitlines():
            if re.match(r"\| [1-6] \|", line):
                cells = [cell.strip() for cell in line.strip("|").split("|")]
                ticks.append(int(cells[0]))
                temporal["第一组"].append(cells[1])
                temporal["第二组"].append(cells[2])
        self.assertEqual(ticks, [1, 2, 3, 4, 5, 6])
        self.assertEqual(temporal["第一组"], ["A", "B", "C", "D", "A", "B"])
        self.assertEqual(temporal["第二组"], ["等待", "等待", "A", "B", "C", "D"])
        self.assertEqual(temporal["第一组"][:4], temporal["第二组"][2:])
        self.assertIn("这里假设材料本来适合轮唱", text)
        self.assertIn("没有证明两个段落同时响起来一定和谐", text)

    def test_making_original_diagrams_show_alternating_crossings_and_eight_pages(self):
        ns = "{http://www.w3.org/2000/svg}"
        weave = ET.parse(ROOT / "assets/media/weave-crossings.svg").getroot()
        crossings = {node.get("id"): node for node in weave.iter(ns + "g")
                     if node.get("id", "").startswith("cross-")}
        self.assertEqual(len(crossings), 36)
        for row in range(6):
            for col in range(6):
                node = crossings[f"cross-{row}-{col}"]
                expected = "warp" if (row + col) % 2 == 0 else "weft"
                self.assertEqual(node.get("data-top"), expected)
                paths = list(node.iter(ns + "path"))
                self.assertEqual(len(paths), 2 if expected == "warp" else 0)
                if paths:
                    x, y = 90 + 52 * col, 178 + 48 * row
                    self.assertEqual(paths[-1].get("d"), f"M{x} {y-13}V{y+13}")
        zine = ET.parse(ROOT / "assets/media/zine-structure.svg").getroot()
        paths = {node.get("id"): node for node in zine.iter(ns + "path")}
        self.assertEqual(paths["central-opening"].get("d"), "M130 240H310")
        self.assertEqual(paths["crease-h"].get("d"), "M40 240H400")
        rects = {node.get("id"): node for node in zine.iter(ns + "rect")}
        self.assertEqual({key for key in rects if key and key.startswith("reading-page-")},
                         {f"reading-page-{i}" for i in range(1, 9)})
        self.assertEqual(rects["source-paper"].get("width"), "360")
        for a, b in ((2, 3), (4, 5), (6, 7)):
            self.assertEqual(rects[f"reading-page-{a}"].get("y"),
                             rects[f"reading-page-{b}"].get("y"))
        for name, height in (("weave-crossings", 1220), ("zine-structure", 1768)):
            image = (ROOT / "assets/media" / (name + ".png")).read_bytes()
            self.assertEqual(image[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(int.from_bytes(image[16:20], "big"), 880)
            self.assertEqual(int.from_bytes(image[20:24], "big"), height)
            svg = ET.parse(ROOT / "assets/media" / (name + ".svg")).getroot()
            self.assertIsNotNone(svg.find(ns + "title"))
            self.assertIsNotNone(svg.find(ns + "desc"))

    def test_fear_and_insight_sources_keep_samples_nonresults_and_spoilers(self):
        chapters = {item["id"]: item for item in
                    json.loads(self.outputs["data/chapters.json"])["chapters"]}
        notes = {item["id"]: item for item in
                 json.loads(self.outputs["data/evidence.json"])["notes"]}
        records = {item["id"]: item for item in
                   json.loads(self.outputs["data/research.json"])["records"]}
        for identifier in ("B15", "B16"):
            self.assertEqual(records[identifier]["verified_at"], "2026-09-30")
            self.assertEqual(records[identifier]["access_level"], "full_text")
            self.assertFalse(records[identifier]["directly_validates_cards"])
            self.assertTrue(all(identifier not in item["background_ids"]
                                for item in self.export["cards"]))
        for identifier in ("N15", "N16"):
            self.assertEqual(notes[identifier]["source_kind"], "study_reading_note")
        self.assertEqual(notes["F24"]["source_kind"], "literary_primary_text")
        self.assertNotIn("F24", records)
        for phrase in ("92", "p = .564", "p = .760", "没有预注册",
                       "p = .776", "未完成鬼屋体验"):
            self.assertIn(phrase, notes["N15"]["text"])
        for phrase in ("2,450", "1,778", "1,124", "417", "2017-01-20",
                       "不是所有顿悟中有 37%", "p = .061", "p = .08", "p = .926",
                       "合理可行的替代解释", "没有收到答案正确与否的反馈"):
            self.assertIn(phrase, notes["N16"]["text"])
        for identifier in ("C31", "C32"):
            self.assertEqual(chapters[identifier]["scope"], "full_chapter")
            self.assertEqual(chapters[identifier]["card_ids"], [])
            self.assertIn(chapters[identifier]["text"], self.outputs["llms-full.txt"])
        self.assertEqual(chapters["C31"]["text"].count("<details>"), 1)
        self.assertEqual(chapters["C32"]["text"].count("<details>"), 8)
        self.assertEqual(notes["F24"]["text"].count("<details>"), 1)
        self.assertIn("没有直接交代第三个愿望的具体措辞", chapters["C31"]["text"])
        self.assertIn("不是作者访谈、观众反应研究", notes["F24"]["text"])
        for source, identifier in (
                ("docs/evidence/B15-recreational-fear.md", "n15"),
                ("docs/evidence/B16-false-insight.md", "n16"),
                ("docs/evidence/F24-monkeys-paw.md", "f24")):
            self.assertEqual(build.local_href(source, "README.md"), "#" + identifier)
            self.assertIn('href="#' + identifier + '"', self.outputs["index.html"])

    def test_collecting_chapter_and_source_notes_roundtrip(self):
        chapters = {item["id"]: item for item in
                    json.loads(self.outputs["data/chapters.json"])["chapters"]}
        notes = {item["id"]: item for item in
                 json.loads(self.outputs["data/evidence.json"])["notes"]}
        text = (ROOT / "book/26-collecting.md").read_text()
        chapter = chapters["C26"]
        self.assertEqual(chapter["text"], text.strip())
        self.assertEqual(chapter["scope"], "full_chapter")
        self.assertEqual(chapter["card_ids"], [])
        self.assertIn(text, self.outputs["llms-full.txt"])
        rendered = build.markdown(text, chapter["source"])
        for anchor in ("collecting-crosses", "collecting-layers", "collecting-digital",
                       "collecting-return", "collecting-abundance"):
            self.assertIn('id="' + anchor + '"', rendered)
            self.assertIn('href="#' + anchor + '"', rendered)
        for identifier, kind in (("F38", "artwork_record_and_image"),
                                 ("F39", "personal_digital_archiving_guidance")):
            note = notes[identifier]
            self.assertEqual(note["source_kind"], kind)
            self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
            self.assertIn(note["text"], self.outputs["llms-full.txt"])
            self.assertIn('href="#' + identifier.lower() + '"', rendered)
            self.assertIn('href="#c26"', build.markdown(note["text"], note["source"]))
        self.assertEqual(len(json.loads(self.outputs["data/research.json"])["records"]), 26)
        self.assertTrue(all(not ({"F38", "F39"} & set(c["background_ids"]))
                            for c in self.export["cards"]))

    def test_games_chapter_sources_and_links_export(self):
        chapters = {c["id"]: c for c in json.loads(self.outputs["data/chapters.json"])["chapters"]}
        notes = {n["id"]: n for n in json.loads(self.outputs["data/evidence.json"])["notes"]}
        text = (ROOT / "book/19-games.md").read_text()
        self.assertEqual(chapters["C19"]["text"], text.strip())
        self.assertEqual(chapters["C19"]["scope"], "full_chapter")
        self.assertEqual(chapters["C19"]["card_ids"], [])
        self.assertIn(text, self.outputs["llms-full.txt"])
        html = build.markdown(text, "book/19-games.md")
        for anchor in ("games-othello", "games-hanabi", "games-uncertainty",
                       "games-chosen-rules", "games-delegation"):
            self.assertIn('id="' + anchor + '"', html)
            self.assertIn('href="#' + anchor + '"', html)
        for identifier, kind in (("F42", "official_game_rules_and_original_position"),
                                 ("F43", "publisher_game_rules")):
            note = notes[identifier]
            self.assertEqual(note["source_kind"], kind)
            self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
            self.assertIn(note["text"], self.outputs["llms-full.txt"])
            self.assertIn('href="#' + identifier.lower() + '"', html)
            self.assertIn('href="#c19"', build.markdown(note["text"], note["source"]))
        for retained in ("f09", "n09"):
            self.assertIn('href="#' + retained + '"', html)
        self.assertTrue(all(not ({"F42", "F43"} & set(c["background_ids"]))
                            for c in self.export["cards"]))

    def test_games_original_diagram_and_limited_claims(self):
        text = (ROOT / "book/19-games.md").read_text()
        figures = re.findall(r"!\[([^\]]+)\]\(([^)]+)\)", text)
        self.assertEqual(len(figures), 1)
        alt, href = figures[0]
        self.assertGreater(len(alt), 90)
        for marker in ("B1", "E1", "A1", "各11枚", "三枚", "一枚"):
            self.assertIn(marker, alt)
        self.assertTrue((ROOT / "book" / href).is_file())
        html = build.markdown(text, "book/19-games.md")
        self.assertEqual(html.count('src="data:image/png;base64,'), 1)
        for marker in ("黑 15、白 8", "黑 13、白 10", "没有证明乙是最优解",
                       "红 1｜蓝 1｜红 3｜绿 2｜白 5", "乙此前没有收到",
                       "第 1、3 张", "第 1、2 张", "甲选择提示",
                       "提示当时的空序列",
                       "原规则、共同商定的变体、没说出口的暗号"):
            self.assertIn(marker, text)

    def test_games_notes_preserve_source_and_version_limits(self):
        othello = (ROOT / "docs/evidence/F42-othello-choice.md").read_text()
        hanabi = (ROOT / "docs/evidence/F43-hanabi-information.md").read_text()
        for marker in ("没有正文第 3 条", "没有证明 E1 最优、B1 必败",
                       "黑 14、白 10", "不是名局", "不搜索全局最优"):
            self.assertIn(marker, othello)
        for marker in ("©2013", "2 个横向三栏", "文本提取只返回少量图例文字",
                       "所有蓝色标记都在桌上时不能弃牌", "6 fireworks",
                       "本书保留这处不一致", "不是完整发牌模拟"):
            self.assertIn(marker, hanabi)
        self.assertIn("F42/F43", (ROOT / "docs/reading-map.md").read_text())

    def test_celebration_chapter_and_sources_roundtrip(self):
        chapters = {c["id"]: c for c in json.loads(self.outputs["data/chapters.json"])["chapters"]}
        notes = {n["id"]: n for n in json.loads(self.outputs["data/evidence.json"])["notes"]}
        text = (ROOT / "book/18-celebration.md").read_text()
        self.assertEqual(chapters["C18"]["text"], text.strip())
        self.assertEqual(chapters["C18"]["scope"], "full_chapter")
        self.assertEqual(chapters["C18"]["card_ids"], [])
        self.assertIn(text, self.outputs["llms-full.txt"])
        html = build.markdown(text, "book/18-celebration.md")
        for anchor in ("celebration-top", "celebration-calendar", "celebration-repetition",
                       "celebration-magi", "celebration-generosity", "celebration-objection"):
            self.assertIn('id="' + anchor + '"', html)
            self.assertIn('href="#' + anchor + '"', html)
        for identifier, kind in (("F44", "official_heritage_description"),
                                 ("F45", "literary_primary_text")):
            note = notes[identifier]
            self.assertEqual(note["source_kind"], kind)
            self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
            self.assertIn(note["text"], self.outputs["llms-full.txt"])
            self.assertIn('href="#' + identifier.lower() + '"', html)
            self.assertIn('href="#c18"', build.markdown(note["text"], note["source"]))
        self.assertIn('href="#n08"', html)
        self.assertTrue(all(not ({"F44", "F45"} & set(c["background_ids"]))
                            for c in self.export["cards"]))

    def test_novelty_chapter_keeps_prose_card_and_source_boundaries(self):
        chapters = {c["id"]: c for c in json.loads(self.outputs["data/chapters.json"])["chapters"]}
        notes = {n["id"]: n for n in json.loads(self.outputs["data/evidence.json"])["notes"]}
        text = (ROOT / "book/03-novelty.md").read_text()
        prose = text.split('<a id="j013"></a>', 1)[0].strip()
        self.assertEqual(chapters["C03"]["text"], prose)
        self.assertIn(prose, self.outputs["llms-full.txt"])
        self.assertEqual(chapters["C03"]["card_ids"], [f"J{i:03d}" for i in range(13, 19)])
        html = build.markdown(prose, "book/03-novelty.md")
        for anchor in ("novelty-cube", "novelty-uncertainty", "novelty-learning",
                       "novelty-repeat", "novelty-intensity"):
            self.assertIn('id="' + anchor + '"', html)
            self.assertIn('href="#' + anchor + '"', html)
        note = notes["F49"]
        self.assertEqual(note["source_kind"], "researcher_authored_explainer")
        self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
        self.assertIn(note["text"], self.outputs["llms-full.txt"])
        self.assertIn('href="#f49"', html)
        self.assertIn('href="#n03"', html)
        self.assertIn('href="#novelty-cube"', build.markdown(note["text"], note["source"]))
        self.assertTrue(all("F49" not in c["background_ids"] for c in self.export["cards"]))
        self.assertEqual(html.count('src="data:image/png;base64,'), 1)
        self.assertIn("不是本书这张立方体图的实验", text)

    def test_novelty_diagram_is_static_and_described_without_color_dependency(self):
        svg = (ROOT / "assets/media/novelty-cube.svg").read_text()
        root = ET.fromstring(svg)
        self.assertEqual(root.attrib["viewBox"], "0 0 840 880")
        self.assertNotIn("<animate", svg)
        self.assertNotIn("<script", svg)
        self.assertNotIn("<image", svg)
        ns = {"s": "http://www.w3.org/2000/svg"}
        wires = [root.find(f".//s:g[@id='{key}']/s:path", ns).attrib["d"]
                 for key in ("wireframe", "interpretation-a", "interpretation-b")]
        self.assertEqual(len(set(wires)), 1)
        text = (ROOT / "book/03-novelty.md").read_text()
        alt = re.search(r"!\[([^\]]+)\]\(\.\./assets/media/novelty-cube.png\)", text).group(1)
        for marker in ("十二条边", "左下", "右上", "没有动画", "平面线条"):
            self.assertIn(marker, alt)
        self.assertGreater(len(alt), 100)

    def test_novelty_policy_does_not_upgrade_the_richness_proof(self):
        notes = {n["id"]: n for n in json.loads(self.outputs["data/evidence.json"])["notes"]}
        for marker in ("Under Review", "HTTP 403", "没有把这层转引", "内克尔立方体"):
            if marker == "没有把这层转引":
                self.assertIn(marker, (ROOT / "book/03-novelty.md").read_text())
            else:
                self.assertIn(marker, notes["N03"]["text"])
        for path in ("docs/reading-map.md",):
            self.assertIn("C03/F49/B03", (ROOT / path).read_text())

    def test_cognitive_labor_keeps_author_summary_and_original_analogy_distinct(self):
        notes = {n["id"]: n for n in json.loads(self.outputs["data/evidence.json"])["notes"]}
        note = notes["F50"]
        self.assertEqual(note["source_kind"], "researcher_authored_project_summary")
        self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
        self.assertIn(note["text"], self.outputs["llms-full.txt"])
        for phrase in ("不是本项目已核读的原始论文全文", "170余次访谈",
                       "不能直接充当2019年论文的样本量", "不是PDF",
                       "不是已验证的家庭公平评分", "全部是本书原创假想"):
            self.assertIn(phrase, note["text"])
        records = json.loads(self.outputs["data/research.json"])["records"]
        self.assertNotIn("10.1177/0003122419859007", {r["doi"] for r in records})
        self.assertTrue(all("F50" not in c["background_ids"] for c in self.export["cards"]))
        chapter = next(c for c in json.loads(self.outputs["data/chapters.json"])["chapters"]
                       if c["id"] == "C09")
        text = (ROOT / chapter["source"]).read_text()
        self.assertEqual(chapter["text"], text.split('<a id="j049"></a>', 1)[0].strip())
        for anchor in ("constrained-cognitive", "constrained-three-arrangements",
                       "constrained-authority"):
            self.assertIn('id="' + anchor + '"', chapter["text"])
            self.assertEqual(self.outputs["index.html"].count('id="' + anchor + '"'), 1)
            self.assertIn('href="#' + anchor + '"', self.outputs["index.html"])
        for phrase in ("两句话可以同时属实", "三种安排没有实验排名",
                       "退出一段劳动，与放弃所有发言权", "喜欢有对象、强度和期限"):
            self.assertIn(phrase, chapter["text"])
        self.assertIn('href="#f50"', self.outputs["index.html"])
        self.assertEqual(build.local_href("../../book/09-constrained.md#constrained-cognitive",
                                          note["source"]), "#constrained-cognitive")
        self.assertEqual(re.findall(r'<!-- pick: .*?"id":"(J\d+)"', text),
                         [f"J{i:03d}" for i in range(49, 55)])
        for path in ("docs/reading-map.md",):
            self.assertIn("C09/F50", (ROOT / path).read_text())

    def test_solitude_literary_sources_and_navigation_survive_exports(self):
        chapters = {c["id"]: c for c in json.loads(self.outputs["data/chapters.json"])["chapters"]}
        notes = {n["id"]: n for n in json.loads(self.outputs["data/evidence.json"])["notes"]}
        text = (ROOT / "book/07-solo.md").read_text()
        self.assertEqual(chapters["C07"]["text"], text.split('<a id="j037"></a>', 1)[0].strip())
        self.assertIn(chapters["C07"]["text"], self.outputs["llms-full.txt"])
        html = build.markdown(text, "book/07-solo.md")
        for anchor in ("solo-own-pace", "solo-walden", "solo-room",
                       "solo-availability", "solo-not-audition"):
            self.assertIn('id="' + anchor + '"', html)
            self.assertIn('href="#' + anchor + '"', html)
        for identifier, anchor in (("F47", "solo-walden"), ("F48", "solo-room")):
            note = notes[identifier]
            self.assertEqual(note["source_kind"], "literary_primary_text")
            self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
            self.assertIn(note["text"], self.outputs["llms-full.txt"])
            self.assertIn('href="#' + identifier.lower() + '"', html)
            self.assertIn('href="#' + anchor + '"',
                          build.markdown(note["text"], note["source"]))
        self.assertIn('href="#n06"', html)
        self.assertEqual(re.findall(r"<!-- pick: .*?\"id\":\"(J\d+)\"", text),
                         [f"J{i:03d}" for i in range(37, 43)])
        self.assertTrue(all(not ({"F47", "F48"} & set(c["background_ids"]))
                            for c in self.export["cards"]))

    def test_solitude_machine_policy_keeps_text_and_research_distinct(self):
        walden = (ROOT / "docs/evidence/F47-walden-solitude.md").read_text()
        room = (ROOT / "docs/evidence/F48-room-and-freedom.md").read_text()
        self.assertIn("不是通读整本", walden)
        self.assertIn("不是全书通读", room)
        self.assertIn("虚构地点", room)
        for path in ("docs/reading-map.md",):
            self.assertIn("C07/F47/F48/B06", (ROOT / path).read_text())

    def test_cross_file_chapter_anchors_stay_local_only_when_explicit(self):
        for fragment in ("solo-room", "solo-walden"):
            self.assertEqual(build.local_href("../../book/07-solo.md#" + fragment,
                                              "docs/evidence/F48-room-and-freedom.md"),
                             "#" + fragment)
        self.assertEqual(build.local_href("../book/32-puzzles.md#puzzle-invariants",
                                          "docs/research.md"), "#puzzle-invariants")
        self.assertEqual(build.local_href("../book/07-solo.md#not-an-explicit-anchor",
                                          "docs/research.md"),
                         "https://github.com/solomon-8/EnjoyTheMoment/blob/main/"
                         "book/07-solo.md#not-an-explicit-anchor")

    def test_puzzle_structures_export_conditions_and_folded_answers(self):
        chapters = {c["id"]: c for c in json.loads(self.outputs["data/chapters.json"])["chapters"]}
        notes = {n["id"]: n for n in json.loads(self.outputs["data/evidence.json"])["notes"]}
        text = (ROOT / "book/32-puzzles.md").read_text()
        self.assertEqual(chapters["C32"]["text"], text.strip())
        self.assertIn(text, self.outputs["llms-full.txt"])
        html = build.markdown(text, "book/32-puzzles.md")
        for anchor in ("puzzle-cards", "puzzle-roads", "puzzle-invariants",
                       "puzzle-rule-change", "puzzle-knowing"):
            self.assertIn('id="' + anchor + '"', html)
            self.assertIn('href="#' + anchor + '"', html)
        note = notes["F46"]
        self.assertEqual(note["source_kind"], "mathematics_textbook_and_original_examples")
        self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
        self.assertIn(note["text"], self.outputs["llms-full.txt"])
        self.assertIn('href="#f46"', html)
        self.assertIn('href="#c32"', build.markdown(note["text"], note["source"]))
        self.assertEqual(html.count("<details>"), 8)
        self.assertNotIn("<details open", html)
        folds = re.findall(r"<details>(.*?)</details>", text, re.S)
        self.assertIn("B → A → C → B → D → C", folds[5])
        self.assertIn("00000 → 11000 → 10100 → 10010 → 10001", folds[6])
        self.assertIn("8个可达状态", folds[7])
        for marker in ("有边地点连通", "却已不足以保证可达", "不是实际景区路线",
                       "不要求接电", "必要条件"):
            self.assertIn(marker, text)
        self.assertEqual(html.count('src="data:image/png;base64,'), 1)
        figures = re.findall(r"!\[([^\]]+)\]\(([^)]+)\)", text)
        self.assertEqual(len(figures), 1)
        self.assertGreater(len(figures[0][0]), 100)
        self.assertTrue(all("F46" not in card["background_ids"] for card in self.export["cards"]))
        for marker in ("2018-06-06", "1,048", "17th century", "未读取Euler论文",
                       "未核读该习题", "63个", "32种", "16个", "8个"):
            self.assertIn(marker, note["text"])

    def test_celebration_spoilers_dates_and_evidence_limits(self):
        text = (ROOT / "book/18-celebration.md").read_text()
        html = build.markdown(text, "book/18-celebration.md")
        self.assertEqual(html.count("<details>"), 1)
        self.assertNotIn("<details open", html)
        folded = text.split("<details>", 1)[1].split("</details>", 1)[0]
        self.assertIn("自己卖掉了金表来买发梳", folded)
        for marker in ("欣赏一种付出，与取得要求别人付出的权利",
                       "不等于送礼说明书", "必购清单"):
            self.assertIn(marker, text)
        festival = (ROOT / "docs/evidence/F44-festival-and-time.md").read_text()
        magi = (ROOT / "docs/evidence/F45-magi-and-giving.md").read_text()
        for marker in ("02126", "19.COM 7.b.29", "2024-12-13", "12 月 4 日",
                       "并非三次独立", "不是经过对照或追踪"):
            self.assertIn(marker, festival)
        for marker in ("2021-12-24", "2021-12-25", "相差一天", "全文",
                       "不是小说首刊日期", "不能得出昂贵礼物更感人"):
            self.assertIn(marker, magi)
        for path in ("docs/reading-map.md",):
            self.assertIn("F44/F45", (ROOT / path).read_text())

    def test_live_chapter_and_sources_export_without_turning_into_card_evidence(self):
        chapters = {c["id"]: c for c in json.loads(self.outputs["data/chapters.json"])["chapters"]}
        notes = {n["id"]: n for n in json.loads(self.outputs["data/evidence.json"])["notes"]}
        source = "book/13-live-events.md"
        text = (ROOT / source).read_text()
        self.assertEqual(chapters["C13"]["text"], text.strip())
        self.assertEqual(chapters["C13"]["scope"], "full_chapter")
        self.assertEqual(chapters["C13"]["card_ids"], [])
        self.assertIn(text, self.outputs["llms-full.txt"])
        html = build.markdown(text, source)
        for anchor in ("live-medium", "live-space", "live-convention",
                       "live-anticipation", "live-understanding"):
            self.assertIn('id="' + anchor + '"', html)
            self.assertIn('href="#' + anchor + '"', html)
        for identifier, kind in (("F40", "theatre_educational_reference"),
                                 ("F41", "heritage_description_and_nomination")):
            note = notes[identifier]
            self.assertEqual(note["source_kind"], kind)
            self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
            self.assertIn(note["text"], self.outputs["llms-full.txt"])
            self.assertIn('href="#' + identifier.lower() + '"', html)
            self.assertIn('href="#c13"', build.markdown(note["text"], note["source"]))
        self.assertIn('href="#f04"', html)
        self.assertTrue(all(not ({"F40", "F41"} & set(c["background_ids"]))
                            for c in self.export["cards"]))

    def test_live_diagram_is_original_local_and_accessible(self):
        source = "book/13-live-events.md"
        text = (ROOT / source).read_text()
        figures = re.findall(r"!\[([^\]]+)\]\(([^)]+)\)", text)
        self.assertEqual(len(figures), 1)
        alt, href = figures[0]
        for phrase in ("镜框式", "三侧", "四周", "不是实际场馆座位图"):
            self.assertIn(phrase, alt)
        self.assertTrue((ROOT / "book" / href).is_file())
        html = build.markdown(text, source)
        self.assertEqual(html.count('src="data:image/png;base64,'), 1)
        svg = ET.parse(ROOT / "assets/media/theatre-layouts.svg").getroot()
        ns = {"s": "http://www.w3.org/2000/svg"}
        self.assertEqual(svg.get("viewBox"), "0 0 440 900")
        self.assertIn("不按比例", svg.find("s:desc", ns).text)
        self.assertEqual(svg.findall(".//s:image", ns), [])
        self.assertIn("theatre-layouts.png", (ROOT / "assets/media/README.md").read_text())

    def test_live_sources_preserve_description_and_performance_boundary(self):
        text = (ROOT / "book/13-live-events.md").read_text()
        for phrase in ("作品", "这一次实现", "自己的在场关系", "黑匣子",
                       "不是某出京剧的舞台实录", "不用功也有资格，用功也可以只是享乐",
                       "没有观看并核验一场实际京剧演出"):
            self.assertIn(phrase, text)
        note = (ROOT / "docs/evidence/F41-jingju-conventions.md").read_text()
        for phrase in ("00418", "2010", "第 3—4 页", "第 5—11 页不作为",
                       "不把两者加申报文件说成三项独立实证研究", "不对应《三岔口》"):
            self.assertIn(phrase, note)
        space = (ROOT / "docs/evidence/F40-theatre-space.md").read_text()
        for phrase in ("不固定等于", "不是互斥分类", "没有在真实场馆测量",
                       "不能用于选座推荐"):
            self.assertIn(phrase, space)

    def test_collecting_official_images_preserve_download_bytes_and_attribution(self):
        source = "book/26-collecting.md"
        text = (ROOT / source).read_text()
        figures = re.findall(r"!\[([^\]]+)\]\(([^)]+)\)", text)
        self.assertEqual(len(figures), 2)
        rendered = build.markdown(text, source)
        self.assertEqual(rendered.count('src="data:image/jpeg;base64,'), 2)
        self.assertEqual(rendered.count('<figure class="artwork">'), 2)
        expected = {
            "rembrandt-three-crosses-41-1-31.jpg":
                "349980d9db7fa6e83f8790a0665ffba6d436115ff58c14b62e9b0cb113333915",
            "rembrandt-three-crosses-41-1-33.jpg":
                "295635b81df098ad6c8073d1775deae84c7fc9a81a039cf077377bccb2895a2e",
        }
        for alt, href in figures:
            path = ROOT / "book" / href
            self.assertGreater(len(alt), 50)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected[path.name])
        phrase = "Gift of Felix M. Warburg and his family, 1941"
        for path in ("assets/art/README.md", "docs/sources.md",
                     "docs/evidence/F38-print-comparison.md"):
            self.assertIn(phrase, (ROOT / path).read_text())
        self.assertIn("A/B标签", (ROOT / "docs/sources.md").read_text())

    def test_collecting_preserves_measurement_and_archiving_scope(self):
        text = (ROOT / "book/26-collecting.md").read_text()
        note = (ROOT / "docs/evidence/F38-print-comparison.md").read_text()
        for marker in ("41.1.31", "41.1.33", "38.1 × 43.8",
                       "38.4 × 44.3", "38.2 × 44.4", "ca. 1660",
                       "不算第二个独立机构来源", "不是历史编号"):
            self.assertIn(marker, note)
        for marker in ("约 1660", "A、B 只区分眼前对象", "毛刺", "不是鉴定流程"):
            self.assertIn(marker, text)
        archive = (ROOT / "docs/evidence/F39-digital-collections.md").read_text()
        for marker in ("至少每年检查一次", "每五年或必要时", "没有显示可核实的发布",
                       "不是核验过的当前产品比较", "没有观看或阅读"):
            self.assertIn(marker, archive)
        for marker in ("技术质量与版本意义不是同一条轴", "完全相同的一份备用副本",
                       "同一块存储介质", "不是做过一次便永久安全",
                       "以后不许花钱"):
            self.assertIn(marker, text)
        self.assertIn("不按文件名、像素或大小替用户删除数据", (ROOT / "docs/reading-map.md").read_text())

    def test_artwork_images_are_local_accessible_and_not_raw_html(self):
        source = "book/25-looking-at-art.md"
        text = (ROOT / source).read_text()
        figures = re.findall(r"!\[([^\]]+)\]\(([^)]+)\)", text)
        self.assertEqual(len(figures), 3)
        rendered = build.markdown(text, source)
        self.assertEqual(rendered.count('<figure class="artwork">'), 3)
        self.assertEqual(rendered.count('loading="lazy"'), 3)
        for alt, href in figures:
            self.assertGreater(len(alt), 30)
            self.assertTrue((ROOT / "book" / href).is_file())
        self.assertEqual(rendered.count('src="data:image/jpeg;base64,'), 3)
        self.assertNotIn('src="assets/', rendered)
        escaped = build.markdown('![<tag> "quote"](../assets/art/van-gogh-bedroom.jpg)', source)
        self.assertIn('alt="&lt;tag&gt; &quot;quote&quot;"', escaped)
        for bad in ("https://example.com/tracker.jpg", "../README.md",
                    "../assets/cover.svg", "../assets/art/missing.jpg",
                    "../assets/art/../../README.md"):
            with self.assertRaises(ValueError):
                build.markdown("![不可信图片](" + bad + ")", source)

    def test_art_and_collecting_keep_object_facts_separate_from_interpretation(self):
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        self.assertEqual(notes["F13"]["source_kind"], "artwork_record_and_image")
        self.assertEqual(notes["F14"]["source_kind"], "educational_reference")
        for fragment in ("1926.417", "1926.224", "1981.15", "未把所有高分辨率区域逐块审核",
                         "不是现场观展报告", "CC BY 4.0", "没有推断它们在核读日都正在展出"):
            self.assertIn(fragment, notes["F13"]["text"])
        self.assertIn("不是藏品鉴定", notes["F14"]["text"])
        self.assertIn("分母不能单独排除其他留样", notes["F14"]["text"])
        self.assertEqual(build.local_href("../docs/evidence/F13-artworks.md",
                                          "book/25-looking-at-art.md"), "#f13")
        self.assertEqual(build.local_href("../docs/evidence/F14-editions.md",
                                          "book/26-collecting.md"), "#f14")
        chapters = {item["id"]: item for item in json.loads(self.outputs["data/chapters.json"])["chapters"]}
        self.assertIn("不是在报道某场真实展览", chapters["C25"]["text"])
        self.assertIn("下面是虚构例子", chapters["C26"]["text"])
        self.assertIn("不提供价格预测、鉴定结论或投资建议", chapters["C26"]["text"])

    def test_art_letters_conservation_and_reactions_stay_distinct(self):
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        chapters = {item["id"]: item for item in json.loads(self.outputs["data/chapters.json"])["chapters"]}
        self.assertEqual(notes["F54"]["source_kind"], "artist_letters_in_scholarly_edition")
        self.assertEqual(notes["F55"]["source_kind"], "museum_conservation_explainer")
        for phrase in ("没有逐字核读法文原文", "两封信的日期来自编辑判断",
                       "706致Gauguin", "705的对应措辞并不完全相同",
                       "后来的版本沿用了", "不是观众实验"):
            self.assertIn(phrase, notes["F54"]["text"])
        for phrase in ("不是完整实验报告", "不计为四项独立实验",
                       "没有独立读取那封完整书信", "没有核看显微照片",
                       "不采用其年限作为普遍预测", "没有新增到仓库",
                       "800 × 634", "1888年10月"):
            self.assertIn(phrase, notes["F55"]["text"])
        chapter = chapters["C25"]
        self.assertNotIn("木地板", chapter["text"])
        for phrase in ("不是上方芝加哥所藏的1889年第二版", "只凭这些条纹",
                       "旧补色", "不是实验完整报告", "耍起不是反对费心",
                       "不是用屏幕测量原作颜料的厚度"):
            self.assertIn(phrase, chapter["text"])
        rendered = build.markdown(chapter["text"], chapter["source"])
        self.assertEqual(rendered.count("<table>"), 3)
        self.assertEqual(rendered.count('<figure class="artwork">'), 3)
        for anchor in ("art-letters-and-versions", "art-material-history",
                       "art-traces-and-meaning", "art-knowledge-and-pleasure"):
            self.assertIn('<span id="' + anchor + '"></span>', rendered)
        for identifier, path, anchor in (
            ("F54", "F54-bedroom-letters.md", "art-letters-and-versions"),
            ("F55", "F55-bedroom-conservation.md", "art-material-history")
        ):
            self.assertEqual(build.local_href("../docs/evidence/" + path,
                                              chapter["source"]), "#" + identifier.lower())
            self.assertEqual(build.local_href("../../book/25-looking-at-art.md#" + anchor,
                                              notes[identifier]["source"]), "#" + anchor)
        self.assertTrue(all(not ({"F54", "F55"} & set(card["background_ids"]))
                            for card in self.export["cards"]))
        for path in ("docs/reading-map.md",):
            self.assertIn("C25/F13/F54/F55", (ROOT / path).read_text())

    def test_music_and_film_media_are_local_and_described(self):
        for path, count, mime in (("book/11-music.md", 2, "png"),
                                  ("book/12-film.md", 3, "jpeg")):
            text = (ROOT / path).read_text()
            figures = re.findall(r"!\[([^\]]+)\]\(([^)]+)\)", text)
            self.assertEqual(len(figures), count)
            for alt, href in figures:
                self.assertGreater(len(alt), 30)
                self.assertTrue((ROOT / Path(path).parent / href).is_file())
            rendered = build.markdown(text, path)
            self.assertEqual(rendered.count('src="data:image/' + mime + ';base64,'), count)
            self.assertNotIn('src="https:', rendered)
        for href in ("../assets/media/../../README.md", "../assets/media/missing.png",
                     "../assets/media/README.md", "https://example.com/film.jpg"):
            with self.assertRaises(ValueError):
                build.markdown("![外部或非图片素材](" + href + ")", "book/12-film.md")

    def test_media_bytes_and_attribution_affect_source_digest(self):
        baseline = build.source_digest(ROOT)
        original = Path.read_bytes
        for name in ("bach-opening.png", "train-closeup.jpg", "README.md",
                     "photo-viewpoint.svg", "photo-viewpoint.png",
                     "photo-duration.svg", "photo-duration.png"):
            target = ROOT / "assets/media" / name
            def changed_read(path):
                value = original(path)
                return value + b"\nchanged" if path == target else value
            with mock.patch.object(Path, "read_bytes", changed_read):
                self.assertNotEqual(build.source_digest(ROOT), baseline)

    def test_score_and_film_sources_keep_observation_limits(self):
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        self.assertEqual(notes["F15"]["source_kind"], "musical_score")
        self.assertEqual(notes["F16"]["source_kind"], "film_and_historical_catalog")
        for text in ("Unknown", "没有实际试听", "不是录音评测", "2017/11/05-941"):
            self.assertIn(text, notes["F15"]["text"])
        for text in ("不是连续完整播放", "807.708", "没有音轨", "开头或末尾", "不是测量过多少观众"):
            self.assertIn(text, notes["F16"]["text"])
        self.assertEqual(build.local_href("../docs/evidence/F15-musical-scores.md", "book/11-music.md"), "#f15")
        self.assertEqual(build.local_href("../docs/evidence/F16-train-robbery.md", "book/12-film.md"), "#f16")
        self.assertEqual(len(json.loads(self.outputs["data/research.json"])["records"]), 26)

    def test_film_ending_is_inside_opt_in_spoiler_block(self):
        text = (ROOT / "book/12-film.md").read_text()
        start, end = text.index("<details>"), text.index("</details>")
        self.assertLess(start, text.index("train-closeup.jpg"))
        self.assertGreater(end, text.index("开头或结尾"))
        rendered = build.markdown(text, "book/12-film.md")
        self.assertEqual(rendered.count("<details>"), 1)
        self.assertNotIn("<details open", rendered)

    def test_dance_sources_are_not_performance_or_health_claims(self):
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        note = notes["F17"]
        self.assertEqual(note["source_kind"], "dance_education_and_work_record")
        for phrase in ("Version 1.3 June 2026", "没有观看并核验完整演出", "不把考试标准",
                       "本书原创构作", "不是享乐效果研究"):
            self.assertIn(phrase, note["text"])
        self.assertEqual(build.local_href("../docs/evidence/F17-dance-language.md", "book/27-dance.md"), "#f17")

    def test_dance_timeline_preserves_individual_material_and_changes_relations(self):
        import dance_examples
        together = dance_examples.timeline((0, 0, 0))
        staggered = dance_examples.timeline((0, 1, 2))
        self.assertEqual(together, (("P", "Q", "R", ".", "."),) * 3)
        self.assertEqual(staggered, (("P", "Q", "R", ".", "."),
                                     (".", "P", "Q", "R", "."),
                                     (".", ".", "P", "Q", "R")))
        for grid in (together, staggered):
            self.assertEqual(sum(v != "." for row in grid for v in row), 9)
            self.assertTrue(all(tuple(v for v in row if v != ".") == ("P", "Q", "R")
                                for row in grid))
        self.assertEqual(tuple(row[2] for row in staggered), ("R", "Q", "P"))
        with self.assertRaises(ValueError):
            dance_examples.timeline((0, 3))
        with self.assertRaises(ValueError):
            dance_examples.timeline((-1,))
        svg = (ROOT / "assets/media/dance-time-grid.svg").read_text()
        self.assertEqual(svg, dance_examples.svg())
        root = ET.fromstring(svg)
        self.assertEqual(root.attrib["viewBox"], "0 0 720 1080")
        cells = [el for el in root.iter() if "data-value" in el.attrib]
        self.assertEqual(len(cells), 30)
        for el in cells:
            grid = together if el.attrib["data-panel"] == "unison" else staggered
            self.assertEqual(el.attrib["data-value"],
                             grid[int(el.attrib["data-row"])][int(el.attrib["data-slot"]) - 1])
        for forbidden in ("<script", "<animate", "<image"):
            self.assertNotIn(forbidden, svg)

    def test_dance_chance_rules_have_distinct_exact_distributions(self):
        import dance_examples
        permutations = tuple(itertools.permutations(("P", "Q", "R")))
        self.assertEqual(len(permutations), 6)
        allowed = dance_examples.allowed_orders()
        self.assertEqual(allowed, (("P", "Q", "R"), ("P", "R", "Q"), ("R", "P", "Q")))
        by_order, by_first = dance_examples.distributions()
        self.assertEqual(set(by_order), set(allowed))
        self.assertEqual(set(by_first), set(allowed))
        self.assertEqual(sum(by_order.values()), 1)
        self.assertEqual(sum(by_first.values()), 1)
        self.assertEqual(set(by_order.values()), {Fraction(1, 3)})
        self.assertEqual(by_first, {("P", "Q", "R"): Fraction(1, 4),
                                   ("P", "R", "Q"): Fraction(1, 4),
                                   ("R", "P", "Q"): Fraction(1, 2)})
        self.assertEqual(sum(p for order, p in by_order.items() if order[0] == "P"),
                         Fraction(2, 3))
        self.assertEqual(sum(p for order, p in by_first.items() if order[0] == "P"),
                         Fraction(1, 2))

    def test_dance_work_records_and_original_diagram_survive_exports(self):
        notes = {n["id"]: n for n in json.loads(self.outputs["data/evidence.json"])["notes"]}
        chapter = next(c for c in json.loads(self.outputs["data/chapters.json"])["chapters"]
                       if c["id"] == "C27")
        text = (ROOT / "book/27-dance.md").read_text()
        self.assertEqual(chapter["text"], text.strip())
        self.assertIn(chapter["text"], self.outputs["llms-full.txt"])
        for identifier, kind, anchor in (
            ("F51", "creator_work_and_participation_record", "dance-rosas"),
            ("F52", "artist_trust_work_and_method_record", "dance-chance"),
        ):
            note = notes[identifier]
            self.assertEqual(note["source_kind"], kind)
            self.assertEqual(note["text"], (ROOT / note["source"]).read_text())
            self.assertIn(note["text"], self.outputs["llms-full.txt"])
            self.assertIn('href="#' + identifier.lower() + '"', self.outputs["index.html"])
            self.assertIn('href="#' + anchor + '"', build.markdown(note["text"], note["source"]))
        for phrase in ("未观看并核验完整演出", "简化版本", "不是该作动作或舞谱的复原"):
            self.assertIn(phrase, notes["F51"]["text"])
        for phrase in ("舞团成立", "没有取得那些图表", "不是Cunningham使用过的算法", "1/4"):
            self.assertIn(phrase, notes["F52"]["text"])
        for anchor in ("dance-time-grid", "dance-rosas", "dance-remix", "dance-chance"):
            self.assertEqual(self.outputs["index.html"].count('id="' + anchor + '"'), 1)
        html = build.markdown(text, "book/27-dance.md")
        self.assertEqual(html.count('src="data:image/png;base64,'), 1)
        alt = re.search(r"!\[([^\]]+)\]\(\.\./assets/media/dance-time-grid.png\)", text).group(1)
        for marker in ("第1至第5格", "第3格甲为R", "不指定其他姿势", "没有动画"):
            self.assertIn(marker, alt)
        self.assertTrue(all(not ({"F51", "F52"} & set(c["background_ids"]))
                            for c in self.export["cards"]))
        for path in ("docs/reading-map.md",):
            self.assertIn("C27/F51/F52", (ROOT / path).read_text())

    def test_sport_sources_preserve_versions_and_decision_conditions(self):
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        for identifier in ("F18", "F19"):
            self.assertEqual(notes[identifier]["source_kind"], "official_sport_rules")
        for phrase in ("2026/27", "`latest`", "位置本身不是犯规", "门将用手抛球时采用最后接触点",
                       "直接接到", "最低补时"):
            self.assertIn(phrase, notes["F18"]["text"])
        for phrase in ("2026-09-30", "2026-10-01", "生效日尚未到来", "14 秒", "24 秒",
                       "触及对方篮圈", "本书虚构假设", "不是 NBA"):
            self.assertIn(phrase, notes["F19"]["text"])
        self.assertEqual(len(json.loads(self.outputs["data/research.json"])["records"]), 26)
        self.assertEqual(build.local_href("../docs/evidence/F19-basketball-rules.md", "book/28-watching-sport.md"), "#f19")

    def test_sport_illustration_and_hypothetical_math_are_explicit(self):
        text = (ROOT / "book/28-watching-sport.md").read_text()
        self.assertIn("本书的虚构算例，不是球员统计或球队预测", text)
        for points, probability, expected in re.findall(r"(\d) × (0\.\d+) = (1\.\d+)", text):
            self.assertAlmostEqual(int(points) * float(probability), float(expected))
        self.assertEqual(len(re.findall(r"\d × 0\.\d+ = 1\.\d+", text)), 2)
        self.assertIn("甲、乙是同一次传球的两个时点，丙是另一个情形", text)
        rendered = build.markdown(text, "book/28-watching-sport.md")
        self.assertEqual(rendered.count('src="data:image/png;base64,'), 1)
        self.assertTrue((ROOT / "assets/media/offside-timing.svg").is_file())
        diagram = (ROOT / "assets/media/offside-timing.svg").read_text()
        self.assertIn("本书原创位置示意", diagram)
        self.assertIn('viewBox="0 0 440 960"', diagram)
        self.assertGreaterEqual(min(map(int, re.findall(r'font-size="(\d+)"', diagram))), 22)

    def test_spoilers_allow_only_fixed_safe_html(self):
        result = build.markdown("<details>\n<summary>答案</summary>\n\n内容\n\n</details>", "README.md")
        self.assertIn("<details>", result)
        self.assertIn("<summary>答案</summary>", result)
        self.assertNotIn('<details onclick=', build.markdown('<details onclick="bad()">', "README.md"))

    def test_richness_proof_preserves_version_and_counterevidence(self):
        records = {item["id"]: item for item in json.loads(self.outputs["data/research.json"])["records"]}
        richness = records["B03"]
        self.assertEqual(richness["access_level"], "full_text")
        self.assertIn("页校样", richness["fields"]["版本边界"])
        self.assertIn("不冒充已核验的期刊最终版", richness["fields"]["版本边界"])
        self.assertIn("即时满足比延迟更好", richness["fields"]["不能推出"])
        self.assertIn("p = .05", richness["fields"]["关键限制"])
        self.assertIn("p = .44", richness["fields"]["关键限制"])
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        self.assertEqual(notes["N03"]["source_kind"], "study_reading_note")
        self.assertIn("德国为 49.7%", notes["N03"]["text"])
        self.assertIn("这不是问他们是否最偏爱丰富人生", notes["N03"]["text"])
        self.assertEqual(build.local_href("../docs/evidence/B03-richness.md",
                                          "essays/02-excitement-without-escalation.md"), "#n03")

    def test_flavor_and_public_space_sources_keep_nonexperimental_kinds(self):
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        self.assertEqual(notes["F05"]["source_kind"], "official_explainer")
        self.assertEqual(notes["F06"]["source_kind"], "practice_framework")
        self.assertIn("没有进行盲品", notes["F05"]["text"])
        self.assertIn("没有实地评估任何街区", notes["F06"]["text"])
        studies = {item["id"] for item in json.loads(self.outputs["data/research.json"])["records"]}
        self.assertTrue({"F05", "F06"}.isdisjoint(studies))
        for chapter, note, path in [
            ("14-flavor.md", "F05-flavor.md", "#f05"),
            ("15-neighborhood.md", "F06-public-space.md", "#f06"),
        ]:
            self.assertEqual(build.local_href("../docs/evidence/" + note, "book/" + chapter), path)

    def test_value_answers_are_not_forced_into_activity_card_format(self):
        protocol = (ROOT / "docs/ai.md").read_text()
        self.assertIn("引用行动卡时必须保留", protocol)
        self.assertIn("回答价值与生活问题时，不套用行动卡格式", protocol)
        self.assertNotIn("每条回答必须保留", protocol)

    def test_making_and_rituals_keep_outcomes_and_null_results_distinct(self):
        records = {item["id"]: item for item in json.loads(self.outputs["data/research.json"])["records"]}
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        self.assertIn("不是制作过程快乐的直接测量", records["B07"]["fields"]["有限结论"])
        self.assertIn("p > .60", records["B07"]["fields"]["关键限制"])
        self.assertIn("盲评认为两种作品质量相当", notes["N07"]["text"])
        self.assertIn("Crossmark 返回该内容暂无数据", notes["N07"]["text"])
        for text in ("p = .06", "p = .053", "p = .23", "F < 1"):
            self.assertIn(text, records["B08"]["fields"]["关键限制"])
        self.assertIn("current，不是可靠性或复现认证", records["B08"]["fields"]["关键限制"])
        self.assertIn("没有无仪式组", notes["N08"]["text"])
        self.assertIn("内在兴趣没有被独立随机操纵", notes["N08"]["text"])
        self.assertEqual(notes["N07"]["source_kind"], "study_reading_note")
        self.assertEqual(notes["N08"]["source_kind"], "study_reading_note")
        self.assertTrue(all("B07" not in card["background_ids"] and "B08" not in card["background_ids"]
                            for card in self.export["cards"]))

    def test_textile_teaching_and_care_page_do_not_claim_full_standard(self):
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        self.assertEqual(notes["F07"]["source_kind"], "educational_reference")
        self.assertEqual(notes["F08"]["source_kind"], "technical_guidance")
        self.assertIn("没有取得并完整审核 ISO 标准原文", notes["F08"]["text"])
        self.assertIn("不提供温度速查表", notes["F08"]["text"])
        self.assertIn("没有测试材料强度", notes["F07"]["text"])
        for chapter, note, anchor in [
            ("16-dress.md", "F08-textile-care.md", "#f08"),
            ("17-making.md", "F07-textiles.md", "#f07"),
            ("18-celebration.md", "B08-rituals.md", "#n08"),
        ]:
            self.assertEqual(build.local_href("../docs/evidence/" + note, "book/" + chapter), anchor)

    def test_games_keep_observation_missingness_and_motivation_boundaries(self):
        records = {item["id"]: item for item in json.loads(self.outputs["data/research.json"])["records"]}
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        self.assertIn("不是随机实验", records["B09"]["fields"]["设计与对象"])
        self.assertIn("未预注册", records["B09"]["fields"]["关键限制"])
        self.assertIn("[−0.01, 0.18]", records["B09"]["fields"]["关键限制"])
        self.assertIn("部分估计的方向随之改变", notes["N09"]["text"])
        self.assertIn("不是 38,935 人都完成三轮", notes["N09"]["text"])
        self.assertEqual(notes["F09"]["source_kind"], "technical_guidance")
        self.assertIn("不证明目前每个产品", notes["F09"]["text"])

    def test_photography_preserves_version_nulls_and_outcome_distinctions(self):
        records = {item["id"]: item for item in json.loads(self.outputs["data/research.json"])["records"]}
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        self.assertIn("提前在线发表稿", records["B10"]["fields"]["实际读取"])
        self.assertIn("不能一概称逐人随机分配", records["B10"]["fields"]["设计与对象"])
        for text in ("p = .133", "p = .067", "p = .373", "p = .058"):
            self.assertIn(text, records["B10"]["fields"]["关键限制"])
        self.assertIn("p = .091", notes["N10"]["text"])
        self.assertIn("记得自己当时多享受，与准确记住发生过什么", notes["N10"]["text"])
        self.assertEqual(notes["F10"]["source_kind"], "educational_reference")
        self.assertTrue(all(not ({"B09", "B10"} & set(card["background_ids"])) for card in self.export["cards"]))
        for chapter, note, anchor in [
            ("19-games.md", "B09-games.md", "#n09"),
            ("19-games.md", "F09-game-difficulty.md", "#f09"),
            ("20-photography.md", "B10-photography.md", "#n10"),
            ("20-photography.md", "F10-photography-language.md", "#f10"),
        ]:
            self.assertEqual(build.local_href("../docs/evidence/" + note, "book/" + chapter), anchor)

    def test_offline_evidence_navigation(self):
        self.assertEqual(build.local_href("../docs/evidence/B04-anticipation.md",
                                          "essays/03-now-or-later.md"), "#n04")
        self.assertEqual(build.local_href("README.md", "guides/01-word-studio.md"), "#playbooks")

    def test_scheduling_keeps_attendance_selection_and_nulls(self):
        records = {item["id"]: item for item in json.loads(self.outputs["data/research.json"])["records"]}
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        for text in ("发券 148、兑换 54", "p > .10", "p = .06", "未完整读取网络附录"):
            self.assertIn(text, records["B11"]["fields"]["关键限制"])
        self.assertIn("明确时点组到场比例更高", records["B11"]["fields"]["有限结论"])
        self.assertIn("给未到场者擅自补一个零分", notes["N11"]["text"])
        self.assertIn("并非同一活动只改变", notes["N11"]["text"])
        self.assertEqual(notes["N11"]["source_kind"], "study_reading_note")
        self.assertTrue(all("B11" not in card["background_ids"] for card in self.export["cards"]))
        self.assertEqual(build.local_href("../docs/evidence/B11-scheduling.md",
                                          "book/21-free-time.md"), "#n11")

    def test_literary_text_is_not_study_or_authorial_testimony(self):
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        note = notes["F11"]
        self.assertEqual(note["source_kind"], "literary_primary_text")
        self.assertIn("没有把下载全本说成逐字核读全书", note["text"])
        self.assertIn("未完成版本谱系及异文校勘", note["text"])
        self.assertIn("不是作者本人解释", note["text"])
        chapter = next(c for c in json.loads(self.outputs["data/chapters.json"])["chapters"]
                       if c["id"] == "C22")
        self.assertIn("他等了很久，她没有来", chapter["text"])
        self.assertIn("不是文学作品引文", chapter["text"])
        rendered = build.markdown(chapter["text"], chapter["source"])
        self.assertIn("<table>", rendered)
        self.assertEqual(build.local_href("../docs/evidence/F11-reading-texts.md",
                                          "book/22-reading.md"), "#f11")

    def test_search_is_and_match(self):
        matches = pick.filter_cards(pick.load_cards(), 1000, 1000, query="游戏 结束")
        self.assertGreater(len(matches), 0)
        for card in matches:
            self.assertIn("游戏", card.title + card.body)
            self.assertIn("结束", card.title + card.body)

    def test_reading_inference_keeps_claims_and_spoilers_scoped(self):
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        note = notes["F53"]
        self.assertEqual(note["source_kind"], "literary_primary_text")
        for phrase in ("没有通读整本短篇集", "事故是她所述",
                       "不是已被来客证实的恐犬病史", "不是心理实验",
                       "作者说明", "2011-12-26"):
            self.assertIn(phrase, note["text"])
        chapter = next(c for c in json.loads(self.outputs["data/chapters.json"])["chapters"]
                       if c["id"] == "C22")
        self.assertIn("搭在手臂上", chapter["text"])
        self.assertIn("披在肩上", chapter["text"])
        self.assertIn("好笑与残忍，可以同时成立", chapter["text"])
        self.assertIn("有些时间不是信息运送得太慢", chapter["text"])
        for text in (chapter["text"], note["text"]):
            before, after = text.split("<details>", 1)
            spoiler, remainder = after.split("</details>", 1)
            self.assertIn("完整情节与结局", spoiler)
            self.assertIn("恒河", spoiler)
            self.assertNotIn("恒河", before + remainder)
            self.assertNotIn("<details open", text)
        rendered = build.markdown(chapter["text"], chapter["source"])
        self.assertIn('<span id="reading-detail-and-cause"></span>', rendered)
        self.assertIn("<table>", rendered)
        self.assertEqual(build.local_href("../docs/evidence/F53-open-window.md",
                                          "book/22-reading.md"), "#f53")
        self.assertEqual(build.local_href("../../book/22-reading.md#reading-open-window",
                                          note["source"]), "#reading-open-window")
        self.assertTrue(all("F53" not in card["background_ids"] for card in self.export["cards"]))
        for path in ("docs/reading-map.md",):
            text = (ROOT / path).read_text()
            self.assertIn("C22/F", text)
            self.assertIn("F53", text)

    def test_travel_keeps_observation_outcomes_and_scoped_guidance(self):
        records = {item["id"]: item for item in json.loads(self.outputs["data/research.json"])["records"]}
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        self.assertIn("不是随机实验", records["B12"]["fields"]["设计与对象"])
        self.assertIn("仍在旅行的 142 人", records["B12"]["fields"]["设计与对象"])
        self.assertIn("没有旅途中逐段享受测量", records["B12"]["fields"]["关键限制"])
        self.assertIn("没有直接把一年总休假时间固定", notes["N12"]["text"])
        self.assertIn("不是把同一批人逐日追踪八周", notes["N12"]["text"])
        self.assertEqual(notes["F12"]["source_kind"], "official_visitor_guidance")
        self.assertIn("2026-08-21", notes["F12"]["text"])
        self.assertIn("不能被拼接成该来源支持随意离队", notes["F12"]["text"])
        self.assertEqual(build.local_href("../docs/evidence/B12-vacation.md",
                                          "book/23-travel.md"), "#n12")
        self.assertEqual(build.local_href("../docs/evidence/F12-trip-planning.md",
                                          "book/23-travel.md"), "#f12")

    def test_humor_keeps_reported_sample_gap_and_nonclaims(self):
        records = {item["id"]: item for item in json.loads(self.outputs["data/research.json"])["records"]}
        notes = {item["id"]: item for item in json.loads(self.outputs["data/evidence.json"])["notes"]}
        self.assertIn("方法报 73、表 5 跨版本 N = 72", records["B13"]["fields"]["关键限制"])
        self.assertIn("坐标启动，不是时间流逝", records["B13"]["fields"]["关键限制"])
        self.assertIn("不鉴定每个笑容的内心含义", notes["N13"]["text"])
        self.assertIn("不是现实行为已被证明无害", notes["N13"]["text"])
        self.assertTrue(all(not ({"B12", "B13"} & set(c["background_ids"])) for c in self.export["cards"]))
        self.assertEqual(build.local_href("../docs/evidence/B13-humor.md",
                                          "book/24-humor.md"), "#n13")

    def test_travel_example_arithmetic_and_humor_originality_are_preserved(self):
        chapters = {c["id"]: c for c in json.loads(self.outputs["data/chapters.json"])["chapters"]}
        # This checks a specific fictional table, not the accuracy of real itineraries.
        travel = chapters["C23"]["text"]
        rows = re.findall(r"^\| [^|]+ \| (\d+) 分钟 \|$", travel, re.M)
        self.assertEqual(sum(map(int, rows)), 310)
        self.assertIn("**310 分钟**", travel)
        self.assertIn("这些是假设输入，不是当地报价", travel)
        humor = chapters["C24"]["text"]
        self.assertIn("未注明作品出处的例句为本书原创说明", humor)
        self.assertIn("不是受众测试结果", humor)
        self.assertIn("我家的书架已经很有文化了", humor)
        self.assertIn("笑声不能代替同意", (ROOT / "docs/evidence/B13-humor.md").read_text())


if __name__ == "__main__":
    unittest.main()
