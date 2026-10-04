"""Keep the new argument/source retrievable, without treating assertions as truth tests."""
import contextlib
import io
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check
import epub
import read


class JoyForSomeoneTests(unittest.TestCase):
    def fetch(self, identifier):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = read.main(["--id", identifier], ROOT)
        self.assertEqual(code, 0)
        return json.loads(output.getvalue())

    def test_argument_and_source_are_complete_separate_records(self):
        essay = self.fetch("E09")
        note = self.fetch("F96")
        self.assertTrue(essay["complete"])
        self.assertTrue(note["complete"])
        self.assertEqual(
            note["record"]["text"],
            (ROOT / "docs/evidence/F96-hume-and-self-love.md").read_text(),
        )
        self.assertIn("F96", {x["id"] for x in essay["linked_records"]})
        self.assertTrue(all("text" not in x for x in essay["linked_records"]))
        self.assertIn("friends-joy-for-you", check.anchors_for(essay["record"]["text"]))
        self.assertIn("hume-object-and-enjoyment", check.anchors_for(note["record"]["text"]))
        source = next(
            x for x in json.loads((ROOT / "data/evidence.json").read_text())["notes"]
            if x["id"] == "F96"
        )
        self.assertEqual(source["source_kind"], "philosophical_primary_text")

    def test_route_keeps_the_specific_source_limits(self):
        route = self.fetch("R05")["record"]["text"]
        self.assertIn('"F96"', route)
        self.assertIn("不是现代实验", route)
        self.assertIn("不是识别朋友动机的测试", route)
        self.assertIn("不把自我享受排除为不真诚", route)
        self.assertIn("不要求无限牺牲", route)

    def test_exported_essay_is_the_canonical_text_not_a_summary(self):
        source = (ROOT / "essays/09-friends-not-assets.md").read_text()
        exported = next(
            x for x in json.loads((ROOT / "data/essays.json").read_text())["essays"]
            if x["id"] == "E09"
        )
        self.assertEqual(exported["text"], source)
        self.assertIn("愿望属于我，不等于愿望的对象只能是我的感受", source)
        self.assertIn("不必声称朋友的快乐一定使自己的总快乐净增加", source)
        self.assertIn("反过来，也不必为了证明真心，设法让自己一无所得", source)

    def test_epub_links_connect_new_source_and_argument(self):
        essay_path = "essays/09-friends-not-assets.md"
        note_path = "docs/evidence/F96-hume-and-self-love.md"
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            essay = archive.read("EPUB/" + epub.document_name(essay_path)).decode()
            note = archive.read("EPUB/" + epub.document_name(note_path)).decode()
        self.assertIn('id="friends-joy-for-you"', essay)
        self.assertIn('id="hume-object-and-enjoyment"', note)
        self.assertIn("F96-hume-and-self-love.xhtml#hume-object-and-enjoyment", essay)
        self.assertIn("09-friends-not-assets.xhtml#friends-joy-for-you", note)
        self.assertIn("不是行为实验", note)


if __name__ == "__main__":
    unittest.main()
