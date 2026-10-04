"""Preserve an argument and its limits; not a quality or persuasion score."""
from pathlib import Path
import json
import subprocess
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import epub


class BuyingTimeArgumentTests(unittest.TestCase):
    def test_full_argument_and_limits_are_retrievable(self):
        source = (ROOT / "essays/04-buying-pleasure.md").read_text()
        section = source.split('<a id="purchase-hourly-price"></a>', 1)[1].split(
            "### 一个假设预算内的比较", 1
        )[0]
        for phrase in (
            "两个原创假想",
            "服务费高于她的平均时薪",
            "服务费低于平均时薪",
            "一次愿意与长期愿意不是同一结论",
            "不能证明它此刻付得起",
            "不是Whillans实验测出的时薪门槛或消费处方",
        ):
            self.assertIn(phrase, section)
        result = json.loads(subprocess.check_output(
            [sys.executable, str(ROOT / "tools/read.py"), "--id", "E04"],
            cwd=ROOT, text=True,
        ))
        self.assertTrue(result["complete"])
        self.assertEqual(source, result["record"]["text"])
        self.assertIn("#rest-real-income", section)
        self.assertIn(source, (ROOT / "llms-full.txt").read_text())
        self.assertIn(
            "#purchase-hourly-price", (ROOT / "docs/reading-map.md").read_text()
        )

    def test_web_and_epub_preserve_the_comparison(self):
        path = "essays/04-buying-pleasure.md"
        source = (ROOT / path).read_text()
        self.assertTrue(
            build.markdown(source, path, omit_title=True)
            in (ROOT / "index.html").read_text(),
            "The generated web essay must retain its complete canonical body",
        )
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            text = archive.read("EPUB/" + epub.document_name(path)).decode()
        for phrase in (
            "你的时薪，不是周日的票价",
            "没有额外协调、等待或返工",
            "一个不挣钱的下午，可以值得付钱",
            "不是Whillans实验测出的时薪门槛或消费处方",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
