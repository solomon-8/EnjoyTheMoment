"""Source scope, causal limits and canonical preservation; not a value verdict."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import epub
import read


class RealityFamiliarityTests(unittest.TestCase):
    def fetch(self, identifier):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = read.main(["--id", identifier], ROOT)
        self.assertEqual(code, 0)
        return json.loads(output.getvalue())

    def test_original_study_is_not_a_machine_trial_or_nozick_primary(self):
        note = self.fetch("F98")
        self.assertTrue(note["complete"])
        record = note["record"]
        self.assertEqual(record["source_kind"], "primary_study_and_philosophical_argument")
        raw = (ROOT / record["source"]).read_bytes()
        self.assertEqual(record["text"], raw.decode())
        self.assertEqual(record["source_sha256"], hashlib.sha256(raw).hexdigest())
        for phrase in ("每组24人", "不是现实／机器两种起点的随机对照",
                       "没有交代两次招募是否有人重叠", "152名独立参与者",
                       "不是从这批答卷拟合出的个人参数",
                       "不是实际体验机器试验", "本文内的诺齐克引文仍是转引"):
            self.assertIn(phrase, record["text"])

    def test_argument_preserves_mechanism_and_value_distinctions(self):
        essay = self.fetch("E11")
        text = essay["record"]["text"].split(
            '<a id="pleasure-familiarity"></a>', 1)[1].split(
                '<a id="reality-events"></a>', 1)[0]
        for phrase in ("不是一组从现实进入、一组从机器退出", "54%、13%和50%",
                       "文中没有报告同一批人从46%变到59%的前后变化",
                       "生活是否改变与选项怎样命名一起变了",
                       "专门显著性检验", "解释一个选择怎样产生",
                       "不能把没有发生的事改成发生过",
                       "没有自动作废", "不把新鲜奉为另一种命令"):
            self.assertIn(phrase, text)
        self.assertIn("F98", {r["id"] for r in essay["linked_records"]})
        self.assertIn("E11", {r["id"] for r in self.fetch("F98")["linked_records"]})
        route = self.fetch("R06")["record"]
        self.assertIn("F98", route["targets"])
        for phrase in ("χ²检验属于初次三组", "诺齐克原书仍未直接核读",
                       "差额不能单独归因于现状倾向"):
            self.assertIn(phrase, route["text"])

    def test_same_source_and_argument_reach_all_reading_formats(self):
        for ident, exported_path, key in [
                ("E11", "data/essays.json", "essays"),
                ("F98", "data/evidence.json", "notes")]:
            record = self.fetch(ident)["record"]
            exported = next(x for x in json.loads(
                (ROOT / exported_path).read_text())[key] if x["id"] == ident)
            self.assertEqual(exported["text"], record["text"])
            self.assertIn(record["text"].strip(), (ROOT / "llms-full.txt").read_text())
        with ZipFile(ROOT / "downloads/EnjoyTheMoment.epub") as archive:
            essay = archive.read("EPUB/" + epub.document_name(
                "essays/11-pleasure-and-reality.md")).decode()
            note = archive.read("EPUB/" + epub.document_name(
                "docs/evidence/F98-reality-and-familiarity.md")).decode()
        self.assertIn('id="pleasure-familiarity"', essay)
        self.assertIn("F98-reality-and-familiarity.xhtml#reality-study-design", essay)
        self.assertIn("11-pleasure-and-reality.xhtml#pleasure-familiarity", note)
        self.assertIn("不同选项措辞", note)

    def test_existing_secondary_source_retains_its_own_limits(self):
        text = self.fetch("F27")["record"]["text"]
        self.assertIn("没有直接核读", text)
        self.assertIn("没有采用二手转述的实验统计", text)
        self.assertIn("不是将本页二手统计改称原作阅读", text)
        self.assertIn("F98-reality-and-familiarity.md", text)


if __name__ == "__main__":
    unittest.main()
