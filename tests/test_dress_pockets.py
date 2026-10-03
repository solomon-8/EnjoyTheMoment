"""Checks published content, provenance and retrieval, not wearing outcomes."""

import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build


class DressPocketTests(unittest.TestCase):
    def test_history_and_original_judgments_remain_distinct(self):
        chapter = (ROOT / "book/16-dress.md").read_text()
        for phrase in ("2009.300.2241", "约1784", "Lady Clapham",
                       "约1690—1700", "这个范围不是全世界所有女性服装的共同年表",
                       "本书没有检查玩偶实物", "眼前资料没有建立这条统一因果链",
                       "不是本书亲手触摸过的实物", "漂亮可以是第一人称的感受",
                       "漂亮不需要永远实用，但不便必须有资格被说出来"):
            self.assertIn(phrase, chapter)
        for phrase in ("#dress-form-examples", "### 西装的语言，可以被重新分配",
                       "## 镜子里的合适，与身体里的合适",
                       "clothing-color-relations.png"):
            self.assertIn(phrase, chapter)
        self.assertEqual(chapter.count("!["), 2)
        rendered = build.markdown(chapter, "book/16-dress.md")
        self.assertEqual(rendered.count('src="data:image/png;base64,'), 1)
        self.assertEqual(rendered.count('src="data:image/jpeg;base64,'), 1)
        self.assertIn('href="#f66"', rendered)

    def test_open_access_image_and_reading_limits_are_preserved(self):
        path = ROOT / "docs/evidence/F66-pockets-and-dress.md"
        text = path.read_text()
        for phrase in ("本次返回429", "isPublicDomain", "2000 × 1895",
                       "880 × 833", "未裁切", "不是仅凭数据集许可",
                       "没有转载V&A照片", "未独立读取所引原始庭审",
                       "不作为本书当下建议", "不猜制作人", "没有幸福或自主性量表"):
            self.assertIn(phrase, text)
        image = (ROOT / "assets/media/pocket-met-157045.jpg").read_bytes()
        self.assertEqual(hashlib.sha256(image).hexdigest(),
                         "880475a581642d5ffd745c833a00580d0c72824e3696e2b939613d1f059a9598")
        self.assertTrue(image.startswith(b"\xff\xd8"))
        self.assertTrue(image.endswith(b"\xff\xd9"))
        encoded = base64.b64encode(image).decode()
        self.assertIn("data:image/jpeg;base64," + encoded,
                      (ROOT / "index.html").read_text())
        for filename in ("LICENSE", "assets/media/README.md"):
            credit = (ROOT / filename).read_text()
            for marker in ("pocket-met-157045.jpg", "The Metropolitan Museum of Art",
                           "2009.300.2241", "Marie Bernice Bitzer"):
                self.assertIn(marker, credit)

    def test_full_sources_remain_retrievable_and_not_a_new_study(self):
        for identifier, source in (
                ("C16", "book/16-dress.md"),
                ("F66", "docs/evidence/F66-pockets-and-dress.md")):
            result = json.loads(subprocess.check_output(
                [sys.executable, "tools/read.py", "--id", identifier], cwd=ROOT))
            self.assertTrue(result["complete"])
            self.assertEqual(result["record"]["text"], (ROOT / source).read_text())
            self.assertEqual(result["record"]["source_sha256"],
                             hashlib.sha256((ROOT / source).read_bytes()).hexdigest())
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        note = next(n for n in notes if n["id"] == "F66")
        self.assertEqual(note["source_kind"], "museum_history_record_and_image")
        self.assertEqual(len(notes), 137)
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(records), 48)
        self.assertNotIn("F66", {r["id"] for r in records})
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("F66" not in c["background_ids"] for c in cards))
        rendered = build.markdown(note["text"], note["source"])
        for anchor in ("dress-pocket-object", "dress-private-beauty",
                       "dress-carrying-tradeoffs"):
            self.assertIn('href="#' + anchor + '"', rendered)

    def test_route_retains_material_and_normative_boundaries(self):
        routes = json.loads((ROOT / "data/reading-map.json").read_text())["routes"]
        route = next(r for r in routes if r["id"] == "R63")
        self.assertEqual(set(route["targets"]),
                         {"C16", "F66", "F26", "F07", "F08", "C02", "C09", "E08"})
        for phrase in ("不是行为研究", "不自动把价值判断请求改成购物/穿搭清单",
                       "只是馆方个例", "不把CSV元数据CC0套到全部图片"):
            self.assertIn(phrase, route["text"])


if __name__ == "__main__":
    unittest.main()
