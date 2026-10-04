"""Argument hierarchy and retrieval integrity, not a measure of reader interest."""
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

SECTIONS = {'book/16-dress.md': {'stages': {'dress-wishes': '一、想要的好看，只有修正身体这一种吗？', 'dress-pockets': '二、一只口袋，怎样把漂亮与行动连在一起？', 'dress-use': '三、试衣间里的喜欢，能否进入日常生活？', 'dress-gaze': '四、别人的眼光，能参与到哪一步？'}, 'old_titles': ['好看是一个愿望，但不必只有一种好看', '不用先懂风格名称，也能看出一套衣服在做什么', '三件具体衣服：好看，不只有“把身体修正好”这一条路', '欣赏高级定制，不必把它当作生活资格', '没有口袋，少掉的只是一个装东西的地方吗？', '一只约1784年的口袋，把花纹和开口放在一起', '不是“口袋消失了，女人才开始拿包”', '藏起来的花纹，不一定要等别人夸才算数', '有口袋，也不等于这一晚更自由', '最强的反对意见：连漂亮都要交实用性作业吗？', '镜子里的合适，与身体里的合适', '纤维名字、表面样子与穿着感，不是同一层信息', '维护成本也是穿着体验，不是买完以后才发生的意外', '一件喜欢的衣服，怎样进入现有生活？', '给意见之前，先确认对方问的是什么', '想被人看见，也不丢人', '最强的反对意见：这会不会只是让消费更好听？']}, 'book/25-looking-at-art.md': {'stages': {'art-intention': '一、作者的意思，能替你决定看见什么吗？', 'art-choices': '二、从习作到成画，只是把细节补齐吗？', 'art-viewpoints': '三、认出一个人，为什么还没有看完？', 'art-exhibition': '四、走进一场展览，谁在安排你的注意？'}, 'old_titles': ['先把三个问题拆开：画了什么，怎样画，我有什么感觉', '《卧室》：同一个房间，颜色与线条可以说不同的话', '一封信能说明画家的打算，却不能替观众填写感受', '今天看到的蓝，不一定就是当年画下的蓝', '一处痕迹，未必只通向一个人的内心', '做过功课，还能坦率地说“不喜欢”吗？', '《大碗岛》：远处是一个下午，近处是许多决定', '草图不是“还没画好”：它保留了另一种可能', '认出它是什么，为什么还没有看完？', '展签不是标准答案，但也不只是可有可无的废话', '一场展览，常常在用相邻关系说话', '名作可以是入口，不应吞掉旁边所有东西', '“不好看”可以更具体，批评也能成为享受的一部分', '真正反对的，不是学习，而是把感受交给资格证']}, 'book/37-nightlife.md': {'stages': {'nightlife-place': '一、为什么要专门走进这一间屋子？', 'nightlife-time': '二、曲目一样，一晚为什么还能不同？', 'nightlife-repeat': '三、知道下一拍，为什么还想继续？', 'nightlife-belonging': '四、共享一个舞池，意味着怎样的关系？', 'nightlife-choice': '五、愿意为这一晚付出什么，又不能替谁答应？'}, 'old_titles': ['在家也能放同一首歌，为什么还要走这一趟？', '“气氛好”不是一个没有内容的答案', '一间游艇展厅，怎样被改写成舞池？', '漂亮不是问题，只有一种漂亮才是问题', 'DJ不只是把好听的歌排在一起', '高潮可以有价值，但整晚不是等一个爆点', '明明知道下一拍会来，为什么还想一直跳？', '都敲四下，为什么不一定是同一种四下？', '“中等切分更让人想动”，为什么还不是快乐配方？', '不是等它告诉你新消息，而是让自己继续在里面', '一间能待着的屋子，有时比一张热门歌单更重要', '与陌生人一起，不一定是为了认识陌生人', '“放开一点”，为什么有时听起来像另一份命令？', '值得晚一点回家，不等于越晚越值得', '最强的反对意见：这不就是花钱买一点逃避？', '另一种反对：为什么又把热闹写得比安静高级？']}}


class SensoryStructureTests(unittest.TestCase):
    def test_original_subsections_keep_order_inside_argument_groups(self):
        for path, spec in SECTIONS.items():
            with self.subTest(path=path):
                text = (ROOT / path).read_text()
                self.assertEqual(re.findall(r"^## (.+)$", text, re.M), list(spec["stages"].values()))
                self.assertEqual(re.findall(r"^### (.+)$", text, re.M), spec["old_titles"])

    def test_new_navigation_and_published_subsection_targets(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            for path, spec in SECTIONS.items():
                with self.subTest(path=path):
                    text = (ROOT / path).read_text()
                    rendered = build.markdown(text, path)
                    book = archive.read("EPUB/text/" + path.replace("/", "--").replace(".md", ".xhtml")).decode()
                    for anchor in list(spec["stages"]) + [epub.heading_slug(t) for t in spec["old_titles"]]:
                        for surface in (rendered, book):
                            self.assertEqual(surface.count('id="' + anchor + '"'), 1, anchor)
                    for anchor in spec["stages"]:
                        self.assertIn('href="#' + anchor + '"', rendered)

    def test_full_text_exports_do_not_substitute_outlines(self):
        documents, routes = read.load_documents(ROOT)
        docs = {d["source"]: d for d in documents}
        chapters = {d["source"]: d for d in json.loads((ROOT / "data/chapters.json").read_text())["chapters"]}
        full = (ROOT / "llms-full.txt").read_text()
        for path in SECTIONS:
            text = (ROOT / path).read_text()
            self.assertEqual(docs[path]["text"], text)
            self.assertEqual(chapters[path]["text"], text.strip())
            self.assertIn(text, full)

    def test_claim_limits_stay_with_the_concrete_material(self):
        limits = {
            "book/16-dress.md": ("不是全世界所有女性服装的共同年表", "没有证明某位携带者因此感到受压迫", "漂亮不需要永远实用，但不便必须有资格被说出来"),
            "book/25-looking-at-art.md": ("不是上方芝加哥所藏的1889年第二版", "关于组合来源，两馆的说法并不完全相同", "不能把它们说成一次连续绕行的记录"),
            "book/37-nightlife.md": ("想动”的二次模型整体检验不显著", "两个指标之间的差异已经被检验成立", "知道下一拍在哪里，不等于已经经历过下一拍", "这一刻没有升级，我仍想让它继续"),
        }
        for path, phrases in limits.items():
            text = (ROOT / path).read_text()
            for phrase in phrases:
                self.assertIn(phrase, text)

    def test_ai_routes_keep_arguments_not_a_sequence_of_activities(self):
        _, routes = read.load_documents(ROOT)
        routes = {r["id"]: r for r in routes}
        for rid, path in (("R26", "book/25-looking-at-art.md"), ("R63", "book/16-dress.md"), ("R70", "book/37-nightlife.md")):
            for anchor in SECTIONS[path]["stages"]:
                self.assertIn("#" + anchor, routes[rid]["text"])
        self.assertIn("不是出门流程", routes["R70"]["text"])
        self.assertIn("不能把它当作实验已证实的机制", routes["R70"]["text"])


if __name__ == "__main__":
    unittest.main()
