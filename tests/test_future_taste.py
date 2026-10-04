"""Guard reading scope and source identity, not persuasion or prediction accuracy."""
import hashlib
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read


class FutureTasteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = "docs/evidence/F99-predicting-future-taste.md"
        cls.source = (ROOT / cls.path).read_text()
        cls.essay = (ROOT / "essays/03-now-or-later.md").read_text()

    def test_present_preference_does_not_certify_prediction(self):
        for text in (
            "今天确实喜欢，与今天能准确预测以后仍然喜欢",
            "不是把同一批人跟踪十年", "不是实际多花钱的记录",
            "两组所评价的乐队身份和演出时间都不同",
            "今天愿付多少钱", "129美元与80美元",
            "我想把这份兴趣培养下去", "短承诺也不是普遍优解",
            "承认它现在真，也不必替它无限续约",
        ):
            self.assertIn(text, self.essay)
        section = self.essay.split('<a id="waiting-predicted-taste"></a>')[1].split(
            '<a id="waiting-open-future"></a>')[0]
        visible, details = section.split("<details>", 1)
        self.assertIn("不是实际多花钱", visible)
        self.assertIn("演出时间都不同", visible)
        self.assertIn("独立的MIDUS人格追踪", details)
        self.assertEqual(build.markdown(self.essay, "essays/03-now-or-later.md").count("<table>"), 1)

    def test_source_separates_design_findings_and_unresolved_table(self):
        for text in (
            "10.1126/science.1229294", "170名", "18—64岁", "52%女性",
            "今天愿意支付的最高金额", "今天愿意支付的金额",
            "71与99", "7130、7420、2945", "7519、2717、7130",
            "未解决的表文对齐", "不能因此单独识别", "没有真实交易",
            "不是研究4那170人的后续调查", "不能确定原因",
            "10.1177/01461672211036873", "未取得主文",
            "不是中国样本", "未转载PDF",
        ):
            self.assertIn(text, self.source)

    def test_complete_retrieval_and_route_keep_limits(self):
        documents, routes = read.load_documents(ROOT)
        record = next(d for d in documents if d["id"] == "F99")
        self.assertEqual(record["text"], self.source)
        self.assertEqual(record["source_sha256"], hashlib.sha256(self.source.encode()).hexdigest())
        self.assertEqual(record["source_kind"], "primary_research_excerpt")
        route = next(d for d in routes if d["id"] == "R04")
        self.assertIn("F99", route["targets"])
        for text in ("两组均问今天愿付多少", "不是实际购票", "不是音乐追踪",
                     "小岑假想身份不变", "主动培养兴趣"):
            self.assertIn(text, route["text"])
        self.assertIn(self.source, (ROOT / "llms-full.txt").read_text())

    def test_epub_preserves_expanded_details_and_bidirectional_links(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            essay = ET.fromstring(z.read("EPUB/text/essays--03-now-or-later.xhtml"))
            source = ET.fromstring(z.read(
                "EPUB/text/docs--evidence--F99-predicting-future-taste.xhtml"))
        self.assertIn("独立的MIDUS人格追踪", "".join(essay.itertext()))
        self.assertIn("表文对齐", "".join(source.itertext()))
        self.assertIn("docs--evidence--F99-predicting-future-taste.xhtml",
                      [e.attrib["href"] for e in essay.iter() if "href" in e.attrib])
        self.assertIn("essays--03-now-or-later.xhtml#waiting-predicted-taste",
                      [e.attrib["href"] for e in source.iter() if "href" in e.attrib])


if __name__ == "__main__":
    unittest.main()
