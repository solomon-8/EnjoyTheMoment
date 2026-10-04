"""Guard adopted scope and complete retrieval; not a test of literary superiority."""
import hashlib
import json
import sys
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import read


class LeisureEndsTests(unittest.TestCase):
    def test_stronger_opponent_and_non_instrumental_reply_survive(self):
        text = (ROOT / 'essays/07-rest-is-not-work.md').read_text()
        section = text.split('<a id="rest-higher-life"></a>')[1].split(
            '<a id="rest-lafargue"></a>')[0]
        for phrase in (
            '这不只是别人管你', '第7节紧接着把沉思推到最高位置',
            '不能直接译成现代雇佣工作', '本书也不接受',
            '一件事不必值得拿整个人生去换，才值得拿一个晚上去过',
            '生活中一部分独立的好', '不是声称两节选读已经推翻',
            '两者都没有职业用途', '不需要靠表演恢复阅读能力',
            '没有同等的收获', '不说两边价值必然相等',
            '如果每晚都如此呢', '一次放弃不是毫无代价',
            '生活不必每一刻都在为“更好的生活”作准备',
        ):
            self.assertIn(phrase, section)
        self.assertIn('11-pleasure-and-reality.md#pleasure-quality', section)
        self.assertIn('这三个版本是虚构对照，不是读者案例', text)
        self.assertIn('05-play-is-not-performance.md', text)
        self.assertNotIn('<!-- pick:', text)

    def test_adopted_source_has_both_parts_and_no_empirical_upgrade(self):
        text = (ROOT / 'docs/evidence/F27-pleasure-philosophy.md').read_text()
        for phrase in (
            'W. D. Ross', '卷十第6、7节', '没有核读希腊文',
            '不能只截第6节', '不是原书案例', '本书不接受这种身份等级',
            '同一作品、同一署名译者', '不把两处表达重复计作两套原创理论',
            '没有直接核读《无政府、国家与乌托邦》1974 年原版',
            '不能称为原典核读', '数字文本、译文和第三方文章',
        ):
            self.assertIn(phrase, text)
        notes = json.loads((ROOT / 'data/evidence.json').read_text())['notes']
        self.assertEqual(len(notes), 143)
        note = next(n for n in notes if n['id'] == 'F27')
        self.assertEqual(note['text'], text)
        self.assertEqual(note['source_kind'], 'philosophical_primary_and_secondary')
        records = json.loads((ROOT / 'data/research.json').read_text())['records']
        self.assertNotIn('F27', {n['id'] for n in records})
        self.assertTrue(all('F27' not in c['background_ids'] for c in
                           json.loads((ROOT / 'data/catalog.json').read_text())['cards']))

    def test_full_retrieval_route_and_epub_keep_the_argument(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {d['id']: d for d in documents}
        route = next(r for r in routes if r['id'] == 'R41')
        self.assertIn('F27', route['targets'])
        self.assertTrue(set(route['targets']) <=
                        {d['id'] for d in read.linked_records(route, documents, ROOT)})
        self.assertIn('不重复计原创理论或行为研究', route['text'])
        html = (ROOT / 'index.html').read_text()
        with ZipFile(ROOT / 'downloads/EnjoyTheMoment.epub') as archive:
            for identifier, path, anchor in (
                ('E07', 'essays/07-rest-is-not-work.md', 'rest-higher-life'),
                ('F27', 'docs/evidence/F27-pleasure-philosophy.md', 'source-aristotle-leisure'),
            ):
                raw = (ROOT / path).read_bytes()
                self.assertEqual(by_id[identifier]['text'], raw.decode())
                self.assertEqual(by_id[identifier]['source_sha256'], hashlib.sha256(raw).hexdigest())
                self.assertEqual((ROOT / 'llms-full.txt').read_text().count(raw.decode().strip()), 1)
                target = 'EPUB/text/' + path.replace('/', '--').replace('.md', '.xhtml')
                xhtml = archive.read(target).decode()
                self.assertEqual(xhtml.count(f'id="{anchor}"'), 1)
                if identifier == 'E07':
                    self.assertEqual(html.count(f'id="{anchor}"'), 1)
                    self.assertIn('docs--evidence--F27-pleasure-philosophy.xhtml#source-aristotle-leisure', xhtml)
                else:
                    self.assertIn('essays--07-rest-is-not-work.xhtml#rest-higher-life', xhtml)
                    self.assertIn('第7节把沉思视为最高的幸福活动', xhtml)


if __name__ == '__main__':
    unittest.main()
