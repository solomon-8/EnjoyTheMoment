"""Keep the manifesto's concise position consistent with its full argument."""
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read


class ManifestoExitTests(unittest.TestCase):
    def test_dislike_and_existing_commitments_remain_distinct(self):
        text = (ROOT / "SHUAQI.md").read_text()
        section = text.split('<a id="shuaqi-exit"></a>', 1)[1].split(
            '<a id="shuaqi-costs"></a>', 1)[0]
        for phrase in (
            "不必靠硬撑证明真心", "不再喜欢，可以停",
            "已经花掉的钱未必退得回", "已经答应的事自动作废",
            "改变安排仍要说明、协商与处理影响", "突然消失",
            "继续表演尽兴", "无限接下尚未答应的将来",
        ):
            self.assertIn(phrase, section)
        self.assertIn("essays/03-now-or-later.md#waiting-open-future", section)
        self.assertIn("自己愿意，他人同意，代价看得见，过程退得出", section)

    def test_old_and_new_manifesto_fragments_survive_exports(self):
        text = (ROOT / "SHUAQI.md").read_text()
        web = (ROOT / "index.html").read_text()
        rendered = build.markdown(text, "SHUAQI.md")
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            item = next(name for name in archive.namelist()
                        if name.endswith("/SHUAQI.xhtml"))
            epub_text = archive.read(item).decode()
        for anchor in ("5-不好耍了随时散场", "shuaqi-exit"):
            for output in (rendered, web, epub_text):
                self.assertEqual(output.count('id="' + anchor + '"'), 1)
        self.assertIn(text, (ROOT / "llms-full.txt").read_text())

    def test_ai_route_returns_the_full_position_not_unqualified_cancellation(self):
        documents, routes = read.load_documents(ROOT)
        text = (ROOT / "SHUAQI.md").read_text()
        self.assertEqual(next(doc for doc in documents if doc["id"] == "SHUAQI")["text"], text)
        route = next(row for row in routes if row["id"] == "R01")
        self.assertEqual(set(route["targets"]), {"SHUAQI", "E01", "F86", "F97"})
        self.assertIn("#shuaqi-exit", route["text"])
        self.assertIn("不能把“过程退得出”抽成无条件、无代价取消承诺的保证", route["text"])


if __name__ == "__main__":
    unittest.main()
