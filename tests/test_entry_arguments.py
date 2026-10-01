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
        self.assertEqual(rendered.count("<h3>"), 4)
        self.assertNotIn("&lt;br", rendered)

    def test_argument_routes_precede_activities_and_work_offline(self):
        page = self.outputs["index.html"]
        self.assertLess(page.index('id="disagreements"'), page.index('id="menu"'))
        excerpt = page.split('id="disagreements"', 1)[1].split("</section>", 1)[0]
        self.assertNotIn("<details", excerpt)
        links = re.findall(r'href="([^"]+)"', excerpt)
        self.assertEqual(len(links), 4)
        for href in links:
            self.assertTrue(href.startswith("#"))
            self.assertEqual(page.count('id="' + href[1:] + '"'), 1)
            self.assertFalse(re.fullmatch(r"#j\d+", href))

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
