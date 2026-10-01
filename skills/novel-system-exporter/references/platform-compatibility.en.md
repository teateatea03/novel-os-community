# Novel OS Platform Compatibility and Dependency Matrix

<!-- language-navigation -->

[繁體中文](platform-compatibility.md) | **English** | [日本語](platform-compatibility.ja.md) | [한국어](platform-compatibility.ko.md) | [Español](platform-compatibility.es.md) | [Français](platform-compatibility.fr.md) | [Deutsch](platform-compatibility.de.md) | [Português](platform-compatibility.pt.md)


This document must be delivered with the ZIP. Novel OS is a collection of **skill instructions + local templates/Python validators**, not a standalone model, chat platform, vector database, or cloud service. Whether it can be “automatically deployed” depends on whether the target AI framework permits reading multi-file skills, writing files, running commands, and optionally calling models/accessing the network.

```text
- 1 coordinator + 16 collaborating skills, for a total of 17 runtime Skills (the source also includes the exporter)
- Model-capability compatibility: `novel-model-capability-compatibility`, responsible for actual endpoint probes, L0–L5, adapters, fallback, and post-switch regression
- Reality state: `novel-reality-state-engine`, providing an event → state → capability → behavior → prose validation chain
- World databases: `novel-world-database-builder`
- Special-object databases: `special-object-database-builder`, with the authoritative root at `SPECIAL_OBJECT_DATABASE_ROOT`
- Completion of abandoned works: unfinished-novel-completion
```

## 1. Core components and their dependencies

| Component/function | System/format used | Minimum dependencies | Optional dependencies | Fallback when unavailable |
|---|---|---|---|---|
| Skill dispatch | `SKILL.md` YAML frontmatter + Markdown; `novel-operating-system` | An AI/agent that can load multiple text files | A Skills runtime that automatically triggers skills by description | Use the coordinator as the system prompt/project instructions and manually attach the other skills |
| Project persistence | Markdown, JSON, ordinary folders | UTF-8 file reads/writes | Git | Maintain same-named files in chat/Canvas/cloud documents; explicitly state that persistence across turns is not guaranteed |
| Long-form initialization and local gates | Python CLI, standard library | **Python 3.10+**, shell, writable disk | Git | Copy templates and checklists manually; do not claim gates/snapshots have run |
| Authoritative relationship graph | Graphify-compatible node-link JSON | Python 3.10+ (initialization, JSON validation) | `networkx`: path/affected; `graphifyy` + `networkx`: HTML, community analysis, Cypher export | Save/read graph.json; query relationships manually, without claiming visualizations or shortest paths were generated |
| World database | Graphify-compatible JSON; world/location/faction/resource/rule/event/claim nodes, source evidence, and incremental batches | Python 3.10+, persistent UTF-8 files | `networkx`/`graphifyy`: path, affected, HTML, GraphML, Cypher | Save graph.json and Markdown ledgers; perform version/knowledge checks manually, without claiming visualization exports are complete |
| Special-object database | Graphify-compatible JSON; object/version/variant/module/capability/specification/energy/constraint/possession/operation/lifecycle nodes and source evidence | Python 3.10+, persistent UTF-8 files | `networkx`/`graphifyy`: path, affected, HTML, GraphML, Cypher | Save graph.json and object ledgers; perform version/specification conflict checks manually, without claiming visualization exports are complete |
| Interactive fiction | JSON-compatible state, Markdown turn log | File reads/writes; Python 3.10+ supports validation/checkpoints | Long-term memory/database | Review the state pasted into chat on each turn; retention after reopening a conversation is not guaranteed |
| Completion-source research and validation | Unfinished works | `unfinished-novel-completion`; research/attachment tools are optional | `source_ingest.py` records hashes, versions, completeness, and rights status; `completion_gate.py` checks overclaims about intent and publication boundaries | |
| Independent model review | The host's model-calling CLI/API | None; not required | Ability to call a second model or sub-agent | Use a manual/same-model checklist; do not claim “reviewed by an independent model” |

### Source research and unfinished-work tools

The basic tools in `unfinished-novel-completion` use only the Python standard library: `init_completion_project.py`, `source_ingest.py`, `compare_source_versions.py`, `branch_diff.py`, `feasibility_report.py`, `sync_graph.py`, `completion_gate.py`, `provenance_report.py`, and `run_regression.py`. Network access, OCR, PDF tools, browsers, and a second model are all optional. Without them, user-provided files can still be processed, but the scope of sources and unknowns must be identified; do not pretend verification took place.

### Minimum “fully automated” environment

- **Python 3.10 or later:** current core scripts use the `X | None` type-union syntax; Python 3.11+ is recommended.
- **POSIX shell or equivalent process runner:** to run the Python CLI.
- **Writable persistent filesystem:** to install skills and save novel projects; at least one writable skills directory and one projects directory are required.
- **UTF-8 file support:** stories, templates, JSON, and Traditional Chinese content all use UTF-8.
- **ZIP extraction:** required only for ZIP distribution; Git/folder upload can be used instead.
- **Local standard library:** core initializer, ledger, gate, state, and bundle scripts depend only on the Python standard library; the basic smoke test does not require `pip install`.

