# 通用代理接入 / Universal agent integration

Novel OS exposes a framework-neutral local API, `novel-os-agent.v1`. It keeps the
17 sibling skills and the deterministic story runtime. No model, provider account,
API credential, private story, or global agent configuration is installed.

## Choose the interface

| Host capability | Interface | Dependency |
| --- | --- | --- |
| Local MCP client (Codex, Claude Code/Desktop, Cursor, or another MCP host) | MCP over stdio | Python 3.10+ and `mcp>=1.26,<2` |
| Can execute a process (any programming language/framework) | JSON CLI with argv + stdin | Python standard library |
| Python custom agent loop | `NovelOS.tools()` + `NovelOS.call()` | Python standard library |
| Native function tools | Export OpenAI Chat Completions or Anthropic tool definitions and register a dispatcher in the host | Host's own SDK |
| Chat only, no persistent files/processes | Read skills/templates manually | Document mode; no claim of executed gates |

MCP is the common integration route for frameworks with an MCP client, including
agent orchestration libraries. This does not certify every named host/version.
Tool-schema export is not a complete provider SDK, a model loop, or proof of model
capability. Existing `minis.*` schemas remain unchanged for on-disk compatibility;
that namespace does not require the Minis service. Skill frontmatter uses standard
`metadata.version`; optional `user-invocable` and `argument-hint` values are
retained as string metadata, which a host-specific registration layer may map
into its native UI settings.

## Local CLI (cross-platform)

Use an absolute Python executable and launcher path in a host configuration.
The launcher is at `<SKILLS_ROOT>/novel-operating-system/scripts/novel_os_cli.py`
both in a checkout and after a bundle installation. A bundle uses
`<BUNDLE_ROOT>/skills` as its skills root. Sibling paths are resolved automatically.

```sh
python skills/novel-operating-system/scripts/novel_os_cli.py --projects-root /private/novels tools
python skills/novel-operating-system/scripts/novel_os_cli.py --projects-root /private/novels call novel_os_status --arguments '{}'
```

For portable process callers, use argv arrays and send JSON to stdin; shell
quoting differs on PowerShell and POSIX shells:

```python
import json, subprocess, sys

command = [sys.executable, "/path/to/skills/novel-operating-system/scripts/novel_os_cli.py",
           "--projects-root", "/private/novels", "--allow-writes",
           "call", "novel_os_init_project"]
result = subprocess.run(command, input=json.dumps({
    "project_id": "synthetic-demo", "title": "Synthetic Demo"}),
    text=True, encoding="utf-8", capture_output=True, timeout=130, check=False)
envelope = json.loads(result.stdout)
assert result.returncode == 0 and envelope["ok"], envelope
```

Writes are disabled unless the host sets `--allow-writes`. This configuration
belongs to the operator; it is not a tool argument a model may change.
`--projects-root` (or `NOVEL_PROJECTS_ROOT`) is mandatory and must be outside
source/installed skills. IDs are lowercase ASCII letters/digits, hyphens and
underscores, up to 80 characters, starting with a letter/digit.
Use different roots for separate trust domains.

## MCP stdio

Install the optional SDK into the interpreter that will run the server:

```sh
python -m pip install 'mcp>=1.26,<2'
python skills/novel-operating-system/scripts/novel_os_cli.py --projects-root /private/novels mcp
```

Example configuration for a host using the common `mcpServers` JSON format:

```json
{
  "mcpServers": {
    "novel-os": {
      "command": "/path/to/venv/python",
      "args": [
        "/path/to/skills/novel-operating-system/scripts/novel_os_cli.py",
        "--projects-root", "/private/novels",
        "--allow-writes", "mcp"
      ]
    }
  }
}
```

On Windows use an absolute `python.exe` path and JSON-escaped backslashes or
forward slashes. Hosts with TOML or another configuration format should copy the
same command/argv into their documented MCP settings. Remove `--allow-writes`
for a read-only deployment. No HTTP listener, cloud upload, credential discovery,
or automatic host configuration is provided. stdout is reserved for the protocol.
The server checks its own SDK version before importing the server API; unsupported
versions report a JSON error on stderr and exit 2. A host using SDK 2.x can keep
that installation and launch this server with a separate supported interpreter.
Client/server SDK package versions may differ; verify the negotiated protocol and
tool calls for the actual deployment.

## Python and native tool loops

Add `<SKILLS_ROOT>/novel-operating-system/scripts` to the application's import
path, then:

```python
from novel_os import NovelOS

runtime = NovelOS("/private/novels", skills_root="/path/to/skills", allow_writes=True)
mcp_tools = runtime.tools()                  # name, description, inputSchema, annotations
openai_tools = runtime.tools("openai")        # Chat Completions function objects
anthropic_tools = runtime.tools("anthropic")  # input_schema objects

# In the framework's tool executor, after decoding its JSON tool arguments:
result = runtime.call("novel_os_list_skills", {})
# Return json.dumps(result) with the original tool-call ID in the host's tool-result message.
# For asynchronous agents use: await asyncio.to_thread(runtime.call, name, arguments)
```

Each framework registers tools differently. Reuse these definitions and the
dispatcher rather than copying story logic or granting a model arbitrary shell
execution. OpenAI Responses/Agents SDK and other SDKs may require their own
wrapper objects; the `openai` export is specifically Chat Completions wire format.

