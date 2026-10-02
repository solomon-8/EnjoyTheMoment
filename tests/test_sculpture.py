"""Keep sculpture observations, object identities and photo limits together."""
from pathlib import Path
import hashlib
import json
import re
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read


class SculptureTests(unittest.TestCase):
    def test_argument_keeps_object_relations_objections_and_old_art(self):
        source = "book/25-looking-at-art.md"
        text = (ROOT / source).read_text()
        for phrase in (
            "两条腿围出来、能透见后方的空间",
            "不是量过雕塑的重心",
            "两馆的说法并不完全相同",
            "雕塑的部件选择，不能替真实的人定义身体价值",
            "两次拍摄的位置、取景和灯光都没有被本书固定",
            "1987.217", "84.1厘米", "S.998", "213.5厘米",
            "这不就是替大师没做完找理由吗",
            "不等于欠作品一份看完的义务",
        ):
            self.assertIn(phrase, text)
        html = build.markdown(text, source)
        for anchor in (
            "art-sculpture-recognition", "art-sculpture-fragment",
            "art-sculpture-two-views", "art-sculpture-objection",
            "art-letters-and-versions", "art-material-history",
            "art-traces-and-meaning", "art-knowledge-and-pleasure",
        ):
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
        self.assertEqual(html.count('<figure class="artwork">'), 5)
        self.assertEqual(html.count("<table>"), 3)
        for filename in ("van-gogh-bedroom.jpg", "seurat-grande-jatte.jpg",
                         "seurat-oil-sketch.jpg"):
            self.assertIn(filename, text)

    def test_source_preserves_conflicting_accounts_and_access_limits(self):
        text = (ROOT / "docs/evidence/F77-sculpture-and-viewpoint.md").read_text()
        for phrase in (
            "躯干来自另一构图", "躯干很可能也为圣约翰而作",
            "这些字段不能移给芝加哥的1987.217",
            "不是这件大尺寸青铜的铸造日期",
            "未核清这句的关系与引文出处",
            "本次请求返回403", "未采用Brancusi检索候选",
            "2014-01-17", "2015-01-17",
            "不能称作同一次连续绕行",
            "不是现场观展报告、动作实验或享乐效果研究",
            "没有独立的馆藏号鉴定文件",
            "不从作品进入公有领域自动推断任意照片许可",
        ):
            self.assertIn(phrase, text)
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        note = next(n for n in notes if n["id"] == "F77")
        self.assertEqual(note["source_kind"], "museum_records_and_open_photographs")
        self.assertEqual(note["text"], text)
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual({r["id"] for r in records},
                         {f"B{number:02d}" for number in range(1, 47)})
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("F77" not in card["background_ids"] for card in cards))

    def test_photographs_are_attributed_local_and_retained_in_epub(self):
        digests = {
            "rodin-walking-front.jpg":
                "26e137fcd114244a4142d56a1fcdfcf7576d34b61578741b323454bb68f4aae2",
            "rodin-walking-rear.jpg":
                "4a9fadc4c60cb8643a728d37b0c13bf3d7799ec2a23b0a5b9d5ac7c8f211cdb9",
        }
        chapter = (ROOT / "book/25-looking-at-art.md").read_text()
        credits = (ROOT / "assets/art/README.md").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            for filename, digest in digests.items():
                raw = (ROOT / "assets/art" / filename).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
                self.assertEqual(archive.read("EPUB/images/" + filename), raw)
                self.assertIn(digest, credits)
                self.assertIn(filename, chapter)
            rendered = archive.read(
                "EPUB/text/book--25-looking-at-art.xhtml").decode()
            self.assertIn("F77-sculpture-and-viewpoint.xhtml", rendered)
            self.assertIn("art-sculpture-two-views", rendered)
            self.assertIn("2014-01-17", rendered)
            self.assertIn("2015-01-17", rendered)
        for path in ("assets/art/README.md", "docs/sources.md",
                     "docs/evidence/F77-sculpture-and-viewpoint.md"):
            text = (ROOT / path).read_text()
            self.assertIn("Mx. Granger", text)
            self.assertIn("CC0", text)
            self.assertIn("不是", text)
        alt_texts = re.findall(r"!\[([^\]]+)\]\([^)]*rodin[^)]*\)", chapter)
        self.assertEqual(len(alt_texts), 2)
        self.assertTrue(all(len(alt) > 60 for alt in alt_texts))

    def test_full_retrieval_keeps_photos_versions_and_interpretation_together(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {d["id"]: d for d in documents}
        for identifier, source in (
            ("C25", "book/25-looking-at-art.md"),
            ("F77", "docs/evidence/F77-sculpture-and-viewpoint.md"),
        ):
            raw = (ROOT / source).read_bytes()
            self.assertEqual(by_id[identifier]["text"], raw.decode())
            self.assertEqual(by_id[identifier]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertIn(raw.decode(), (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R77")
        self.assertEqual(set(route["targets"]),
                         {"C25", "F77", "F13", "F54", "F55", "C20", "C26", "E01"})
        for identifier in route["targets"]:
            self.assertIn("[" + identifier, route["text"])
        self.assertIn("不拼接日期/尺寸", route["text"])
        self.assertIn("不称同次连续绕行或控制实验", route["text"])
        self.assertIn("不自动生成购票/参观/必须绕行任务", route["text"])


if __name__ == "__main__":
    unittest.main()
