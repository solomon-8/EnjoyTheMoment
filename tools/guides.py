"""Canonical long-form playbooks: metadata, full text and bounded retrieval."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {"id", "category", "minutes", "budget", "company", "energy", "card_ids", "summary"}


def load_guides(root=ROOT):
    records = []
    for path in sorted((root / "guides").glob("[0-9]*.md")):
        text = path.read_text(encoding="utf-8")
        matches = re.findall(r"^<!-- playbook: (.+) -->$", text, re.M)
        if len(matches) != 1:
            raise ValueError(f"{path}: expected one playbook record")
        record = json.loads(matches[0])
        if not isinstance(record, dict) or set(record) != FIELDS:
            raise ValueError(f"{path}: invalid playbook fields")
        if not isinstance(record["id"], str) or not re.fullmatch(r"P\d{3,}", record["id"]):
            raise ValueError(f"{path}: invalid playbook ID")
        for key, minimum in (("minutes", 1), ("budget", 0)):
            if type(record[key]) is not int or record[key] < minimum:
                raise ValueError(f"{path}: invalid {key}")
        for key in ("category", "summary"):
            if not isinstance(record[key], str) or not record[key].strip():
                raise ValueError(f"{path}: invalid {key}")
        if record["company"] not in ("solo", "social", "either") or record["energy"] not in ("low", "medium", "high"):
            raise ValueError(f"{path}: invalid participation labels")
        if not isinstance(record["card_ids"], list) or not all(
                isinstance(x, str) and re.fullmatch(r"J\d{3,}", x) for x in record["card_ids"]):
            raise ValueError(f"{path}: invalid card references")
        title = re.search(r"^# (.+)$", text, re.M).group(1)
        if not title.startswith(record["id"] + " · "):
            raise ValueError(f"{path}: ID/title mismatch")
        record.update(title=title, source=path.relative_to(root).as_posix(),
                      text=text, evidence_type="original_proposal",
                      source_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        records.append(record)
    if len({r["id"] for r in records}) != len(records):
        raise ValueError("Duplicate playbook ID")
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="")
    parser.add_argument("--id")
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.limit <= 10:
        parser.error("--limit must be 1..10")
    records = load_guides()
    if args.id and args.query:
        parser.error("--id and --query cannot be combined")
    if args.id:
        records = [r for r in records if r["id"] == args.id.upper()]
    else:
        words = args.query.lower().split()
        records = [r for r in records if all(w in r["text"].lower() for w in words)]
    print(json.dumps({"scope": "exact_id" if args.id else "literal_and",
                      "total_matches": len(records), "guides": records[:args.limit]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
