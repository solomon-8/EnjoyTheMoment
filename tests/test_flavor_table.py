"""Preserve food-essay context and counterarguments, not certify enjoyment."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read

SOURCE = "book/14-flavor.md"
NOTE = "docs/evidence/F90-suiyuan-and-table.md"


class FlavorTableTests(unittest.TestCase):
    def test_three_lines_keep_old_technical_comparisons_and_entrances(self):
        text = (ROOT / SOURCE).read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M), [
            "这一口有什么差别",
            "标准能解释什么，不能替谁喜欢",
            "一桌热闹，不必是每道菜的最佳时刻",
        ])
        for anchor in ("flavor-structure", "flavor-judgment", "flavor-whole-meal",
                       "flavor-suiyuan", "flavor-ice-cream", "flavor-coffee",
                       "flavor-coffee-standards"):
            self.assertIn("](#" + anchor + ")", text)
        for phrase in ("100 毫升变成 150 毫升", "后一个约为 33.3%",
                       "3.6 ÷ 360 = 1.0%", "3.6 ÷ 20仍是18%",
                       "不是证明完全相同", "270不是受试者人数",
                       "可选的少，不等于享受能力低"):
            self.assertIn(phrase, text)
        html = build.markdown(text, SOURCE)
        self.assertEqual(html.count("<table>"), 2)
        self.assertEqual(html.count('src="data:image/png;base64,'), 1)

    def test_old_essay_is_a_challenge_not_a_modern_food_experiment(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in (
            "不是说耳朵不参与风味",
            "也不是说食物的颜色和摆盘没有价值",
            "不是我们今天一切火锅的实测结果",
            "不立即吃完，未必已经回答了菜做得怎样",
            "不是宣布袁枚的两句话必然自相矛盾",
            "不把劳动者写成供食客调教的工具",
            "不是袁枚记下的席面，也不是用餐实验",
            "不靠品尝来判断安全",
            "没有一种处理免费保住所有东西",
            "食物的某项状态变了，与整顿饭变差",
            "不需要谎称“其实口感完全没变”",
            "也不是被专家规训",
            "不足以抹掉已经约定的投入",
            "没有责任表演每一口都惊艳",
            "不总能和每道菜的最高完成度同时获得",
        ):
            self.assertIn(phrase, text)
        for link in ("../essays/11-pleasure-and-reality.md#pleasure-taste-choice",
                     "05-connection.md#connection-compromise"):
            self.assertIn(link, text)
        note = (ROOT / NOTE).read_text()
        for phrase in ("9733386", "第12—17图", "45页PDF", "请求返回429",
                       "文件页所载元数据", "没有通读全书",
                       "没有该括注", "不是可移植的厨房产能数据",
                       "不自动证明整本书平等对待所有参与者",
                       "仓库不复制整册PDF"):
            self.assertIn(phrase, note)

    def test_full_text_source_and_routes_keep_the_same_scope(self):
        documents, routes = read.load_documents(ROOT)
        docs = {d["id"]: d for d in documents}
        full = (ROOT / "llms-full.txt").read_text()
        for identifier, path in (("C14", SOURCE), ("F90", NOTE)):
            raw = (ROOT / path).read_bytes()
            self.assertEqual(docs[identifier]["text"], raw.decode())
            self.assertEqual(docs[identifier]["source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertEqual(full.count(raw.decode().strip()), 1)
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        note = next(n for n in notes if n["id"] == "F90")
        self.assertEqual(note["source_kind"],
                         "historical_food_essay_transcription_and_scan")
        route = next(r for r in routes if r["id"] == "R57")
        old_heading_alias = '<a id="r57--咖啡与理想标准描述不等于喜欢"></a>'
        self.assertIn(old_heading_alias, route["text"])
        previous_route = next(r for r in routes if r["id"] == "R56")
        self.assertNotIn(old_heading_alias, previous_route["text"])
        self.assertNotIn('<a id="r57"></a>', previous_route["text"])
        self.assertEqual(set(route["targets"]), {
            "C14", "C02", "C06", "B29", "N29", "F05", "F25", "F90", "E11", "C05"})
        for phrase in ("不立即吃完不证明菜坏", "古代辱称和厨者赏罚观",
                       "不重复计成新实验", "三种安排有真实损失"):
            self.assertIn(phrase, route["text"])
        self.assertEqual(len(json.loads((ROOT / "data/catalog.json").read_text())["cards"]), 60)
        self.assertEqual(len(json.loads((ROOT / "data/research.json").read_text())["records"]), 48)

    def test_epub_has_complete_argument_and_return_links(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            chapter = z.read("EPUB/text/book--14-flavor.xhtml").decode()
            note = z.read("EPUB/text/docs--evidence--F90-suiyuan-and-table.xhtml").decode()
            routes = z.read("EPUB/text/docs--reading-map.xhtml").decode()
        self.assertEqual(routes.count('id="r57--咖啡与理想标准描述不等于喜欢"'), 1)
        for anchor in ("flavor-structure", "flavor-judgment", "flavor-whole-meal",
                       "flavor-suiyuan", "flavor-table-time", "flavor-cook-objection"):
            self.assertEqual(chapter.count('id="' + anchor + '"'), 1)
        self.assertIn("docs--evidence--F90-suiyuan-and-table.xhtml", chapter)
        self.assertIn("book--14-flavor.xhtml#flavor-table-time", note)
        self.assertIn("book--14-flavor.xhtml#flavor-cook-objection", note)
        self.assertIn("没有责任表演每一口都惊艳", chapter)
        self.assertIn("不是可移植的厨房产能数据", note)


if __name__ == "__main__":
    unittest.main()
