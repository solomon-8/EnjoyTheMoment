"""Preservation and retrieval checks, not tests of persuasion or wellbeing."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read


class DesirePleasureTests(unittest.TestCase):
    def test_disagreement_keeps_pursuit_pleasure_and_authority_separate(self):
        text = (ROOT / "essays/10-pleasure-not-retention.md").read_text()
        for phrase in (
            "想要不是命令，享乐不是服从",
            "看一个原创假想", "不是心理测验", "不是三种互斥的人",
            "我还想得到什么", "正在经历的部分，我喜欢吗",
            "知道这些以后，我还认可这个选择吗",
            "有一个愿望，不等于已经同意满足它的全部方式",
            "我喜欢的就是追逐", "谁来裁定我是不是真的快乐",
            "旁观者不能仅凭点击宣布你不喜欢",
            "真实的喜欢也不能消除失实说明或替他人同意",
            "研究没有把解释你生活的资格交给我们",
        ):
            self.assertIn(phrase, text)
        for anchor in (
            "digital-desire", "digital-desire-study",
            "digital-desire-pleasure", "digital-desire-authority",
            "digital-chosen-limits", "digital-experiment",
            "digital-model", "digital-limit-authority",
        ):
            self.assertEqual(text.count(f'<a id="{anchor}"></a>'), 1)
            rendered = build.markdown(text, "essays/10-pleasure-not-retention.md")
            self.assertEqual(rendered.count(f'id="{anchor}"'), 1)
            self.assertEqual((ROOT / "index.html").read_text().count(
                f'id="{anchor}"'), 1)

    def test_experiment_does_not_become_diagnosis_or_equivalence(self):
        essay = (ROOT / "essays/10-pleasure-not-retention.md").read_text()
        note = (ROOT / "docs/evidence/B42-cue-wanting-and-liking.md").read_text()
        for phrase in (
            "排除5人后分析36人", "相对握压次数增幅",
            "p = .85", "没有测量多巴胺",
            "一项显著、另一项不显著", "协变量控制",
        ):
            self.assertIn(phrase, essay)
        for phrase in (
            "2014-12-22", "未复现分析", "Firmenich",
            "主文没有清楚交代随机分派", "未取得或核读补充材料",
            "超过个人最大握力50%阈值", "迁移测试后另行评价",
            "1.88次", "p = .13", "p = .051", "t(34) = 2.20",
            "不是两组完全相同的证明", "未取得数据",
            "不能据此识别读者是否患病",
        ):
            self.assertIn(phrase, note)
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        record = next(r for r in records if r["id"] == "B42")
        self.assertEqual(record["doi"], "10.1037/xan0000052")
        self.assertEqual(record["verified_at"], "2026-10-02")
        self.assertEqual(record["access_level"], "full_text")
        self.assertFalse(record["directly_validates_cards"])
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertTrue(all("B42" not in c["background_ids"] for c in cards))
        self.assertEqual(len(cards), 60)

    def test_ai_routes_keep_entire_argument_and_source_limits(self):
        documents, routes = read.load_documents(ROOT)
        documents = {d["id"]: d for d in documents}
        routes = {r["id"]: r for r in routes}
        for ident, path in (
            ("E10", "essays/10-pleasure-not-retention.md"),
            ("N42", "docs/evidence/B42-cue-wanting-and-liking.md"),
        ):
            raw = (ROOT / path).read_bytes()
            self.assertEqual(documents[ident]["text"], raw.decode())
            self.assertEqual(documents[ident]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertIn(raw.decode().strip(), (ROOT / "llms-full.txt").read_text())
        route = routes["R80"]
        self.assertEqual(set(route["targets"]),
                         {"E10", "B42", "N42", "E04", "E02", "B28", "N28", "E11"})
        for phrase in ("不自动改答成戒手机", "组别随机分派", "不证明等效",
                       "不授予旁观者", "不是独立复现", "不验证J卡"):
            self.assertIn(phrase, route["text"])

    def test_epub_retains_reciprocal_links_and_argument(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            essay = z.read(
                "EPUB/text/essays--10-pleasure-not-retention.xhtml").decode()
            note = z.read(
                "EPUB/text/docs--evidence--B42-cue-wanting-and-liking.xhtml").decode()
            self.assertIn("想要不是命令，享乐不是服从", essay)
            self.assertIn("不是三种互斥的人", essay)
            self.assertIn("docs--evidence--B42-cue-wanting-and-liking.xhtml", essay)
            self.assertIn("essays--10-pleasure-not-retention.xhtml#digital-desire-study", note)
            self.assertIn("p = .051", note)
            self.assertIn("未取得或核读补充材料", note)


if __name__ == "__main__":
    unittest.main()
