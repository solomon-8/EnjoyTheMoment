#!/usr/bin/env python3
"""Generate a no-dependency offline reader and AI exports from canonical Markdown."""

import argparse
import base64
import hashlib
import html
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import unquote

from pick import ROOT, load_cards
from guides import load_guides
from reading import load_routes


ESSAYS = [
    ("E01", "essays/01-pleasure-is-an-end.md"),
    ("E02", "essays/02-excitement-without-escalation.md"),
    ("E03", "essays/03-now-or-later.md"),
    ("E04", "essays/04-buying-pleasure.md"),
    ("E05", "essays/05-play-is-not-performance.md"),
    ("E06", "essays/06-real-life-constraints.md"),
    ("E07", "essays/07-rest-is-not-work.md"),
    ("E08", "essays/08-life-without-an-audience.md"),
    ("E09", "essays/09-friends-not-assets.md"),
    ("E10", "essays/10-pleasure-not-retention.md"),
    ("E11", "essays/11-pleasure-and-reality.md"),
]
EVIDENCE = [
    ("N02", "docs/evidence/B02-quantification.md"),
    ("N03", "docs/evidence/B03-richness.md"),
    ("N04", "docs/evidence/B04-anticipation.md"),
    ("N05", "docs/evidence/B05-leisure-value.md"),
    ("N06", "docs/evidence/B06-solitude.md"),
    ("N07", "docs/evidence/B07-making.md"),
    ("N08", "docs/evidence/B08-rituals.md"),
    ("N09", "docs/evidence/B09-games.md"),
    ("N10", "docs/evidence/B10-photography.md"),
    ("N11", "docs/evidence/B11-scheduling.md"),
    ("N12", "docs/evidence/B12-vacation.md"),
    ("N13", "docs/evidence/B13-humor.md"),
    ("N14", "docs/evidence/B14-dark-patterns.md"),
    ("N15", "docs/evidence/B15-recreational-fear.md"),
    ("N16", "docs/evidence/B16-false-insight.md"),
    ("N17", "docs/evidence/B17-enjoyable-procrastination.md"),
    ("N18", "docs/evidence/B18-experience-and-memory.md"),
    ("N19", "docs/evidence/B19-price-and-pleasantness.md"),
    ("N20", "docs/evidence/B20-sunk-cost.md"),
    ("N21", "docs/evidence/B21-shared-amplification.md"),
    ("N22", "docs/evidence/B22-shared-distance.md"),
    ("N23", "docs/evidence/B23-reliable-waiting.md"),
    ("N24", "docs/evidence/B24-hedonic-reversals.md"),
    ("F01", "docs/evidence/F01-time-use.md"),
    ("F02", "docs/evidence/F02-listening-language.md"),
    ("F03", "docs/evidence/F03-film-language.md"),
    ("F04", "docs/evidence/F04-safe-listening.md"),
    ("F05", "docs/evidence/F05-flavor.md"),
    ("F06", "docs/evidence/F06-public-space.md"),
    ("F07", "docs/evidence/F07-textiles.md"),
    ("F08", "docs/evidence/F08-textile-care.md"),
    ("F09", "docs/evidence/F09-game-difficulty.md"),
    ("F10", "docs/evidence/F10-photography-language.md"),
    ("F11", "docs/evidence/F11-reading-texts.md"),
    ("F12", "docs/evidence/F12-trip-planning.md"),
    ("F13", "docs/evidence/F13-artworks.md"),
    ("F14", "docs/evidence/F14-editions.md"),
    ("F15", "docs/evidence/F15-musical-scores.md"),
    ("F16", "docs/evidence/F16-train-robbery.md"),
    ("F17", "docs/evidence/F17-dance-language.md"),
    ("F18", "docs/evidence/F18-football-rules.md"),
    ("F19", "docs/evidence/F19-basketball-rules.md"),
    ("F20", "docs/evidence/F20-interface-report.md"),
    ("F21", "docs/evidence/F21-night-sky.md"),
    ("F22", "docs/evidence/F22-bird-identification.md"),
    ("F23", "docs/evidence/F23-bird-records-and-ethics.md"),
    ("F24", "docs/evidence/F24-monkeys-paw.md"),
    ("F25", "docs/evidence/F25-ice-cream-structure.md"),
    ("F26", "docs/evidence/F26-clothing-forms.md"),
    ("F27", "docs/evidence/F27-pleasure-philosophy.md"),
    ("F28", "docs/evidence/F28-weaving-and-material.md"),
    ("F29", "docs/evidence/F29-zine-structure.md"),
    ("F30", "docs/evidence/F30-voice-and-musical-relations.md"),
    ("F31", "docs/evidence/F31-microphones-and-voice-care.md"),
    ("F32", "docs/evidence/F32-action-and-consequences.md"),
    ("F33", "docs/evidence/F33-aspects-and-shared-fiction.md"),
    ("F34", "docs/evidence/F34-photographic-space-and-time.md"),
    ("F35", "docs/evidence/F35-public-life-observation.md"),
    ("F36", "docs/evidence/F36-midtown-public-space.md"),
    ("F37", "docs/evidence/F37-comic-scenes.md"),
    ("F38", "docs/evidence/F38-print-comparison.md"),
    ("F39", "docs/evidence/F39-digital-collections.md"),
    ("F40", "docs/evidence/F40-theatre-space.md"),
    ("F41", "docs/evidence/F41-jingju-conventions.md"),
    ("F42", "docs/evidence/F42-othello-choice.md"),
    ("F43", "docs/evidence/F43-hanabi-information.md"),
    ("F44", "docs/evidence/F44-festival-and-time.md"),
    ("F45", "docs/evidence/F45-magi-and-giving.md"),
    ("F46", "docs/evidence/F46-puzzle-structures.md"),
    ("F47", "docs/evidence/F47-walden-solitude.md"),
    ("F48", "docs/evidence/F48-room-and-freedom.md"),
    ("F49", "docs/evidence/F49-novelty-and-perception.md"),
    ("F50", "docs/evidence/F50-cognitive-labor.md"),
    ("F51", "docs/evidence/F51-rosas-repetition.md"),
    ("F52", "docs/evidence/F52-cunningham-chance.md"),
    ("F53", "docs/evidence/F53-open-window.md"),
    ("F54", "docs/evidence/F54-bedroom-letters.md"),
    ("F55", "docs/evidence/F55-bedroom-conservation.md"),
    ("F56", "docs/evidence/F56-moon-rotation-and-view.md"),
    ("F57", "docs/evidence/F57-friendship-and-reciprocity.md"),
]
EVIDENCE_KINDS = {
    "F01": "official_statistics",
    "F02": "educational_reference",
    "F03": "educational_reference",
    "F04": "official_health_guidance",
    "F05": "official_explainer",
    "F06": "practice_framework",
    "F07": "educational_reference",
    "F08": "technical_guidance",
    "F09": "technical_guidance",
    "F10": "educational_reference",
    "F11": "literary_primary_text",
    "F12": "official_visitor_guidance",
    "F13": "artwork_record_and_image",
    "F14": "educational_reference",
    "F15": "musical_score",
    "F16": "film_and_historical_catalog",
    "F17": "dance_education_and_work_record",
    "F18": "official_sport_rules",
    "F19": "official_sport_rules",
    "F20": "regulatory_staff_report",
    "F21": "official_science_explainer",
    "F22": "species_identification_reference",
    "F23": "birding_ethics_and_protocol",
    "F24": "literary_primary_text",
    "F25": "supplier_technical_handbook",
    "F26": "fashion_record_and_image",
    "F27": "philosophical_primary_and_secondary",
    "F28": "museum_teaching_and_artist_text",
    "F29": "museum_instructional_diagrams",
    "F30": "acoustics_and_music_education",
    "F31": "manufacturer_manual_and_health_guidance",
    "F32": "game_rules_and_original_probability",
    "F33": "official_game_srd",
    "F34": "educational_optics_and_original_models",
    "F35": "public_life_observation_protocol",
    "F36": "municipal_before_after_evaluation",
    "F37": "literary_primary_text",
    "F38": "artwork_record_and_image",
    "F39": "personal_digital_archiving_guidance",
    "F40": "theatre_educational_reference",
    "F41": "heritage_description_and_nomination",
    "F42": "official_game_rules_and_original_position",
    "F43": "publisher_game_rules",
    "F44": "official_heritage_description",
    "F45": "literary_primary_text",
    "F46": "mathematics_textbook_and_original_examples",
    "F47": "literary_primary_text",
    "F48": "literary_primary_text",
    "F49": "researcher_authored_explainer",
    "F50": "researcher_authored_project_summary",
    "F51": "creator_work_and_participation_record",
    "F52": "artist_trust_work_and_method_record",
    "F53": "literary_primary_text",
    "F54": "artist_letters_in_scholarly_edition",
    "F55": "museum_conservation_explainer",
    "F56": "official_science_explainer_and_visualization_metadata",
    "F57": "philosophical_primary_translation",
}
RELATIONS = [
    {"card_ids": ["J033"], "background_ids": ["B01"], "essay_ids": ["E04"]},
    {"card_ids": ["J024", "J040", "J058", "J059"], "background_ids": ["B02"], "essay_ids": ["E05"]},
    {"card_ids": ["J013", "J015", "J016", "J019", "J020"], "background_ids": ["B03"], "essay_ids": ["E02"]},
    {"card_ids": ["J006", "J025", "J031"], "background_ids": ["B04"], "essay_ids": ["E03"]},
    {"card_ids": ["J043", "J048"], "background_ids": ["B05"], "essay_ids": ["E07"]},
]


