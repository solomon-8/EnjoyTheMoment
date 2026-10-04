#!/usr/bin/env python3
"""Read complete canonical arguments and sources by ID; search returns locations, not answers."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

import build
from reading import load_routes

ROOT = Path(__file__).resolve().parents[1]
KINDS = ("chapter", "essay", "evidence", "research", "position", "culture", "route")


def file_record(root, identifier, kind, source):
    path = root / source
    text = path.read_text(encoding="utf-8")
    title = re.search(r"^# (.+)$", text, re.M)
    if not title:
        raise ValueError("Missing document title: " + source)
    return {
        "id": identifier, "kind": kind, "title": title[1], "source": source,
        "scope": "full_file", "text": text,
        "contains_folded_content": "<details" in text,
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def load_documents(root=ROOT):
    documents = [
        file_record(root, "SHUAQI", "position", "SHUAQI.md"),
        file_record(root, "CULTURE", "culture", "docs/culture-shuaqi.md"),
    ]
    for path in sorted((root / "book").glob("[0-9][0-9]-*.md")):
        documents.append(file_record(root, "C" + path.stem[:2], "chapter",
                                     path.relative_to(root).as_posix()))
    for identifier, source in build.ESSAYS:
        documents.append(file_record(root, identifier, "essay", source))
    for identifier, source in build.EVIDENCE:
        record = file_record(root, identifier, "evidence", source)
        record["source_kind"] = build.EVIDENCE_KINDS.get(identifier, "study_reading_note")
        documents.append(record)

    ledger = (root / "docs/research.md").read_text(encoding="utf-8")
    sections = list(re.finditer(r"^## (B\d+) · (.+)$", ledger, re.M))
    metadata = {r["id"]: r for r in build.research_records(root)}
    for match in sections:
        next_heading = re.search(r"^## ", ledger[match.end():], re.M)
        end = match.end() + next_heading.start() if next_heading else len(ledger)
        text = ledger[match.start():end]
        text = re.sub(r'\n<a id="[^"]+"></a>\s*$', "", text).strip()
        record = metadata[match[1]]
        documents.append({
            "id": record["id"], "kind": "research", "title": record["title"],
            "source": record["source"], "scope": "complete_ledger_entry", "text": text,
            "source_sha256": hashlib.sha256((root / "docs/research.md").read_bytes()).hexdigest(),
            "contains_folded_content": "<details" in text,
            "verified_at": record["verified_at"], "access_level": record["access_level"],
            "directly_validates_cards": False,
        })
    if len(documents) != len({r["id"] for r in documents}):
        raise ValueError("Duplicate canonical document ID")
    routes = load_routes(root, {r["id"] for r in documents})
    documents.extend(dict(route, kind="route", contains_folded_content=False) for route in routes)
    return documents, routes


def location(record):
    return {key: value for key, value in record.items() if key != "text"}


def retrieval_digest(documents):
    digest = hashlib.sha256()
    for record in sorted(documents, key=lambda item: item["id"]):
        digest.update(record["id"].encode("utf-8"))
        digest.update(b"\0")
        digest.update(record["source_sha256"].encode("ascii"))
    return digest.hexdigest()


def linked_records(record, documents, root):
    """Only local links observed in this exact text; not inferred evidence of efficacy."""
    by_file = {}
    by_fragment = {}
    for item in documents:
        parsed = urlsplit(item["source"])
        if parsed.fragment:
            by_fragment[(parsed.path, parsed.fragment)] = item
        else:
            by_file[parsed.path] = item
    parent = (root / urlsplit(record["source"]).path).parent
    links = re.findall(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", record["text"])
    # Route Markdown is authored relative to docs/, not to its fragment.
    found = {}
    for href in links:
        parsed = urlsplit(href)
        if parsed.scheme or parsed.netloc:
            continue
        file = (parent / unquote(parsed.path)).resolve() if parsed.path else (root / urlsplit(record["source"]).path).resolve()
        try:
            relative = file.relative_to(root.resolve()).as_posix()
        except ValueError:
            continue
        candidate = by_fragment.get((relative, unquote(parsed.fragment))) or by_file.get(relative)
        if candidate and candidate["id"] != record["id"]:
            found[candidate["id"]] = location(candidate)
    return list(found.values())


def positive_limit(value):
    integer = int(value)
    if not 1 <= integer <= 20:
        raise argparse.ArgumentTypeError("--limit must be 1..20")
    return integer


def nonnegative_offset(value):
    integer = int(value)
    if integer < 0:
        raise argparse.ArgumentTypeError("--offset must be nonnegative")
    return integer


def page_size(value):
    integer = int(value)
    if not 1 <= integer <= 8000:
        raise argparse.ArgumentTypeError("--page-chars must be 1..8000")
    return integer


def sha256_argument(value):
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise argparse.ArgumentTypeError("--expect-digest must be a lowercase SHA-256")
    return value


class PageError(ValueError):
    def __init__(self, code, detail):
        super().__init__(detail)
        self.code = code


def exact_page(record, documents, routes, root, size, cursor, digest):
    """Slice the existing canonical text, not a summary or a new semantic unit."""
    text = record["text"]
    text_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    start = 0
    if cursor is not None:
        # A cursor is an integrity/continuation hint, not a credential or signature.
        match = re.fullmatch(
            r"p1:([A-Z0-9]{1,16}):([1-9][0-9]{0,11}):([0-9a-f]{64}):([0-9a-f]{64})",
            cursor,
        )
        if not match:
            raise PageError("invalid_cursor", "Copy next_cursor exactly; do not invent an offset.")
        identifier, offset, previous_digest, previous_text = match.groups()
        if identifier != record["id"]:
            raise PageError("cursor_id_mismatch", "This cursor belongs to a different ID.")
        if previous_digest != digest or previous_text != text_digest:
            raise PageError("cursor_version_mismatch", "Sources or extracted text changed; restart, do not concatenate versions.")
        start = int(offset)
        if start >= len(text):
            raise PageError("cursor_out_of_range", "The cursor does not identify an unread text position.")
    end = min(start + size, len(text))
    next_cursor = (
        "p1:{}:{}:{}:{}".format(record["id"], end, digest, text_digest)
        if end < len(text) else None
    )
    return {
        "schema_version": "1.1",
        "scope": "exact_id_page",
        "record": dict(location(record), scope="text_page",
                       canonical_scope=record["scope"], text=text[start:end]),
        # The last page is not the whole record. Only a one-page read is complete.
        "complete": start == 0 and end == len(text),
        "text_sha256": text_digest,
        "pagination": {
            "unit": "unicode_code_point", "start": start, "end": end,
            "total": len(text), "next_cursor": next_cursor,
        },
        "reading_guidance_ids": [r["id"] for r in routes if record["id"] in r["targets"]],
        "linked_record_ids": [r["id"] for r in linked_records(record, documents, root)],
        "page_notice": "A page can split a sentence, table or folded answer. Join record.text in order, without separators, through next_cursor=null; verify text_sha256. Guidance and linked IDs are unread: retrieve relevant IDs with --expect-digest.",
    }


def main(argv=None, root=ROOT):
    parser = argparse.ArgumentParser(description=__doc__)
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--id", help="C/E/B/N/F/R ID, SHUAQI or CULTURE; returns complete text")
    selector.add_argument("--query", help="literal AND search; titles/locations only, including folded text matches")
    selector.add_argument("--list", action="store_true", help="list titles and source paths")
    parser.add_argument("--kind", choices=KINDS)
    parser.add_argument("--limit", type=positive_limit, default=5)
    parser.add_argument("--offset", type=nonnegative_offset, default=0,
                        help="continue a search/list with the same query, kind and source version")
    parser.add_argument("--page-chars", type=page_size,
                        help="optional exact-ID text page, 1..8000 Unicode code points (not tokens)")
    parser.add_argument("--cursor", help="copy next_cursor from an exact-ID page; requires --page-chars")
    parser.add_argument("--expect-digest", type=sha256_argument,
                        help="reject if retrieval_digest changed, including when following another ID")
    args = parser.parse_args(argv)
    if args.id and args.kind:
        parser.error("--id and --kind cannot be combined; exact lookup does not apply filters")
    if args.id and args.offset:
        parser.error("--id and --offset cannot be combined")
    if args.query is not None and not args.query.strip():
        parser.error("--query cannot be empty")
    if (args.page_chars is not None or args.cursor is not None) and not args.id:
        parser.error("--page-chars and --cursor require --id")
    if args.cursor is not None and args.page_chars is None:
        parser.error("--cursor requires --page-chars")
    try:
        documents, routes = load_documents(root)
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"error": "source_read_failed", "detail": str(exc)}, ensure_ascii=False))
        return 2
    envelope = {
        "schema_version": "1.0", "retrieval_digest": retrieval_digest(documents),
        "notice": "Read-only canonical retrieval, not semantic intent classification or efficacy evidence. Full text may contain spoilers; read privately before choosing what to reveal. Linked locations have not been read by this command.",
    }
    if args.expect_digest is not None and args.expect_digest != envelope["retrieval_digest"]:
        envelope.update(error="retrieval_version_mismatch",
                        expected_retrieval_digest=args.expect_digest,
                        detail="Sources changed; restart the reading or use a checkout of the original commit.")
        print(json.dumps(envelope, ensure_ascii=False, indent=2))
        return 2
    if args.id:
        identifier = args.id.upper()
        selected = next((r for r in documents if r["id"] == identifier), None)
        if selected is None:
            envelope.update(scope="exact_id", error="unknown_id", requested_id=identifier)
            print(json.dumps(envelope, ensure_ascii=False, indent=2))
            return 1
        if args.page_chars is not None:
            try:
                envelope.update(exact_page(selected, documents, routes, root,
                                           args.page_chars, args.cursor, envelope["retrieval_digest"]))
            except PageError as exc:
                envelope.update(scope="exact_id_page", error=exc.code, detail=str(exc))
                print(json.dumps(envelope, ensure_ascii=False, indent=2))
                return 2
        else:
            envelope.update(scope="exact_id", record=selected, complete=True,
                            reading_guidance=[r for r in routes if identifier in r["targets"]],
                            linked_records=linked_records(selected, documents, root))
    else:
        words = args.query.casefold().split() if args.query is not None else []
        candidates = [r for r in documents if args.kind is None or r["kind"] == args.kind]
        matches = [r for r in candidates if all(word in (r["title"] + "\n" + r["text"]).casefold() for word in words)]
        matches.sort(key=lambda r: (-sum(w in r["title"].casefold() for w in words), r["id"]))
        page = matches[args.offset:args.offset + args.limit]
        next_offset = args.offset + len(page) if args.offset + len(page) < len(matches) else None
        envelope.update(
            scope="literal_and" if words else "list", total_matches=len(matches),
            offset=args.offset, returned=len(page), has_more=next_offset is not None,
            next_offset=next_offset, results=[location(r) for r in page],
            complete_text_returned=False,
        )
    print(json.dumps(envelope, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
