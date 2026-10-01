# Local setup and portable installation

<!-- language-navigation --> [繁體中文](GETTING_STARTED.zh-TW.md) | **English** | [日本語](GETTING_STARTED.ja.md) | [한국어](GETTING_STARTED.ko.md) | [Español](GETTING_STARTED.es.md) | [Français](GETTING_STARTED.fr.md) | [Deutsch](GETTING_STARTED.de.md) | [Português](GETTING_STARTED.pt.md)

This guide covers the local runtime and portable bundle. Use and redistribution are governed by [LICENSE](../LICENSE); commercial reporting and payment details are in [COMMERCIAL_TERMS.md](COMMERCIAL_TERMS.md).

## Language coverage

Public documentation is available in Traditional Chinese, English, Japanese, Korean, Spanish, French, German, and Portuguese. Runtime skills, templates, and their technical references currently retain their original language. This eight-language documentation release does not translate the runtime.

## Choose a mode

- **Local tools:** Python 3.10+ and persistent UTF-8 files. Core validation, project scaffolding, and tests use the standard library
- **Agent runtime:** the above plus a host that can load sibling `SKILL.md` packages, read/write project files, and run Python. Register `novel-operating-system` as the entry point
- **Document/manual mode:** a host without shell or persistent files can follow the templates, but cannot claim CLI gates, installation, or durable state have run

Novel OS does not include a model, API account, web service, or private manuscript. There are 18 source skill directories: 17 installable runtime skills (one coordinator plus 16 collaborators) and the exporter.

## Check a fresh checkout

Run these commands from the repository root on a POSIX shell:

```sh
python3 --version
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 -m compileall -q skills scripts
python3 scripts/run_tests.py
```

Use a separate private project directory for real work. Do not copy existing manuscripts or databases into this checkout. For a synthetic first project, use the `mktemp` example in the root README. Explicit `--root` takes priority over `NOVEL_PROJECTS_ROOT`; without either, project initializers use `~/.novel-os/novels`.

## Build and test a local bundle

These commands use only repository files and temporary directories. No uploads, live models, API keys, or external research are involved. Build output must stay outside the source checkout so generated payloads are not committed by accident.

```sh
BUNDLE_WORK="$(mktemp -d)"
INSTALL_WORK="$(mktemp -d)"
EXPORTER="skills/novel-system-exporter/scripts"

python3 "$EXPORTER/build_novel_os_bundle.py" refresh \
  --source-root skills --bundle-root "$BUNDLE_WORK"
python3 "$EXPORTER/build_novel_os_bundle.py" verify \
  --bundle-root "$BUNDLE_WORK/payload"
python3 scripts/privacy_scan.py "$BUNDLE_WORK/payload"
python3 "$EXPORTER/verify_novel_os.py" --profile full \
  --bundle-root "$BUNDLE_WORK/payload" --output "$BUNDLE_WORK/verification.json"
python3 "$EXPORTER/install_novel_os.py" \
  --bundle-root "$BUNDLE_WORK/payload" --target "$INSTALL_WORK" --smoke-test
```

The full verification profile exercises a synthetic 100k+ character long-form pilot as well as local regression suites. This is a local correctness check, not live-model quality or cross-platform certification. The installer refuses to overwrite existing skills unless `--upgrade` is explicitly supplied; upgrades make local backups. Do not target a live skills directory for your first test.

To create an archive after those checks pass:

```sh
python3 "$EXPORTER/build_novel_os_bundle.py" build \
  --bundle-root "$BUNDLE_WORK/payload" \
  --output "$BUNDLE_WORK/novel-os-review.zip"
```

The manifest lists and hashes all packaged files, including all eight language versions of the project license, commercial terms, and third-party guide, plus the unchanged Humanizer-zh notice inside its adapted skill. Keep those notices with the archive and installation. The installer retains project-level notices under `novel-operating-system/DISTRIBUTION_NOTICES/` rather than overwriting the host's root license.

## Optional features

Install only what your host needs, in an isolated environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-optional.txt
```

The file lists compatibility ranges, not a reproducible lock. If you enable an optional integration, select/test its exact version and review its upstream terms. No optional dependency is needed for the core walkthrough above.

- NetworkX enables optional graph algorithms/GraphML; Graphify is installed separately for its extra exporters
- PyYAML enables YAML NPC projection input; MCP and its external Instagram server are optional integrations
- Independent model review needs a host-specific replacement for `minis-model-use` outside its original host. If unavailable, record it as not run
- `lieflat-less-ai-tone` is not bundled. Its source/license must be verified separately; without it, use the built-in human-voice workflow and record the extra pass as not run

See [THIRD_PARTY.md](../THIRD_PARTY.md), [platform compatibility](../skills/novel-system-exporter/references/platform-compatibility.en.md), and the [host adapter contract](../skills/novel-system-exporter/references/host-adapter-contract.en.md). Windows/native host and optional-service tests are separate acceptance work; a Linux smoke test does not verify them.
