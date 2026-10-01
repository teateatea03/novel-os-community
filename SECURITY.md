# Security and privacy policy

<!-- language-navigation --> [繁體中文](SECURITY.zh-TW.md) | **English** | [日本語](SECURITY.ja.md) | [한국어](SECURITY.ko.md) | [Español](SECURITY.es.md) | [Français](SECURITY.fr.md) | [Deutsch](SECURITY.de.md) | [Português](SECURITY.pt.md)

## Supported versions

Security and privacy fixes target the current `main` branch.

## Reporting

Do not file public issues containing personal data, credentials, private manuscripts, session logs, unpublished story material, or research records. Use private vulnerability reporting when enabled. If no private contact is available, open an issue asking the maintainer for a private reporting channel without including sensitive details.

## Contribution boundary

Contributors must submit only material they have the right to share. Never commit:

- API keys, passwords, tokens, SSH keys, cookies, environment files, or device paths;
- private conversations, agent memories, logs, backups, or exports;
- unpublished fiction, interactive-session state, or personal research data;
- data about real people that is not appropriate for public redistribution.

## Before publishing a change

1. Review `git diff --cached --name-only`.
2. Run `python3 scripts/privacy_scan.py .`.
3. Inspect any finding manually; do not suppress a finding without a written reason.
4. Confirm that every included file belongs to the reusable system, not a live project or private dataset.

## Disclosure process

If private material is committed or exposed, stop further distribution, make the repository private if necessary, revoke affected credentials, preserve evidence for review, and remove the material from current and historical Git objects before reopening access.
