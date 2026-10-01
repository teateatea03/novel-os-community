# Contributing to Novel OS

Thank you for helping improve Novel OS. Contributions must preserve the project's source-available commercial terms and the privacy boundary.

## Privacy and rights are release blockers

Only contribute reusable system material that you have the right to share. Do **not** submit:

- manuscripts, chapter drafts, interactive sessions, story state, author feedback, or private project fixtures;
- character/world/research databases or records about real people;
- chat memories, local logs, generated backups, credentials, cookies, device paths, or private endpoints;
- copyrighted source text, leaked material, paywalled copies, or third-party code without compatible licensing and attribution.

Use fictional, minimal, clearly synthetic fixtures. Do not merely rename real private data.

Build bundles and create story projects outside the source checkout. A root virtual environment is allowed for local development but must not be committed.

## Before opening a pull request

```sh
python3 scripts/privacy_scan.py .
python3 -m compileall -q skills scripts
python3 scripts/validate_json.py .
python3 scripts/run_tests.py
```

The scanner and JSON validator review working-tree files, including untracked and gitignored files. They exclude Git metadata, generated Python/test caches, and confirmed root virtual environments; tracked files remain in scope. They reject symlinks, unreadable files, and non-UTF-8 source. Review the staged diff separately: a working-tree pass is not a scan of the staged index, Git history, or GitHub-retained objects.

Also inspect:

```sh
git diff --cached --name-only
git diff --cached
```

Explain any new dependency, external source, generated artifact, or platform-specific behavior in the pull request.

## Change expectations

- Keep code and documentation portable; platform defaults must be overrideable.
- Add or update tests for behavioral changes.
- Preserve canon/author authority and fail-closed safety contracts.
- Keep public examples synthetic and free of personally identifying information.
- Do not silently weaken privacy, provenance, or validation gates.

## Commit and review model

Use focused commits with an imperative summary. Pull requests require maintainer review. Security or privacy fixes should use private reporting rather than a public issue.

## Licensing

Contribute only material you have the right to distribute under [LICENSE](LICENSE). Identify modifications, keep the same license for project-derived changes, and preserve all required third-party notices. This does not transfer your copyright to the maintainer. Public pull requests must not include financial reports, payment details, or private creative material.
