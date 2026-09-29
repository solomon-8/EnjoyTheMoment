#!/usr/bin/env python3
"""Check catalog structure, local Markdown links, IDs, counts, and SVG syntax."""

import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlsplit

from pick import ROOT, load_cards


def prose_only(text):
    """Ignore example code fences when extracting real headings or links."""
    return re.sub(r"^(```|~~~).*?^\1[ \t]*$", "", text, flags=re.MULTILINE | re.DOTALL)


def anchors_for(text):
    clean = prose_only(text)
    anchors = set(re.findall(r'\bid=["\']([^"\']+)["\']', clean))
    occurrences = {}
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", clean, re.MULTILINE):
        heading = re.sub(r"<[^>]+>", "", heading).lower().strip()
        heading = re.sub(r"\*\*|__|`", "", heading)
        slug = "".join(
            char for char in heading
            if char in ("-", "_", " ") or unicodedata.category(char)[0] in ("L", "N", "M")
        ).replace(" ", "-")
        occurrence = occurrences.get(slug, 0)
        occurrences[slug] = occurrence + 1
        anchors.add(slug if occurrence == 0 else "{0}-{1}".format(slug, occurrence))
    return anchors


def check(root=ROOT):
    problems = []
    try:
        cards = load_cards(root)
    except (OSError, ValueError) as exc:
        return [str(exc)], 0
    ids = sorted(int(card.id[1:]) for card in cards)
    if ids != list(range(1, len(cards) + 1)):
        problems.append("当前目录的卡片编号不连续；删除卡片时需保留可追溯占位或调整此检查")
    readme = (root / "README.md").read_text(encoding="utf-8")
    declared = re.findall(r"<!-- catalog-count: (\d+) -->", readme)
    if declared != [str(len(cards))]:
        problems.append("README catalog-count 与实际卡片数不一致")
    chapters = len(list((root / "book").glob("*.md")))
    if "**{0} 个章节，{1} 张原创行动卡。**".format(chapters, len(cards)) not in readme:
        problems.append("README 可见章节/卡片数量与内容不一致")
    english = (root / "README.en.md").read_text(encoding="utf-8")
    if "**{0} chapters. {1} original activity cards.**".format(chapters, len(cards)) not in english:
        problems.append("英文首页可见数量与内容不一致")

    for path in sorted(root.rglob("*.md")):
        if any(part in {".git", ".venv", "private"} for part in path.relative_to(root).parts):
            continue
        text = prose_only(path.read_text(encoding="utf-8"))
        links = re.findall(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", text)
        links += re.findall(r'<(?:img|a)\b[^>]*\b(?:src|href)=["\']([^"\']+)', text)
        for link in links:
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                continue
            target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            if not target.is_relative_to(root.resolve()):
                problems.append("{0}: 链接越出仓库 {1}".format(path.relative_to(root), link))
            elif not target.exists():
                problems.append("{0}: 不存在的本地链接 {1}".format(path.relative_to(root), link))
            elif parsed.fragment and target.suffix == ".md":
                fragment = unquote(parsed.fragment)
                if fragment not in anchors_for(target.read_text(encoding="utf-8")):
                    problems.append("{0}: 找不到锚点 {1}".format(path.relative_to(root), link))
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith(("<<<<<<< ", "=======", ">>>>>>> ")):
                problems.append("{0}:{1}: 疑似冲突标记".format(path.relative_to(root), line_number))

    for path in (root / "assets").glob("*.svg"):
        try:
            tree = ET.parse(path)
            namespace = "{http://www.w3.org/2000/svg}"
            if tree.getroot().find(namespace + "title") is None:
                problems.append("{0}: 缺少 SVG title".format(path.name))
        except ET.ParseError as exc:
            problems.append("{0}: SVG 语法错误 {1}".format(path.name, exc))
    return problems, len(cards)


def main():
    try:
        problems, count = check()
    except (OSError, ValueError) as exc:
        print("检查未完成：{0}".format(exc), file=sys.stderr)
        return 1
    if problems:
        for problem in problems:
            print("FAIL: {0}".format(problem), file=sys.stderr)
        return 1
    print("OK: {0} 张卡片；结构、数量、编号、本地文件/锚点链接与 SVG 语法通过。".format(count))
    print("未验证外链可达性、实时价格、医学效果或用户体验。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
