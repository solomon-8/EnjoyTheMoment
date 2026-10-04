"""Lossless, version-bound transport; not a test of AI answer quality."""
import contextlib
import copy
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import read


class ReadPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents, cls.routes = read.load_documents(ROOT)
        cls.digest = read.retrieval_digest(cls.documents)
        cls.by_id = {r["id"]: r for r in cls.documents}

    def call(self, *args, documents=None, routes=None):
        output = io.StringIO()
        with mock.patch.object(read, "load_documents", return_value=(
            self.documents if documents is None else documents,
            self.routes if routes is None else routes,
        )), contextlib.redirect_stdout(output):
            code = read.main(args, ROOT)
        return code, json.loads(output.getvalue())

    def test_all_documents_reassemble_exactly_with_complete_guidance_and_links(self):
        for record in self.documents:
            with self.subTest(id=record["id"]):
                cursor = None
                position = 0
                pieces = []
                while True:
                    args = ["--id", record["id"], "--page-chars", "600"]
                    if cursor:
                        args += ["--cursor", cursor]
                    code, page = self.call(*args)
                    self.assertEqual(code, 0)
                    self.assertEqual(page["scope"], "exact_id_page")
                    self.assertEqual(page["record"]["scope"], "text_page")
                    self.assertEqual(page["record"]["canonical_scope"], record["scope"])
                    for key, value in read.location(record).items():
                        if key != "scope":
                            self.assertEqual(page["record"][key], value)
                    piece = page["record"]["text"]
                    pagination = page["pagination"]
                    self.assertEqual(pagination["unit"], "unicode_code_point")
                    self.assertEqual(pagination["start"], position)
                    self.assertEqual(pagination["total"], len(record["text"]))
                    self.assertEqual(pagination["end"], position + len(piece))
                    self.assertEqual(page["complete"], len(piece) == len(record["text"]))
                    self.assertLessEqual(len(piece), 600)
                    self.assertEqual(page["reading_guidance_ids"], [
                        r["id"] for r in self.routes if record["id"] in r["targets"]
                    ])
                    self.assertEqual(page["linked_record_ids"], [
                        r["id"] for r in read.linked_records(record, self.documents, ROOT)
                    ])
                    self.assertNotIn("reading_guidance", page)
                    self.assertNotIn("linked_records", page)
                    self.assertEqual(page["retrieval_digest"], self.digest)
                    pieces.append(piece)
                    position += len(piece)
                    cursor = pagination["next_cursor"]
                    if cursor is None:
                        break
                    self.assertFalse(page["complete"])
                joined = "".join(pieces)
                self.assertEqual(joined, record["text"])
                self.assertEqual(page["text_sha256"], hashlib.sha256(joined.encode("utf-8")).hexdigest())
                self.assertEqual(position, len(record["text"]))

    def test_unicode_whitespace_folded_content_and_page_resize(self):
        text = '开头😀e\u0301👩\u200d👩\u200d👧\u200d👦\n\n| 表 | 格 |\n<details>\n答案\n</details>\n尾部  \n'
        record = dict(self.by_id["E01"], text=text, contains_folded_content=True)
        documents = [record]
        digest = read.retrieval_digest(documents)
        pieces, cursor = [], None
        for index in range(len(text)):
            page = read.exact_page(record, documents, [], ROOT, 1 if index % 2 else 3, cursor, digest)
            pieces.append(page["record"]["text"])
            self.assertTrue(page["record"]["contains_folded_content"])
            cursor = page["pagination"]["next_cursor"]
            if cursor is None:
                break
        self.assertEqual("".join(pieces), text)
        self.assertFalse(page["complete"])
        short = read.exact_page(record, documents, [], ROOT, 8000, None, digest)
        self.assertTrue(short["complete"])
        self.assertIsNone(short["pagination"]["next_cursor"])

    def test_cursor_is_repeatable_and_page_size_can_shrink(self):
        _, first = self.call("--id", "E01", "--page-chars", "100")
        cursor = first["pagination"]["next_cursor"]
        args = ("--id", "E01", "--page-chars", "100", "--cursor", cursor)
        self.assertEqual(self.call(*args), self.call(*args))
        _, smaller = self.call("--id", "E01", "--page-chars", "17", "--cursor", cursor)
        self.assertEqual(smaller["record"]["text"], self.by_id["E01"]["text"][100:117])
        self.assertEqual(smaller["pagination"]["start"], 100)
        _, first_small = self.call("--id", "E01", "--page-chars", "17")
        self.assertEqual(first_small["record"]["text"], self.by_id["E01"]["text"][:17])

    def test_cursor_rejects_other_id_malformed_or_out_of_range(self):
        _, first = self.call("--id", "E01", "--page-chars", "1")
        cursor = first["pagination"]["next_cursor"]
        wrong_range = cursor.split(":")
        wrong_range[2] = str(len(self.by_id["E01"]["text"]))
        cases = [
            ("E09", cursor, "cursor_id_mismatch"),
            ("E01", ":".join(wrong_range), "cursor_out_of_range"),
        ]
        for bad in ("", "garbage", cursor + "suffix", cursor.replace(":1:", ":-1:", 1),
                    cursor.replace(":1:", ":0:", 1), "x" * 4096):
            cases.append(("E01", bad, "invalid_cursor"))
        for identifier, value, expected in cases:
            with self.subTest(expected=expected, cursor=value[:40]):
                code, page = self.call("--id", identifier, "--page-chars", "1", "--cursor", value)
                self.assertEqual(code, 2)
                self.assertEqual(page["error"], expected)
                self.assertNotIn("record", page)

    def test_cursor_rejects_source_guidance_or_extracted_text_changes(self):
        _, first = self.call("--id", "E01", "--page-chars", "1")
        args = ("--id", "E01", "--page-chars", "1", "--cursor", first["pagination"]["next_cursor"])
        for identifier, field, value in [
            ("E01", "source_sha256", "0" * 64),
            ("R01", "source_sha256", "1" * 64),
            ("F96", "source_sha256", "2" * 64),
            ("E01", "text", "changed extracted text"),
        ]:
            documents = copy.deepcopy(self.documents)
            next(r for r in documents if r["id"] == identifier)[field] = value
            code, page = self.call(*args, documents=documents)
            self.assertEqual(code, 2)
            self.assertEqual(page["error"], "cursor_version_mismatch")
            self.assertNotIn("record", page)

    def test_expected_digest_binds_followed_ids_search_and_list(self):
        for args in [
            ("--id", "F96"), ("--id", "R05", "--page-chars", "200"),
            ("--query", "朋友"), ("--list", "--kind", "essay"),
        ]:
            code, result = self.call(*args, "--expect-digest", self.digest)
            self.assertEqual(code, 0)
            self.assertEqual(result["retrieval_digest"], self.digest)
            code, result = self.call(*args, "--expect-digest", "0" * 64)
            self.assertEqual(code, 2)
            self.assertEqual(result["error"], "retrieval_version_mismatch")
            self.assertNotIn("record", result)
            self.assertNotIn("results", result)

    def test_invalid_flag_combinations_are_not_silently_ignored(self):
        for args in [
            ("--query", "朋友", "--page-chars", "20"),
            ("--list", "--cursor", "x"),
            ("--id", "E01", "--cursor", "x"),
            ("--id", "E01", "--page-chars", "0"),
            ("--id", "E01", "--page-chars", "8001"),
            ("--id", "E01", "--page-chars", "abc"),
            ("--id", "E01", "--page-chars", "20", "--offset", "1"),
            ("--id", "E01", "--expect-digest", "not-a-digest"),
        ]:
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    read.main(args, ROOT)
                self.assertEqual(raised.exception.code, 2)
        code, result = self.call("--id", "E999", "--page-chars", "20")
        self.assertEqual(code, 1)
        self.assertEqual(result["error"], "unknown_id")

    def test_real_cli_continuation_from_outside_checkout(self):
        command = [sys.executable, str(ROOT / "tools/read.py"), "--id", "E01", "--page-chars", "75"]
        first = subprocess.run(command, cwd=tempfile.gettempdir(), capture_output=True, text=True, check=True)
        page = json.loads(first.stdout)
        second = subprocess.run(command + ["--cursor", page["pagination"]["next_cursor"]],
                                cwd=tempfile.gettempdir(), capture_output=True, text=True, check=True)
        continuation = json.loads(second.stdout)
        self.assertEqual(continuation["record"]["text"], self.by_id["E01"]["text"][75:150])
        self.assertEqual(continuation["pagination"]["start"], 75)


if __name__ == "__main__":
    unittest.main()
