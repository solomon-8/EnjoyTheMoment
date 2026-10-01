"""Publication guards, not a replication or an audience-response test."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build


class FilmContextTests(unittest.TestCase):
    def test_study_designs_and_outcomes_do_not_collapse(self):
        text = (ROOT / "book/12-film.md").read_text()
        for marker in ("同一段脸在一个序列内重复",
                       "不等于同一张脸在三种情境里都被测试",
                       "p = .879", "p = .293", "3.98、3.93、3.87",
                       "没有在同一实验里随机比较", "我已经哭了，我仍可以觉得它拍得不好",
                       "不对应任何真实人物或事件"):
            self.assertIn(marker, text)
        self.assertEqual(12 + 59 + 31, 102)
        self.assertEqual(18 * 9 * 3, 486)
        self.assertEqual(text.count("<details>"), 1)
        self.assertEqual(text.count("![") , 3)
        # Original chapter anchors and the protected spoiler wrapper remain.
        for marker in ("## 六个够用的概念，不必一次全记",
                       "## 黑边不一定是故障，铺满也不一定是完整",
                       "<summary>展开后段与结尾分析"):
            self.assertIn(marker, text)

    def test_evidence_preserves_conflicts_and_access_limits(self):
        first = (ROOT / "docs/evidence/B32-film-context.md").read_text()
        second = (ROOT / "docs/evidence/B33-context-and-categorization.md").read_text()
        for marker in ("正文报告 **.406**", "图3D图注报告 **.005**",
                       "−0.02 ± .14", "0.02 ± .13", "未读取这些文件的内容",
                       "评分不是客观外周生理记录", "Michael B. Steinborn是编辑"):
            self.assertIn(marker, first)
        for marker in ("0.2个百分点", "29.03%", "angry", "fearful", "403",
                       "未取得分析代码", "不自行判定正确单位", "未报告面孔或情境项目随机效应"):
            self.assertIn(marker, second)
        records = json.loads((ROOT / "data/research.json").read_text())["records"]
        by_id = {r["id"]: r for r in records}
        self.assertEqual(len(records), 36)
        for identifier in ("B32", "B33"):
            self.assertEqual(by_id[identifier]["verified_at"], "2026-10-01")
            self.assertEqual(by_id[identifier]["access_level"], "full_text")
            self.assertFalse(by_id[identifier]["directly_validates_cards"])
        self.assertEqual(by_id["B32"]["doi"], "10.1371/journal.pone.0308295")
        self.assertEqual(by_id["B33"]["doi"], "10.1177/20416695251410119")
        cards = json.loads((ROOT / "data/catalog.json").read_text())["cards"]
        self.assertEqual(len(cards), 60)
        self.assertTrue(all(not {"B32", "B33"} & set(c["background_ids"]) for c in cards))

    def test_complete_sources_are_retrievable_without_detached_limits(self):
        sources = {
            "N32": "docs/evidence/B32-film-context.md",
            "N33": "docs/evidence/B33-context-and-categorization.md",
            "C12": "book/12-film.md",
        }
        for identifier, path in sources.items():
            data = json.loads(subprocess.check_output(
                [sys.executable, "tools/read.py", "--id", identifier], cwd=ROOT))
            self.assertTrue(data["complete"])
            self.assertEqual(data["record"]["text"], (ROOT / path).read_text())
            self.assertEqual(data["record"]["source_sha256"],
                             hashlib.sha256((ROOT / path).read_bytes()).hexdigest())
        self.assertEqual(build.local_href("../docs/evidence/B32-film-context.md",
                                         "book/12-film.md"), "#n32")
        self.assertEqual(build.local_href("../../book/12-film.md#film-context-boundary",
                                         sources["N33"]), "#film-context-boundary")
        # The renderer omits breadcrumb lines. The body must retain real backlinks.
        for identifier, anchor in (("N32", "film-context-study"),
                                   ("N33", "film-context-boundary")):
            rendered = build.markdown((ROOT / sources[identifier]).read_text(),
                                      sources[identifier])
            self.assertIn('href="#' + anchor + '"', rendered)

    def test_route_has_visible_links_to_every_declared_target(self):
        routes = json.loads((ROOT / "data/reading-map.json").read_text())["routes"]
        route = next(r for r in routes if r["id"] == "R62")
        self.assertEqual(set(route["targets"]),
                         {"C12", "B32", "N32", "B33", "N33", "F03", "F16", "C31", "E11"})
        text = (ROOT / "docs/reading-map.md").read_text().split('id="r62"')[1]
        for marker in ("p = .879", "p = .293", "不是每张脸跨所有情境",
                       "不能宣称其缺失已被证明为原因", "均不测喜欢"):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