These features do not require an API key, database, Node.js, or network access.

### Optional dependencies (enhancements, not the baseline workflow)

```bash
# Graph paths, cascading queries, GraphML
python -m pip install networkx

# Graphify HTML/community/Cypher exports; the upstream package is named graphifyy
python -m pip install graphifyy networkx

# Git version snapshots and gate-protected commits
git --version
```

- `relationship_graph.py init/validate/search/neighbors/timeline/add/import/snapshot` can use only the Python standard library; `path`/some cycle checks require `networkx`.
- `relationship_graph.py export` requires **`networkx` + `graphifyy`**. Without them, retain `graph.json` and do not falsely claim HTML/GraphML/Cypher output was generated.
- `independent_review.py` is currently a **Minis-specific adapter** that calls `minis-model-use`. In another framework, replace it with that framework's second-model/sub-agent/API adapter, or disable this optional review step.
- `novel_git.py` is an optional version-control layer. Without Git, `snapshot_project.py` can still create file snapshots.

## 3.2 Host binding points and required replacements

The bundle's core data formats are portable, but the integrator must address these **host/framework binding points**:

| Binding point | Current Minis usage | What other AI frameworks must do |
|---|---|---|
| Default novel root | `<NOVEL_PROJECTS_ROOT>` | Set `NOVEL_PROJECTS_ROOT` or pass `--root <persistent-projects-root>` to each initializer; do not assume `<MINIS_ROOT>` exists |
| Character database root | `<CHARACTER_DATABASE_ROOT>` | Map `<CHARACTER_DATABASE_ROOT>` and map batch staging to `<CHARACTER_DATABASE_WORK_ROOT>`; both must be accessible to the same project/agent |
| Special-object database root | `<SPECIAL_OBJECT_DATABASE_ROOT>` | Map `<SPECIAL_OBJECT_DATABASE_ROOT>` and map batch staging to `<SPECIAL_OBJECT_DATABASE_WORK_ROOT>`; both must be accessible to the same project/agent |
| Interactive-fiction state root | `<INTERACTIVE_PROJECTS_ROOT>` | Map `<INTERACTIVE_PROJECTS_ROOT>` and ensure state/checkpoints/logs can be read across runs |
| Independent review | `minis-model-use run` | Rewrite the command adapter in `independent_review.py`, or create an equivalent sub-agent function; preserve the JSON schema, error artifacts, and rule against automatic promotion to canon |
| Skill discovery | Minis skill registry + sibling directories | Register **17** descriptions (the coordinator + sixteen specialized skills), or build an intent router; allow the agent to read sibling resource files on demand |
| Long-term state | Minis shared directory | Map a durable volume, database, artifact store, or framework checkpointer, retrieving state by project ID |
| Research tools | Minis browser/shell | Map framework browser/search/file tools; otherwise restrict research to user-provided material |

- `init_novel_project.py` already supports `NOVEL_PROJECTS_ROOT`; an explicit `--root` takes precedence. The `<..._ROOT>` placeholders for character/world/special-object databases and interactive fiction must be replaced by the framework router/deployment configuration. Every `<MINIS_ROOT>/...` in the original documentation is an **example default path** outside Minis, not a hard system requirement.

## 4. AI framework capability levels

### A | Native Skills + shell + filesystem (full mode)

For frameworks with a Skill runtime, agent tools, and a sandbox/terminal. Install the complete package directly by running:

```bash
python3 scripts/install_novel_os.py --target <SKILLS_DIR> --smoke-test
```

**The framework must:**

1. Register `<SKILLS_DIR>/novel-operating-system/SKILL.md` as the primary triggerable skill.
2. Preserve all **17** skill folders (the coordinator + sixteen collaborating skills) as siblings; do not upload only the entry-point file.
3. Allow the agent to read sibling skills' `SKILL.md`, templates, references, and scripts.
4. Provide a safe command tool or process runner for `python3`.
5. After reindexing/restarting the skill registry, use the smoke-test results for acceptance.

**Recommended additions:** web research tools, a second-model adapter, Git, `networkx`, and `graphifyy`.

### B | Custom agent/tool-calling frameworks (adapter required)

For frameworks with a system prompt, function calling, and file tools, but no understanding of `SKILL.md`.

**The framework integrator must:**

1. Put `novel-operating-system/SKILL.md` into the agent's system/developer instructions; retain the YAML description as routing rules.
2. Make the remaining **sixteen** skills retrievable reference documents, or build a router for them that loads the appropriate `SKILL.md` according to user intent.
3. Map tools:
   - shell → Python scripts;
   - read/write/list files → project files and state;
   - web search/browser → public-source research;
   - second-model/sub-agent → a replacement adapter for `independent_review.py`.
