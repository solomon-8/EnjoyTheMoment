"""Fidelity guards, not a verdict on permission, persuasion or reader understanding."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import check
import read

SOURCE = "essays/01-pleasure-is-an-end.md"
NOTE = "docs/evidence/F86-liberty-and-disapproval.md"
ANCHORS = ("pleasure-consent-scope", "pleasure-disapproval", "pleasure-concern")


class ConsentApprovalTests(unittest.TestCase):
    def test_three_scenes_distinguish_approval_participation_and_shared_costs(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in ("他人同意，不等于他人赞许", "三个原创假想", "戴耳机听歌",
                       "音箱搬进共用客厅", "别人答应陪你，不等于答应交出自己的感受",
                       "不能约定对方必须真心感动", "共同责任不只等于白纸黑字",
                       "威胁、持续羞辱、针对他人的骚扰", "具备自主判断能力的成年人"):
            self.assertIn(phrase, text)
        self.assertIn("../book/36-home.md#home-sharing", text)
        self.assertIn("../book/08-permission.md#permission-belonging", text)
        self.assertIn("11-pleasure-and-reality.md#pleasure-quality", text)
        for anchor in ANCHORS:
            self.assertIn(anchor, check.anchors_for(text))
        self.assertIn("不要求别人为了证明宽容，必须继续陪伴每一种选择", text)

    def test_primary_source_preserves_scope_and_disagreement_with_mill(self):
        text = (ROOT / NOTE).read_text()
        for phrase in ("前12个正文段落及第16段", "不是完整核读第四章", "不是通读全书",
                       "电子发布日期不是原作出版年份", "Courtney的导言也不是密尔正文",
                       "没有对照纸本扫描", "不是原书印刷段号", "低下趣味",
                       "不采用该段历史人物", "不把关系义务缩成书面合同",
                       "没有提供一个通用动机检测法", "不增加B类效果研究"):
            self.assertIn(phrase, text)
        note = next(x for x in json.loads((ROOT / "data/evidence.json").read_text())["notes"]
                    if x["id"] == "F86")
        self.assertEqual(note["source_kind"], "philosophical_primary_argument")
        self.assertEqual(note["text"], text)
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(records), 50)
        self.assertNotIn("F86", {r["id"] for r in records})
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("F86" not in c["background_ids"] for c in cards))

    def test_full_retrieval_and_route_keep_limits_not_just_a_catchphrase(self):
        documents, routes = read.load_documents(ROOT)
        for identifier, source in (("E01", SOURCE), ("F86", NOTE)):
            raw = (ROOT / source).read_bytes()
            record = next(d for d in documents if d["id"] == identifier)
            self.assertEqual(record["text"], raw.decode())
            self.assertEqual(record["source_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertIn(raw.decode(), (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R01")
        self.assertEqual(set(route["targets"]), {"SHUAQI", "E01", "F86", "F97"})
        self.assertIn("不以失望自动授予全部私人选择的否决权", route["text"])
        self.assertIn("不是全章、全书或法律规则", route["text"])

    def test_public_entrypoints_and_epub_preserve_the_qualified_argument(self):
        for source in ("README.md", "README.en.md", "SHUAQI.md", "docs/manifesto.md"):
            self.assertIn("#pleasure-consent-scope", (ROOT / source).read_text())
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            essay = archive.read("EPUB/text/essays--01-pleasure-is-an-end.xhtml").decode()
            note = archive.read("EPUB/text/docs--evidence--F86-liberty-and-disapproval.xhtml").decode()
            manifesto = archive.read("EPUB/text/SHUAQI.xhtml").decode()
        for anchor in ANCHORS:
            self.assertEqual(html.count('id="' + anchor + '"'), 1)
            self.assertEqual(essay.count('id="' + anchor + '"'), 1)
        self.assertIn("docs--evidence--F86-liberty-and-disapproval.xhtml", essay)
        self.assertIn("essays--01-pleasure-is-an-end.xhtml#pleasure-consent-scope", note)
        self.assertIn("essays--01-pleasure-is-an-end.xhtml#pleasure-consent-scope", manifesto)
        self.assertIn("不是完整核读第四章", note)


if __name__ == "__main__":
    unittest.main()
