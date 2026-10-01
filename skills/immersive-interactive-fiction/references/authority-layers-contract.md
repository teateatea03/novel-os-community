# Authority Layers Contract v1

## Why this exists

A single `PASS` must never mean all of the following at once:

1. safe to commit canon
2. free of narrative bugs
3. editorially strong
4. readers will like it
5. the author prefers this version

Novel Judge therefore separates five authority layers.

## Layers

| Layer | Purpose | Default commit effect |
|---|---|---|
| `CANON_INTEGRITY` | state, agency, knowledge, reality, durability, authorization | hard block on P0 |
| `NARRATIVE_QA` | high-confidence continuity / prose-contract bugs with evidence | hard block only on high-confidence P0 |
| `EDITORIAL_DIAGNOSIS` | structure, pacing, arcs, scene function, craft suggestions | advisory only |
| `READER_RESPONSE` | blind/beta reader reactions | advisory only; never objective truth |
| `AUTHOR_DECISION` | explicit accept / reject / revise | preference truth source; not auto-derived from workflow commits |

## Finding shape

`minis.authority-finding.v1` should include:

- `layer`
- `code`
- `severity` (`P0` / `P1` / `P2` / `OK`)
- `confidence` (`high` / `medium` / `low`)
- `claim`
- `evidence`
- optional `span`
- optional `minimal_fix`
- `blocks_commit`
- `author_overridable`

## Policy

Default host policy:

- only `CANON_INTEGRITY` and high-confidence `NARRATIVE_QA` P0 can refuse commit
- editorial and reader layers never alone refuse commit
- author override remains forbidden for FAIL/P0 canon/agency/reality gates
- workflow commit proxies never become `AUTHOR_DECISION`

## Reports

- `minis.authority-layer-report.v1` — layered summary + commit decision
- `minis.narrative-qa-report.v1` — deterministic prose QA
- `minis.editorial-diagnosis.v1` / `minis.manuscript-diagnosis.v1` — advisory edit board
- `minis.narrative-bug-ticket.v1` — localizable narrative issue ticket

## Explicit non-claims

These components do **not** claim:

- literary greatness
- genre satisfaction
- emotional payoff quality
- market readiness
- author preference, unless an explicit author decision event exists

## Wave 2 additions

- Scene-bound `ProjectRuntimeAdapter.commit` requires explicit `author_decision` when `require_author_decision_on_scene_commit` is true.
- Successful scene commits append `AUTHOR_DECISION` feedback events.
- Pairwise harness: `pairwise_judge.evaluate_fixture_set` with order-swap consistency.
- Cold-read/beta workflow: `cold_read.py`.
- Scene goal diagnostics: `scene_goals.py`.
- Interactive coverage: `playtest_coverage.py`.

## Wave 3 (practitioner-aligned, 0.13.8)

Sources: Jane Friedman / Barbara Linn Probst (92-author survey); Andrew Noakes / The Niche Reader; Dabble beta-feedback practice; MT-Bench, Judging the Judges, Length-Controlled AlpacaEval, OffsetBias. Details in `judge-practitioner-methods.md`.

- Machine Narrative QA is a **prescan**. `cold_read_text` must not emit `READER_RESPONSE` findings or claim to be a beta reader.
- Human beta questionnaires use a short **core** list; optional craft questions are not required homework.
- One independent human report is an anecdote; two+ on the same code/locus is a `consensus_candidate`. Consensus is not `AUTHOR_DECISION` and the author may reject it.
- Scene Studio inspect/draft attach `scene_review` (QA + goals + editorial tickets) without blocking commit.
- Pairwise heuristic scores remain non-truth; swap consistency and length-gap visibility are required.
- CLI: `inspect-prose`, `diagnose`, `cold-read`, `open-beta`, `pairwise` are read-only / sidecar.
