"""Guard the rest argument and its boundaries, not quality or reader attention."""
import hashlib
from pathlib import Path
import re
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import check
import read

SOURCE = 'essays/07-rest-is-not-work.md'
PARTS = (
    ('rest-value', '一、不是工作奖给生活的时间'),
    ('rest-cost', '二、代价是真的，生活也是真的'),
    ('rest-shared', '三、自己的热爱，不自动续订别人的时间'),
    ('rest-position', '四、把今天拿回来，不必交一份精彩证明'),
)


class RestRaceTests(unittest.TestCase):
    def test_argument_has_a_progression_not_a_flat_checklist(self):
        text = (ROOT / SOURCE).read_text()
        self.assertEqual(re.findall(r'^## (.+)$', text, re.M), [t for _, t in PARTS])
        self.assertEqual(len(re.findall(r'^### .+$', text, re.M)), 16)
        self.assertEqual(len(re.findall(r'^#### .+$', text, re.M)), 4)
        opening = text.split('\n## ', 1)[0]
        for anchor, _ in PARTS:
            self.assertIn(f'](#{anchor})', opening)
        self.assertIn('](#rest-race)', opening)
        for first, second in (
            ('rest-returns', 'rest-lafargue'),
            ('rest-leisure-command', 'rest-cost'),
            ('rest-real-income', 'rest-paid-evening'),
            ('rest-paid-evening', 'rest-race'),
            ('rest-race', 'rest-shared'),
            ('rest-service-work', 'rest-position'),
            ('rest-position', 'rest-no-verdict'),
        ):
            self.assertLess(text.index(f'id="{first}"'), text.index(f'id="{second}"'))

    def test_competition_can_have_both_real_gains_and_relative_costs(self):
        text = (ROOT / SOURCE).read_text()
        passage = text.split('<a id="rest-race"></a>', 1)[1].split(
            '<a id="rest-shared"></a>', 1)[0]
        for phrase in (
            '五个人都完成了约定任务', '新项目只有两个名额',
            '比较确实看作品质量，不是谁在线更久',
            '不是任何公司的招聘或晋升规则', '不是对现实机会概率的估计',
            '休息有价值，不等于休息没有竞争代价',
            '最后仍只有两人取得这两个名额',
            '这也不证明多出的方案毫无价值',
            '名额稀缺本身不等于安排不公',
            '不能要求别人放弃热爱',
            '不会凭空增加名额', '也未必适合每一种需要持续探索的工作',
            '不能影响安排的人，则不该独自承担',
            '小周若继续做方案，不等于他认输了',
            '规则值得讨论，也不等于个人今天就有安全退出的余地',
            '不把“绝不能落后”奉为有权占用全部生活的理由',
        ):
            self.assertIn(phrase, passage)
        self.assertNotRegex(passage, r'\[(?:B\d{2}|F\d{2}|J\d{3})\]')

    def test_old_tradeoffs_and_historical_limits_are_preserved(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in (
            '质量、收入、需求和人员都不变',
            '不能把它先说成没人要的垃圾',
            '并且永远拿不到那次任务的报酬',
            '也不准备用“玩好了反而赚得更多”来圆场',
            '具体责任需要具体处理', '自愿安排能否止于本人',
            '不能拿“尊重劳动”把服务失约变成顾客必须体谅',
            '本篇没有证据保证它们能保住全部体验、收入和可及性',
            '不是对任何劳动合同或法定权利作判断',
            '原文的主张，不是本书核实过的当代效果',
            '不能把每一句都当可执行政策',
            '不喜欢这次安排，不等于没有资格拥有这段时间',
        ):
            self.assertIn(phrase, text)
        self.assertEqual(len(re.findall(r'^\| ---', text, re.M)), 1)
        for title in ('“有用”究竟对谁有用',
                      '最强的反对意见：没有挣钱的能力，拿什么谈快乐？',
                      '演出结束了，为什么不能再多尽兴半小时？',
                      '我们愿意接受什么代价'):
            self.assertTrue(check.anchors_for('# ' + title) <= check.anchors_for(text))

    def test_reading_route_full_text_and_formats_keep_the_same_claim(self):
        raw = (ROOT / SOURCE).read_bytes()
        docs, routes = read.load_documents(ROOT)
        essay = next(d for d in docs if d['id'] == 'E07')
        self.assertEqual(essay['text'], raw.decode())
        self.assertEqual(essay['source_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertIn(raw.decode(), (ROOT / 'llms-full.txt').read_text())
        route = next(r for r in routes if r['id'] == 'R41')
        self.assertEqual(set(route['targets']),
                         {'E07', 'F82', 'C08', 'C09', 'C21', 'E01', 'B05', 'N05'})
        for phrase in ('五人争两个名额', '绝对改善', '同轮相对位置',
                       '不要求受限者先牺牲来示范', '不借F82/B05背书'):
            self.assertIn(phrase, route['text'])
        html = (ROOT / 'index.html').read_text()
        with ZipFile(ROOT / 'downloads/EnjoyTheMoment.epub') as z:
            epub = z.read('EPUB/text/essays--07-rest-is-not-work.xhtml').decode()
            source = z.read('EPUB/text/docs--evidence--F82-right-to-be-lazy.xhtml').decode()
        for anchor in [a for a, _ in PARTS] + ['rest-race']:
            self.assertEqual(html.count(f'id="{anchor}"'), 1)
            self.assertEqual(epub.count(f'id="{anchor}"'), 1)
            self.assertIn(f'href="#{anchor}"', html)
        self.assertIn('essays--07-rest-is-not-work.xhtml#rest-productivity-defense', source)
        self.assertIn('F82-right-to-be-lazy.xhtml', epub)


if __name__ == '__main__':
    unittest.main()
