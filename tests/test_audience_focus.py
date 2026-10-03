"""Keep the argument and old links while removing a misleading either/or."""
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

SOURCE = "essays/08-life-without-an-audience.md"
TITLE = "E08 · 想被看见，也不必把生活交给观众打分"
ALIASES = {
    "不要用不发朋友圈建立另一条鄙视链": "audience-not-a-purity-test",
    "最强的反对意见没有展示怎么找到同好": "audience-three-requests",
}


class AudienceFocusTests(unittest.TestCase):
    def test_title_does_not_require_a_choice_between_pleasure_and_expression(self):
        text = (ROOT / SOURCE).read_text()
        self.assertIn("# " + TITLE, text)
        self.assertNotIn("# E08 · 你要的是快乐，还是看起来很精彩的人生？", text)
        self.assertIn(TITLE, (ROOT / "README.md").read_text())
        self.assertIn(TITLE.replace("E08 · ", "E08："),
                      (ROOT / "essays/04-buying-pleasure.md").read_text())
        for phrase in (
            "表达可以成为生活的一部分",
            "不能当作鉴定真心的试纸",
            "依赖回应的快乐，不是伪造的快乐",
            "也不把这个目标偷偷缩小",
            "不是“禁止享受被夸”的规定",
            "理解也不欠作者赞同",
        ):
            self.assertIn(phrase, text)

    def test_consolidation_keeps_distinct_audiences_and_no_purity_ranking(self):
        text = (ROOT / SOURCE).read_text()
        purity = text.split('id="audience-not-a-purity-test"></a>', 1)[1].split(
            'id="audience-three-requests"></a>', 1)[0]
        requests = text.split('id="audience-three-requests"></a>', 1)[1].split(
            'id="audience-admiration"></a>', 1)[0]
        self.assertIn("“真正会生活的人从来不晒”也不是更高明的答案", purity)
        self.assertIn("外人不能只凭发没发，判断经历是否真实", purity)
        for phrase in (
            "让更多人知道", "让某个人理解", "得到对作品的认真反馈",
            "和别人一起参与", "更不要求把追求广泛传播的人劝回私聊",
            "发出邀请不是获得关注的合同",
            "不能据一次可见数字诊断陌生人的感情",
        ):
            self.assertIn(phrase, requests)
        self.assertNotIn("### 不要用“不发朋友圈”建立另一条鄙视链", text)
        self.assertNotIn("### 最强的反对意见：没有展示，怎么找到同好？", text)

    def test_old_fragment_targets_are_preserved_next_to_their_arguments(self):
        text = (ROOT / SOURCE).read_text()
        old_title = "e08--你要的是快乐还是看起来很精彩的人生"
        html = build.markdown(text, SOURCE)
        for old, target in ALIASES.items():
            self.assertIn(f'<a id="{old}"></a>\n<a id="{target}"></a>', text)
        for anchor in (*ALIASES, *ALIASES.values(), old_title):
            self.assertIn(anchor, check.anchors_for(text))
            self.assertEqual(html.count(f'id="{anchor}"'), 1)

    def test_exported_full_text_preserves_sources_and_later_counterarguments(self):
        raw = (ROOT / SOURCE).read_bytes()
        docs, routes = read.load_documents(ROOT)
        essay = next(d for d in docs if d["id"] == "E08")
        self.assertEqual(essay["text"], raw.decode())
        self.assertEqual(essay["source_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertIn(raw.decode(), (ROOT / "llms-full.txt").read_text())
        data = json.loads((ROOT / "data/essays.json").read_text())["essays"]
        self.assertEqual(next(d for d in data if d["id"] == "E08")["title"], TITLE)
        self.assertEqual(set(next(r for r in routes if r["id"] == "R45")["targets"]),
                         {"E08", "C20", "B10", "N10", "B44", "N44"})
        for phrase in (
            "只读到作者公开的摘要", "不能独立核查这些机制",
            "场景有没有被安排，作者对场景作了什么声称，参与者是否愿意",
            "目标可以改，不能假装旧目标已经完成",
            "我们不要求从每个失败里挖出隐藏的幸福",
        ):
            self.assertIn(phrase, raw.decode())
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            epub = archive.read(
                "EPUB/text/essays--08-life-without-an-audience.xhtml").decode()
        for anchor in check.anchors_for(raw.decode()):
            self.assertEqual(epub.count(f'id="{anchor}"'), 1)
        self.assertIn(TITLE, epub)


if __name__ == "__main__":
    unittest.main()
