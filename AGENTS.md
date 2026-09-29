# Repository editing notes

- Canonical content lives in `book/`, `essays/`, `guides/`, `SHUAQI.md` and `docs/`.
- Edit canonical content first. Run `python3 tools/build.py` to regenerate `index.html`, `llms-full.txt` and exported JSON.
- Run `python3 tools/check.py`, `python3 tools/build.py --check`, and `python3 -m unittest discover -s tests -v`.
- Preserve published card IDs and their underlying meaning. Add a new ID for a different activity; do not silently repurpose old links.
- Distinguish project values, original proposals, personal accounts, research results, and dated cultural reporting.
- Never turn a background study into validation of a card's action, duration, budget or efficacy.
- Do not upload private experience notes, local paths or credentials. A content change does not authorize purchases, messages, or external promotion.
- Present reader-facing files as the current guide, not an iteration diary. Keep comparison reports and release-planning notes outside the repository.
- Maintain later change descriptions in merge/pull requests, not a repository CHANGELOG or "what changed" sections on reader pages. Do not rewrite existing Git history to achieve this.
