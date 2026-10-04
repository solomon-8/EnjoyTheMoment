"""Publication integrity for a project rationale, not evidence of popularity."""
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import epub


class CultureEditorialFocusTests(unittest.TestCase):
    def test_rationale_keeps_values_and_materials_ahead_of_activities(self):
        source = (ROOT / "docs/culture-shuaqi.md").read_text()
        rationale = source.split("## 为什么把它作为核心", 1)[1].split(
            "## 三层内容不要混写", 1
        )[0]
        for phrase in (
            "以下是本项目的**编辑判断**",
            "有值得争论的偏向",
            "即使读者不照着做",
            "小份是选项",
            "不是传播效果预测",
        ):
            self.assertIn(phrase, rationale)
        self.assertNotIn("走到一次小尝试", rationale)
        self.assertIn("行动菜单只在读者需要玩法时提供支持", source)
        self.assertIn("没有核验完整原演出", source)

    def test_rationale_and_source_limits_survive_all_editions(self):
        source = (ROOT / "docs/culture-shuaqi.md").read_text()
        self.assertIn(source, (ROOT / "llms-full.txt").read_text())
        self.assertIn(
            build.markdown(source, "docs/culture-shuaqi.md"),
            (ROOT / "index.html").read_text(),
        )
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            text = archive.read(
                "EPUB/" + epub.document_name("docs/culture-shuaqi.md")
            ).decode()
        for phrase in ("即使读者不照着做", "没有核验完整原演出", "未核验正文"):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
