"""C18 structure and preserved retrieval boundaries; not a quality score."""
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

SOURCE = "book/18-celebration.md"
STAGES = {'celebration-reasons': '一、为什么值得把一天圈出来？', 'celebration-participation': '二、怎样让人真正进入这场庆祝？', 'celebration-giving': '三、礼物表达什么，又没有买下什么？', 'celebration-unfinished': '四、没有理想的结局，这一天还成立吗？'}
OLD_TITLES = ['过年不是年度优秀员工的专属福利', '年年差不多，为什么还要再来一次', '为什么偏要在大家都出门的那天出门？', '《西湖七月半》：来看月亮的人，究竟在看什么？', '散场以后，才是好时候——但谁等得起？', '“我不想错过”，会不会只是被气氛绑架？', '仪式有用的地方，不一定是隆重', '研究说“仪式可能增加享受”，不是让所有人照做', '主角想要的，与组织者想呈现的', '邀请要让人知道是在答应什么', '一场聚会，不需要所有人从头到尾同样兴奋', '预算买到了什么，不妨说具体', '谁布置、谁收拾，决定谁真正参加了庆祝', '礼物不是感情的计价器', '《麦琪的礼物》：感人的故事，不等于送礼说明书', '不是反对花大钱，是反对花钱取得感动的债权', '没有人记得，也不必把这一天撤销', '不是所有告别都需要被做成正能量', '最强的反对意见：没有成绩也庆祝，会不会让庆祝失去意义？']


class CelebrationStructureTests(unittest.TestCase):
    def test_four_questions_keep_nineteen_distinct_sections(self):
        text = (ROOT / SOURCE).read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M), list(STAGES.values()))
        self.assertEqual(re.findall(r"^### (.+)$", text, re.M), OLD_TITLES)
        self.assertLess(text.index("第三类与第五类"), text.index("## 二、"))
        self.assertLess(text.index("## 三、"), text.index("德拉（Della）"))
        self.assertLess(text.index("## 四、"), text.index("失落是真实的"))

    def test_old_and_new_routes_resolve_in_web_and_epub(self):
        text = (ROOT / SOURCE).read_text()
        html = build.markdown(text, SOURCE)
        reader = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            book = archive.read("EPUB/text/book--18-celebration.xhtml").decode()
        anchors = list(STAGES) + [epub.heading_slug(t) for t in OLD_TITLES]
        anchors += ["celebration-calendar", "celebration-west-lake", "celebration-magi"]
        for anchor in anchors:
            for rendered in (html, reader, book):
                self.assertEqual(rendered.count('id="' + anchor + '"'), 1, anchor)
        for anchor in STAGES:
            self.assertIn('href="#' + anchor + '"', html)

    def test_literary_and_research_boundaries_remain_local(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in ("不是一次调查归纳出的游客画像", "第三类与第五类",
                       "文章没有交代每个人的报酬", "不是庆祝活动的效果试验",
                       "没有达到常用的 .05 门槛", "没有显著交互",
                       "先分开礼物、心意与接收者的反应", "变成以他人的牺牲证明自己值得被爱",
                       "不是心理治疗", "本段不是人群安全或延长营业的建议"):
            self.assertIn(phrase, text)
        self.assertEqual(text.count("<details>"), 1)
        self.assertEqual(text.count("</details>"), 1)
        fold = text.split("<details>")[1].split("</details>")[0]
        self.assertIn("自己卖掉了金表", fold)
        self.assertNotIn("第三类与第五类", fold)

    def test_ai_gets_complete_chapter_and_not_an_event_checklist(self):
        text = (ROOT / SOURCE).read_text()
        documents, routes = read.load_documents(ROOT)
        self.assertEqual(next(d for d in documents if d["id"] == "C18")["text"], text)
        self.assertIn(text, (ROOT / "llms-full.txt").read_text())
        chapter = next(c for c in json.loads((ROOT / "data/chapters.json").read_text())["chapters"] if c["id"] == "C18")
        self.assertEqual(chapter["text"], text.strip())
        route = next(d for d in routes if d["id"] == "R17")
        self.assertEqual(route["targets"], ["C18","F44","F45","F81","B08","N08","C05","C08","E08","C21"])
        for anchor in STAGES:
            self.assertIn("#" + anchor, route["text"])
        self.assertIn("结构不是活动流程", route["text"])
        self.assertIn("用户未要结局时不要主动剧透", route["text"])


if __name__ == "__main__":
    unittest.main()
