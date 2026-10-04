"""Research detail may fold; claims, counterarguments and central limits may not."""
import hashlib
from pathlib import Path
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import read

CASES = {
    "E02": ("essays/02-excitement-without-escalation.md", (
        "也没有证明三种安排等效", "不是谁有权决定信息何时出现",
        "不能将其说成重读效果实验", "这是偏好问卷，不是刺激剂量实验",
        "不是临床诊断", "不是为每个人测出最佳强度",
        "不能把接近承受极限设成娱乐目标",
    ), ("p = .29", "978次", "877位", "66名", "48—58", "82%")),
    "E05": ("essays/05-play-is-not-performance.md", (
        "相关性", "没有纳入操纵训练", "后来有统计勘误",
        "更正后的数字也没有解决全部分歧",
        "刚学完更容易写出来，不等于隔一周也更容易写出来",
        "反复重读组的评分反而较低", "不是整个过程的享受量表",
        "不能擅自把训练写成快乐的敌人",
        "一种方法可以更适合完成目标，却没有因此取得替你选择目标的权力",
    ), ("2018年勘误", "14%不是", "120名18—24岁", "180人", "14个百分点")),
}


class ArgumentReadingTests(unittest.TestCase):
    def test_visible_route_is_an_argument_not_a_methods_gate(self):
        for ident, (path, claims, details) in CASES.items():
            text = (ROOT / path).read_text()
            folds = re.findall(r"<details>(.*?)</details>", text, re.S)
            self.assertEqual(len(folds), 2, ident)
            visible = re.sub(r"<details>.*?</details>", "", text, flags=re.S)
            for phrase in claims:
                self.assertIn(phrase, visible, (ident, phrase))
            for phrase in details:
                self.assertTrue(any(phrase in fold for fold in folds), (ident, phrase))
            for fold in folds:
                self.assertNotIn("<a id=", fold)
                self.assertNotRegex(fold, r"(?m)^#{1,6} ")
                self.assertRegex(fold, r"\s*<summary>[^<]+</summary>")
            self.assertNotIn("<details open", text)

    def test_full_retrieval_and_epub_do_not_lose_optional_methods(self):
        documents, _ = read.load_documents(ROOT)
        documents = {d["id"]: d for d in documents}
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            for ident, (path, claims, details) in CASES.items():
                text = (ROOT / path).read_text()
                self.assertEqual(documents[ident]["text"], text)
                self.assertEqual(documents[ident]["source_sha256"],
                                 hashlib.sha256(text.encode()).hexdigest())
                self.assertIn(text, (ROOT / "llms-full.txt").read_text())
                member = "EPUB/text/" + path.replace("/", "--").replace(".md", ".xhtml")
                tree = ET.fromstring(archive.read(member))
                rendered = "".join(tree.itertext())
                for phrase in claims + details:
                    self.assertIn(phrase, rendered, (ident, phrase))
                for summary in re.findall(r"<summary>(.*?)</summary>", text):
                    self.assertIn(summary, rendered)


if __name__ == "__main__":
    unittest.main()
