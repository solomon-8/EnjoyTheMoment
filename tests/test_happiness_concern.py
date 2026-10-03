"""Preserve argument/source boundaries across formats, not a persuasion test."""
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


class HappinessConcernTests(unittest.TestCase):
    def test_argument_does_not_become_a_happiness_quota_or_reverse_ban(self):
        source = "essays/01-pleasure-is-an-end.md"
        text = (ROOT / source).read_text()
        for phrase in (
            "把快乐当正事，不是给快乐定业绩",
            "反馈应当帮助修改选择",
            "不是所有单项结果都毫无关系",
            "没有预测幸福感的变化",
            "没有证明放弃追求就会更幸福",
            "不能用“降低期待”替提供者免除责任",
            "给自己少打一次分，并不会凭空增加时间",
            "不是诊断，也不是治疗建议",
            "例子为虚构情境，不是用户案例",
            "保留选择的能力",
            "第三种不是天然不合理",
            "不是一个普遍最优算法",
            "不存在的晚上",
        ):
            self.assertIn(phrase, text)
        rendered = build.markdown(text, source)
        for anchor in (
            "pleasure-options", "pleasure-enough", "pleasure-not-quota",
            "pleasure-happiness-study", "pleasure-disappointment",
        ):
            self.assertEqual(rendered.count(f'id="{anchor}"'), 1)
        self.assertEqual(rendered.count("<table>"), 2)
        self.assertIn("pleasure-not-quota", (ROOT / "SHUAQI.md").read_text())

    def test_research_keeps_design_access_and_null_result_qualifications(self):
        text = (ROOT / "docs/evidence/B40-happiness-concern.md").read_text()
        for phrase in (
            "先行版，不是对最终刊版逐字核验",
            "图S1未核读",
            "未取得项目文件",
            "未复算或复现",
            "1,815", "每维四题", ".50–.60",
            "不是两类互斥人格",
            "没有临床诊断阈值",
            "只有E预注册",
            "不是快乐时长、刺激强度或临床诊断",
            "不是同一个人某天更担忧、下一天就更差",
            "没有预测幸福感的变化",
            "不等于每个样本每个结果都不显著",
            "−.58", "−.47", "−.20", "−.16",
            "−.12", "不是幸福减少12%",
            "未独立读取预注册核对差异",
            "不是感官刺激或愉悦有多强",
        ):
            self.assertIn(phrase, text)
        research = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual({r["id"] for r in research},
                         {f"B{n:02d}" for n in range(1, 49)})
        record = next(r for r in research if r["id"] == "B40")
        self.assertEqual(record["doi"], "10.1037/emo0001381")
        self.assertFalse(record["directly_validates_cards"])
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("B40" not in c["background_ids"] for c in cards))

    def test_retrieval_route_retains_conditions_and_whole_source(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {d["id"]: d for d in documents}
        for identifier, source in (
            ("E01", "essays/01-pleasure-is-an-end.md"),
            ("N40", "docs/evidence/B40-happiness-concern.md"),
        ):
            raw = (ROOT / source).read_bytes()
            self.assertEqual(by_id[identifier]["text"], raw.decode())
            self.assertEqual(by_id[identifier]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertIn(raw.decode(), (ROOT / "llms-full.txt").read_text())
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        note = next(n for n in notes if n["id"] == "N40")
        self.assertEqual(note["source_kind"], "study_reading_note")
        self.assertEqual(note["text"], by_id["N40"]["text"])
        route = next(r for r in routes if r["id"] == "R78")
        self.assertEqual(set(route["targets"]),
                         {"E01", "B40", "N40", "E06", "C09", "E03", "E11"})
        route_text = (ROOT / "docs/reading-map.md").read_text().split(
            '<a id="r78"></a>')[1]
        self.assertIn("纵向分析没有预测幸福感变化", route_text)
        self.assertIn("不称复现", route_text)
        self.assertIn("不生成量表诊断、快乐KPI或疗效保证", route_text)

    def test_epub_preserves_arguments_tables_and_navigation(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            essay = archive.read(
                "EPUB/text/essays--01-pleasure-is-an-end.xhtml").decode()
            note = archive.read(
                "EPUB/text/docs--evidence--B40-happiness-concern.xhtml").decode()
            self.assertIn('id="pleasure-not-quota"', essay)
            self.assertIn("B40-happiness-concern.xhtml", essay)
            self.assertIn("没有预测幸福感的变化", essay)
            self.assertIn("先行版，不是对最终刊版逐字核验", note)
            self.assertIn("不是同一个人某天更担忧、下一天就更差", note)
            self.assertEqual(note.count("<table>"), 2)
            self.assertIn("01-pleasure-is-an-end.xhtml#pleasure-not-quota", note)


if __name__ == "__main__":
    unittest.main()
