"""Guard argument order, provisional invitations and retrieval; not quality scores."""
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

SOURCE = "book/21-free-time.md"


class TimeStructureTests(unittest.TestCase):
    def test_four_questions_do_not_turn_into_a_scheduled_activity_list(self):
        text = (ROOT / SOURCE).read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M), [
            "一、空出来的时间，怎样才算到了自己手里？",
            "二、想让相聚发生，不等于要排满每一分钟",
            "三、谁为共同时间，放弃了自己的选择？",
            "四、没有尽兴，也不该把时间自动还给工作",
        ])
        order = ["一张空白日历", "连续时间不只是碎片的加总",
                 '<a id="time-making-room">', '<a id="time-tentative">',
                 '<a id="time-scheduling-study">', '<a id="time-shared-costs">',
                 '<a id="time-overlap">', '<a id="time-cancellation">',
                 '<a id="time-reservation">', '<a id="time-not-a-score">',
                 '<a id="time-empty">', '<a id="time-study">']
        locations = [text.index(t) for t in order]
        self.assertEqual(locations, sorted(locations))
        self.assertNotIn("前面讨论的取消权仍然成立", text)
        self.assertIn("[取消仍然可以讨论](#time-cancellation)", text)
        self.assertNotIn("<!-- pick:", text)

    def test_tentative_invitation_preserves_real_choice_and_strong_objection(self):
        text = (ROOT / SOURCE).read_text()
        part = text.split('<a id="time-tentative"></a>', 1)[1].split(
            '<a id="time-scheduling-study"></a>', 1)[0]
        for phrase in ("原创假想", "周六下午五点", "需要当天答复",
                       "没有一条路能同时保住全部选择",
                       "不是在敷衍", "确认之前，我们答应怎样为这次见面留时间",
                       "第一种少了其他机会", "第二种可能错过最想见的人",
                       "第三种可能最终凑不到一起",
                       "难道以后只有日程稳定的人，才配被等",
                       "等待也可以是本人愿意送给这段关系的时间",
                       "两人若本来就接受到时再说",
                       "不是要求每次说“周末见”都附一页条款",
                       "不能靠一句“别那么较真”"):
            self.assertIn(phrase, part)
        self.assertIn("essays/09-friends-not-assets.md#friends-partiality", part)
        self.assertNotIn("研究表明", part)

    def test_sources_keep_attendance_selection_and_uncertainty(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in ("明确时点组 67 人中有 33 人到场",
                       "宽时间窗口组 81 人中有 21 人到场",
                       "没有到场的人不能被擅自记成“零快乐”",
                       "不替多日假期、长期照料或具体个人作结论",
                       "p = .066", "p = .02",
                       "不是实际替他们减少工作并追踪半年",
                       "不是收回时间决定权的充分理由",
                       "本书不把它改判成违约"):
            self.assertIn(phrase, text)
        data = json.loads((ROOT / "data/research.json").read_text())
        self.assertEqual(len(data["records"]), 49)
        self.assertEqual(len(json.loads((ROOT / "data/catalog.json").read_text())["cards"]), 60)

    def test_efficiency_argument_keeps_the_objection_and_does_not_claim_a_study(self):
        text = (ROOT / SOURCE).read_text()
        part = text.split('<a id="time-efficiency-choice"></a>', 1)[1].split(
            "### 连续时间不只是碎片的加总", 1)[0]
        for phrase in ("原创假想", "答应完成这一份名单", "答应今晚一起帮到十点",
                       "答应一起把开场前必要的准备做完",
                       "任务未必一开始就分得公平", "能力不同",
                       "不是劳动权利的判断", "不能事后挑一个最有利于自己的版本",
                       "不是许诺它回来以后又能提高效率",
                       "节省可以用来多做，也可以用来少做"):
            self.assertIn(phrase, part)
        self.assertNotIn("研究表明", part)
        self.assertNotIn("J0", part)
        self.assertIn("09-constrained.md#constrained-cognitive", part)
        self.assertIn("07-rest-is-not-work.md#rest-returns", part)

    def test_full_retrieval_epub_and_links_keep_the_whole_disagreement(self):
        text = (ROOT / SOURCE).read_text()
        html = build.markdown(text, SOURCE)
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            epub = z.read("EPUB/text/book--21-free-time.xhtml").decode()
        for anchor in ("time-ownership", "time-making-room", "time-shared-costs",
                       "time-not-a-score", "time-tentative", "time-cancellation",
                       "time-scheduling-study", "time-overlap", "time-common",
                       "time-reservation", "不给空白写用途是否就是浪费",
                       "time-empty", "time-study", "time-worth",
                       "time-efficiency-choice",
                       "最后一个任务做完以后往往还会有最后一个"):
            self.assertEqual(html.count('id="' + anchor + '"'), 1)
            self.assertEqual(epub.count('id="' + anchor + '"'), 1)
        for anchor in ("time-ownership", "time-making-room", "time-shared-costs",
                       "time-not-a-score", "time-tentative", "time-cancellation",
                       "friends-partiality"):
            self.assertIn('href="#' + anchor + '"', html)
        self.assertIn("essays--09-friends-not-assets.xhtml#friends-partiality", epub)
        documents, routes = read.load_documents(ROOT)
        self.assertEqual(next(d for d in documents if d["id"] == "C21")["text"], text)
        route = next(r for r in routes if r["id"] == "R49")
        self.assertIn("E09", route["targets"])
        self.assertIn("不把朋友按可靠程度排榜", route["text"])
        self.assertIn("不是调查或普遍预约规则", route["text"])
        self.assertIn("不另算一项新证据", route["text"])
        self.assertIn("time-efficiency-choice", route["text"])
        self.assertIn("没有用B11/B27验证这个假想", route["text"])
        self.assertEqual(set(route["targets"]),
                         {"C21", "C09", "E07", "E09", "B11", "N11", "B27", "N27"})


if __name__ == "__main__":
    unittest.main()
