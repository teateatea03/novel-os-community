# Random Event Suggestion Contract v1

## Product boundary

Only two user-visible modes exist in this release:

- `off` — default. No pool validation, draw, suggestion audit, agenda, or prose injection occurs.
- `on-suggestion` — an explicit eligible window may request one optional, non-canonical direction card.

Mode is branch-scoped and can only be changed by `user` or `author` authority. This release does not invent low/standard/high frequency, storyteller profiles, automatic cadence, shadow mode, or irreversible-event opt-ins.

## Non-canonical authority

A suggestion has `commit_authority: none` and empty `state_delta`, `graph_patch`, `knowledge_patch`, `timeline_patch`, and `prose_patch`. It cannot:

- declare that an event happened;
- act, decide, feel, trust, refuse, or speak for the player;
- reveal protected unknowns;
- establish death, pregnancy, marriage, betrayal, permanent injury, relationship formation/break, faction destruction, or world-rule changes;
- update State, Graph, Knowledge, relationships, objects, injuries, clocks, timeline, prose, or canon.

If the user/author wants to use a direction, `make_adoption_handoff()` creates only a planning handoff. The idea must be rebuilt against the current state and pass Reality, Knowledge, Player Agency, Character Behavior, World Rules, and Canon Gates. A prior draw never grants commit authority.

## Timing contract

Supported semantic request points are:

- `action_resolution` — only when the deterministic consequence is unclear and `randomness_needed=true`;
- `scene_boundary` / `transition`;
- `travel` / `downtime`;
- `post_scene` / `post_chapter`;
- `world_pulse`;
- `telegraphed_threat_due` — only after a perceptible warning.

Suppression is mandatory for meta/status/revision/clarification input, pending direct consequences, deterministic consequences already available, emotional closure, unresolved high-intensity scenes without a natural break, and untelegraphed threats.

The runtime does not schedule these points automatically. The host must make an explicit request at a verified semantic window. This prevents hidden background draws while still making timing auditable.

## Pool and selection

- Eligibility is checked before selection.
- Required roles are bound before an event enters the weighted tier.
- Protected actors/facts and category/dedup suppression are checked first.
- Urgency and frequency are separate: select the highest eligible urgency tier, then use frequency weights within it.
- `no_event_weight` is mandatory and participates in every non-empty draw.
- The algorithm is deterministic `sha256-weighted-v1`; provenance records source state hash, pool hash, seed, eligible set, weights, roll digest, selected item or no-event.
- Replaying a recorded suggestion uses its audit record; it must not redraw. Hosts pass a stable branch-scoped `request_id`; retrying that request replays the existing record instead of appending a duplicate.
- Suggestion audit records form a manifest-backed hash chain. A malformed, truncated, reordered, or tampered chain must block replay of an old request.
- Every suggestion carries its source state hash. Adoption handoff is rejected after state advances; the direction must be rebuilt against current state.

## Audit separation

Suggestion audits live under the branch's `random-events/suggestion-audit.jsonl`. They are non-canonical operational records and are not appended to the canonical world event log. Turning mode off performs no draw and writes no audit.

## Host integration

Interactive hosts display a generated direction to the user/author as optional. Long-form hosts request it only during chapter/scene planning or settlement, never while rendering prose. Both use the same runtime. Host adapters must keep lore activation separate from event delivery.
