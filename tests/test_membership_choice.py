"""Bounded source claims and export integrity, not reader-interest evidence."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read


class MembershipChoiceTests(unittest.TestCase):
    def test_renewal_question_keeps_contract_and_observation_distinct(self):
        text = (ROOT / "book/06-spending.md").read_text()
        section = text.split('<a id="spending-renewal"></a>', 1)[1].split(
            '<a id="spending-default-choice"></a>', 1)[0]
        for phrase in ("年付则到期结束", "月付会自动扣费",
                       "最后一次出勤到合同终止", "特定子样本",
                       "没有企业补贴", "价格及入会时间限制",
                       "不是全体会员的平均数", "没有直接给出那个决定发生的时间",
                       "不是随机分配", "没有测量快乐",
                       "3月10日最后出勤", "4月5日取消", "4月30日会籍结束"):
            self.assertIn(phrase, section)
        self.assertIn("不是当天提出取消就当天结束", section)
        note = (ROOT / "docs/evidence/F91-membership-and-renewal.md").read_text()
        self.assertIn("10号以前", note)
        self.assertIn("10号之后", note)
        self.assertIn("未补定恰好10号", note)

    def test_original_comparison_keeps_symmetry_and_counterargument(self):
        text = (ROOT / "book/06-spending.md").read_text()
        section = text.split('<a id="spending-default-choice"></a>', 1)[1].split(
            '<a id="spending-stop-and-like"></a>', 1)[0]
        for phrase in ("本书虚构", "价格、内容、预约条件相同",
                       "没有额外收费或名额损失", "默认结束不是没有代价",
                       "因为漏了操作而错过服务", "对称比较就不成立",
                       "也不能自动为每笔遗忘的扣款补写理由"):
            self.assertIn(phrase, section)
        ending = text.split('<a id="spending-stop-and-like"></a>', 1)[1]
        self.assertIn("停止一项交易，不必把一整类快乐贬低掉", ending)
        self.assertIn("按次、月付、年付都可能合适", ending)
        # Existing calculations, cards, and four tables remain available.
        self.assertEqual(len(re.findall(r"^\| ---", text, re.M)), 4)
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual([c["id"] for c in cards if c["chapter_id"] == "06"],
                         ["J031", "J032", "J033", "J034", "J035", "J036"])

    def test_source_scope_and_route_travel_with_full_text(self):
        documents, routes = read.load_documents(ROOT)
        documents = {d["id"]: d for d in documents}
        routes = {r["id"]: r for r in routes}
        source = "docs/evidence/F91-membership-and-renewal.md"
        text = (ROOT / source).read_text()
        self.assertEqual(documents["F91"]["text"], text)
        self.assertEqual(documents["F91"]["source_sha256"],
                         hashlib.sha256((ROOT / source).read_bytes()).hexdigest())
        self.assertEqual(build.EVIDENCE_KINDS["F91"], "primary_research_excerpt")
        for phrase in ("指定段落", "未复算模型", "未与出版商副本逐字对照",
                       "不补写该特定子样本人数", "不是随机",
                       "按次用户的实际出勤", "没有测量主观快乐"):
            self.assertIn(phrase, text)
        self.assertEqual(routes["R10"]["targets"], ["C06", "E04", "B20", "N20", "F91"])
        self.assertIn("不是全7,752人或决定不要后的延迟", routes["R10"]["text"])
        self.assertIn(text.strip(), (ROOT / "llms-full.txt").read_text())
        research = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertFalse(any(r["id"] == "F91" for r in research))

    def test_new_and_legacy_entrances_in_web_and_epub(self):
        source = "book/06-spending.md"
        rendered = build.markdown((ROOT / source).read_text(), source)
        reader = (ROOT / "index.html").read_text()
        anchors = ("spending-renewal", "spending-default-choice",
                   "spending-stop-and-like", "快乐不是免检章节俭也不是否决权")
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            names = archive.namelist()
            path = next(n for n in names if n.endswith("book--06-spending.xhtml"))
            epub = archive.read(path).decode()
            note_path = next(n for n in names if n.endswith(
                "docs--evidence--F91-membership-and-renewal.xhtml"))
            note = archive.read(note_path).decode()
            self.assertIn("2.31个完整月", epub)
            self.assertIn("primary_research_excerpt", note)
            for anchor in anchors:
                for output in (rendered, reader, epub):
                    self.assertEqual(output.count('id="' + anchor + '"'), 1)


if __name__ == "__main__":
    unittest.main()
