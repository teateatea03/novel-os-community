#!/usr/bin/env python3
"""Check source/bundle version, skill inventory, and retained notices offline."""
from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import os
import re
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXPORTER = ROOT / "skills/novel-system-exporter"


def load(name):
    spec = importlib.util.spec_from_file_location(name, EXPORTER / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DistributionContractTests(unittest.TestCase):
    def test_versions_and_inventory_match(self):
        builder = load("build_novel_os_bundle")
        installer = load("install_novel_os")
        self.assertEqual(builder.VERSION, installer.VERSION)
        self.assertIn("version: " + builder.VERSION, (EXPORTER / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual(builder.PACKAGE_SKILLS, installer.CORE)
        discovered = {p.name for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file()}
        self.assertEqual(discovered, set(builder.PACKAGE_SKILLS) | {"novel-system-exporter"})
        self.assertEqual(len(builder.PACKAGE_SKILLS), 17)

    def test_adapted_material_notice_survives_packaging(self):
        builder = load("build_novel_os_bundle")
        notice = Path("skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt")
        with tempfile.TemporaryDirectory() as tmp:
            builder.refresh(types.SimpleNamespace(source_root=str(ROOT / "skills"), bundle_root=tmp))
            payload = Path(tmp) / "payload"
            self.assertEqual((payload / notice).read_bytes(), (ROOT / notice).read_bytes())
            self.assertEqual(builder.verify_root(payload), [])
            installer = load("install_novel_os")
            target = Path(tmp) / "installed"
            with contextlib.redirect_stdout(io.StringIO()):
                installer.install(types.SimpleNamespace(bundle_root=str(payload), target=str(target),
                                                        upgrade=False, smoke_test=False))
            notices = target / installer.NOTICE_DIR
            # Source-relative links in the real THIRD_PARTY and commercial
            # documents must resolve inside the retained notice-only layout.
            self.assertEqual((notices / notice).read_bytes(), (ROOT / notice).read_bytes())
            self.assertEqual((notices / "docs/../LICENSE").read_bytes(), (ROOT / "LICENSE").read_bytes())
            self.assertEqual(installer.verify_installed_notices(target), [])
            listed = {entry["path"] for entry in builder.manifest_for(payload)["files"]}
            self.assertIn(notice.as_posix(), listed)
            manifest_path = payload / "MANIFEST.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["runtime_build"], builder.runtime_build(ROOT))
            manifest["runtime_build"] = "novel-judge/0.0.0"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertIn("runtime build drift", builder.verify_root(payload))

    def test_eight_language_notices_and_portability_guides_survive_distribution(self):
        builder = load("build_novel_os_bundle")
        installer = load("install_novel_os")
        expected_notices = {"LICENSE", "THIRD_PARTY.md", "docs/COMMERCIAL_TERMS.md"}
        for language in ("zh-TW", "ja", "ko", "es", "fr", "de", "pt"):
            expected_notices.update((f"LICENSE.{language}.md", f"THIRD_PARTY.{language}.md",
                                     f"docs/COMMERCIAL_TERMS.{language}.md"))
        self.assertEqual(set(builder.REQUIRED_ROOT_NOTICES), expected_notices)
        self.assertEqual(len(builder.PORTABILITY_DOCUMENTS), 32)
        pairs = (sorted(expected_notices),)
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stdout(io.StringIO()):
                builder.refresh(types.SimpleNamespace(source_root=str(ROOT / "skills"), bundle_root=tmp))
                payload = Path(tmp) / "payload"
                target = Path(tmp) / "installed"
                installer.install(types.SimpleNamespace(bundle_root=str(payload), target=str(target),
                                                        upgrade=False, smoke_test=False))
                archive = Path(tmp) / "eight-language.zip"
                builder.build(types.SimpleNamespace(bundle_root=str(payload), source_root=None,
                                                    output=str(archive), refresh=False))
            with zipfile.ZipFile(archive) as zipped:
                for pair in pairs:
                    for rel in pair:
                        expected = (ROOT / rel).read_bytes()
                        self.assertEqual((payload / rel).read_bytes(), expected)
                        installed = target / installer.NOTICE_DIR / rel
                        self.assertEqual(installed.read_bytes(), expected)
                        self.assertEqual(zipped.read(f"novel-os-portable-v{builder.VERSION}/{rel}"), expected)
                        for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", installed.read_text(encoding="utf-8")):
                            if "://" not in link and not link.startswith("#"):
                                self.assertTrue((installed.parent / link.split("#", 1)[0]).is_file(), link)
                for name in builder.PORTABILITY_DOCUMENTS:
                    expected = (EXPORTER / "references" / name).read_bytes()
                    self.assertEqual((payload / "references" / name).read_bytes(), expected)
                    self.assertEqual(zipped.read(f"novel-os-portable-v{builder.VERSION}/references/{name}"),
                                     expected)
            self.assertEqual(installer.verify_installed_notices(target), [])

    def test_runtime_version_is_read_without_execution(self):
        builder = load("build_novel_os_bundle")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "skills/immersive-interactive-fiction/scripts/novel_judge/runtime_versioning.py"
            source.parent.mkdir(parents=True)
            source.write_text('RUNTIME_BUILD = "novel-judge/1.2.3"\nraise RuntimeError("must not execute")\n', encoding="utf-8")
            self.assertEqual(builder.runtime_build(root), "novel-judge/1.2.3")
            source.write_text('RUNTIME_BUILD = str("novel-judge/1.2.3")\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                builder.runtime_build(root)


class PublicDocumentationTests(unittest.TestCase):
    LANGUAGES = ("en", "zh-TW", "ja", "ko", "es", "fr", "de", "pt")
    ROOT_STEMS = ("README", "LICENSE", "CONTRIBUTING", "CODE_OF_CONDUCT",
                  "SECURITY", "THIRD_PARTY", "docs/GETTING_STARTED", "docs/COMMERCIAL_TERMS")
    REFERENCE_STEMS = ("portable-install", "platform-compatibility",
                       "host-adapter-contract", "bundle-contract")

    def families(self):
        for stem in self.ROOT_STEMS:
            yield {language: ROOT / (stem + ("" if stem == "LICENSE" else ".md")
                   if language == "en" else f"{stem}.{language}.md")
                   for language in self.LANGUAGES}
        for stem in self.REFERENCE_STEMS:
            yield {language: EXPORTER / "references" /
                   f"{stem}{'' if language == 'zh-TW' else '.' + language}.md"
                   for language in self.LANGUAGES}

    def test_all_96_full_documents_have_eight_language_navigation(self):
        families = list(self.families())
        self.assertEqual(len(families), 12)
        for family in families:
            for language, path in family.items():
                with self.subTest(path=path.relative_to(ROOT)):
                    self.assertTrue(path.is_file())
                    text = path.read_text(encoding="utf-8")
                    lines = text.splitlines()
                    marker = "<!-- language-navigation -->"
                    self.assertEqual(lines.count(marker), 1,
                                     "Keep the HTML marker on its own line")
                    marker_index = lines.index(marker)
                    self.assertEqual(lines[marker_index + 1], "",
                                     "Blank line prevents GitHub treating navigation as raw HTML")
                    navigation = lines[marker_index + 2]
                    self.assertEqual(lines[marker_index + 3], "",
                                     "Keep language links separate from the document introduction")
                    self.assertEqual(len(re.findall(r"\[[^\]]+\]\([^)]+\)", navigation)), 7)
                    self.assertEqual(len(re.findall(r"\*\*[^*]+\*\*", navigation)), 1)
                    for target in family.values():
                        if target != path:
                            self.assertIn(f"({target.name})", navigation)
                    self.assertGreater(len(text.splitlines()), 20)

    def test_pull_request_language_navigation_is_a_separate_markdown_paragraph(self):
        for language in self.LANGUAGES:
            path = ROOT / ".github/PULL_REQUEST_TEMPLATE" / f"{language}.md"
            text = path.read_text(encoding="utf-8")
            marker = "<!-- language-navigation -->"
            self.assertEqual(text.count(marker), 1)
            self.assertIn(marker + "\n\n", text)
            navigation = text.split(marker + "\n\n", 1)[1].split("\n\n", 1)[0]
            self.assertNotIn("\n", navigation)
            self.assertEqual(len(re.findall(r"\[[^\]]+\]\([^)]+\)", navigation)), 7)
            self.assertEqual(len(re.findall(r"\*\*[^*]+\*\*", navigation)), 1)

    def test_public_document_relative_links_resolve(self):
        for family in self.families():
            for path in family.values():
                for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                    if "://" not in link and not link.startswith("#"):
                        self.assertTrue((path.parent / link.split("#", 1)[0]).is_file(),
                                        f"{path.relative_to(ROOT)} -> {link}")

    def test_translated_payment_identifiers_and_license_sections(self):
        addresses = ("0xE35023A45F4d7c8e070D335Db6Cc4C5c9a3Fe4Bd",
                     "0x55d398326f99059ff775485246999027b3197955",
                     "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d")
        for language in self.LANGUAGES:
            suffix = "" if language == "en" else "." + language
            terms = (ROOT / f"docs/COMMERCIAL_TERMS{suffix}.md").read_text(encoding="utf-8")
            for address in addresses:
                self.assertIn(address, terms)
            license_path = ROOT / ("LICENSE" if language == "en" else f"LICENSE.{language}.md")
            license_text = license_path.read_text(encoding="utf-8")
            self.assertRegex(license_text, r"0[.,]5\s*%")
            self.assertRegex(license_text, r"0[.,]005")
            self.assertIn("2026-10-01", license_text)
            self.assertIn("teateatea03", license_text)
            self.assertEqual(len(re.findall(r"^(?:## )?[1-6][.、]", license_text, re.M)), 6)


class NoticeRetentionTests(unittest.TestCase):
    """All legal text here is synthetic test data, never an operative license."""

    def setUp(self):
        self.builder = load("build_novel_os_bundle")
        self.installer = load("install_novel_os")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "source"
        for name in self.builder.PACKAGE_SKILLS:
            path = self.source / "skills" / name / "SKILL.md"
            path.parent.mkdir(parents=True)
            path.write_text("---\nversion: 0.0.0\n---\nSynthetic skill fixture.\n", encoding="utf-8")
        runtime = self.source / "skills/immersive-interactive-fiction/scripts/novel_judge/runtime_versioning.py"
        runtime.parent.mkdir(parents=True)
        runtime.write_text('RUNTIME_BUILD = "novel-judge/0.0.0"\n', encoding="utf-8")
        self.upstream = self.builder.REQUIRED_SKILL_NOTICES[0]
        self.notices = {
            rel: f"SYNTHETIC TEST NOTICE ONLY: {rel}\n".encode()
            for rel in (*self.builder.REQUIRED_ROOT_NOTICES, "NOTICE.txt",
                        "docs/COMMERCIAL_LICENSE.md", self.upstream)
        }
        for rel, content in self.notices.items():
            path = self.source / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        (self.source / "docs/COMMERCIAL_LICENSE_DISCUSSION.zh-TW.md").write_text(
            "Synthetic non-operative discussion draft; do not distribute as terms.\n", encoding="utf-8")
        self.payload = self.base / "bundle/payload"
        self.target = self.base / "host"
        self.refresh()

    def quiet(self, func, *args, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return func(*args, **kwargs)

    def refresh(self):
        self.quiet(self.builder.refresh, types.SimpleNamespace(
            source_root=str(self.source / "skills"), bundle_root=str(self.payload.parent)))

    def install(self, upgrade=False):
        self.quiet(self.installer.install, types.SimpleNamespace(
            bundle_root=str(self.payload), target=str(self.target), upgrade=upgrade, smoke_test=False))

    def read_manifest(self):
        return json.loads((self.payload / "MANIFEST.json").read_text(encoding="utf-8"))

    def write_manifest(self, manifest):
        (self.payload / "MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")

    def test_source_payload_zip_and_install_retain_exact_notice_bytes(self):
        self.assertEqual(self.builder.verify_root(self.payload), [])
        manifest = self.read_manifest()
        self.assertEqual(set(manifest["distribution_notices"]), set(self.notices))
        self.assertFalse((self.payload / "docs/COMMERCIAL_LICENSE_DISCUSSION.zh-TW.md").exists())
        archive = self.base / "bundle.zip"
        result = self.quiet(self.builder.build, types.SimpleNamespace(
            bundle_root=str(self.payload), output=str(archive), refresh=False))
        self.assertEqual(result, 0)
        with zipfile.ZipFile(archive) as zipped:
            for rel, content in self.notices.items():
                self.assertEqual((self.source / rel).read_bytes(), content)
                self.assertEqual((self.payload / rel).read_bytes(), content)
                self.assertEqual(zipped.read(f"novel-os-portable-v{self.builder.VERSION}/{rel}"), content)
        self.install()
        for rel, content in self.notices.items():
            self.assertEqual((self.target / self.installer.installed_notice_path(rel)).read_bytes(), content)
            self.assertEqual((self.target / self.installer.NOTICE_DIR / rel).read_bytes(), content)
        self.assertEqual(self.installer.verify_installed_notices(self.target), [])

    def test_missing_required_source_notice_fails_before_payload_changes(self):
        original = (self.payload / "MANIFEST.json").read_bytes()
        for rel in (*self.builder.REQUIRED_ROOT_NOTICES, *self.builder.REQUIRED_SKILL_NOTICES):
            with self.subTest(rel=rel):
                (self.source / rel).unlink()
                with self.assertRaisesRegex(SystemExit, "missing or unsafe distribution notice"):
                    self.refresh()
                self.assertEqual((self.payload / "MANIFEST.json").read_bytes(), original)
                (self.source / rel).write_bytes(self.notices[rel])

    def test_required_notices_cannot_be_silently_removed_from_manifest(self):
        for rel in (*self.builder.REQUIRED_ROOT_NOTICES, *self.builder.REQUIRED_SKILL_NOTICES):
            with self.subTest(rel=rel):
                (self.payload / rel).unlink()
                manifest = self.read_manifest()
                manifest["files"] = [entry for entry in manifest["files"] if entry["path"] != rel]
                manifest["distribution_notices"].remove(rel)
                self.write_manifest(manifest)
                self.assertTrue(self.builder.verify_root(self.payload))
                with self.assertRaisesRegex(SystemExit, "Bundle integrity check failed"):
                    self.install()
                self.assertFalse(self.target.exists())
                self.refresh()

    def test_upstream_notice_inventory_rejects_removed_file_and_hash_entry(self):
        (self.payload / self.upstream).unlink()
        manifest = self.read_manifest()
        manifest["files"] = [entry for entry in manifest["files"] if entry["path"] != self.upstream]
        self.write_manifest(manifest)
        self.assertIn(f"distribution notice not hashed: {self.upstream}", self.builder.verify_root(self.payload))
        with self.assertRaises(SystemExit): self.install()

    def test_tampered_notice_is_rejected_before_install(self):
        (self.payload / "LICENSE").write_text("Modified synthetic fixture", encoding="utf-8")
        self.assertIn("hash mismatch: LICENSE", self.builder.verify_root(self.payload))
        with self.assertRaises(SystemExit): self.install()

    def test_build_refresh_from_a_new_directory_keeps_notice_contract(self):
        root = self.base / "new-bundle"
        archive = self.base / "new-bundle.zip"
        result = self.quiet(self.builder.build, types.SimpleNamespace(
            bundle_root=str(root), source_root=str(self.source / "skills"), output=str(archive), refresh=True))
        self.assertEqual(result, 0)
        self.assertEqual(self.builder.verify_root(root / "payload"), [])
        with zipfile.ZipFile(archive) as zipped:
            self.assertEqual(zipped.read(f"novel-os-portable-v{self.builder.VERSION}/LICENSE"), self.notices["LICENSE"])

    def test_refresh_removes_stale_optional_notices(self):
        (self.source / "NOTICE.txt").unlink()
        self.refresh()
        self.assertFalse((self.payload / "NOTICE.txt").exists())
        self.assertNotIn("NOTICE.txt", self.read_manifest()["distribution_notices"])
        self.assertEqual(self.builder.verify_root(self.payload), [])

    def test_leftover_discussion_draft_cannot_enter_a_new_manifest(self):
        rel = "docs/COMMERCIAL_LICENSE_DISCUSSION.zh-TW.md"
        (self.payload / rel).write_text("Synthetic leftover discussion draft", encoding="utf-8")
        with self.assertRaisesRegex(SystemExit, "Unexpected existing payload file"):
            self.refresh()
        self.assertIn(f"unapproved payload path: {rel}", self.builder.verify_root(self.payload))
        with self.assertRaises(SystemExit): self.install()

    def test_source_symlink_and_payload_notice_symlink_are_rejected(self):
        external = self.base / "external.txt"
        external.write_bytes(self.notices["LICENSE"])
        source = self.source / "LICENSE"
        source.unlink(); source.symlink_to(external)
        with self.assertRaisesRegex(SystemExit, "missing or unsafe distribution notice"):
            self.refresh()
        source.unlink(); source.write_bytes(self.notices["LICENSE"])
        notice = self.payload / "LICENSE"
        notice.unlink(); notice.symlink_to(external)
        with self.assertRaises(SystemExit): self.install()
        self.assertTrue(self.builder.verify_root(self.payload))

    def test_source_skill_links_cannot_copy_external_data(self):
        external = self.base / "external"
        external.mkdir()
        (external / "private.txt").write_text("Synthetic outside-tree marker", encoding="utf-8")
        original = (self.payload / "MANIFEST.json").read_bytes()
        link = self.source / "skills/novel-human-voice-editor/outside-link"
        for destination in (external / "private.txt", external):
            with self.subTest(directory=destination.is_dir()):
                link.symlink_to(destination, target_is_directory=destination.is_dir())
                with self.assertRaisesRegex(SystemExit, "Source symlink is not distributable"):
                    self.refresh()
                self.assertFalse((self.payload / "skills/novel-human-voice-editor/outside-link").exists())
                self.assertEqual((self.payload / "MANIFEST.json").read_bytes(), original)
                link.unlink()
        alias = self.base / "linked-skills"
        alias.symlink_to(self.source / "skills", target_is_directory=True)
        with self.assertRaisesRegex(SystemExit, "Source skills root must not use symlinks"):
            self.quiet(self.builder.refresh, types.SimpleNamespace(source_root=str(alias), bundle_root=str(self.base / "new-output")))
        self.assertFalse((self.base / "new-output").exists())

    def test_manifest_notice_and_file_paths_must_be_safe(self):
        for rel in ("../LICENSE", "/LICENSE", "docs/../LICENSE", "docs\\LICENSE"):
            with self.subTest(rel=rel):
                manifest = self.read_manifest()
                manifest["distribution_notices"].append(rel)
                self.write_manifest(manifest)
                with self.assertRaises(SystemExit): self.install()
                self.refresh()
                manifest = self.read_manifest()
                manifest["files"][0]["path"] = rel
                self.write_manifest(manifest)
                with self.assertRaises(SystemExit): self.install()
                self.refresh()

    def test_missing_notice_inventory_is_rejected(self):
        manifest = self.read_manifest(); del manifest["distribution_notices"]
        self.write_manifest(manifest)
        self.assertIn("missing or invalid distribution notice inventory", self.builder.verify_root(self.payload))
        with self.assertRaises(SystemExit): self.install()

    def test_installed_link_copy_is_required_and_hash_verified(self):
        self.install()
        copy = self.target / self.installer.NOTICE_DIR / self.upstream
        copy.write_bytes(b"Changed synthetic fixture")
        self.assertIn(f"modified notice document copy: {self.upstream}",
                      self.installer.verify_installed_notices(self.target))
        copy.unlink()
        self.assertIn(f"missing or unsafe notice document copy: {self.upstream}",
                      self.installer.verify_installed_notices(self.target))

    def test_upgrade_preserves_old_notices_and_unrelated_host_files(self):
        self.target.mkdir()
        host_files = {"LICENSE": b"Host license", "THIRD_PARTY.md": b"Host notice",
                      "docs/COMMERCIAL_TERMS.md": b"Host terms", "other-skill/keep.txt": b"Host skill"}
        for rel, content in host_files.items():
            path = self.target / rel
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(content)
        self.install()
        old = self.notices["LICENSE"]
        new = b"SYNTHETIC TEST NOTICE ONLY: revised placeholder license\n"
        (self.source / "LICENSE").write_bytes(new); self.refresh()
        self.install(upgrade=True)
        info = json.loads((self.target / "novel-operating-system/INSTALLATION.json").read_text(encoding="utf-8"))
        installed = self.installer.installed_notice_path("LICENSE")
        self.assertEqual((self.target / installed).read_bytes(), new)
        self.assertEqual((Path(info["backup"]) / installed).read_bytes(), old)
        for rel, content in host_files.items(): self.assertEqual((self.target / rel).read_bytes(), content)
        self.assertEqual(self.installer.verify_installed_notices(self.target), [])
        (self.target / installed).write_bytes(b"Changed synthetic fixture")
        self.assertIn("modified installed notice: LICENSE", self.installer.verify_installed_notices(self.target))

    def test_failed_upgrade_restores_previous_notice_and_skill_trees(self):
        self.install()
        original = (self.target / "novel-operating-system/INSTALLATION.json").read_bytes()
        real_replace = os.replace
        calls = []
        def fail_after_first(src, dst):
            calls.append(str(src))
            if len(calls) == 2: raise OSError("Synthetic publication failure")
            return real_replace(src, dst)
        with mock.patch.object(self.installer.os, "replace", side_effect=fail_after_first):
            with self.assertRaisesRegex(OSError, "Synthetic publication failure"):
                self.install(upgrade=True)
        self.assertEqual((self.target / "novel-operating-system/INSTALLATION.json").read_bytes(), original)
        self.assertEqual(self.installer.verify_installed_notices(self.target), [])
        for skill in self.installer.CORE: self.assertTrue((self.target / skill / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
