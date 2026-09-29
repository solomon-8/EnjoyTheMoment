import contextlib
import io
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import check
import pick


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cards = pick.load_cards()

    def test_nonempty_unique_catalog(self):
        self.assertGreater(len(self.cards), 0)
        self.assertEqual(len(self.cards), len({card.id for card in self.cards}))

    def test_all_local_checks(self):
        problems, count = check.check()
        self.assertEqual(problems, [])
        self.assertEqual(count, len(self.cards))

    def test_zero_budget_solo_low_energy(self):
        matches = pick.filter_cards(self.cards, 20, 0, "solo", "low")
        self.assertGreater(len(matches), 0)
        for card in matches:
            self.assertEqual(card.budget, 0)
            self.assertLessEqual(card.minutes, 20)
            self.assertIn(card.company, {"solo", "either"})
            self.assertEqual(card.energy, "low")

    def test_social_excludes_solo(self):
        matches = pick.filter_cards(self.cards, 1000, 1000, "social")
        self.assertGreater(len(matches), 0)
        self.assertTrue(all(card.company != "solo" for card in matches))

    def test_maximum_energy_is_inclusive(self):
        matches = pick.filter_cards(self.cards, 1000, 1000, energy="medium")
        self.assertTrue(any(card.energy == "low" for card in matches))
        self.assertTrue(any(card.energy == "medium" for card in matches))
        self.assertFalse(any(card.energy == "high" for card in matches))

    def test_no_matches_and_no_upsell(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = pick.main(["--minutes", "0", "--budget", "0"])
        self.assertEqual(code, 0)
        self.assertIn("不必加钱或加时间", output.getvalue())

    def test_reproducible_seed(self):
        outputs = []
        for _ in range(2):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(pick.main(["--seed", "42"]), 0)
            outputs.append(output.getvalue())
        self.assertEqual(outputs[0], outputs[1])

    def test_list_mode(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = pick.main(["--minutes", "5", "--budget", "0", "--list"])
        self.assertEqual(code, 0)
        self.assertIn("匹配", output.getvalue())
        self.assertIn("J001", output.getvalue())

    def test_negative_argument_is_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            pick.main(["--budget", "-1"])
        self.assertEqual(caught.exception.code, 2)

    def test_body_does_not_leak_metadata_or_next_anchor(self):
        for card in self.cards:
            self.assertNotIn("<!-- pick:", card.body)
            self.assertNotRegex(card.body, r'<a id="j\d+">')

    def test_absolute_script_path_works_from_another_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/pick.py"), "--seed", "1", "--minutes", "5"],
                cwd=directory, capture_output=True, text=True, check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("享受当下", result.stdout)

    def test_empty_catalog_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "没有可读取"):
                pick.load_cards(Path(directory))

    def test_duplicate_id_fails(self):
        source = (ROOT / "book/01-start-now.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as directory:
            book = Path(directory) / "book"
            book.mkdir()
            (book / "a.md").write_text(source, encoding="utf-8")
            (book / "b.md").write_text(source, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "编号重复"):
                pick.load_cards(Path(directory))

    def test_invalid_metadata_fails(self):
        source = (ROOT / "book/01-start-now.md").read_text(encoding="utf-8")
        bad = source.replace('"minutes":5', '"minutes":-5', 1)
        with tempfile.TemporaryDirectory() as directory:
            book = Path(directory) / "book"
            book.mkdir()
            (book / "a.md").write_text(bad, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "非负整数"):
                pick.load_cards(Path(directory))

    def test_missing_body_field_fails(self):
        source = (ROOT / "book/01-start-now.md").read_text(encoding="utf-8")
        bad = re.sub(r"^- \*\*散场线\*\*：.+\n", "", source, count=1, flags=re.MULTILINE)
        with tempfile.TemporaryDirectory() as directory:
            book = Path(directory) / "book"
            book.mkdir()
            (book / "a.md").write_text(bad, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "散场线"):
                pick.load_cards(Path(directory))

    def test_code_fence_example_is_not_real_anchor(self):
        text = '# Real heading\n\n```markdown\n<a id="fake"></a>\n# Fake\n```\n'
        self.assertIn("real-heading", check.anchors_for(text))
        self.assertNotIn("fake", check.anchors_for(text))


if __name__ == "__main__":
    unittest.main()
