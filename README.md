# Novel OS

<!-- language-navigation -->

[繁體中文](README.zh-TW.md) | **English** | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt.md)

Novel OS is a reusable collection of AI-agent skills and local Python tooling for long-form fiction, interactive fiction, continuity, character/world research, behavioral consistency, provenance-aware graphs, and narrative validation.

> **License:** source-available under the [Novel OS commercial profit-share license](LICENSE), copyright teateatea03. Noncommercial use is free; commercial use owes 0.5% of annual related positive net profit. Modifications and redistribution keep the same terms and notices. This is not MIT, GPL, or an OSI-open-source license.

For commercial-use and dual-token payment details, see [commercial profit sharing and payment information](docs/COMMERCIAL_TERMS.md). Rights to users’ novels and other outputs are not transferred to the system owner.

## Language coverage

Public documentation is available in Traditional Chinese, English, Japanese, Korean, Spanish, French, German, and Portuguese. Runtime skills, templates, and their technical references currently retain their original language. This eight-language documentation release does not translate the runtime.

## Privacy boundary

This source repository intentionally excludes:

- manuscripts, chapter drafts, interactive play sessions, story state, and author-feedback datasets;
- character, world, special-object, and real-person research databases;
- chat memories, device-local state, backups, exports, credentials, private endpoints, and environment files.

Public examples and fixtures must be synthetic. Before every push or release, run the privacy scanner and review the staged manifest.

## Repository layout

- `skills/` — reusable skill packages, scripts, templates, and synthetic fixtures
- `scripts/` — privacy, validation, and test utilities
- `docs/` — project governance and publication-boundary documentation

The source tree has 18 skill directories: 17 installable runtime skills (one coordinator and 16 collaborators) plus the bundle exporter. The exporter is a packaging tool and is not installed as a runtime skill.

## Requirements

- Python 3.10+
- UTF-8 persistent storage
- Standard-library-only core paths
- Optional features: see `requirements-optional.txt` and `THIRD_PARTY.md`

Install optional Python dependencies in an isolated environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-optional.txt
```

Graphify integration is optional and installed separately according to its upstream documentation.

## First local run (no model or network required)

From the repository root, use Python 3.10+ and Git. The core checks and synthetic demo need no optional packages, API keys, or private manuscripts:

```sh
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 scripts/run_tests.py

# Keep generated project state outside the source repository.
DEMO_ROOT="$(mktemp -d)"
python3 skills/long-form-novel-writer/scripts/init_novel_project.py \
  --title "Synthetic Demo" --slug synthetic-demo --root "$DEMO_ROOT"
python3 skills/knowledge-relationship-graph/scripts/relationship_graph.py \
  validate --root "$DEMO_ROOT/synthetic-demo"
```

The initializer creates an empty planning/state scaffold; it does not generate a novel or call a model. Keep your own stories in a separate private directory. The initializer refuses to overwrite an existing project.

For an agent host, preserve the runtime skills as sibling directories and register `novel-operating-system` as the entry point. Hosts without persistent files or a Python process runner support document/manual mode only. See the [tested local build and install guide](docs/GETTING_STARTED.md) for bundle commands, smoke tests, optional integrations, and platform limits.

## Verification

```sh
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 -m compileall -q skills scripts
python3 scripts/run_tests.py
```

The Novel Judge suite must be run through `scripts/run_tests.py`; invoking its package-relative test files one by one is not supported.

The privacy and JSON checks inspect source files, including untracked and gitignored files. They exclude Git metadata, generated Python/test caches, and confirmed root virtual environments; tracked files are still checked. Symlinks, unreadable files, and non-UTF-8 text fail closed. Keep generated bundles and story state outside this checkout. The scanner reports file names and finding categories, never matched contents; it is a heuristic check, not proof of privacy or a history scan.

## Platform paths

Documentation uses placeholders such as `<SKILLS_ROOT>`, `<WORKSPACE_ROOT>`, and `<NOVEL_PROJECTS_ROOT>`. Configure these for the host platform. Runnable initializers default to `~/.novel-os/novels` unless `NOVEL_PROJECTS_ROOT` or an explicit `--root` is supplied.

## Safety and research scope

The research skills are designed for lawful, publicly accessible material and must not bypass login walls, CAPTCHA, paywalls, robots/access controls, or platform restrictions. Real-person research requires source provenance and must not turn unverified or sensitive material into factual claims.

## Governance

Read:

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [SECURITY.md](SECURITY.md)
- [THIRD_PARTY.md](THIRD_PARTY.md)

## License and contributions

Read [LICENSE](LICENSE) and [commercial payment details](docs/COMMERCIAL_TERMS.md) before commercial use. Only positive annual net profit from related products, services, and novels is included; unrelated business is excluded. Reporting is self-declared with no hidden telemetry or automatic collection. Third-party components keep their own licenses and notices.

Commercial users explicitly acknowledge the license version before use. Start with a GitHub issue containing no private or financial details to arrange a private reporting channel; do not post financial statements or payment records publicly. Contribution and redistribution rules are in [CONTRIBUTING.md](CONTRIBUTING.md).

## Verification limits

Core Linux tests and synthetic installation checks are provided. Optional Graphify/MCP/Instagram services, live models, native-agent integrations, and a cross-platform/Python-version matrix are not certified. Example model reports are synthetic illustrations, not evidence of measured provider/model performance.
