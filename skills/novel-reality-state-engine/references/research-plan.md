# Reality State Engine research and implementation plan

## Goal
Build a cross-project layer that prevents the common failure where a model remembers events but does not let time, resources, physiology, cognition and knowledge boundaries constrain behaviour.

## Phase plan

### M0 — Contract and fixtures
- Define immutable event schema, valid-time intervals, state deltas, knowledge ledger and branch metadata.
- Add fixtures for normal fatigue, hunger with water available, cold exposure, injury, medication uncertainty and ambiguous time.
- Acceptance: deterministic validation; no silent state overwrite.

### M1 — Deterministic reducer
- Reduce events into resources, environment, physiological load, cognitive capacity and affordances.
- Use ranges when time or dosage is unknown.
- Acceptance: same event log produces the same Reality Card; superseded events remain queryable.

### M2 — Psychology bridge
- Encode Feeling → Thought → Action as a structured reasoning contract.
- Add competing hypotheses, protective factors, triggers and likely errors.
- Acceptance: the output never claims diagnosis or hidden motives as fact.

### M3 — Graph integration
- Create event → state → capacity → affordance → consequence edges.
- Query affected subgraphs before generation and write back approved deltas after generation.
- Acceptance: every important state change has provenance and valid time.

### M4 — Generation gates
- Pre-write gate checks required sources and creates a Reality Card.
- Post-write gate checks temporal, physiological, cognitive, knowledge, agency and consent-boundary consistency.
- Acceptance: intentionally over-capacity prose fails; a corrected version passes.

### M5 — Branching and rollback
- Keep mainline, interactive branches and draft hypotheses separate.
- Support snapshots, supersession and semantic rollback.
- Acceptance: branch events never silently alter another branch.

### M6 — Evaluation
- Measure state contradiction rate, character-capacity violations, knowledge leaks, resource continuity, action-cost coverage and delayed-consequence coverage.
- Add human review for psychological plausibility; automated checks are filters, not arbiters.

### M7 — Cross-project regression
- Run the same fixtures through long-form, interactive-fiction, behaviour consultant, graph and export paths.
- Acceptance: clean install and portable bundle retain the engine and tests.

### M8 — Domain adapters
- Add optional adapters for injury, illness, addiction, trauma, sleep deprivation, magic systems, cybernetic load and non-human physiology.
- Each adapter must declare assumptions and uncertainty; never silently turn fiction rules into medical claims.

## Research questions

1. Which physiological variables need deterministic arithmetic, and which should remain qualitative?
2. How should cognitive capacity degrade without making characters generically irrational?
3. How can we represent individual differences without using personality labels as destiny?
4. How should contradictory observations update belief without rewriting facts?
5. What is the minimum state needed to prevent continuity drift while keeping context affordable?
6. How should human authors approve low-probability but intentional reactions?

## Required deliverables

- `state-schema.md`
- `research-sources.md`
- deterministic reducer and validator
- Reality Card fixture set
- pre-write and post-write gates
- Graphify adapter contract
- cross-skill regression report
- portable bundle manifest entry
