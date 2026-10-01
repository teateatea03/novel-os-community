#!/usr/bin/env python3
"""Check source/bundle version, skill inventory, and retained notices offline."""
from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import os
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
