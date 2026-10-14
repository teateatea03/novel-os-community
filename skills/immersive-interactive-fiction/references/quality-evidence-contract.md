# Quality evidence and first-acceptance statistics

Quality Eval v2 keeps explicit author feedback, observed revisions, and workflow
proxies separate. A feedback event qualifies as explicit evidence only when its
`explicit` field is the boolean `true`; false or missing flags do not qualify.
The fixture builder preserves those events as `observed_author_feedback` with
`explicit_author_decision: false`, outside explicit metrics and Gate calibration.
An AI-generated evaluation must not be labeled as a human owner's decision.

## Accepted-only denominator

`explicit_author_pass_at_1` retains its existing accepted-only meaning: the
fraction of explicit accepted samples whose known revision round is zero.
It is not a success rate over every attempt, rejection, or revision request.
A known round is a nonnegative integer, excluding booleans. Missing, null, or
invalid rounds remain unknown; they count neither as successes nor failures.
When no accepted sample has a known round, the metric is `null`.

Fixture evaluation and production telemetry share the same calculation and expose:

- `explicit_accept_known_round_count`
- `explicit_accept_unknown_round_count`
- `explicit_accept_round_coverage`: known accepts divided by all explicit accepts;
  `null` when no explicit accept exists
- `explicit_author_pass_at_1_denominator`: the denominator's meaning

For explicit accepts at rounds 0 and 2, the result is 0.5. Adding an accept with
an unknown round leaves 0.5 unchanged and lowers round coverage to 2/3.
Unknown-round decisions can still inform Gate calibration when their explicit
decision and Gate outcome are known; uncertainty concerns the round, not the decision.

## Rebuild derived data after upgrading

Previously generated fixtures may have promoted nonexplicit feedback and unknown
rounds. Rebuild those derived fixtures and their baseline from the original
append-only feedback ledger using `refresh_quality_evaluation(adapter)` (or the
existing host quality-refresh workflow). Do not edit or rewrite raw feedback
ledgers, event hashes, or canonical state. Evaluating an old derived fixture alone
cannot recover source provenance that the old builder discarded.
