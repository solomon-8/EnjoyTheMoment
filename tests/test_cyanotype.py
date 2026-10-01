"""Content/provenance/retrieval regression, not artistic or reader-outcome tests."""

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


class CyanotypeTests(unittest.TestCase):
    def test_observation_does_not_become_universal_truth(self):
        chapter = (ROOT / "book/20-photography.md").read_text()
        for phrase in ("2005.100.557 (78)", "约1853年",
                       "没有检查原作、翻阅完整册页",
                       "蓝色是外观线索，不是鉴定证明",
                       "不是发现了作者唯一的构图意图",
                       "你希望它忠实于什么",
                       "材料的参与、构图的安排和故事的断言，是三件事",
                       "照片不必记录得更多，才值得你看得更久",
                       "没有完成原来的任务"):
            self.assertIn(phrase, chapter)
        for anchor in ("photo-viewpoint", "photo-duration", "photo-sequence",
                       "photo-audience", "photo-contact", "photo-cyanotype-object",
                       "photo-selective-truth", "photo-arranged-presence",
                       "photo-process-objection"):
            self.assertIn('id="' + anchor + '"', chapter)
        rendered = build.markdown(chapter, "book/20-photography.md")
        self.assertEqual(rendered.count('src="data:image/png;base64,'), 2)
        self.assertEqual(rendered.count('src="data:image/jpeg;base64,'), 1)
        self.assertIn('href="#f67"', rendered)

    def test_image_and_source_limits_remain_visible(self):
        note = (ROOT / "docs/evidence/F67-cyanotype-and-selection.md").read_text()
        for phrase in ("2026-06-16", "2022-11-07", "perhaps",
                       "不是本书转载的Met藏品", "没有用现代分类数据库",
                       "3266 × 4000", "720 × 882", "不提供制作教程",
                       "不等于所有蓝晒都属于植物物影照片", "未裁切",
                       "CSV的CC0不自动包括全部图像", "不是行为研究"):
            self.assertIn(phrase, note)
        image = (ROOT / "assets/media/atkins-met-291575.jpg").read_bytes()
        self.assertEqual(hashlib.sha256(image).hexdigest(),
                         "fdc021e8e7e2675a5e7e03522c163cdf8bba4fc7dd41cfe92f4a49fcd91ffd14")
        self.assertTrue(image.startswith(b"\xff\xd8") and image.endswith(b"\xff\xd9"))
        self.assertIn("data:image/jpeg;base64," + base64.b64encode(image).decode(),
                      (ROOT / "index.html").read_text())
        for filename in ("LICENSE", "assets/media/README.md"):
            text = (ROOT / filename).read_text()
            for marker in ("atkins-met-291575.jpg", "Anna Atkins",
                           "2005.100.557 (78)", "Joyce and Robert Menschel"):
                self.assertIn(marker, text)

    def test_full_text_provenance_and_backlinks(self):
        for identifier, source in (
                ("C20", "book/20-photography.md"),
                ("F67", "docs/evidence/F67-cyanotype-and-selection.md")):
            result = json.loads(subprocess.check_output(
                [sys.executable, "tools/read.py", "--id", identifier], cwd=ROOT))
            self.assertTrue(result["complete"])
            self.assertEqual(result["record"]["text"], (ROOT / source).read_text())
            self.assertEqual(result["record"]["source_sha256"],
                             hashlib.sha256((ROOT / source).read_bytes()).hexdigest())
        notes = json.loads((ROOT / "data/evidence.json").read_text())["notes"]
        note = next(n for n in notes if n["id"] == "F67")
        self.assertEqual(note["source_kind"], "museum_process_record_and_image")
        self.assertEqual(len(notes), 101)
        rendered = build.markdown(note["text"], note["source"])
        for anchor in ("photo-contact", "photo-selective-truth",
                       "photo-arranged-presence", "photo-process-objection"):
            self.assertIn('href="#' + anchor + '"', rendered)
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        self.assertEqual(len(records), 35)
        self.assertNotIn("F67", {r["id"] for r in records})
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all("F67" not in c["background_ids"] for c in cards))

    def test_route_does_not_turn_values_into_activities(self):
        routes = json.loads((ROOT / "data/reading-map.json").read_text())["routes"]
        route = next(r for r in routes if r["id"] == "R64")
        self.assertEqual(set(route["targets"]),
                         {"C20", "F67", "F34", "F10", "B10", "N10", "C25", "E08", "E11"})
        for phrase in ("不是新增行为研究", "蓝晒是工艺", "不升级为事实",
                       "不自动把价值讨论转成制作、购物或拍照任务"):
            self.assertIn(phrase, route["text"])


if __name__ == "__main__":
    unittest.main()
