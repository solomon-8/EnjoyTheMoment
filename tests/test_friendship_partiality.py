"""Protect argument distinctions and source limits, not reader response scores."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import check
import read

ESSAY = 'essays/09-friends-not-assets.md'
NOTE = 'docs/evidence/F57-friendship-and-reciprocity.md'
PARTS = (
    ('friends-value', '一、共同享乐，不等于互相供给快乐'),
    ('friends-terms', '二、不把友情算成价格，也要看见真正的付出'),
    ('friends-change', '三、关心一个人，不等于保住一种不变的相处'),
    ('friends-position', '四、相处已经发生，不必等未来证明'),
)


class FriendshipPartialityTests(unittest.TestCase):
    def test_structure_preserves_the_existing_argument_order(self):
        text = (ROOT / ESSAY).read_text()
        self.assertEqual(re.findall(r'^## (.+)$', text, re.M), [t for _, t in PARTS])
        self.assertEqual(len(re.findall(r'^### .+$', text, re.M)), 14)
        self.assertEqual(len(re.findall(r'^#### .+$', text, re.M)), 5)
        opening = text.split('\n## ', 1)[0]
        for anchor, _ in PARTS:
            self.assertIn(f'](#{anchor})', opening)
        for first, second in (
            ('friends-not-a-service', 'friends-aristotle'),
            ('friends-aristotle', 'friends-terms'),
            ('friends-reciprocity', 'friends-exchange-study'),
            ('friends-clear-terms', 'friends-change'),
            ('friends-comfort-and-agreement', 'friends-hard-times'),
            ('friends-limited', 'friends-partiality'),
            ('friends-partiality', 'friends-ending'),
            ('friends-ending', 'friends-position'),
        ):
            self.assertLess(text.index(f'id="{first}"'), text.index(f'id="{second}"'))
        for row in ('| 交换式 | 173 | 149 |', '| 关怀式 | 156 | 191 |'):
            self.assertIn(row, text)
        for phrase in ('每格10人', '未获显著支持', '不是两项实验实际检验的结果',
                       '不必把辛苦偷偷改名成享受', '不要求先把过去写坏'):
            self.assertIn(phrase, text)

    def test_partiality_does_not_erase_commitments_or_disappointment(self):
        text = (ROOT / ESSAY).read_text()
        section = text.split('<a id="friends-partiality"></a>', 1)[1].split(
            '### 分开玩，不代表关系正在失败', 1)[0]
        for phrase in (
            '尚未答应任何人，也没有占用共同资源',
            '另一个朋友更懂音乐', '不必先证明他是所有朋友里最有趣',
            '不因此获得每个周六的永久优先权',
            '不是今日私人选择自由的宣言',
            '四个人共同出钱、约好各带一张唱片',
            '临时取消另一人的分享',
            '共同安排也不必每分钟绝对平均',
            '不能让负责组织自动变成替所有人决定',
            '不是给私人聚会、社团或其他组织作法律分类',
            '一个圈子若公开说欢迎新伙伴',
            '要求每一次两人见面都必须开放，不是同一个要求',
            '没有失约，不等于没有损失',
            '却不能保证每个人被同等需要',
            '不能为了暂时安慰就许下自己并不想兑现的亲密',
            '尊重可以平等，亲近不必均分',
        ):
            self.assertIn(phrase, section)
        self.assertNotRegex(section, r'\[(?:B\d{2}|N\d{2}|J\d{3})\]')
        self.assertIn('#friendship-source-partiality)', section)

    def test_added_primary_section_is_dated_and_not_a_modern_prescription(self):
        text = (ROOT / NOTE).read_text()
        for phrase in (
            '第八卷第2、3、4、13节与第九卷第3、12节为**2026-09-30**',
            '第九卷第2节为**2026-10-02**',
            '第 **2、3、12** 节', '这七节为引用范围',
            '没有通读全书', '没有读取希腊文',
            '作者明确反对在所有事情上都优先同一个人',
            '先提出通常应回报恩惠，再讨论例外',
            '不能剪成“永远先还人情”', '不能剪成“喜欢谁就优先谁”',
            '本项目不采用其中的身份优先次序',
            '`nobility necessity`', '不擅自补连词或标点',
            '不是亚里士多德案例或验证过的社交方法',
            '不从原文得出聚会法律性质',
            '不验证 J025—J030',
        ):
            self.assertIn(phrase, text)
        self.assertIn('the must', text)
        research = json.loads((ROOT / 'data/research.json').read_text())['records']
        self.assertEqual(len(research), 46)
        self.assertNotIn('F57', {x['id'] for x in research})
        notes = json.loads((ROOT / 'data/evidence.json').read_text())['notes']
        self.assertEqual(len(notes), 129)
        note = next(x for x in notes if x['id'] == 'F57')
        self.assertEqual(note['source_kind'], 'philosophical_primary_translation')
        self.assertEqual(note['text'], text)

    def test_routes_full_text_and_reader_links_keep_the_same_scope(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {d['id']: d for d in documents}
        for identifier, path in (('E09', ESSAY), ('F57', NOTE)):
            raw = (ROOT / path).read_bytes()
            self.assertEqual(by_id[identifier]['text'], raw.decode())
            self.assertEqual(by_id[identifier]['source_sha256'], hashlib.sha256(raw).hexdigest())
            self.assertIn(raw.decode(), (ROOT / 'llms-full.txt').read_text())
        routes = {r['id']: r for r in routes}
        self.assertEqual(set(routes['R05']['targets']), {'E09', 'F57'})
        self.assertEqual(set(routes['R75']['targets']), {'E09', 'B39', 'N39', 'F57', 'C05', 'C06'})
        self.assertIn('指定七节', routes['R05']['text'])
        self.assertIn('不冒充重读或通读两卷', routes['R05']['text'])
        self.assertIn('不用B39学生实验验证偏爱', routes['R75']['text'])
        html = (ROOT / 'index.html').read_text()
        with ZipFile(ROOT / 'downloads/EnjoyTheMoment.epub') as archive:
            essay = archive.read('EPUB/text/essays--09-friends-not-assets.xhtml').decode()
            note = archive.read('EPUB/text/docs--evidence--F57-friendship-and-reciprocity.xhtml').decode()
        for anchor in [a for a, _ in PARTS] + ['friends-partiality']:
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
            self.assertEqual(essay.count(f'id="{anchor}"'), 1)
            self.assertIn(f'href="#{anchor}"', html)
        self.assertEqual(note.count('id="friendship-source-partiality"'), 1)
        self.assertIn('F57-friendship-and-reciprocity.xhtml#friendship-source-partiality', essay)
        self.assertIn('essays--09-friends-not-assets.xhtml#friends-partiality', note)
        self.assertTrue(check.anchors_for('# 允许散场，为什么不等于抹掉一起的岁月') <=
                        check.anchors_for((ROOT / ESSAY).read_text()))


if __name__ == '__main__':
    unittest.main()