def json_text(data):
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def source_digest(root):
    files = sorted((root / "book").glob("*.md")) + sorted((root / "guides").glob("[0-9]*.md")) + [
        root / path for _, path in ESSAYS
    ] + [root / path for _, path in EVIDENCE] + [
        root / "docs/research.md", root / "SHUAQI.md", root / "docs/culture-shuaqi.md"
    ] + sorted((root / "assets/art").glob("*")) + sorted((root / "assets/media").glob("*"))
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def research_records(root):
    text = (root / "docs/research.md").read_text(encoding="utf-8")
    records = []
    matches = list(re.finditer(r"^## (B\d+) · (.+)$", text, re.MULTILINE))
    for index, match in enumerate(matches):
        next_heading = re.search(r"^## ", text[match.end():], re.MULTILINE)
        end = match.end() + next_heading.start() if next_heading else len(text)
        block = text[match.end():end]
        # Parentheses in DOI suffixes are URL-encoded in the Markdown subset.
        # Export the DOI identifier, not its transport encoding.
        doi_match = re.search(r"https://doi.org/([^)]+)", block)
        if not doi_match:
            raise ValueError("背景研究缺少 DOI 来源：" + match.group(1))
        doi = unquote(doi_match.group(1))
        fields = dict(re.findall(r"^- \*\*(.+?)\*\*：(.+)$", block, re.MULTILINE))
        verified_at = fields.get("核读日期", "").rstrip("。")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", verified_at):
            raise ValueError("背景研究缺少有效核读日期：" + match.group(1))
        date.fromisoformat(verified_at)
        records.append({
            "id": match.group(1), "title": match.group(2), "doi": doi,
            "access_level": "full_text" if "`full_text`" in block else "abstract_only",
            "verified_at": verified_at, "fields": fields,
            "directly_validates_cards": False,
            "source": "docs/research.md#" + match.group(1).lower(),
        })
    if not records or len({record["id"] for record in records}) != len(records):
        raise ValueError("背景研究记录为空或编号重复")
    return records


