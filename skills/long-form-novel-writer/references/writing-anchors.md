# Optional writing anchors

Use author-selected original excerpts when a chapter needs its immediate predecessor's
ending or a concrete voice sample. This is optional prompt context, not an automated
style score, canon update, continuity proof, or requirement to imitate every passage.
Use only text you have the right to process; do not publish private manuscripts or
third-party novel quotations with this repository. All examples below are synthetic.

Create a project-local JSON file with schema `minis.writing-anchors.v1`, an optional
`budget_characters` (default 2400), and an `anchors` array. Each anchor has:

- `id`: unique ASCII letters, digits, `_` or `-`
- `role`: `previous_chapter_tail` or `style_original`
- `order`: integer; ascending order, then ID, determines rendered order
- `file`: portable project-relative path, no traversal or symlinks
- `source_sha256`: SHA-256 of the complete original file bytes, pinned by the author
- `start` and `end`: inclusive one-based source lines; alternatively `tail_lines`
  selects the last N lines for `previous_chapter_tail` only
- `applies_to`: optional `chapters`, `povs`, `scenes` arrays; an empty or absent
  array is unrestricted. A restricted POV/scene requires a matching CLI value;
  applicability is exact metadata matching, not inferred from prose
- `skip_reason`: optionally `first_chapter`, `intentional_style_change`, or
  `author_disabled`; explicitly skipped anchors need no file/hash/range

Example configuration shape (replace the placeholder with the actual file hash):

```json
{
  "schema": "minis.writing-anchors.v1",
  "budget_characters": 2400,
  "anchors": [
    {"id": "prior-ending", "role": "previous_chapter_tail", "order": 10,
     "skip_reason": "first_chapter"},
    {"id": "quiet-voice", "role": "style_original", "order": 20,
     "file": "samples/quiet.md", "start": 2, "end": 3,
     "source_sha256": "REPLACE_WITH_64_LOWERCASE_HEX_DIGITS",
     "applies_to": {"povs": ["observer"], "scenes": ["quiet"]}}
  ]
}
```

```sh
python3 scripts/build_context_pack.py --root <project> --chapter chapter-002 \
  --query "signal" --writing-anchors writing-anchors.json --pov observer --scene quiet
```

No anchor is automatically selected from an arbitrary previous filename or inferred
style preference. Missing sources, changed pinned hashes, unavailable ranges, empty
excerpts and applicability mismatches produce explicit omissions. To intentionally
change voice, skip or replace the style anchor; do not mislabel the choice as drift.
Update a pinned hash only after reviewing the changed source. Changing an included
source after building still invalidates its v5 evidence and requires a rebuild.

## Budget and evidence contract

Anchors are considered in explicit order before ordinary retrieval. Their complete
excerpts reserve space within both the anchor character allowance and the overall
`--budget`; they do not consume ordinary `--top-k` slots. They have first admission
priority within the existing token input allowance, which retains system/output/
safety reserves. An anchor that does not fit is omitted whole, never silently sliced;
later smaller anchors can still fit. This does not reserve the complete serialized
prompt overhead, and model consumers can impose a smaller prefix limit.

Configured anchor files are excluded from ordinary keyword retrieval, including
when the anchor is skipped, stale, or outside its applicability. This avoids pulling
an intentionally excluded voice back into context. Put independent canon/reference
material in separate files when it must remain retrievable. Disabling the optional
config restores ordinary retrieval behavior.

The Markdown decision list and v5 `writing_anchors` sidecar report every configured
anchor, its role/order/applicability, fingerprint/range when available, placement,
and omission reason. `render_order` records only anchors actually embedded. Source
records retain normal v5 hashes and exact Unicode half-open pack offsets. Ranked
selection counts include eligible anchor candidates as well as retrieval candidates;
unavailable/inapplicable anchors appear only in the decision list.

Consumers reuse `assess_context` with the exact prefix sent to the model. Its
`writing_anchors[].inclusion` is `full`, `partial`, or `omitted`; an address or decision
line never counts as original text read. The pack's `inline` placement is not a
consumer read receipt. Truncation is visible even if the omitted anchor's decision
appears earlier in the prompt. Inclusion proves character delivery only, never
attention, understanding, style fidelity, or semantic completeness. Reader and style
judgments remain review suggestions under the existing evidence protocol.
