#!/usr/bin/env python3
"""Build a deterministic EPUB from the full reading corpus (standard library only).

Run directly to update the edition, or --check to verify it without writing.
The modification timestamp is retained while all source bytes stay the same.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import html
import io
import json
from pathlib import Path
import posixpath
import re
import unicodedata
from urllib.parse import quote, unquote, urlsplit
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED, ZIP_STORED

import build
from check import anchors_for

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = "downloads/EnjoyTheMoment.epub"
STATE = "data/epub-edition.json"
REPOSITORY = "https://github.com/solomon-8/EnjoyTheMoment"
XHTML = "http://www.w3.org/1999/xhtml"
EPUB = "http://www.idpf.org/2007/ops"
OPF = "http://www.idpf.org/2007/opf"
DC = "http://purl.org/dc/elements/1.1/"


def reading_groups(root=ROOT):
    """Explicit reader scope, including all essays, chapters, cards and notes."""
    relative = lambda p: p.relative_to(root).as_posix()
    return [
        ("从这里读", ["docs/reading-editions.md", "SHUAQI.md"]),
        ("核心争论", [source for _, source in build.ESSAYS]),
        ("生活与乐趣", [relative(p) for p in sorted((root / "book").glob("[0-9][0-9]-*.md"))]),
        ("完整玩法", ["guides/README.md"] +
         [relative(p) for p in sorted((root / "guides").glob("[0-9][0-9]-*.md"))]),
        ("按问题查找", ["docs/reading-map.md"]),
        ("研究与核读", ["docs/research.md"] + [source for _, source in build.EVIDENCE]),
        ("背景、反对意见与署名", [
            "docs/faq.md", "docs/editorial-policy.md", "docs/culture-shuaqi.md", "docs/manifesto.md",
            "docs/seven-days.md", "docs/sources.md", "assets/art/README.md",
            "assets/media/README.md", "templates/my-menu.md",
            "templates/experience-note.md", "LICENSE",
        ]),
    ]


def source_files(root=ROOT):
    files = [p for _, paths in reading_groups(root) for p in paths]
    if len(files) != len(set(files)):
        raise ValueError("Duplicate reading source")
    # A new essay/note must not silently remain outside the book registry.
    for folder, registered in (("essays", build.ESSAYS), ("docs/evidence", build.EVIDENCE)):
        actual = {p.relative_to(root).as_posix() for p in (root / folder).glob("*.md")}
        if actual != {p for _, p in registered}:
            raise ValueError("Unregistered reading source in " + folder)
    return files


def document_name(source):
    return "text/" + source.replace("/", "--").removesuffix(".md") + ".xhtml"


def local_target(href, source):
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc:
        return None, None
    clean = posixpath.normpath(posixpath.join(posixpath.dirname(source), unquote(parsed.path)))
    if not parsed.path:
        clean = source
    if clean == ".." or clean.startswith("../") or clean.startswith("/"):
        raise ValueError("Path outside repository: " + href)
    return clean, unquote(parsed.fragment)


def heading_slug(label):
    label = re.sub(r"<[^>]+>", "", label).lower().strip()
    label = re.sub(r"\*\*|__|`", "", label)
    return "".join(c for c in label
                   if c in ("-", "_", " ") or unicodedata.category(c)[0] in ("L", "N", "M")).replace(" ", "-")


def render_document(text, source, names, assets, root=ROOT):
    """Render the repository's Markdown subset as well-formed EPUB XHTML.

    Unlike the interactive reader, this preserves fenced diagrams, quotations,
    heading fragments and expanded details. Unknown raw HTML fails the build.
    """
    def link(href, _source):
        target, fragment = local_target(href, source)
        if target is None:
            if urlsplit(href).scheme not in ("http", "https", "mailto"):
                raise ValueError("Unsupported link scheme: " + href)
            return href
        if target in names:
            target_text = (root / target).read_text()
            if fragment and fragment not in anchors_for(target_text):
                raise ValueError("Missing source fragment: " + source + " -> " + href)
            relative = posixpath.relpath(names[target], posixpath.dirname(names[source]))
            return relative + ("#" + quote(fragment, safe="-._~") if fragment else "")
        # Code, homepage and download endpoints are deliberately online links.
        if not (root / target).exists() and target != OUTPUT:
            raise ValueError("Missing linked file: " + source + " -> " + href)
        return REPOSITORY + "/blob/main/" + quote(target, safe="/") + (
            "#" + quote(fragment, safe="-._~") if fragment else "")

    inline = lambda s: build.inline(s, source, href_resolver=link)
    out, paragraph, code_lines, headings = [], [], [], []
    listing, table, fence, details = None, False, None, 0
    seen_headings, ids = {}, set()
    explicit = set(re.findall(r'^<a id="([^"]+)"></a>$', text, re.M))

    def flush():
        if paragraph:
            out.append("<p>" + inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()

    def close():
        nonlocal listing, table
        flush()
        if listing:
            out.append("</" + listing + ">")
            listing = None
        if table:
            out.append("</tbody></table></div>")
            table = False

    clean = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    for line in clean.splitlines():
        if fence:
            if line.strip().startswith(fence):
                out.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
                code_lines.clear()
                fence = None
            else:
                code_lines.append(line)
            continue
        if re.match(r"^(```|~~~)", line):
            close()
            fence = line[:3]
            continue
        if not line.strip():
            close()
            continue
        if line == "<details>":
            close()
            out.append('<section class="expanded">')
            details += 1
            continue
        if line == "</details>":
            close()
            if not details:
                raise ValueError("Unbalanced details: " + source)
            out.append("</section>")
            details -= 1
            continue
        summary = re.fullmatch(r"<summary>([^<>]+)</summary>", line)
        if summary:
            close()
            out.append('<p class="expanded-title">' + inline(summary[1]) + "</p>")
            continue
        anchor = re.fullmatch(r'<a id="([^"]+)"></a>', line)
        if anchor:
            close()
            if anchor[1] in ids:
                raise ValueError("Duplicate anchor: " + source + "#" + anchor[1])
            ids.add(anchor[1])
            out.append('<span id="' + html.escape(anchor[1], quote=True) + '"></span>')
            continue
        if line.startswith("<"):
            raise ValueError("Unsupported raw HTML: " + source + ": " + line)
        heading = re.match(r"^(#{1,6}) (.+?)(?:\s+#+)?$", line)
        image = re.fullmatch(r"!\[([^\]]*)\]\(([^)\s]+)\)", line)
        item = re.match(r"^(- |\d+\. )(.+)", line)
        if heading:
            close()
            level, label = len(heading[1]), heading[2]
            slug = heading_slug(label)
            occurrence = seen_headings.get(slug, 0)
            seen_headings[slug] = occurrence + 1
            slug += "-" + str(occurrence) if occurrence else ""
            attr = ""
            if slug not in explicit:
                if slug in ids:
                    raise ValueError("Duplicate heading anchor: " + source + "#" + slug)
                ids.add(slug)
                attr = ' id="' + html.escape(slug, quote=True) + '"'
            out.append("<h{0}{1}>{2}</h{0}>".format(level, attr, inline(label)))
            headings.append((level, re.sub(r"[*`]", "", label), slug))
        elif image:
            close()
            alt, href = image.groups()
            target, fragment = local_target(href, source)
            if (not alt or target is None or fragment or not target.startswith(("assets/art/", "assets/media/"))
                    or Path(target).suffix not in (".png", ".jpg")):
                raise ValueError("Unsupported image: " + source + " -> " + href)
            data = (root / target).read_bytes()
            name = "images/" + Path(target).name
            if name in assets and assets[name] != data:
                raise ValueError("Image filename collision: " + name)
            assets[name] = data
            out.append('<figure><img src="../' + name + '" alt="' +
                       html.escape(alt, quote=True) + '" /></figure>')
        elif line.startswith("|"):
            if re.fullmatch(r"\|[\s:|-]+\|", line):
                continue
            if listing or paragraph:
                close()
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not table:
                out.append('<div class="table-scroll"><table><thead><tr>' +
                           "".join('<th scope="col">' + inline(c) + "</th>" for c in cells) +
                           "</tr></thead><tbody>")
                table = True
            else:
                out.append("<tr>" + "".join("<td>" + inline(c) + "</td>" for c in cells) + "</tr>")
        elif item:
            flush()
            desired = "ul" if item[1] == "- " else "ol"
            if table or (listing and listing != desired):
                close()
            if not listing:
                start = "" if desired == "ul" else ' start="' + item[1].split(".")[0] + '"'
                out.append("<" + desired + start + ">")
                listing = desired
            out.append("<li>" + inline(item[2]) + "</li>")
        elif line.startswith("> "):
            close()
            out.append("<blockquote><p>" + inline(line[2:]) + "</p></blockquote>")
        elif line == "---":
            close()
            out.append("<hr />")
        else:
            if listing or table:
                close()
            paragraph.append(line)
    close()
    if fence or details:
        raise ValueError("Unclosed block: " + source)
    return "\n".join(out), headings


def xhtml(title, body, style="style.css"):
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE html>\n'
            '<html xmlns="' + XHTML + '" xmlns:epub="' + EPUB +
            '" lang="zh-CN" xml:lang="zh-CN"><head><meta charset="utf-8" />'
            "<title>" + html.escape(title) + '</title><link rel="stylesheet" type="text/css" href="' +
            style + '" /></head><body>' + body + "</body></html>").encode()


def edition_inputs(root=ROOT):
    files = source_files(root) + ["tools/epub.py", "tools/build.py", "tools/check.py", "web/epub.css"]
    # Hash both embedded and attribution-linked media, not only prose.
    files += [p.relative_to(root).as_posix() for folder in ("assets/art", "assets/media")
              for p in (root / folder).iterdir() if p.is_file()]
    return {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in sorted(set(files))}


def edition_metadata(root=ROOT, previous=None):
    sources = edition_inputs(root)
    digest = hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()
    modified = (previous or {}).get("modified") if (previous or {}).get("source_digest") == digest else None
    if not modified:
        modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", modified):
        raise ValueError("Invalid EPUB modification timestamp")
    return {"schema_version": "1.0", "title": "享受当下 · Enjoy the Moment",
            "language": "zh-CN", "modified": modified, "source_digest": digest,
            "scope": "full_reading_corpus", "sources": sources,
            "reading_files": source_files(root)}


def build_epub(root=ROOT, metadata=None):
    metadata = metadata or edition_metadata(root)
    sources = source_files(root)
    names = {s: document_name(s) for s in sources}
    if len(set(names.values())) != len(names):
        raise ValueError("Document filename collision")
    assets, contents, titles, subsections = {}, {}, {}, {}
    for source in sources:
        text = (root / source).read_text()
        if source == "LICENSE":
            text = "# 许可与第三方权利\n\n" + text
        rendered, headings = render_document(text, source, names, assets, root)
        if not headings:
            raise ValueError("Missing document heading: " + source)
        title = headings[0][1]
        titles[source] = title
        subsections[source] = [(label, slug) for level, label, slug in headings
                               if level == 2 or (level == 3 and re.match(r"J\d{3} ·", label))]
        footer = ('<p class="back-to-toc"><a href="../nav.xhtml">返回全书目录</a></p>'
                  '<p class="source-link"><a href="' + REPOSITORY + '/blob/main/' +
                  quote(source, safe="/") + '">查看本篇的仓库原文（需联网）</a></p>')
        contents[names[source]] = xhtml(title, rendered + footer, "../style.css")
    nav = ['<h1>全书目录</h1><nav epub:type="toc" id="toc"><h2>内容</h2><ol>']
    for group, paths in reading_groups(root):
        nav.append("<li><span>" + html.escape(group) + "</span><ol>")
        for source in paths:
            nav.append('<li><a href="' + names[source] + '">' + html.escape(titles[source]) + "</a>")
            if subsections[source]:
                nav.append("<ol>")
                for title, slug in subsections[source]:
                    nav.append('<li><a href="' + names[source] + "#" + quote(slug, safe="-._~") +
                               '">' + html.escape(title) + "</a></li>")
                nav.append("</ol>")
            nav.append("</li>")
        nav.append("</ol></li>")
    nav.append("</ol></nav>")
    nav.append('<nav epub:type="landmarks" hidden="hidden"><h2>阅读入口</h2><ol>'
               '<li><a epub:type="cover" href="title.xhtml">书名页</a></li>'
               '<li><a epub:type="bodymatter" href="' + names["SHUAQI.md"] + '">耍起</a></li>'
               '</ol></nav>')
    contents["nav.xhtml"] = xhtml("目录 · 享受当下", "".join(nav))
    contents["title.xhtml"] = xhtml(metadata["title"],
        '<section epub:type="titlepage"><h1>享受当下</h1><p>Enjoy the Moment</p>'
        '<p><strong>耍起。把快乐当正事。</strong></p>'
        '<p>solomon-8 / EnjoyTheMoment 贡献者</p>'
        '<p><a href="nav.xhtml">打开全书目录</a></p>'
        '<p>中文全文版。价值主张、原创假想和研究结果分开呈现；行动卡不是效果处方。</p>'
        '<p>第三方图像与其他材料保留各自权利，详见书末来源、素材署名与许可。</p></section>')
    contents["style.css"] = (root / "web/epub.css").read_bytes()
    contents.update(assets)
    manifest, spine = [], []
    ordered = ["title.xhtml", "nav.xhtml"] + [names[s] for s in sources]
    for index, name in enumerate(ordered + sorted(set(contents) - set(ordered))):
        identifier = "item-" + str(index)
        media = {"xhtml": "application/xhtml+xml", "css": "text/css", "jpg": "image/jpeg",
                 "png": "image/png"}[name.rsplit(".", 1)[1]]
        props = ' properties="nav"' if name == "nav.xhtml" else ""
        manifest.append('<item id="' + identifier + '" href="' + name +
                        '" media-type="' + media + '"' + props + " />")
        if name in ordered:
            spine.append('<itemref idref="' + identifier + '" />')
    package = ('<?xml version="1.0" encoding="UTF-8"?>'
        '<package xmlns="' + OPF + '" unique-identifier="book-id" version="3.0" xml:lang="zh-CN">'
        '<metadata xmlns:dc="' + DC + '"><dc:identifier id="book-id">urn:enjoythemoment:zh-cn</dc:identifier>'
        '<dc:title>' + html.escape(metadata["title"]) + '</dc:title><dc:language>zh-CN</dc:language>'
        '<dc:creator>solomon-8 / EnjoyTheMoment 贡献者</dc:creator>'
        '<dc:source>' + REPOSITORY + '</dc:source>'
        '<dc:rights>原创材料采用MIT许可；第三方材料保留各自权利。详见书末许可与素材署名。</dc:rights>'
        '<meta property="dcterms:modified">' + metadata["modified"] + '</meta>'
        '<meta property="rendition:layout">reflowable</meta>'
        '</metadata><manifest>' + "".join(manifest) + '</manifest><spine>' +
        "".join(spine) + '</spine></package>').encode()
    container = (b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        b'<rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml" />'
        b'</rootfiles></container>')
    entries = {"META-INF/container.xml": container, "EPUB/package.opf": package}
    entries.update({"EPUB/" + k: v for k, v in contents.items()})
    validate_internal(entries)
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as archive:
        for name, data in [("mimetype", b"application/epub+zip")] + sorted(entries.items()):
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_STORED if name == "mimetype" else ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    return buffer.getvalue()


def validate_internal(entries):
    """No broken local targets, duplicate IDs, scripting or remote resources."""
    ids, trees = {}, {}
    for name, data in entries.items():
        if not name.endswith((".xhtml", ".opf", ".xml")):
            continue
        tree = ET.fromstring(data)
        trees[name] = tree
        found = [e.attrib["id"] for e in tree.iter() if "id" in e.attrib]
        if len(found) != len(set(found)):
            raise ValueError("Duplicate ID in " + name)
        ids[name] = set(found)
    for name, tree in trees.items():
        for element in tree.iter():
            tag = element.tag.rsplit("}", 1)[-1]
            if tag in ("script", "iframe", "form", "details"):
                raise ValueError("Interactive content in " + name)
            for attribute in ("src", "href"):
                if attribute not in element.attrib:
                    continue
                value = element.attrib[attribute]
                parsed = urlsplit(value)
                if parsed.scheme or parsed.netloc:
                    if attribute != "href" or tag != "a":
                        raise ValueError("Remote resource: " + name + " -> " + value)
                    continue
                target = (posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(parsed.path)))
                          if parsed.path else name)
                if target not in entries:
                    raise ValueError("Missing package target: " + name + " -> " + value)
                if parsed.fragment and unquote(parsed.fragment) not in ids.get(target, set()):
                    raise ValueError("Missing package fragment: " + name + " -> " + value)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    state_path = ROOT / STATE
    previous = json.loads(state_path.read_text()) if state_path.exists() else None
    metadata = edition_metadata(ROOT, previous)
    result = build_epub(ROOT, metadata)
    state = json.dumps(metadata, ensure_ascii=False, indent=2) + "\n"
    target = ROOT / OUTPUT
    if args.check:
        if (not target.exists() or target.read_bytes() != result or not state_path.exists()
                or state_path.read_text() != state):
            parser.exit(1, "EPUB已过期，请运行 python3 tools/epub.py\n")
        print("OK: EPUB内容、内部链接、源哈希与可复现打包一致")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(result)
        state_path.write_text(state)
        print("Generated", OUTPUT, len(result), "bytes;", len(metadata["reading_files"]), "source files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
