"""EPUB coverage and data integrity; not an accessibility or reader study."""
import hashlib
import html
import io
import json
from pathlib import Path
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZIP_STORED

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import epub
from check import anchors_for

NS = {"h": epub.XHTML, "p": epub.OPF}


def source_words(text):
    """Independent text oracle: remove markup, not prose or numeric content."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    lines, fenced = [], False
    for line in text.splitlines():
        if line.startswith(("```", "~~~")):
            fenced = not fenced
            continue
        if fenced:
            lines.append(line)
            continue
        if re.fullmatch(r'<a id="[^"]+"></a>|</?details>|---', line):
            continue
        line = re.sub(r"</?summary>", "", line)
        # A numbered heading is content, not a Markdown list marker.
        line = (re.sub(r"^#{1,6} +", "", line) if line.startswith("#")
                else re.sub(r"^(- |> |\d+\. )", "", line))
        if line.startswith("|"):
            if re.fullmatch(r"\|[\s:|-]+\|", line):
                continue
            line = line.replace("|", "")
        line = re.sub(r"!?\[([^\]]*)\]\([^)]+\)", r"\1", line)
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        line = re.sub(r"`([^`]+)`", r"\1", line)
        line = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", line)
        lines.append(line)
    # Keep punctuation, signs, decimal points and percentages: stripping to
    # alphanumerics could hide a changed negative number or confidence interval.
    return re.sub(r"\s+", "", html.unescape("".join(lines)))


def visible_words(element):
    chunks = []
    if element.text:
        chunks.append(element.text)
    for child in element:
        if child.attrib.get("class") in ("source-link", "back-to-toc"):
            continue
        if child.tag == "{" + epub.XHTML + "}img":
            chunks.append(child.attrib["alt"])
        chunks.append(visible_words(child))
        if child.tail:
            chunks.append(child.tail)
    return re.sub(r"\s+", "", "".join(chunks))


class EpubTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metadata = json.loads((ROOT / epub.STATE).read_text())
        cls.data = (ROOT / epub.OUTPUT).read_bytes()
        cls.archive = ZipFile(io.BytesIO(cls.data))
        cls.entries = {name: cls.archive.read(name) for name in cls.archive.namelist()}

    @classmethod
    def tearDownClass(cls):
        cls.archive.close()

    def test_container_manifest_spine_and_no_runtime_resources(self):
        first = self.archive.infolist()[0]
        self.assertEqual(first.filename, "mimetype")
        self.assertEqual(first.compress_type, ZIP_STORED)
        self.assertEqual(first.extra, b"")
        self.assertEqual(self.entries["mimetype"], b"application/epub+zip")
        epub.validate_internal({k: v for k, v in self.entries.items() if k != "mimetype"})
        package = ET.fromstring(self.entries["EPUB/package.opf"])
        items = package.findall("p:manifest/p:item", NS)
        manifest = {item.attrib["id"]: "EPUB/" + item.attrib["href"] for item in items}
        resources = set(manifest.values())
        self.assertEqual(resources, set(self.entries) - {
            "mimetype", "META-INF/container.xml", "EPUB/package.opf"})
        spine = [manifest[item.attrib["idref"]]
                 for item in package.findall("p:spine/p:itemref", NS)]
        expected = ["EPUB/title.xhtml", "EPUB/nav.xhtml"] + [
            "EPUB/" + epub.document_name(source) for source in epub.source_files(ROOT)]
        self.assertEqual(spine, expected)
        self.assertEqual(len(spine), len(set(spine)))

    def test_every_reading_source_keeps_all_text_in_order(self):
        for source in epub.source_files(ROOT):
            with self.subTest(source=source):
                original = (ROOT / source).read_text()
                if source == "LICENSE":
                    original = "# 许可与第三方权利\n\n" + original
                tree = ET.fromstring(self.entries["EPUB/" + epub.document_name(source)])
                actual = visible_words(tree.find("h:body", NS))
                expected = source_words(original)
                # A bounded diagnostic avoids dumping a whole book on failure.
                if actual != expected:
                    pos = next((i for i, pair in enumerate(zip(actual, expected))
                                if pair[0] != pair[1]), min(len(actual), len(expected)))
                    self.fail("{} text differs at {}: expected {!r}, got {!r}".format(
                        source, pos, expected[max(0, pos-40):pos+80],
                        actual[max(0, pos-40):pos+80]))

    def test_images_are_original_bytes_with_alt_text_and_credits(self):
        images = set()
        for name, data in self.entries.items():
            if not name.endswith(".xhtml"):
                continue
            for image in ET.fromstring(data).findall(".//h:img", NS):
                self.assertTrue(image.attrib.get("alt"))
                filename = Path(image.attrib["src"]).name
                images.add(filename)
                candidates = [ROOT / "assets" / folder / filename for folder in ("art", "media")]
                original = next(p for p in candidates if p.is_file())
                self.assertEqual(self.entries["EPUB/images/" + filename], original.read_bytes())
        self.assertGreater(len(images), 20)
        for source in ("assets/art/README.md", "assets/media/README.md", "LICENSE"):
            self.assertIn("EPUB/" + epub.document_name(source), self.entries)
        self.assertIn("EPUB/" + epub.document_name("docs/editorial-policy.md"), self.entries)

    def test_all_old_source_fragments_survive_and_details_are_expanded(self):
        for source in epub.source_files(ROOT):
            if source == "LICENSE":
                continue
            tree = ET.fromstring(self.entries["EPUB/" + epub.document_name(source)])
            ids = {element.attrib["id"] for element in tree.iter() if "id" in element.attrib}
            self.assertTrue(anchors_for((ROOT / source).read_text()).issubset(ids), source)
            self.assertFalse(tree.findall(".//h:details", NS), source)
        diagram = ET.fromstring(self.entries[
            "EPUB/" + epub.document_name("docs/evidence/F42-othello-choice.md")])
        self.assertIn("  ABCDEFGH\n1 ..W.....\n2 .BWW....",
                      diagram.find(".//h:pre/h:code", NS).text)
        navigation = ET.fromstring(self.entries["EPUB/nav.xhtml"])
        labels = ["".join(a.itertext()) for a in navigation.findall(".//h:a", NS)]
        self.assertEqual(sum(bool(re.match(r"J\d{3} ·", label)) for label in labels), 60)

    def test_current_sources_and_reproducible_archive_match(self):
        current = epub.edition_metadata(ROOT, self.metadata)
        self.assertEqual(current, self.metadata)
        self.assertEqual(epub.build_epub(ROOT, current), self.data)
        self.assertEqual(epub.build_epub(ROOT, current), self.data)
        for source, digest in current["sources"].items():
            self.assertEqual(hashlib.sha256((ROOT / source).read_bytes()).hexdigest(), digest)
        core = {p.relative_to(ROOT).as_posix() for folder in
                ("book", "essays", "docs/evidence") for p in (ROOT / folder).glob("*.md")}
        self.assertTrue(core.issubset(set(current["reading_files"])))

    def test_renderer_rejects_missing_targets_and_unsafe_content(self):
        names = {"SHUAQI.md": "text/SHUAQI.xhtml"}
        for text in ('# title\n<script>alert(1)</script>', '# title\n[x](missing.md)',
                     '# title\n[x](#missing)', '# title\n[x](javascript:alert)',
                     '# title\n![image](https://example.org/image.png)',
                     '# title\n```\nunclosed'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                epub.render_document(text, "SHUAQI.md", names, {}, ROOT)


if __name__ == "__main__":
    unittest.main()