def local_href(href, source_path):
    if href.startswith(("https://", "http://", "mailto:", "#")):
        return href
    file_part, _, fragment = href.partition("#")
    if fragment and re.fullmatch(r"j\d+", fragment):
        return "#" + fragment
    clean = (Path(source_path).parent / file_part).as_posix()
    clean = str((ROOT / clean).resolve().relative_to(ROOT)).replace("\\", "/")
    if clean.startswith("book/"):
        if not fragment:
            return "#c" + Path(clean).stem[:2]
        # Explicit chapter anchors are rendered in the offline reader too.
        # Keep unknown/automatic GitHub heading fragments on the source page.
        target = ROOT / clean
        if target.is_file() and re.search(
                r'^<a id="' + re.escape(fragment) + r'"></a>$',
                target.read_text(encoding="utf-8"), re.MULTILINE):
            return "#" + fragment
    for essay_id, path in ESSAYS + EVIDENCE:
        if clean == path:
            if fragment and re.search(
                    r'^<a id="' + re.escape(fragment) + r'"></a>$',
                    (ROOT / clean).read_text(encoding="utf-8"), re.MULTILINE):
                return "#" + fragment
            return "#" + essay_id.lower()
    if clean == "docs/research.md":
        return "#" + (fragment or "research")
    if clean == "SHUAQI.md":
        if fragment and re.search(
                r'^<a id="' + re.escape(fragment) + r'"></a>$',
                (ROOT / clean).read_text(encoding="utf-8"), re.MULTILINE):
            return "#" + fragment
        return "#shuaqi"
    if clean == "docs/culture-shuaqi.md":
        return "#culture"
    if clean == "guides/README.md":
        return "#playbooks"
    for guide in load_guides():
        if clean == guide["source"]:
            return "#" + guide["id"].lower()
    return "https://github.com/solomon-8/EnjoyTheMoment/blob/main/" + clean + (
        "#" + fragment if fragment else "")


