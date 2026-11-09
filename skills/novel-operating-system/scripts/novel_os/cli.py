"""JSON CLI: stdout contains exactly one JSON document, diagnostics use stderr."""
from __future__ import annotations
import argparse
import json
import os
import sys
from .runtime import NovelOS

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-root")
    parser.add_argument("--projects-root", default=os.environ.get("NOVEL_PROJECTS_ROOT"))
    parser.add_argument("--allow-writes", action="store_true")
    parser.add_argument("--timeout", type=float, default=120)
    sub = parser.add_subparsers(dest="command", required=True)
    catalog = sub.add_parser("tools")
    catalog.add_argument("--format", choices=("mcp", "openai", "anthropic"), default="mcp")
    call = sub.add_parser("call")
    call.add_argument("name")
    call.add_argument("--arguments", help="JSON object; omit to read JSON from stdin")
    sub.add_parser("mcp", help="Serve MCP over local stdio (optional mcp SDK required)")
    args = parser.parse_args(argv)
    if not args.projects_root:
        parser.error("--projects-root or NOVEL_PROJECTS_ROOT is required")
    # Explicit encoding also covers Windows hosts with a non-UTF-8 console.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        runtime = NovelOS(args.projects_root, skills_root=args.skills_root,
                          allow_writes=args.allow_writes, timeout=args.timeout)
        if args.command == "mcp":
            from .mcp_server import serve
            import asyncio
            asyncio.run(serve(runtime))
            return 0
        if args.command == "tools":
            result = runtime.tools(args.format)
        else:
            def reject_constant(value):
                raise ValueError("non-finite JSON is not allowed")
            text = args.arguments if args.arguments is not None else sys.stdin.read(65537)
            if len(text) > 65536:
                raise ValueError("arguments exceed 64 KiB")
            result = runtime.call(args.name, json.loads(text, parse_constant=reject_constant))
    except (OSError, ValueError, ImportError) as error:
        result = NovelOS._error("configuration_or_input", str(error))
        if args.command == "mcp":
            print(json.dumps(result, ensure_ascii=True), file=sys.stderr)
            return 2
    print(json.dumps(result, ensure_ascii=True, allow_nan=False))
    return 0 if isinstance(result, list) or result.get("ok") else 2

if __name__ == "__main__":
    raise SystemExit(main())
