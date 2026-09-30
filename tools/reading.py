"""Validate the canonical, on-demand reading map without fetching external sources."""
import hashlib
import json
import re


def load_routes(root, known_ids=None):
    path = root / "docs/reading-map.md"
    source = path.read_text(encoding="utf-8")
    sections = list(re.finditer(r"^## (R\d{2,}) · (.+)$", source, re.M))
    routes = []
    for index, match in enumerate(sections):
        end = sections[index + 1].start() if index + 1 < len(sections) else len(source)
        block = source[match.end():end]
        # The next section's explicit anchor precedes its heading.
        block = re.sub(r'\n<a id="r\d+"></a>\s*$', "", block)
        markers = re.findall(r"^<!-- reading-route: (.+) -->$", block, re.M)
        if len(markers) != 1:
            raise ValueError("Each reading topic requires one metadata record: " + match[1])
        record = json.loads(markers[0])
        if not isinstance(record, dict) or set(record) != {"id", "targets"} or record["id"] != match[1]:
            raise ValueError("Reading topic ID/heading mismatch: " + match[1])
        targets = record["targets"]
        if not isinstance(targets, list) or not targets or not all(isinstance(x, str) for x in targets):
            raise ValueError("Invalid reading topic targets: " + match[1])
        if len(targets) != len(set(targets)):
            raise ValueError("Duplicate reading topic targets: " + match[1])
        if known_ids is not None and any(x not in known_ids for x in targets):
            raise ValueError("Unknown reading topic target: " + match[1])
        record.update(
            title=match[2], source="docs/reading-map.md#" + match[1].lower(),
            scope="reading_guidance", text=block.strip(),
            source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        routes.append(record)
    if not routes or len(routes) != len({r["id"] for r in routes}):
        raise ValueError("Missing or duplicate reading topics")
    marker_count = len(re.findall(r"^<!-- reading-route:", source, re.M))
    if marker_count != len(routes):
        raise ValueError("Reading topic metadata outside a declared section")
    return routes
