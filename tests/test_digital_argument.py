"""Preserve the argument and its limits; not evidence of reader persuasion."""
import hashlib
import re
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check
import read

SOURCE = "essays/10-pleasure-not-retention.md"
PARTS = (
    ("digital-value", "一、先分清：留下来、想要和喜欢，是不是同一回事？"),
    ("digital-conditions", "二、可以吸引我，不能替我把下一步答应掉"),
    ("digital-delegation", "三、我愿意设限，也不把决定权交给新家长"),
    ("digital-commercial-costs", "四、如果尊重拒绝会损失收入，我们还坚持吗？"),
)


class DigitalArgumentTests(unittest.TestCase):
    def test_four_argument_groups_and_old_questions_remain(self):
        text = (ROOT / SOURCE).read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M),
                         [title for _, title in PARTS])
        self.assertEqual(len(re.findall(r"^### .+$", text, re.M)), 16)
        self.assertEqual(len(re.findall(r"^#### .+$", text, re.M)), 3)
        opening = text.split("\n## ", 1)[0]
        for anchor, _ in PARTS:
            self.assertIn(f"](#{anchor})", opening)
        for heading in (
            "留得更久，和过得更好，中间缺了一句话",
            "方便与操纵，不能只看有没有“下一步”",
            "倒计时为什么要问“到零以后呢？”",
            "最贵的部分，可能在你决定之后才出现",
            "别让“不买”变成对自己的一次羞辱",
            "你今天不想继续，不代表昨天的喜欢是假的",
            "喜欢推荐，不代表必须把一切交给推荐",
            "省下来的娱乐时间，也可以继续用来娱乐",
            "最强的反对意见：免费服务也要活下去，难道不能劝人留下？",
        ):
            self.assertTrue(check.anchors_for("# " + heading) <=
                            check.anchors_for(text))
        self.assertLess(text.index('id="digital-experiment"'),
                        text.index('id="digital-model"'))
        self.assertLess(text.index('id="digital-model"'),
                        text.index('id="digital-commercial-costs"'))

    def test_honest_cost_keeps_the_strong_objection_and_distribution(self):
        text = (ROOT / SOURCE).read_text()
        section = text.split('<a id="digital-honest-cost"></a>', 1)[1].split(
            "### 为什么不只劝人“管住自己”？", 1)[0]
        for phrase in (
            "更难的原创假想", "刻意假定损失存在", "不把它写成真实行业统计",
            "下一季可能无法制作", "喜欢这项服务的人也可能承担代价",
            "对付不起新价格的人", "没看清条件或难以离开",
            "仍要面对已经作出的承诺", "不能靠别人没能成功拒绝来代领",
            "不能代表沉默者授权", "也不能要求工作室永远按原价继续",
            "我们自己少一些免费内容", "并不会独自解决分配问题",
            "不能用标题许诺正文没有的东西", "不能把误解当成主张获得了认同",
        ):
            self.assertIn(phrase, section)
        self.assertNotIn("[B", section)

    def test_source_scope_and_original_examples_survive(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in (
            "分析36人", "p = .85", "不能单凭这一点宣称两种心理过程",
            "没有测量多巴胺", "1,818", "140 个网站上的 157",
            "不是今天所有网站的比例", "不是对该服务今天界面的实测",
            "进入主要分析的有1,933人", "其他手机应用增加约12分钟",
            "p = .026", "q = .09", "p = .18", "q = .24",
            "不是给每一分钟贴标签后数出来的比例", "没有完成全面的福利分析",
            "不是给所有人开同一张戒断处方", "同一个晚上另一种快乐",
        ):
            self.assertIn(phrase, text)
        self.assertEqual(len(re.findall(r"^\| ---", text, re.M)), 3)

    def test_retrieval_routes_and_epub_preserve_the_argument(self):
        raw = (ROOT / SOURCE).read_bytes()
        text = raw.decode()
        documents, routes = read.load_documents(ROOT)
        essay = next(d for d in documents if d["id"] == "E10")
        self.assertEqual(essay["text"], text)
        self.assertEqual(essay["source_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertIn(text, (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R29")
        self.assertEqual(set(route["targets"]), {"E10", "B14", "F20", "N14"})
        for phrase in ("假想", "不是B14/F20研究结果或行业统计",
                       "不承诺透明设计必然更盈利", "条件透明不自动解决分配问题"):
            self.assertIn(phrase, route["text"])
        html = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            epub = archive.read("EPUB/text/essays--10-pleasure-not-retention.xhtml").decode()
            note = archive.read("EPUB/text/docs--evidence--B28-digital-choice.xhtml").decode()
        for anchor in [a for a, _ in PARTS] + ["digital-honest-cost"]:
            self.assertIn("#" + anchor, route["text"])
            self.assertEqual(html.count('id="' + anchor + '"'), 1)
            self.assertEqual(epub.count('id="' + anchor + '"'), 1)
        self.assertIn("essays--10-pleasure-not-retention.xhtml#digital-experiment", note)


if __name__ == "__main__":
    unittest.main()
