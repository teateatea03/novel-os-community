# Novel OS Host Adapter Contract

Languages: **English** | [繁體中文](host-adapter-contract.md)

**Source consistency note:** the Skill router row below says “fifteen specialized skills,” while section C and the current bundle inventory specify one coordinator plus sixteen specialized skills (17 total). This translation preserves the source wording rather than silently changing the contract; reconcile the discrepancy when reviewing the source contract.

This contract is for integrators of AI frameworks other than Minis. Novel OS is not a plugin that can acquire file access, model access, or cross-conversation memory simply by uploading a ZIP. The host must provide the following capabilities for the deployment to qualify as automated.

## A. Minimum interfaces the host should provide

| Capability | Minimum operations | Novel OS use | If unavailable |
|---|---|---|---|
| Skill router | `load_skill(name)`/read resource files | The coordinator loads fifteen specialized skills by intent | Manually include the appropriate Skill in the prompt |
| Persistent storage | `read(path)`, `write(path)`, `list(path)`, `mkdir(path)` | Project bible, chapters, ledgers, state, graphs, and snapshots | Document-only mode; no guarantee of continuity across runs |
| Process runner | `run(argv, cwd)` | Run Python initializer, gate, state, and graph tools | Use templates and checklists manually; do not claim validation has run |
| Project identity | Stable `project_id` → storage root | Read the same novel's state in a new conversation/worker | The user manually supplies files/summaries each time |
| Branch writer lock | `lock(project,session,branch)`/transaction lock | Serialize recovery, stale-hash, event, state, and manifest commits | Allow only a single writer; do not claim multi-worker safety |
| Model task adapter | Accept `minis.model-task.v1`, persist the schedule first, let workers claim with a lease, and return a fixed schema | Restrict L1/L2 models to individual extract/plan/render/repair tasks; support retry/cancel/stale/restart recovery | Document mode or manual forms; models have no state authority |
| Runtime/event versioning | Runtime build, event schema, transition contract, golden replay fixture | Replaying old history after an upgrade still produces the same state hash; unknown contracts fail closed | Freeze the old runtime; upgrade only after manual migration |
| Story solver | Bounded storylet state exploration | Find unreachable states, broken targets, and soft locks while disclosing exploration limits | Manual path review; do not claim validation of all paths |
| Random-event suggestion control | Branch-scoped `off`/`on-suggestion`, semantic window, seeded pool, non-canonical audit | Offer optional direction cards only in eligible windows, preserving no-event outcomes and reproducible provenance | Keep fixed at `off`; do not secretly draw through prompts or treat suggestions as canon |
| Memory/Graph projector | Event → episodic memory; events → Graphify projection | Traceable memory and rebuildable graphs | Preserve events; mark derived indexes as not updated |
| Graphify completion index | `sync_graph.py` synchronizes sources, claims, and branches to the existing `graph.json` | Queryable sources, evidence, versions, and completion hypotheses | The graph is a derived index and must not overwrite prose/canon in reverse |

The process runner should prefer **argv arrays over concatenated shell strings**, stay within project/skill workspaces, and retain stdout, stderr, and exit code as gate artifacts.

## B. Path mapping

Deployment configuration should provide the following values. Do not hard-code Minis paths into another environment:

```text
SKILLS_ROOT=/agent/skills
NOVEL_PROJECTS_ROOT=/agent/data/novels
CHARACTER_DATABASE_ROOT=/agent/data/character-databases
CHARACTER_DATABASE_WORK_ROOT=/agent/work/character-db-batches
WORLD_DATABASE_ROOT=/agent/data/world-databases
SPECIAL_OBJECT_DATABASE_ROOT=/agent/data/special-object-databases
SPECIAL_OBJECT_DATABASE_WORK_ROOT=/agent/work/special-object-db-batches
INTERACTIVE_PROJECTS_ROOT=/agent/data/interactive-fiction
```

- `init_novel_project.py` can read `NOVEL_PROJECTS_ROOT`, or accept an explicit `--root`.
- `SPECIAL_OBJECT_DATABASE_ROOT` stores the authoritative special-object database at `graphify-out/graph.json`; `SPECIAL_OBJECT_DATABASE_WORK_ROOT` stores batch JSON and handoff packages and cannot replace the authoritative copy.
- `WORLD_DATABASE_ROOT` stores the authoritative world database at `graphify-out/graph.json`; `WORLD_DATABASE_WORK_ROOT` stores world batch JSON and handoff packages and cannot replace the authoritative copy.
- Other roots are router/framework adapter settings. Replace the `<..._ROOT>` placeholders in the relevant Skills with actual persistent paths.
- All files for a novel must reside under the same project root that can be read again; do not keep only the latest chapter in temporary chat context.

## C. Required deployment procedure

1. Extract the bundle and run this first:

   ```bash
   # First confirm Python, hashes, and the complete smoke test are available:
   python3 scripts/install_novel_os.py --target "$SKILLS_ROOT" --smoke-test
   ```

