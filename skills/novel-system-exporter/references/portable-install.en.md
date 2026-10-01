# Importing and Deploying Novel OS

Languages: **English** | [繁體中文](portable-install.md)

## Start with a capability inventory: choose the right deployment mode

Before delivery, have the target environment answer:

```text
1. Can it install multiple Skills/commands? Where is the entry-point directory or configuration?
2. Can the agent read and write persistent files, list directories, and run Python/shell commands?
3. Which Python version is available? Are networkx, graphifyy, and Git installations allowed?
4. Are web/browser tools, a second model, or sub-agents available, and how are they invoked through tools?
5. Where do project files live across new conversations, new workers, or restarts?
```

Choose according to the answers: **A: full installation** (Skills + shell + storage), **B: adapter integration** (custom agent tools), **C: knowledge-file mode**, or **D: single-prompt manual mode**. See [platform-compatibility.en.md](platform-compatibility.en.md) for the full assessment, packages, and each framework's adapter requirements. Without the prerequisites for A/B, do not claim that “automatic deployment” is complete.

## AI platforms with custom skill directories (A: full mode)

1. Extract the ZIP.
2. Run this from the extracted root directory:

   ```bash
   python3 scripts/install_novel_os.py --target /path/to/agent/skills --smoke-test
   ```

3. Have the platform rescan its skills, or restart its skill index.
4. Test with “Create a long-form novel project.” This should trigger `novel-operating-system`, create the project scaffold, determine whether research/worldbuilding/behavior/style/graph work is needed, and complete planning and gates before drafting prose.

**Upgrades:** add `--upgrade`. The installer moves existing skills with the same names into `<target>/backups/novel-os-<timestamp>-<unique>/` before replacing them; it restores the original files on failure.

### Licensing and third-party notices

The complete ZIP must retain the root `LICENSE`, `LICENSE.zh-TW.md`, `THIRD_PARTY.md`, `THIRD_PARTY.zh-TW.md`, `docs/COMMERCIAL_TERMS.md`, and `docs/COMMERCIAL_TERMS.zh-TW.md`, together with each skill's original third-party license files. The installer stores these notices under `<target>/novel-operating-system/DISTRIBUTION_NOTICES/`, preserving their original relative paths so license links in the documents continue to work. Upstream notices within skills also remain in their original locations. It does not overwrite the host's root `LICENSE` or `docs/`. Pre-upgrade notices are saved with the original skills in that upgrade's backup.

`novel-operating-system/INSTALLATION.json` records each notice's source/installed paths, SHA-256, and byte count. After installation, run this read-only check from the extracted ZIP:

```bash
python3 scripts/install_novel_os.py --target /path/to/agent/skills --verify-installed-notices
```

Missing or modified files cause failure. This is a local integrity check, not a substitute for a trusted release source. See the explicit document inventory in [bundle-contract.en.md](bundle-contract.en.md). Discussion drafts do not constitute effective licenses and are not exported as formal terms.

Manual porting modes B/C/D must also deliver the project license/commercial terms and all upstream notices together. Do not copy only `skills/` and omit the license documents.

## Custom agent/tool-calling frameworks (B: adapter required)

If a framework has no native `SKILL.md` runtime but does provide a system prompt, function calling, and file/command tools, extracting the ZIP alone does not complete deployment. The integrator must:

1. Place `novel-operating-system/SKILL.md` in the system/developer instructions and use its description to build an intent router.
2. Make the sixteen specialized skills available as resources that the router can read on demand; preserve the relative folder relationships.
3. For an abandoned or unfinished work, first complete the source/canon/evidence/intent/feasibility/branch/rights/provenance handoff in `unfinished-novel-completion`, then hand the selected branch to the long-form writer.
4. Map file reads/writes, directory listing, Python processes, a persistent workspace, `WORLD_DATABASE_ROOT`/`WORLD_DATABASE_WORK_ROOT`, `SPECIAL_OBJECT_DATABASE_ROOT`/`SPECIAL_OBJECT_DATABASE_WORK_ROOT`, and web research to the framework's tool API.
5. Replace the `minis-model-use` call in `independent_review.py` with the platform's second-model/sub-agent/API integration. If none is available, disable this step and record it as not run.
6. Use the deployment acceptance checklist in the documentation to test file persistence across runs and post-chapter state updates.

See [platform-compatibility.en.md](platform-compatibility.en.md) for common integration points in LangGraph/CrewAI/AutoGen, MCP, OpenAI/Claude/Gemini, and Dify/Flowise/Open WebUI. All require the framework integrator to build a router/tool adapter; this ZIP cannot automatically do that in an unfamiliar cloud account.

## Platforms with only one Skill import field (C: knowledge-file mode)

Upload or paste the entire `skills/novel-operating-system/` directory, including its references, and keep the other sixteen skill folders at the same level as attachments/knowledge files. Instruct the AI:

> Read novel-operating-system/SKILL.md first. All sibling skills are required collaborators in this system. Without a shell, create equivalent Markdown/JSON project files and show which gates cannot run. Do not falsely claim to have created Git snapshots, run validators, or completed graph exports.

## Chat-only/custom-instruction platforms (D: manual fallback)

Use `novel-operating-system/SKILL.md` as the primary instructions and the full `skills/` package as retrieval documents. This mode can port workflows, templates, schemas, output formats, rules, and checklists. It cannot guarantee automatic file creation, persistence across turns, CLI validation, ZIP installation, or trigger detection.

### Deployment checks for completing unfinished works

When handing over an abandoned work, retain the ordinary novel project files plus `completion-brief.md`, `source-manifest.json`, the evidence/intent/version/branch ledgers, `rights-and-publication.md`, `completion-provenance.md`, `completion-state.json`, and the completion Gate. Works with unknown or unauthorized rights default to `private-only`/`research` mode; do not directly publish their prose.

Do not put the project directly into the skill ZIP. Deliver a separate project folder or clean ZIP:

1. First check for sensitive information about real people, private sources, credentials, unauthorized source text, or drafts that should not be shared.
2. Run the existing system's `snapshot_project.py`, `deep_consistency.py`, and `chapter_gate.py`; include the results in the handoff note.
3. Clearly identify the canon cutoff chapter, unfinished draft chapters, the author's override authority, and known risks in `project-brief.md`.
4. After importing, the recipient should read the story bible, current state, timeline, reader ledger, plot threads, entity registry, and latest summary before continuing the story.
