# Portable Novel OS Bundle Contract

<!-- language-navigation -->

[繁體中文](bundle-contract.md) | **English** | [日本語](bundle-contract.ja.md) | [한국어](bundle-contract.ko.md) | [Español](bundle-contract.es.md) | [Français](bundle-contract.fr.md) | [Deutsch](bundle-contract.de.md) | [Português](bundle-contract.pt.md)

In the `novel-os-portable-v<version>/` package layout, `skills/` contains one coordinator and 16 specialized skills. `public-web-research/` provides safe, resumable public HTTP(S) acquisition and Evidence Run candidate staging. `novel-model-capability-compatibility/` maintains the model-capability probe/L0–L5/fallback contracts. `novel-reality-state-engine/` maintains the event → state → capability → behavior → prose validation tools. `novel-world-database-builder/` maintains world-database schemas, batch templates, handoff packages, and query specifications. `special-object-database-builder/` maintains version, capability, specification, and lifecycle schemas for props/armor/mechs/devices.

```text
novel-os-portable-v<version>/
├── MANIFEST.json
├── LICENSE
├── LICENSE.{zh-TW,ja,ko,es,fr,de,pt}.md
├── THIRD_PARTY.md
├── THIRD_PARTY.{zh-TW,ja,ko,es,fr,de,pt}.md
├── docs/
│   ├── COMMERCIAL_TERMS.md
│   └── COMMERCIAL_TERMS.{zh-TW,ja,ko,es,fr,de,pt}.md
├── references/
│   ├── portable-install.md
│   ├── portable-install.{en,ja,ko,es,fr,de,pt}.md
│   ├── platform-compatibility.md
│   ├── platform-compatibility.{en,ja,ko,es,fr,de,pt}.md
│   ├── host-adapter-contract.md
│   ├── host-adapter-contract.{en,ja,ko,es,fr,de,pt}.md
│   ├── bundle-contract.md
│   └── bundle-contract.{en,ja,ko,es,fr,de,pt}.md
├── skills/
│   ├── novel-operating-system/      # mandatory single entry point
│   ├── long-form-novel-writer/
│   ├── novel-character-deep-digger/
│   ├── human-behavior-personality-consultant/
│   ├── novel-worldbuilding-architect/
│   ├── novel-style-craft-director/
│   ├── novel-human-voice-editor/
│   ├── knowledge-relationship-graph/
│   ├── character-database-builder/
│   ├── immersive-interactive-fiction/
│   ├── unfinished-novel-completion/
│   ├── novel-world-database-builder/
│   ├── special-object-database-builder/
│   ├── novel-reality-state-engine/
│   ├── novel-model-capability-compatibility/
│   ├── novel-sensory-sound-prose/
│   └── public-web-research/
└── scripts/
    ├── install_novel_os.py
    ├── verify_novel_os.py
    └── build_novel_os_bundle.py
```

The braces in the layout abbreviate separate files for each listed language.

`MANIFEST.json` contains: bundle schema/version, package list, source skill versions, a SHA-256 digest and byte count for every payload file, a separate `distribution_notices` inventory, build time, exclusions, and runtime dependency declarations. The payload also includes a portable copy of the **platform compatibility guide**. It contains no secret, local absolute path, story project, account configuration, or world database.

## License and notice retention

