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
        self.assertEqual(sum(record["access_level"] == "full_text" for record in research["records"]), 3)
        for card in self.export["cards"]:
            self.assertTrue(card["background_is_not_validation"])
            self.assertTrue(set(card["background_ids"]).issubset(ids))
            self.assertEqual(card["evidence_type"], "original_proposal")
        self.assertTrue(all(not record["directly_validates_cards"] for record in research["records"]))

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
        self.assertEqual(len(chapters), 10)
        for chapter in chapters:
            source = ROOT / chapter["source"]
            introduction = source.read_text().split('<a id="j', 1)[0].strip()
            self.assertEqual(chapter["text"], introduction)
            self.assertEqual(chapter["source_sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertEqual(chapter["scope"], "chapter_introduction")
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

    def test_spoilers_allow_only_fixed_safe_html(self):
        result = build.markdown("<details>\n<summary>答案</summary>\n\n内容\n\n</details>", "README.md")
        self.assertIn("<details>", result)
        self.assertIn("<summary>答案</summary>", result)
        self.assertNotIn('<details onclick=', build.markdown('<details onclick="bad()">', "README.md"))

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
