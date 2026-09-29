import contextlib
import hashlib
import io
import json
import re
import sys
import unittest
from unittest import mock
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
        self.assertEqual(sum(record["access_level"] == "full_text" for record in research["records"]), 13)
        self.assertEqual(ids, {"B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B09", "B10", "B11", "B12", "B13"})
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
        self.assertEqual(len(chapters), 28)
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
                         {"C11", "C12", "C13", "C14", "C15", "C16", "C17", "C18", "C19", "C20", "C21", "C22", "C23", "C24", "C25", "C26", "C27", "C28"})
        for chapter in standalone:
            self.assertEqual(chapter["card_ids"], [])
            self.assertEqual(chapter["text"], (ROOT / chapter["source"]).read_text().strip())
            self.assertEqual(build.local_href(chapter["source"], "README.md"), "#" + chapter["id"].lower())
        self.assertNotIn("<p>配套行动：</p>", self.outputs["index.html"])
        self.assertEqual(len(self.export["cards"]), 60)

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
        for name in ("bach-opening.png", "train-closeup.jpg", "README.md"):
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
        self.assertEqual(len(json.loads(self.outputs["data/research.json"])["records"]), 13)

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
        self.assertEqual(len(json.loads(self.outputs["data/research.json"])["records"]), 13)
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
        self.assertIn("例句均由本书为解释而创作", humor)
        self.assertIn("没有经过受众测试", humor)
        self.assertIn("我家的书架已经很有文化了", humor)
        self.assertIn("笑声不能代替同意", (ROOT / "docs/evidence/B13-humor.md").read_text())


if __name__ == "__main__":
    unittest.main()
