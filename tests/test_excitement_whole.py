"""Keep complete experience distinct from mandatory trials or escalating size."""
from pathlib import Path
import json
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build

SOURCE = "essays/02-excitement-without-escalation.md"

class ExcitementWholeTests(unittest.TestCase):
    def test_wholeness_has_a_specific_object_and_a_counterargument(self):
        text = (ROOT / SOURCE).read_text()
        section = text.split('<a id="excitement-whole"></a>', 1)[1].split(
            '<a id="excitement-information"></a>', 1)[0]
        for phrase in ("哪些东西一旦被删掉", "另设一段虚构表演", "迟到的朋友",
                       "不是实际演出的记录", "短片并不因此低级",
                       "完整保护的是想经历的关系", "范围来自愿望",
                       "也不能为了显得更完整，就替愿望不断加码",
                       "事前留出整晚，与事中必须熬到最后", "不把退出说成没有代价"):
            self.assertIn(phrase, section)
        self.assertIn("有些快乐，值得占用一整个晚上", text)
        self.assertIn("不等于用“活得精彩”证明风险越高越好", text)

    def test_clear_wish_exploration_and_unavailable_conditions_are_not_one_recipe(self):
        text = (ROOT / SOURCE).read_text()
        part = text.split('<a id="excitement-evening"></a>', 1)[1].split(
            '<a id="excitement-mixed-feelings"></a>', 1)[0]
        for phrase in ("不是读者反馈", "实际参与条件也已经核实",
                       "直接支持他把晚上交给演出", "如果他只知道不满足",
                       "不是三步流程", "探索可能无效", "今晚的条件却不成立",
                       "不必把整个晚上判成作废", "不是同一件工作"):
            self.assertIn(phrase, part)
        self.assertNotIn("此时有三种小试法", text)
        self.assertIn("两者没有一一对应的处方", text)
        self.assertNotIn("| 你说的“没劲” |", text)

    def test_links_and_legacy_titles_survive_in_generated_readers(self):
        text = (ROOT / SOURCE).read_text()
        html = build.markdown(text, SOURCE)
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            epub = z.read("EPUB/text/essays--02-excitement-without-escalation.xhtml").decode()
        for anchor in ("excitement-whole", "excitement-not-fun", "excitement-evening",
                       "e02--想要更刺激不等于想把自己弄坏",
                       "四种没劲可能要四个不同的出口", "情境刷了一小时想做点真正带劲的"):
            self.assertEqual(html.count('id="' + anchor + '"'), 1)
            self.assertEqual(epub.count('id="' + anchor + '"'), 1)
        for dest in ("waiting-different-goods", "waiting-pleasure-procrastination", "spending-learning"):
            self.assertIn('href="#' + dest + '"', html)
            self.assertIn('.xhtml#' + dest + '"', epub)
        route = next(x for x in json.loads((ROOT / "data/reading-map.json").read_text())["routes"] if x["id"] == "R03")
        self.assertIn("不是演出实录或观众效果实验", route["text"])
        self.assertIn("不把这些共享原则重复算成新的证据", route["text"])
        self.assertEqual(len(json.loads((ROOT / "data/research.json").read_text())["records"]), 50)
        self.assertEqual(len(json.loads((ROOT / "data/catalog.json").read_text())["cards"]), 60)

if __name__ == "__main__":
    unittest.main()
