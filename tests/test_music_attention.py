"""Music argument structure and source boundaries; not an enjoyment-effect test."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest
from zipfile import ZipFile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import build
import read
SOURCE = 'book/11-music.md'
NOTE = 'docs/evidence/F89-cage-and-listening.md'

class MusicAttentionTests(unittest.TestCase):
    def test_three_lines_start_from_works_not_a_vocabulary_exam(self):
        text = (ROOT / SOURCE).read_text()
        self.assertEqual(len(re.findall(r'^## ', text, re.M)), 3)
        for anchor in ('music-relations', 'music-judgment', 'music-own-evening',
                       'music-cage-frame', 'music-natural', 'music-culture-study',
                       'music-taste-history'):
            self.assertEqual(text.count(f'<a id="{anchor}"></a>'), 1)
        self.assertLess(text.index('### 四个音'), text.index('### 不奏出一个音'))
        self.assertLess(text.index('### 不奏出一个音'), text.index('### “有感觉”'))
        html = build.markdown(text, SOURCE)
        self.assertEqual(html.count('<table>'), 4)
        self.assertEqual(html.count('src="data:image/png;base64,'), 2)
        for phrase in ('不能只挑前一组的星号', 'p = .31', 'p = .60', 'p = .0003',
                       '不是先进与落后', '没有做版本盲听'):
            self.assertIn(phrase, text)

    def test_cage_case_does_not_pretend_to_be_a_listening_experiment(self):
        text = (ROOT / SOURCE).read_text()
        for phrase in ('这不就是给空气收费', '形式上的新问题，不是满意保证',
                       '不能只用“有无音符”', '本书假想', '这不是已验证的听众反应',
                       '不把所有声音一概封为好音乐', '不假定所有人拥有相同的听觉经验',
                       '不是从低级到高级的三关', '没有试听指定录音'):
            self.assertIn(phrase, text)
        self.assertIn('../essays/11-pleasure-and-reality.md#pleasure-taste-criticism', text)
        self.assertIn('15-neighborhood.md#street-paley', text)
        note = (ROOT / NOTE).read_text()
        for phrase in ('1994-07-15', '2012-01-28', '33秒与30秒不是同一记载',
                       '没有实际试听指定版本', '本次未核读这本书',
                       '不复制原稿照片', '不是实验', '不将作品标题或静默误认'):
            self.assertIn(phrase, note)

    def test_exported_source_and_retrieval_keep_the_whole_argument(self):
        text = (ROOT / SOURCE).read_text()
        note = (ROOT / NOTE).read_text()
        documents, routes = read.load_documents(ROOT)
        self.assertEqual(next(d for d in documents if d['id'] == 'C11')['text'], text)
        record = next(d for d in documents if d['id'] == 'F89')
        self.assertEqual(record['text'], note)
        self.assertEqual(record['source_sha256'], hashlib.sha256((ROOT / NOTE).read_bytes()).hexdigest())
        data = json.loads((ROOT / 'data/evidence.json').read_text())['notes']
        self.assertEqual(next(n for n in data if n['id'] == 'F89')['source_kind'],
                         'work_record_and_recipient_account')
        route = next(r for r in routes if r['id'] == 'R60')
        self.assertEqual(set(route['targets']), {'C11','C14','C33','B31','N31','F02','F15','F89','E11','C15'})
        for phrase in ('未裁决', '无观众效果结论', '不提供注意力练习', '不当新增证据'):
            self.assertIn(phrase, route['text'])
        full = (ROOT / 'llms-full.txt').read_text()
        self.assertEqual(full.count(text.strip()), 1)
        self.assertEqual(full.count(note.strip()), 1)
        self.assertEqual(len(json.loads((ROOT / 'data/catalog.json').read_text())['cards']), 60)
        self.assertEqual(len(json.loads((ROOT / 'data/research.json').read_text())['records']), 50)

    def test_epub_preserves_the_new_case_and_return_links(self):
        with ZipFile(ROOT / 'downloads/EnjoyTheMoment.epub') as z:
            chapter = z.read('EPUB/text/book--11-music.xhtml').decode()
            note = z.read('EPUB/text/docs--evidence--F89-cage-and-listening.xhtml').decode()
        self.assertEqual(chapter.count('<table'), 4)
        self.assertIn('形式上的新问题，不是满意保证', chapter)
        self.assertIn('docs--evidence--F89-cage-and-listening.xhtml#f89-versions', chapter)
        self.assertIn('essays--11-pleasure-and-reality.xhtml#pleasure-taste-criticism', chapter)
        self.assertIn('book--11-music.xhtml#music-cage-frame', note)
        for anchor in ('music-relations','music-judgment','music-own-evening','music-cage-frame'):
            self.assertEqual(chapter.count('id="' + anchor + '"'), 1)

if __name__ == '__main__':
    unittest.main()
