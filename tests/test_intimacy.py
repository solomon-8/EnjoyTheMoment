"""Content and retrieval guards, not clinical, consent or comprehension validation."""
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


class IntimacyTests(unittest.TestCase):
    def test_four_reading_lines_keep_invitation_distinctions(self):
        text = (ROOT / "book/35-intimacy.md").read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.M), [
            "一、向一个人靠近，不只是找回自己",
            "二、被主动想起，为什么不能只按次数算",
            "三、愿望不同，怎样仍有相处的余地",
            "四、激情不必被管理，选择仍可被纠正",
        ])
        invitation = text.split('<a id="intimacy-invitation"></a>', 1)[1].split(
            '<a id="intimacy-difference"></a>', 1)[0]
        for phrase in ("原创情境与价值讨论", "林和遥", "自己选择，不等于从未受对方影响",
                       "发起和安排是不是总由同一个人承担",
                       "在我没有提醒的时候，你有没有想起过我",
                       "不可能把“林曾提醒过”这段历史变成没发生",
                       "不能单独说明遥此前从未想起过他",
                       "没发生的行动、尚不知道的念头、已经失落的感受",
                       "缺失不必被夸大为对其他一切的判决",
                       "不把“都沟通了就应该满意”当答案",
                       "愿望可以长期存在，某一次仍然不合适",
                       "不把接受活动邀请当作任何身体接触的同意"):
            self.assertIn(phrase, invitation)
        self.assertNotIn("<!-- pick:", invitation)

    def test_invitation_is_not_a_claimed_experiment_or_model(self):
        _, routes = read.load_documents(ROOT)
        route = next(r for r in routes if r["id"] == "R67")
        for phrase in ("林与遥是原创假想", "不预测效果", "过去提醒也不自动否定现在的自主",
                       "主动邀请不预授接触同意", "不把沟通后满意当义务"):
            self.assertIn(phrase, route["text"])
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(notes), 142)
        self.assertEqual(len(records), 50)
        self.assertFalse(any("林和遥" in r.get("text", "") for r in notes + records))

    def test_invitation_entrances_survive_in_all_reading_surfaces(self):
        source = "book/35-intimacy.md"
        text = (ROOT / source).read_text()
        rendered = build.markdown(text, source)
        reader = (ROOT / "index.html").read_text()
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            epub = archive.read("EPUB/text/book--35-intimacy.xhtml").decode()
            for anchor in ("intimacy-closeness", "intimacy-invitation",
                           "intimacy-authored-invitation", "intimacy-signal-and-choice",
                           "intimacy-initiative-objection", "intimacy-invitation-range",
                           "intimacy-difference", "intimacy-judgment"):
                for output in (rendered, reader, epub):
                    self.assertEqual(output.count('id="' + anchor + '"'), 1)
            self.assertEqual(epub.count("<table>"), 2)
            self.assertIn("自己选择，不等于从未受对方影响", epub)

    def test_chapter_is_argument_not_frequency_prescription(self):
        text = (ROOT / "book/35-intimacy.md").read_text()
        for phrase in ("亲密不必拿次数证明，欲望也不必被假装没有", "原创假想",
                       "四个不能互相代答的问题", "未达到作者标注的10%显著性门槛",
                       "需要被认真看见，和需要被指定的人满足，是两回事",
                       "没有在该实验里检验这些替代安排", "不把友情写成性关系的低配",
                       "最强的反对意见", "没有最低频率"):
            self.assertIn(phrase, text)
        html = build.markdown(text, "book/35-intimacy.md")
        self.assertEqual(html.count('<table>'), 2)
        for target in ("#b36", "#n36", "#f69"):
            self.assertIn('href="' + target + '"', html)
        self.assertNotIn('<!-- pick:', text)

    def test_study_uncertainties_are_retained(self):
        text = (ROOT / "docs/evidence/B36-sexual-frequency.md").read_text()
        for phrase in ("64对", "128", "90天", "不是按性行为次数付钱",
                       "表2的对照表头却为60人", "未达到p < .1", "没有单独随机化",
                       "表7模型IV的年龄项印作−3.79", "欲望p = .2", "p = .45",
                       "最多124次观测", "未取得在线补充问卷", "没有回答自发发生"):
            # 128 is explicitly recorded in the structured study ledger.
            if phrase == '128':
                self.assertIn(phrase, (ROOT / 'docs/research.md').read_text())
            else:
                self.assertIn(phrase, text)
        self.assertIn('href="#intimacy-frequency"',
                      build.markdown(text, "docs/evidence/B36-sexual-frequency.md"))

    def test_position_statement_is_not_experiment_or_diagnosis(self):
        text = (ROOT / "docs/evidence/F69-sexual-health-and-asexuality.md").read_text()
        for phrase in ("不代表WHO正式立场", "不是新随机实验", "未独立核读",
                       "没有采用其中的人口比例", "不按单一行为作诊断",
                       "改变取向", "未采用"):
            self.assertIn(phrase, text)
        notes = json.loads((ROOT / 'data/evidence.json').read_text())['notes']
        f69 = next(n for n in notes if n['id'] == 'F69')
        self.assertEqual(f69['source_kind'], 'public_health_working_definition_and_professional_position')
        self.assertEqual(next(n for n in notes if n['id'] == 'N36')['source_kind'], 'study_reading_note')

    def test_new_chapter_and_notes_export_full_text_once(self):
        docs, routes = read.load_documents(ROOT)
        by_id = {x['id']: x for x in docs}
        for ident, path in [('C35', 'book/35-intimacy.md'),
                            ('N36', 'docs/evidence/B36-sexual-frequency.md'),
                            ('F69', 'docs/evidence/F69-sexual-health-and-asexuality.md'),
                            ('F80', 'docs/evidence/F80-symposium-and-wholeness.md')]:
            text = (ROOT / path).read_text()
            self.assertEqual(by_id[ident]['text'].strip(), text.strip())
            self.assertEqual(by_id[ident]['source_sha256'], hashlib.sha256((ROOT / path).read_bytes()).hexdigest())
            self.assertEqual((ROOT / 'llms-full.txt').read_text().count(text.strip()), 1)
        chapter = next(c for c in json.loads((ROOT / 'data/chapters.json').read_text())['chapters'] if c['id'] == 'C35')
        self.assertEqual(chapter['scope'], 'full_chapter')
        self.assertEqual(chapter['card_ids'], [])
        route = next(r for r in routes if r['id'] == 'R67')
        self.assertEqual(set(route['targets']),
                         {'C35', 'B36', 'N36', 'F69', 'F80', 'C02', 'C05',
                          'C07', 'C09', 'E06', 'E09'})
        self.assertTrue(set(route['targets']) <= {x['id'] for x in read.linked_records(route, docs, ROOT)})

    def test_study_does_not_reassign_existing_cards(self):
        records = json.loads((ROOT / 'data/research.json').read_text())['records']
        b36 = next(r for r in records if r['id'] == 'B36')
        self.assertEqual(b36['access_level'], 'full_text')
        self.assertEqual(b36['verified_at'], '2026-10-01')
        self.assertFalse(b36['directly_validates_cards'])
        cards = json.loads((ROOT / 'data/catalog.json').read_text())['cards']
        self.assertEqual(len(cards), 60)
        self.assertTrue(all('B36' not in card['background_ids'] for card in cards))

    def test_wholeness_is_a_dialogue_argument_not_an_empirical_law(self):
        note = (ROOT / 'docs/evidence/F80-symposium-and-wholeness.md').read_text()
        for boundary in ('Benjamin Jowett', '没有核读希腊原文', '不声称通读',
                         '不是狄奥提玛在宴会上直接发言', '性别等级', '年龄关系',
                         '身体熔合后思想必然一致', '不是心理实验', '不是新增B研究',
                         '原创假想', '不提供医学、心理诊断或当地法律结论'):
            self.assertIn(boundary, note)
        notes = json.loads((ROOT / 'data/evidence.json').read_text())['notes']
        f80 = next(n for n in notes if n['id'] == 'F80')
        self.assertEqual(f80['source_kind'], 'philosophical_literary_dialogue_primary')
        records = json.loads((ROOT / 'data/research.json').read_text())['records']
        self.assertEqual(len(records), 50)
        self.assertNotIn('F80', {r['id'] for r in records})
        chapter = (ROOT / 'book/35-intimacy.md').read_text()
        for distinction in ('神话没有说明熔合后思想必然一致', '不是我们的现成答案',
                            '不把自己说成残缺，不等于宣布自己不需要任何人',
                            '自主不必表现为永远不变', '散步推到身体接触'):
            self.assertIn(distinction, chapter)
        route = next(r for r in read.load_documents(ROOT)[1]
                     if r['id'] == 'R67')
        self.assertIn('不把不愿改变判为不够爱', route['text'])

    def test_wholeness_navigation_and_epub_keep_four_distinct_questions(self):
        chapter_path = 'book/35-intimacy.md'
        note_path = 'docs/evidence/F80-symposium-and-wholeness.md'
        anchors = ('intimacy-halves', 'intimacy-fusion',
                   'intimacy-dependence', 'intimacy-changing')
        html = (ROOT / 'index.html').read_text()
        text = (ROOT / chapter_path).read_text()
        for anchor in anchors:
            self.assertEqual(text.count('<a id="' + anchor + '"></a>'), 1)
            self.assertEqual(html.count('id="' + anchor + '"'), 1)
            self.assertIn('](#' + anchor + ')', text)
            self.assertEqual(build.local_href('../../' + chapter_path + '#' + anchor,
                                              note_path), '#' + anchor)
        with ZipFile(ROOT / 'downloads/EnjoyTheMoment.epub') as archive:
            chapter = archive.read('EPUB/text/book--35-intimacy.xhtml').decode()
            source = archive.read(
                'EPUB/text/docs--evidence--F80-symposium-and-wholeness.xhtml').decode()
            for anchor in anchors:
                self.assertEqual(chapter.count('id="' + anchor + '"'), 1)
            self.assertEqual(chapter.count('<table>'), 2)
            self.assertIn('F80-symposium-and-wholeness.xhtml', chapter)
            self.assertIn('book--35-intimacy.xhtml#intimacy-fusion', source)
            self.assertIn('不是狄奥提玛在宴会上直接发言', source)
            self.assertIn('未经同意', chapter)


if __name__ == '__main__':
    unittest.main()