2. Register **17** Skills (the coordinator + 16 specialized Skills). `novel-reality-state-engine` must provide event/state JSON, a Reality Card, and an executable Reality Gate. `novel-model-capability-compatibility` must provide text/JSON/tool/state probes of the actual endpoint, capability levels, and fallback. `novel-sensory-sound-prose` must retain its sound/five-sense prose contract. Preserve sibling relative paths.
3. Map `project_id` to the persistent roots above and authorize the agent to read and write that project's files.
4. Run the initializer for a new project and confirm that Markdown/JSON/`graphify-out/graph.json` are all created successfully.
5. Close and start a new agent run, asking it to read the state before continuing the story, to verify that it does not rely on temporary context.
6. Have two workers commit concurrently against the same source state hash: exactly one must succeed, and the other must receive stale-hash/conflict. Then verify the current state hash through event replay.
7. Create two episodic memories and verify that reflection cites at least two existing evidence IDs. Compile an L1 render task and confirm that the package contains no hidden truth and has `may_commit_state=false`.
8. Rebuild the interactive Graphify projection from events. Deleting and rebuilding it should produce the same source hash.
9. Retain at least one golden-history fixture. Replaying it with a new runtime must produce the expected state hash, and unknown transition contracts must be rejected.
10. Create a model activity and verify recovery after lease expiry, marking old results as stale after state advances, and blocking the author console while an activity is pending.
11. Create a storylet fixture containing unreachable states, broken targets, and soft locks; confirm that the solver detects all of them and explicitly states max depth/max states.
12. After compacting events, delete the index and tamper with the archive. The manifest integrity gate must reject it before the index is rebuilt.
13. Verify that a new branch defaults to `off`, with no draws or audit writes. After the user enables `on-suggestion`, use a fixed seed at a scene boundary to obtain the same suggestion/no-event outcome, and confirm that the canonical event log, State, Graph, Knowledge, and prose remain unchanged.
14. Submit requests for meta input, a pending direct consequence, high-pressure situations with no natural break, an existing deterministic consequence, and an unforeshadowed threat; all must be suppressed. Adopting a suggestion may only create a planning handoff and must list the Reality/Knowledge/Agency/Behavior/World/Canon Gates.
15. Verify the active segment's manifest hash/bytes/count: after deleting the event index, tampering with the active log must fail closed. Activity claims return a fencing token; completion must be rejected for old tokens, missing tokens, or expired leases. All file-based IDs must reject path traversal. Retrying the same random-event `request_id` must not redraw or create a second audit entry. A tampered audit hash chain must not be replayed, and expired suggestions must not create adoption handoffs.

## D. Optional tool adapters

### Web research

If the host provides browser/search tools, the router must record search results, URLs, publishers, dates, and short quotations in research/graph evidence fields. Without a browser, it may only process user-provided material, must use `【待定】` (“undetermined”)/`【提案】` (“proposal”), and must not pretend to have verified sources.

### Second-model/sub-agent review

`long-form-novel-writer/scripts/independent_review.py` currently calls Minis's `minis-model-use`. Non-Minis frameworks must do one of the following:

1. Write a framework adapter that accepts `role`, `prompt`, and `max_tokens`, calls another model/sub-agent, and saves the raw text and parsed JSON under `reviews/`; or
2. Disable independent review, use local gates/manual checklists instead, and mark “second model not run” in the handoff.

In either case, preserve these output rules: `machine_suggestion` cannot be directly promoted to `[CANON]`; issues without two supporting pieces of evidence go only into `questions`; failures must produce an `unavailable` artifact and must never silently count as passing.

### Graphs and version control

- `networkx`: enables path, affected, GraphML, and related features.
- `graphifyy` + `networkx`: enables Graphify HTML, community analysis, and Cypher exports.
- Git: used only for commits/branches; file snapshots remain available without Git.

These are enhancements, not prerequisites for starting a novel.

## E. Minimum router logic

```text
if request is to create/update/query/compare/export a special-object database:
    load special-object-database-builder
    add novel-worldbuilding-architect + knowledge-relationship-graph
    add character-db + behavior when operator/autonomous-machine/personality matters
    add long-form when linked to a novel project or chapter state
elif request is to create/update/query/export a world database:
    load novel-world-database-builder
    add novel-worldbuilding-architect + knowledge-relationship-graph
    add long-form when linked to a novel project or chapter state
elif request is cross-chapter writing/continuation/outline revision:
    load long-form + behavior
    add world/style/graph only when the story state needs them
elif request is character research:
    load character-deep-digger
    add behavior + character-db/graph when evidence or persistence is needed
elif request is a human-voice/Taiwan Traditional Chinese/character-voice revision:
    load human-voice-editor after content/continuity/style checks
elif request is completion of an abandoned/unfinished novel, original-author intent, or an alternative ending:
    load unfinished-novel-completion
    add long-form + evidence/source tools + world/behavior/style/graph as needed
elif request is free-input interactive fiction:
    load immersive-interactive-fiction
    add world/behavior/style/graph by scene complexity
```

The coordinator should handle this router first. Do not blindly put every Skill into the model context on every turn.

## F. What the bundle cannot do automatically

- Install Skills, configure API keys, enable tool permissions, or create databases in unauthorized cloud accounts.
- Give a chat-only model a shell, filesystem, permanent memory, or multi-model capabilities.
- Override the target model/platform's content policies, token limits, privacy rules, or network restrictions.

If any prerequisites are missing, use the B/C/D fallback modes in [platform-compatibility.en.md](platform-compatibility.en.md) and list each disabled feature in the deployment report.
