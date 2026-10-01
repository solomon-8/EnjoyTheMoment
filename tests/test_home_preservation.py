"""Source and export guards; not a housing-performance or reader-effects test."""
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


class HomePreservationTests(unittest.TestCase):
    def test_new_argument_keeps_different_kinds_of_continuity_and_objections(self):
        source = "book/36-home.md"
        text = (ROOT / source).read_text()
        for phrase in (
            "保住一间房，还是保住一种生活",
            "想保留开放的感受，不等于可以不管理开放的代价",
            "清理与抹掉历史，不是必然相同的操作",
            "不凭照片判断霉变、材料状态或安全",
            "同一件实物继续存在",
            "一种空间关系继续存在",
            "一种实践继续发生",
            "不是计划对所有家庭制定的三分类",
            "不能把“要求辨明”说成“已经全部辨明”",
            "可普通人的家，凭什么要按博物馆来过",
            "其他人默认答应终身维护它",
            "租期不确定", "同住，不等于共享一种理想的家",
        ):
            self.assertIn(phrase, text)
        rendered = build.markdown(text, source)
        for anchor in (
            "home-arrival", "home-schroder", "home-modes", "home-view",
            "home-objects", "home-eames", "home-traces", "home-continuity",
            "home-preservation-objection", "home-temporary", "home-sharing",
            "home-objections", "home-lived",
        ):
            self.assertEqual(rendered.count(f'id="{anchor}"'), 1)
        self.assertEqual(rendered.count("<table>"), 1)
        self.assertEqual(rendered.count('src="data:image/png;base64,'), 1)
        self.assertIn('href="#f78"', rendered)
        self.assertNotIn("<!-- pick:", text)

    def test_source_does_not_turn_policy_into_completed_work_or_housing_advice(self):
        text = (ROOT / "docs/evidence/F78-eames-and-lived-preservation.md").read_text()
        for phrase in (
            "不是通读208页", "315页PDF", "不据该文件新增技术结论",
            "119、155、161—163页另目视核对",
            "不是监测原始数据或所有实施后的性能结果",
            "不是每项政策已经执行",
            "不能当作多个独立团队的复现",
            "不是直接取得采访录音",
            "C1.4", "C1.5", "C1.15", "B7.7", "B7.4—B7.6",
            "2016年图注不保证2026年实时陈列完全相同",
            "替代物标识不足",
            "不以2018计划直接判定2026仍存在同样缺口",
            "文件可下载不等于其图像与全文属于公有领域",
        ):
            self.assertIn(phrase, text)
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        note = next(n for n in notes if n["id"] == "F78")
        self.assertEqual(note["text"], text)
        self.assertEqual(note["source_kind"], "institutional_conservation_plan_and_reporting")
        research = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual({r["id"] for r in research},
                         {f"B{n:02d}" for n in range(1, 42)})
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("F78" not in c["background_ids"] for c in cards))

    def test_full_retrieval_and_cross_source_access_scope_are_preserved(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {d["id"]: d for d in documents}
        for identifier, source in (
            ("C36", "book/36-home.md"),
            ("F78", "docs/evidence/F78-eames-and-lived-preservation.md"),
        ):
            raw = (ROOT / source).read_bytes()
            self.assertEqual(by_id[identifier]["text"], raw.decode())
            self.assertEqual(by_id[identifier]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertIn(raw.decode(), (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R79")
        self.assertEqual(set(route["targets"]),
                         {"C36", "F78", "F70", "C26", "F68", "C17", "C09", "E01"})
        text = (ROOT / "docs/reading-map.md").read_text().split('<a id="r79"></a>')[1]
        self.assertIn("不能把后面的政策当成这些缺口已经解决", text)
        self.assertIn("不开出采光、通风、温湿度、除霉", text)
        f70 = (ROOT / "docs/evidence/F70-home-and-schroder.md").read_text()
        self.assertIn("未采用其中内容", f70)
        self.assertIn("不以本条失败记录代表所有相关材料的可访问性", f70)
        self.assertIn("F78", (ROOT / "docs/sources.md").read_text())

    def test_epub_keeps_new_argument_and_old_diagram(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            chapter = archive.read("EPUB/text/book--36-home.xhtml").decode()
            source = archive.read(
                "EPUB/text/docs--evidence--F78-eames-and-lived-preservation.xhtml").decode()
            self.assertIn('id="home-eames"', chapter)
            self.assertIn("F78-eames-and-lived-preservation.xhtml", chapter)
            self.assertIn("不能把“要求辨明”说成“已经全部辨明”", chapter)
            self.assertIn("不是通读208页", source)
            self.assertIn("替代物标识不足", source)
            self.assertEqual(chapter.count("<table>"), 1)
            self.assertIn("home-relations.png", chapter)
            self.assertEqual(archive.read("EPUB/images/home-relations.png"),
                             (ROOT / "assets/media/home-relations.png").read_bytes())


if __name__ == "__main__":
    unittest.main()
