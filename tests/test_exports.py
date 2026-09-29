import contextlib
import hashlib
import io
import json
import re
import sys
import unittest
from pathlib import Path

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

    def test_background_does_not_validate_cards(self):
        research = json.loads(self.outputs["data/research.json"])
        ids = {record["id"] for record in research["records"]}
        self.assertEqual(sum(record["access_level"] == "full_text" for record in research["records"]), 8)
        self.assertEqual(ids, {"B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08"})
        for card in self.export["cards"]:
            self.assertTrue(card["background_is_not_validation"])
            self.assertTrue(set(card["background_ids"]).issubset(ids))
            self.assertEqual(card["evidence_type"], "original_proposal")
        self.assertTrue(all(not record["directly_validates_cards"] for record in research["records"]))

    def test_both_homepages_keep_research_count_in_sync(self):
        count = len(json.loads(self.outputs["data/research.json"])["records"])
        self.assertIn(f"{count} 篇背景研究", (ROOT / "README.md").read_text())
        self.assertIn(f"{count} background studies", (ROOT / "README.en.md").read_text())

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
        self.assertEqual(len(chapters), 18)
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
                         {"C11", "C12", "C13", "C14", "C15", "C16", "C17", "C18"})
        for chapter in standalone:
            self.assertEqual(chapter["card_ids"], [])
            self.assertEqual(chapter["text"], (ROOT / chapter["source"]).read_text().strip())
            self.assertEqual(build.local_href(chapter["source"], "README.md"), "#" + chapter["id"].lower())
        self.assertNotIn("<p>配套行动：</p>", self.outputs["index.html"])
        self.assertEqual(len(self.export["cards"]), 60)

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

    def test_offline_evidence_navigation(self):
        self.assertEqual(build.local_href("../docs/evidence/B04-anticipation.md",
                                          "essays/03-now-or-later.md"), "#n04")
        self.assertEqual(build.local_href("README.md", "guides/01-word-studio.md"), "#playbooks")

    def test_search_is_and_match(self):
        matches = pick.filter_cards(pick.load_cards(), 1000, 1000, query="游戏 结束")
        self.assertGreater(len(matches), 0)
        for card in matches:
            self.assertIn("游戏", card.title + card.body)
            self.assertIn("结束", card.title + card.body)


if __name__ == "__main__":
    unittest.main()
