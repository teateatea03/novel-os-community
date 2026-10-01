#!/usr/bin/env python3
"""Keep generated fiction outside a source checkout by default."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SKILLS = Path(__file__).resolve().parents[2]
INITIALIZERS = (
    SKILLS / "long-form-novel-writer/scripts/init_novel_project.py",
    SKILLS / "unfinished-novel-completion/scripts/init_completion_project.py",
)


class ProjectRootTests(unittest.TestCase):
    def check_root(self, script, mode):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            home = base / "home"
            home.mkdir()
            cwd = base / "checkout"
            cwd.mkdir()
            env = os.environ.copy()
            env["HOME"] = str(home)
            env.pop("NOVEL_PROJECTS_ROOT", None)
            env.pop("PYTHONPATH", None)
            command = [sys.executable, str(script), "--title", "Synthetic Demo", "--slug", "synthetic-demo"]
            expected = home / ".novel-os/novels"
            if mode in {"environment", "explicit"}:
                env["NOVEL_PROJECTS_ROOT"] = str(base / "configured-projects")
                expected = base / "configured-projects"
            if mode == "explicit":
                expected = base / "explicit-projects"
                command.extend(["--root", str(expected)])
            result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            project = expected / "synthetic-demo"
            self.assertEqual(Path(json.loads(result.stdout)["project"]), project)
            self.assertTrue((project / "project.json").is_file())
            self.assertEqual(list(cwd.iterdir()), [])
            marker = project / "preserved.txt"
            marker.write_text("synthetic sentinel", encoding="utf-8")
            repeated = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertEqual(marker.read_text(encoding="utf-8"), "synthetic sentinel")

    def test_home_default(self):
        for script in INITIALIZERS:
            with self.subTest(initializer=script.parent.parent.name):
                self.check_root(script, "default")

    def test_environment_override(self):
        for script in INITIALIZERS:
            with self.subTest(initializer=script.parent.parent.name):
                self.check_root(script, "environment")

    def test_explicit_root_wins(self):
        for script in INITIALIZERS:
            with self.subTest(initializer=script.parent.parent.name):
                self.check_root(script, "explicit")


if __name__ == "__main__":
    unittest.main()
