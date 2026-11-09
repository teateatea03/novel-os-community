# State schema and provenance contract

## Event

This invented equipment-check example is synthetic and is not a manuscript excerpt.

```json
{
  "id": "T0001",
  "valid_time": {"start": "D1", "end": "D1", "precision": "day"},
  "status": "CANON",
  "actor": "technician",
  "action": "install_lens_cover",
  "observed_by": ["observer"],
  "facts": {"equipment": "lens_cover", "fit": "confirmed"},
  "state_delta": {
    "equipment.lens_cover.location": {"set": "telescope"},
    "equipment.telescope.exposure": {"set": "covered"}
  },
  "confidence": "EXTRACTED",
  "provenance": ["canon/events.md"]
}
```

## Current state

Derived state must record its sources and uncertainty:

```json
{
  "as_of": "D10",
  "source_events": ["T0016", "T0020"],
  "validity": {"last_meal_hours": {"min": 18, "max": 36}},
  "physical": {},
  "cognition": {},
  "psychology": {},
  "affordances": [],
  "knowledge_boundary": {},
  "derivation_confidence": "medium"
}
```

## State transitions

- Immutable events are never edited to make a later scene convenient.
- A new event can supersede a derived state, but must not erase the prior state.
- Unknown duration remains an interval.
- A branch must carry `branch_id`, `parent_checkpoint` and `canon_status`.
- A character's observed belief is not the same as world truth.

## Gate failure classes

- `TIME_CONTRADICTION`
- `RESOURCE_CONTRADICTION`
- `CAPACITY_OVERFLOW`
- `KNOWLEDGE_LEAK`
- `PLAYER_AGENCY_VIOLATION`
- `CONSENT_INFERENCE_ERROR`
- `MISSING_PROVENANCE`
- `BRANCH_MIXING`

## Executable input preflight

The heuristic CLI requires an object root, a nonempty `events` array of objects
with an `id` or legacy `turn`, and an object `world` with a nonblank string `now`.
Optional `world.resources`, `world.environment`, `knowledge_ledger`, `npcs`, and
character psychology must retain their documented container types; explicit null
or incorrect types are rejected rather than converted into defaults. An empty
NPC list is allowed. This is minimum executable input validation, not complete
event semantics, evidence/provenance, medical validity, or narrative quality.

`validate`, `card` and `gate` reject invalid state before inference.
`gate` also requires a readable, strictly decoded UTF-8 manuscript whose
`text.strip()` is nonempty. Invalid input returns exit 2 and JSON with
`ok=false`, `status=invalid_input`, `evaluation=not_evaluated`, and `card=null`;
it does not write an output card. Valid inputs retain the existing heuristic
checks. The universal facade/MCP transport must preserve the failure result.

## Scope

The engine is a writing consistency tool. It does not diagnose real people, calculate medical risk, or infer a real person's private mental state.
