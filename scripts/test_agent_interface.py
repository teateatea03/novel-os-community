"""Synthetic contract/integration tests for framework-neutral transport and isolation."""
from __future__ import annotations
import asyncio
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/novel-operating-system/scripts"
sys.path.insert(0, str(SCRIPTS))
from novel_os import NovelOS
from novel_os.mcp_server import mcp_sdk_supported

class AgentInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "private-projects"
        self.api = NovelOS(self.root, allow_writes=True)

    def call(self, tool, **args):
        return self.api.call("novel_os_" + tool, args)

    def init(self):
        result = self.call("init_project", project_id="synthetic-demo", title="Synthetic 測試")
        self.assertTrue(result["ok"], result)
        return self.root / "synthetic-demo"

    def test_catalog_and_provider_schemas_share_names_and_parameters(self):
        mcp, openai, anthropic = (self.api.tools(x) for x in ("mcp", "openai", "anthropic"))
        self.assertEqual(len(mcp), 10)
        self.assertEqual(len(self.call("list_skills")["data"]["skills"]), 17)
        for a, b, c in zip(mcp, openai, anthropic):
            self.assertEqual(a["name"], b["function"]["name"])
            self.assertEqual(a["name"], c["name"])
            self.assertEqual(a["inputSchema"], b["function"]["parameters"])
            self.assertEqual(a["inputSchema"], c["input_schema"])
        openai[0]["function"]["name"] = "changed"
        self.assertEqual(self.api.tools()[0]["name"], "novel_os_status")

    def test_read_only_default_and_unknown_arguments(self):
        api = NovelOS(self.root)
        for tool in ("init_project", "build_context", "resume_project"):
            args = {"project_id": "synthetic"}
            if tool == "init_project": args["title"] = "Synthetic"
            if tool == "build_context": args["chapter"] = "ch01"
            self.assertEqual(api.call("novel_os_" + tool, args)["error"]["code"], "write_disabled")
        self.assertFalse(self.root.exists())
        for args in ({"root": "/outside"}, [], {"allow_writes": True}):
            self.assertFalse(api.call("novel_os_status", args)["ok"])
        self.assertFalse(api.call("arbitrary_command", {})["ok"])

    def test_resource_paging_and_path_rejections(self):
        first = self.call("read_skill", skill="novel-operating-system", limit=10)
        self.assertTrue(first["ok"], first)
        self.assertEqual(first["data"]["next_offset"], 10)
        second = self.call("read_skill", skill="novel-operating-system", offset=10, limit=20)
        self.assertEqual(first["data"]["sha256"], second["data"]["sha256"])
        self.assertTrue(self.call("read_skill", skill="novel-operating-system", resource="references/agent-evaluation.xml")["ok"])
        for resource in ("../LICENSE", "/etc/passwd", "C:/outside", "references/../../x", ".env", "CON.txt", "SKILL.md:stream"):
            self.assertFalse(self.call("read_skill", skill="novel-operating-system", resource=resource)["ok"], resource)
        self.assertFalse(self.call("read_skill", skill="novel-operating-system", limit=True)["ok"])
        self.assertFalse(self.call("read_skill", skill="novel-operating-system", limit=0)["ok"])

    def test_project_root_is_separate_and_ids_cannot_traverse(self):
        for root in (ROOT / "private", ROOT / "skills/data", ROOT.parent):
            with self.assertRaises(ValueError):
                NovelOS(root)
        for ident in ("../outside", "UPPER", "demo/branch", "C:", "con", "x."):
            self.assertFalse(self.call("init_project", project_id=ident, title="Synthetic")["ok"])

    def test_end_to_end_init_validate_resume_context_and_prose(self):
        project = self.init()
        original = (project / "project.json").read_bytes()
        self.assertFalse(self.call("init_project", project_id="synthetic-demo", title="Replacement")["ok"])
        self.assertEqual((project / "project.json").read_bytes(), original)
        for tool in ("validate_graph", "resume_project"):
            result = self.call(tool, project_id="synthetic-demo")
            self.assertTrue(result["ok"], result)
        result = self.call("build_context", project_id="synthetic-demo", chapter="ch01", query="世界規則")
        self.assertTrue(result["ok"], result)
        read = self.call("read_project", project_id="synthetic-demo", resource="context-packs/ch01.json")
        self.assertTrue(read["ok"], read)
        result = self.call("inspect_prose", project_id="synthetic-demo", resource="story-bible.md")
        self.assertTrue(result["ok"], result)

    def test_gate_failure_keeps_exit_code_and_canon_unchanged(self):
        project = self.init()
        (project / "state.json").write_text(json.dumps({"events": [{"id": "synthetic"}],
            "world": {"now": "synthetic", "environment": {"temperature": "cold"}}}), encoding="utf-8")
        (project / "draft.md").write_text("She was comfortably warm.", encoding="utf-8")
        before = {p.relative_to(project).as_posix(): p.read_bytes() for p in project.rglob("*") if p.is_file()}
        result = self.call("reality_gate", project_id="synthetic-demo", state_file="state.json", text_file="draft.md")
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["data"]["exit_code"], 2)
        self.assertFalse(result["data"]["result"]["ok"])
        after = {p.relative_to(project).as_posix(): p.read_bytes() for p in project.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_reality_gate_rejects_empty_state_and_empty_draft(self):
        project = self.init()
        state, draft = project / "state.json", project / "draft.md"
        valid = {"world": {"now": "synthetic-day"}, "events": [{"id": "synthetic-1"}]}
        for data, prose in (({}, "Synthetic prose."), (valid, ""), (valid, " \t\n\u3000")):
            state.write_text(json.dumps(data), encoding="utf-8")
            draft.write_text(prose, encoding="utf-8")
            before = {p.relative_to(project).as_posix(): p.read_bytes() for p in project.rglob("*") if p.is_file()}
            result = self.call("reality_gate", project_id="synthetic-demo", state_file="state.json", text_file="draft.md")
            self.assertFalse(result["ok"], result)
            self.assertEqual(result["data"]["exit_code"], 2)
            inner = result["data"]["result"]
            self.assertEqual(inner["status"], "invalid_input")
            self.assertEqual(inner["evaluation"], "not_evaluated")
            self.assertIsNone(inner.get("card"))
            after = {p.relative_to(project).as_posix(): p.read_bytes() for p in project.rglob("*") if p.is_file()}
            self.assertEqual(before, after)

    def test_corrupt_graph_is_failed_not_passing(self):
        project = self.init()
        (project / "graphify-out/graph.json").write_text("not JSON", encoding="utf-8")
        result = self.call("validate_graph", project_id="synthetic-demo")
        self.assertFalse(result["ok"], result)
        self.assertNotEqual(result["data"]["exit_code"], 0)

    def test_bundle_install_retains_the_executable_interface(self):
        import contextlib
        import io
        import types
        exporter = ROOT / "skills/novel-system-exporter/scripts"
        def load(name):
            spec = importlib.util.spec_from_file_location(name, exporter / (name + ".py"))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        builder, installer = load("build_novel_os_bundle"), load("install_novel_os")
        bundle = Path(self.temp.name) / "bundle"
        installed = Path(self.temp.name) / "installed"
        with contextlib.redirect_stdout(io.StringIO()):
            builder.refresh(types.SimpleNamespace(source_root=str(ROOT / "skills"), bundle_root=str(bundle)))
            self.assertEqual(builder.verify_root(bundle / "payload"), [])
            installer.install(types.SimpleNamespace(bundle_root=str(bundle / "payload"), target=str(installed),
                                                    upgrade=False, smoke_test=False))
        launcher = installed / "novel-operating-system/scripts/novel_os_cli.py"
        result = subprocess.run([sys.executable, str(launcher), "--projects-root", str(self.root),
                                 "--allow-writes", "call", "novel_os_init_project"],
                                input=json.dumps({"project_id": "installed-demo", "title": "Synthetic installed demo"}),
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue(json.loads(result.stdout)["ok"])
        self.assertTrue((self.root / "installed-demo/project.json").is_file())
        self.assertEqual(installer.verify_installed_notices(installed), [])

    def test_metadata_paths_fail_closed(self):
        project = self.init()
        meta = json.loads((project / "project.json").read_text(encoding="utf-8"))
        meta["production_authority"]["session_id"] = "../outside"
        (project / "project.json").write_text(json.dumps(meta), encoding="utf-8")
        self.assertFalse(self.call("resume_project", project_id="synthetic-demo")["ok"])

    def test_json_cli_stdin_and_error_exit(self):
        command = [sys.executable, str(SCRIPTS / "novel_os_cli.py"), "--projects-root", str(self.root)]
        result = subprocess.run(command + ["call", "novel_os_status"], input="{}", text=True,
                                encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])
        self.assertEqual(result.stderr, "")
        for text in ("[]", "{bad", '{"extra":NaN}'):
            result = subprocess.run(command + ["call", "novel_os_status"], input=text, text=True,
                                    encoding="utf-8", capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(json.loads(result.stdout)["ok"])

    @unittest.skipUnless(mcp_sdk_supported(), "MCP stdio test requires supported SDK >=1.26,<2")
    def test_real_mcp_stdio_round_trip(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        project = self.init()
        (project / "empty-state.json").write_text("{}", encoding="utf-8")
        (project / "draft.md").write_text("Synthetic prose.", encoding="utf-8")
        async def run():
            params = StdioServerParameters(command=sys.executable, args=[
                str(SCRIPTS / "novel_os_cli.py"), "--projects-root", str(self.root), "mcp"])
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    listed = await session.list_tools()
                    self.assertEqual(len(listed.tools), 10)
                    result = await session.call_tool("novel_os_status", {})
                    self.assertFalse(result.isError)
                    self.assertEqual(result.structuredContent["data"]["api"], "novel-os-agent.v1")
                    blocked = await session.call_tool("novel_os_init_project", {"project_id": "synthetic", "title": "Synthetic"})
                    self.assertTrue(blocked.isError)
                    self.assertFalse(blocked.structuredContent["ok"])
                    resource = await session.call_tool("novel_os_read_skill", {"skill": "novel-operating-system", "limit": 20})
                    self.assertFalse(resource.isError)
                    gate = await session.call_tool("novel_os_reality_gate", {"project_id": "synthetic-demo",
                        "state_file": "empty-state.json", "text_file": "draft.md"})
                    self.assertTrue(gate.isError)
                    self.assertFalse(gate.structuredContent["ok"])
                    self.assertEqual(gate.structuredContent["data"]["result"]["evaluation"], "not_evaluated")
                    self.assertIsNone(gate.structuredContent["data"]["result"]["card"])
        asyncio.run(run())

class MCPSDKPreflightTests(unittest.TestCase):
    def test_supported_sdk_boundaries(self):
        from unittest.mock import patch
        from novel_os.mcp_server import require_mcp_sdk
        for version in ("1.26.0", "1.30.0", "1.26.0.post1", "1.26.0+local"):
            with self.subTest(version=version), patch("novel_os.mcp_server.version", return_value=version):
                self.assertEqual(require_mcp_sdk(), version)
                self.assertTrue(mcp_sdk_supported())

    def test_unsupported_and_missing_sdk(self):
        from importlib.metadata import PackageNotFoundError
        from unittest.mock import patch
        from novel_os.mcp_server import require_mcp_sdk
        for version in ("1.25.9", "2.3.0", "3.0.0", "1.26.0rc1", "invalid"):
            with self.subTest(version=version), patch("novel_os.mcp_server.version", return_value=version):
                self.assertFalse(mcp_sdk_supported())
                with self.assertRaisesRegex(ImportError, "Unsupported MCP SDK"):
                    require_mcp_sdk()
        with patch("novel_os.mcp_server.version", side_effect=PackageNotFoundError("mcp")):
            self.assertFalse(mcp_sdk_supported())

    def test_unsupported_mcp_startup_keeps_stdout_protocol_clean(self):
        import contextlib
        import io
        from unittest.mock import patch
        from novel_os.cli import main
        with tempfile.TemporaryDirectory() as tmp:
            out, err = io.StringIO(), io.StringIO()
            with patch("novel_os.mcp_server.version", return_value="2.3.0"):
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    code = main(["--projects-root", str(Path(tmp) / "projects"), "mcp"])
            self.assertEqual(code, 2)
            self.assertEqual(out.getvalue(), "")
            result = json.loads(err.getvalue())
            self.assertFalse(result["ok"])
            self.assertIn("Unsupported MCP SDK 2.3.0", result["error"]["message"])
            self.assertIn("separate interpreter", result["error"]["message"])


if __name__ == "__main__":
    unittest.main()
