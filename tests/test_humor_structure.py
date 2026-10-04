"""Preserve C24's arguments, provenance and old routes; not a quality score."""
import json
from pathlib import Path
import re
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import epub
import read

SOURCE = "book/24-humor.md"
STAGES = {
    "humor-attention": "一、为什么要这么认真读一件“没用”的事？",
    "humor-expression": "二、一个转折怎样起作用？",
    "humor-scenes": "三、笑点已经知道，为什么还愿意看下去？",
    "humor-context": "四、谁在一起玩，谁在替笑声付代价？",
}
OLD_TITLES = [
    "一个转弯：从普通陈述到可以看见的错位",
    "反转不只靠最后一句，也靠前面让人等什么",
    "把一条歪理认真执行，能长出什么",
    "重复与回扣：第二次出现时，意思已经不同",
    "同一件小事，可以从三个方向变形",
    "一本正经、故意装傻、明显夸张，不是同一种声音",
    "一盘三明治：台词还在讲礼貌，手已经拆了台",
    "不是乱说：一句话调换位置，关系已经变了",
    "时间停在六点：让一句歪理长出家具、杯子和后果",
    "知道结尾以后，还能看什么？",
    "为什么要这么认真读一件“没用”的事？",
    "“良性违背”提供一个视角，不是全世界笑话的总开关",
    "一个笑话里，至少有四个不同位置",
    "“我们关系好”不是永久授权",
    "自嘲可以是表达，不必成为入场费",
    "可以拿问题开玩笑，不必拿求助的人当笑点",
    "幽默有时能拆掉权威，也能替权威卸责",
    "发出去以后，上下文不会自动跟着走",
    "没有人笑，下一句不必更狠",
    "最强的反对意见：顾虑这么多，幽默不就没了？",
]


class HumorStructureTests(unittest.TestCase):
    def test_value_expression_scenes_and_context_are_distinct_stages(self):
        text = (ROOT / SOURCE).read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M), list(STAGES.values()))
        self.assertEqual(re.findall(r"^### (.+)$", text, re.M),
                         OLD_TITLES[:10] + OLD_TITLES[11:])
        positions = [text.index('<a id="' + anchor + '"></a>') for anchor in STAGES]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(text.index("有些事情值得认真投入"),
                        text.index("先看两句话"))
        self.assertLess(text.index("欣赏者不是尚未升级的创作者"),
                        text.index('<a id="humor-context"></a>'))
        self.assertEqual(text.count("下面的研究和关系讨论补上这个维度"), 1)

    def test_all_old_heading_fragments_work_on_web_and_epub(self):
        text = (ROOT / SOURCE).read_text()
        html = build.markdown(text, SOURCE)
        reader = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            package_text = archive.read("EPUB/text/book--24-humor.xhtml").decode()
        anchors = list(STAGES) + [epub.heading_slug(title) for title in OLD_TITLES]
        anchors += ["humor-sandwich", "humor-language", "humor-time", "humor-return"]
        for anchor in anchors:
            for rendered in (html, reader, package_text):
                self.assertEqual(rendered.count('id="' + anchor + '"'), 1, anchor)
        for anchor in STAGES:
            self.assertIn('href="#' + anchor + '"', html)

    def test_scene_and_research_limits_stay_in_the_chapter(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in (
            "未注明作品出处的例句为本书原创说明", "不是受众测试结果",
            "观众先看见，人物继续装不知道", "不能给它补上一个几秒的停顿",
            "没有得到完整系统说明", "不保证第二次更好笑", "beat time",
            "不是作者或讲笑话的人替所有相关者宣布客观无害",
            "觉得好笑与反感能够一起出现", "没有因此证明所有文字游戏",
            "不提供治疗方法", "我们允许尖锐、荒唐、尴尬、黑色幽默",
            "欣赏者不是尚未升级的创作者", "不编造他说过的话",
        ):
            self.assertIn(phrase, text)
        fold = text.split("<details>", 1)[1].split("</details>", 1)[0]
        self.assertIn("空盘", fold)
        self.assertNotIn("beat time", fold)
        self.assertEqual(text.count("<details>"), 1)
        self.assertEqual(text.count("</details>"), 1)

    def test_ai_retrieval_keeps_complete_text_and_stage_routes(self):
        text = (ROOT / SOURCE).read_text()
        documents, routes = read.load_documents(ROOT)
        self.assertEqual(next(doc for doc in documents if doc["id"] == "C24")["text"], text)
        self.assertIn(text, (ROOT / "llms-full.txt").read_text())
        chapter = next(row for row in json.loads((ROOT / "data/chapters.json").read_text())["chapters"]
                       if row["id"] == "C24")
        self.assertEqual(chapter["text"], text.strip())
        self.assertEqual(chapter["card_ids"], [])
        route = next(row for row in routes if row["id"] == "R20")
        self.assertEqual(set(route["targets"]), {"C24", "F37", "B13", "N13"})
        for anchor in STAGES:
            self.assertIn("#" + anchor, route["text"])
        self.assertIn("不要把欣赏喜剧改成必须创作笑话的任务", route["text"])
        self.assertIn("折叠区只包住三明治场景后段", route["text"])


if __name__ == "__main__":
    unittest.main()
