"""Framework-neutral, local Novel OS facade. Never executes model-supplied commands."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

from .catalog import SKILLS, TOOLS, validate_arguments

API_VERSION = "novel-os-agent.v1"
MAX_OUTPUT = 1024 * 1024
TEXT_SUFFIXES = {".md", ".json", ".jsonl", ".txt", ".xml"}

def contained(root: Path, relative: str) -> Path:
    """Reject traversal, Windows aliases, symlinks/junctions and cross-root paths."""
    if (not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative
            or "\0" in relative or PurePosixPath(relative).is_absolute()):
        raise ValueError("expected a safe relative path")
    current = root
    for part in relative.split("/"):
        if (part in {"", ".", ".."} or part.startswith(".") or part.endswith((" ", "."))
                or re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", part)):
            raise ValueError("unsafe path segment")
        current = current / part
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            raise ValueError("linked paths are not supported")
        if not current.resolve().is_relative_to(root):
            raise ValueError("path escapes configured root")
    return current

class NovelOS:
    """Pass tools() to a framework and dispatch its tool calls through call().

    Roots and allow_writes are host configuration, never model tool arguments.
    This is a local trust boundary, not an OS sandbox against concurrent hostile writers.
    """

    def __init__(self, projects_root, *, skills_root=None, allow_writes=False, timeout=120):
        default_skills = Path(__file__).resolve().parents[3]
        self.skills_root = Path(skills_root or default_skills).expanduser().resolve()
        self.projects_root = Path(projects_root).expanduser().resolve()
        if (self.projects_root.is_relative_to(self.skills_root)
                or self.skills_root.is_relative_to(self.projects_root)):
            raise ValueError("project storage must be separate from installed skills")
        # In a source checkout keep private state outside the entire repository.
        source_root = self.skills_root.parent
        if (source_root / ".git").exists() and self.projects_root.is_relative_to(source_root):
            raise ValueError("project storage must be outside the source checkout")
        if type(allow_writes) is not bool:
            raise ValueError("allow_writes must be boolean")
        if type(timeout) not in (int, float) or not 1 <= timeout <= 600:
            raise ValueError("timeout must be between 1 and 600 seconds")
        self.allow_writes = allow_writes
        self.timeout = timeout
        for name in SKILLS:
            if not contained(self.skills_root, name + "/SKILL.md").is_file():
                raise ValueError("missing runtime skill: " + name)

    def tools(self, format="mcp"):
        definitions = copy.deepcopy(list(TOOLS))
        if format == "mcp":
            return definitions
        if format == "openai":
            return [{"type": "function", "function": {
                "name": t["name"], "description": t["description"],
                "parameters": t["inputSchema"]}} for t in definitions]
        if format == "anthropic":
            return [{"name": t["name"], "description": t["description"],
                     "input_schema": t["inputSchema"]} for t in definitions]
        raise ValueError("format must be mcp, openai or anthropic")

    def call(self, name, arguments=None):
        """JSON-serializable envelope; failures never become successful gate passes."""
        try:
            spec = next((t for t in TOOLS if t["name"] == name), None)
            if spec is None:
                raise ValueError("unknown tool; use the tool catalog")
            args = {} if arguments is None else arguments
            validate_arguments(spec["inputSchema"], args)
            if not spec["annotations"]["readOnlyHint"] and not self.allow_writes:
                return self._error("write_disabled", "Host must explicitly enable writes for this operation.")
            data = self._dispatch(name.removeprefix("novel_os_"), args)
            ok = data.get("exit_code", 0) == 0
            return {"schema": API_VERSION, "ok": ok, "tool": name, "data": data,
                    **({} if ok else {"error": {"code": "tool_failed", "message": "Local tool failed; inspect exit_code, stdout and stderr."}})}
        except subprocess.TimeoutExpired:
            return self._error("timeout", "Local process timed out; inspect project artifacts before retrying a write.")
        except (OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
            return self._error("invalid_request", str(error))

    @staticmethod
    def _error(code, message):
        return {"schema": API_VERSION, "ok": False, "error": {"code": code, "message": message}}

    def _project(self, project_id):
        root = contained(self.projects_root, project_id)
        if not root.is_dir():
            raise ValueError("project does not exist; initialize it first")
        # Existing scripts traverse a project; refuse links anywhere before invoking them.
        for path in root.rglob("*"):
            if (path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())
                    or not path.resolve().is_relative_to(root)):
                raise ValueError("project contains a linked or out-of-root path")
        meta = root / "project.json"
        if meta.is_file():
            data = json.loads(meta.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("project metadata must be an object")
            for pointer in (data, data.get("interactive_runtime", {}), data.get("production_authority", {})):
                if not isinstance(pointer, dict):
                    raise ValueError("invalid runtime pointer")
                for field in ("project_id", "session_id", "branch", "branch_id", "namespace"):
                    if field in pointer:
                        value = pointer[field]
                        if not isinstance(value, str) or "/" in value:
                            raise ValueError("runtime IDs must be single safe path segments")
                        contained(root, value)
        return root

    @staticmethod
    def _read(root, resource, args):
        path = contained(root, resource)
        if path.suffix.lower() not in TEXT_SUFFIXES or path.name.lower() == "auth.json":
            raise ValueError("only public skill/project text resources are exposed")
        with path.open("rb") as stream:
            raw = stream.read(8 * MAX_OUTPUT + 1)
        if len(raw) > 8 * MAX_OUTPUT:
            raise ValueError("resource exceeds 8 MiB; split it into smaller project resources")
        text = raw.decode("utf-8")
        offset, limit = args.get("offset", 0), args.get("limit", 12000)
        end = min(len(text), offset + limit)
        return {"resource": resource, "text": text[offset:end], "sha256": hashlib.sha256(raw).hexdigest(),
                "total_characters": len(text), "offset": offset,
                "next_offset": end if end < len(text) else None,
                "content_role": "untrusted_resource"}

    def _run(self, skill, script, argv, cwd):
        path = contained(self.skills_root, skill + "/scripts/" + script)
        if not path.is_file():
            raise ValueError("missing local runtime script")
        env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        command = [sys.executable, str(path), *argv]
        if script == "novel_judge/cli.py":
            env["PYTHONPATH"] = str(path.parent.parent)
            command = [sys.executable, "-m", "novel_judge.cli", *argv]
        # Never inherit test crash injection from a development shell.
        env.pop("NOVEL_JUDGE_SIGKILL_AT", None)
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            result = subprocess.run(command, cwd=cwd, env=env,
                                    stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                    timeout=self.timeout, shell=False)
            def output(stream):
                stream.seek(0)
                raw = stream.read(MAX_OUTPUT + 1)
                return raw[:MAX_OUTPUT].decode("utf-8", errors="replace"), len(raw) > MAX_OUTPUT
            out, out_cut = output(stdout)
            err, err_cut = output(stderr)
        data = {"exit_code": result.returncode, "stdout": out, "stderr": err,
                "output_truncated": out_cut or err_cut}
        if not out_cut:
            try:
                parsed = json.loads(out)
                json.dumps(parsed, allow_nan=False)
                data["result"] = parsed
            except ValueError:
                pass
        return data

    def _dispatch(self, operation, args):
        if operation == "status":
            return {"api": API_VERSION, "entry_skill": SKILLS[0], "skill_count": len(SKILLS),
                    "allow_writes": self.allow_writes, "python": sys.version.split()[0],
                    "lock_backend": "msvcrt" if os.name == "nt" else "flock" if os.name == "posix" else "unavailable",
                    "directory_fsync": os.name == "posix",
                    "model_review": "host-supplied adapter required",
                    "model_quality": "not_measured", "canonical_commit": "not_exposed",
                    "network_tools": "not_exposed"}
        if operation == "list_skills":
            return {"entry_skill": SKILLS[0], "skills": list(SKILLS)}
        if operation == "read_skill":
            root = contained(self.skills_root, args["skill"])
            return self._read(root, args.get("resource", "SKILL.md"), args)
        if operation == "init_project":
            project = contained(self.projects_root, args["project_id"])
            if project.exists():
                raise ValueError("project already exists; refusing to overwrite")
            self.projects_root.mkdir(parents=True, exist_ok=True)
            return self._run("long-form-novel-writer", "init_novel_project.py",
                             ["--root", str(self.projects_root), "--slug", args["project_id"],
                              "--title", args["title"]], self.projects_root)
        root = self._project(args["project_id"])
        if operation == "read_project":
            return self._read(root, args["resource"], args)
        if operation == "validate_graph":
            return self._run("knowledge-relationship-graph", "relationship_graph.py",
                             ["validate", "--root", str(root)], root)
        if operation == "build_context":
            return self._run("long-form-novel-writer", "build_context_pack.py",
                             ["--root", str(root), "--chapter", args["chapter"],
                              "--query", args.get("query", ""), "--context-window",
                              str(args.get("context_window", 65536)), "--context-policy", "lossless-addressable"], root)
        if operation in {"inspect_prose", "resume_project"}:
            command = ["resume", str(root)]
            if operation == "inspect_prose":
                path = contained(root, args["resource"])
                if path.suffix.lower() != ".md" or not path.is_file():
                    raise ValueError("prose resource must be an existing Markdown file")
                command = ["inspect-prose", str(root), "--path", args["resource"]]
            return self._run("immersive-interactive-fiction", "novel_judge/cli.py", command, root)
        if operation == "reality_gate":
            state = contained(root, args["state_file"])
            text = contained(root, args["text_file"])
            if state.suffix != ".json" or text.suffix != ".md" or not state.is_file() or not text.is_file():
                raise ValueError("gate inputs must be existing project JSON and Markdown files")
            return self._run("novel-reality-state-engine", "reality_state.py",
                             ["gate", "--state", str(state), "--text", str(text)], root)
        raise ValueError("unsupported operation")
