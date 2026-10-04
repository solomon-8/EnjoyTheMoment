"""Content and retrieval guards, not risk advice or an editorial victory score."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check
import read

ESSAY = "essays/02-excitement-without-escalation.md"
NOTE = "docs/evidence/F86-liberty-and-disapproval.md"
ANCHORS = (
    "excitement-chosen-uncertainty",
    "excitement-bridge",
    "excitement-risk-not-permission",
)


class ChosenUncertaintyTests(unittest.TestCase):
    def test_choice_outcome_and_permitted_challenge_remain_distinct(self):
        text = (ROOT / ESSAY).read_text()
        for phrase in (
            "设想一场原创的朋友聚会",
            "不想要坏结果，与愿意选择包含坏结果可能的经历，并不矛盾",
            "不是说越没准备越真实",
            "事前选择即兴，不是签下一份“事后不得难过”的约定",
            "接受一种可能，不等于把制造它的任何方式都交给别人",
            "比赛中的对手可以认真寻找让你失分的机会",
            "问题不是“故意”两个字就能决定",
            "尴尬本身并不证明谁违约",
            "也可以发现这种未定感并不合自己，下次不再选",
            "本书没有权替她宣布精彩",
        ):
            self.assertIn(phrase, text)
        positions = [text.index(f'<a id="{anchor}"') for anchor in ANCHORS]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("04-buying-pleasure.md#purchase-judgement", text)

    def test_same_primary_record_keeps_both_reading_scopes_and_limits(self):
        text = (ROOT / NOTE).read_text()
        for phrase in (
            "第四章前12个正文段落及第16段、第五章前7个正文段落",
            "不是完整核读第四章或第五章",
            "不是原书印刷段号",
            "儿童、神志不清及不能充分使用反思能力的状态",
            "本书不采用其中药品、危险物品、饮酒、强制劳动",
            "第五章其余段落未读",
            "不是密尔举例或受访者经历",
            "不提供具体身体风险、刺激剂量、冒险收益或效果保证",
        ):
            self.assertIn(phrase, text)
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        self.assertEqual(sum(n["id"] == "F86" for n in notes), 1)
        self.assertEqual(len(notes), 143)
        self.assertEqual(next(n for n in notes if n["id"] == "F86")["source_kind"],
                         "philosophical_primary_argument")
        self.assertEqual(len(json.loads(
            (ROOT / "data/research.json").read_text())["records"]), 50)

    def test_full_retrieval_and_route_keep_original_and_qualified_text(self):
        documents, routes = read.load_documents(ROOT)
        for identifier, source in (("E02", ESSAY), ("F86", NOTE)):
            raw = (ROOT / source).read_bytes()
            doc = next(d for d in documents if d["id"] == identifier)
            self.assertEqual(doc["text"], raw.decode())
            self.assertEqual(doc["source_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertIn(raw.decode(), (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R03")
        self.assertIn("F86", route["targets"])
        for phrase in ("不满意不证明违约", "不是全书、现行法律、风险模型或能力测验",
                       "不把“自愿”当充分知情或安全证明"):
            self.assertIn(phrase, route["text"])

    def test_offline_and_epub_keep_anchors_and_bidirectional_links(self):
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            essay = archive.read(
                "EPUB/text/essays--02-excitement-without-escalation.xhtml").decode()
            note = archive.read(
                "EPUB/text/docs--evidence--F86-liberty-and-disapproval.xhtml").decode()
        self.assertTrue(set(ANCHORS) <= check.anchors_for((ROOT / ESSAY).read_text()))
        for anchor in ANCHORS:
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
            self.assertEqual(essay.count(f'id="{anchor}"'), 1)
        self.assertEqual(html.count('id="liberty-bridge"'), 1)
        self.assertEqual(note.count('id="liberty-bridge"'), 1)
        self.assertIn("docs--evidence--F86-liberty-and-disapproval.xhtml#liberty-bridge",
                      essay)
        self.assertIn("essays--02-excitement-without-escalation.xhtml"
                      "#excitement-chosen-uncertainty", note)


if __name__ == "__main__":
    unittest.main()
