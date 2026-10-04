"""Argument-boundary/retrieval regression; not evidence of reader preference."""
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

class PleasureTimingArcTests(unittest.TestCase):
    def test_time_alone_does_not_decide_and_full_wishes_still_count(self):
        text = (ROOT / 'essays/01-pleasure-is-an-end.md').read_text()
        section = text.split('<a id="pleasure-timely-response"></a>')[1].split(
            '<a id="pleasure-feedback"></a>')[0]
        for phrase in (
            '时间顺序不替代代价、意愿与条件的判断',
            '我们偏向让那个晚上发生', '不再索要一份长期收益报告',
            '不只给容易退出的小愿望', '不需要先把愿望缩小',
            '不是经过实验验证的决策法则',
            '结果可以换一天、独自去或不去', '不能替同行者先答应',
            '这是原创假想，不是购票步骤', '还在等什么',
            '回应不是执行，慎重也不是无限延期',
            '等待本身可以是想要的期待', '广告倒计时不自动成为自己的期限',
            '需要更充分地了解与确认', '允许不喜欢',
        ):
            self.assertIn(phrase, section)
        self.assertNotRegex(section, r'(?m)^- ')
        self.assertEqual(len(re.findall(r'^## ', text, re.M)), 5)
        self.assertEqual(len(re.findall(r'^### ', text, re.M)), 18)
        self.assertIn('03-now-or-later.md', section)
        self.assertIn('02-excitement-without-escalation.md#excitement-costs', section)
        for phrase in ('同一个人可以采用两种账本', '不把它安到参考作者头上',
                       '贡献、信仰、创造、责任与成就', '不必被一律劝回安静'):
            self.assertIn(phrase, text)

    def test_aliases_and_full_route_do_not_drop_old_arguments(self):
        raw = (ROOT / 'essays/01-pleasure-is-an-end.md').read_bytes()
        text = raw.decode()
        anchors = ['即时满足是否天生低级', '即时满足究竟在哪些地方有优先权',
                   'pleasure-timely-response']
        html = (ROOT / 'index.html').read_text()
        with ZipFile(ROOT / 'downloads/EnjoyTheMoment.epub') as z:
            epub = z.read('EPUB/text/essays--01-pleasure-is-an-end.xhtml').decode()
        for a in anchors:
            self.assertIn(a, check.anchors_for(text))
            self.assertEqual(html.count(f'id="{a}"'), 1)
            self.assertEqual(epub.count(f'id="{a}"'), 1)
        for phrase in ('没有证明它与“耍起”不相容', '尚未说清的别人劳动',
                       '不要求它预知未来', '不存在的晚上', '没有预测幸福感的变化',
                       '共同资金却不能由一个人决定'):
            self.assertIn(phrase, text)
        documents, routes = read.load_documents(ROOT)
        record = next(x for x in documents if x['id'] == 'E01')
        self.assertEqual(record['text'], text)
        self.assertEqual(record['source_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual((ROOT / 'llms-full.txt').read_text().count(text.strip()), 1)
        route = next(x for x in routes if x['id'] == 'R01')
        self.assertEqual(set(route['targets']), {'SHUAQI', 'E01', 'F86', 'F97'})
        self.assertIn('不自动改写成购票指令', route['text'])
        self.assertIn('不是五步行动处方', route['text'])
        self.assertIn('#pleasure-timely-response', route['text'])
        self.assertIn('essays--02-excitement-without-escalation.xhtml#excitement-costs', epub)
        exported = json.loads((ROOT / 'data/essays.json').read_text())['essays']
        self.assertEqual(next(x for x in exported if x['id'] == 'E01')['text'], text)

if __name__ == '__main__':
    unittest.main()
