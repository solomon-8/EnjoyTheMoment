"""Content/retrieval/diagram guards, not housing-performance or reader-effect tests."""
import base64
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import build
import read


class HomeTests(unittest.TestCase):
    def test_lived_space_and_tradeoffs_not_asset_or_style_quota(self):
        text = (ROOT / 'book/36-home.md').read_text()
        for phrase in ('临时住处不等于临时人生', '1925年1月', '共同设计者',
                       '1936年返回', '不是施罗德住宅平面图', '不自动阻隔声音',
                       '转换需要付出多少劳动、由谁执行', '能决定窗外是什么',
                       '整洁可以是一种真正的快乐', '最强的反对意见',
                       '本章不解释某地租约', '没有实地进入住宅'):
            self.assertIn(phrase, text)
        html = build.markdown(text, 'book/36-home.md')
        self.assertEqual(html.count('<table>'), 1)
        self.assertEqual(html.count('src="data:image/png;base64,'), 1)
        self.assertIn('href="#f70"', html)
        self.assertNotIn('<!-- pick:', text)

    def test_source_kind_scope_and_nonclaims(self):
        text = (ROOT / 'docs/evidence/F70-home-and-schroder.md').read_text()
        for phrase in ('没有取得并通读该书', '未测性能', '不能逐项划分双方功劳',
                       '1936年返回', '房顶增加一层', '未采用其中内容',
                       '不转载馆方照片', '不是施罗德住宅图纸'):
            self.assertIn(phrase, text)
        html = build.markdown(text, 'docs/evidence/F70-home-and-schroder.md')
        for anchor in ('home-schroder', 'home-modes', 'home-view', 'home-temporary'):
            self.assertIn('href="#' + anchor + '"', html)
        notes = json.loads((ROOT / 'data/evidence.json').read_text())['notes']
        note = next(n for n in notes if n['id'] == 'F70')
        self.assertEqual(note['source_kind'], 'museum_architectural_and_residential_history')

    def test_diagram_reuses_shell_and_parallel_geometry(self):
        root = ET.parse(ROOT / 'assets/media/home-relations.svg').getroot()
        ns = {'s': 'http://www.w3.org/2000/svg'}
        self.assertEqual(root.attrib['viewBox'], '0 0 400 1040')
        for identifier in ('together', 'parallel', 'screened'):
            group = root.find('.//s:g[@id="' + identifier + '"]', ns)
            uses = [u.attrib['href'] for u in group.findall('s:use', ns)]
            self.assertEqual(uses[0], '#shell')
            if identifier != 'together':
                self.assertEqual(uses, ['#shell', '#separate-tables'])
        screen = root.find('.//s:path[@id="screen"]', ns)
        self.assertEqual(screen.attrib['d'], 'M170 31V135')
        # The shell spans y=0..166: the short segment leaves both ends open.
        self.assertNotIn('screen', [n.attrib.get('id') for n in root.find('.//s:g[@id="parallel"]', ns)])
        png = (ROOT / 'assets/media/home-relations.png').read_bytes()
        self.assertEqual(png[:8], b'\x89PNG\r\n\x1a\n')
        self.assertEqual(struct.unpack('>II', png[16:24]), (800, 2080))
        self.assertIn('data:image/png;base64,' + base64.b64encode(png).decode(),
                      (ROOT / 'index.html').read_text())
        self.assertIn('home-relations.svg', (ROOT / 'assets/media/README.md').read_text())

    def test_full_text_hash_routes_and_no_action_footer(self):
        documents, routes = read.load_documents(ROOT)
        by_id = {x['id']: x for x in documents}
        for identifier, path in [('C36', 'book/36-home.md'),
                                 ('F70', 'docs/evidence/F70-home-and-schroder.md')]:
            text = (ROOT / path).read_text()
            self.assertEqual(by_id[identifier]['text'].strip(), text.strip())
            self.assertEqual(by_id[identifier]['source_sha256'], hashlib.sha256((ROOT / path).read_bytes()).hexdigest())
            self.assertEqual((ROOT / 'llms-full.txt').read_text().count(text.strip()), 1)
        chapter = next(c for c in json.loads((ROOT / 'data/chapters.json').read_text())['chapters'] if c['id'] == 'C36')
        self.assertEqual(chapter['scope'], 'full_chapter')
        self.assertEqual(chapter['card_ids'], [])
        route = next(r for r in routes if r['id'] == 'R68')
        self.assertEqual(set(route['targets']), {'C36', 'F70', 'C07', 'F48', 'C09', 'C15', 'C17', 'C26', 'E06', 'E08'})
        self.assertTrue(set(route['targets']) <= {x['id'] for x in read.linked_records(route, documents, ROOT)})

    def test_not_an_added_behavioral_experiment_or_card(self):
        studies = json.loads((ROOT / 'data/research.json').read_text())['records']
        self.assertEqual(len(studies), 45)
        self.assertNotIn('F70', {s['id'] for s in studies})
        cards = json.loads((ROOT / 'data/catalog.json').read_text())['cards']
        self.assertEqual(len(cards), 60)
        self.assertTrue(all('F70' not in c['background_ids'] for c in cards))


if __name__ == '__main__':
    unittest.main()
