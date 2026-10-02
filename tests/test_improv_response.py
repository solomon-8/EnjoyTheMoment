"""Content preservation and retrieval, not evidence of improv or wellbeing effects."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import read


class ImprovResponseTests(unittest.TestCase):
    def test_written_scene_keeps_alternatives_and_unknowns(self):
        text = (ROOT / "book/04-play.md").read_text()
        for phrase in (
            "本书原创的微型场景", "咱们帽子店", "这里是修车铺",
            "好，把它放回橱窗", "帽檐上就少一朵花",
            "不因为平常就算失败", "不是唯一正确答案",
            "不是假装记录现场即兴", "您昨天刚缝上的",
            "店钥匙到现在还在我手里", "没有确定帽子去了哪里",
            "帽子自己回来当作店里的怪日常", "钥匙为什么还在甲这里",
            "新增飞船也不是原罪", "不是为了给每一句话打分",
        ):
            self.assertIn(phrase, text)
        for anchor in ("play-offer", "play-response", "play-improv-objection",
                       "play-unrepeatable", "play-wanting-to-win"):
            self.assertEqual(text.count(f'<a id="{anchor}"></a>'), 1)
            self.assertEqual((ROOT / "index.html").read_text().count(f'id="{anchor}"'), 1)

    def test_acceptance_does_not_erase_character_refusal_or_real_stop(self):
        text = (ROOT / "book/04-play.md").read_text()
        for phrase in (
            "角色说“不”也能把故事接下去", "不同意角色要做的事",
            "现实中的人可以直接停止", "不需要先想出漂亮台词",
            "不欠全场一个继续好笑的办法", "共同创作可能因分歧而结束",
            "尽兴可以来自认真回应，而不只是不断得到",
        ):
            self.assertIn(phrase, text)
        note = (ROOT / "docs/evidence/F85-improv-and-response.md").read_text()
        for phrase in (
            "David Alger", "Hayley Kellett", "2018-04-17", "2021-04-27",
            "不是共同创作效果实验", "作者自述", "未播放嵌入视频",
            "不能从这里推出", "即兴绝对不准问问题", "不是现场即兴记录",
            "不能把它当成取得接触同意的证据", "没有唯一答案",
            "不增加B类背景研究", "不是法律上的要约",
        ):
            self.assertIn(phrase, note)

    def test_full_text_retrieval_and_route_keep_scope(self):
        documents, routes = read.load_documents(ROOT)
        docs = {d["id"]: d for d in documents}
        for ident, path in (("C04", "book/04-play.md"),
                            ("F85", "docs/evidence/F85-improv-and-response.md")):
            raw = (ROOT / path).read_bytes()
            self.assertEqual(docs[ident]["text"], raw.decode())
            self.assertEqual(docs[ident]["source_sha256"], hashlib.sha256(raw).hexdigest())
        note = next(n for n in json.loads((ROOT / "data/evidence.json").read_text())["notes"]
                    if n["id"] == "F85")
        self.assertEqual(note["source_kind"], "improv_teaching_and_practitioner_account")
        self.assertIn(note["text"], (ROOT / "llms-full.txt").read_text())
        route = next(r for r in routes if r["id"] == "R56")
        self.assertTrue({"C04", "F63", "F85"} <= set(route["targets"]))
        for phrase in ("不按三种回应给好笑程度排名", "现实参与者停止",
                       "目光接触不是同意证据", "不是快乐实验", "不保证协调必定成功"):
            self.assertIn(phrase, route["text"])
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(records), 47)
        self.assertNotIn("F85", {r["id"] for r in records})
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("F85" not in c["background_ids"] for c in cards))

    def test_epub_preserves_scene_and_reciprocal_links(self):
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as z:
            chapter = z.read("EPUB/text/book--04-play.xhtml").decode()
            note = z.read("EPUB/text/docs--evidence--F85-improv-and-response.xhtml").decode()
            self.assertIn("咱们帽子店", chapter)
            self.assertIn("docs--evidence--F85-improv-and-response.xhtml", chapter)
            for anchor in ("play-offer", "play-response", "play-improv-objection"):
                self.assertIn("book--04-play.xhtml#" + anchor, note)
            self.assertIn("作者自述", note)
            self.assertIn("不是现场即兴记录", note)


if __name__ == "__main__":
    unittest.main()
