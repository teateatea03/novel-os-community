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

## Scope

The engine is a writing consistency tool. It does not diagnose real people, calculate medical risk, or infer a real person's private mental state.
