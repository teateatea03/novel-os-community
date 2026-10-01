# Production Authority Contract v1

## Purpose

Every production novel project has exactly one canonical mutation path:

```text
ProjectRuntimeAdapter.commit
  → FileStore.transaction_lock
  → recover pending transaction
  → stale source-state check
  → append canonical event
  → write turn/audit/graph sidecars
  → replace canonical state
  → update branch manifest
  → clear journal
  → refresh project/runtime-head projections
```

Models, candidate builders, project scripts, UI, Markdown projectors and legacy
writers have zero direct canonical write authority.

## Authority record

Each branch contains `production-authority.json` with:

- schema `minis.production-authority.v1`
- mode `single_filestore_event_kernel`
- canonical commit API `ProjectRuntimeAdapter.commit`
- project/session/branch/namespace
- trusted baseline ID and state hash
- legacy writer mode `migration_read_only`
- cutover status and provenance

Baseline creation is not a normal commit. It requires explicit
`migration_authorized=True`, is allowed once on an empty branch, and writes a
checkpoint plus provenance. Step 3 owns historical reconstruction and real
production cutover.

## Authority versus projections

Canonical authority:

1. append-only event history
2. canonical state checkpoint
3. branch manifest
4. transaction journal while a commit is in flight

`runtime-head.json` and `project.json.production_authority` are synchronized
projections. They can be rebuilt and never authorize a transition by
themselves.

## Project adapters

A project adapter may:

- prepare candidate prose and deterministic operations
- invoke `ProjectRuntimeAdapter.commit`
- call `recover`, `status` and read-only projectors

It may not:

- call `FileStore.save_state`, `append_event` or `update_head` for normal
  production work
- replace `events.jsonl`
- write an independent HEAD or project canon pointer
- keep an active project-specific canonical writer
- treat candidate directories as a second event store

Legacy project writers remain readable only for migration evidence until Step
3. They must not be enabled alongside the shared adapter.

## Conformance requirements

An adapter is conformant only if isolated tests prove:

1. one canonical commit API is declared;
2. two processes using one source hash produce one commit and one stale reject;
3. event, state, branch manifest, runtime HEAD and project pointer agree;
4. baseline replay reaches current state hash;
5. real SIGKILL after event append, active manifest, index, state and head can
   recover, replay and clear the journal;
6. event integrity passes;
7. an unbound project cannot call production commit;
8. normal commit cannot initialize or silently replace a baseline.

Gate payload authorization is deliberately Step 2. Step 1 only guarantees a
single durable authority path; it does not claim the existing Gate policy is
complete.