def inline(text, source_path):
    """Render a small, escaped Markdown subset; source never becomes raw HTML."""
    escaped = html.escape(text)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: '<a href="{0}">{1}</a>'.format(
        html.escape(local_href(html.unescape(m.group(2)), source_path), quote=True), m.group(1)), escaped)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)
    return escaped


def markdown(text, source_path, omit_title=False):
    """The essay/research sources use headings, paragraphs, lists, and tables."""
    out, paragraph, listing, table = [], [], None, False

    def flush():
        if paragraph:
            out.append("<p>" + inline(" ".join(paragraph), source_path) + "</p>")
            paragraph.clear()

    def close_blocks():
        nonlocal listing, table
        if listing:
            out.append("</" + listing + ">")
            listing = None
        if table:
            out.append("</tbody></table></div>")
            table = False

    for line in text.splitlines():
        if line.startswith("[←") or line.startswith("<!--"):
            continue
        if line in ("<details>", "</details>") or re.fullmatch(r"<summary>[^<>]+</summary>", line):
            flush()
            close_blocks()
            if line.startswith("<summary>"):
                out.append("<summary>" + html.escape(line[9:-10]) + "</summary>")
            else:
                out.append(line)
            continue
        if line.startswith('<a id="'):
            flush()
            close_blocks()
            identifier = re.search(r'id="([^"]+)"', line).group(1)
            out.append('<span id="{0}"></span>'.format(html.escape(identifier)))
            continue
        if not line.strip():
            flush()
            close_blocks()
            continue
        heading = re.match(r"^(#{1,4}) (.+)", line)
        image = re.fullmatch(r"!\[([^\]]+)\]\(([^)\s]+)\)", line)
        if image:
            flush()
            close_blocks()
            alt, href = image.groups()
            target = (ROOT / Path(source_path).parent / href).resolve()
            allowed_roots = ((ROOT / "assets/art").resolve(), (ROOT / "assets/media").resolve())
            if (not any(target.is_relative_to(folder) for folder in allowed_roots)
                    or target.suffix.lower() not in {".jpg", ".png", ".webp"}
                    or not target.is_file()):
                raise ValueError("正文图片仅支持 assets/art 或 assets/media 内已存在的本地图像：" + href)
            mime = {".jpg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}[target.suffix.lower()]
            out.append('<figure class="artwork"><img src="data:{0};base64,{1}" alt="{2}" loading="lazy" decoding="async"></figure>'.format(
                mime, base64.b64encode(target.read_bytes()).decode("ascii"),
                html.escape(alt, quote=True)))
        elif heading:
            flush()
            close_blocks()
            if omit_title and len(heading.group(1)) == 1:
                continue
            level = min(5, len(heading.group(1)) + 1)
            out.append("<h{0}>{1}</h{0}>".format(level, inline(heading.group(2), source_path)))
        elif line.startswith("|"):
            flush()
            if re.match(r"^\|[\s:|-]+\|$", line):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not table:
                out.append('<div class="table-scroll"><table><thead><tr>' +
                           "".join("<th>" + inline(c, source_path) + "</th>" for c in cells) +
                           "</tr></thead><tbody>")
                table = True
            else:
                out.append("<tr>" + "".join("<td>" + inline(c, source_path) + "</td>" for c in cells) + "</tr>")
        elif re.match(r"^(?:- |\d+\. )", line):
            flush()
            desired = "ul" if line.startswith("- ") else "ol"
            if listing and listing != desired:
                close_blocks()
            if not listing:
                start = "" if desired == "ul" else ' start="' + line.split(".", 1)[0] + '"'
                out.append("<" + desired + start + ">")
                listing = desired
            out.append("<li>" + inline(re.sub(r"^(?:- |\d+\. )", "", line), source_path) + "</li>")
        else:
            close_blocks()
            paragraph.append(line)
    flush()
    close_blocks()
    return "\n".join(out)


def outputs(root=ROOT):
    cards = load_cards(root)
    guides = load_guides(root)
    records = research_records(root)
    digest = source_digest(root)
    chapters = {}
    chapter_data = []
    chapter_ids = set()
    for path in sorted((root / "book").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if not re.fullmatch(r"\d{2}-.+", path.stem):
            raise ValueError("章节文件名须为两位编号加名称：" + path.name)
        identifier = "C" + path.stem[:2]
        if identifier in chapter_ids:
            raise ValueError("章节编号重复：" + identifier)
        chapter_ids.add(identifier)
        headings = re.findall(r"^# (.+)$", text, re.MULTILINE)
        if len(headings) != 1:
            raise ValueError("章节须恰有一个一级标题：" + path.name)
        introduction, separator, _ = text.partition('<a id="j')
        introduction = introduction.strip()
        if not introduction:
            raise ValueError("章节正文为空：" + path.name)
        chapter_data.append({
            "id": identifier,
            "title": headings[0],
            "source": path.relative_to(root).as_posix(),
            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "text": introduction,
            "card_ids": [card.id for card in cards if card.path == path.relative_to(root)],
            "scope": "chapter_introduction" if separator else "full_chapter",
        })
    card_data = []
    for card in cards:
        path = root / card.path
        title = re.search(r"^# (.+)$", path.read_text(), re.MULTILINE).group(1)
        chapter_id = card.path.stem[:2]
        chapters[chapter_id] = title
        record = card.to_dict(root)
        record.update(chapter_id=chapter_id, chapter_title=title,
                      background_ids=[], essay_ids=[], background_is_not_validation=True)
        for relation in RELATIONS:
            if card.id in relation["card_ids"]:
                record["background_ids"] += relation["background_ids"]
                record["essay_ids"] += relation["essay_ids"]
        card_data.append(record)
    export = {
        "schema_version": "1.0", "source_digest": digest, "canonical_source": "book/*.md",
        "count": len(cards), "notice": "原创试做；预算非报价；背景研究不直接验证行动卡。",
        "cards": card_data,
    }
    longform = []
    for essay_id, path in ESSAYS:
        text = (root / path).read_text(encoding="utf-8")
        title = re.search(r"^# (.+)$", text, re.MULTILINE).group(1)
        longform.append({"id": essay_id, "title": title, "source": path, "text": text})
    evidence = []
    for identifier, path in EVIDENCE:
        text = (root / path).read_text(encoding="utf-8")
        evidence.append({"id": identifier, "source": path, "text": text,
                         "source_kind": EVIDENCE_KINDS.get(identifier, "study_reading_note"),
                         "title": re.search(r"^# (.+)$", text, re.MULTILINE).group(1)})

    cards_html = []
    for record in card_data:
        f = record["fields"]
        related = "".join('<a href="#{0}">{1}</a> '.format(x.lower(), x)
                          for x in record["essay_ids"] + record["background_ids"])
        cards_html.append(
            '<details class="card" id="{id}" data-id="{ID}" data-chapter="{chapter}" '
            'data-minutes="{minutes}" data-budget="{budget}" data-company="{company}" data-energy="{energy}">'
            '<summary><span class="eyebrow">{ID} · {chapter_name}</span><h3>{title}</h3>'
            '<span class="meta">预留 ≤{minutes} 分钟 · 新增 ≤¥{budget} · {company_label}</span>'
            '<span class="teaser">{teaser}</span></summary>'
            '<div class="card-body"><dl>{fields}</dl><p class="card-links">'
            '<a href="#{id}" class="permalink" aria-label="{ID} 本页直达链接"># 本页直达</a> '
            '<a href="{source}">Markdown 原文</a> {related}</p></div></details>'.format(
                id=record["id"].lower(), ID=record["id"], chapter=record["chapter_id"],
                chapter_name=html.escape(record["chapter_title"].split(" · ", 1)[-1]),
                minutes=record["minutes"], budget=record["budget"], company=record["company"],
                energy=record["energy"], title=html.escape(record["title"]),
                company_label={"solo": "独自", "social": "需要同伴", "either": "独自 / 一起"}[record["company"]],
                teaser=html.escape(f["现在做"]),
                fields="".join("<dt>{0}</dt><dd>{1}</dd>".format(html.escape(k), inline(v, record["source"]))
                               for k, v in f.items()),
                source=html.escape(record["source_url"], quote=True), related=related,
            ))
    essays_html = []
    for item in longform:
        essays_html.append('<details class="essay argument" id="{0}"><summary>{1}</summary><div class="prose">{2}</div></details>'.format(
            item["id"].lower(), html.escape(item["title"]), markdown(item["text"], item["source"], omit_title=True)))
    research_html = markdown((root / "docs/research.md").read_text(), "docs/research.md")
    template = (root / "web/reader.html").read_text()
    replacements = {
        "@@CHAPTERINTROS@@": "\n".join(
            '<details class="essay chapter-intro" id="{0}"><summary>{1}</summary>'
            '<div class="prose">{2}{3}</div></details>'.format(
                item["id"].lower(), html.escape(item["title"]),
                markdown(item["text"], item["source"], omit_title=True),
                ("<p>配套行动：" + " · ".join(
                    '<a href="#{0}">{1}</a>'.format(identifier.lower(), identifier)
                    for identifier in item["card_ids"]) + "</p>") if item["card_ids"] else "")
            for item in chapter_data),
        "@@GUIDES@@": "\n".join(
            '<details class="essay playbook" id="{0}"><summary>{1}<br><small>{2}</small></summary>'
            '<div class="prose">{3}</div></details>'.format(
                item["id"].lower(), html.escape(item["title"]), html.escape(item["summary"]),
                markdown(item["text"], item["source"], omit_title=True)) for item in guides),
        "@@CARDS@@": "\n".join(cards_html),
        "@@ESSAYS@@": "\n".join(essays_html),
        "@@RESEARCH@@": research_html,
        "@@EVIDENCE@@": "\n".join(
            '<details class="essay" id="{0}"><summary>{1}</summary><div class="prose">{2}</div></details>'.format(
                item["id"].lower(), html.escape(item["title"]), markdown(item["text"], item["source"], omit_title=True))
            for item in evidence),
        "@@RESEARCHCOUNT@@": str(len(records)),
        "@@ESSAYCOUNT@@": str(len(longform)),
        "@@FULLCOUNT@@": str(sum(r["access_level"] == "full_text" for r in records)),
        "@@ABSTRACTCOUNT@@": str(sum(r["access_level"] == "abstract_only" for r in records)),
        "@@SHUAQI@@": markdown((root / "SHUAQI.md").read_text(), "SHUAQI.md"),
        "@@CULTURE@@": markdown((root / "docs/culture-shuaqi.md").read_text(), "docs/culture-shuaqi.md"),
        "@@CHAPTERS@@": "".join('<option value="{0}">{1}</option>'.format(k, html.escape(v))
                               for k, v in chapters.items()),
        "@@COUNT@@": str(len(cards)),
        "@@DIGEST@@": digest,
        "@@CSS@@": (root / "web/reader.css").read_text(),
        "@@JS@@": (root / "web/reader.js").read_text(),
    }
    for key, value in replacements.items():
        template = template.replace(key, value)
    if re.search(r"@@[A-Z]+@@", template):
        raise ValueError("阅读页仍有未替换占位符")
    full_text = "\n\n".join(
        ["# Enjoy The Moment · AI full text\n\n"
         "Canonical source: book/, essays/, guides/ and docs/. Values and original proposals are not validated interventions.\n"
         "Budgets are illustrative CNY caps. Preserve alternatives, stopping conditions and evidence status.\n"
         "Source digest: " + digest]
        + [(root / "SHUAQI.md").read_text()]
        + [item["text"] for item in longform]
        + [item["text"] for item in chapter_data]
        + ["## " + card.reference + "\n\n### " + card.id + " · " + card.title + "\n\n" + card.body for card in cards]
        + [item["text"] for item in guides]
        + [item["text"] for item in evidence]
        + [(root / path).read_text() for path in ["docs/research.md", "docs/culture-shuaqi.md"]]
    ).rstrip() + "\n"
    reading_routes = load_routes(root, {r["id"] for r in chapter_data + longform + evidence + records}
                                 | {"SHUAQI", "CULTURE"})
    return {
        "data/reading-map.json": json_text({
            "schema_version": "1.0", "canonical_source": "docs/reading-map.md",
            "source_sha256": hashlib.sha256((root / "docs/reading-map.md").read_bytes()).hexdigest(),
            "notice": "Reading guidance only, not new evidence or an efficacy rating.",
            "routes": reading_routes,
        }),
        "data/chapters.json": json_text({"schema_version": "1.0", "source_digest": digest, "chapters": chapter_data}),
        "data/guides.json": json_text({"schema_version": "1.0", "source_digest": digest, "guides": guides}),
        "data/evidence.json": json_text({"schema_version": "1.0", "source_digest": digest, "notes": evidence}),
        "data/catalog.json": json_text(export),
        "data/essays.json": json_text({"schema_version": "1.0", "source_digest": digest, "essays": longform}),
        "data/research.json": json_text({"schema_version": "1.0", "records": records, "relations": RELATIONS}),
        "llms-full.txt": full_text,
        "index.html": template,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="只检查生成文件是否与源内容一致")
    args = parser.parse_args()
    stale = []
    for path, content in outputs().items():
        target = ROOT / path
        if args.check:
            if not target.exists() or target.read_text(encoding="utf-8") != content:
                stale.append(path)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            print("Generated", path)
    if stale:
        parser.exit(1, "生成文件过期，请运行 python3 tools/build.py：\n" + "\n".join(stale) + "\n")
    if args.check:
        print("OK: 所有派生文件与 Markdown 源一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
