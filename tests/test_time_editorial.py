"""Compatibility and retrieval tests for the time chapters, not editorial scores."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read


class TimeEditorialTests(unittest.TestCase):
    def test_reservation_and_legacy_fragment_resolve_to_same_chapter(self):
        source = "book/21-free-time.md"
        text = (ROOT / source).read_text()
        html = build.markdown(text, source)
        reader = (ROOT / "index.html").read_text()
        for anchor in ("不给空白写用途是否就是浪费", "time-reservation"):
            marker = 'id="' + anchor + '"'
            self.assertEqual(html.count(marker), 1)
            self.assertEqual(reader.count(marker), 1)
            self.assertEqual(build.local_href(source + "#" + anchor, "README.md"),
                             "#" + anchor)
        # Compatibility preserves destinations; the current introduction can
        # use a different outline without linking to every legacy fragment.
        self.assertIn('href="#time-reservation"',
                      build.markdown((ROOT / "docs/reading-map.md").read_text(),
                                     "docs/reading-map.md"))

    def test_condensed_argument_links_keep_their_destinations(self):
        for source, anchors in (
            ("book/01-start-now.md", ("rest-paid-evening", "excitement-costs",
                                      "waiting-plan-revision")),
            ("book/21-free-time.md", ("rest-returns", "rest-no-verdict")),
        ):
            html = build.markdown((ROOT / source).read_text(), source)
            for anchor in anchors:
                with self.subTest(source=source, anchor=anchor):
                    self.assertIn('href="#' + anchor + '"', html)
                    self.assertIn('id="' + anchor + '"',
                                  (ROOT / "index.html").read_text())

    def test_full_text_retrieval_keeps_example_and_its_objection_together(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {d["id"]: d for d in documents}
        full = (ROOT / "llms-full.txt").read_text()
        chapters = {c["id"]: c for c in json.loads(
            (ROOT / "data/chapters.json").read_text())["chapters"]}
        for identifier, source in (("C01", "book/01-start-now.md"),
                                   ("C21", "book/21-free-time.md")):
            data = (ROOT / source).read_bytes()
            self.assertEqual(by_id[identifier]["text"], data.decode())
            self.assertEqual(by_id[identifier]["source_sha256"],
                             hashlib.sha256(data).hexdigest())
            # read.py returns the complete canonical file. The combined export
            # deliberately separates chapter prose from cards; do not require
            # that the two remain adjacent in that different representation.
            prose = data.decode().partition('<a id="j')[0].strip()
            self.assertEqual(chapters[identifier]["text"], prose)
            self.assertTrue(prose in full, identifier + " prose missing from full export")
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        for card in cards:
            if card["chapter_id"] == "01":
                self.assertTrue(card["body"] in full,
                                card["id"] + " body missing from full export")
        # Scope marker and strongest objection belong in the same retrieved
        # argument, not in a detached note that a reader can miss.
        text = by_id["C21"]["text"]
        section = text.split('<a id="time-reservation"></a>', 1)[1].split(
            '<a id="time-empty"></a>', 1)[0]
        self.assertIn("原创假想", section)
        self.assertIn("最有力的反对", section)
        self.assertIn("不提供场馆规定或法律结论", section)
        self.assertIn("不把它改判成违约", section)
        route = next(r for r in routes if r["id"] == "R49")
        self.assertIn("#time-reservation", route["text"])
        self.assertIn("利用率不等于公平", route["text"])
        self.assertEqual(set(route["targets"]),
                         {"C21", "C09", "E07", "E09", "B11", "N11", "B27", "N27"})

    def test_reservation_is_not_exported_as_new_empirical_evidence(self):
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertTrue(all("time-reservation" not in r["source"] for r in records))
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        self.assertTrue(all(n["source"] != "book/21-free-time.md" for n in notes))
        chapters = json.loads((ROOT / "data/chapters.json").read_text())["chapters"]
        chapter = next(c for c in chapters if c["id"] == "C21")
        self.assertEqual(chapter["card_ids"], [])
        self.assertIn("原创假想", chapter["text"])
