"""Behavioral contracts for local reading, not tests of reader comprehension or AI judgment."""
import contextlib
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import check
import read
from reading import load_routes


class ReadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents, cls.routes = read.load_documents(ROOT)
        cls.by_id = {r["id"]: r for r in cls.documents}

    def call(self, *arguments):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = read.main(arguments, ROOT)
        return code, json.loads(output.getvalue())

    def test_complete_canonical_coverage_and_scope(self):
        expected = {"SHUAQI", "CULTURE"}
        expected |= {"C" + p.stem[:2] for p in (ROOT / "book").glob("[0-9][0-9]-*.md")}
        expected |= {identifier for identifier, _ in build.ESSAYS + build.EVIDENCE}
        expected |= {r["id"] for r in build.research_records(ROOT)}
        actual = {r["id"] for r in self.documents if r["kind"] != "route"}
        self.assertEqual(actual, expected)
        self.assertEqual(actual, {i for route in self.routes for i in route["targets"]})
        self.assertEqual(len(self.by_id), len(self.documents))
        self.assertFalse(any(r["kind"] in {"card", "guide"} for r in self.documents))

    def test_every_exact_file_is_complete_and_hash_matches(self):
        for identifier, record in self.by_id.items():
            with self.subTest(identifier=identifier):
                code, result = self.call("--id", identifier.lower())
                self.assertEqual(code, 0)
                self.assertTrue(result["complete"])
                self.assertEqual(result["record"], record)
                if record["scope"] == "full_file":
                    source = ROOT / record["source"]
                    self.assertEqual(record["text"], source.read_text())
                    self.assertEqual(record["source_sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
                expected_guidance = [r for r in self.routes if identifier in r["targets"]]
                self.assertEqual(result["reading_guidance"], expected_guidance)

    def test_chapter_read_includes_cards_not_only_introduction(self):
        _, result = self.call("--id", "C01")
        self.assertIn('<a id="j001"', result["record"]["text"])
        self.assertIn('<a id="j006"', result["record"]["text"])
        self.assertEqual(result["record"]["scope"], "full_file")
        intro = next(r for r in json.loads((ROOT / "data/chapters.json").read_text())["chapters"]
                     if r["id"] == "C01")
        self.assertIn(intro["text"], result["record"]["text"])
        self.assertGreater(len(result["record"]["text"]), len(intro["text"]))

    def test_research_entries_have_all_fields_and_valid_local_anchors(self):
        ledger = (ROOT / "docs/research.md").read_text()
        anchors = check.anchors_for(ledger)
        for record in build.research_records(ROOT):
            item = self.by_id[record["id"]]
            self.assertEqual(item["scope"], "complete_ledger_entry")
            self.assertIn(record["source"].split("#")[1], anchors)
            self.assertEqual(re.findall(r"^## (B\d+) · ", item["text"], re.M), [record["id"]])
            for field, value in record["fields"].items():
                self.assertIn("- **" + field + "**：" + value, item["text"])
            self.assertFalse(item["directly_validates_cards"])
            self.assertEqual(item["verified_at"], record["verified_at"])

    def test_search_is_deterministic_bounded_and_never_returns_body(self):
        first = self.call("--query", "朋友", "--kind", "essay", "--limit", "2")
        self.assertEqual(first, self.call("--query", "朋友", "--kind", "essay", "--limit", "2"))
        code, data = first
        self.assertEqual(code, 0)
        self.assertEqual(data["results"][0]["id"], "E09")
        self.assertEqual(data["returned"], 2)
        self.assertTrue(data["has_more"])
        self.assertFalse(data["complete_text_returned"])
        for item in data["results"]:
            self.assertNotIn("text", item)
            self.assertNotIn("excerpt", item)
            self.assertEqual(item["kind"], "essay")
        _, empty = self.call("--query", "不存在的论点abcdefXYZ")
        self.assertEqual(empty["results"], [])
        self.assertEqual(empty["total_matches"], 0)
        self.assertIsNone(empty["next_offset"])

    def test_multiword_query_is_literal_and_not_semantic(self):
        _, data = self.call("--query", "朋友 虚构", "--kind", "essay", "--limit", "20")
        expected = {
            r["id"] for r in self.documents if r["kind"] == "essay"
            and all(word in (r["title"] + "\n" + r["text"]) for word in ("朋友", "虚构"))
        }
        self.assertEqual({r["id"] for r in data["results"]}, expected)
        _, punctuation = self.call("--query", "朋友|休息", "--limit", "20")
        self.assertEqual(punctuation["total_matches"], 0)

    def test_pagination_can_retrieve_every_chapter_without_repetition(self):
        ids, offset, digest = [], 0, None
        while True:
            code, data = self.call("--list", "--kind", "chapter", "--limit", "7", "--offset", str(offset))
            self.assertEqual(code, 0)
            self.assertEqual(data["offset"], offset)
            if digest is None:
                digest = data["retrieval_digest"]
            self.assertEqual(data["retrieval_digest"], digest)
            ids.extend(r["id"] for r in data["results"])
            if data["next_offset"] is None:
                break
            self.assertGreater(data["next_offset"], offset)
            offset = data["next_offset"]
        self.assertEqual(ids, sorted(r["id"] for r in self.documents if r["kind"] == "chapter"))
        self.assertEqual(len(ids), len(set(ids)))
        _, beyond = self.call("--list", "--kind", "chapter", "--offset", "999")
        self.assertEqual(beyond["results"], [])
        self.assertIsNone(beyond["next_offset"])

    def test_unknown_ids_and_invalid_flags_are_not_silent_fallbacks(self):
        for identifier in ("E99", "../../etc/passwd", "J001"):
            code, data = self.call("--id", identifier)
            self.assertEqual(code, 1)
            self.assertEqual(data["error"], "unknown_id")
            self.assertNotIn("record", data)
        for arguments in ([], ["--query", ""], ["--list", "--limit", "0"],
                          ["--list", "--offset", "-1"], ["--id", "E01", "--kind", "essay"],
                          ["--id", "E01", "--query", "朋友"], ["--id", "E01", "--offset", "2"]):
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    read.main(arguments, ROOT)

    def test_broken_sources_return_explicit_error(self):
        with mock.patch.object(read, "load_documents", side_effect=ValueError("bad route")):
            code, data = self.call("--id", "E09")
        self.assertEqual(code, 2)
        self.assertEqual(data["error"], "source_read_failed")
        self.assertNotIn("record", data)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for folder in ("book", "essays", "docs"):
                shutil.copytree(ROOT / folder, root / folder)
            shutil.copyfile(ROOT / "SHUAQI.md", root / "SHUAQI.md")
            ledger = root / "docs/research.md"
            ledger.write_text(ledger.read_text().replace("https://doi.org/", "https://invalid.example/", 1))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = read.main(["--id", "E09"], root)
            data = json.loads(output.getvalue())
            self.assertEqual(code, 2)
            self.assertEqual(data["error"], "source_read_failed")
            self.assertIn("DOI", data["detail"])
            (root / "SHUAQI.md").unlink()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = read.main(["--id", "E09"], root)
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(output.getvalue())["error"], "source_read_failed")

    def test_source_links_are_locations_not_unread_content(self):
        _, data = self.call("--id", "E09")
        self.assertIn("F57", {r["id"] for r in data["linked_records"]})
        self.assertTrue(all("text" not in r for r in data["linked_records"]))
        _, data = self.call("--id", "B21")
        self.assertIn("N21", {r["id"] for r in data["linked_records"]})
        self.assertIn("C05", {r["id"] for r in data["linked_records"]})

    def test_folded_content_is_preserved_but_not_exposed_by_search(self):
        _, full = self.call("--id", "C22")
        self.assertTrue(full["record"]["contains_folded_content"])
        self.assertIn("<details>", full["record"]["text"])
        _, search = self.call("--query", "恒河", "--kind", "chapter", "--limit", "20")
        self.assertIn("C22", {r["id"] for r in search["results"]})
        self.assertNotIn("恒河", json.dumps(search, ensure_ascii=False))

    def test_route_json_matches_canonical_map_and_targets(self):
        export = json.loads((ROOT / "data/reading-map.json").read_text())
        self.assertEqual(export["routes"], self.routes)
        self.assertEqual(export["source_sha256"], hashlib.sha256((ROOT / "docs/reading-map.md").read_bytes()).hexdigest())
        for route in self.routes:
            self.assertIn(route["source"].split("#")[1], check.anchors_for((ROOT / "docs/reading-map.md").read_text()))
            self.assertTrue(all(identifier in self.by_id for identifier in route["targets"]))
            links = read.linked_records(route, self.documents, ROOT)
            self.assertTrue(set(route["targets"]) <= {r["id"] for r in links})
        for entry in ("llms.txt", "docs/ai.md", "skills/enjoy-the-moment/SKILL.md"):
            text = (ROOT / entry).read_text()
            self.assertIn("reading-map.md", text)
            self.assertIn("tools/read.py", text)

    def test_bad_route_metadata_is_rejected(self):
        original = (ROOT / "docs/reading-map.md").read_text()
        for changed in (
            original.replace('"id":"R01"', '"id":"R99"', 1),
            original.replace('"SHUAQI","E01"', '"SHUAQI","E99"', 1),
            original.replace('"SHUAQI","E01"', '"E01","E01"', 1),
            original.replace('{"id":"R01","targets":["SHUAQI","E01","F86","F97"]}', 'null', 1),
            original.replace('{"id":"R01","targets":["SHUAQI","E01","F86","F97"]}', '["R01"]', 1),
            original.replace('"targets":["SHUAQI","E01","F86","F97"]', '"targets":"SHUAQI"', 1),
            original + '\n<!-- reading-route: {"id":"R99","targets":["E01"]} -->\n',
        ):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / "docs").mkdir()
                (root / "docs/reading-map.md").write_text(changed)
                with self.assertRaises(ValueError):
                    load_routes(root, set(self.by_id))

    def test_retrieval_digest_changes_with_source_or_guidance(self):
        initial = read.retrieval_digest(self.documents)
        altered = [dict(record) for record in self.documents]
        altered[0]["source_sha256"] = "0" * 64
        self.assertNotEqual(initial, read.retrieval_digest(altered))
        altered = [dict(record) for record in self.documents]
        next(r for r in altered if r["kind"] == "route")["source_sha256"] = "1" * 64
        self.assertNotEqual(initial, read.retrieval_digest(altered))

    def test_cli_does_not_require_repository_working_directory(self):
        process = subprocess.run([sys.executable, str(ROOT / "tools/read.py"), "--id", "E07"],
                                 cwd=tempfile.gettempdir(), capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)["record"]["id"], "E07")


if __name__ == "__main__":
    unittest.main()