4. Replace the Minis-specific `minis-model-use` call with the framework's own model client. Preserve the original JSON review schema, failure artifacts, and principle that “machine_suggestion is not automatically promoted to canon.”
5. Specify a durable storage key/workspace so the same work's files are carried across conversations/workers.
6. Implement automatic skill triggering or explicitly disable it; putting **17 Skill documents** into context does not justify claiming they will automatically collaborate.

### C | Chat AI supporting only knowledge-file uploads/custom instructions (document mode)

Writing conventions, templates, data schemas, and checklists are portable, but genuine automation is unavailable.

**Required:** upload the complete `skills/` subtree; set the coordinator as the project instructions; each turn, attach or have the AI consult the work's current state, story bible, timeline, character files, reader ledger, and previous-chapter summary.

**Do not promise:** automatic folder creation, CLI gates, hash verification, Git, Graphify export, cross-chat memory, background tasks, or second-model review.

### D | Models with only a single system prompt (manual fallback)

Paste a condensed coordinator into the system prompt and use the specialized skills and project templates as a knowledge base. The user/integrator must manually save the state documents produced on each turn. This preserves the reasoning framework but is not equivalent to the full Novel OS.

## 5. Common framework integration checklist

| Type | Where it belongs | Required configuration | Key caution |
|---|---|---|---|
| OpenAI Assistants/Responses-style | System instructions + vector/file search + code interpreter/custom sandbox | Build a router, persistent file store, and Python execution adapter | Do not assume files synchronize automatically across runs; project files must be saved back explicitly |
| Claude Projects/MCP-style | Project instructions + knowledge files; MCP filesystem/shell server | Expose skills as resources; use MCP for reads/writes/runner/web | Without MCP, this is level C and cannot run scripts |
| Gemini Gems/Vertex Agent-style | System instruction + File Search/Code Execution/Cloud Storage | Connect durable storage, a function router, and a Python runner | Gem instructions alone generally do not provide cross-conversation file workflows |
| LangChain/LangGraph/CrewAI/AutoGen-style | Router node + file tools + subprocess tool + durable checkpointer | Load skills by intent, preserve project ID, and build a review-agent adapter | Skill discovery and state checkpoints must be implemented; extraction alone does not activate them |
| Open WebUI/AnythingLLM/Dify/Flowise-style | Knowledge base + agent workflow/tool nodes | Upload skill files, connect shell/Python tools, and mount a persistent volume | Pure RAG chat is level C; workflows are needed to reach A/B |
| World database host | `WORLD_DATABASE_ROOT` + `WORLD_DATABASE_WORK_ROOT` | Mount a persistent world graph and batch workspace; provide snapshot/validate/affected/export | Without a process runner, save only JSON/Markdown and do not claim the Graphify CLI has run |
| Special-object database host | `SPECIAL_OBJECT_DATABASE_ROOT` + `SPECIAL_OBJECT_DATABASE_WORK_ROOT` | Mount a persistent special-object graph and batch workspace; provide snapshot/validate/affected/export | Without a process runner, save only JSON/Markdown and do not claim special-object validation or export has run |
| Coding agents such as Cursor/Claude Code/Codex CLI | Skills/commands directory + workspace | Install **17** folders and configure Python and the workspace root | The conversational model-review adapter must be rewritten for the relevant CLI |

These names illustrate integration types only. Product versions, plans, and permissions vary; confirm their latest documentation before deployment.

## 6. Deployment acceptance checklist

After integration, the host or integrator should verify each item:

- [ ] `novel-operating-system` and sixteen neighboring specialized skills can be read.
- [ ] After writing a test file, a new agent run/conversation can read it back.
- [ ] `python3 --version` is ≥ 3.10; if graph exporters are needed, `networkx`/`graphifyy` can be imported.
- [ ] `python3 scripts/install_novel_os.py --target <SKILLS_DIR> --smoke-test` passes, or items that cannot run are explicitly documented.
- [ ] A new test novel project has its story bible, state, timeline, reader ledger, and graph.json created.
- [ ] The agent writes a short passage, updates state, and continues in a new run, demonstrating that continuity does not rely only on leftover context.
- [ ] If research is enabled, it can record URLs/sources/confidence rather than treating search snippets as canon.
- [ ] If second-model review is enabled, adapter failures produce only an unavailable artifact, without blocking or fabricating results.

## 7. Platform limitations and responsibility boundaries

- The target model's content policies, tool permissions, token limits, data retention, and network rules are independent of Novel OS and cannot be overridden by this Skill.
- “Automatic deployment” means automatic installation, scaffolding, and router loading inside an **agent framework with installation/file/shell permissions**. It does not mean permanently installing the ZIP by giving it to any chat model.
- External models, browsers, and Git are all optional enhancements. When absent, state the fallback mode explicitly; do not use completion claims to conceal capability gaps.