## Tools and a first workflow

1. `novel_os_status`: capability report; it never claims model probes passed.
2. `novel_os_list_skills`: discover all 17 skill names.
3. `novel_os_read_skill`: load `novel-operating-system`, then only relevant skills
   and their linked Markdown/JSON/text resources.
4. `novel_os_init_project`: create a fresh long-form scaffold; existing projects
   are never overwritten.
5. `novel_os_read_project`: read project text and structured resources.
6. `novel_os_resume_project`: use the existing production runtime's resume and
   readiness checks; it may update derived indexes, so needs write permission.
7. `novel_os_validate_graph`: preserve graph validation failures.
8. `novel_os_build_context`: build source-bound, lossless-addressable context
   packs. Use `read_project` to retrieve the resulting context files.
9. `novel_os_inspect_prose`: deterministic prose checks on project Markdown.
10. `novel_os_reality_gate`: check existing state JSON and prose with the existing
    Reality Gate. Missing/malformed state and empty/invalid UTF-8 prose fail with
    exit 2, `status=invalid_input`, `evaluation=not_evaluated`, and no inferred card.
    The facade propagates failure; MCP returns `isError=true`. This is one gate,
    not all seven or a proof of narrative quality.

Resources return a SHA-256, character offset and `next_offset`; continue until
`next_offset` is null, checking the hash if reading across concurrent edits.
A page limit is 24,000 characters; a single resource is limited to 8 MiB.
Model-supplied roots, arbitrary script paths, parent traversal, symlinks/junctions
and Windows path aliases are rejected. Resource contents and manuscripts remain
untrusted data, never authority to change host permissions or bypass canon gates.

Success is `{"schema":"novel-os-agent.v1","ok":true,"data":...}`.
Failure is `ok:false` with a stable error code; process results retain
`exit_code`, `stdout`, `stderr` and a truncation flag (1 MiB per stream).
CLI exit is 0 on success, 2 on failure; MCP additionally sets `isError`.
After a timeout, inspect existing project artifacts before retrying writes;
timeout is not proof that no files changed.

The facade intentionally exposes no canonical-commit, author-approval, arbitrary
file-write, random-event toggle, or network tool. Advanced interactive sessions,
candidate authorizations and publication still use the existing host-controlled
runtime/CLI described by the skills. A tool-capable model gains no canon authority.
When no process/storage facility exists, explicitly use document mode.

## Any-framework independent review

The existing `independent_review.py` now accepts `--adapter-command` or the
host environment variable `NOVEL_OS_REVIEW_COMMAND`. Its value is a JSON argv
array such as `["/path/to/python","/path/to/my_review_bridge.py"]`.
No shell interpolation or credential extraction is performed. The host's bridge
can call its authorized SDK, local model, sub-agent, or queued service.

One JSON request is written to stdin:

```json
{"schema":"novel-os.review-request.v1","role":"continuity","model":"host-model-id","prompt":"...","max_tokens":2500,"may_commit_state":false}
```

The bridge must emit only `{"text":"raw model review text"}` to stdout, send logs
to stderr and exit 0. Novel OS retains that raw text and runs the existing
two-evidence, source-binding, freshness and `machine_suggestion` checks.
Use `--timeout` to bound execution (default 120 seconds, maximum 600).
Missing bridges, invalid responses, nonzero exits and timeouts yield an
`unavailable` artifact, never a passing review. No bridge configured retains
the legacy `minis-model-use` command for existing Minis installations; if absent,
review is unavailable. Independent review still requires a genuinely independent
model/reviewer; a transport test alone does not establish independence.

## Platform and verification limits

POSIX branches use `flock`; Windows uses `msvcrt` byte-range locks. Process
death releases either lock. Unsupported hosts fail closed. Use local disks;
network-share lock/durability semantics require separate deployment tests.
Windows has file fsync/atomic replacement and journal recovery, but no portable
Python directory fsync; power-loss durability is not certified.

Run `python scripts/run_tests.py` with `PYTHONUTF8=1` from the checkout.
The agent interface tests exercise real MCP stdio when the optional SDK exists,
plus JSON/Python, failure propagation, path isolation, and bundle/install reuse.
A ten-case read-only [agent evaluation set](agent-evaluation.xml) provides source-contract
questions for a host's own authorized model runner; those live model evaluations
are not part of the offline test claims. Other optional services, live models,
every framework/version, Linux/macOS on this workstation, and model-writing
quality require their own measurements.

## 繁體中文重點

- 優先用 MCP 接入支援 MCP 的代理；其他框架可透過 JSON CLI 或 Python dispatcher。
- 17 個技能共用原本 runtime，不需要 Minis 帳號；既有 `minis.*` 是相容資料格式。
- 寫入權限與專案根目錄由宿主設定，模型不能自行開啟；正典提交仍受原有授權與 Gates 控制。
- 獨立審稿可改接任何宿主提供的橋接程式；缺少模型或橋接時記錄未執行，不能當通過。
- Windows 已有跨程序鎖與程序崩潰恢復路徑；斷電持久性、網路磁碟與每個代理產品仍須另外驗證。