- `--source-root` names the source `skills/` directory. Its repository parent must contain all 24 required notices: `LICENSE`, `THIRD_PARTY.md`, and `docs/COMMERCIAL_TERMS.md` in English, plus `LICENSE.<language>.md`, `THIRD_PARTY.<language>.md`, and `docs/COMMERCIAL_TERMS.<language>.md` for each of `zh-TW`, `ja`, `ko`, `es`, `fr`, `de`, and `pt`. Refresh refuses a missing, non-file, or symlinked required document before changing the payload. These are owner-selected project terms; upstream notices retain their own scope.
- The additional explicit allowlist is `LICENSE.md`, `LICENSE.txt`, `NOTICE`, `NOTICE.md`, `NOTICE.txt`, and `docs/COMMERCIAL_LICENSE.md`. If present, each is copied byte-for-byte. No other root `docs/` files are exported. In particular, `docs/COMMERCIAL_LICENSE_DISCUSSION.zh-TW.md` is a non-operative discussion draft and is not exported as a license or commercial terms.
- Skill-local `LICENSE`, `LICENSE.md`, `LICENSE.txt`, `COPYING`, `COPYING.md`, `COPYING.txt`, `NOTICE`, `NOTICE.md`, `NOTICE.txt`, `THIRD_PARTY.md`, and every file under `THIRD_PARTY_LICENSES/` are retained with the skill and declared in `distribution_notices`. Refresh checks their bytes against the source; build and install reject absent declarations, missing files, altered bytes, unsafe paths, or missing digest entries.
- The existing adapted Humanizer-zh material specifically requires `skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt`. It cannot be removed from the source or manifest while that material is distributed.
- New legally required filenames must be added to this explicit contract before release. Do not rely on a link to an unbundled document. Refresh removes obsolete optional root notice copies from an existing payload.
- The ZIP preserves the same root-relative layout. Installation stores all notice documents under `<target>/novel-operating-system/DISTRIBUTION_NOTICES/`, preserving paths such as `docs/COMMERCIAL_TERMS.md` and `skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt`, so relative license links still work. Skill-local upstream notices also stay in their original skill directories. The installer never writes `<target>/LICENSE`, `<target>/THIRD_PARTY.md`, or `<target>/docs/`.
- `novel-operating-system/INSTALLATION.json` records every installed notice's original path, installed path, document-copy path, SHA-256, and byte count. Staging and final installation verify both copies where applicable. Upgrade carries the previous coordinator and its notices into the normal skill backup, and restores them if installation fails. `DISTRIBUTION_NOTICES/` within the coordinator is reserved for installer-managed documents.
- To recheck an installation, run `python3 scripts/install_novel_os.py --target <SKILLS_ROOT> --verify-installed-notices` from the extracted bundle. This read-only mode checks root and upstream notice files against the installation record. Digests establish local integrity, not authenticity against an attacker who can replace both files and records; retain a trusted release separately.

## Runtime dependency declaration

Every release must ship all 32 explicitly allowlisted portability references: each of `portable-install`, `platform-compatibility`, `host-adapter-contract`, and `bundle-contract` under `references/`, with `.md` for Traditional Chinese and `.<language>.md` for each of `en`, `ja`, `ko`, `es`, `fr`, `de`, and `pt`. Declare these levels truthfully:

- **Baseline document workflow**: an LLM that can read the Skill files; no code execution required.
- **Automated local workflow (v2.7)**: Python 3.10+ (3.11+ recommended), a shell/process runner, persistent UTF-8 files, multi-skill discovery or an equivalent router, a branch lock, a single `ProjectRuntimeAdapter.commit()` production authority, seven Gates, typed semantic events, project readiness/projection freshness, author-feedback Quality Eval, and extraction capability if distributed as a ZIP. World databases additionally require writable `WORLD_DATABASE_ROOT`/`WORLD_DATABASE_WORK_ROOT`; special-object databases additionally require writable `SPECIAL_OBJECT_DATABASE_ROOT`/`SPECIAL_OBJECT_DATABASE_WORK_ROOT`.
- **Graph enhancement**: `networkx` for graph traversal; `graphifyy` plus `networkx` for Graphify HTML/community/Cypher exports. The graph JSON itself remains usable without either package.
- **Optional integrations**: Git for commits, web/browser tools for source research, and a host-specific second-model/sub-agent adapter for independent review. `independent_review.py` is Minis-specific until replaced.

No Node.js, database server, API key, or internet connection is required for the local baseline. A framework without file/process access must be described as document/manual mode, not a full automatic installation.


## Build policy

- The payload must contain **17** allowlisted skill directories (one coordinator + 16 specialized skills), portability references, installation/build scripts, and ordinary text/source/fixture/template files.
- Exclude `.git`, `.DS_Store`, `__pycache__`, `*.pyc`, `.env*`, `node_modules`, `dist`, `build`, all novel projects, databases, archives and system-specific files.
- Reject symlinks in the source skills path or any packaged skill before changing the payload; never follow a skill link into unrelated host files. Existing unapproved payload documents also fail refresh instead of silently entering a new manifest.
- Preserve executable bits for `scripts/*.py` where the source has them.
- Read only the local source skill tree and the explicit repository-level notice allowlist. Building is deterministic other than `built_at`.
- The bundle is self-contained: runtime helpers use Python standard library and discover dependencies relative to their installed location.

## Verify policy

`verify` must reject absent, altered, unexpected, or hash-mismatched payload files; then compile every Python file. The installer smoke test must additionally:

1. initialize a temporary novel project under active production authority;
2. verify direct FileStore canonical mutation is fenced;
3. execute the full Novel Judge suite, including Gate authority, readiness, command executor, Quality Eval v2, typed semantic events and traditional long-form production;
4. run the graph validator and long-form/Reality/capability regressions;
5. verify the bundled skill set and source-set drift; and
6. for a full release, run the isolated second-project contract probe plus 100k+ traditional long-form/knowledge-reversal/cascade pilot.

A platform that cannot execute Python is supported only at workflow/document level; call that limitation out in the handoff.
