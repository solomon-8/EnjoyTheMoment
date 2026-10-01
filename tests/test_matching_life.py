"""Text, provenance and retrieval guards; not evidence of consumer psychology."""
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


class MatchingLifeTests(unittest.TestCase):
    def test_new_argument_keeps_real_aesthetic_preference_and_existing_choices(self):
        text = (ROOT / "book/06-spending.md").read_text()
        for phrase in (
            "买得起一件喜欢的东西，不等于答应升级整套生活",
            "新增了两种不同的愿望",
            "原愿望确实缺少必要条件",
            "本来就是关系，而不是孤立物件",
            "已有购买带来了身份要求",
            "不是为了找出一个绝对纯净的欲望",
            "愿望没有完成，不等于今天的使用只是试用",
            "不是要求立即拆封所有藏品",
            "真的更喜欢完整、统一的样子",
            "不必让生活通过物品的验收",
        ):
            self.assertIn(phrase, text)
        rendered = build.markdown(text, "book/06-spending.md")
        for anchor in (
            "spending-matching-life", "spending-diderot", "spending-three-additions",
            "spending-enjoy-before-complete", "spending-pass-arithmetic",
            "spending-learning", "spending-theatre-study", "spending-future-cost",
        ):
            self.assertEqual(rendered.count(f'id="{anchor}"'), 1)
        self.assertIn('href="#f76"', rendered)
        # Existing numerical comparisons remain four tables, not new study data.
        self.assertEqual(rendered.count("<table>"), 4)

    def test_historical_source_is_not_recast_as_an_experiment_or_biography(self):
        source = "docs/evidence/F76-diderot-and-matching.md"
        text = (ROOT / source).read_text()
        for phrase in (
            "法文原作数字文本", "1875", "15968129", "第15—22图",
            "印刷6、7、11页", "印刷8、9、12页图请求返回429",
            "未完成全篇逐字图文对校",
            "没有考证“狄德罗效应”一词的命名史",
            "旧地毯", "韦尔内画作",
            "正文叙述与后出的编者说明",
            "没有独立核查编者所引记账资料",
            "不是原文提出的三因素模型",
        ):
            self.assertIn(phrase, text)
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        note = next(n for n in notes if n["id"] == "F76")
        self.assertEqual(note["text"], text)
        self.assertEqual(note["source_kind"], "literary_philosophical_primary_text")
        self.assertIn(text, (ROOT / "llms-full.txt").read_text())
        research = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual({r["id"] for r in research}, {f"B{n:02d}" for n in range(1, 40)})
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("F76" not in c["background_ids"] for c in cards))

    def test_full_retrieval_and_reading_route_keep_arguments_with_limits(self):
        docs, routes = read.load_documents(ROOT)
        by_id = {d["id"]: d for d in docs}
        for identifier, source in (("C06", "book/06-spending.md"),
                                   ("F76", "docs/evidence/F76-diderot-and-matching.md")):
            raw = (ROOT / source).read_bytes()
            self.assertEqual(by_id[identifier]["text"], raw.decode())
            self.assertEqual(by_id[identifier]["source_sha256"], hashlib.sha256(raw).hexdigest())
        route = next(r for r in routes if r["id"] == "R76")
        self.assertEqual(set(route["targets"]), {"C06", "F76", "E04", "C26", "C36", "C08"})
        for identifier in route["targets"]:
            self.assertIn("[" + identifier, route["text"])
        self.assertIn("不默认劝少买", route["text"])
        self.assertIn("未全篇逐字对校", route["text"])
        self.assertIn("保留旧地毯", route["text"])

    def test_faq_explains_arguments_not_just_activities_and_reaches_epub(self):
        text = (ROOT / "docs/faq.md").read_text()
        self.assertNotIn("所以本仓库要求落到具体动作", text)
        self.assertNotIn("所以我们写菜单，不写排名", text)
        for phrase in (
            "附上六十张玩法卡，也不会自动",
            "行动卡是配套，不是论证的替身",
            "主观不等于没有可讨论的内容",
            "接受知识而反对价值排序",
        ):
            self.assertIn(phrase, text)
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            names = z.namelist()
            faq = next(n for n in names if n.endswith("docs--faq.xhtml"))
            rendered = z.read(faq).decode()
            self.assertIn("行动卡是配套，不是论证的替身", rendered)
            self.assertIn("book--06-spending.xhtml#spending-matching-life", rendered)


if __name__ == "__main__":
    unittest.main()
