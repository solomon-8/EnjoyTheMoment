# Repository editing notes

- The primary acceptance standard is a stronger work than the agreed reference: substantive depth, argument quality and readability, together with a distinctive position worth remembering and discussing. "Ready to play" is a supporting usability requirement, not the project's purpose or a substitute for that comparison.
- Prioritize the manifesto, central arguments and substantive chapters over additional cards, export formats or tools. First identify a concrete weakness through paired reading of the reference and our text; decide whether to deepen, restructure or cut before deciding to add. More words, citations, files or passing tests do not establish improvement.
- Evaluate attention at two separate levels: editorial reasons a passage may attract interest, and observed reader interest. Never present the former as proof of the latter. Keep comparative reviews and acceptance decisions outside reader-facing repository content.
- Canonical content lives in `book/`, `essays/`, `guides/`, `SHUAQI.md` and `docs/`.
- The `entry-arguments` excerpt in `README.md` is the canonical short argument index for the homepage, offline reader and AI full text. Edit it once and regenerate; don't maintain a second version in HTML. Links introduce arguments, not activity recommendations or evidence of persuasion.
- Keep the shared AI entrypoints short; topic-specific reading limits belong in canonical `docs/reading-map.md`, with visible links for every target ID. `data/reading-map.json` is generated. Verify full-text retrieval and route coverage with `tests/test_reading.py`; do not replace content accuracy checks with entrypoint length targets.
- Edit canonical content first. Run `python3 tools/build.py` to regenerate `index.html`, `llms-full.txt` and exported JSON.
- The same build also updates the complete Chinese EPUB in `downloads/` and its current input manifest. Preserve all reading text, expanded details, source limits, image bytes and attributions. `tools/epub.py --check` verifies reproducibility and package links; EPUBCheck and actual reader rendering are separate checks, not proof of reader comprehension.
- Run `python3 tools/check.py`, `python3 tools/build.py --check`, and `python3 -m unittest discover -s tests -v`.
- Preserve published card IDs and their underlying meaning. Add a new ID for a different activity; do not silently repurpose old links.
- Distinguish project values, original proposals, personal accounts, research results, and dated cultural reporting.
- Never turn a background study into validation of a card's action, duration, budget or efficacy.
- Do not upload private experience notes, local paths or credentials. A content change does not authorize purchases, messages, or external promotion.
- Present reader-facing files as the current guide, not an iteration diary. Keep comparison reports and release-planning notes outside the repository.
- Maintain later change descriptions in merge/pull requests, not a repository CHANGELOG or "what changed" sections on reader pages. Do not rewrite existing Git history to achieve this.
